import matplotlib
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import datetime
import pandas as pd


def plot_delivery_times_over_time(
    df, filter_incomplete_data=True, filter_categories=None, filename="test.png"
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

    matplotlib.pyplot.figure(figsize=(5.0, 3.0))

    _, ax = plt.subplots()
    ax.xaxis.set_major_formatter(
        mdates.ConciseDateFormatter(ax.xaxis.get_major_locator())
    )
    ax.xaxis.set_minor_locator(mdates.MonthLocator())
    ax.xaxis_date()

    plt.plot(time, y1, label="Actual Delivery Time", marker=".")
    plt.plot(time, y2, label="Estimated Delivery Time", marker=".")

    plt.title(
        "Average Estimated vs. Actual Delivery Time Over Time",
        fontsize=14,
    )
    plt.xlabel("Month of First Appearance")
    plt.ylabel("Delivery Time (Months)")
    plt.grid(True)
    plt.legend(loc="upper right")

    plt.savefig(filename, dpi=200)
    plt.close()
