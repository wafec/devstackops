from openstack.configuration import CommonConfig
from openstack.identity import *
from openstack.image import *


config = CommonConfig.get_instance()
print(identity_token(config, 'admin', 'labstack'))
result = image_create(config, 'bare', 'raw', 'Ubuntu', 'b2173dd3-7ad6-4362-baa6-a68bce3565cb')
print(result)