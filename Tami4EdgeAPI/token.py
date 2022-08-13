from datetime import datetime, timedelta


class Token(object):
    access_token: str
    refresh_token: str
    expires_at: datetime

    def __init__(
        self, refresh_token: str, access_token: str = None, expires_in: int = None
    ):
        self.refresh_token = refresh_token
        self.access_token = access_token if access_token else None
        self.expires_at = (
            datetime.now() + timedelta(seconds=expires_in) if expires_in else None
        )

    @property
    def is_valid(self):
        return self.access_token is not None and self.expires_at > datetime.now()
