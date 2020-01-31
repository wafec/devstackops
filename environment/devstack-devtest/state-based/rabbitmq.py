import requests
import pika
import json
import multiprocessing
import threading


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


def falsify_bindings(host, user, passwd):
    bindings = _get_management_service(host, user, passwd, 'bindings')
    exchanges = _get_management_service(host, user, passwd, 'exchanges')
    queues = _get_management_service(host, user, passwd, 'queues')
    exchanges = [exchange for exchange in exchanges if not exchange['auto_delete']]
    bindings = [binding for binding in bindings if binding['source'] in [exchange['name'] for exchange in exchanges]]
    bindings = [binding for binding in bindings if binding['destination'] in [queue['name'] for queue in queues]]
    bindings = [binding for binding in bindings if binding['source'] and binding['destination']]
    if bindings and exchanges and queues:
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
        _assert_falsification(host, user, passwd)
        return True
    return False


class MessageArrivedHandler(multiprocessing.Process):
    def __init__(self, binding, connection_props, mapi_port):
        super(MessageArrivedHandler, self).__init__()
        self._binding = binding
        self._connection_props = connection_props
        self._connection = _create_connection(connection_props['host'], connection_props['user'], connection_props['passwd'])
        self._mapi_port = mapi_port
        self._temp_queue, self._key, self._exchange = (binding['destination'], binding['routing_key'], binding['source'])
        self._queue = self._temp_queue[len(WILDCARD):]
        self._temp_key = '%s%s' % (WILDCARD, self._key)

    def run(self):
        channel = self._connection.channel()
        channel.queue_declare(self._temp_queue)
        print('consuming queue %s' % self._temp_queue)
        channel.basic_consume(self._temp_queue, self._on_message_arrived)

    def _on_message_arrived(self, channel, method_frame, header_frame, body):
        data = { body: body }
        res = requests.post('http://localhost:%d/messages' % self._mapi_port, json=data)
        if res.status_code == 200:
            body = res.json['body']
        channel = self._connection.channel()
        channel.queue_declare(self._queue)
        channel.basic_publish(queue=self._queue, exchange=self._exchange, routing_key=self._temp_key, body=body)
        channel.basic_ack(delivery_tag=method_frame.delivery_tag)


def _start_binding_falsified_queues(bindings, host, user, passwd, sync_ev, termination_ev, mapi_port):
    handlers = []
    for binding in bindings:
        handler = MessageArrivedHandler(binding, { 'host': host, 'user': user, 'passwd': passwd }, mapi_port)
        handler.start()
        handlers.append(handler)
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
        bindings = [binding for binding in bindings if binding['destination'].startswith(WILDCARD)]
        sync_ev = threading.Event()
        handler = threading.Thread(target=_start_binding_falsified_queues, args=(bindings, host, user, passwd, sync_ev, termination_ev, mapi_port))
        handler.start()
        sync_ev.wait()
        return True
    return False