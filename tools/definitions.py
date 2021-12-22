from typing import TypedDict, Literal


class action_ids(TypedDict):
    action_id: str
    action_utc: str


ACTION_TYPE = Literal[
    "ADJUSTMENT",
    "DEPOSIT",
    "WITHDRAW",
    "FEE",
    "INTEREST",
    "SWAP",
    "TRANSFER",
    "MINING",
    "LOSS",
    "GAIN",
]


class Raw_Actions(TypedDict):
    utc_date: str
    action_type: ACTION_TYPE
    coin: str
    amount: float
    investment: float
    wallet: str


class Actions(Raw_Actions):
    id: str
    action_id: str


class Raw_Coin_History(TypedDict):
    open_time: int
    pair: str
    close_time: int
    open: float
    high: float
    low: float
    close: float
    file_id: int


raw_history_list = list[Raw_Coin_History]


RAW_ASSET = tuple[str, str, str, str, str, float, float, str]


class Coin(TypedDict):
    amount: float
    coin: str
    id: str


class Investment(TypedDict):
    amount: float
    investment: float


class Swap(TypedDict):
    src: Coin
    dest: Coin
    utc_date: str
    wallet: str


TRACKED_INVESTMENT = dict[str, Investment]
TRACKED_SWAP = dict[str, Swap]
