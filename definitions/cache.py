from typing import TypedDict


class Coin(TypedDict):
    amount: float
    coin: str
    id: str


class Inventory(TypedDict):
    amount: float
    investment: float


class Swap_Coin(TypedDict):
    src: Coin
    dest: Coin
    utc_date: str
    wallet: str


DICT_COIN = dict[str, Inventory]
