import state_based
import myopenstack
import database
import myenv


tests = state_based.tests_from_file('./tests/01-test-test-case.yaml')
test_number = 1
test_id = database.test_add(1, test_number)
print('tests test_id=%d, test_number=%d' % (test_id, test_number))
myenv.wait_env(test_id)
test_handler = state_based.TestHandler(tests, test_id, test_number)
myopenstack.build_tests(test_handler, tests, 'devstack', False)
state_based.test_tests(tests,
                       profile='local-test',
                       state_monitor_function=myopenstack.StateMonitorFunction(test_handler, 'devstack').func,
                       test_handler=test_handler, ignore_falsification=False)
myenv.wait_test_finish()
if len(test_handler.exceptions) > 0:
    for exception in test_handler.exceptions:
        print(exception)