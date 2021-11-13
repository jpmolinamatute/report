#!/usr/bin/env python

import sys
import logging
import csv
import uuid
from sqlite3 import Connection
from os import path
from typing import TypedDict, Literal
from datetime import datetime

from tools import startdb


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
    "LOSS",
    "GAIN",
]


class Ations(TypedDict):
    id: str
    utc_date: str
    action_type: ACTION_TYPE
    action_id: str
    coin: str
    amount: float
    investment: float
    wallet: str


def write_data(conn: Connection, records: list[Ations]) -> None:
    sql_str = """
        INSERT INTO actions(id, utc_date, action_type, action_id, coin, amount, investment, wallet)
        VALUES(:id, :utc_date, :action_type, :action_id, :coin, :amount, :investment, :wallet);
    """

    cursor = conn.cursor()
    cursor.executemany(sql_str, records)
    conn.commit()
    cursor.close()


def get_op_id(action_id_list: list[action_ids], action_utc: str) -> str:
    action_id = next(
        (sub["action_id"] for sub in action_id_list if sub["action_utc"] == action_utc), None
    )
    if not action_id:
        action_id = str(uuid.uuid4())
        action_id_list.append(
            {
                "action_id": action_id,
                "action_utc": action_utc,
            }
        )
    return action_id


def load(file_path: str) -> list[dict[str, str]]:
    dataloaded: list[dict[str, str]]
    with open(file_path, mode="r", encoding="utf-8") as csv_file:
        dataloaded = [dict(row.items()) for row in csv.DictReader(csv_file, skipinitialspace=True)]

    return dataloaded


def process_data_type_2(csv_reader: list[dict[str, str]]) -> list[Ations]:
    action_list: list[Ations] = []
    action_id_list: list[action_ids] = []
    for line in csv_reader:
        try:
            datetime.strptime(line["UTC_Time"], "%Y-%m-%d %H:%M:%S")
        except ValueError as err:
            raise ValueError("Incorrect data format, should be %Y-%m-%d %H:%M:%S") from err
        action_type: ACTION_TYPE
        row_id = str(uuid.uuid4())
        action_id = row_id
        transfer_choices = [
            "POS savings purchase",
            "POS savings redemption",
            "transfer_out",
            "transfer_in",
        ]
        swap_choices = [
            "Small assets exchange BNB",
            "Large OTC trading",
            "Buy",
            "Sell",
        ]
        same_choices = ["ADJUSTMENT", "TRANSFER", "INTEREST", "FEE", "WITHDRAW", "DEPOSIT"]
        if line["Operation"] == "POS savings interest":
            action_type = "INTEREST"
        elif line["Operation"] in transfer_choices:
            action_type = "TRANSFER"
        elif line["Operation"] in swap_choices:
            action_type = "SWAP"
        elif line["Operation"].upper() in same_choices:
            action_type = line["Operation"].upper()  # type: ignore[assignment]
        else:
            raise Exception("Error: invalid action type")

        if action_type in ["SWAP", "TRANSFER", "FEE"]:
            action_id = get_op_id(action_id_list, line["UTC_Time"])

        action_list.append(
            {
                "id": row_id,
                "utc_date": line["UTC_Time"],
                "action_type": action_type,
                "action_id": action_id,
                "coin": line["Coin"],
                "amount": round(float(line["Change"]), 8),
                "investment": round(float(line["Investment"]), 8) if line["Investment"] else 0.00,
                "wallet": line["Wallet"],
            }
        )
    return action_list


def proccess_files(conn: Connection) -> None:
    file_list = "/home/juanpa/Projects/reports/statements/best-binance.csv"
    dataloaded = load(file_list)
    records = process_data_type_2(dataloaded)
    write_data(conn, records)


def main() -> None:
    logging.basicConfig(level=logging.DEBUG)
    logging.info(f"Script {path.basename(__file__)} has started")
    conn = startdb()
    proccess_files(conn)
    conn.close()


if __name__ == "__main__":
    try:
        exit_status = 0
        main()
    except KeyboardInterrupt:
        logging.info("Bye!")
    except Exception as e:
        logging.exception(e)
        exit_status = 2
    finally:
        sys.exit(exit_status)
