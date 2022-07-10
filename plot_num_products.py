import matplotlib
import matplotlib.pyplot as plt
import pandas as pd
import matplotlib.dates as mdates

import datetime


def plot_num_products(df_all, filename="test.png"):
    matplotlib.pyplot.figure(figsize=(5.0, 4.0))

    time = []
    num_products_in_progress = []
    num_products_completed = []

    df_all["scrape_month"] = pd.to_datetime(
        df_all["scrape_time"] + pd.offsets.MonthBegin(-1)
    ).dt.date

    num_completed = (
        df_all.loc[df_all["status"].isin(["completed", "Fulfilled!"])]
        .groupby(["scrape_month", "product_name"], as_index=False)["product_name"]
        .first()
        .groupby("scrape_month")
        .agg(count=("product_name", "count"), scrape_month=("scrape_month", "first"))
    )

    num_in_progress = (
        df_all.where(df_all["status"] != "completed")
        .where(df_all["status"] != "Fulfilled!")
        .groupby(["scrape_month", "product_name"], as_index=False)["product_name"]
        .first()
        .groupby("scrape_month")
        .agg(count=("product_name", "count"), scrape_month=("scrape_month", "first"))
        # .agg(count=("product_name", "count"), scrape_month=("scrape_month", "first"))
    )

    time = num_in_progress["scrape_month"]
    num_products_in_progress = num_in_progress["count"]
    num_products_completed = num_completed["count"]

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
    ax.legend(loc="upper left")

    plt.xlabel("Month")
    plt.ylabel("Number of Products")

    plt.axvline(x=datetime.datetime(2021, 8, 17), color="black", linestyle="dashed")
    plt.text(datetime.datetime(2021, 8, 20), 80, "Website Redesign", fontsize=7)

    plt.title("Number of products on Novelkeys Updates page by Month")
    plt.savefig(filename, dpi=200)
    plt.close()
