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


class Message(object):
    def __init__(self, name, fields):
        self.name = name
        self.fields = fields


class Arg(object):
    def __init__(self, name, value):
        self.name = name
        self.value = value


class TestEntry(object):
    def __init__(self, event, args=None, messages=None, func=None):
        self._event = event
        self._args = args if args else []
        self._messages = messages if messages else []
        self._func = func

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


def tests_from_file(filepath):
    if os.path.exists(filepath):
        with open(filepath, 'r') as tests_file:
            tests = yaml.load(tests_file, Loader=yaml.FullLoader)
        test_case = []
        for test in tests['test-case']:
            test_entry = TestEntry(test['event'])
            for arg in test['args']:
                test_entry.args.append(Arg(arg['name'], arg['value']))
            test_case.append(test_entry)
        return test_case
    return None


class TestHandler(object):
    STOPPED = 0
    STARTED = 1
    NONE = 2

    def __init__(self, tests):
        self.tests = tests
        self.current_test = None
        self.execution_cv = threading.Condition()
        self.status = TestHandler.NONE
        self.completion_cv = threading.Condition()
        self.statem_ev = threading.Event()
        self._iteration_number = None

    def start_iteration_counting(self):
        self._iteration_number = 0

    def stop_iteration_counting(self):
        self._iteration_number = None

    def increment_iteration_by_one(self):
        if self._iteration_number is not None:
            self._iteration_number = self._iteration_number + 1

    @property
    def iteration_number(self):
        return 0 if not self._iteration_number else self._iteration_number


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
            test.func()
            with self._test_handler.execution_cv:
                self._test_handler.execution_cv.notify()
                print('[%02d] execution waiting states completion' % self._test_handler.iteration_number)
                self._test_handler.execution_cv.wait()
                self._test_handler.status = TestHandler.STARTED if test != self._test_handler.tests[-1] else TestHandler.STOPPED
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
            print('[%02d] monitor waiting test execution' % self._test_handler.iteration_number)
            with self._test_handler.execution_cv:
                self._test_handler.statem_ev.set()
                self._test_handler.execution_cv.wait()
                print('[%02d] monitor states' % self._test_handler.iteration_number)
                self.func()
                self._test_handler.execution_cv.notify()
                self._test_handler.execution_cv.wait()
        print('state-monitor stopped')


class MessageMonitorApi(Resource):
    def __init__(self, test_handler):
        self._test_handler = test_handler

    def post(self, body):
        return { 'body': body }

    def get(self):
        return 'MessageMonitorApi is active!'


class MessageMonitor(threading.Thread):
    def __init__(self, test_handler, port):
        super(MessageMonitor, self).__init__()
        self._test_handler = test_handler
        self._port = port

    def run(self):
        app = Flask('message-monitor')
        api = Api(app)
        api.add_resource(MessageMonitorApi, '/messages', resource_class_kwargs= { 'test_handler': self._test_handler })
        server = multiprocessing.Process(target=app.run, kwargs={ 'port': self._port })
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


def test_tests(tests, opts_or_file=None, profile=None):
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

    falsification_completed = rabbitmq.falsify_bindings(rmq_host, rmq_user, rmq_passwd)
    if falsification_completed:
        termination_ev = threading.Event()
        rabbitmq.bind_to_falsified_queues(rmq_host, rmq_user, rmq_passwd, termination_ev, message_api_port)

        test_handler = TestHandler(tests)
        test_execution = TestSuiteExecution(test_handler)
        state_monitor = StateMonitor(test_handler)
        message_monitor = MessageMonitor(test_handler, message_api_port)

        message_monitor.start()
        message_api_active = wait_for_message_monitor_api(message_api_port)
        if not message_api_active:
            with test_handler.completion_cv.notify():
                test_handler.completion_cv.notify()
        if message_api_active:
            test_execution.start()
            state_monitor.start()
            test_execution.join()
            state_monitor.join()
        message_monitor.join()
        termination_ev.set()
        print('tests completed')


if __name__ == '__main__':
    tests = [TestEntry('create'), TestEntry('build'), TestEntry('stop')]

    test_tests(tests, profile='development')
