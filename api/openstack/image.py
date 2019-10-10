import requests
from openstack.util import *
import random


def image_create(conf, container_format, disk_format, name, id=None, error_callback=None):
    data = {
        'container_format': container_format,
        'disk_format': disk_format,
        'name': name,
        'id': id
    }
    if not id:
        del data['id']
    response = requests.post(url=conf.image_url + '/images', json=data, headers=conf.headers)
    return util_handle_response(response, error_callback=error_callback)


def image_exists(conf, id, error_callback=None):
    response = requests.get(url=conf.image_url + '/images/' + id, headers=conf.headers)
    parsed = util_handle_response(response, error_callback=error_callback)
    return parsed is not None


def image_delete(conf, id, error_callback=None):
    response = requests.delete(url=conf.image_url + '/images/' + id, headers=conf.headers)
    parsed = util_handle_response(response, error_callback=error_callback)
    return parsed


def image_show(conf, id, error_callback=None):
    response = requests.get(url=conf.image_url + '/images/' + id, headers=conf.headers)
    return util_handle_response(response, error_callback=error_callback)


def image_upload_file(conf, id, file_path, error_callback=None):
    headers = conf.headers
    headers['Content-Type'] = 'application/octet-stream'
    response = requests.put(url=conf.image_url + '/images/' + id + '/file', data=open(file_path, 'rb'), headers=headers)
    return util_handle_response(response, error_callback=error_callback)


def image_get_random_id():
    return random.getrandbits(128)
