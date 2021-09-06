#!/usr/bin/env python

import sys
import logging
import csv
import re
import uuid
import sqlite3
from os import path
from typing import TypedDict, Optional
from datetime import datetime
from tools import Op_Id


class Coin(TypedDict):
    amount: float
    coin: str


class Coin_Record(TypedDict, total=False):
    id: str
    op_id: str
    coin: str
    change: float
    wallet: Optional[str]


class Operation(TypedDict):
    id: str
    utc_date: str
    name: str


class Data_Loaded(TypedDict):
    csv_reader: list[dict[str, str]]
    file_type: int


class Data_Extracted(TypedDict):
    coin_list: list[Coin_Record]
    payment_list: list[Operation]


# sqlite3.Cursor
def startdb() -> sqlite3.Connection:
    conn = sqlite3.connect(
        "./sqlite2.db", detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES
    )
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON;")
    conn.commit()
    cursor.close()
    return conn


def split_raw_amount_coin(amount_coin: str) -> Coin:
    match = re.search(r"[A-Z]+$", amount_coin)
    result: Optional[Coin] = None
    if match:
        result = {
            "coin": match.group(),
            "amount": round(float(re.sub(r"[A-Z,]+", "", amount_coin)), 8),
        }
    else:
        raise Exception(f"Error: invalid input '{amount_coin}'")
    return result


def write_report_data(conn: sqlite3.Connection, records: list[Coin_Record]) -> None:
    sql_str = """
        INSERT INTO operation_details(id, op_id, coin, change)
        VALUES(:id, :op_id, :coin, :change)
    """
    cursor = conn.cursor()
    cursor.executemany(sql_str, records)
    conn.commit()
    cursor.close()


def write_operation_data(conn: sqlite3.Connection, records: list[Operation]) -> None:
    sql_str = """
        INSERT INTO operation(id, utc_date, name)
        VALUES(:id, :utc_date, :name)
    """
    cursor = conn.cursor()
    cursor.executemany(sql_str, records)
    conn.commit()
    cursor.close()


def get_op_id(op_id_list: list[Op_Id], utc_time: float) -> str:
    op_id_str = ""
    if utc_time in op_id_list:
        for op in op_id_list:
            if op == utc_time:
                op_id_str = op.op_id
    else:
        op_id_str = str(uuid.uuid4())
        op_id_list.append(Op_Id(op_id_str, utc_time))
    return op_id_str


def load(file_path: str) -> Data_Loaded:
    dataloaded: Data_Loaded = {}
    type_1 = "Date(UTC),Pair,Side,Price,Executed,Amount,Fee".split(",")
    type_2 = "UTC_Time,Account,Operation,Coin,Change,Remark".split(",")

    with open(file_path, mode="r", encoding="utf-8") as csv_file:
        dataloaded["csv_reader"] = [
            {k: v for k, v in row.items()}
            for row in csv.DictReader(csv_file, skipinitialspace=True)
        ]

    with open(file_path, mode="r", encoding="utf-8") as f:
        header = f.readline().rstrip().split(",")

    if all(elem in type_1 for elem in header):
        dataloaded["file_type"] = 1
    elif all(elem in type_2 for elem in header):
        dataloaded["file_type"] = 2
    else:
        raise Exception("ERROR: invalid csv file")
    return dataloaded


def process_data_type_1(csv_reader: list[dict[str, str]]) -> Data_Extracted:
    coin_list: list[Coin_Record] = []
    payment_list: list[Operation] = []
    for line in csv_reader:
        if (
            "Date(UTC)" in line
            and "Pair" in line
            and "Side" in line
            and "Price" in line
            and "Executed" in line
            and "Amount" in line
            and "Fee" in line
        ):
            try:
                datetime.strptime(line["Date(UTC)"], "%Y-%m-%d %H:%M:%S")
            except ValueError as err:
                raise ValueError("Incorrect data format, should be %Y-%m-%d %H:%M:%S") from err
            executed = split_raw_amount_coin(line["Executed"])
            amount = split_raw_amount_coin(line["Amount"])
            fee = split_raw_amount_coin(line["Fee"])
            if fee["amount"]:
                fee["amount"] *= -1

            if line["Side"] == "SELL":
                executed["amount"] *= -1
            elif line["Side"] == "BUY":
                amount["amount"] *= -1
            op_id = str(uuid.uuid4())
            utc_date = line["Date(UTC)"]
            operation = line["Side"]
            coin_list.append(
                {
                    "id": str(uuid.uuid4()),
                    "op_id": op_id,
                    "coin": executed["coin"],
                    "change": executed["amount"],
                }
            )
            coin_list.append(
                {
                    "id": str(uuid.uuid4()),
                    "op_id": op_id,
                    "coin": amount["coin"],
                    "change": amount["amount"],
                }
            )
            coin_list.append(
                {
                    "id": str(uuid.uuid4()),
                    "op_id": op_id,
                    "coin": fee["coin"],
                    "change": fee["amount"],
                }
            )
            payment_list.append(
                {
                    "id": op_id,
                    "utc_date": utc_date,
                    "name": operation,
                }
            )
    return {"coin_list": coin_list, "payment_list": payment_list}


def process_data_type_2(csv_reader: list[dict[str, str]]) -> Data_Extracted:
    coin_list: list[Coin_Record] = []
    payment_list: list[Operation] = []
    op_id_list: list[Op_Id] = []
    for line in csv_reader:
        if line["Account"] == "Spot" and line["Operation"] not in [
            "Sell",
            "Buy",
            "Transaction Related",
            "Fee",
        ]:
            try:
                datetime.strptime(line["UTC_Time"], "%Y-%m-%d %H:%M:%S")
            except ValueError as err:
                raise ValueError("Incorrect data format, should be %Y-%m-%d %H:%M:%S") from err
            operation = ""
            op_id = str(uuid.uuid4())
            if line["Operation"] == "POS savings interest":
                operation = "INTEREST"
            elif line["Operation"] in ["Withdraw", "transfer_out", "POS savings purchase"]:
                operation = "WITHDRAW"
            elif line["Operation"] in ["transfer_in", "Deposit", "POS savings redemption"]:
                operation = "DEPOSIT"
            elif line["Operation"] in ["Small assets exchange BNB", "Large OTC trading"]:
                operation = "CONVERTION"
                utc_time = datetime.strptime(line["UTC_Time"], "%Y-%m-%d %H:%M:%S").timestamp()
                op_id = get_op_id(op_id_list, utc_time)
            elif line["Operation"] == "ADJUSTMENT":
                operation = "ADJUSTMENT"

            if not any(d["id"] == op_id for d in payment_list):
                payment_list.append(
                    {
                        "id": op_id,
                        "utc_date": line["UTC_Time"],
                        "name": operation,
                    }
                )
            coin_list.append(
                {
                    "id": str(uuid.uuid4()),
                    "op_id": op_id,
                    "coin": line["Coin"],
                    "change": round(float(line["Change"]), 8),
                }
            )
    return {"coin_list": coin_list, "payment_list": payment_list}


def main() -> None:
    logging.basicConfig(level=logging.DEBUG)
    logging.info(f"Script {path.basename(__file__)} has started")
    file_list = [
        "/home/juanpa/Projects/reports/statements/uptodate-04-sep-2021.csv",
        "/home/juanpa/Projects/reports/statements/2021-04-11-2021-09-03.csv",
        "/home/juanpa/Projects/reports/statements/adjustments.csv",
    ]
    conn = startdb()
    for f in file_list:
        dataloaded = load(f)
        if dataloaded["file_type"] == 1:
            records = process_data_type_1(dataloaded["csv_reader"])
        elif dataloaded["file_type"] == 2:
            records = process_data_type_2(dataloaded["csv_reader"])
        write_operation_data(conn, records["payment_list"])
        write_report_data(conn, records["coin_list"])

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
