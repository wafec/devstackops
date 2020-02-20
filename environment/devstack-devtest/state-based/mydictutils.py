

def dict_collect_params(parent, path=None, result=None):
    path = path if path is not None else ''
    result = result if result is not None else []
    if parent:
        if isinstance(parent, dict):
            for k in parent.keys():
                dict_collect_params(parent[k], path + ' ' + k, result)
            result.append(path.strip())
        elif isinstance(parent, list) and len(parent) > 0:
            dict_collect_params(parent[0], path + ' $0', result)
            result.append(path.strip())
        else:
            result.append(path.strip())
    else:
        result.append(path.strip())
    return [x for x in result if x]


def dict_param_get_set(subject, path, value=None, method='get'):
    parts = path.split(' ')
    if parts and len(parts) > 0 and subject:
        for part, index in zip(parts, range(len(parts))):
            if part != '$0':
                if subject and isinstance(subject, dict) and part in subject:
                    if index == len(parts) - 1 and method == 'set':
                        print('dict will change %s, %s = %s' % (path, part, subject[part]))
                        subject[part] = value
                    subject = subject[part]
            else:
                if subject and len(subject) > 0:
                    if index == len(parts) - 1 and method == 'set':
                        subject[0] = value
                    subject = subject[0]
    return subject


def dict_param_get(subject, path):
    return dict_param_get_set(subject, path)


def dict_param_set(subject, path, value):
    return dict_param_get_set(subject, path, value, method='set')


def dict_what_type_is_it(value):
    if value is None:
        return 'none'
    if isinstance(value, int) or isinstance(value, float):
        return 'number'
    if isinstance(value, dict):
        return 'dict'
    if isinstance(value, list):
        return 'list'
    if isinstance(value, str):
        return 'string'
    if isinstance(value, bool):
        return 'bool'
    return 'unknown'


if __name__ == '__main__':
    subject = {
        'oslo.message': {
            'args': [
                {
                    'name': 'Wallace'
                }
            ]
        }
    }
    result = dict_collect_params(subject)
    print(result)
    print(dict_param_get_set(subject, result[0]))
    new_value = dict_param_set(subject, result[0], 'José')
    print(new_value)
    print(subject)
    print(dict_param_get(subject, result[1]))
    print(dict_param_get(subject, result[2]))