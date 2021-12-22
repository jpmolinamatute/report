import sqlite3
import logging
import csv
import uuid

from datetime import datetime
from os import path, listdir
from typing import Any

from .definitions import ACTION_TYPE


def get_action_type(operation: str) -> ACTION_TYPE:
    action_type: ACTION_TYPE
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
    same_choices = ["ADJUSTMENT", "TRANSFER", "INTEREST", "FEE", "WITHDRAW", "DEPOSIT", "MINING"]
    if operation == "POS savings interest":
        action_type = "INTEREST"
    elif operation in transfer_choices:
        action_type = "TRANSFER"
    elif operation in swap_choices:
        action_type = "SWAP"
    elif operation.upper() in same_choices:
        action_type = operation.upper()  # type: ignore[assignment]
    else:
        raise Exception(f"Error: action '{operation}' is invalid")
    return action_type


def process_raw_data(file_path: str) -> list[dict[str, str]]:
    csv_reader: list[dict[str, str]]
    with open(file_path, mode="r", encoding="utf-8") as csv_file:
        csv_reader = [dict(row.items()) for row in csv.DictReader(csv_file, skipinitialspace=True)]

    return csv_reader


def load_hist_file(csv_dir: str, single_file: str, file_id: int) -> list[dict]:
    file_content = []
    pair = single_file.split("-")[0]
    full_path = path.join(csv_dir, single_file)
    with open(full_path, mode="r", encoding="utf-8") as csv_file:
        reader = csv.reader(csv_file)
        #      0      1    2   3   4       5        6
        # Open time,Open,High,Low,Close,Volume,Close time,Quote asset volume,Number of trades,
        # Taker buy base asset volume,Taker buy quote asset volume,Ignore
        # open_time pair close_time open high low close
        for row in reader:
            file_content.append(
                {
                    "open_time": int(row[0]),
                    "pair": pair,
                    "close_time": int(row[6]),
                    "open": float(row[1]),
                    "high": float(row[2]),
                    "low": float(row[3]),
                    "close": float(row[4]),
                    "file_id": file_id,
                }
            )
    return file_content


def get_epoch(utc_date: str) -> int:
    utc_date = f"{utc_date[:-2]}00"
    date_int = datetime.strptime(utc_date, "%Y-%m-%d %H:%M:%S").timestamp() * 1000
    return int(date_int)


class Collect:
    STABLE_COIN = ("BUSD", "USDT")
    OTHER_BASE_COIN = ("BTC", "ETH", "BNB")
    FIAT_EXCHANGE_RATE = 1.28

    def __init__(self, dbfile: str = "./sqlite2.db") -> None:
        self.conn = sqlite3.connect(
            dbfile, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES
        )
        self.start_db()
        self.logger = logging.getLogger("COLLECT")
        self.history_index_table = "history_index"
        self.actions_table = "actions"
        self.history_table = "history"
        self.track: dict = {}
        self.counter1 = 0
        self.counter2 = 0

    def start_db(self) -> None:
        cursor = self.conn.cursor()
        cursor.execute("PRAGMA foreign_keys = ON;")
        cursor.execute("PRAGMA optimize;")
        self.conn.commit()
        cursor.close()

    def proccess_raw_statement(self, file_list: str) -> None:
        action_list: list[dict] = []
        csv_reader = process_raw_data(file_list)
        for line in csv_reader:
            try:
                datetime.strptime(line["UTC_Time"], "%Y-%m-%d %H:%M:%S")
            except ValueError as err:
                raise ValueError("Incorrect data format, should be %Y-%m-%d %H:%M:%S") from err

            action_list.append(
                {
                    "id": str(uuid.uuid4()),
                    "utc_date": line["UTC_Time"],
                    "action_type": get_action_type(line["Operation"]),
                    "coin": line["Coin"],
                    "amount": float(line["Amount"]),
                    "investment": float(line["Investment"]) if line["Investment"] else 0.00,
                    "wallet": line["Wallet"],
                }
            )

        self.write_data(action_list)
        self.process(action_list)

    def executemany(self, sql_str: str, records) -> None:
        cursor = self.conn.cursor()
        try:
            cursor.executemany(sql_str, records)
            self.conn.commit()
        except sqlite3.OperationalError:
            self.logger.exception(f"'{sql_str}' failed")
            raise
        cursor.close()

    def execute(self, sql_str: str, records) -> None:
        cursor = self.conn.cursor()
        cursor.execute(sql_str, records)
        self.conn.commit()
        cursor.close()

    def query(self, sql_str: str, values: dict) -> Any:
        cursor = self.conn.cursor()
        cursor.execute(sql_str, values)
        rows = cursor.fetchall()
        cursor.close()
        return rows

    def insert(self, sql_str: str, values: dict) -> int:
        cursor = self.conn.cursor()
        cursor.execute(sql_str, values)
        self.conn.commit()
        lastrowid = cursor.lastrowid
        cursor.close()
        return lastrowid

    def write_raw_data(self, records: list[dict]) -> None:
        sql_str = f"""
            INSERT INTO {self.actions_table}_tmp(utc_date, action_type, coin, amount, investment, wallet)
            VALUES(:utc_date, :action_type, :coin, :amount, :investment, :wallet);
        """
        self.executemany(sql_str, records)

    def write_data(self, records: list[dict]) -> None:
        sql_str = f"""
            INSERT INTO {self.actions_table}(id, utc_date, action_type, coin, amount, investment, wallet)
            VALUES(:id, :utc_date, :action_type, :coin, :amount, :investment, :wallet);
        """
        self.executemany(sql_str, records)

    def get_history_id(self, file_name: str) -> int:
        sql_str = f"""
            SELECT id
            FROM {self.history_index_table}
            WHERE file_name = :file_name
        """
        row_id = self.query(sql_str, {"file_name": file_name})
        if row_id:
            result = 0
        else:
            sql_str = f"""
                INSERT INTO {self.history_index_table} (file_name)
                VALUES(:file_name)
            """
            result = self.insert(sql_str, {"file_name": file_name})
        return result

    def write_history(self, history: list[dict]) -> None:
        sql_str = f"""
            INSERT INTO {self.history_table}(open_time, pair, close_time, open, high, low, close, file_id)
            VALUES(:open_time, :pair, :close_time, :open, :high, :low, :close, :file_id);
        """

        self.executemany(sql_str, history)

    def save_history(self, csv_dir) -> None:
        if path.isdir(csv_dir):
            for single_file in listdir(csv_dir):
                file_id = self.get_history_id(single_file)
                if file_id:
                    result = load_hist_file(csv_dir, single_file, file_id)
                    self.write_history(result)
        else:
            raise Exception(f"ERROR: invalid directory '{csv_dir}'")

    def calculate_swap_investment(self, swap: dict) -> float:
        amount = swap["dest"]["amount"]
        coin = swap["dest"]["coin"]
        utc_date = swap["utc_date"]
        if coin not in self.STABLE_COIN:
            utc_date = f"{utc_date[:-2]}00"
            date_int = int(datetime.strptime(utc_date, "%Y-%m-%d %H:%M:%S").timestamp() * 1000)
            price = self.get_price(f"{coin}BUSD", date_int)
            investment = amount * price
            investment = investment * self.FIAT_EXCHANGE_RATE
        else:
            investment = amount * self.FIAT_EXCHANGE_RATE
        return investment

    def get_price(self, pair: str, open_time: int) -> float:
        sql_str = f"""
            SELECT open, high, low, close
            FROM {self.history_table}
            WHERE open_time = :open_time
            AND pair = :pair;
        """

        rows = self.query(sql_str, {"pair": pair, "open_time": open_time})
        if rows:
            row = rows[0]
            result = (row[0] + row[1] + row[2] + row[3]) / 4
        else:
            logging.error(f"ERROR: {pair=} {open_time=} NOT FOUND")
            logging.error(rows)
            result = 0.0
        return result

    def update_row_investment(self, row_id: str, investment: float) -> None:
        sql_str = """
            UPDATE actions
            SET investment = :investment
            WHERE id = :id;
        """
        self.execute(sql_str, {"investment": investment, "id": row_id})

    def add_gain_loss(self, action: dict) -> None:
        sql_str = """
            INSERT INTO actions(id, utc_date, action_type, coin, amount, investment, wallet)
            VALUES(:id, :utc_date, :action_type, :coin, :amount, :investment, :wallet);
        """
        self.execute(sql_str, action)

    def update_investment(self, swap: dict) -> None:
        investment = self.calculate_swap_investment(swap)
        src_id = swap["src"]["id"]
        dest_id = swap["dest"]["id"]
        src_coin = swap["src"]["coin"]
        dest_coin = swap["dest"]["coin"]
        src_amount = swap["src"]["amount"]
        dest_amount = swap["dest"]["amount"]
        utc_date = swap["utc_date"]
        wallet = swap["wallet"]
        self.update_row_investment(src_id, investment * -1)
        self.update_row_investment(dest_id, investment)
        track_investment = self.track[src_coin]["investment"] * (
            (src_amount * -1) / self.track[src_coin]["amount"]
        )
        gain_loss = investment - track_investment
        if gain_loss > 0:
            action_type = "GAIN"
        elif gain_loss < 0:
            action_type = "LOSS"
        if action_type:
            self.add_gain_loss(
                {
                    "id": str(uuid.uuid4()),
                    "utc_date": utc_date,
                    "action_type": action_type,
                    "coin": src_coin,
                    "amount": 0.00,
                    "investment": gain_loss,
                    "wallet": wallet,
                }
            )

        # if src_coin == "ATOM":
        #     self.counter += 1
        #     self.logger.debug(swap["src"])
        #     self.logger.debug("############################################")

        self.track[src_coin]["investment"] -= investment
        self.track[src_coin]["investment"] += gain_loss
        self.track[src_coin]["amount"] += src_amount
        self.track[dest_coin]["investment"] += investment
        self.track[dest_coin]["amount"] += dest_amount

    def process(self, action_list: list[dict]) -> None:
        swap: dict = {}
        for action in action_list:
            coin = action["coin"]
            action_id = action["utc_date"]
            amount = action["amount"]

            if coin not in self.track:
                self.track[coin] = {
                    "amount": 0.0,
                    "investment": 0.0,
                }

            if action["action_type"] in ["DEPOSIT", "WITHDRAW"]:
                self.track[coin]["investment"] += action["investment"]
                self.track[coin]["amount"] += amount
            elif action["action_type"] in ["FEE", "INTEREST", "ADJUSTMENT", "MINING", "TRANSFER"]:
                self.track[coin]["amount"] += amount
            elif action["action_type"] == "SWAP":
                # we process SWAP here
                # we have two rows and we can't control the order of them
                # swap should contain only two transactions

                if action_id not in swap:
                    swap.clear()
                    swap = {action_id: {"utc_date": action["utc_date"], "wallet": action["wallet"]}}
                if coin == "ATOM":
                    self.counter1 += 1
                src_dest = "dest" if amount > 0.0 else "src"
                swap[action_id][src_dest] = {"amount": amount, "coin": coin, "id": action["id"]}

                # we make sure we have the two rows stored in cache
                # if "dest" in swap[action_id] and "src" in swap[action_id]:
                if all(k in swap[action_id] for k in ("dest", "src")):
                    if swap[action_id]["src"]["coin"] == "ATOM":
                        self.counter2 += 1
                    self.update_investment(swap[action_id])
            else:
                raise Exception(f"Unknown action {action['action_type']}")

    def close_db(self) -> None:
        self.conn.close()
