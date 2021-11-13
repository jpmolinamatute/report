from typing import TypedDict


class Asset(TypedDict):
    id: str
    utc_date: str
    action_type: str
    action_id: str
    coin: str
    amount: float
    investment: float
    wallet: str


RAW_ASSET = tuple[str, str, str, str, str, float, float, str]
