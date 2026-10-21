import logging
import os
import re
import shutil
import uuid
from typing import Annotated

import pandas as pd
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from utils.bias_analysis import run_bias_analysis
from utils.smote import run_smote

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# -------------------- APP SETUP --------------------
app = FastAPI(
    title="CSV Bias & SMOTE API",
    description=(
        "Uploads a CSV, reports class and subgroup distributions, and writes a "
        "class-balanced copy of the dataset using SMOTE."
    ),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Absolute paths, so the output location does not depend on the server's
# working directory.
UPLOAD_DIR = os.path.abspath("uploads")
OUTPUT_DIR = os.path.abspath("outputs")

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# -------------------- HELPERS --------------------
def create_output_dir(base_name: str) -> str:
    out_dir = os.path.join(OUTPUT_DIR, base_name)
    os.makedirs(out_dir, exist_ok=True)
    return out_dir

TARGET_NAME_HINTS = ("label", "target", "class", "outcome", "result", "churn", "y")


def detect_target(df: pd.DataFrame) -> str:
    """Pick the most likely target column.

    A column is a candidate if it has few distinct values (a class label) and
    is not constant. Constant columns are excluded because they carry no
    signal. Among the candidates, a column with a conventional target name
    wins; otherwise the last candidate is used, which is the usual convention
    for a target placed at the end of the dataset.
    """
    candidates = [
        c for c in df.columns
        if 1 < df[c].nunique() <= 20
    ]
    if not candidates:
        raise ValueError(
            "No suitable target column found. The target should be a numeric "
            "column with a small number of distinct values (e.g. 0/1)."
        )

    for col in candidates:
        if col.strip().lower() in TARGET_NAME_HINTS:
            return col

    return candidates[-1]


def resolve_target(df: pd.DataFrame, target: str | None) -> str:
    """Return the user-supplied target column, or auto-detect one."""
    if not target:
        return detect_target(df)
    if target not in df.columns:
        raise ValueError(
            f"Target column '{target}' is not present in the uploaded file. "
            f"Available columns: {list(df.columns)}"
        )
    return target


def compute_sample_weights(df: pd.DataFrame, sensitive: str, target: str) -> pd.DataFrame:
    """Inverse-frequency weights for each (sensitive, target) group."""
    # Name the computed columns so they cannot collide with a source column of
    # the same name, which would otherwise duplicate them as count_x/count_y.
    freq = (
        df.groupby([sensitive, target])
        .size()
        .reset_index(name="group_count")
    )
    total = freq["group_count"].sum()
    freq["sample_weight"] = total / (freq["group_count"] * len(freq))
    return freq


def generate_weighted_datasets(
    df: pd.DataFrame, target: str, sensitive_cols: list[str], out_dir: str
) -> None:
    for col in sensitive_cols:
        freq = compute_sample_weights(df, col, target)
        weighted = df.merge(freq, on=[col, target], how="left")
        weighted.to_csv(
            os.path.join(out_dir, f"weighted_{col}.csv"),
            index=False,
        )


# -------------------- API ENDPOINTS --------------------
@app.post("/process")
def process_csv(
    file: Annotated[UploadFile, File()],
    target: Annotated[str | None, Form()] = None,
):
    """Analyze an uploaded CSV and write the processed outputs.

    This is a synchronous endpoint on purpose: reading the upload, parsing
    the CSV and running SMOTE are all blocking operations, and FastAPI runs
    synchronous endpoints in a worker thread instead of on the event loop.
    """
    uid = uuid.uuid4().hex
    # The client-supplied filename is only used as a readable label, so strip
    # any path separators or parent-directory references from it before it is
    # joined onto the upload and output directories.
    stem = os.path.splitext(os.path.basename(file.filename or "dataset"))[0]
    stem = re.sub(r"[^A-Za-z0-9._-]", "_", stem).strip("._") or "dataset"
    base_name = f"{stem[:60]}_{uid}"

    upload_path = os.path.join(UPLOAD_DIR, f"{base_name}.csv")

    with open(upload_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        df = pd.read_csv(upload_path)
    except (OSError, ValueError) as exc:
        raise HTTPException(
            status_code=400, detail=f"Could not read the uploaded file as CSV: {exc}"
        ) from exc

    out_dir = create_output_dir(base_name)

    try:
        target_col = resolve_target(df, target)
        sensitive_cols = run_bias_analysis(df, target_col, out_dir)
        run_smote(df, target_col, out_dir)
        generate_weighted_datasets(df, target_col, sensitive_cols, out_dir)
    except (ValueError, KeyError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    logger.info("Processed %s (target=%s)", base_name, target_col)

    files = sorted(os.listdir(out_dir))

    return {
        "folder": base_name,
        "target": target_col,
        "files": [
            f"/download/{base_name}/{f}" for f in files
        ],
    }


@app.get("/download/{folder}/{filename}")
def download_file(folder: str, filename: str):
    # Reject any name that tries to escape the output directory. The route
    # already blocks "/" in the path, but ".." on its own is enough to walk up
    # a directory, so the resolved path is checked against the base directory.
    output_root = os.path.realpath(OUTPUT_DIR)
    file_path = os.path.realpath(os.path.join(output_root, folder, filename))
    if not file_path.startswith(output_root + os.sep):
        raise HTTPException(status_code=400, detail="Invalid file path.")
    if not os.path.isfile(file_path):
        raise HTTPException(status_code=404, detail="File not found.")
    return FileResponse(file_path, filename=filename)
