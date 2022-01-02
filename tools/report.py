import logging
import csv
from datetime import datetime
import base64

from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
import requests
from prettytable import PrettyTable

from .db import Actions
from .definitions import ACTION_TYPE, SWAP_KEYS, Swap


def process_raw_data(file_path: str) -> list[dict[str, str]]:
    csv_reader: list[dict[str, str]]
    with open(file_path, mode="r", encoding="utf-8") as csv_file:
        csv_reader = [dict(row.items()) for row in csv.DictReader(csv_file, skipinitialspace=True)]

    return csv_reader


def cast_to_float(number, precision: int) -> float:
    return round(float(number), precision)


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


class Report:
    FIAT_EXCHANGE_RATE = 1.28

    def __init__(self) -> None:
        engine = create_engine(
            "postgresql+psycopg2://juanpa:@localhost/report", logging_name="postgresqlt-conn", echo=False
        )
        Session = sessionmaker(bind=engine)
        self.conn = Session()
        self.logger = logging.getLogger("REPORT")
        self.track: dict = {}
        self.binance_url = "https://api.binance.com"

    def load_raw_statement(self, file_list: str) -> None:
        action_list: list[Actions] = []
        csv_reader = process_raw_data(file_list)
        for line in csv_reader:
            try:
                row_date = datetime.strptime(line["UTC_Time"], "%Y-%m-%d %H:%M:%S")
            except ValueError as err:
                raise ValueError("Incorrect data format, should be %Y-%m-%d %H:%M:%S") from err
            action_id = base64.b64encode(line["UTC_Time"].encode("utf-8"))
            action_list.append(
                Actions(
                    utc_date=row_date,
                    action_type=get_action_type(line["Operation"]),
                    coin=line["Coin"],
                    action_id=action_id,
                    amount=cast_to_float(line["Amount"], 8),
                    investment=cast_to_float(line["Investment"], 2) if line["Investment"] else 0.00,
                    wallet=line["Wallet"],
                )
            )

        self.conn.add_all(action_list)
        self.conn.commit()

    def update_investment(self, swap: Swap) -> None:
        src_coin = swap["src"].coin
        dest_coin = swap["dest"].coin
        src_amount = swap["src"].amount
        dest_amount = swap["dest"].amount
        track_investment = self.track[src_coin]["investment"] * ((src_amount * -1) / self.track[src_coin]["amount"])
        if track_investment < 0:
            self.logger.debug(f"{track_investment=}")
            self.logger.debug(f"{self.track[src_coin]['investment']=}")
            self.logger.debug((src_amount * -1) / self.track[src_coin]["amount"])
            self.logger.debug("=====================================================================")
        self.track[src_coin]["amount"] += src_amount
        self.track[dest_coin]["amount"] += dest_amount
        self.track[src_coin]["investment"] -= track_investment
        self.track[dest_coin]["investment"] += track_investment
        swap["src"].investment = track_investment * -1
        swap["dest"].investment = track_investment
        self.conn.commit()

    def get_current_price(self, sess: requests.Session, coin: str) -> float:
        if coin == "BUSD":
            current_price = self.FIAT_EXCHANGE_RATE
        else:
            raw_response = sess.get(f"{self.binance_url}/api/v3/avgPrice?symbol={coin}BUSD")
            raw_response.raise_for_status()
            json_response = raw_response.json()
            current_price = cast_to_float(float(json_response["price"]) * self.FIAT_EXCHANGE_RATE, 2)
        return current_price

    def process(self) -> None:
        swap: dict[str, Swap] = {}
        for data in self.conn.query(Actions).order_by(Actions.utc_date).all():
            if data.coin not in self.track:
                self.track[data.coin] = {
                    "amount": 0.0,
                    "investment": 0.0,
                }

            if data.action_type in ["DEPOSIT", "WITHDRAW", "ADJUSTMENT"]:
                self.track[data.coin]["investment"] += data.investment
                self.track[data.coin]["amount"] += data.amount
            elif data.action_type in ["FEE", "INTEREST", "MINING", "TRANSFER"]:
                self.track[data.coin]["amount"] += data.amount
            elif data.action_type == "SWAP":
                # we process SWAP here
                # we have two rows and we can't control the order of them
                # swap should contain only two transactions

                if data.action_id not in swap:
                    swap.clear()
                    swap = {data.action_id: {}}
                src_dest: SWAP_KEYS = "dest" if data.amount > 0.0 else "src"
                swap[data.action_id][src_dest] = data

                # we make sure we have the two rows stored in cache
                # if "dest" in swap[action_id] and "src" in swap[action_id]:
                if all(k in swap[data.action_id] for k in ("dest", "src")):
                    self.update_investment(swap[data.action_id])
            else:
                raise Exception(f"Unknown action {data.action_type}")

    def get_portfolio(self) -> None:
        all_values = 0.0
        actual_investment = 0.0
        table = PrettyTable()
        table.field_names = [
            "time",
            "investment",
            "coin",
            "amount",
            "current_price",
            "current_value",
            "min_price",
            "difference",
        ]
        with requests.Session() as sess:
            query = self.conn.query(
                Actions.coin,
                func.sum(Actions.amount),
                func.sum(Actions.investment),
            )
            query = query.add_columns(func.sum(Actions.investment) / func.sum(Actions.amount))
            query = query.group_by(Actions.coin)
            query = query.having(func.sum(Actions.amount) > 0)

            for item in query.all():
                current_price = self.get_current_price(sess, item[0])
                now = datetime.now()
                current_value = cast_to_float(current_price * item[1], 2)
                all_values += current_value
                table.add_row(
                    [
                        now.strftime("%H:%M:%S %d/%b/%Y"),
                        cast_to_float(item[2], 2),  # investment
                        item[0],  # coin
                        cast_to_float(item[1], 8),  # amount
                        current_price,
                        current_value,
                        cast_to_float(item[3], 2),  # min_price
                        cast_to_float(current_value - item[2], 2),  # difference
                    ]
                )
        table.add_row(
            [
                "-",
                actual_investment,
                "-",
                "-",
                "-",
                round(all_values, 3),
                "-",
                round(all_values - actual_investment, 3),
            ]
        )
        print(table)

    def close(self) -> None:
        self.conn.close()
