import matplotlib
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import datetime
from numpy.polynomial.polynomial import polyfit


def plot_estimate_times_over_time(
    df, filter_incomplete_data=True, filter_categories=None, filename="test.png"
):
    matplotlib.pyplot.figure(figsize=(5.0, 3.0))

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

    plt.savefig(filename, dpi=200)
    plt.close()
