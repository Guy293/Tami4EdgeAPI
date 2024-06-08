from datetime import datetime, timedelta
from typing import Optional


class Token(object):
    refresh_token: str
    access_token: str
    expires_at: Optional[datetime]

    def __init__(
        self,
        refresh_token: str,
        access_token: Optional[str] = None,
        expires_at: Optional[datetime] = None,
    ):
        self.refresh_token = refresh_token
        self.access_token = access_token if access_token else None
        self.expires_at = expires_at

    @property
    def is_valid(self):
        return (
            self.access_token is not None
            and self.expires_at is not None
            and self.expires_at > datetime.now()
        )
