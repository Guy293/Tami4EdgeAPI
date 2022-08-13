from dataclasses import dataclass


@dataclass
class Drink(object):
    id: str
    name: str
    settings: list[str]
    vessel: str
    include_in_customer_statistics: bool
    default_drink: bool
