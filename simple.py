#!/usr/bin/env python

import sys
import logging
import csv
import re
import uuid
import sqlite3
from os import path
from typing import TypedDict, Optional, Union, Literal
from datetime import datetime
from tools import Op_Id


OPERATION_TYPE = Literal["ADJUSTMENT", "DEPOSIT", "FEE", "INTEREST", "SWAP", "TRANSFER", "WITHDRAW"]
DETAIL_TYPE = Literal["details", "fees", "interest", "operations"]
MISSING_FIAT_INVOLVED = tuple[str, str, str, float]


class Coin(TypedDict):
    amount: float
    coin: str


class Operation_Details(TypedDict, total=False):
    id: str
    op_id: str
    coin: str
    amount: float
    investment: float
    wallet: Optional[str]


class Operations(TypedDict):
    id: str
    utc_date: str
    op_type: OPERATION_TYPE


class Data_Extracted(TypedDict, total=False):
    detail_list: list[Operation_Details]
    operation_list: list[Operations]
    fee_list: Optional[list[Operation_Details]]
    interest_list: Optional[list[Operation_Details]]


class Data_Loaded(TypedDict):
    csv_reader: list[dict[str, str]]
    file_type: int


ALL_OPERATIONS = Union[list[Operation_Details], list[Operations]]

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


def write_data(conn: sqlite3.Connection, records: ALL_OPERATIONS, detail_type: DETAIL_TYPE) -> None:
    sql_str = {
        "details": """
            INSERT INTO operation_details(id, op_id, coin, amount, investment)
            VALUES(:id, :op_id, :coin, :amount, :investment);
        """,
        "fees": """
            INSERT INTO operation_fees(id, op_id, coin, amount)
            VALUES(:id, :op_id, :coin, :amount);
        """,
        "interest": """
            INSERT INTO interest(id, op_id, coin, amount)
            VALUES(:id, :op_id, :coin, :amount);
        """,
        "operations": """
            INSERT INTO operations(id, utc_date, op_type)
            VALUES(:id, :utc_date, :op_type);
        """,
    }

    cursor = conn.cursor()
    logging.debug(sql_str[detail_type])
    cursor.executemany(sql_str[detail_type], records)
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
    dataloaded: Data_Loaded = {}  # type: ignore[typeddict-item]
    with open(file_path, mode="r", encoding="utf-8") as csv_file:
        dataloaded["csv_reader"] = [
            {k: v for k, v in row.items()}
            for row in csv.DictReader(csv_file, skipinitialspace=True)
        ]

    return dataloaded


def process_data_type_2(csv_reader: list[dict[str, str]]) -> Data_Extracted:
    detail_list: list[Operation_Details] = []
    interest_list: list[Operation_Details] = []
    operation_list: list[Operations] = []
    fee_list: list[Operation_Details] = []
    op_id_list: list[Op_Id] = []
    for line in csv_reader:
        try:
            datetime.strptime(line["UTC_Time"], "%Y-%m-%d %H:%M:%S")
        except ValueError as err:
            raise ValueError("Incorrect data format, should be %Y-%m-%d %H:%M:%S") from err
        operation: OPERATION_TYPE
        op_id = str(uuid.uuid4())
        if line["Operation"] == "POS savings interest":
            operation = "INTEREST"
        elif line["Operation"] in ["Withdraw", "transfer_out", "POS savings purchase"]:
            operation = "WITHDRAW"
        elif line["Operation"] in ["Deposit", "transfer_in", "POS savings redemption"]:
            operation = "DEPOSIT"
        elif line["Operation"] in [
            "Small assets exchange BNB",
            "Large OTC trading",
            "Buy",
            "Sell",
        ]:
            operation = "SWAP"
            utc_time = datetime.strptime(line["UTC_Time"], "%Y-%m-%d %H:%M:%S").timestamp()
            op_id = get_op_id(op_id_list, utc_time)
        elif line["Operation"] in ["ADJUSTMENT", "TRANSFER", "INTEREST", "FEE"]:
            operation = line["Operation"]  # type: ignore[assignment]

        if not any(d["id"] == op_id for d in operation_list):
            operation_list.append(
                {
                    "id": op_id,
                    "utc_date": line["UTC_Time"],
                    "op_type": operation,
                }
            )
        if operation == "INTEREST":
            interest_list.append(
                {
                    "id": str(uuid.uuid4()),
                    "op_id": op_id,
                    "coin": line["Coin"],
                    "amount": round(float(line["Change"]), 8),
                }
            )
        elif operation == "FEE":
            fee_list.append(
                {
                    "id": str(uuid.uuid4()),
                    "op_id": op_id,
                    "coin": line["Coin"],
                    "amount": round(float(line["Change"]), 8),
                }
            )
        else:
            if line["Investment"]:
                investment = round(float(line["Investment"]), 8)
            else:
                investment = 0.00
            detail_list.append(
                {
                    "id": str(uuid.uuid4()),
                    "op_id": op_id,
                    "coin": line["Coin"],
                    "amount": round(float(line["Change"]), 8),
                    "investment": investment,
                }
            )
    return {
        "detail_list": detail_list,
        "operation_list": operation_list,
        "interest_list": interest_list,
        "fee_list": fee_list,
    }


def proccess_files(conn: sqlite3.Connection) -> None:
    file_list = [
        "/home/juanpa/Projects/reports/statements/best-binance.csv",
        # "/home/juanpa/Projects/reports/statements/data_type_1.csv",
        # "/home/juanpa/Projects/reports/statements/adjustments.csv",
    ]
    for f in file_list:
        dataloaded = load(f)
        records = process_data_type_2(dataloaded["csv_reader"])
        write_data(conn, records["operation_list"], "operations")
        write_data(conn, records["detail_list"], "details")
        if "fee_list" in records:
            write_data(conn, records["fee_list"], "fees")  # type: ignore[arg-type]
        if "interest_list" in records:
            write_data(conn, records["interest_list"], "interest")  # type: ignore[arg-type]


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
