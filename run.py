#!/usr/bin/env python

import sys
import logging
from os import path
import sqlite3
import json
from definitions import DICT_COIN, Asset, RAW_ASSET


def startdb(dbfile: str = "./sqlite2.db") -> sqlite3.Connection:
    conn = sqlite3.connect(dbfile, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON;")
    cursor.execute("PRAGMA optimize;")
    conn.commit()
    cursor.close()
    return conn


def get_price(coin: str, utc_date: str) -> float:
    # @INFO I'll use some sort of API call to get the price
    print(f"{coin=}      {utc_date=}")
    return 0.0


def update_investment(conn: sqlite3.Connection, row_id: str, investment: float) -> None:
    sql_str = """
        UPDATE actions
        SET investment = :investment
        WHERE id = :id;
    """
    cursor = conn.cursor()
    cursor.execute(sql_str, ({"investment": investment, "id": row_id},))
    conn.commit()
    cursor.close()


def get_data(conn: sqlite3.Connection) -> list[RAW_ASSET]:
    sql_str = """
        SELECT *
        FROM actions
        WHERE action_type NOT IN ("TRANSFER_IN", "TRANSFER_OUT")
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


def process(asset_list: list[Asset]) -> None:
    track: DICT_COIN = {}
    for asset in asset_list:
        coin = asset["coin"]
        if coin not in track:
            track[coin] = {
                "amount": 0.0,
                "investment": 0.0,
            }

        if asset["action_type"] == "SWAP":
            if asset["amount"] > 0:
                price = get_price(coin, asset["utc_date"])
            else:
                # I need to do something else here but what?
                pass
            track[coin]["amount"] = round(track[coin]["amount"] + asset["amount"], 8)
            track[coin]["investment"] += asset["investment"]
        elif asset["action_type"] in ["DEPOSIT", "WITHDRAW"]:
            track[coin]["amount"] = round(track[coin]["amount"] + asset["amount"], 8)
            track[coin]["investment"] += asset["investment"]
        elif asset["action_type"] in ["LOSS", "GAIN"]:
            track[coin]["investment"] += asset["investment"]
        elif asset["action_type"] in ["FEE", "INTEREST", "ADJUSTMENT"]:
            track[coin]["amount"] = round(track[coin]["amount"] + asset["amount"], 8)
        print(json.dumps(track, indent=4, sort_keys=True))


def main() -> None:
    logging.basicConfig(level=logging.DEBUG)
    logging.info(f"Script {path.basename(__file__)} has started")
    conn = startdb()
    result1 = get_data(conn)
    result2 = clean_data(result1)
    process(result2)
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
