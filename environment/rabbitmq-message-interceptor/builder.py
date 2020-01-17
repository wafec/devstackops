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
    return binding_instance["destination_kind"] == 'queue' and binding_instance["source_kind"] == 'exchange' and\
           binding_instance["source_name"]


binding_instances = [instance for instance in binding_instances if is_binding_instance_worthy(instance)]

credentials = pika.PlainCredentials('stackrabbit', 'supersecret')
parameters = pika.ConnectionParameters(
    'localhost',
    5672,
    '/',
    credentials
)
connection = pika.BlockingConnection(parameters)
channel = connection.channel()

for binding_instance in binding_instances:
    channel.queue_declare(queue=binding_instance["destination_name"] + '-bridge')

for binding_instance in binding_instances:
    channel.queue_unbind(
        queue=binding_instance["destination_name"],
        exchange=binding_instance["source_name"],
        routing_key=binding_instance["routing_key"]
    )

for binding_instance in binding_instances:
    channel.queue_bind(
        queue=binding_instance["destination_name"] + '-bridge',
        exchange=binding_instance["source_name"],
        routing_key=binding_instance["routing_key"]
    )

for binding_instance in binding_instances:
    channel.queue_bind(
        queue=binding_instance["destination_name"],
        exchange=binding_instance["source_name"],
        routing_key=binding_instance["routing_key"] + '-origin'
    )

with open('./data/builder', 'w') as builder_file:
    for binding_instance in binding_instances:
        builder_file.write(json.dumps(binding_instance) + '\n')

print('Bindings well done.')