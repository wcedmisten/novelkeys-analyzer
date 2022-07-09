from aggregate import aggregate_data
import json
import os.path

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.patches as mpatches
import datetime

from numpy.polynomial.polynomial import polyfit
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
}

# turn a text estimate into a datetime
def refine_estimate(estimate):
    if not estimate:
        return estimate

    estimate = (
        estimate.replace(".", "")
        .replace("Sept", "Sep")
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


status_set = set()
estimate_set = set()

for timestamp, val in cleaned_data.items():
    for name, product in val.items():
        estimate_set.add(product.get("estimate"))
        status_set.add(product.get("status"))


def get_num_completed(snapshot_data):
    return len(
        list(
            filter(
                lambda v: v.get("status") == "completed"
                or v.get("status") == "Fulfilled!",
                snapshot_data.values(),
            )
        )
    )


# convert everything into flat rows
denormalized_data = []
for timestamp, val in cleaned_data.items():
    for name, product in val.items():
        product["product_name"] = name
        product["scrape_time"] = datetime.datetime.strptime(timestamp, "%Y%m%d%H%M%S")
        denormalized_data.append(product)

df = pd.DataFrame(data=denormalized_data)

completed_time = (
    df.loc[df["status"].isin(["completed", "Fulfilled!"])]
    .groupby("product_name")
    .agg(completed_time=("scrape_time", "min"))
)

with pd.option_context(
    "display.max_rows", None, "display.max_columns", None
):  # more options can be specified also
    print(df.loc[df["product_name"] == "GMK Striker 2"])

df = df.where(df["status"] != "completed").where(df["status"] != "Fulfilled!")

df = df.merge(completed_time, how="left", on="product_name")


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
    ax.xaxis.set_major_formatter(
        mdates.ConciseDateFormatter(ax.xaxis.get_major_locator())
    )
    ax.xaxis.set_minor_locator(mdates.MonthLocator())
    ax.xaxis_date()
    ax.legend()

    plt.title("Number of products on Novelkeys Updates page over time")
    plt.show()


def plot_product_updates(
    df,
    sort_by_earliest=True,
    show_categories=True,
    show_product_labels=False,
    filter_incomplete_data=True,
    filter_completed_data=False,
    filter_categories=None,
    show_estimates=True,
    title="Timeline of Novelkeys Updates",
):
    if filter_categories is not None:
        df = df.loc[df["category"].isin(filter_categories)]

    agg_data = (
        df.groupby("product_name")
        .agg(
            earliest_seen=("scrape_time", "min"),
            latest_seen=("scrape_time", "max"),
            completed_time=("completed_time", "first"),
            product_name=("product_name", "first"),
            category=("category", "first"),
            estimate=("refined_estimate", "first"),
        )
        .sort_values(
            ["earliest_seen", "latest_seen"] if sort_by_earliest else "latest_seen"
        )
    )

    agg_data["completed_time"].fillna(
        agg_data["latest_seen"],
        inplace=True,
    )

    if filter_incomplete_data:
        # only show products which have started after the first scrape date
        # and ended before the last date, to get the whole run accurately
        agg_data = agg_data.loc[
            agg_data["completed_time"] < datetime.datetime(2022, 6, 17)
        ]
        agg_data = agg_data.loc[
            agg_data["earliest_seen"] > datetime.datetime(2019, 11, 14)
        ]

    if filter_completed_data:
        agg_data = agg_data.loc[
            agg_data["latest_seen"] > datetime.datetime(2022, 6, 17)
        ]

    earliest_date = agg_data["earliest_seen"]
    latest_date = agg_data["completed_time"]

    estimate_date = agg_data["estimate"]

    labels = agg_data["product_name"]
    categories = agg_data["category"]

    color_map = {
        "unknown": "#73a7fa",
        "keyboards": "#7ddb72",
        "deskpads": "#bc0072",
        "keycaps": "#ff5949",
        "switches": "#9d6000",
    }

    colors = list(map(lambda category: color_map.get(category, "black"), categories))

    # Now convert them to matplotlib's internal format...
    earliest_date, latest_date, estimate_date = [
        mdates.date2num(item) for item in (earliest_date, latest_date, estimate_date)
    ]

    ypos = range(len(earliest_date))
    _, ax = plt.subplots()

    widths = earliest_date - latest_date
    for i in range(len(widths)):
        if widths[i] == 0:
            widths[i] = 10

    # Plot the data
    container = ax.barh(
        ypos,
        widths,
        left=latest_date,
        height=0.8,
        # align="center",
        color=(colors if show_categories else None),
    )

    if not filter_incomplete_data or filter_completed_data:
        plt.axvline(x=datetime.datetime(2022, 6, 17), color="red")
        plt.text(
            datetime.datetime(2022, 6, 20), 2, "Last\ncollected\nsnapshot", fontsize=16
        )

    if show_estimates:
        estimate_points = plt.scatter(
            estimate_date,
            ypos,
            s=40 if filter_completed_data else 10,
            c="black",
            marker="*",
            label="Initial Estimate (Worst Case)",
        )

    ax.get_yaxis().set_visible(False)
    ax.axis("auto")
    ax.xaxis.set_major_formatter(
        mdates.ConciseDateFormatter(ax.xaxis.get_major_locator())
    )
    ax.xaxis.set_minor_locator(mdates.MonthLocator())
    ax.xaxis_date()

    xmax = (
        datetime.datetime(2023, 5, 17)
        if show_estimates and not filter_incomplete_data
        else datetime.datetime(2022, 6, 17)
    )
    ax.set_xlim([datetime.datetime(2019, 11, 14), xmax])

    if show_product_labels:
        ax.bar_label(container, labels, fontsize=5)

    ax.legend(color_map.keys(), color_map.values())

    legend_handles = []

    if show_categories:
        legend_handles = list(
            map(
                lambda item: mpatches.Patch(color=item[1], label=item[0]),
                color_map.items(),
            ),
        )
    if show_estimates:
        legend_handles.append(estimate_points)

    if show_categories or show_estimates:
        ax.legend(handles=legend_handles)

    plt.title(title)
    plt.show()


def plot_delivery_times_over_time(
    df,
    filter_incomplete_data=True,
    filter_categories=None,
):
    agg_data = df.groupby("product_name").agg(
        earliest_seen=("scrape_time", "min"),
        latest_seen=("scrape_time", "max"),
        product_name=("product_name", "first"),
        category=("category", "first"),
        estimate=("refined_estimate", "first"),
        estimate_text=("estimate", "first"),
    )

    if filter_incomplete_data:
        agg_data = agg_data.loc[
            agg_data["latest_seen"] < datetime.datetime(2022, 6, 17)
        ]
        agg_data = agg_data.loc[
            agg_data["earliest_seen"] > datetime.datetime(2019, 11, 14)
        ]

    if filter_categories is not None:
        agg_data = agg_data.loc[agg_data["category"].isin(filter_categories)]

    agg_data["delivery_time"] = (
        agg_data["latest_seen"] - agg_data["earliest_seen"]
    ).apply(lambda t: round(t.days / 30.42))

    agg_data["estimated_time"] = (
        agg_data["estimate"] - agg_data["earliest_seen"]
    ).apply(lambda t: round(t.days / 30.42))

    # get the month the product was first seen
    agg_data["earliest_seen_month"] = pd.to_datetime(
        agg_data["earliest_seen"] + pd.offsets.MonthBegin(-1)
    ).dt.date

    agg_by_earliest_seen = agg_data.groupby("earliest_seen_month").agg(
        avg_delivery=("delivery_time", "mean"),
        avg_estimate=("estimated_time", "mean"),
        earliest_seen=("earliest_seen_month", "first"),
        count=("product_name", "count"),
    )

    # filter out snapshots that have fewer than 3 new products
    # agg_by_earliest_seen = agg_by_earliest_seen.loc[agg_by_earliest_seen["count"] >= 3]

    time = agg_by_earliest_seen["earliest_seen"]

    y1 = agg_by_earliest_seen["avg_delivery"]
    y2 = agg_by_earliest_seen["avg_estimate"]

    _, ax = plt.subplots()
    ax.xaxis.set_major_formatter(
        mdates.ConciseDateFormatter(ax.xaxis.get_major_locator())
    )
    ax.xaxis.set_minor_locator(mdates.MonthLocator())
    ax.xaxis_date()

    plt.plot(time, y1, label="Actual Delivery Time", marker=".")
    plt.plot(time, y2, label="Estimated Delivery Time", marker=".")

    plt.title(
        "Average Estimated vs. Actual Delivery Time by Month of First Appearance",
        fontsize=14,
    )
    plt.xlabel("Month of First Appearance")
    plt.ylabel("Delivery Time (Months)")
    plt.grid(True)
    plt.legend()
    plt.show()


def plot_num_exceeding_estimate(
    df,
    filter_categories=None,
):
    agg_data = df.groupby("product_name").agg(
        earliest_seen=("scrape_time", "min"),
        latest_seen=("scrape_time", "max"),
        product_name=("product_name", "first"),
        category=("category", "first"),
        estimate=("refined_estimate", "first"),
        estimate_text=("estimate", "first"),
    )

    # get the month the product was first seen in
    agg_data["earliest_seen_month"] = pd.to_datetime(
        agg_data["earliest_seen"] + pd.offsets.MonthBegin(-1)
    ).dt.date

    if filter_categories is not None:
        agg_data = agg_data.loc[agg_data["category"].isin(filter_categories)]

    delivered_early = agg_data.where(
        agg_data["latest_seen"] <= agg_data["estimate"]
    ).loc[agg_data["latest_seen"] < datetime.datetime(2022, 6, 17)]
    delivered_late = agg_data.where(agg_data["latest_seen"] > agg_data["estimate"])

    num_early = delivered_early.groupby("earliest_seen_month").agg(
        earliest_seen=("earliest_seen_month", "first"),
        count=("product_name", "count"),
    )

    num_late = delivered_late.groupby("earliest_seen_month").agg(
        earliest_seen=("earliest_seen_month", "first"),
        count=("product_name", "count"),
    )

    early_time = mdates.date2num(num_early["earliest_seen"])
    late_time = mdates.date2num(num_late["earliest_seen"])

    y1 = num_early["count"]
    y2 = num_late["count"]

    _, ax = plt.subplots()
    ax.xaxis.set_major_formatter(
        mdates.ConciseDateFormatter(ax.xaxis.get_major_locator())
    )
    ax.xaxis.set_minor_locator(mdates.MonthLocator())
    ax.xaxis_date()

    width = 10

    plt.bar(
        early_time - width / 2,
        y1,
        label="Delivered At or Before Estimated Date",
        width=width,
    )
    plt.bar(
        late_time + width / 2,
        y2,
        label="Delivered Later Than Estimated",
        width=width,
    )

    plt.title(
        "Number of Products Delivered Early/Late by Month of First Appearance",
        fontsize=14,
    )
    plt.xlabel("Month of First Appearance")
    plt.ylabel("Number of Products")

    plt.legend()
    plt.show()


def plot_estimate_times_over_time(
    df,
    filter_incomplete_data=True,
    filter_categories=None,
):
    agg_data = df.groupby("product_name").agg(
        earliest_seen=("scrape_time", "min"),
        latest_seen=("scrape_time", "max"),
        product_name=("product_name", "first"),
        category=("category", "first"),
        estimate=("refined_estimate", "first"),
        estimate_text=("estimate", "first"),
    )

    if filter_incomplete_data:
        agg_data = agg_data.loc[
            agg_data["latest_seen"] < datetime.datetime(2022, 6, 17)
        ]
        agg_data = agg_data.loc[
            agg_data["earliest_seen"] > datetime.datetime(2019, 11, 14)
        ]

    if filter_categories is not None:
        agg_data = agg_data.loc[agg_data["category"].isin(filter_categories)]

    agg_data["delivery_time"] = (
        agg_data["latest_seen"] - agg_data["earliest_seen"]
    ).apply(lambda t: round(t.days / 30.42))

    agg_data["estimated_time"] = (
        agg_data["estimate"] - agg_data["earliest_seen"]
    ).apply(lambda t: round(t.days / 30.42))

    x = mdates.date2num(agg_data["earliest_seen"])
    y = agg_data["estimated_time"]

    # Fit with polyfit
    b, m = polyfit(x, y, 1)

    _, ax = plt.subplots()

    plt.plot(x, y, ".")
    plt.plot(x, b + m * x, "-")
    plt.scatter(x, y, label="Estimated Delivery Time", marker=".")

    ax.xaxis.set_major_formatter(
        mdates.ConciseDateFormatter(ax.xaxis.get_major_locator())
    )
    ax.xaxis.set_minor_locator(mdates.MonthLocator())
    ax.xaxis_date()

    plt.title(
        "Estimated Delivery Time by Date of First Appearance",
        fontsize=14,
    )
    plt.xlabel("Date of First Appearance")
    plt.ylabel("Estimated Delivery Time (Months)")

    plt.show()


# plot_num_products()
# plot_product_updates(df, filter_incomplete_data=False)

# plot_product_updates(
#     df, filter_incomplete_data=False, show_estimates=False, show_categories=False
# )

plot_product_updates(
    df,
    filter_incomplete_data=False,
    show_estimates=False,
    show_categories=False,
    title="Timeline of All Novelkeys Products",
)

plot_product_updates(
    df,
    filter_incomplete_data=False,
    show_estimates=False,
    show_product_labels=True,
    title="Labeled Timeline of All Novelkeys Products",
)

plot_product_updates(
    df,
    filter_incomplete_data=True,
    show_estimates=True,
    show_product_labels=True,
    title="Timeline of Completed Novelkeys Products as of June 16, 2022",
)

plot_product_updates(
    df,
    filter_incomplete_data=False,
    filter_completed_data=True,
    show_estimates=True,
    show_product_labels=True,
    title="Timeline of In Progress Novelkeys Products as of June 16, 2022",
)

# plot_product_updates(df, show_categories=False)

# plot_product_updates(df, display_estimates=True, show_product_labels=True)
# plot_product_updates(df, display_estimates=False)

# plot_product_updates(
#     df, filter_incomplete_data=False, show_estimates=True, show_categories=True
# )

# plot_product_updates(df, filter_categories=["keycaps"])

plot_delivery_times_over_time(df)

plot_num_exceeding_estimate(df)

plot_estimate_times_over_time(df, filter_incomplete_data=False)
