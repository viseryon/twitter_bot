import argparse
from datetime import datetime

from bot import TermStructureBot
from mylogging import setup

logger = setup(__name__, __file__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Example script with --force flag")

    parser.add_argument(
        "--force",
        "-f",
        action="store_true",
        default=False,
        help="Force the action (skip confirmations)",
    )

    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    if args.force:
        logger.info("forced to post, running pricing term structure project")
        bot = TermStructureBot()
        bot.run()
    elif datetime.today().day == 1:
        logger.info("it's first of the month, running pricing term structure project")
        bot = TermStructureBot()
        bot.run()
    else:
        logger.info("skipping pricing term structure project")
