#!/usr/bin/env python

import openstack
import json
from collections import Iterable
from pygments import highlight, lexers, formatters


class TestFunc:
    def __init__(self, test, cloud, json_print=False):
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
        if self._test.event in locals():
            return locals()[self._test.event]
        return None

    def _parse_args(self):
        kwargs = {}
        if self._test.args:
            for arg in self._test.args:
                kwargs[arg.name] = arg.value
        return kwargs

    def run(self):
        conn = openstack.connect(cloud=self._cloud)
        test_func = self._get_instance_func(conn, self._test.event)
        if not test_func:
            test_func = self._get_local_func(self._test.event)
        if test_func:
            print('test-func %s found' % self._test.event)
            args = self._parse_args()
            result = test_func(**args)
            if self._json_print and result:
                print_result = self._build_print_result(result)
                bw_json = json.dumps(print_result, indent=2, sort_keys=True)
                colorful_json = highlight(bw_json, lexers.JsonLexer(), formatters.TerminalFormatter())
                print(colorful_json)
        else:
            print('test-func %s not found' % self._test.event)

    def _build_print_result(self, result):
        print_result = None
        if not hasattr(result, 'to_dict'):
            print_result = []
            for res in result:
                print_result.append(self._build_print_result(res))
        else:
            print_result = result.to_dict()
        return print_result


def build_test_func(test, cloud, json_print=False):
    test_func = TestFunc(test, cloud, json_print=json_print)
    return test_func.run


class Test:
    def __init__(self, event):
        self.event = event
        self.args = None


build_test_func(Test('compute.servers'), 'devstack', True)()
build_test_func(Test('compute.images'), 'devstack', True)()

