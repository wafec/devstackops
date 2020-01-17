#!/usr/bin/env python

import pika
import json
import os
import threading


if not os.path.exists('./data/names'):
    print("File 'names' not found.")
    exit(-1)

binding_instances = []

with open('./data/names') as names_file:
    for line in names_file:
        binding_instance = json.loads(line)
        binding_instances.append(binding_instance)


def is_binding_instance_worthy(binding_instance):
    return binding_instance["destination_kind"] == 'queue' and binding_instance["source_kind"] == 'exchange'


binding_instances = [instance for instance in binding_instances if is_binding_instance_worthy(instance)]


class BaseQueueAction(object):
    def __init__(self, channel):
        self._channel = channel
        self._event = threading.Event()

    def action(self):
        self._run(self._callback)
        self._event.wait()

    def _callback(self, arg):
        self._event.set()


class QueueDeclare(BaseQueueAction):
    def __init__(self, channel, queue_name):
        super(self, QueueDeclare).__init__(channel)
        self._queue_name = queue_name

    def _run(self, callback):
        self._channel.queue_declare(queue=self._queue_name, callback=callback)


class QueueUnbind(BaseQueueAction):
    def __init__(self, channel, queue_name, exchange_name, routing_key):
        super(self, QueueUnbind).__init__(channel)
        self._queue_name = queue_name
        self._exchange_name = exchange_name
        self._routing_key = routing_key

    def _run(self, callback):
        self._channel.queue_unbind(
            queue=self._queue_name,
            exchange=self._exchange_name,
            routing_key=self._routing_key,
            callback=callback
        )


class QueueBind(BaseQueueAction):
    def __init__(self, channel, queue_name, exchange_name, routing_key):
        super(self, QueueBind).__init__(channel)
        self._queue_name = queue_name
        self._exchange_name = exchange_name
        self._routing_key = routing_key

    def _run(self, callback):
        self._channel.queue_bind(
            queue=self._queue_name,
            exchange=self._exchange,
            routing_key=self._routing_key,
            callback=callback
        )


parameters = pika.ConnectionParameters('localhost')
connection = pika.BlockingConnection(parameters)
channel = connection.channel()

for binding_instance in binding_instances:
    queue_declare = new QueueDeclare(
        channel,
        binding_instance["destination_name"] + '-bridge'
    )
    queue_declare.action()

for binding_instance in binding_instances:
    queue_unbind = new QueueUnbind(
        channel,
        binding_instance["destination_name"],
        binding_instance["source_name"],
        binding_instance["routing_key"]
    )
    queue_unbind.action()

for binding_instance in binding_instances:
    queue_bind = new QueueBind(
        channel,
        binding_instance["destination_name"] + '-bridge',
        binding_instance["source_name"],
        binding_instance["routing_key"]
    )
    queue_bind.action()

for binding_instance in binding_instances:
    queue_bind = new QueueBind(
        channel,
        binding_instance["destination_name"],
        binding_instance["source_name"],
        binding_instance["routing_key"] + '-origin'
    )

with open('./data/builder', 'w') as builder_file:
    for binding_instance in binding_instances:
        builder_file.write(json.dumps(binding_instance) + '\n')

print('Bindings well done.')