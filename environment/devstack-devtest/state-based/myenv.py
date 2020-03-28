from flask import Flask, request, jsonify
from flask_restful import Api, Resource
import database
import requests
import time
import argparse
import subprocess
import yaml
import logging
import multiprocessing


logging.getLogger('werkzeug').setLevel(logging.ERROR)


def load_env_config():
    result = None
    with open('tests.yaml', 'r') as tests_file:
        result = yaml.load(tests_file, Loader=yaml.FullLoader)
    return result


ENV_CONFIG = load_env_config()
EXTERNAL_PORT = 9000
EXTERNAL_URL = 'localhost'
PROFILE_CURRENT = ''
PROFILE_CONFIG = None


def external_address():
    return str(EXTERNAL_URL) + ':' + str(EXTERNAL_PORT)


def url():
    return 'http://' + external_address() + '/env'


class EnvService(Resource):
    def __init__(self):
        pass

    def put(self):
        args = request.args
        test_id = database.control_ret_last_test_id()
        database.control_update(test_id, state=args['state'])
        print('env-service updating test id ' + str(test_id) + ' to ' + args['state'])

    def get(self):
        test_id = database.control_ret_last_test_id()
        if test_id > 0:
            state = database.control_ret_state(test_id)
            return jsonify({'state': state})
        else:
            return jsonify({'state': 'nop'})

    def post(self):
        content = request.json
        database.control_add(test_id=content['test_id'], state='init')
        print('env-service init test id ' + str(content['test_id']))


def _get_state(response):
    try:
        return response.json()['state']
    except:
        return None


def _wait_for_state(expected_state, url):
    expected_state_list = expected_state if isinstance(expected_state, list) else [expected_state]
    observed_state = _get_state(requests.get(url))
    while observed_state not in expected_state_list:
        time.sleep(0.5)
        observed_state = _get_state(requests.get(url))
    if observed_state in expected_state_list:
        return observed_state
    return None


def wait_env(test_id):
    requests.post(url(), json={'test_id': test_id})
    print('env waiting state = running')
    _wait_for_state('env_up', url())
    print('env state = running (sleeping 1s)')
    time.sleep(1)


def wait_test_finish():
    requests.put(url() + '?state=' + 'terminated')
    print('env state = terminated')


def _do_env_setup_worker(machine):
    subprocess.run(['VBoxManage', 'startvm', machine['name']])
    time.sleep(1)


def _do_env_setup():
    machines = ENV_CONFIG['tests'][PROFILE_CURRENT]['env-api']['devices']

    for machine in machines:
        subprocess.run(['VBoxManage', 'controlvm', machine['name'], 'poweroff'])
    time.sleep(1)
    for machine in machines:
        subprocess.run(['VBoxManage', 'snapshot', machine['name'], 'restore', machine['snapshot']])
    time.sleep(1)

    for x in range(20):
        processes = []
        for machine in machines:
            prio = 1
            if 'priority' in machine:
                prio = int(machine['priority'])
            if prio == x:
                p = multiprocessing.Process(target=_do_env_setup_worker, args=(machine,))
                processes.append(p)
                p.start()
        for p in processes:
            p.join()
    print('VMs started')


def wait_init():
    while True:
        print('env waiting init')
        _wait_for_state('init', url())
        print('env init found')
        _do_env_setup()
        requests.put(url() + '?state=env_up')
        print('env state = running')


def agent_get_outputs():
    import sh
    for line in sh.tail("-f", "/var/log/syslog", _iter=True):
        yield line


def agent_collect_outputs():
    if PROFILE_CONFIG is None:
        raise ValueError('Profile cannot be none')

    f_state = 0

    for output in agent_get_outputs():
        try:
            res = requests.post('http://' + PROFILE_CONFIG['env-api']['address'] + ':' + str(PROFILE_CONFIG['message-api']['port']) + '/outputs',
                                json={ 'output': output })
            if res.status_code == 200:
                if f_state != 1:
                    print('output-api receiving')
                    f_state = 1
            else:
                if f_state != 2:
                    print('output-api not receiving, code' % res.status_code)
                    f_state = 2
        except Exception as exc:
            if f_state != 3:
                print('output-api not receiving, exception "%s"' % repr(exc))
                f_state = 3


def prepare_vars(profile):
    global EXTERNAL_PORT
    global EXTERNAL_URL
    global PROFILE_CURRENT
    global PROFILE_CONFIG

    tests = ENV_CONFIG['tests']
    if profile in tests:
        print('Profile changed to ' + profile)
        api = tests[profile]['env-api']
        PROFILE_CURRENT = profile
        PROFILE_CONFIG = tests[profile]
        if 'address' in api:
            EXTERNAL_URL = api['address']
        if 'port' in api:
            EXTERNAL_PORT = api['port']


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('mode', type=str, choices=['server', 'client', 'agent'])
    parser.add_argument('--profile', type=str, required=False, default=None)
    args = parser.parse_args()
    if args.profile:
        prepare_vars(args.profile)
    if args.mode == 'server':
        app = Flask('environment-controller')
        api = Api(app)
        api.add_resource(EnvService, '/env')
        app.run(port=EXTERNAL_PORT, host='0.0.0.0')
    elif args.mode == 'client':
        wait_init()
    elif args.mode == 'agent':
        agent_collect_outputs()