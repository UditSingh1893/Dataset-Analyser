import logging
import warnings

import pandas as pd
from imblearn.over_sampling import SMOTE, SMOTENC
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler

from utils.plotting import plot_bar

logger = logging.getLogger(__name__)


def run_smote(df: pd.DataFrame, target: str, out_dir: str) -> None:
    """Balance the classes of ``df`` and write one balanced CSV.

    The dataset is never split, so there is no train/test leakage to guard
    against: every output row is either an original row or a synthetic one, and
    all of them come from the same source distribution.
    """
    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    if target not in numeric_cols:
        raise ValueError(
            f"Target column '{target}' is not numeric, so it cannot be used as "
            "a SMOTE label. Rename it to a numeric class label (0/1) and re-upload."
        )

    y = df[target].astype(int)
    before = y.value_counts()

    # Every column except the target is a feature. Keeping the original column
    # order means the output CSV matches the uploaded dataset's layout.
    feature_cols = [c for c in df.columns if c != target]

    # Categorical features are handled natively by SMOTENC, so they survive
    # into the output instead of being silently dropped.
    cat_cols = [
        c for c in df.select_dtypes(include=["object", "category"]).columns
        if c in feature_cols
    ]
    cont_cols = [c for c in feature_cols if c not in cat_cols]

    X = df[feature_cols].copy()

    # SMOTE's nearest-neighbour search cannot handle missing values, so fill
    # them with the column median. This keeps synthetic rows in the same units
    # as the original data.
    #
    # A column that is entirely empty carries no signal, and the imputer drops
    # it from its output, which would misalign the columns. Such columns are
    # filled with 0 instead so the layout stays intact.
    if cont_cols:
        all_empty = [c for c in cont_cols if X[c].isna().all()]
        imputable = [c for c in cont_cols if c not in all_empty]
        if imputable and X[imputable].isna().any().any():
            imputer = SimpleImputer(strategy="median")
            X[imputable] = imputer.fit_transform(X[imputable])
        for c in all_empty:
            X[c] = 0.0

    # Scale the continuous columns so no single feature dominates the
    # distance calculation that SMOTE relies on.
    scaler = StandardScaler()
    if cont_cols:
        X_scaled = X.copy()
        X_scaled[cont_cols] = scaler.fit_transform(X[cont_cols])
    else:
        X_scaled = X

    # SMOTE needs at least 6 samples in the minority class for its default
    # k=5 neighbours. On a very small minority it cannot run at all.
    min_class = int(y.value_counts().min())
    if min_class < 6:
        warnings.warn(
            f"The smallest class has only {min_class} sample(s), which is too "
            "few for SMOTE (it needs at least 6). The dataset was returned "
            "unbalanced."
        )
        X_resampled, y_resampled = X_scaled, y
    elif not cat_cols:
        # Nothing categorical to preserve, so plain SMOTE is used. SMOTENC
        # requires at least one categorical feature and would refuse to run.
        smote = SMOTE(random_state=42)
        X_resampled, y_resampled = smote.fit_resample(X_scaled, y)
    else:
        # A boolean mask keeps SMOTENC aware of which columns are categorical
        # regardless of their position, so the original column order is kept.
        cat_mask = [col in cat_cols for col in feature_cols]
        smote = SMOTENC(
            categorical_features=cat_mask,
            random_state=42,
        )
        X_resampled, y_resampled = smote.fit_resample(X_scaled, y)

    # Undo the scaling so the output keeps the original units and column order.
    X_resampled = pd.DataFrame(X_resampled, columns=X.columns)
    if cont_cols:
        X_resampled[cont_cols] = scaler.inverse_transform(X_resampled[cont_cols])

    # Restore the original column dtypes. The scale round-trip turns integer
    # columns into floats, and SMOTENC decodes categoricals as objects, so
    # cast them back. Integer columns are rounded first so that synthetic
    # values are not truncated towards zero.
    for col in X.columns:
        original_dtype = df[col].dtype
        if pd.api.types.is_integer_dtype(original_dtype):
            X_resampled[col] = X_resampled[col].round().astype(original_dtype)
        else:
            X_resampled[col] = X_resampled[col].astype(original_dtype)

    after = pd.Series(y_resampled).value_counts()

    plot_bar(before, "Class Distribution Before SMOTE", f"{out_dir}/smote_before.png")
    plot_bar(after, "Class Distribution After SMOTE", f"{out_dir}/smote_after.png")

    pd.concat([X_resampled, y_resampled], axis=1).to_csv(
        f"{out_dir}/smote_resampled.csv", index=False
    )

    logger.info(
        "SMOTE oversampling completed. Before: %s. After: %s.",
        before.to_dict(),
        after.to_dict(),
    )
