import matplotlib
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.patches as mpatches
import datetime


def plot_product_updates(
    df,
    sort_by_earliest=True,
    show_categories=True,
    show_product_labels=False,
    show_delivered_products=True,
    show_in_progress_products=False,
    filter_categories=None,
    show_estimates=True,
    title="Timeline of Novelkeys Updates",
    filename="test.png",
):
    matplotlib.pyplot.figure(figsize=(5.0, 6.0))
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

    if show_delivered_products:
        # only show products which have started after the first scrape date
        # and ended before the last date, to get the whole run accurately
        agg_data = agg_data.loc[
            agg_data["completed_time"] < datetime.datetime(2022, 6, 17)
        ]
        agg_data = agg_data.loc[
            agg_data["earliest_seen"] > datetime.datetime(2019, 11, 14)
        ]

    if show_in_progress_products:
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
        height=0.7,
        # align="center",
        color=(colors if show_categories else None),
    )

    if show_in_progress_products:
        plt.axvline(x=datetime.datetime(2022, 6, 17), color="black", linestyle="dashed")
        plt.text(
            datetime.datetime(2022, 6, 20), 2, "Last collected\nsnapshot", fontsize=10
        )

    if show_estimates:
        estimate_points = plt.scatter(
            estimate_date,
            ypos,
            s=40 if show_in_progress_products else 10,
            c="black",
            marker="*",
            label="Initial Estimate",
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
        if show_estimates and not show_delivered_products
        else datetime.datetime(2022, 6, 17)
    )
    ax.set_xlim([datetime.datetime(2019, 11, 14), xmax])

    if show_product_labels:
        ax.bar_label(container, labels, fontsize=3)

    if show_estimates or show_categories:
        ax.legend(color_map.keys(), color_map.values(), loc="upper left")

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
        ax.legend(handles=legend_handles, loc="upper left")

    plt.title(title)

    plt.savefig(filename, dpi=200)
    plt.close()
