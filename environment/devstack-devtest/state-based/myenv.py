from flask import Flask, request
from flask_restful import Api, Resource
import database
import requests
import time
import argparse


EXTERNAL_ADDRESS = 'localhost:9000'


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
        return {'state': state}

    def post(self):
        content = request.json
        database.control_add(test_id=content['test_id'], state='init')


def _wait_for_state(expected_state, url):
    observed_state = requests.get(url).json()['state']
    while observed_state != expected_state:
        time.sleep(0.5)
        observed_state = requests.get(url).json()['state']


def wait_env(test_id):
    url = 'http://localhost:9000/env'
    requests.post(url, json={'test_id': test_id})
    _wait_for_state('env_up', url)


def _do_env_setup():
    time.sleep(1)
    print('env up')


def wait_init():
    url = 'http://' + str(EXTERNAL_ADDRESS) + '/env'
    while True:
        _wait_for_state('init', url)
        _do_env_setup()
        requests.put(url + '?state=env_up')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('mode', type=str, choices=['server', 'client'])
    args = parser.parse_args()
    if args.mode == 'server':
        app = Flask('environment-controller')
        api = Api(app)
        api.add_resource(EnvService, '/env')
        app.run(port=9000)
    elif args.mode == 'client':
        wait_init()