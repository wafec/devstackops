import requests
import pika
import json


WILDCARD = 'test-'


def _create_connection(host, user, passwd):
    credentials = pika.PlainCredentials(user, passwd)
    parameters = pika.ConnectionParameters(host, '5672', '/', credentials)
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
    res = requests.get('http://%s:15672/api/bindings' % (host), auth=(user, passwd))
    if res.status_code:
        bindings = json.loads(res.content)
        connection = _create_connection(host, user, passwd)
        _create_test_bindings(connection)
        channel = connection.channel()
        for binding in bindings:
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