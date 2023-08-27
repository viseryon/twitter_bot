from datetime import datetime as dt

import pandas as pd


def get_market_open_days():
    business_days = pd.date_range("2023-01-01", "2023-12-31", freq="B")
    business_days = [dt.date(x) for x in business_days]

    dni_bez_sesji = [
        "2023-01-06",
        "2023-04-07",
        "2023-04-10",
        "2023-05-01",
        "2023-05-03",
        "2023-06-08",
        "2023-08-15",
        "2023-11-01",
        "2023-12-25",
        "2023-12-26",
    ]

    dni_bez_sesji = [dt.strptime(x, r"%Y-%m-%d") for x in dni_bez_sesji]
    dni_bez_sesji = [dt.date(x) for x in dni_bez_sesji]

    market_open_days = list(set(business_days) - set(dni_bez_sesji))

    return market_open_days


def is_good_day_to_post_option_charts() -> bool:
    market_open_days = get_market_open_days()
    td = dt.today()
    td = dt.date(td)

    if td in market_open_days:
        return True
    else:
        return False


if __name__ == "__main__":
    pass
