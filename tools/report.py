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
    STABLE_COINS = ["BUSD", "USDT"]

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
            investment = cast_to_float(line["Investment"], 2) if "Investment" in line and line["Investment"] else 0.00
            action_list.append(
                Actions(
                    utc_date=row_date,
                    action_type=get_action_type(line["Operation"]),
                    coin=line["Coin"],
                    action_id=action_id,
                    amount=cast_to_float(line["Amount"], 8),
                    investment=investment,
                    wallet=line["Wallet"],
                )
            )

        self.conn.add_all(action_list)
        self.conn.commit()

    def get_swap_percentage(self, action: Actions) -> float:
        src_coin = action.coin
        src_amount = cast_to_float(action.amount * -1, 8)

        self.logger.debug(f"{self.track[src_coin]['amount']} {src_amount}")
        if self.track[src_coin]["amount"] < src_amount:
            percentage = 1.0
        elif self.track[src_coin]["amount"] > 0.0:
            percentage = src_amount / self.track[src_coin]["amount"]
        else:
            percentage = 0.0

        return percentage

    def get_actual_investment(self) -> float:
        query = self.conn.query(func.sum(Actions.investment))
        query = query.filter(Actions.action_type.in_(["DEPOSIT", "WITHDRAW"]))
        result = query.first()
        return result[0]  # type: ignore[index]

    def update_investment(self, swap: Swap) -> None:
        src_coin = swap["src"].coin
        dest_coin = swap["dest"].coin
        src_amount = swap["src"].amount
        dest_amount = swap["dest"].amount

        if (self.track[src_coin]["amount"] + src_amount) >= 0:
            self.track[src_coin]["amount"] += src_amount
            swap_percentage = self.get_swap_percentage(swap["src"])
        else:
            self.track[src_coin]["amount"] = 0
            swap_percentage = 1.0

        track_investment = cast_to_float(self.track[src_coin]["investment"] * swap_percentage, 2)
        self.track[dest_coin]["amount"] += dest_amount
        self.track[src_coin]["investment"] -= track_investment
        self.track[dest_coin]["investment"] += track_investment
        swap["src"].investment = track_investment * -1
        swap["dest"].investment = track_investment
        self.conn.commit()

    def get_current_price(self, sess: requests.Session, coin: str) -> float:
        if coin in self.STABLE_COINS:
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
                    swap = {data.action_id: {}}  # type: ignore[typeddict-item]
                src_dest: SWAP_KEYS = "dest" if data.amount > 0.0 else "src"
                swap[data.action_id][src_dest] = data

                # we make sure we have the two rows stored in cache
                # if "dest" in swap[action_id] and "src" in swap[action_id]:
                if all(k in swap[data.action_id] for k in ("dest", "src")):
                    self.update_investment(swap[data.action_id])
            else:
                raise Exception(f"Unknown action {data.action_type}")

    def get_data_for_portfolio(self) -> list[tuple]:
        query = self.conn.query(
            Actions.coin,
            func.sum(Actions.amount),
            func.sum(Actions.investment),
        )
        query = query.add_columns(func.sum(Actions.investment) / func.sum(Actions.amount))
        query = query.group_by(Actions.coin)
        query = query.having(func.sum(Actions.amount) > 0)
        query = query.order_by(Actions.coin)
        return query.all()

    def get_portfolio(self) -> None:
        all_values = 0.0
        current_investment = 0.0
        actual_investment = self.get_actual_investment()
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
            for item in self.get_data_for_portfolio():
                current_price = self.get_current_price(sess, item[0])
                now = datetime.now()
                current_value = cast_to_float(current_price * item[1], 2)
                all_values += current_value
                investment = cast_to_float(item[2], 2)
                current_investment = cast_to_float(current_investment + investment, 2)
                table.add_row(
                    [
                        now.strftime("%H:%M:%S %d/%b/%Y"),
                        investment,  # investment
                        item[0],  # coin
                        cast_to_float(item[1], 8),  # amount
                        current_price,
                        current_value,
                        cast_to_float(item[3], 2) if len(item) == 4 else "-",  # min_price
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
                cast_to_float(all_values, 2),
                "-",
                cast_to_float(all_values - actual_investment, 2),
            ]
        )
        if current_investment != actual_investment:
            msg = f"WARNING: {current_investment=} are different {actual_investment=} "
            msg += f"{actual_investment - current_investment}"
            self.logger.warning(msg)
        print(table)

    def close(self) -> None:
        self.conn.close()
