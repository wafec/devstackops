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
    def __init__(self, event, args, messages):
        self._event = event
        self._args = args
        self._messages = messages


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


class TestSuiteExecution(threading.Thread):
    def __init__(self, test_handler):
        super(TestSuiteExecution, self).__init__()
        self._test_handler = test_handler

    def run(self):
        self._test_handler.status = TestHandler.STARTED
        for test in self._test_handler.tests:
            print('run test')
            self._test_handler.current_test = test
            time.sleep(2)
            with self._test_handler.execution_cv:
                self._test_handler.execution_cv.notifyAll()
            with self._test_handler.execution_cv:
                print('execution waiting states completion')
                self._test_handler.execution_cv.wait()
            with self._test_handler.execution_cv:
                self._test_handler.status = TestHandler.STARTED if test != self._test_handler.tests[-1] else TestHandler.STOPPED
                self._test_handler.execution_cv.notifyAll()
        print('test-execution finished')
        with self._test_handler.completion_cv:
            self._test_handler.completion_cv.notifyAll()


class StateMonitor(threading.Thread):
    def __init__(self, test_handler):
        super(StateMonitor, self).__init__()
        self._test_handler = test_handler

    def run(self):
        while self._test_handler.status != TestHandler.STOPPED:
            print('monitor waiting test execution')
            with self._test_handler.execution_cv:
                self._test_handler.execution_cv.wait()
            print('monitor states')
            time.sleep(2)
            with self._test_handler.execution_cv:
                self._test_handler.execution_cv.notifyAll()
            with self._test_handler.execution_cv:
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
        server = multiprocessing.Process(target=app.run, kwargs={ 'port': 5052 })
        server.start()
        with self._test_handler.completion_cv:
            self._test_handler.completion_cv.wait()
        server.terminate()
        server.join()
        print('message-monitor terminated')


if __name__ == '__main__':
    rabbitmq.falsify_bindings('localhost', 'admin', 'supersecret')

    test_handler = TestHandler([1, 2, 3, 4, 5])
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