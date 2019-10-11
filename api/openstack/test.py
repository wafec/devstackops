from openstack.configuration import CommonConfig
from openstack.identity import *
from openstack.image import *
from openstack.compute import *
import os


UBUNTU_IMG = 'cirros-0.4.0-x86_64-disk.img'


def _test_get_data_resource(name):
    root_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(root_dir, '../data/' + name)


def _test_default_error_callback(http_err, response):
    print(http_err)
    print(response.text)


def _test_identity_token():
    config = CommonConfig.get_instance()
    identity_token(config, 'admin', 'labstack')
    assert(config.token is not None)
    print('Token:', config.token, 'Generated')
    return config


def _test_identity_token_revoke(config, token=None, error_callback=None):
    result = identity_token_revoke(config, token if token else config.token, error_callback=error_callback)
    assert(result is not None)
    print('Token:', token, 'Revoked')


def test_authentication():
    config = _test_identity_token()
    assert(config is not None)
    assert(config.token is not None)


def _test_image_create(config, name='Basic', disk_format='qcow2', container_format='bare', error_callback=None):
    result = image_create(config, container_format=container_format, disk_format=disk_format, name=name, id=None,
                          error_callback=error_callback)
    assert(result is not None)
    print('Image:', result['id'], 'Created')
    return result


def _test_image_delete(config, id, error_callback=None):
    result = image_delete(config, id, error_callback=error_callback)
    assert(result is not None)
    print('Image:', id, 'Deleted')


def _test_image_clear(config, id=None, error_callback=None):
    images = image_list(config, error_callback=error_callback)
    assert(images is not None)
    if id:
        images = [x for x in images['images'] if x['id'] == id]
    else:
        images = images['images']
    for image in images:
        _test_image_delete(config, image['id'], error_callback=error_callback)


def test_image_create():
    config = _test_identity_token()
    _test_image_clear(config)
    result = _test_image_create(config, 'Ubuntu', container_format='bare', disk_format='qcow2',
                                error_callback=_test_default_error_callback)
    _test_image_delete(config, result['id'])
    _test_identity_token_revoke(config, config.token)


def test_image_upload():
    config = _test_identity_token()
    _test_image_clear(config)
    img_result = _test_image_create(config, 'Ubuntu', container_format='bare', disk_format='qcow2')
    file_result = image_upload_file(config, img_result['id'], _test_get_data_resource(UBUNTU_IMG))
    assert(file_result is not None)
    print('File', UBUNTU_IMG, 'Uploaded')
    _test_image_delete(config, img_result['id'])
    _test_identity_token_revoke(config, config.token)


def test_image_list():
    config = _test_identity_token()
    _test_image_clear(config)
    img_result = _test_image_create(config)
    image_upload_file(config, img_result["id"], _test_get_data_resource(UBUNTU_IMG))
    list = image_list(config, error_callback=_test_default_error_callback)
    assert(list is not None)
    _test_image_clear(config)
    _test_identity_token_revoke(config)


def _test_flavor_clear(config, name=None, error_callback=None):
    flavors = compute_flavors(config, error_callback=error_callback)
    assert(flavors is not None)
    if name:
        flavors = [x for x in flavors['flavors'] if x['name'] == name]
        if flavors:
            _test_flavor_delete(config, flavors[0]['id'])
    else:
        for flavor in flavors['flavors']:
            _test_flavor_delete(config, flavor['id'])


def _test_flavor_create(config, name='Basic', ram=256, vcpus=1, disk=0, rxtx_factor=2.0, error_callback=None):
    result = compute_flavor_create(config, name=name, ram=ram, vcpus=vcpus, disk=disk, rxtx_factor=rxtx_factor,
                                   error_callback=error_callback)
    assert(result is not None)
    print('Flavor:', result['flavor']['id'], 'Created')
    return result


def _test_flavor_delete(config, id, error_callback=None):
    result = compute_flavor_delete(config, id, error_callback=error_callback)
    assert (result is not None)
    print('Flavor:', id, 'Deleted')


def test_flavor_create():
    config = _test_identity_token()
    _test_flavor_clear(config, name='Basic')
    flavor = _test_flavor_create(config, name='Basic', ram=256, vcpus=1, disk=0, rxtx_factor=2.0,
                                 error_callback=_test_default_error_callback)
    _test_flavor_delete(config, flavor['flavor']['id'])


def test_flavors():
    config = _test_identity_token()
    _test_flavor_clear(config, name=None)
    flavor = _test_flavor_create(config, name='Basic', ram=256, vcpus=1, disk=0, rxtx_factor=2.0)
    flavors = compute_flavors(config)
    assert(flavors is not None)
    assert(len(flavors['flavors']) == 1)
    _test_flavor_delete(config, flavor['flavor']['id'])
    _test_identity_token_revoke(config, config.token)


def _test_compute_server_delete(config, id, error_callback=None):
    result = compute_server_delete(config, id, error_callback=error_callback)
    assert(result is not None)
    print('Server', id, 'Deleted')


def _test_compute_server_clear(config, name=None, error_callback=None):
    servers = compute_servers(config, error_callback=error_callback)
    assert(servers is not None)
    if name:
        servers = [x for x in servers['servers'] if x['name'] == name]
    else:
        servers = servers['servers']
    for server in servers:
        _test_compute_server_delete(config, server['id'], error_callback=error_callback)


def _test_compute_server_create(config, image_ref, flavor_ref, name, error_callback=None):
    result = compute_server_create(config, name=name, image_ref=image_ref, flavor_ref=flavor_ref,
                                   error_callback=error_callback)
    assert(result is not None)
    print('Server:', result['server']['id'], 'Created')
    return result


def test_server_create():
    config = _test_identity_token()
    _test_compute_server_clear(config)
    _test_flavor_clear(config)
    image = _test_image_create(config)
    image_upload_file(config, image['id'], file_path=_test_get_data_resource(UBUNTU_IMG))
    flavor = _test_flavor_create(config)
    server = _test_compute_server_create(config, image_ref=image['id'], flavor_ref=flavor['flavor']['id'],
                                         name='Test Server', error_callback=_test_default_error_callback)
    assert(server is not None)
    print('Server:', server['server']['id'], 'Created')
    _test_compute_server_clear(config)
    _test_flavor_clear(config)
    _test_image_delete(config, image['id'])
    _test_identity_token_revoke(config, config.token)


def test_server_delete():
    config = _test_identity_token()
    _test_compute_server_clear(config)
    _test_flavor_clear(config)
