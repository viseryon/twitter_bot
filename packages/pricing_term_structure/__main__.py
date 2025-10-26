from datetime import datetime

from bot import TermStructureBot
from mylogging import setup

logger = setup(__name__, __file__)

if __name__ == "__main__":
    if datetime.today().day == 1:
        logger.info("it's first of the month, running pricing term structure project")
        bot = TermStructureBot()
        bot.run()
    else:
        logger.info("skipping pricing term structure project")
