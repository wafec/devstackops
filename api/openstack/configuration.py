import os


class CommonConfig:
    def __init__(self, controller=None, token=None, protocol=None, identity=None, image=None, compute=None):
        self.controller = controller
        self.token = token
        self.protocol = protocol if protocol else 'http'
        self.identity = identity if identity else '/identity/v3'
        self.compute = compute if compute else '/compute/v2.1'
        self.image = image if image else '/image/v2'

    @staticmethod
    def get_instance():
        controller = os.environ.get('OS_CONTROLLER')
        conf = CommonConfig(controller=controller)
        return conf

    def get_default_url(self, path):
        return self.protocol + '://' + self.controller + path

    @property
    def identity_url(self):
        return self.get_default_url(self.identity)

    @property
    def image_url(self):
        return self.get_default_url(self.image)

    @property
    def compute_url(self):
        return self.get_default_url(self.compute)

    @property
    def headers(self):
        return {
            'X-Auth-Token': self.token,
            'Content-Type': 'application/json'
        }
