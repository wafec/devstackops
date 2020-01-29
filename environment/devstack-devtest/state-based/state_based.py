import threading
import multiprocessing
from flask import Flask, request
from flask_restful import Api, Resource
import time
import rabbitmq
import requests
import sys, traceback


class Message(object):
    def __init__(self, name, fields):
        self._name = name
        self._fields = fields


class TestCase(object):
    def __init__(self, event, args=None, messages=None, func=None):
        self._event = event
        self._args = args
        self._messages = messages
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


def assert_message_monitor_is_active(port, attempts=10):
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
        if (not attempts):
            traceback.print_exc(file=sys.stdout)
        if not attempts:
            print('oops! an exception occurred trying to assert whether message-monitor-api is active')
        is_active = False
    if attempts and not is_active:
        time.sleep(0.5)
        is_active = assert_message_monitor_is_active(port, attempts - 1)
    return is_active


if __name__ == '__main__':
    host, user, passwd = ('localhost', 'admin', 'supersecret')
    mapi_port = 5064
    termination_ev = threading.Event()
    rabbitmq.falsify_bindings(host, user, passwd)
    rabbitmq.bind_to_falsified_queues(host, user, passwd, termination_ev, mapi_port)

    tests = [TestCase('create'), TestCase('build'), TestCase('stop')]

    test_handler = TestHandler(tests)
    test_execution = TestSuiteExecution(test_handler)
    state_monitor = StateMonitor(test_handler)
    message_monitor = MessageMonitor(test_handler, mapi_port)

    message_monitor.start()
    is_message_monitor_active = assert_message_monitor_is_active(mapi_port)
    if not is_message_monitor_active:
        with test_handler.completion_cv:
            test_handler.completion_cv.notify()
    if is_message_monitor_active:
        test_execution.start()
        state_monitor.start()

        test_execution.join()
        state_monitor.join()
    message_monitor.join()

    termination_ev.set()

    print('tests completed')