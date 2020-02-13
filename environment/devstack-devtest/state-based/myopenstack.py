#!/usr/bin/env python

import openstack
import json
from collections import Iterable
from pygments import highlight, lexers, formatters
import time
import threading


class TestFunc:
    def __init__(self, test_handler, test, cloud, json_print=False):
        self._test_handler = test_handler
        self._test = test
        self._cloud = cloud
        self._json_print = json_print

    def _get_instance_func(self, instance, name):
        modules = name.split('.')
        if len(modules) > 0 and hasattr(instance, modules[0]):
            instance = getattr(instance, modules[0])
            if len(modules) > 1:
                return self._get_instance_func(instance, '.'.join(modules[1:]))
            return instance
        return None

    def _get_local_func(self, name):
        if self._test.event in globals():
            return globals()[self._test.event]
        return None

    def _parse_args(self):
        kwargs = {}
        if self._test.args:
            for arg in self._test.args:
                kwargs[arg.name] = arg.value
                if isinstance(arg.value, str) and (arg.value.strip().startswith('[') or arg.value.strip().startswith('{')):
                    kwargs[arg.name] = eval(arg.value)
                if arg.value in self._test_handler.instances:
                    kwargs[arg.name] = self._test_handler.instances[arg.value]
                if arg.name.endswith('_id') and hasattr(kwargs[arg.name], 'id'):
                    kwargs[arg.name] = kwargs[arg.name].id
        return kwargs

    def run(self):
        result = None
        conn = openstack.connect(cloud=self._cloud)
        test_func = self._get_instance_func(conn, self._test.event)
        if not test_func:
            test_func = self._get_local_func(self._test.event)
        if test_func:
            print('test-func %s found' % self._test.event)
            args = self._parse_args()
            result = test_func(**args)
            if 'name' in args and result:
                self._test_handler.instances[args['name']] = result
            if self._json_print and result:
                print_result = self._build_print_result(result)
                bw_json = json.dumps(print_result, indent=2, sort_keys=True)
                colorful_json = highlight(bw_json, lexers.JsonLexer(), formatters.TerminalFormatter())
                print(colorful_json)
        else:
            print('test-func %s not found' % self._test.event)
        return result

    def _build_print_result(self, result):
        print_result = None
        if not hasattr(result, 'to_dict'):
            print_result = []
            for res in result:
                print_result.append(self._build_print_result(res))
        else:
            print_result = result.to_dict()
        return print_result


def build_test_func(test_handler, test, cloud, json_print=False):
    test_func = TestFunc(test_handler, test, cloud, json_print=json_print)
    return test_func.run


def build_tests(test_handler, tests, cloud, json_print=False):
    for test in tests:
        test.func = build_test_func(test_handler, test, cloud, json_print)


class StateMonitorException(Exception):
    pass


def st_wait(function, times=100, interval=1):
    def wrapped_function(*args, **kwargs):
        status_ok = False
        counter = 0
        opts = kwargs['opts']
        opts['conn'] = openstack.connect(cloud=opts['cloud'])
        while not status_ok and counter < times:
            try:
                function(*args, **kwargs)
                status_ok = True
            except StateMonitorException:
                status_ok = False
                time.sleep(interval)
            counter = counter + 1
    return wrapped_function


@st_wait
def st_flavor_created(opts):
    test_handler, conn = opts['test_handler'], opts['conn']
    try:
        result = conn.compute.get_flavor(test_handler.current_result)
        if not result:
            raise StateMonitorException('flavor result None')
        print('flavor %s created' % result.id)
    except openstack.exceptions.InvalidRequest:
        raise StateMonitorException('flavor invalid request ')


@st_wait
def st_image_created(opts):
    test_handler, conn = opts['test_handler'], opts['conn']
    try:
        result = conn.image.get_image(test_handler.current_result)
        if not result:
            raise StateMonitorException('image result None')
        print('image %s created' % result.id)
    except openstack.exceptions.InvalidRequest:
        raise StateMonitorException('image invalid request')


@st_wait
def st_server_created(opts):
    test_handler, conn = opts['test_handler'], opts['conn']
    try:
        result = conn.compute.get_server(test_handler.current_result)
        if not result:
            raise StateMonitorException('server result None')
        if result.status and result.status.lower() == 'active':
            print('server state %s' % result.status.lower())
        else:
            print('invalid server state %s' % result.status.lower())
            raise StateMonitorException('invalid server state')
    except openstack.exceptions.InvalidRequest:
        raise StateMonitorException('server invalid request')


@st_wait
def st_volume_created(opts):
    test_handler, conn = opts['test_handler'], opts['conn']
    try:
        result = conn.block_storage.get_volume(test_handler.current_result)
        if not result:
            raise StateMonitorException('volume result None')
        print('volume %s created' % result.id)
    except openstack.exceptions.InvalidRequest:
        raise StateMonitorException('volume invalid request')


class StateMonitorFunction:
    def __init__(self, test_handler, cloud):
        self._cloud = cloud
        self._test_handler = test_handler
        self._lock = threading.Lock()
        self._states_counter = None
        self._states_ev = threading.Event()

    @property
    def current_test(self):
        return self._test_handler.current_test

    def _monitor(self, state):
        print('[%02d] monitor %s' % (self._test_handler.iteration_number, state))
        if ('st_%s' % state.name) in globals():
            print('st_%s found' % state.name)
            func = globals()['st_%s' % state.name]
            opts = { 'cloud': self._cloud, 'test_handler': self._test_handler }
            func(opts=opts)
        else:
            print('st_%s not found' % state.name)
        with self._lock:
            self._states_counter = self._states_counter + 1
            if self._states_counter >= len(self.current_test.states):
                self._states_ev.set()

    def func(self):
        if self.current_test:
            self._states_counter = 0
            self._states_ev.clear()
            for state in self.current_test.states:
                threading.Thread(target=self._monitor, args=(state,)).start()
            self._states_ev.wait()
