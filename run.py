#!/usr/bin/env python

import sys
import json
import logging
from os import path

from tools import Collect


def main() -> None:
    logging.basicConfig(level=logging.DEBUG)
    logging.info(f"Script {path.basename(__file__)} has started")
    c = Collect("./sqlite3.db")
    c.proccess_raw_statement("./data/csv/best-binance.csv")
    portfolio = c.get_portfolio()
    c.logger.debug(json.dumps(portfolio, indent=4, sort_keys=True))
    c.save_history("./data/csv/history/")
    c.close_db()


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
