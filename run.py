#!/usr/bin/env python

import sys
import logging
from os import path
import argparse

from tools import Report


def validate_path(statement: str) -> str:
    file_path = ""
    if path.exists(statement) and path.splitext(statement)[1] == ".csv":
        file_path = path.abspath(statement)
    else:
        raise argparse.ArgumentTypeError("Invalid file")

    return file_path


def main() -> None:
    logging.basicConfig(level=logging.DEBUG)
    logging.info(f"Script {path.basename(__file__)} has started")

    parser = argparse.ArgumentParser(description="Generate crypto asset table.")
    parser.add_argument("--statement", required=False, type=validate_path, help="Path to CSV statement file")
    args = vars(parser.parse_args())

    r = Report()
    if args["statement"]:
        r.load_raw_statement(args["statement"])
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
