import requests
from openstack.util import *


def compute_flavor_create(conf, name, ram, vcpus, disk, rxtx_factor, error_callback=None):
    data = {
        'flavor': {
            'name': name,
            'ram': ram,
            'vcpus': vcpus,
            'disk': disk,
            'rxtx_factor': rxtx_factor
        }
    }
    response = requests.post(url=conf.compute_url + '/flavors', json=data, headers=conf.headers)
    return util_handle_response(response, error_callback=error_callback)


def compute_flavor_delete(conf, id, error_callback=None):
    response = requests.delete(url=conf.compute_url + '/flavors/' + id, headers=conf.headers)
    return util_handle_response(response, error_callback=error_callback)


def compute_flavors(conf, error_callback=None):
    response = requests.get(url=conf.compute_url + '/flavors', headers=conf.headers)
    return util_handle_response(response, error_callback=error_callback)


def compute_server_create(conf, name, image_ref, flavor_ref, error_callback=None):
    data = {
        'server': {
            'name': name,
            'imageRef': image_ref,
            'flavorRef': flavor_ref
        }
    }
    response = requests.post(url=conf.compute_url + '/servers', json=data, headers=conf.headers)
    return util_handle_response(response, error_callback=error_callback)


def compute_server_delete(conf, id, error_callback=None):
    response = requests.delete(url=conf.compute_url + '/servers/' + id, headers=conf.headers)
    return util_handle_response(response, error_callback=error_callback)


def compute_servers(conf, error_callback=None):
    response = requests.get(url=conf.compute_url + '/servers', headers=conf.headers)
    return util_handle_response(response, error_callback=error_callback)