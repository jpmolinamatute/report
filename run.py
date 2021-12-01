#!/usr/bin/env python

import sys
import logging
from os import path
from sqlite3 import Connection
import uuid
import json
from datetime import datetime
from typing import Union
from definitions import DICT_COIN, Asset, RAW_ASSET, Swap_Coin
from tools import startdb

FIAT_VALUE = 1.25
STABLE_COIN = ("BUSD", "USDT")
OTHER_BASE_COIN = ("BTC", "ETH", "BNB")


def get_pair(coin1: str, coin2: str) -> str:
    result = ""
    if coin1 != coin2:
        for o in STABLE_COIN + OTHER_BASE_COIN:
            if o in [coin1, coin2]:
                if coin1 == o:
                    result = f"{coin2}{coin1}"
                else:
                    result = f"{coin1}{coin2}"
                break
        if not result:
            raise Exception(f"ERROR: invalid pair '{coin2}' <-> '{coin1}'")
    else:
        raise Exception(f"ERROR: invalid pair '{coin2}' <-> '{coin1}'")

    return result


def write_data(
    conn: Connection, sql_str: str, values: Union[dict[str, Union[str, float]], Asset]
) -> None:
    cursor = conn.cursor()
    cursor.execute(sql_str, values)
    conn.commit()
    cursor.close()


def get_price(conn: Connection, pair: str, open_time: int) -> float:
    sql_str = """
        SELECT open, high, low, close
        FROM history
        WHERE open_time = :open_time
        AND pair = :pair;
    """
    cursor = conn.cursor()
    cursor.execute(sql_str, {"pair": pair, "open_time": open_time})
    rows = cursor.fetchall()
    if rows:
        row = rows[0]
        cursor.close()
        result = round((row[0] + row[1] + row[2] + row[3]) / 4, 8)
    else:
        logging.error(f"ERROR: {pair=} {open_time=} NOT FOUND")
        logging.error(rows)
        result = 0.0
    return result


def get_dest_value(conn: Connection, coin1: str, coin2: str, utc_date: str, amount: float) -> float:
    utc_date = f"{utc_date[:-2]}00"
    date_int = int(datetime.strptime(utc_date, "%Y-%m-%d %H:%M:%S").timestamp() * 1000)
    #     p     a          v
    # 186.84 4.61SOL 861.3324BUSD
    # price = value / amount
    # amout = value / price
    # value = price * amount
    if coin1 in STABLE_COIN or coin2 in STABLE_COIN:
        pair = get_pair(coin1, coin2)
        value = get_price(conn, pair, date_int)
        price = value / amount
    else:
        pair1 = get_pair(coin1, coin2)
        value1 = get_price(conn, pair, date_int)
        base_coin = coin1 if coin1 in OTHER_BASE_COIN else coin2
        pair2 = get_pair(base_coin, STABLE_COIN[0])
        value2 = get_price(conn, pair2, date_int)
        logging.error(
            "Fix this, when a swap is done and no stable coin is involved, so I need to find the value in the base_coin so that I can convert it into stable_coin and figure out the actual price in fiat"
        )

    return price * FIAT_VALUE


def update_investment(conn: Connection, row_id: str, investment: float) -> None:
    sql_str = """
        UPDATE actions
        SET investment = :investment
        WHERE id = :id;
    """
    write_data(conn, sql_str, {"investment": investment, "id": row_id})


def add_gain_loss(conn: Connection, asset: Asset) -> None:
    sql_str = """
        INSERT INTO actions(id, utc_date, action_type, action_id, coin, amount, investment, wallet)
        VALUES(:id, :utc_date, :action_type, :action_id, :coin, :amount, :investment, :wallet);
    """
    write_data(conn, sql_str, asset)


def get_data(conn: Connection) -> list[RAW_ASSET]:
    sql_str = """
        SELECT *
        FROM actions
        WHERE action_type IN ("SWAP", "DEPOSIT", "WITHDRAW", "FEE", "INTEREST", "ADJUSTMENT")
        ORDER BY utc_date;
    """
    cursor = conn.cursor()
    cursor.execute(sql_str)
    rows = cursor.fetchall()
    cursor.close()
    return rows


def clean_data(raw_asset_list: list[RAW_ASSET]) -> list[Asset]:
    def loop(raw: RAW_ASSET) -> Asset:
        my_dict: Asset = {}
        (
            my_dict["id"],
            my_dict["utc_date"],
            my_dict["action_type"],
            my_dict["action_id"],
            my_dict["coin"],
            my_dict["amount"],
            my_dict["investment"],
            my_dict["wallet"],
        ) = raw
        return my_dict

    return [loop(r) for r in raw_asset_list]


def is_complete_swap(coin: str, src_coin_sum_amount: float) -> bool:
    result = True
    # src_coin_sum_amount == 0 means a complete swap
    if src_coin_sum_amount > 0:
        result = False
    elif src_coin_sum_amount < 0:
        raise Exception(f"Error: '{coin}' has a negative value")
    return result


def calculate_gain_loss(
    conn: Connection, action_id: str, track: DICT_COIN, swap: Swap_Coin
) -> None:
    utc_date = swap["utc_date"]
    wallet = swap["wallet"]

    swap_src_coin = swap["src"]["coin"]
    swap_src_amount = swap["src"]["amount"]
    swap_src_id = swap["src"]["id"]

    swap_dest_coin = swap["dest"]["coin"]
    swap_dest_amount = swap["dest"]["amount"]
    swap_dest_id = swap["dest"]["id"]

    tracked_src_amount = track[swap_src_coin]["amount"]
    tracked_src_investment = track[swap_src_coin]["investment"]

    src_investment_debit = tracked_src_investment * (tracked_src_amount / swap_src_amount)

    value = get_dest_value(conn, swap_src_coin, swap_dest_coin, utc_date, swap_dest_amount)
    track[swap_src_coin]["amount"] = round(track[swap_src_coin]["amount"] + swap_src_amount, 8)
    track[swap_src_coin]["investment"] += src_investment_debit
    track[swap_dest_coin]["amount"] = round(track[swap_dest_coin]["amount"] + swap_dest_amount, 8)
    track[swap_dest_coin]["investment"] += value

    update_investment(
        conn, swap_src_id, src_investment_debit
    )  # src_investment_debit must be negative

    update_investment(conn, swap_dest_id, value)  # value must be positive
    action_type = ""
    if value > tracked_src_investment:
        action_type = "GAIN"
    elif value < tracked_src_investment:
        action_type = "LOSS"

    if action_type:
        add_gain_loss(
            conn,
            {
                "id": str(uuid.uuid4()),
                "utc_date": utc_date,
                "action_type": action_type,
                "action_id": action_id,
                "coin": "NA",
                "amount": 0.00,
                "investment": value - tracked_src_investment,
                "wallet": wallet,
            },
        )


def process(conn: Connection, asset_list: list[Asset]) -> None:
    track: DICT_COIN = {}
    swap: dict[str, Swap_Coin] = {}
    for asset in asset_list:
        coin = asset["coin"]
        action_id = asset["action_id"]
        amount = asset["amount"]

        if coin not in track:
            track[coin] = {
                "amount": 0.0,
                "investment": 0.0,
            }

        if asset["action_type"] in ["DEPOSIT", "WITHDRAW"]:
            track[coin]["investment"] += asset["investment"]
            track[coin]["amount"] = round(track[coin]["amount"] + amount, 8)
        elif asset["action_type"] in ["FEE", "INTEREST", "ADJUSTMENT", "MINING", "TRANSFER"]:
            track[coin]["amount"] = round(track[coin]["amount"] + amount, 8)
        elif asset["action_type"] == "SWAP":
            # we process SWAP here
            # we have two rows and we can't control the order of them
            # swap should contain only two transactions
            if action_id not in swap:
                swap = {action_id: {"utc_date": asset["utc_date"], "wallet": asset["wallet"]}}

            src_dest = "dest" if amount > 0.0 else "src"
            swap[action_id][src_dest] = {"amount": amount, "coin": coin, "id": asset["id"]}
            # we make sure we have the two rows stored in cache
            if "dest" in swap[action_id] and "src" in swap[action_id]:
                calculate_gain_loss(conn, action_id, track, swap[action_id])
        else:
            raise Exception(f"Unknown action {asset['action_type']}")
    logging.debug(
        json.dumps(
            track,
            indent=4,
            sort_keys=True,
        )
    )


def main() -> None:
    logging.basicConfig(level=logging.DEBUG)
    logging.info(f"Script {path.basename(__file__)} has started")
    conn = startdb()
    result1 = get_data(conn)
    result2 = clean_data(result1)
    process(conn, result2)
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
