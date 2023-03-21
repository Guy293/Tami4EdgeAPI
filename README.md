# Tami 4 Edge / Edge+ API in Python
![GitHub release](https://img.shields.io/github/v/release/Guy293/Tami4EdgeAPI)
![workflow](https://github.com/Guy293/Tami4EdgeAPI/actions/workflows/python-publish.yml/badge.svg)

[![tami4.png](https://i.postimg.cc/GhywJQDz/tami4.png)](https://postimg.cc/Tpf4TnCW)

Tami4EdgeAPI can be used to control Strauss'es Tami4 Edge / Edge+ devices.  
You can boil the water, prepare drinks, get information about the filter or UV light  and other information about the device.

## Installing

```sh
pip install Tami4EdgeAPI
```

## Authenticating

You first need to obtain a ``refresh_token`` by requesting an sms code to the phone you registered to the app with.
```py
from Tami4EdgeAPI import Tami4EdgeAPI

# You must add the country code!
phone_number = "+972xxxxxxxxx"

Tami4EdgeAPI.request_otp(phone_number)
otp_code = input("Enter OTP: ")
refresh_token = Tami4EdgeAPI.submit_otp(otp_code)
```
Store the ``refresh_token`` somewhere safe, you will use it to authenticate with the API.

## Usage

```py
edge = Tami4EdgeAPI(refresh_token)
print(f"Bar Name: {edge.device.name}, Firmware Version: {edge.device.device_firmware}")
```

### Boil Water
```py
edge.boil_water()
```

### Get User Drinks
```py
drinks = edge.get_drinks()
for drink in drinks:
  print(drink.name)
```

### Prepare A Drink
```py
edge.prepare_drink(drink)
```

### Get Filter / UV Information
```py
water_quality = edge.get_water_quality()
water_quality.uv.last_replacement
water_quality.uv.upcoming_replacement
water_quality.uv.status
water_quality.filter.milli_litters_passed
```
