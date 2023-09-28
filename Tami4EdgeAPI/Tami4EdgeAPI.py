import logging
from typing import Callable

import requests
from requests.models import PreparedRequest
from requests.exceptions import RequestException

from Tami4EdgeAPI.device import Device
from Tami4EdgeAPI.drink import Drink
from Tami4EdgeAPI.token import Token
from Tami4EdgeAPI.water_quality import UV, Filter, WaterQuality

class Tami4EdgeAPIException(Exception):
    pass

class TokenRefreshFailedException(Tami4EdgeAPIException):
    pass

class APIRequestFailedException(Tami4EdgeAPIException):
    pass

class OTPFailedException(Tami4EdgeAPIException):
    pass

class _Auth(requests.auth.AuthBase):
    def __init__(self, get_access_token: Callable) -> None:
        self.get_access_token = get_access_token

    def __call__(self, r: PreparedRequest) -> PreparedRequest:
        r.headers["authorization"] = "Bearer " + self.get_access_token()
        return r


class Tami4EdgeAPI:
    """Tami4Edge API Interface."""

    ENDPOINT = "https://swelcustomers.strauss-water.com"
    ANCHOR_URL = "https://www.google.com/recaptcha/enterprise/anchor?ar=1&k=6Lf-jYgUAAAAAEQiRRXezC9dfIQoxofIhqBnGisq&co=aHR0cHM6Ly93d3cudGFtaTQuY28uaWw6NDQz&hl=en&v=gWN_U6xTIPevg0vuq7g1hct0&size=invisible&cb=ji0lh9higcza"

    def __init__(self, refresh_token: str) -> None:
        logging.basicConfig(level=logging.INFO)

        self._token = Token(refresh_token=refresh_token)

        self._session = requests.Session()
        self._session.auth = _Auth(self.get_access_token)

        # As of date of writing, /v1/ seems to suppose to support multiple devices,
        # but /v2/ only supports one device.
        # Also, the app doesn't seem to support multiple devices at all.
        # So for now, we'll use the first device we get from the API.
        self.device = self._get_devices()[0]

    def get_access_token(self) -> str:
        """Get the access token, refreshing it if necessary."""

        if not self._token.is_valid:
            logging.debug("Token is invalid, refreshing Token")

            try:
                response = requests.post(
                    f"{Tami4EdgeAPI.ENDPOINT}/public/token/refresh",
                    json={"token": self._token.refresh_token},
                ).json()
            except RequestException as ex:
                raise TokenRefreshFailedException("Token Refresh Failed") from ex

            if "access_token" not in response:
                logging.error("Token Refresh Failed, response: %s", response)
                raise TokenRefreshFailedException("Token Refresh Failed: No access_token")

            logging.debug("Token Refresh Successful")

            self._token = Token(
                refresh_token=response["refresh_token"],
                access_token=response["access_token"],
                expires_in=response["expires_in"],
            )

        return self._token.access_token

    def _get_devices(self) -> list[Device]:
        try:
            response = self._session.get(f"{self.ENDPOINT}/api/v1/device")
        except RequestException as ex:
            raise APIRequestFailedException("Device Request Failed") from ex

        return [
            Device(
                id=d["id"],
                name=d["name"],
                connected=d["connected"],
                psn=d["psn"],
                type=d["type"],
                device_firmware=d["deviceFirmware"],
            )
            for d in response.json()
        ]

    def get_drinks(self) -> list[Drink]:
        """Fetch the drinks."""

        try:
            response = self._session.get(f"{self.ENDPOINT}/api/v1/customer/drink")
        except RequestException as ex:
            raise APIRequestFailedException("Drink Request Failed") from ex

        return [
            Drink(
                id=d["id"],
                name=d["name"],
                settings=d["settings"],
                vessel=d["vessel"],
                include_in_customer_statistics=d["includeInCustomerStatistics"],
                default_drink=d["defaultDrink"],
            )
            for d in response.json()["drinks"]
        ]

    def get_water_quality(self) -> WaterQuality:
        """Fetch the water quality."""

        response = self._session.get(
            f"{self.ENDPOINT}/api/v2/customer/waterQuality"
        ).json()
        _filter = response["filterInfo"]
        uv = response["uvInfo"]
        return WaterQuality(
            uv=UV(
                last_replacement=uv["lastReplacement"],
                upcoming_replacement=uv["upcomingReplacement"],
                status=uv["status"],
            ),
            filter=Filter(
                last_replacement=_filter["lastReplacement"],
                upcoming_replacement=_filter["upcomingReplacement"],
                status=_filter["status"],
                milli_litters_passed=_filter["milliLittersPassed"],
            ),
        )

    def prepare_drink(self, drink: Drink) -> None:
        """Prepare a drink."""
        try:
            self._session.post(
                f"{self.ENDPOINT}/api/v1/device/{self.device.id}/prepareDrink/{drink.id}"
            )
        except RequestException as ex:
            raise APIRequestFailedException("Drink Prepare Request Failed") from ex

    def boil_water(self) -> None:
        """Boil water."""
        try:
            response = self._session.post(
                f"{self.ENDPOINT}/api/v1/device/{self.device.id}/startBoiling"
            )
        except RequestException as ex:
            raise APIRequestFailedException("Boil Water Request Failed") from ex

        if response.status_code == 502:
            logging.info("Water is already boiled")

    @staticmethod
    def _get_recaptcha_token() -> str:
        return reCaptchaV3(Tami4EdgeAPI.ANCHOR_URL)

    @staticmethod
    def request_otp(phone_number: str) -> None:
        """Request an OTP code."""
        try:
            response = requests.post(
                f"{Tami4EdgeAPI.ENDPOINT}/public/phone/generateOTP",
                json={
                    "phoneNumber": phone_number,
                    "reCaptchaToken": Tami4EdgeAPI._get_recaptcha_token(),
                },
            ).json()
        except RequestException as ex:
            raise OTPFailedException("OTP Request Failed") from ex

        if not response["success"]:
            logging.error("OTP Request Failed, response: %s", response)
            raise OTPFailedException("OTP Request Failed")

        logging.info("OTP Request Successful")

    @staticmethod
    def submit_otp(phone_number: str, otp: int) -> str:
        """Submit an OTP code."""
        try:
            response = requests.post(
                f"{Tami4EdgeAPI.ENDPOINT}/public/phone/submitOTP",
                json={
                    "phoneNumber": phone_number,
                    "code": otp,
                    "reCaptchaToken": Tami4EdgeAPI._get_recaptcha_token(),
                },
            ).json()
        except RequestException as ex:
            raise OTPFailedException("OTP Submission Failed") from ex

        if not response["access_token"]:
            logging.error("OTP Submission Failed, response: %s", response)
            raise OTPFailedException("OTP Submission Failed")

        logging.info("OTP Submission Successful")

        return response["refresh_token"]
