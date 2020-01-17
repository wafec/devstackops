#!/usr/bin/env python

import os
import json


if not os.path.exists('./data/bindings'):
    print("File 'bindings' not found.")
    exit(-1)

binding_instances = []

with open('./data/bindings', 'r') as bindings_file:
    for line in bindings_file.readlines()[1:]:
        fields = line.replace('\n', '').split('\t')
        binding_instance = {
            "source_name": fields[0],
            "source_kind": fields[1],
            "destination_name": fields[2],
            "destination_kind": fields[3],
            "routing_key": fields[4],
            "arguments": fields[5]
        }
        binding_instances.append(binding_instance)

with open('./data/names', 'w') as names_file:
    for binding_instance in binding_instances:
        instance_str = json.dumps(binding_instance)
        names_file.write(instance_str + '\n')

print("File 'names' created successfully.")