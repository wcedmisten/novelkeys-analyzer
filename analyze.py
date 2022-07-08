import pprint

import matplotlib.dates as mdates
import matplotlib.patches as mpatches

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
    "NK65™ - Oblivion V3.1 Edition": "GMK Oblivion V3.1",
    "GMK Monokai": "GMK Monokai Material",
    "GMK Handarbeit R2 GB": "GMK Handarbeit R2",
    "Colorchrome Deskpads": "Colorchrome Deskpad",
    "Awaken Deskpads": "Awaken Deskpad",
    "Analog Dreams Deskpads": "Analog Dreams R2 Deskpad",
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
        # special case - skip this because it's duplicate
        if name == "NK65™ - Oblivion V3.1 Edition":
            continue

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

print(
    df.loc[df["product_name"] == "GMK Dots R2"].filter(items=["status", "scrape_time"])
)


def graph_product_updates(
    df,
    sort_by_earliest=True,
    show_categories=True,
    show_product_labels=False,
    filter_incomplete_data=True,
    filter_categories=None,
    display_estimates=True,
):
    if filter_incomplete_data:
        # only show products which have started after the first scrape date
        # and ended before the last date, to get the whole run accurately
        df = df.loc[df["latest_seen"] < datetime.datetime(2022, 6, 17)]
        df = df.loc[df["earliest_seen"] > datetime.datetime(2019, 11, 14)]

    if filter_categories is not None:
        df = df.loc[df["category"].isin(filter_categories)]

    agg_data = (
        df.groupby("product_name")
        .agg(
            earliest_seen=("earliest_seen", "first"),
            latest_seen=("latest_seen", "first"),
            product_name=("product_name", "first"),
            category=("category", "first"),
            estimate=("refined_estimate", "first"),
        )
        .sort_values("earliest_seen" if sort_by_earliest else "latest_seen")
    )

    earliest_date = agg_data["earliest_seen"]
    latest_date = agg_data["latest_seen"]

    estimate_date = agg_data["estimate"]

    labels = agg_data["product_name"]
    categories = agg_data["category"]

    color_map = {
        "keycaps": "#0168b4",
        "keyboards": "#7ddb72",
        "deskpads": "#bc0072",
        "switches": "#ff5949",
    }

    colors = list(map(lambda category: color_map.get(category, "black"), categories))

    # Now convert them to matplotlib's internal format...
    earliest_date, latest_date, estimate_date = [
        mdates.date2num(item) for item in (earliest_date, latest_date, estimate_date)
    ]

    ypos = range(len(earliest_date))
    fig, ax = plt.subplots()

    # Plot the estimate
    # ax.barh(
    #     ypos,
    #     earliest_date - estimate_date,
    #     left=estimate_date,
    #     height=0.8,
    #     align="center",
    #     color="black",
    # )

    # Plot the data
    container = ax.barh(
        ypos,
        earliest_date - latest_date,
        left=latest_date,
        height=0.9,
        align="center",
        color=(colors if show_categories else None),
    )

    if display_estimates:
        estimate_points = plt.scatter(
            estimate_date, ypos, s=40, c="black", marker="*", label="Initial Estimate"
        )

    ax.get_yaxis().set_visible(False)
    ax.axis("auto")
    ax.set_xlim([datetime.datetime(2019, 11, 14), datetime.datetime(2022, 6, 17)])

    if show_product_labels:
        ax.bar_label(container, labels)
    ax.xaxis_date()

    ax.legend(color_map.keys(), color_map.values())

    legend_handles = list(
        map(
            lambda item: mpatches.Patch(color=item[1], label=item[0]),
            color_map.items(),
        ),
    )
    if display_estimates:
        legend_handles.append(estimate_points)

    if show_categories:
        ax.legend(handles=legend_handles)

    plt.title(
        "Timeline of Novelkeys Updates, sorted by "
        + ("start date" if sort_by_earliest else "completion date")
    )
    plt.show()


# plot_num_products()
# graph_product_updates(df)

# graph_product_updates(df, show_categories=False, filter_incomplete_data=False)

# graph_product_updates(df, show_categories=False)

graph_product_updates(df, display_estimates=True)
graph_product_updates(df, display_estimates=False)

# graph_product_updates(df, filter_categories=["keycaps"])
