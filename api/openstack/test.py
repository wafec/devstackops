from openstack.configuration import CommonConfig
from openstack.identity import *
from openstack.image import *
import os


UBUNTU_IMG = 'ubuntu-16.04-server-cloudimg-amd64-disk1.img'


def _test_get_cloud_resource(name):
    root_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(root_dir, '../cloud/' + name)


def _test_identity_token():
    config = CommonConfig.get_instance()
    identity_token(config, 'admin', 'labstack')
    assert(config.token is not None)
    print('Token:', config.token, 'Generated')
    return config


def _test_identity_token_revoke(config, token, error_callback=None):
    result = identity_token_revoke(config, token, error_callback=error_callback)
    assert(result is not None)
    print('Token:', token, 'Revoked')


def test_authentication():
    config = _test_identity_token()
    assert(config is not None)
    assert(config.token is not None)


def _test_image_create(config, name, disk_format, container_format, error_callback=None):
    result = image_create(config, container_format=container_format, disk_format=disk_format, name=name, id=None,
                          error_callback=error_callback)
    assert(result is not None)
    print('Image:', result['id'], 'Created')
    return result


def _test_image_delete(config, id, error_callback=None):
    result = image_delete(config, id, error_callback=error_callback)
    assert(result is not None)
    print('Image:', id, 'Deleted')


def _test_image_create_error_callback(http_err, response):
    print(http_err)


def test_image_create():
    config = _test_identity_token()
    result = _test_image_create(config, 'Ubuntu', container_format='bare', disk_format='qcow2',
                                error_callback=_test_image_create_error_callback)
    _test_image_delete(config, result['id'])
    _test_identity_token_revoke(config, config.token)


def test_image_upload():
    config = _test_identity_token()
    img_result = _test_image_create(config, 'Ubuntu', container_format='bare', disk_format='qcow2')
    file_result = image_upload_file(config, img_result['id'], _test_get_cloud_resource(UBUNTU_IMG))
    assert(file_result is not None)
    print('File', UBUNTU_IMG, 'Uploaded')
    _test_image_delete(config, img_result['id'])
    _test_identity_token_revoke(config, config.token)