import logging
from typing import Callable, Optional

import requests
from pypasser import reCaptchaV3
from requests.auth import AuthBase
from requests.exceptions import JSONDecodeError, RequestException
from requests.models import PreparedRequest

from Tami4EdgeAPI import exceptions
from Tami4EdgeAPI.device import Device
from Tami4EdgeAPI.drink import Drink
from Tami4EdgeAPI.token import Token
from Tami4EdgeAPI.water_quality import UV, Filter, WaterQuality


class _Auth(AuthBase):
    def __init__(self, get_access_token: Callable) -> None:
        self.get_access_token = get_access_token

    def __call__(self, r: PreparedRequest) -> PreparedRequest:
        r.headers["authorization"] = "Bearer " + self.get_access_token()
        return r


def request_wrapper(
    method: str,
    url: str,
    *args,
    session: Optional[requests.Session] = None,
    exception: Exception,
    **kwargs,
) -> requests.models.Response:
    try:
        if session:
            return session.request(method, url, *args, timeout=10, **kwargs)
        else:
            return requests.request(method, url, *args, timeout=10, **kwargs)
    except RequestException as ex:
        raise exception from ex


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
            self._request_new_token()

        return self._token.access_token

    def _request_new_token(self):
        response = request_wrapper(
            "POST",
            f"{Tami4EdgeAPI.ENDPOINT}/public/token/refresh",
            json={"token": self._token.refresh_token},
            exception=exceptions.TokenRefreshFailedException("Token Refresh Failed"),
        )

        if "Invalid refresh token (expired)" in response.text:
            raise exceptions.RefreshTokenExpiredException("Refresh token has expired")

        try:
            response_json = response.json()
        except JSONDecodeError as ex:
            raise exceptions.TokenRefreshFailedException("Token Refresh Failed") from ex

        if "access_token" not in response_json:
            logging.error("Token Refresh Failed, response: %s", response_json)
            raise exceptions.TokenRefreshFailedException(
                "Token Refresh Failed: No access_token key"
            )

        logging.debug("Token Refresh Successful")

        self._token = Token(
            refresh_token=response_json["refresh_token"],
            access_token=response_json["access_token"],
            expires_in=response_json["expires_in"],
        )

    def _get_devices(self) -> list[Device]:
        response = request_wrapper(
            "GET",
            f"{self.ENDPOINT}/api/v1/device",
            session=self._session,
            exception=exceptions.APIRequestFailedException("Device Request Failed"),
        )

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

        response = request_wrapper(
            "GET",
            f"{self.ENDPOINT}/api/v1/customer/drink",
            session=self._session,
            exception=exceptions.APIRequestFailedException("Drink Request Failed"),
        )

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

        response = request_wrapper(
            "GET",
            f"{self.ENDPOINT}/api/v2/customer/waterQuality",
            session=self._session,
            exception=exceptions.APIRequestFailedException(
                "Water Quality Request Failed"
            ),
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

        request_wrapper(
            "POST",
            f"{self.ENDPOINT}/api/v1/device/{self.device.id}/prepareDrink/{drink.id}",
            session=self._session,
            exception=exceptions.APIRequestFailedException(
                "Drink Prepare Request Failed"
            ),
        )

    def boil_water(self) -> None:
        """Boil water."""

        response = request_wrapper(
            "POST",
            f"{self.ENDPOINT}/api/v1/device/{self.device.id}/startBoiling",
            session=self._session,
            exception=exceptions.APIRequestFailedException("Boil Water Request Failed"),
        )

        if response.status_code == 502:
            logging.info("Water is already boiling")

    @staticmethod
    def _get_recaptcha_token() -> str:
        return reCaptchaV3(Tami4EdgeAPI.ANCHOR_URL)

    @staticmethod
    def request_otp(phone_number: str) -> None:
        """Request an OTP code."""

        response = request_wrapper(
            "POST",
            f"{Tami4EdgeAPI.ENDPOINT}/public/phone/generateOTP",
            json={
                "phoneNumber": phone_number,
                "reCaptchaToken": Tami4EdgeAPI._get_recaptcha_token(),
            },
            exception=exceptions.OTPFailedException("OTP Request Failed"),
        ).json()

        if not response["success"]:
            logging.error("OTP Request Failed, response: %s", response)
            raise exceptions.OTPFailedException("OTP Request Failed")

        logging.info("OTP Request Successful")

    @staticmethod
    def submit_otp(phone_number: str, otp: int) -> str:
        """Submit an OTP code."""

        response = request_wrapper(
            "POST",
            f"{Tami4EdgeAPI.ENDPOINT}/public/phone/submitOTP",
            json={
                "phoneNumber": phone_number,
                "code": otp,
                "reCaptchaToken": Tami4EdgeAPI._get_recaptcha_token(),
            },
            exception=exceptions.OTPFailedException("OTP Submission Failed"),
        ).json()

        if "access_token" not in response:
            logging.error("OTP Submission Failed, response: %s", response)
            raise exceptions.OTPFailedException("OTP Submission Failed")

        logging.info("OTP Submission Successful")

        return response["refresh_token"]
