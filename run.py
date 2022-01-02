#!/usr/bin/env python

import sys
import logging
from os import path

# from tools import Collect
from tools import Report


def main() -> None:
    logging.basicConfig(level=logging.DEBUG)
    logging.info(f"Script {path.basename(__file__)} has started")
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
