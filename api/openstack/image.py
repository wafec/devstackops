import requests
from openstack.util import *


def image_create(conf, container_format, disk_format, name, id, error_callback=None):
    data = {
        'container_format': container_format,
        'disk_format': disk_format,
        'name': name,
        'id': id
    }
    response = requests.post(url=conf.image_url + '/images', json=data, headers=conf.headers)
    return util_handle_response(response, error_callback=error_callback)
