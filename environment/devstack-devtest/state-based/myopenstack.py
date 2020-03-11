#!/usr/bin/env python
from pickle import _dump

import openstack
import json
from collections import Iterable
from pygments import highlight, lexers, formatters
import time
import threading
import database
import datetime


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


def _st_try_log_states(opts, prev_msg_list):
    if 'test_handler' in opts:
        test_handler = opts['test_handler']
        if 'server_test' in test_handler.instances:
            server_test = test_handler.instances['server_test']
            test_id = test_handler.test_id
            conn = opts['conn']
            try:
                result = conn.compute.get_server(server_test)
                if result:
                    msg = _tests_events_log_state(result, test_id, prev_msg_list[-1] if prev_msg_list else None)
                    prev_msg_list.append(msg)
            except openstack.exceptions.InvalidRequest:
                pass
            except openstack.exceptions.ResourceNotFound:
                msg = 'server not found'
                if not prev_msg_list or msg != prev_msg_list[-1]:
                    database.logs_add('tests_events', msg, test_id)
                    prev_msg_list.append(msg)


def st_wait(times=20, interval=1):
    def st_wait_wrapper(function):
        def wrapped_function(*args, **kwargs):
            status_ok = False
            exc = None
            counter = 0
            prev_msg_list = []
            opts = kwargs['opts']
            opts['conn'] = openstack.connect(cloud=opts['cloud'])
            start_time = datetime.datetime.now()
            while not status_ok and counter < times:
                _st_try_log_states(opts, prev_msg_list)
                try:
                    function(*args, **kwargs)
                    status_ok = True
                    exc = None
                except StateMonitorException as state_exc:
                    status_ok = False
                    exc = state_exc
                    time.sleep(interval)
                counter = counter + 1
            if 'test_handler' in opts:
                end_time = datetime.datetime.now()
                secs = (end_time - start_time).total_seconds()
                msg = 'test status: %s, time: %s, error: %s' % (
                    'PASS' if status_ok else 'FAIL',
                    '%s secs' % secs,
                    repr(exc) if not status_ok else 'NO_ERROR'
                )
                database.logs_add('tests_events', msg, opts['test_handler'].test_id)
                _st_try_log_states(opts, prev_msg_list)
            return status_ok, exc
        return wrapped_function
    return st_wait_wrapper


@st_wait()
def st_flavor_created(opts):
    test_handler, conn = opts['test_handler'], opts['conn']
    try:
        result = conn.compute.get_flavor(test_handler.current_result)
        if not result:
            raise StateMonitorException('flavor result None')
        print('flavor %s created' % result.id)
        database.logs_add('st_flavor', 'flavor created', test_handler.test_id)
    except openstack.exceptions.InvalidRequest:
        database.logs_add('st_flavor', 'flavor invalid request', test_handler.test_id)
        raise StateMonitorException('flavor invalid request ')


@st_wait()
def st_image_created(opts):
    test_handler, conn = opts['test_handler'], opts['conn']
    try:
        result = conn.image.get_image(test_handler.current_result)
        if not result:
            raise StateMonitorException('image result None')
        print('image %s created' % result.id)
        database.logs_add('st_image', 'image created', test_handler.test_id)
    except openstack.exceptions.InvalidRequest:
        database.logs_add('st_image', 'image invalid request', test_handler.test_id)
        raise StateMonitorException('image invalid request')


def _dump_invalid_server_status(result):
    return 'invalid server state (status=%s, task=%s, power=%s, vm=%s)' % (
          result.status.lower(), result.task_state, str(result.power_state), result.vm_state)


def _tests_events_log_state(result, test_id, last_msg=None):
    msg = 'power=%s, vm=%s, task=%s, status=%s' % (result.power_state, result.vm_state, result.task_state, result.status)
    if msg != last_msg:
        database.logs_add('tests_events', msg, test_id)
    return msg


@st_wait(times=120)
def st_server_created(opts):
    test_handler, conn = opts['test_handler'], opts['conn']
    try:
        result = conn.compute.get_server(test_handler.current_result)
        if not result:
            raise StateMonitorException('server result None')
        if result.status and result.status.lower() == 'active':
            print('server state %s' % result.status.lower())
            database.logs_add('st_server', 'correct server state %s' % result.status.lower(), test_handler.test_id)
        else:
            print('invalid server state (status=%s, task=%s, power=%s, vm=%s)' % (result.status.lower(), result.task_state, str(result.power_state), result.vm_state))
            database.logs_add('st_server', 'invalid server state (status=%s, task_state=%s, power_state=%s, vm_state=%s)' % (
                result.status, result.task_state, result.power_state, result.vm_state
            ), test_handler.test_id)
            raise StateMonitorException('invalid server state')
    except openstack.exceptions.InvalidRequest:
        database.logs_add('st_server', 'invalid server request', test_handler.test_id)
        raise StateMonitorException('server invalid request')


@st_wait()
def st_volume_created(opts):
    test_handler, conn = opts['test_handler'], opts['conn']
    try:
        result = conn.block_storage.get_volume(test_handler.current_result)
        if not result:
            raise StateMonitorException('volume result None')
        if result.status == 'available':
            print('volume %s created' % result.id)
            database.logs_add('st_volume', 'volume created', test_handler.test_id)
        else:
            raise StateMonitorException('invalid volume status %s' % result.status)
    except openstack.exceptions.InvalidRequest:
        database.logs_add('st_volume', 'volume invalid request', test_handler.test_id)
        raise StateMonitorException('volume invalid request')


@st_wait()
def st_volume_attached(opts):
    test_handler, conn = opts['test_handler'], opts['conn']
    try:
        result = conn.block_storage.get_volume(test_handler.instances['volume_test'])
        if result.status == 'in-use':
            print('volume status %s' % result.status)
        else:
            raise StateMonitorException('invalid volume state %s' % result.status)
    except openstack.exceptions.InvalidRequest:
        raise StateMonitorException('volume invalid request')


@st_wait(times=120)
def st_server_shelved(opts):
    test_handler, conn = opts['test_handler'], opts['conn']
    try:
        result = conn.compute.get_server(test_handler.instances['server_test'])
        if result.status.lower() == 'shelved_offloaded':
            print('server shelved %s' % result.id)
        else:
            print(_dump_invalid_server_status(result))
            database.logs_add('st_server', _dump_invalid_server_status(result), test_handler.test_id)
            raise StateMonitorException('invalid server state')
    except openstack.exceptions.InvalidRequest:
        raise StateMonitorException('server shelving invalid request')


@st_wait(times=120)
def st_server_unshelved(opts):
    test_handler, conn = opts['test_handler'], opts['conn']
    try:
        result = conn.compute.get_server(test_handler.instances['server_test'])
        if result.status.lower() == 'active':
            print('server active %s' % result.id)
        else:
            print(_dump_invalid_server_status(result))
            database.logs_add('st_server', _dump_invalid_server_status(result), test_handler.test_id)
            raise StateMonitorException('invalid server state')
    except openstack.exceptions.InvalidRequest:
        raise StateMonitorException('server unshelving invalid request')


@st_wait()
def st_server_paused(opts):
    test_handler, conn = opts['test_handler'], opts['conn']
    try:
        result = conn.compute.get_server(test_handler.instances['server_test'])
        if result.status.lower() == 'paused':
            print('server paused %s' % result.id)
        else:
            print(_dump_invalid_server_status(result))
            database.logs_add('st_server', _dump_invalid_server_status(result), test_handler.test_id)
            raise StateMonitorException('invalid server state')
    except openstack.exceptions.InvalidRequest:
        raise StateMonitorException('server pausing invalid request')


@st_wait()
def st_server_unpaused(opts):
    test_handler, conn = opts['test_handler'], opts['conn']
    try:
        result = conn.compute.get_server(test_handler.instances['server_test'])
        if result.status.lower() == 'active':
            print('server unpaused %s' % result.id)
        else:
            print(_dump_invalid_server_status(result))
            database.logs_add('st_server', _dump_invalid_server_status(result), test_handler.test_id)
            raise StateMonitorException('invalid server state')
    except openstack.exceptions.InvalidRequest:
        raise StateMonitorException('server unpausing invalid request')


@st_wait()
def st_server_suspended(opts):
    test_handler, conn = opts['test_handler'], opts['conn']
    try:
        result = conn.compute.get_server(test_handler.instances['server_test'])
        if result.status.lower() == 'suspended':
            print('server suspended %s' % result.id)
        else:
            print(_dump_invalid_server_status(result))
            database.logs_add('st_server', _dump_invalid_server_status(result), test_handler.test_id)
            raise StateMonitorException('invalid server state')
    except openstack.exceptions.InvalidRequest:
        raise StateMonitorException('server suspending invalid request')


@st_wait()
def st_server_resumed(opts):
    test_handler, conn = opts['test_handler'], opts['conn']
    try:
        result = conn.compute.get_server(test_handler.instances['server_test'])
        if result.status.lower() == 'active':
            print('server resumed %s' % result.id)
        else:
            print(_dump_invalid_server_status(result))
            database.logs_add('st_server', _dump_invalid_server_status(result), test_handler.test_id)
            raise StateMonitorException('invalid server state')
    except openstack.exceptions.InvalidRequest:
        raise StateMonitorException('server resuming invalid request')


@st_wait(times=180)
def st_server_resized(opts):
    test_handler, conn = opts['test_handler'], opts['conn']
    try:
        result = conn.compute.get_server(test_handler.instances['server_test'])
        if result.status.lower() == 'verify_resize':
            print('server resized %s' % result.id)
        else:
            print(_dump_invalid_server_status(result))
            database.logs_add('st_server', _dump_invalid_server_status(result), test_handler.test_id)
            raise StateMonitorException('invalid server state')
    except openstack.exceptions.InvalidRequest:
        raise StateMonitorException('server resizing invalid request')


@st_wait(times=120)
def st_server_resize_confirmed(opts):
    test_handler, conn = opts['test_handler'], opts['conn']
    try:
        result = conn.compute.get_server(test_handler.instances['server_test'])
        if result.status.lower() == 'active':
            print('server resize confirmed %s' % result.id)
        else:
            print(_dump_invalid_server_status(result))
            database.logs_add('st_server', _dump_invalid_server_status(result), test_handler.test_id)
            raise StateMonitorException('invalid server state')
    except openstack.exceptions.InvalidRequest:
        raise StateMonitorException('server resize confirming invalid request')


@st_wait(times=120)
def st_server_resize_reverted(opts):
    test_handler, conn = opts['test_handler'], opts['conn']
    try:
        result = conn.compute.get_server(test_handler.instances['server_test'])
        if result.status.lower() == 'active':
            print('server resize reverted %s' % result.id)
        else:
            print(_dump_invalid_server_status(result))
            database.logs_add('st_server', _dump_invalid_server_status(result), test_handler.test_id)
            raise StateMonitorException('invalid server state')
    except openstack.exceptions.InvalidRequest:
        raise StateMonitorException('server resize reverting invalid request')


@st_wait(times=120)
def st_server_stopped(opts):
    test_handler, conn = opts['test_handler'], opts['conn']
    try:
        result = conn.compute.get_server(test_handler.instances['server_test'])
        if result.status.lower() == 'shutoff':
            print('server stopped %s' % result.id)
        else:
            print(_dump_invalid_server_status(result))
            database.logs_add('st_server', _dump_invalid_server_status(result), test_handler.test_id)
            raise StateMonitorException('invalid server state')
    except openstack.exceptions.InvalidRequest:
        raise StateMonitorException('server stopping invalid request')


@st_wait(times=120)
def st_server_started(opts):
    test_handler, conn = opts['test_handler'], opts['conn']
    try:
        result = conn.compute.get_server(test_handler.instances['server_test'])
        if result.status.lower() == 'active':
            print('server started %s' % result.id)
        else:
            print(_dump_invalid_server_status(result))
            database.logs_add('st_server', _dump_invalid_server_status(result), test_handler.test_id)
            raise StateMonitorException('invalid server state')
    except openstack.exceptions.InvalidRequest:
        raise StateMonitorException('server starting invalid request')


@st_wait(times=120)
def st_server_deleted(opts):
    test_handler, conn = opts['test_handler'], opts['conn']
    try:
        result = conn.compute.get_server(test_handler.instances['server_test'])
        print(_dump_invalid_server_status(result))
        database.logs_add('st_server', _dump_invalid_server_status(result), test_handler.test_id)
        raise StateMonitorException('invalid server state')
    except openstack.exceptions.ResourceNotFound:
        print('server deleted')
        pass
    except openstack.exceptions.InvalidRequest:
        raise StateMonitorException('server deleting invalid request')


class StateMonitorFunction:
    def __init__(self, test_handler, cloud):
        self._cloud = cloud
        self._test_handler = test_handler
        self._lock = threading.Lock()
        self._states_counter = None
        self._states_ev = threading.Event()
        self._result = None

    @property
    def current_test(self):
        return self._test_handler.current_test

    def _monitor(self, state):
        print('[%02d] state-monitor %s "state"' % (self._test_handler.iteration_number, state))
        if ('st_%s' % state.name) in globals():
            print('st_%s found' % state.name)
            func = globals()['st_%s' % state.name]
            opts = { 'cloud': self._cloud, 'test_handler': self._test_handler }
            self._result = func(opts=opts)
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
        return self._result
