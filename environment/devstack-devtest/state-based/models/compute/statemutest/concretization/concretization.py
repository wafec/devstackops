from yaml import load, FullLoader, YAMLObject, Dumper
import os
import json
import yaml


class TestSummary(YAMLObject):
    yaml_tag = '!testSummary'

    def __init__(self):
        pass


class TestCase(YAMLObject):
    yaml_tag = '!testcase'

    def __init__(self):
        pass


class TestInput(YAMLObject):
    yaml_tag = '!input'

    def __init__(self):
        pass


class TestExpectation(YAMLObject):
    yaml_tag = '!expected'

    def __init__(self):
        pass


def coding_insert_pre_test_sequence():
    with open('resources/pre_test.json', 'r') as pre_test_file:
        pre_test = json.load(pre_test_file)
    return pre_test


def coding_translate_input_name_to_event(inp):
    name = inp.qualifiedName
    if name.endswith('BuildRun'):
        return 'compute.create_server'
    elif name.endswith('Shelve'):
        return 'compute.shelve_server'
    elif name.endswith('Unshelve'):
        return 'compute.unshelve_server'
    elif name.endswith('Resize'):
        return 'compute.resize_server'
    elif name.endswith('ResizeConfirm'):
        return 'compute.confirm_server_resize'
    elif name.endswith('ResizeRevert'):
        return 'compute.reverse_server_resize',
    elif name.endswith('Pause'):
        return 'compute.pause_server'
    elif name.endswith("Unpause"):
        return 'compute.unpause_server'
    elif name.endswith('Suspend'):
        return 'compute.suspend_server'
    elif name.endswith('Resume'):
        return 'compute.resume_server'
    elif name.endswith('Shutoff'):
        return 'compute.stop_server'
    elif name.endswith('Start'):
        return 'compute.start_server'
    elif name.endswith('Delete'):
        return 'compute.delete_server'
    return None


def coding_translate_input_expectations_to_state_waits(inp, doc):
    states = []
    for expectation in [expectation for expectation in inp.expectedSet if 'GoodTransition' in expectation.qualifiedName]:
        dest_state = expectation.extras['destination']
        if dest_state in doc.states:
            dest_state = doc.states[dest_state]
            if dest_state.endswith('Created'):
                states.append('server_created')
            elif dest_state.endswith('Running'):
                states.append('server_running')
            elif dest_state.endswith('Shelved'):
                states.append('server_shelved')
            elif dest_state.endswith('Paused'):
                states.append('server_paused')
            elif dest_state.endswith('Stopped'):
                states.append('server_stopped')
            elif dest_state.endswith('Suspended'):
                states.append('server_suspended')
            elif dest_state.endswith('Resized'):
                states.append('server_resized')
    return states


def coding_post_tests_processing(tests):
    if tests:
        for cases in tests:
            for test in cases['test-case']:
                if test['event'].endswith('resize_server'):
                    flavors = [item for item in test['args'] if item['name'] == 'flavor']
                    if flavors:
                        for flavor in flavors:
                            if str(flavor['value']) == '0':
                                flavor['value'] = 'server_test'
                            elif str(flavor['value'] == '1'):
                                flavor['value'] = 'server_test_alt'


def coding_build_test_input(inp, doc, event_name, waits):
    with open('resources/ref_intest.json', 'r') as ref_intest_file:
        intest = json.load(ref_intest_file)
    i = [t for t in intest if t['event'] == event_name][0]
    i['states'] = (i['states'] if i['states'] else []) + ([{'name': state} for state in waits] if waits else [])
    names = []
    result = []
    for value in i['states']:
        if value['name'] not in names:
            names.append(value['name'])
            result.append(value)
    i['states'] = result
    i['is_targeted'] = False
    if event_name == 'compute.resize_server':
        i['args'].append({
            'name': 'flavor',
            'value': inp.args['e_flavor']
        })
    return i


def coding_tests_from_test_summary(file_path):
    with open(file_path, 'r') as summary_file:
        doc = load(summary_file, Loader=FullLoader)
    if doc:
        tests = []
        for test in doc.generatedTestCases:
            test_path = os.path.join(os.path.dirname(file_path), test)
            if os.path.exists(test_path):
                t = {'test-case': [], 'test-name': test}
                for pre_test in coding_insert_pre_test_sequence():
                    t['test-case'].append(pre_test)
                with open(test_path, 'r') as test_file:
                    test_object = load(test_file, Loader=FullLoader)
                for inp in test_object.inputSet:
                    if inp.expectedSet is not None:
                        if [e for e in inp.expectedSet if 'GoodTransition' in e.qualifiedName]:
                            event_name = coding_translate_input_name_to_event(inp)
                            waits = coding_translate_input_expectations_to_state_waits(inp, doc)
                            i = coding_build_test_input(inp, doc, event_name, waits)
                            if i['event'] is not None:
                                t['test-case'].append(i)
                tests.append(t)
        coding_post_tests_processing(tests)
        return tests


if __name__ == '__main__':
    tests = coding_tests_from_test_summary('../dest/test-summary-Wellington.yaml')
    for test in tests:
        with open(test['test-name'], 'w') as test_file:
            yaml.dump({'test-case': test['test-case']}, test_file)
