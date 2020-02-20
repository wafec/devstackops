import requests
import pika
import json
import multiprocessing
import threading
import sys
import time


WILDCARD = 'test-'


def _get_management_service(host, user, passwd, service_path):
    res = requests.get('http://%s:15672/api/%s' % (host, service_path), auth=(user, passwd))
    if res.status_code < 300:
        bindings = json.loads(res.content)
        return bindings
    else:
        print('error %s rabbitmq management status_code %d' % (service_path, res.status_code))
        print('reror %s rabbitmq management content %s' % (service_path, res.content))
    return None


def _create_connection(host, user, passwd, vhost='/'):
    credentials = pika.PlainCredentials(user, passwd)
    parameters = pika.ConnectionParameters(host, 5672, vhost, credentials)
    connection = pika.BlockingConnection(parameters)
    return connection


def _create_test_bindings(connection):
    channel = connection.channel()
    channel.queue_declare('temp-queue')
    channel.exchange_declare('temp-exchange', 'topic')
    channel.queue_bind('temp-queue', 'temp-exchange', 'temp-key')


def _assert_falsification(host, user, passwd):
    res = requests.get('http://%s:15672/api/bindings' % host, auth=(user, passwd))
    assert(res.status_code == 200)
    result = json.loads(res.content)
    queues = [binding['destination'] for binding in result]
    exchanges = [binding['source'] for binding in result]
    keys = [binding['routing_key'] for binding in result]
    assert('temp' in ' '.join(queues))
    assert('temp' in ' '. join(exchanges))
    assert('temp' in ' '.join(keys))
    print('falsification was completed')


class Undo:
    def __init__(self, host, user, passwd, binding):
        self._host = host
        self._user = user
        self._passwd = passwd
        self._binding = binding

    def undo_falsify(self):
        connection = _create_connection(self._host, self._user, self._passwd, self._binding['vhost'])
        channel = connection.channel()
        source, destination, key = (self._binding['source'], self._binding['destination'], self._binding['routing_key'])
        test_queue_name = '%s%s' % (WILDCARD, destination)
        channel.queue_unbind(test_queue_name, source, key)
        channel.queue_bind(destination, source, key)


class UndoList:
    def __init__(self):
        self._items = []

    def add(self, host, user, passwd, binding):
        self._items.append(Undo(host, user, passwd, binding))

    def undo_falsify_all(self):
        for item in self._items:
            item.undo_falsify()
        print('all falsification undid')


def falsify_bindings(host, user, passwd):
    bindings = _get_management_service(host, user, passwd, 'bindings')
    exchanges = _get_management_service(host, user, passwd, 'exchanges')
    queues = _get_management_service(host, user, passwd, 'queues')
    exchanges = [exchange for exchange in exchanges if not exchange['auto_delete']]
    bindings = [binding for binding in bindings if binding['source'] in [exchange['name'] for exchange in exchanges]]
    bindings = [binding for binding in bindings if binding['destination'] in [queue['name'] for queue in queues]]
    bindings = [binding for binding in bindings if binding['source'] and binding['destination']]
    if bindings and exchanges and queues:
        undo_list = UndoList()
        for binding in bindings:
            connection = _create_connection(host, user, passwd, binding['vhost'])
            _create_test_bindings(connection)
            channel = connection.channel()
            source, destination, key = (binding['source'], binding['destination'], binding['routing_key'])
            if source and destination and key and \
               not source.startswith(WILDCARD) and not destination.startswith(WILDCARD) and \
               not key.startswith(WILDCARD):
                test_queue_name = '%s%s' % (WILDCARD, destination)
                test_key_name = '%s%s' % (WILDCARD, key)
                channel.queue_unbind(destination, source, key)
                channel.queue_declare(test_queue_name)
                channel.queue_bind(test_queue_name, source, key)
                channel.queue_bind(destination, source, test_key_name)
                undo_list.add(host, user, passwd, binding)
        _assert_falsification(host, user, passwd)
        return undo_list
    return None


class MessageArrivedHandler(multiprocessing.Process):
    def __init__(self, binding, connection_props, mapi_port, continue_ev):
        super(MessageArrivedHandler, self).__init__()
        self._binding = binding
        self._connection_props = connection_props
        self._connection = _create_connection(connection_props['host'], connection_props['user'], connection_props['passwd'], binding['vhost'])
        self._mapi_port = mapi_port
        self._temp_queue, self._key, self._exchange = (binding['destination'], binding['routing_key'], binding['source'])
        self._queue = self._temp_queue[len(WILDCARD):]
        self._test_key = '%s%s' % (WILDCARD, self._key)
        self._continue_ev = continue_ev

    def run(self):
        channel = self._connection.channel()
        channel.queue_declare(self._temp_queue)
        print('consuming queue %s' % self._temp_queue)
        channel.basic_consume(self._temp_queue, self._on_message_arrived)
        self._continue_ev.set()
        channel.start_consuming()

    def _on_message_arrived(self, channel, method_frame, properties, body):
        print('rabbitmq message arrived (exchange=%s, key=%s, delivery=%d)' % (method_frame.exchange,
                                                                               method_frame.routing_key,
                                                                               method_frame.delivery_tag))
        try:
            data = {
                'body': str(body.decode('utf-8')),
                'source': self._binding['source'],
                'destination': self._binding['destination'],
                'routing_key': self._binding['routing_key'],
                'vhost': self._binding['vhost'],
                'wildcard': WILDCARD,
                'test_key': self._test_key,
                'temp_queue': self._temp_queue,
                'queue': self._temp_queue[len(WILDCARD):]
            }
            res = requests.post('http://localhost:%d/messages' % self._mapi_port, json=data)
            if res.status_code == 200:
                body = res.json()['body'].encode('utf-8')
        except:
            print('message-monitor-service unavailable')
        channel.basic_ack(delivery_tag=method_frame.delivery_tag)
        channel.basic_publish(exchange=self._exchange, routing_key=self._test_key, body=body, properties=properties)


def _start_binding_falsified_queues(bindings, host, user, passwd, sync_ev, termination_ev, mapi_port):
    handlers = []
    for binding in bindings:
        continue_ev = multiprocessing.Event()
        handler = MessageArrivedHandler(binding, { 'host': host, 'user': user, 'passwd': passwd }, mapi_port, continue_ev)
        handler.start()
        handlers.append(handler)
        continue_ev.wait()
    sync_ev.set()
    termination_ev.wait()
    for handler in handlers:
        handler.terminate()
        handler.join()
    print('binding to falsification finished')


def bind_to_falsified_queues(host, user, passwd, termination_ev, mapi_port):
    res = requests.get('http://%s:15672/api/bindings' % (host), auth=(user, passwd))
    if res.status_code:
        bindings = json.loads(res.content)
        bindings = [binding for binding in bindings if binding['destination'].startswith(WILDCARD) and binding['source']]
        sync_ev = threading.Event()
        handler = threading.Thread(target=_start_binding_falsified_queues, args=(bindings, host, user, passwd, sync_ev, termination_ev, mapi_port))
        handler.start()
        sync_ev.wait()
        return True
    return False


if __name__ == '__main__':
    cmd = sys.argv[1]
    if cmd == 'a':
        conn = _create_connection('localhost', 'admin', 'supersecret')
        channel = conn.channel()
        channel.queue_declare('queue1')
        channel.exchange_declare('exchange1', exchange_type='topic')
        channel.queue_bind(queue='queue1', exchange='exchange1', routing_key='key1')
        falsify_bindings('localhost', 'admin', 'supersecret')
    elif cmd == 'b':
        def _message_callback(channel, method, frame, body):
            print(body)
            channel.basic_ack(delivery_tag=method.delivery_tag)

        def _consume():
            conn = _create_connection('localhost', 'admin', 'supersecret')
            channel = conn.channel()
            print('consuming test-queue1')
            channel.basic_consume(queue='test-queue1', on_message_callback=_message_callback)
            channel.start_consuming()


        process1 = multiprocessing.Process(target=_consume)
        process1.start()

        time.sleep(2)

        conn = _create_connection('localhost', 'admin', 'supersecret')
        channel = conn.channel()
        print('publishing hello world')
        channel.basic_publish(exchange='exchange1', routing_key='key1', body='Hello World')

        process1.terminate()
        process1.join()
