from hypothesis import strategies
import math
import sys


def number_none(value):
    return None


def number_not_a_number(value):
    return float('NaN')


def number_absolute_less_one(value):
    return number_absolute(value) - 1


def number_absolute_plus_one(value):
    return number_absolute(value) + 1


def number_absolute(value):
    return math.fabs(value)


def number_value_less_one(value):
    return value - 1


def number_value_plus_one(value):
    return value + 1


def number_max(value):
    return sys.maxsize


def number_min(value):
    return -sys.maxsize


def number_overflow(value):
    return math.inf


def number_underflow(value):
    return -math.inf


def list_none(value):
    return None


def list_empty(value):
    return []


def list_first_element(value):
    return value[0]


def list_remove_first_element(value):
    return value[1:]


def list_duplicate_first_element(value):
    return [value[0]] + value


def dict_none(value):
    return None


def string_none(value):
    return None


def string_empty(value):
    return ''


def string_unprintable(value):
    return strategies.text(strategies.characters(max_codepoint=1000, whitelist_categories=('Cc', 'Cs')),
                           min_size=1).map(lambda s: s.strip()).filter(lambda s: len(s) > 0).example()


def string_value_plus_unprintable(value):
    return value + string_unprintable(value)


def string_alpha(value):
    return strategies.text(strategies.characters(max_codepoint=1000, whitelist_categories=(
        'Nd', 'Nl', 'No', 'Lu', 'Ll', 'Lt'
    )), min_size=1).map(lambda s: s.strip()).filter(lambda s: len(s) > 0).example()


def string_overflow(value):
    return ''.join([str(x)[-1] for x in range(4000)])


def string_predefined(value):
    return 'i hate my job'


def bool_negation(value):
    return not value


def bool_none(value):
    return None


def bool_true(value):
    return True


def bool_false(value):
    return False


def the_operators():
    headers = ['number', 'list', 'dict', 'string', 'bool']
    functions = [f for f in globals() if len(f.split('_')) > 1 and
                 f.split('_')[0] in headers]
    result = {}
    for key in headers:
        result[key] = [{ 'name': f, 'function': globals()[f] } for f in functions if f.split('_')[0] == key]
    return result


if __name__ == '__main__':
    they = the_operators()
    print(they)