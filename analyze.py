from bs4 import BeautifulSoup
import pprint
import re
from glob import glob

from scrape import scrape_updates_novelkeys_com, scrape_updates_novelkeys_xyz

xyz_snapshots = []

for file in glob(
    "/home/william/Downloads/novelkeys-wayback/*/novelkeys.xyz/pages/updates"
):
    xyz_snapshots.append(file)

xyz_snapshots.sort()

prev_products = None

xyz_date_regex = re.compile(
    r"/home/william/Downloads/novelkeys-wayback/(?P<date>.*)/novelkeys.xyz/pages/updates"
)

for f in xyz_snapshots:
    scraped_data = scrape_updates_novelkeys_xyz(f)

    m = xyz_date_regex.match(f)
    date = m.group("date")
    print(f"Date: {date}, Found {len(scraped_data)} items")

    # pprint.pprint(scraped_data)
    # curr_products = set(scraped_data.keys())

    # if prev_products:
    #     if prev_products.difference(curr_products):
    #         print("Newly removed")
    #         print(prev_products.difference(curr_products))

    #     if curr_products.difference(prev_products):
    #         print("Newly added")
    #         print(curr_products.difference(prev_products))

    # prev_products = curr_products


com_snapshots = []

for file in glob(
    "/home/william/Downloads/novelkeys-wayback/*/novelkeys.com/pages/product-updates"
):
    com_snapshots.append(file)

com_snapshots.sort()

com_date_regex = re.compile(
    r"/home/william/Downloads/novelkeys-wayback/(?P<date>.*)/novelkeys.com/pages/product-updates"
)

prev_products = set()

for f in com_snapshots:
    scraped_data = scrape_updates_novelkeys_com(f)
    curr_products = set(scraped_data.keys())

    m = com_date_regex.match(f)
    date = m.group("date")
    print(f"Date: {date}, Found {len(scraped_data)} items")

    # pprint.pprint(curr_products)

    # print("Newly removed")
    # print(prev_products.difference(curr_products))

    # print("Newly added")
    # print(curr_products.difference(prev_products))

    # prev_products = curr_products
