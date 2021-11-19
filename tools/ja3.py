import random
import ssl


class SSLFactory:
    def __init__(self):
        ORIGN_CIPHERS = ('ECDH+AESGCM:DH+AESGCM:ECDH+AES256:DH+AES256:ECDH+AES128:DH+AES:ECDH+HIGH:'
                         'DH+HIGH:ECDH+3DES:DH+3DES:RSA+AESGCM:RSA+AES:RSA+HIGH:RSA+3DES')
        self.ciphers = ORIGN_CIPHERS.split(':')

    def __call__(self, ):
        random.shuffle(self.ciphers)
        ciphers = ":".join(self.ciphers)
        ciphers = ciphers + ":!aNULL:!eNULL:!MD5"

        context = ssl.create_default_context()
        context.set_ciphers(ciphers)
        return context
