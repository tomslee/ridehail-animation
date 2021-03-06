#!/usr/bin/python3

import os
import sys
import json
import matplotlib.pyplot as plt
import matplotlib as mpl
import seaborn as sns

mpl.rcParams['figure.dpi'] = 90
mpl.rcParams['savefig.dpi'] = 100
sns.set()
sns.set_palette("muted")


def fit_function(x, a, b, c):
    return (a + b / (x + c))


def main():
    try:
        if os.path.isfile(sys.argv[1]):
            input_file = sys.argv[1]
            filename_root = os.path.splitext(os.path.basename(input_file))[0]
    except Exception:
        print(
            "Usage:\n\tpython rhplotsequence.py <jsonl_file>"
            "\n\n\twhere <jsonl_file> is the output from a run of ridehail.py"
            "\n\twith run_sequence=True")
        exit(-1)
    with open(input_file) as f:
        lines = f.readlines()

    sequence = []
    for line in lines:
        try:
            sequence.append(json.loads(line))
        except json.decoder.JSONDecodeError:
            pass

    driver_costs = [sim["equilibrate"]["driver_cost"] for sim in sequence]
    wait_costs = [sim["equilibrate"]["wait_cost"] for sim in sequence]
    driver_count_scalefactor = 10
    final_driver_counts = [
        driver_count_scalefactor * sim["output"]["mean_driver_count"]
        for sim in sequence
    ]
    request_rate_scalefactor = 100
    final_request_rates = [
        request_rate_scalefactor * sim["output"]["mean_request_rate"]
        for sim in sequence
    ]

    fig = plt.figure(figsize=(16, 8))
    gridspec = fig.add_gridspec(1, 2)
    ax1 = fig.add_subplot(gridspec[0, 0])
    palette = sns.color_palette()
    palette_index = 0
    ax1.scatter(driver_costs,
                wait_costs,
                color=palette[palette_index],
                alpha=0.6,
                marker="o",
                s=final_driver_counts)
    ax1.set_xlabel("Driver Cost")
    ax1.set_ylabel("Wait Cost")
    ax1.set_title("Final driver counts")
    # for i, dc in enumerate(final_driver_counts):
    # dc = dc / driver_count_scalefactor
    # ax1.annotate(f"{dc:.0f}", (driver_costs[i], wait_costs[i]),
    # fontsize=10)
    ax2 = fig.add_subplot(gridspec[0, 1])
    palette_index += 1
    ax2.scatter(driver_costs,
                wait_costs,
                color=palette[palette_index],
                alpha=0.6,
                marker="o",
                s=final_request_rates)
    ax2.set_xlabel("Driver Cost")
    ax2.set_ylabel("Wait Cost")
    ax2.set_title("Final request rates")
    # for i, rr in enumerate(final_request_rates):
    # rr = rr / request_rate_scalefactor
    # ax2.annotate(f"{rr:.1f}", (driver_costs[i], wait_costs[i]),
    # fontsize=10)
    filename = f"img/{filename_root}_equil.png"
    print(f"Writing file {filename}")
    plt.savefig(filename)


if __name__ == '__main__':
    main()
