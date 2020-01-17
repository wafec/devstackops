#!/usr/bin/env python

import pika
import os
import sys
import json


if not os.path.exists('./data/names'):
    print("File 'names' not found")
    exit(-1)

binding_instances = []
with open('./data/names', 'r') as names_file:
    for line in names_file.readlines():
        binding_instances.append(json.loads(line))

credentials = pika.PlainCredentials(os.environ["RABBIT_USER"], os.environ["RABBIT_PASS"])
parameters = pika.ConnectionParameters(
    os.environ["RABBIT_HOST"],
    os.environ["RABBIT_PORT"],
    os.environ["RABBIT_VHOST"],
    credentials
)
connection = pika.BlockingConnection(parameters=parameters)
channel = connection.channel()


class QueueConsumer(object):
    def __init__(self, channel, queue, routing_key, exchange):
        self._channel = channel
        self._queue = queue
        self._routing_key = routing_key
        self._exchange = exchange
    
    def consume(self):
        self._channel.queue_declare(queue=self._queue)
        self._channel.basic_consume(self._queue, self.on_message)

    def on_message(self, channel, method_frame, header_frame, body):
        print(self._queue, body)
        self._channel.basic_publish(exchange=self._exchange, routing_key=self._routing_key, body=body)


def is_bridge(instance):
    return instance and instance["source_name"] and instance["destination_name"].endswith('-bridge') and\
           instance["destination_kind"] == 'queue' and instance["source_kind"] == 'exchange'

queues = []
for binding_instance in [i for i in binding_instances if is_bridge(i)]:
    consumer = QueueConsumer(
        channel,
        binding_instance['destination_name'],
        binding_instance['routing_key'] + '-origin',
        binding_instance['source_name']
    )
    consumer.consume()
    queues.append(binding_instance["destination_name"])

try:
    print("Start consuming...")
    print('Consuming ' + ', '.join(queues))
    channel.start_consuming()
finally:
    channel.stop_consuming()
    connection.close()
