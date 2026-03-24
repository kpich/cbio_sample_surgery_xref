# /// script
# requires-python = ">=3.11"
# dependencies = ["pandas", "matplotlib"]
# ///

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

plt.rcParams["font.family"] = "Arial"
plt.rcParams["font.size"] = 11

COLORS = {
    "biopsy": "#4e79a7",
    "resection": "#f28e2b",
    "unknown": "#bab0ac",
}


def classify_surgery(names: pd.Series) -> str:
    clean = [n for n in names if pd.notna(n)]
    if any("BIOPS" in n for n in clean):
        return "biopsy"
    if any("RESECT" in n for n in clean):
        return "resection"
    return "unknown"


def main():
    parser = argparse.ArgumentParser(
        description="Plot surgery type distribution by oncotree code.",
    )
    parser.add_argument("cbio_flatfile_dir", type=Path)
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        default=Path("surg_dist_by_oncotree.png"),
    )
    args = parser.parse_args()

    clinical = pd.read_csv(
        args.cbio_flatfile_dir / "data_clinical_sample.txt",
        sep="\t",
        comment="#",
        usecols=["SAMPLE_ID", "ONCOTREE_CODE"],
    )

    specimens = pd.read_csv(
        args.cbio_flatfile_dir / "data_timeline_specimen_surgery.txt",
        sep="\t",
        usecols=["PATIENT_ID", "START_DATE", "SAMPLE_ID"],
    )

    surgeries = pd.read_csv(
        args.cbio_flatfile_dir / "data_timeline_surgery.txt",
        sep="\t",
        usecols=["PATIENT_ID", "START_DATE", "PROCEDURE_DESCRIPTION"],
    )

    merged = specimens.merge(surgeries, on=["PATIENT_ID", "START_DATE"], how="left")

    sample_class = (
        merged.groupby("SAMPLE_ID")["PROCEDURE_DESCRIPTION"]
        .apply(classify_surgery)
        .reset_index()
        .rename(columns={"PROCEDURE_DESCRIPTION": "category"})
    )

    df = clinical.merge(sample_class, on="SAMPLE_ID", how="left")
    df["category"] = df["category"].fillna("unknown")

    top50 = df["ONCOTREE_CODE"].value_counts().head(50).index.tolist()
    df = df[df["ONCOTREE_CODE"].isin(top50)]

    counts = df.groupby(["ONCOTREE_CODE", "category"]).size().unstack(fill_value=0)
    for cat in COLORS:
        if cat not in counts.columns:
            counts[cat] = 0
    counts = counts[list(COLORS.keys())].loc[top50]

    fig, axes = plt.subplots(5, 10, sharey="row", figsize=(26, 16))
    fig.subplots_adjust(hspace=0.35, wspace=0.08)

    bar_handles = None
    for i, oncotree in enumerate(top50):
        row, col = divmod(i, 10)
        ax = axes[row, col]
        row_data = counts.loc[oncotree]
        bottom = 0
        bars = []
        for cat, color in COLORS.items():
            val = row_data[cat]
            b = ax.bar(0, val, bottom=bottom, color=color, width=0.6)
            bars.append(b)
            bottom += val
        ax.set_xticks([0])
        ax.set_xticklabels([oncotree], rotation=0, ha="center", fontsize=25)
        ax.tick_params(axis="x", length=0)
        ax.set_xlim(-0.5, 0.5)
        for spine in ax.spines.values():
            spine.set_visible(False)
        ax.yaxis.grid(True, linestyle=":", color="#aaaaaa", linewidth=1.5, zorder=0)
        ax.set_axisbelow(True)
        ax.tick_params(axis="y", length=0, labelsize=22)
        if bar_handles is None:
            bar_handles = bars

    for i in range(len(top50), 50):
        row, col = divmod(i, 10)
        axes[row, col].set_visible(False)

    fig.legend(
        bar_handles,
        list(COLORS.keys()),
        loc="upper left",
        bbox_to_anchor=(1.01, 1.0),
        ncol=1,
        frameon=False,
        handlelength=1,
        handleheight=1,
        fontsize=28,
    )

    plt.savefig(args.output, dpi=150, bbox_inches="tight")
    print(f"Saved to {args.output}")


if __name__ == "__main__":
    main()
