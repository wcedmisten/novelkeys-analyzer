from time import time
from bs4 import BeautifulSoup
import re
from glob import glob

from scrape import scrape_updates_novelkeys_com, scrape_updates_novelkeys_xyz


def aggregate_data():
    timeseries_data = {}

    xyz_snapshots = []

    for file in glob(
        "/home/william/Downloads/novelkeys-wayback/*/novelkeys.xyz/pages/updates"
    ):
        xyz_snapshots.append(file)

    xyz_snapshots.sort()

    xyz_date_regex = re.compile(
        r"/home/william/Downloads/novelkeys-wayback/(?P<date>.*)/novelkeys.xyz/pages/updates"
    )

    for f in xyz_snapshots:
        scraped_data = scrape_updates_novelkeys_xyz(f)

        m = xyz_date_regex.match(f)
        date = m.group("date")
        print(f"Date: {date}, Found {len(scraped_data)} items")

        timeseries_data[date] = scraped_data

    com_snapshots = []

    for file in glob(
        "/home/william/Downloads/novelkeys-wayback/*/novelkeys.com/pages/product-updates"
    ):
        com_snapshots.append(file)

    com_snapshots.sort()

    com_date_regex = re.compile(
        r"/home/william/Downloads/novelkeys-wayback/(?P<date>.*)/novelkeys.com/pages/product-updates"
    )

    for f in com_snapshots:
        print(f)
        scraped_data = scrape_updates_novelkeys_com(f)

        m = com_date_regex.match(f)
        date = m.group("date")
        print(f"Date: {date}, Found {len(scraped_data)} items")

        timeseries_data[date] = scraped_data

    return timeseries_data
