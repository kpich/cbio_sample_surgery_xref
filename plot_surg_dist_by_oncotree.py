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


BIOPSY_TERMS = {"BIOPS", "ASPIRATION", "SAMPLING"}
RESECTION_TERMS = {
    "RESECT",
    "LOBECTOMY",
    "HYSTERECTOMY",
    "EXCISION",
    "PROSTATECTOMY",
    "COLECTOMY",
    "PANCREATECTOMY",
    "NEPHRECTOMY",
    "CYSTECTOMY",
    "HEPATECTOMY",
    "OOPHORECTOMY",
    "WHIPPLE",
    "CRANIOTOMY",
    "CRANIECTOMY",
    "SPLENECTOMY",
    "GASTRECTOMY",
    "MASTECTOMY",
    "THYROIDECTOMY",
    "ADRENALECTOMY",
}


def classify_surgery(names: pd.Series) -> str:
    clean = [n for n in names if pd.notna(n)]
    if any(term in n for n in clean for term in RESECTION_TERMS):
        return "resection"
    if any(term in n for n in clean for term in BIOPSY_TERMS):
        return "biopsy"
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
        usecols=["SAMPLE_ID", "ONCOTREE_CODE", "SAMPLE_TYPE"],
    )
    clinical["sample_group"] = clinical["SAMPLE_TYPE"].map(
        lambda t: "P"
        if t == "Primary"
        else ("M" if t == "Metastasis" else ("L" if t == "Local Recurrence" else "U"))
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

    GROUPS = ["P", "M", "L", "U"]
    BAR_POSITIONS = {"P": -0.45, "M": -0.15, "L": 0.15, "U": 0.45}
    BAR_WIDTH = 0.28

    counts = (
        df.groupby(["ONCOTREE_CODE", "sample_group", "category"])
        .size()
        .unstack(fill_value=0)
    )
    for cat in COLORS:
        if cat not in counts.columns:
            counts[cat] = 0
    counts = counts[list(COLORS.keys())]

    fig, axes = plt.subplots(5, 10, sharey="row", figsize=(26, 16))
    fig.subplots_adjust(hspace=0.35, wspace=0.08)

    bar_handles = None
    for i, oncotree in enumerate(top50):
        row, col = divmod(i, 10)
        ax = axes[row, col]
        bars = []
        for grp in GROUPS:
            xpos = BAR_POSITIONS[grp]
            if (oncotree, grp) in counts.index:
                row_data = counts.loc[(oncotree, grp)]
            else:
                row_data = {cat: 0 for cat in COLORS}
            bottom = 0
            for cat, color in COLORS.items():
                val = row_data[cat]
                b = ax.bar(xpos, val, bottom=bottom, color=color, width=BAR_WIDTH)
                if grp == "P":
                    bars.append(b)
                bottom += val
        ax.set_xticks(list(BAR_POSITIONS.values()))
        ax.set_xticklabels(GROUPS, rotation=0, ha="center", fontsize=20)
        ax.tick_params(axis="x", length=0)
        ax.set_xlim(-0.7, 0.7)
        # oncotree label centered below
        ax.set_xlabel(oncotree, fontsize=22, labelpad=4)
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
        bbox_to_anchor=(1.002, 0.95),
        ncol=1,
        frameon=False,
        handlelength=1,
        handleheight=1,
        fontsize=28,
    )

    group_labels = [
        "P — Primary",
        "M — Metastasis",
        "L — Local Recurrence",
        "U — Unknown",
    ]
    fig.text(
        1.002,
        0.95 - 0.13,
        "\n".join(group_labels),
        va="top",
        ha="left",
        fontsize=22,
        linespacing=1.8,
    )

    plt.savefig(args.output, dpi=150, bbox_inches="tight")
    print(f"Saved to {args.output}")


if __name__ == "__main__":
    main()
