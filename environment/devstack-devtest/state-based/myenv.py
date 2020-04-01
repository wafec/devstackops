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
import os


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
    subprocess.run(['VBoxManage', 'startvm', machine['name'], '--type', 'headless'])
    time.sleep(1)


def _do_env_setup(flag=0x7):
    machines = ENV_CONFIG['tests'][PROFILE_CURRENT]['env-api']['devices']

    if flag & 0x1 != 0:
        for machine in machines:
            subprocess.run(['VBoxManage', 'controlvm', machine['name'], 'poweroff'])
        time.sleep(1)
        print('VMs stopped')
    if flag & 0x2 != 0:
        for machine in machines:
            subprocess.run(['VBoxManage', 'snapshot', machine['name'], 'restore', machine['snapshot']])
        time.sleep(1)
        print('VMs restored')

    if flag & 0x4 != 0:
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
            time.sleep(1)
        print('VMs started')


def wait_init(ignore=False):
    while True:
        print('env waiting init')
        state = _wait_for_state(['init', 'terminated'], url())
        if state == 'terminated':
            if not ignore:
                _do_env_setup(0x1)
            requests.put(url() + '?state=done')
            continue
        print('env init found')
        if not ignore:
            _do_env_setup()
        requests.put(url() + '?state=env_up')
        print('env state = running')


class AgentOutputShared:
    def __init__(self):
        self.f_state = 0


def _agent_send_output(service, output, shared):
    try:
        res = requests.post('http://' + PROFILE_CONFIG['env-api']['address'] + ':' + str(PROFILE_CONFIG['message-api']['port']) + '/outputs',
                            json={ 'output': output })
        if res.status_code == 200:
            if shared.f_state != 1:
                print('output-api receiving')
                shared.f_state = 1
        else:
            if shared.f_state != 2:
                print('output-api not receiving, code' % res.status_code)
                shared.f_state = 2
    except Exception as exc:
        if shared.f_state != 3:
            print('output-api not receiving, exception "%s"' % repr(exc))
            shared.f_state = 3



def agent_get_file_outputs_parallel(lock, handler, filepath, defaultfilepath):
    import sh
    if not os.path.exists(filepath) or not os.path.exists(defaultfilepath) or not os.path.isfile(filepath) or not os.path.isfile(defaultfilepath):
        print('Wow! Invalid arguments in get outputs parallel (%s, %s)' % (filepath, defaultfilepath))
        return 
    print('Listening (%s, %s)' % (filepath, defaultfilepath))
    for line in sh.tail('-f', filepath, _iter=True):
        with lock:
            with open(defaultfilepath, 'a') as defaultf:
                defaultf.write('%s\n' % (line))


def agent_get_outputs_reporter_parallel(lock, handler, defaultfilepath):
    import sh
    if not os.path.exists(defaultfilepath) or not os.path.isfile(defaultfilepath):
        print('Ops! Not a file in reporter parallel (%s)' % (defaultfilepath))
        return
    print('Listening defaults (%s)' % (defaultfilepath))
    for line in sh.tail('-f', defaultfilepath, _iter=True):
        div = line.find(" ")
        service = line[:div]
        output = line[div+1:]
        _agent_send_output(service, output)


def agent_collect_outputs2(services):
    # TODO: multiprocessing
    ps = []
    lock = multiprocessing.Lock()
    handler = multiprocessing.Event()
    defaults = 'defaults.log'
    files = []
    for service in services:
        if os.path.exists(os.path.join('/var/log/', service)):
            service_files = [f for f in os.listdir(os.path.join('/var/log/', service)) if os.path.isfile(f)]
            service_files = [f for f in service_files if f.endswith('.log')]
            files = files + service_files
    if files:
        reporter = multiprocessing.Process(target=agent_get_outputs_reporter_parallel, args=(lock, handler, defaults))
        ps.append(reporter)
        for f in files:
            print('Adding file %s' % f)
            serviced = multiprocessing.Process(target=agent_get_file_outputs_paralell, args=(lock, handler, f, defaults))
            ps.append(serviced)
    if ps and len(ps) > 1:
        print('Starting agent processes')
        for p in ps:
            p.start()
    
        try:
            while True:
                pass
        except:
            for p in ps:
                p.terminate()
    else:
        print('Hmm. No process to start')


def agent_get_outputs():
    import sh
    for line in sh.tail("-f", "/var/log/syslog", _iter=True):
        yield line


def agent_collect_outputs():
    if PROFILE_CONFIG is None:
        raise ValueError('Profile cannot be none')

    shared = AgentOutputShared()

    for output in agent_get_outputs():
        _agent_send_output('syslog', output, shared)


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
    parser.add_argument('mode', type=str, choices=['server', 'client', 'agent', 'agent2'])
    parser.add_argument('--profile', type=str, required=False, default=None)
    parser.add_argument('--ignore', action="store_true", default=False)
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
        agent_collect_outputs(args.ignore)
