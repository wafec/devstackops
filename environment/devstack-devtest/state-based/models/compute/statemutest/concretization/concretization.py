from yaml import load, FullLoader, YAMLObject
import os


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


def coding_translate_input_name_to_event(inp):
    name = inp.qualifiedName
    if name == 'main.BuildRun':
        return 'compute.create_server'
    elif name == 'main.Shelve':
        return 'compute.shelve_server'
    return None


def coding_translate_input_expectations_to_states(inp, doc):
    states = []
    for expectation in [expectation for expectation in inp.expectedSet if 'GoodTransition' in expectation.qualifiedName]:
        dest_state = expectation.extras['destination']
        if dest_state in doc.states:
            dest_state = doc.states[dest_state]
            if dest_state == 'Created':
                states.append('server_created')
            elif dest_state == 'Running':
                states.append('server_running')
            elif dest_state == 'Shelved':
                states.append('server_shelved')
    return states


def coding_tests_from_test_summary(file_path):
    with open(file_path, 'r') as summary_file:
        doc = load(summary_file, Loader=FullLoader)
    if doc:
        tests = []
        for test in doc.generatedTestCases:
            test_path = os.path.join(os.path.dirname(file_path), test)
            if os.path.exists(test_path):
                t = {'test-case': []}
                with open(test_path, 'r') as test_file:
                    test_object = load(test_file, Loader=FullLoader)
                for inp in test_object.inputSet:
                    if inp.expectedSet is not None:
                        if [e for e in inp.expectedSet if 'GoodTransition' in e.qualifiedName]:
                            i = {
                                'event': coding_translate_input_name_to_event(inp),
                                'states': coding_translate_input_expectations_to_states(inp, doc)
                            }
                            if i['event'] is not None:
                                t['test-case'].append(i)
                tests.append(t)
        return tests


if __name__ == '__main__':
    tests = coding_tests_from_test_summary('../dest/test-summary-Deion.yaml')
    print(tests)
