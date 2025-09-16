class TokenBackendError(Exception):
    pass


class TokenBackendExpiredToken(TokenBackendError):
    pass
