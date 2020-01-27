import threading
import multiprocessing
from flask import Flask, request
from flask_restful import Api, Resource
import time
import rabbitmq


class Message(object):
    def __init__(self, name, fields):
        self._name = name
        self._fields = fields


class TestCase(object):
    def __init__(self, event, args=None, messages=None):
        self._event = event
        self._args = args
        self._messages = messages
        self._func = None

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


class TestSuiteExecution(threading.Thread):
    def __init__(self, test_handler):
        super(TestSuiteExecution, self).__init__()
        self._test_handler = test_handler

    def run(self):
        self._test_handler.status = TestHandler.STARTED
        for test in self._test_handler.tests:
            self._test_handler.statem_ev.wait()
            self._test_handler.statem_ev.clear()
            print('run test')
            self._test_handler.current_test = test
            test.func()
            with self._test_handler.execution_cv:
                self._test_handler.execution_cv.notify()
                print('execution waiting states completion')
                self._test_handler.execution_cv.wait()
                self._test_handler.status = TestHandler.STARTED if test != self._test_handler.tests[-1] else TestHandler.STOPPED
                self._test_handler.execution_cv.notify()
        print('test-execution finished')
        with self._test_handler.completion_cv:
            self._test_handler.completion_cv.notify()


class StateMonitor(threading.Thread):
    def __init__(self, test_handler):
        super(StateMonitor, self).__init__()
        self._test_handler = test_handler

    def run(self):
        while self._test_handler.status != TestHandler.STOPPED:
            print('monitor waiting test execution')
            with self._test_handler.execution_cv:
                self._test_handler.statem_ev.set()
                self._test_handler.execution_cv.wait()
                print('monitor states')
                time.sleep(2)
                self._test_handler.execution_cv.notify()
                self._test_handler.execution_cv.wait()
        print('state-monitor stopped')


class MessageMonitorApi(Resource):
    def __init__(self, test_handler):
        self._test_handler = test_handler

    def post(self, body):
        return { 'body': body }


class MessageMonitor(threading.Thread):
    def __init__(self, test_handler):
        super(MessageMonitor, self).__init__()
        self._test_handler = test_handler

    def run(self):
        app = Flask('message-monitor')
        api = Api(app)
        api.add_resource(MessageMonitorApi, '/messages', resource_class_kwargs= { 'test_handler': self._test_handler })
        server = multiprocessing.Process(target=app.run, kwargs={ 'port': 5055 })
        server.start()
        with self._test_handler.completion_cv:
            self._test_handler.completion_cv.wait()
        server.terminate()
        server.join()
        print('message-monitor terminated')


if __name__ == '__main__':
    rabbitmq.falsify_bindings('localhost', 'admin', 'supersecret')

    tests = [TestCase('create'), TestCase('build'), TestCase('stop')]

    test_handler = TestHandler(tests)
    test_execution = TestSuiteExecution(test_handler)
    state_monitor = StateMonitor(test_handler)
    message_monitor = MessageMonitor(test_handler)
    
    test_execution.start()
    state_monitor.start()
    message_monitor.start()

    test_execution.join()
    state_monitor.join()
    message_monitor.join()

    print('tests completed')