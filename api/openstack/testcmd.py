import sys
from openstack import test


if __name__ == '__main__':
    if 0 <= len(sys.argv) < 3:
        test_name = sys.argv[1]
        func = getattr(test, test_name)
        if func:
            func()
        else:
            print('Test not found')
    else:
        print('Invalid number of arguments', '(%d)' % len(sys.argv))