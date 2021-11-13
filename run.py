#!/usr/bin/env python

import sys
import logging
from os import path
from sqlite3 import Connection
import uuid
from definitions import DICT_COIN, Asset, RAW_ASSET, Swap_Coin
from tools import startdb


def get_price(coin: str, utc_date: str) -> float:
    # @INFO I'll use some sort of API call to get the price
    print(f"{coin=}      {utc_date=}")
    return 40.00


def write_data(conn: Connection, sql_str: str, values: dict) -> None:
    cursor = conn.cursor()
    cursor.execute(sql_str, values)
    conn.commit()
    cursor.close()


def get_dest_value(coin: str, utc_date: str, amount: float) -> float:
    price = get_price(coin, utc_date)
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
        return {
            "id": raw[0],
            "utc_date": raw[1],
            "action_type": raw[2],
            "action_id": raw[3],
            "coin": raw[4],
            "amount": raw[5],
            "investment": raw[6],
            "wallet": raw[7],
        }

    return [loop(r) for r in raw_asset_list]


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

        if asset["action_type"] in ["DEPOSIT", "WITHDRAW"]:
            track[coin]["investment"] += asset["investment"]
        elif asset["action_type"] in ["FEE", "INTEREST", "ADJUSTMENT"]:
            track[coin]["amount"] = round(track[coin]["amount"] + amount, 8)
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
                update_investment(
                    conn, src_id, src_investment_debit
                )  # src_investment_debit must be negative
                track[src_coin]["investment"] += src_investment_debit
                value = get_dest_value(dest_coin, utc_date, dest_amount)
                update_investment(conn, dest_id, value)  # value must be positive
                if value > src_tracked_investment:
                    action_type = "GAIN"
                elif value < src_tracked_investment:
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
                            "investment": value - src_tracked_investment,
                            "wallet": wallet,
                        },
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
