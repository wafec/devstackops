from flask import Flask, request, jsonify
from flask_restful import Api, Resource
import database
import requests
import time
import argparse
import subprocess


EXTERNAL_PORT = 9000
EXTERNAL_URL = '192.168.56.114'
EXTERNAL_ADDRESS = str(EXTERNAL_URL) + ':' + str(EXTERNAL_PORT)
_URL = 'http://' + EXTERNAL_ADDRESS + '/env'


class EnvService(Resource):
    def __init__(self):
        pass

    def put(self):
        args = request.args
        test_id = database.control_ret_last_test_id()
        database.control_update(test_id, state=args['state'])

    def get(self):
        test_id = database.control_ret_last_test_id()
        state = database.control_ret_state(test_id)
        return jsonify({'state': state})

    def post(self):
        content = request.json
        database.control_add(test_id=content['test_id'], state='init')


def _wait_for_state(expected_state, url):
    observed_state = requests.get(url).json()['state']
    while observed_state != expected_state:
        time.sleep(0.5)
        observed_state = requests.get(url).json()['state']


def wait_env(test_id):
    requests.post(_URL, json={'test_id': test_id})
    _wait_for_state('env_up', _URL)


def wait_test_finish():
    requests.put(_URL + '?state=' + 'terminated')


def _do_env_setup():
    machines = []
    for machine in machines:
        subprocess.run(['VBoxManage', 'controlvm', machine['name'], 'poweroff'])
        subprocess.run(['VBoxManage', 'snapshot', machine['name'], 'restore', machine['snapshot']])
        subprocess.run(['VBoxManage', 'startvm', machine['name']])


def wait_init():
    while True:
        _wait_for_state('init', _URL)
        _do_env_setup()
        requests.put(_URL + '?state=env_up')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('mode', type=str, choices=['server', 'client'])
    args = parser.parse_args()
    if args.mode == 'server':
        app = Flask('environment-controller')
        api = Api(app)
        api.add_resource(EnvService, '/env')
        app.run(port=EXTERNAL_PORT, host='0.0.0.0')
    elif args.mode == 'client':
        wait_init()