import pprint

from pexpect import ExceptionPexpect
from aggregate import aggregate_data
import json
import os.path

import numpy as np
import matplotlib.pyplot as plt
import datetime

import pandas as pd

aggregate_filename = "aggregate.json"

# load from JSON checkpoint if available
if not os.path.isfile(aggregate_filename):
    data = aggregate_data()

    with open(aggregate_filename, "w") as f:
        json.dump(data, f)

else:
    with open(aggregate_filename, "r") as f:
        data = json.load(f)

all_products = set()

for timestamp, val in data.items():
    for name in val.keys():
        all_products.add(name)

# all_products = {}

# for timestamp, val in data.items():
#     for name in val.keys():
#         if name not in all_products:
#             all_products[name] = []
#         all_products[name].append((timestamp, val[name].get("status")))

# pprint.pprint(all_products)
# print(len(all_products))

name_cleanup = {
    "Superuser Deskpads": "Superuser Deskpad",
    "Sa Tatooine™": "SA Tatooine",
    "Recall Deskpad GB": "Recall Deskpad",
    "RAMA M6-C Oblivion Edition GB": "RAMA M6-C Oblivion Edition",
    "Parcel Deskpads": "Parcel Deskpad",
    "Oblivion V3.1 Deskpad GB": "Oblivion V3.1 Deskpad",
    "NK65™ - Awaken Edition": "NK65 - Awaken Edition",
    "NK65 - Oblivion Edition GB": "NK65 - Oblivion Edition",
    "NK65™ - Superuser Edition": "NK65 - Superuser Edition",
    "NK65™ Olivia Edition": "NK65 - Olivia Edition",
    "Li'l Dragon Deskpads": "Li'l Dragon Deskpad",
    "Li'l Dragon Accesories": "Li'l Dragon Accessories",
    "JTK Griseann / Royal Alphas": "JTK Griseann / Royal Alpha",
    "GMK Oblivion V3.1 GB": "GMK Oblivion V3.1",
    "GMK Handarbeit R2 GB": "GMK Handarbeit R2",
    "Colorchrome Deskpads": "Colorchrome Deskpad",
    "Awaken Deskpads": "Awaken Deskpad",
}

# turn a text estimate into a datetime
def refine_estimate(estimate):
    if not estimate:
        return estimate

    estimate = (
        estimate.replace(".", "")
        .replace("Sept", "Sep")
        .replace("Q1", "Feb")
        .replace("Q2-3", "Jun")
        .replace("Q2", "May")
        .replace("Q3", "Aug")
        .replace("Q4", "Nov")
    )

    refined_estimate = None

    try:
        refined_estimate = datetime.datetime.strptime(estimate, "%b %Y")
    except Exception as e:
        refined_estimate = datetime.datetime.strptime(estimate, "%B %Y")

    return refined_estimate


cleaned_data = {}

for timestamp, val in data.items():
    if timestamp not in cleaned_data:
        cleaned_data[timestamp] = {}

    for name in val.keys():
        # use the preferred "cleaned" name if possible
        # otherwise keep the old name
        new_name = name_cleanup.get(name, name)
        # make sure there are no duplicates
        assert new_name not in cleaned_data[timestamp]
        cleaned_data[timestamp][new_name] = val[name]
        cleaned_data[timestamp][new_name]["refined_estimate"] = refine_estimate(
            cleaned_data[timestamp][new_name].get("estimate")
        )

all_cleaned_products = set()

for timestamp, val in cleaned_data.items():
    for name in val.keys():
        all_cleaned_products.add(name)

print("Names to be cleaned: ", len(name_cleanup))
print("Names before cleaning: ", len(all_products))
print("Names after cleaning: ", len(all_cleaned_products))

status_set = set()
estimate_set = set()

for timestamp, val in cleaned_data.items():
    for name, product in val.items():
        estimate_set.add(product.get("estimate"))
        status_set.add(product.get("status"))

# pprint.pprint(status_set)
# pprint.pprint(estimate_set)


def get_num_completed(snapshot_data):
    return len(
        list(filter(lambda v: v.get("status") == "completed", snapshot_data.values()))
    )


def plot_num_products():
    time = []
    num_products_in_progress = []
    num_products_completed = []

    for timestamp, val in cleaned_data.items():
        time.append(datetime.datetime.strptime(timestamp, "%Y%m%d%H%M%S"))
        # number of unique products on the page
        num_completed = get_num_completed(val)
        total_in_progress = len(val.keys()) - num_completed

        num_products_in_progress.append(total_in_progress)
        num_products_completed.append(num_completed)

    ax = plt.subplot(111)
    ax.bar(time, num_products_in_progress, width=10, label="In progress")
    ax.bar(
        time,
        num_products_completed,
        bottom=num_products_in_progress,
        width=10,
        label="Completed",
    )
    ax.xaxis_date()
    ax.legend()

    plt.title("Number of products on Novelkeys Updates page over time")
    plt.show()


# convert everything into flat rows
denormalized_data = []
for timestamp, val in cleaned_data.items():
    for name, product in val.items():
        product["product_name"] = name
        product["scrape_time"] = datetime.datetime.strptime(timestamp, "%Y%m%d%H%M%S")
        denormalized_data.append(product)

df = pd.DataFrame(data=denormalized_data)

df = df.where(df["status"] != "completed")


df["earliest_seen"] = df.groupby("product_name")["scrape_time"].transform("min")

df["latest_seen"] = df.groupby("product_name")["scrape_time"].transform("max")

df["tracked_time"] = df["latest_seen"] - df["earliest_seen"]

# print(
#     df.filter(
#         items=[
#             "scrape_time",
#             "estimate",
#             "status",
#             "earliest_seen",
#             "product_name",
#             "tracked_time",
#         ]
#     ).sort_values(by="tracked_time", ascending=False)
# )

completed_products = (
    df.filter(
        items=[
            "scrape_time",
            "estimate",
            "status",
            "earliest_seen",
            "product_name",
            "tracked_time",
        ]
    )
    .loc[df["latest_seen"] < datetime.datetime(2022, 6, 17)]["product_name"]
    .unique()
)

print(df.loc[df["product_name"] == "GMK Honor"])
print(completed_products)

x = np.array(df.loc[df["product_name"] == "GMK Honor"]["earliest_seen"].unique())
y = np.array(df.loc[df["product_name"] == "GMK Honor"]["latest_seen"].unique())
print(x, y)
labels = ["GMK Honor"]

# TODO: https://stackoverflow.com/questions/11042290/how-can-i-use-xaxis-date-with-barh

ax = plt.subplot(111)
ax.xaxis_date()

ax.barh(y, [1] * len(x), left=x, color="red", edgecolor="red", align="center", height=1)
plt.ylim(max(y) + 0.5, min(y) - 0.5)
plt.yticks(np.arange(y.max() + 1), labels)
plt.show()
