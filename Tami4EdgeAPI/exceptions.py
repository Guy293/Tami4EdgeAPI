class Tami4EdgeAPIException(Exception):
    pass


class TokenRefreshFailedException(Tami4EdgeAPIException):
    pass


class RefreshTokenExpiredException(TokenRefreshFailedException):
    pass


class APIRequestFailedException(Tami4EdgeAPIException):
    pass


class OTPFailedException(Tami4EdgeAPIException):
    pass
