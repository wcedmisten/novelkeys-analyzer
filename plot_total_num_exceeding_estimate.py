import matplotlib
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.patches as mpatches
import datetime


def plot_total_num_exceeding_estimate(
    df,
    title="Product Delivery Status from Nov. 2019 to Jun. 2022",
    filename="total-delivery-status.png",
):
    agg_data = df.groupby("product_name").agg(
        earliest_seen=("scrape_time", "min"),
        latest_seen=("scrape_time", "max"),
        product_name=("product_name", "first"),
        category=("category", "first"),
        estimate=("refined_estimate", "first"),
        estimate_text=("estimate", "first"),
        completed_time=("completed_time", "first"),
    )

    # go by completed status
    officially_completed = agg_data[agg_data.completed_time.notnull()]

    # not officially marked as "completed", but was removed from the
    # updates page. Use the last seen time
    unofficially_completed = agg_data[agg_data.completed_time.isnull()].loc[
        agg_data["latest_seen"] < datetime.datetime(2022, 6, 17)
    ]

    # in progress
    in_progress = agg_data[agg_data.completed_time.isnull()].loc[
        agg_data["latest_seen"] >= datetime.datetime(2022, 6, 17)
    ]

    delivered_early = officially_completed.loc[
        officially_completed["completed_time"] <= officially_completed["estimate"]
    ]

    delivered_late = officially_completed.loc[
        officially_completed["completed_time"] > officially_completed["estimate"]
    ]

    unofficially_early = unofficially_completed.loc[
        unofficially_completed["latest_seen"] <= unofficially_completed["estimate"]
    ]

    unofficially_late = unofficially_completed.loc[
        unofficially_completed["latest_seen"] > unofficially_completed["estimate"]
    ]

    # still in progress on the website as of last snapshot
    will_deliver_late = in_progress.loc[
        in_progress["latest_seen"] > in_progress["estimate"]
    ]

    in_progress_unknown = in_progress.loc[
        in_progress["latest_seen"] < in_progress["estimate"]
    ]

    _, ax = plt.subplots()

    labels = [
        "Delivered Late",
        "In Progress",
    ]

    container = ax.barh(
        2,
        len(delivered_early) + len(unofficially_early),
        color="#7ddb72",
    )

    container1 = ax.barh(
        [0, 1],
        [
            len(delivered_late) + len(unofficially_late),
            len(in_progress_unknown),
        ],
        color=["#f54e42", "#73a7fa"],
    )

    container2 = ax.barh(
        0, len(will_deliver_late), left=len(delivered_late), color="#f57369"
    )

    ax.get_yaxis().set_visible(False)
    # ax.axis("auto")

    ax.bar_label(container, [" Delivered Early"], fontsize="14", label_type="center")
    ax.bar_label(container1, labels, label_type="center", fontsize="14")
    ax.bar_label(container2, ["Will Deliver Late"], label_type="center", fontsize="14")

    plt.xlabel("Number of Products", fontsize=14)

    plt.title(title, fontsize="14")

    plt.savefig(filename, dpi=200)
    plt.close()
