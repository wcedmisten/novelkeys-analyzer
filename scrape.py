from bs4 import BeautifulSoup
from lxml import html, etree
import pprint
import re
import os
from glob import glob

# note on old website format vs. new
# the old novelkeys.xyz format is less structured, possibly because it uses
# shopify?
# to scrape this data I have to search for a data-href that's unique to the
# product div, then count the number of <spans> found beneath it to find each
# category of product update (live, in progress, completed)
#
# the new novelkeys.com is more structured, and uses classnames to differentiate
# the products, making scraping much easier


def scrape_updates_novelkeys_xyz(filepath):
    """`filepath` is the path to an HTML file with the old novelkeys.xyz shape

    Returns a map where each key is the name of the product,
    and each value is a map with the following keys:
    `status`: status text of the product
    `estimate`: estimate date text of the product

    e.g.

    'Sloth Deskpad': {'estimate': 'Aug. 2021',
                   'status': 'Production complete. In transit to NovelKeys.'},
    """
    data = {}

    # fix unicode error on some pages by ignoring them
    # https://stackoverflow.com/a/62677410
    with open(filepath, "r", encoding="utf-8", errors="ignore") as fp:
        soup = BeautifulSoup(fp, "html.parser")

        all_products = soup.find_all(
            "div", attrs={"data-href": re.compile(r"https://novelkeys.xyz/products/*")}
        )

        for i in all_products:
            item_info = i.find_all("span", attrs={"data-pf-type": "Text"})
            name = item_info[0].text.strip()
            data[name] = {}

            # in progress
            if len(item_info) == 5:
                if len(item_info) > 2:
                    data[name]["estimate"] = item_info[2].text.strip()

                if len(item_info) > 4:
                    data[name]["status"] = item_info[4].text.strip()

            # completed
            elif len(item_info) == 2:
                data[name]["status"] = item_info[1].text.strip()

            # live
            elif len(item_info) == 3:
                data[name]["estimate"] = item_info[2].text.strip()

            else:  # assert there are no edge cases here
                raise Exception("Unknown length", item_info)

    return data


def scrape_updates_novelkeys_com(filepath):
    """`filepath` is the path to an HTML file with the new novelkeys.com shape

    Returns a map where each key is the name of the product,
    and each value is a map with the following keys:
    `status`: status text of the product
    `estimate`: estimate date text of the product

    e.g.

    'Sloth Deskpad': {'estimate': 'Aug. 2021',
                   'status': 'Production complete. In transit to NovelKeys.'},
    """
    with open(filepath) as fp:
        soup = BeautifulSoup(fp, "html.parser")

        all_products = soup.select_one("#keycaps").find_all(
            "div", {"class": "preorder-timeline-details"}
        )

        data = {}

        for product in all_products:
            name = product.find("h2", {"class": "preorder-timeline-title"}).text

            product_details = product.find_all("p", {})
            status = product_details[0].text.strip()
            estimate = None
            if len(product_details) > 1:
                estimate = product_details[1].text.strip()

            data[name] = {"status": status}

            if estimate:
                data[name]["estimate_text"] = estimate
                data[name]["estimate"] = estimate.split("Estimated Arrival:")[1].strip()

    return data
