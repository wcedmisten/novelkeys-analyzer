from bs4 import BeautifulSoup
import pprint
import os
from glob import glob


def scrape_updates(filepath):
    print("scraping ", filepath)
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


snapshots = []

os.walk("/home/wcedmisten/Downloads/novelkeys-wayback")
for (
    file
) in glob(  # TODO: add novelkeys.xyz support. currently it breaks the webpage parsing
    "/home/william/Downloads/novelkeys-wayback/*/novelkeys.com/pages/*updates"
):
    snapshots.append(file)

snapshots.sort()

prev_products = set()

print(len(snapshots))

for f in snapshots:
    print(f)

for f in snapshots:
    curr_products = set(scrape_updates(f).keys())

    print("Newly removed")
    print(prev_products.difference(curr_products))

    print("Newly added")
    print(curr_products.difference(prev_products))

    prev_products = curr_products
