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


def get_pair(coin1: str, coin2: str) -> str:
    result = ""
    if coin1 != coin2:
        for o in ("BUSD", "USDT", "BTC", "ETH", "BNB"):
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
        result = round((row[0] + row[1] + row[2] + row[3]) / 4, 8) if row else 0.0
    else:
        logging.error(f"ERROR: {pair=} {open_time=} NOT FOUND")
        logging.error(rows)
        result = 0.0
    return result


def get_dest_value(conn: Connection, coin1: str, coin2: str, utc_date: str, amount: float) -> float:
    utc_date = f"{utc_date[:-2]}00"
    date_int = int(datetime.strptime(utc_date, "%Y-%m-%d %H:%M:%S").timestamp() * 1000)
    pair = get_pair(coin1, coin2)
    price = get_price(conn, pair, date_int)
    return price * amount


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


def process(conn: Connection, asset_list: list[Asset]) -> None:
    track: DICT_COIN = {}
    swap_cache: dict[str, Swap_Coin] = {}
    for asset in asset_list:
        coin = asset["coin"]
        action_id = asset["action_id"]
        amount = asset["amount"]

        if coin not in track:
            track[coin] = {
                "amount": 0.0,
                "investment": 0.0,
            }
        track[coin]["amount"] += amount
        if asset["action_type"] in ["DEPOSIT", "WITHDRAW"]:
            track[coin]["investment"] += asset["investment"]
        elif asset["action_type"] in ["FEE", "INTEREST", "ADJUSTMENT", "MINING"]:
            pass
        else:
            # we process SWAP here
            # we have two rows and we can't control the order of them
            if action_id not in swap_cache:
                swap_cache[action_id] = {"utc_date": asset["utc_date"], "wallet": asset["wallet"]}

            if amount > 0:
                swap_cache[action_id]["src"] = {"amount": amount, "coin": coin, "id": asset["id"]}
            else:
                swap_cache[action_id]["dest"] = {
                    "amount": amount * -1,
                    "coin": coin,
                    "id": asset["id"],
                }

            # we make sure we have the two rows stored in cache
            if "dest" in swap_cache[action_id] and "src" in swap_cache[action_id]:
                src_coin = swap_cache[action_id]["src"]["coin"]
                utc_date = swap_cache[action_id]["utc_date"]
                wallet = swap_cache[action_id]["wallet"]
                src_amount = swap_cache[action_id]["src"]["amount"]
                src_id = swap_cache[action_id]["src"]["id"]
                dest_coin = swap_cache[action_id]["dest"]["coin"]
                dest_amount = swap_cache[action_id]["dest"]["amount"]
                dest_id = swap_cache[action_id]["dest"]["id"]
                src_tracked_amount = track[src_coin]["amount"]
                src_tracked_investment = track[src_coin]["investment"]
                percentage_asset_sold = round(src_tracked_amount / src_amount, 3)
                src_investment_debit = (src_tracked_investment * percentage_asset_sold) * -1

                # update_investment(
                #     conn, src_id, src_investment_debit
                # )  # src_investment_debit must be negative
                track[src_coin]["investment"] += src_investment_debit

                value = get_dest_value(conn, src_coin, dest_coin, utc_date, dest_amount)
                update_investment(conn, dest_id, value)  # value must be positive
                action_type = ""
                if value > src_tracked_investment:
                    action_type = "GAIN"
                elif value < src_tracked_investment:
                    action_type = "LOSS"
                # logging.debug(f"{value=}     {src_tracked_investment=}")
                # if action_type:
                #     add_gain_loss(
                #         conn,
                #         {
                #             "id": str(uuid.uuid4()),
                #             "utc_date": utc_date,
                #             "action_type": action_type,
                #             "action_id": action_id,
                #             "coin": "NA",
                #             "amount": 0.00,
                #             "investment": value - src_tracked_investment,
                #             "wallet": wallet,
                #         },
                #     )
                # logging.debug(json.dumps(swap_cache, indent=4, sort_keys=True))
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
