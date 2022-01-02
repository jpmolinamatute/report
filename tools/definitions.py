from typing import TypedDict, Literal

from .db import Actions


SWAP_KEYS = Literal["dest", "src"]


class Swap(TypedDict):
    dest: Actions
    src: Actions


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
