# /// script
# requires-python = ">=3.11"
# dependencies = ["pandas"]
# ///

import argparse
import sys
from pathlib import Path

import pandas as pd


def main():
    parser = argparse.ArgumentParser(
        description="Match sample collection dates to surgeries from cBioPortal.",
    )
    parser.add_argument("cbio_flatfile_dir", type=Path)
    parser.add_argument("--output", "-o", type=Path, default=None)
    args = parser.parse_args()

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

    merged = merged.rename(
        columns={
            "PATIENT_ID": "patient_id",
            "SAMPLE_ID": "sample_id",
            "START_DATE": "date",
            "PROCEDURE_DESCRIPTION": "surgery_name",
        }
    )[["patient_id", "sample_id", "date", "surgery_name"]]

    out = open(args.output, "w") if args.output else sys.stdout
    try:
        merged.to_csv(out, index=False)
    finally:
        if args.output:
            out.close()


if __name__ == "__main__":
    main()
