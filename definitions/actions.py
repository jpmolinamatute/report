from typing import TypedDict, Literal


class Transaction(TypedDict):
    coin: str
    amount: float
    investment: float
    wallet: Literal["BINANCE", "TREZOR", "DAEDALUS", "PHANTOM"]


class Complex_Transaction(TypedDict):
    date: str
    action_type: Literal["SWAP", "TRANSFER"]
    src: Transaction
    to: Transaction


class Single_Transaction(Transaction):
    date: str
    action_type: Literal["ADJUSTMENT", "DEPOSIT", "FEE", "INTEREST", "WITHDRAW"]
