import matplotlib
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import datetime
import pandas as pd


def plot_num_exceeding_estimate(df, filter_categories=None, filename="test.png"):
    matplotlib.pyplot.figure(figsize=(5.0, 3.0))

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
        label="Delivered At/Before Estimate",
        width=width,
    )
    plt.bar(
        late_time + width / 2,
        y2,
        label="Delivered After Estimate",
        width=width,
    )

    plt.title(
        "Number of Products Delivered Early/Late Over Time",
        fontsize=14,
    )
    plt.xlabel("Month of First Appearance")
    plt.ylabel("Number of Products")

    plt.legend(loc="upper right")
    plt.savefig(filename, dpi=200)
    plt.close()
