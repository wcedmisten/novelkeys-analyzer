import numpy as np
from aggregate import aggregate_data

from plot_num_products import plot_num_products
from plot_product_updates import plot_product_updates
from plot_delivery_times_over_time import plot_delivery_times_over_time
from plot_num_exceeding_estimate import plot_num_exceeding_estimate
from plot_estimate_times_over_time import plot_estimate_times_over_time
from plot_total_num_exceeding_estimate import plot_total_num_exceeding_estimate


import json
import os.path

import datetime

import pandas as pd

import difflib


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
    "GMK RGB Add-on Kit": "GMK RGB Add on Kit",
    "M6-C Milkshake Edition": "MC-6 - Milkshake Edition",
    "NK65™ - Aluminum Edition": "NK65 Aluminum Edition",
    "NK65 - Aluminum Edition": "NK65 Aluminum Edition",
    "GMK Greek Beige Add-on Kit": "GMK Greek Beige Add-On Kit",
    "NK65 - Olivia Edition": "NK65 Olivia Edition",
    "Yuri Deskpads": "Yuri Deskpad",
    "NK87 Aluminum Edition Preorder": "NK87 - Aluminum Edition",
    "TKC x NK_ Bushid? Stabilizer Kit": "TKC x NK_ Bushidō Stabilizer Kit",
    "Mecha-01 Deskpads": "Mecha-01 Deskpad",
    "Kat Lich": "KAT Lich",
    "Darling Deskpads": "Darling Deskpad",
}

# turn a text estimate into a datetime
def refine_estimate(estimate):
    if not estimate:
        return estimate

    estimate = (
        estimate.replace(".", "")
        .replace("Sept", "Sep")
        # replace the quarter with the last month in the quarter
        .replace("Q1", "Mar")
        .replace("Q2-3", "Sep")
        .replace("Q2", "Jun")
        .replace("Q3", "Sep")
        .replace("Q4", "Dec")
    )

    refined_estimate = None

    try:
        refined_estimate = datetime.datetime.strptime(estimate, "%b %Y")
    except Exception as e:
        refined_estimate = datetime.datetime.strptime(estimate, "%B %Y")

    try:
        nextmonthdate = refined_estimate.replace(
            month=refined_estimate.month + 1, day=1
        )
    except ValueError:
        if refined_estimate.month == 12:
            nextmonthdate = refined_estimate.replace(
                year=refined_estimate.year + 1, month=1, day=1
            )
    return nextmonthdate


cleaned_data = {}

for timestamp, val in data.items():
    if timestamp not in cleaned_data:
        cleaned_data[timestamp] = {}

    for name in val.keys():
        # special case - skip this because it's duplicate
        if name == "NK65™ - Oblivion V3.1 Edition" or name == "Decent65":
            continue

        # use the preferred "cleaned" name if possible
        # otherwise keep the old name
        new_name = name_cleanup.get(name, name)

        # handle special cases where 2nd run was not renamed
        if name == "GMK Striker" and timestamp > "20210613000000":
            new_name = "GMK Striker 2"

        if name == "GMK Bento" and timestamp > "20210613000000":
            new_name = "GMK Bento R2"

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

# find similar names
def print_similar_names():
    for idx, name in enumerate(all_cleaned_products):
        print(
            difflib.get_close_matches(
                name, [x for i, x in enumerate(all_cleaned_products) if i != idx]
            )
        )


# convert everything into flat rows
flattened_data = []
for timestamp, val in cleaned_data.items():
    for name, product in val.items():
        product["product_name"] = name
        product["scrape_time"] = datetime.datetime.strptime(timestamp, "%Y%m%d%H%M%S")
        flattened_data.append(product)

df = pd.DataFrame(data=flattened_data)

categories = df.groupby("product_name").agg(categories=("category", "unique"))


def replace_unknown(categories):
    if len(categories) > 1:
        categories = np.delete(categories, np.argwhere(categories == "unknown"))

    return categories[0]


categories["category"] = categories["categories"].apply(replace_unknown)

df = df.merge(categories, how="left", on="product_name", suffixes=("_x", "")).drop(
    "category_x", axis=1
)

completed_time = (
    df.loc[df["status"].isin(["completed", "Fulfilled!"])]
    .groupby("product_name")
    .agg(completed_time=("scrape_time", "min"))
)

# with pd.option_context(
#     "display.max_rows", None, "display.max_columns", None
# ):  # more options can be specified also
#     print(df[["category", "categories"]])

df_all = df
df = df.where(df["status"] != "completed").where(df["status"] != "Fulfilled!")

df = df.merge(completed_time, how="left", on="product_name")

# number of product updates over time
plot_num_products(df_all, filename="num-product-updates.png")

plot_product_updates(
    df,
    show_delivered_products=False,
    show_estimates=False,
    show_product_labels=False,
    show_categories=False,
    title="Timeline of All Novelkeys Products",
    filename="timeline-all-products.png",
)

plot_product_updates(
    df,
    show_delivered_products=False,
    show_estimates=False,
    show_product_labels=False,
    title="Timeline of All Novelkeys Products by Category",
    filename="timeline-all-by-category.png",
)

plot_product_updates(
    df,
    show_delivered_products=False,
    show_estimates=True,
    show_product_labels=False,
    title="Timeline of All Novelkeys Products by Category With Estimates",
    filename="timeline-all-by-category-with-estimates.png",
)

plot_product_updates(
    df,
    show_delivered_products=True,
    show_estimates=True,
    title="Timeline of Completed Novelkeys Products as of June 16, 2022",
    filename="timeline-completed.png",
)

plot_product_updates(
    df,
    show_delivered_products=False,
    show_in_progress_products=True,
    show_estimates=True,
    title="Timeline of In Progress Novelkeys Products as of June 16, 2022",
    filename="timeline-in-progress.png",
)

plot_delivery_times_over_time(df, filename="delivery-estimate-time.png")

plot_num_exceeding_estimate(df, filename="num-delivered-early-late.png")

plot_estimate_times_over_time(
    df, filter_incomplete_data=False, filename="estimates-over-time.png"
)

plot_total_num_exceeding_estimate(df)
