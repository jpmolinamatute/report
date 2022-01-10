#!/usr/bin/env python

import sys
import logging
from os import path

from tools import Report


def main() -> None:
    logging.basicConfig(level=logging.DEBUG)
    logging.info(f"Script {path.basename(__file__)} has started")
    # c = Collect("./sqlite3.db")
    # c.reset_db("./data/db-definitions.sql")
    # # c.save_history("./data/csv/history/")
    # c.proccess_raw_statement("./data/csv/best-binance.csv")
    # c.get_portfolio()
    # c.close_db()
    r = Report()
    r.load_raw_statement("./data/csv/best-binance.csv")
    r.process()
    r.get_portfolio()
    r.close()


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
