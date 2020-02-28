import state_based
import myopenstack
import database
import myenv


def tests_test(test_number, experiment_id):
    tests, targets = state_based.tests_from_file('./tests/01-test-test-case.yaml')
    test_id = database.test_add(experiment_id, test_number)
    print(''.join(['-' for _ in range(80)]))
    print('tests test_id=%d, test_number=%d, targets=%s' % (test_id, test_number, repr(targets)))
    print(''.join(['-' for _ in range(80)]))
    myenv.wait_env(test_id)
    test_handler = state_based.TestHandler(tests, test_id, test_number)
    test_handler.targets = targets
    myopenstack.build_tests(test_handler, tests, 'devstack', False)
    state_based.test_tests(tests,
                           profile='local-test',
                           state_monitor_function=myopenstack.StateMonitorFunction(test_handler, 'devstack').func,
                           test_handler=test_handler, ignore_falsification=False)
    myenv.wait_test_finish()
    if len(test_handler.exceptions) > 0:
        print('has exceptions')
        for exception in test_handler.exceptions:
            print(exception)


def tests_test_forever():
    test_number = 2
    experiment_id = 2
    injection_count = database.injection_count_by_test_number(test_number)
    injection_count_aux = None
    while injection_count != injection_count_aux:
        injection_count_aux = injection_count
        print('my-tests having ' + str(injection_count_aux) + ' test(s)')
        tests_test(test_number, experiment_id)
        injection_count = database.injection_count_by_test_number(test_number)
    print('test completed')


def tests_test_once():
    test_number = 1
    experiment_id = 1
    tests_test(test_number, experiment_id)


tests_test_once()
