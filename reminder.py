from datetime import date, datetime, timedelta
from dotenv import load_dotenv
from time import sleep
import os
import requests
import schedule


def get_dates():
    r = requests.get(os.getenv("ABFUHR_URL")).json()
    data_list = r["pageProps"]["dehydratedState"]["queries"][0]["state"]["data"]["data"]
    date_list = [data["attributes"] for data in data_list]

    def to_abfallart(date_dict: dict) -> list[str]:
        return [x["attributes"]["titel"] for x in date_dict["abfallarten"]["data"]]

    def to_date(date_dict: dict) -> date:
        return datetime.strptime(date_dict["datum"], "%Y-%m-%d").date()

    return [
        (to_date(date_dict), to_abfallart(date_dict))
        for date_dict in date_list
        if to_date(date_dict) > date.today()
    ]


def check_date_notify(dates: list[tuple[date, list[str]]]):
    if dates[0][0] == (date.today() + timedelta(days=1)):
        params = {
            "to": os.getenv("WHAPI_GROUP"),
            "body": (
                f"[🗑️-Reminder]\n"
                f"Hi alle. Morgen geht Müll: {','.join(dates[0][1])}.\n"
                f"Bitte checkt, wer dran ist, und stellt raus.\n"
                f"🗑️🗑️🗑️"
            ),
        }
        headers = {
            "Authorization": f"Bearer {os.getenv('WHAPI_TOKEN')}",
        }
        requests.post(
            f"https://gate.whapi.cloud/messages/text", json=params, headers=headers
        )
        del dates[0]


load_dotenv()
dates = get_dates()
schedule.every().day.at(os.getenv("SCHEDULE_TIME")).do(lambda: check_date_notify(dates))

while True:
    schedule.run_pending()
    sleep(60)
