import requests
from openstack.util import *


def _identity_token_callback(_, response, conf):
    token = response.headers['X-Subject-Token']
    conf.token = token
    return token


def identity_token(conf, user, passwd, project_domain='default', project_name='admin', domain='Default',
                   error_callback=None):
    data = {
        'auth': {
            'identity': {
                'methods': [
                    'password'
                ],
                'password': {
                    'user': {
                        'name': user,
                        'domain': {
                            'name': domain
                        },
                        'password': passwd
                    }
                }
            },
            'scope': {
                'project': {
                    'domain': {
                        'id': project_domain
                    },
                    'name': project_name
                }
            }
        }
    }
    response = requests.post(url=conf.identity_url + '/auth/tokens', json=data)
    return util_handle_response(response, _identity_token_callback, conf=conf, error_callback=error_callback)
