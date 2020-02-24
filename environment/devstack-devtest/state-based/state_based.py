import threading
import multiprocessing
from flask import Flask, request
from flask_restful import Api, Resource
import time
import rabbitmq
import requests
import sys
import traceback
import yaml
import os
import json
import database
import mydictutils
import operators
import logging


logging.getLogger('werkzeug').setLevel(logging.ERROR)


class Message(object):
    def __init__(self, name, fields):
        self.name = name
        self.fields = fields


class Arg(object):
    def __init__(self, name, value):
        self.name = name
        self.value = value


class State(object):
    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return self.name


class TestEntry(object):
    def __init__(self, event, args=None, messages=None, func=None, states=None):
        self._event = event
        self._args = args if args else []
        self._messages = messages if messages else []
        self._func = func
        self._states = states if states else []

    def _func_undefined(self):
        print('test-case function undefined')

    @property
    def func(self):
        if self._func:
            return self._func
        return self._func_undefined

    @func.setter
    def func(self, func):
        self._func = func
        time.sleep(1)

    @property
    def event(self):
        return self._event

    @property
    def args(self):
        return self._args

    @property
    def messages(self):
        return self._messages

    @property
    def states(self):
        return self._states


def tests_from_file(filepath):
    if os.path.exists(filepath):
        with open(filepath, 'r') as tests_file:
            tests = yaml.load(tests_file, Loader=yaml.FullLoader)
        test_case = []
        for test in tests['test-case']:
            test_entry = TestEntry(test['event'])
            for arg in test['args']:
                test_entry.args.append(Arg(arg['name'], arg['value']))
            for state in test['states']:
                test_entry.states.append(State(state['name']))
            test_case.append(test_entry)
        return test_case
    return None


class TestHandler(object):
    STOPPED = 0
    STARTED = 1
    NONE = 2

    def __init__(self, tests, test_id=None, test_number=None):
        self.tests = tests
        self.current_test = None
        self.current_result = None
        self.execution_cv = threading.Condition()
        self.status = TestHandler.NONE
        self.completion_cv = threading.Condition()
        self.statem_ev = threading.Event()
        self._iteration_number = None
        self._exceptions = []
        self._instances = {}
        self.test_id = test_id
        self.test_number = test_number

    def start_iteration_counting(self):
        self._iteration_number = 0

    def stop_iteration_counting(self):
        self._iteration_number = None

    def increment_iteration_by_one(self):
        if self._iteration_number is not None:
            self._iteration_number = self._iteration_number + 1

    @property
    def exceptions(self):
        return self._exceptions

    @property
    def has_errors(self):
        return len(self._exceptions) > 0

    @property
    def iteration_number(self):
        return 0 if not self._iteration_number else self._iteration_number

    @property
    def instances(self):
        return self._instances


class TestSuiteExecution(threading.Thread):
    def __init__(self, test_handler):
        super(TestSuiteExecution, self).__init__()
        self._test_handler = test_handler

    def run(self):
        self._test_handler.status = TestHandler.STARTED
        self._test_handler.start_iteration_counting()
        for test in self._test_handler.tests:
            self._test_handler.statem_ev.wait()
            self._test_handler.statem_ev.clear()
            print('[%02d] run test' % self._test_handler.iteration_number)
            self._test_handler.current_test = test
            try:
                self._test_handler.current_result = test.func()
            except Exception as func_exc:
                self._test_handler.exceptions.append(func_exc)
                self._test_handler.status = TestHandler.STOPPED
                with self._test_handler.execution_cv:
                    self._test_handler.execution_cv.notify()
                break
            with self._test_handler.execution_cv:
                self._test_handler.execution_cv.notify()
                print('[%02d] execution waiting states completion' % self._test_handler.iteration_number)
                self._test_handler.execution_cv.wait()
                self._test_handler.status = TestHandler.STARTED if test != self._test_handler.tests[-1] and not \
                    self._test_handler.has_errors else TestHandler.STOPPED
                self._test_handler.execution_cv.notify()
            self._test_handler.increment_iteration_by_one()
        print('test-execution finished')
        with self._test_handler.completion_cv:
            self._test_handler.completion_cv.notify()
        self._test_handler.stop_iteration_counting()


class StateMonitor(threading.Thread):
    def __init__(self, test_handler, func=None):
        super(StateMonitor, self).__init__()
        self._test_handler = test_handler
        self._func = func

    def _func_undefined(self):
        print('[%02d] state-monitor function undefined' % self._test_handler.iteration_number)
        time.sleep(1)

    @property
    def func(self):
        if self._func:
            return self._func
        return self._func_undefined

    @func.setter
    def func(self, func):
        self._func = func

    def run(self):
        while self._test_handler.status != TestHandler.STOPPED:
            print('[%02d] state-monitor waiting test execution' % self._test_handler.iteration_number)
            with self._test_handler.execution_cv:
                self._test_handler.statem_ev.set()
                self._test_handler.execution_cv.wait()
                if self._test_handler.status == TestHandler.STOPPED:
                    continue
                print('[%02d] state-monitor states' % self._test_handler.iteration_number)
                try:
                    result = self.func()
                    print('[%02d] state-monitor result = %s' % (self._test_handler.iteration_number, str(result)))
                except Exception as monitor_exc:
                    self._test_handler.exceptions.append(monitor_exc)
                self._test_handler.execution_cv.notify()
                self._test_handler.execution_cv.wait()
        print('state-monitor stopped')


class OutputMonitorApi(Resource):
    def __init__(self, test_handler):
        self._test_handler = test_handler

    def post(self):
        content = request.json
        test_output = content['output']
        database.output_add(self._test_handler.test_id, test_output)


class MessageMonitorApi(Resource):
    def __init__(self, test_handler, injection_enabled=False, lock=None):
        self._test_handler = test_handler
        self._monitor_injection_enabled = injection_enabled
        self._lock = lock if lock is not None else multiprocessing.Lock()

    def _add_injection(self, message_id, path, value, mutation, param_type, name):
        with self._lock:
            try:
                return database.injection_add(message_id, path, value, mutation, param_type, name)
            except database.DatabaseError:
                return database.injection_add(message_id, path, value, 'unsupported type', param_type, name)

    def _monitor_injection(self, message_args, message_id):
        if database.injection_count(self._test_handler.test_id) > 0:
            return None

        params = mydictutils.dict_collect_params(message_args)
        injections = database.injection_list_params(self._test_handler.test_number)
        xs = operators.the_operators()
        for path in params:
            value = mydictutils.dict_param_get(message_args, path)
            param_type = mydictutils.dict_what_type_is_it(value)
            if param_type in xs:
                if path not in [injection['injection_param'] for injection in injections]:
                    function = xs[param_type][0]
                    name = function['name']
                    action = function['function']
                    mutation = action(value)
                    injection_id = self._add_injection(message_id, path, value, mutation, param_type, name)
                    print('[%02d] injection new mutation' % self._test_handler.iteration_number)
                    mydictutils.dict_param_set(message_args, path, mutation)
                    return injection_id
                else:
                    existent = [(injection['injection_operator'], injection['injection_param_type']) for injection in injections if injection['injection_param'] == path]
                    types = set([x[1] for x in existent])
                    names = set([x[0] for x in existent])
                    x = [xs[i] for i in xs if i in types]
                    flat = [item for sublist in x for item in sublist]
                    for e in flat:
                        if e['name'] not in names:
                            action = e['function']
                            name = e['name']
                            mutation = action(value)
                            injection_id = self._add_injection(message_id, path, value, mutation, param_type, name)
                            print('[%02d] injection existent mutation' % self._test_handler.iteration_number)
                            mydictutils.dict_param_set(message_args, path, mutation)
                            return injection_id
        return None

    def post(self):
        content = request.json
        body = None
        if self._monitor_injection_enabled:
            message_src = content['source']
            message_dst = content['destination']
            message_key = content['routing_key']
            body = json.loads(content['body'])
            message_payload = json.loads(body['oslo.message'])
            message_action = None
            message_args = None
            if 'method' in message_payload:
                message_action = message_payload['method']
            if 'args' in message_payload:
                message_args = message_payload['args']
            if self._test_handler.test_id:
                with self._lock:
                    message_id = database.message_add(self._test_handler.test_id,
                                                      message_src, message_dst, message_key, json.dumps(message_payload),
                                                      message_action)
                if message_action and message_args and self._test_handler.test_number:
                    monitor_injection_result = self._monitor_injection(message_args, message_id)
                    if monitor_injection_result is not None:
                        body['oslo.message'] = json.dumps(message_args)
        return { 'body': json.dumps(body) if body else content['body'] }

    def get(self):
        return 'MessageMonitorApi is active!'


class MessageMonitor(threading.Thread):
    def __init__(self, test_handler, port, injection_enabled):
        super(MessageMonitor, self).__init__()
        self._test_handler = test_handler
        self._port = port
        self._injection_enabled = injection_enabled
        print('[%02d] message-monitor injection enabled %s' % (test_handler.iteration_number, 'enabled' if injection_enabled else 'disabled'))

    def run(self):
        return
        app = Flask('message-monitor')
        api = Api(app)
        lock = multiprocessing.Lock()
        api.add_resource(MessageMonitorApi, '/messages', resource_class_kwargs={ 'test_handler': self._test_handler, 'injection_enabled': self._injection_enabled, 'lock': lock })
        api.add_resource(OutputMonitorApi, '/outputs', resource_class_kwargs={ 'test_handler': self._test_handler })
        server = multiprocessing.Process(target=app.run, kwargs={ 'port': self._port, 'host': '0.0.0.0' })
        server.start()
        with self._test_handler.completion_cv:
            self._test_handler.completion_cv.wait()
        server.terminate()
        server.join()
        print('message-monitor terminated')


def wait_for_message_monitor_api(port, attempts=10):
    is_active = None
    try:
        res = requests.get('http://localhost:%s/messages' % port, timeout=10)
        if res.status_code == 200:
            is_active = True
            print('message-monitor-api assertion completed')
        else:
            if not attempts:
                print('message-monitor-api status code  %s' % res.status_code)
    except:
        if not attempts:
            traceback.print_exc(file=sys.stdout)
        if not attempts:
            print('oops! an exception occurred on asserting message-monitor-api was active')
        is_active = False
    if attempts and not is_active:
        time.sleep(0.5)
        is_active = wait_for_message_monitor_api(port, attempts - 1)
    return is_active


def test_tests(tests, opts_or_file=None, profile=None, state_monitor_function=None, test_handler=None,
               ignore_falsification=False):
    if not opts_or_file or isinstance(opts_or_file, str):
        opts_or_file = 'tests.yaml' if not opts_or_file else opts_or_file
        if os.path.exists(opts_or_file):
            with open(opts_or_file, 'r') as tests_yaml_file:
                opts_or_file = yaml.load(tests_yaml_file, Loader=yaml.FullLoader)
            if 'tests' in opts_or_file:
                opts_or_file = opts_or_file['tests']
                if profile:
                    opts_or_file = opts_or_file[profile]
                else:
                    opts_or_file = None
            else:
                opts_or_file = None
    if not opts_or_file:
        raise ValueError('opts_or_file is invalid')

    rmq_host, rmq_user, rmq_passwd = (opts_or_file['rabbitmq']['host'], opts_or_file['rabbitmq']['user'], opts_or_file['rabbitmq']['passwd'])
    message_api_port = opts_or_file['message-api']['port']
    message_api_injection_enabled = False
    if 'injection-enabled' in opts_or_file['message-api']:
        message_api_injection_enabled = opts_or_file['message-api']['injection-enabled']
    falsification_rollback = None
    if not ignore_falsification:
        falsification_rollback = rabbitmq.falsify_bindings(rmq_host, rmq_user, rmq_passwd)
    if falsification_rollback or ignore_falsification:
        termination_ev = threading.Event()
        rabbitmq.bind_to_falsified_queues(rmq_host, rmq_user, rmq_passwd, termination_ev, message_api_port)

        test_handler = test_handler if test_handler else TestHandler(tests)
        test_execution = TestSuiteExecution(test_handler)
        state_monitor = StateMonitor(test_handler, state_monitor_function)
        message_monitor = MessageMonitor(test_handler, message_api_port, message_api_injection_enabled)

        message_monitor.start()
        message_api_active = wait_for_message_monitor_api(message_api_port)
        if not message_api_active:
            with test_handler.completion_cv:
                test_handler.completion_cv.notify()
        if message_api_active:
            test_execution.start()
            state_monitor.start()
            test_execution.join()
            state_monitor.join()
        message_monitor.join()
        termination_ev.set()
        if not ignore_falsification:
            falsification_rollback.undo_falsify_all()
        print('tests completed')


if __name__ == '__main__':
    tests = [TestEntry('create'), TestEntry('build'), TestEntry('stop')]

    test_tests(tests, profile='development')
