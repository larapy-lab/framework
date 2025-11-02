class EncryptionException(Exception):
    pass


class DecryptionException(Exception):
    pass


class InvalidKeyException(EncryptionException):
    pass


class InvalidPayloadException(DecryptionException):
    pass
