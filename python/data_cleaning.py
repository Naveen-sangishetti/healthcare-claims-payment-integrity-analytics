import pandas as pd
from pathlib import Path

# ============================================================
# 1. LOAD RAW DATA
# ============================================================

DATA_DIR = Path("data")

claims = pd.read_csv(DATA_DIR / "claims.csv")
patients = pd.read_csv(DATA_DIR / "patients.csv")
providers = pd.read_csv(DATA_DIR / "providers.csv")
payments = pd.read_csv(DATA_DIR / "payments.csv")

print("Raw datasets loaded successfully.")

print(f"Claims:    {claims.shape}")
print(f"Patients:  {patients.shape}")
print(f"Providers: {providers.shape}")
print(f"Payments:  {payments.shape}")


# ============================================================
# 2. STANDARDIZE COLUMN NAMES
# ============================================================

def clean_column_names(df):
    df.columns = (
        df.columns
        .str.strip()
        .str.lower()
        .str.replace(" ", "_")
    )
    return df


claims = clean_column_names(claims)
patients = clean_column_names(patients)
providers = clean_column_names(providers)
payments = clean_column_names(payments)


# ============================================================
# 3. REMOVE EXACT DUPLICATE ROWS
# ============================================================

print("\nDuplicate rows before cleaning:")

print("Claims:", claims.duplicated().sum())
print("Patients:", patients.duplicated().sum())
print("Providers:", providers.duplicated().sum())
print("Payments:", payments.duplicated().sum())

claims = claims.drop_duplicates()
patients = patients.drop_duplicates()
providers = providers.drop_duplicates()
payments = payments.drop_duplicates()

print("\nDuplicate rows after cleaning:")

print("Claims:", claims.duplicated().sum())
print("Patients:", patients.duplicated().sum())
print("Providers:", providers.duplicated().sum())
print("Payments:", payments.duplicated().sum())


# ============================================================
# 4. FIX DATA TYPES
# ============================================================

# ID columns
claims["claim_id"] = pd.to_numeric(
    claims["claim_id"], errors="coerce"
).astype("Int64")

claims["patient_id"] = pd.to_numeric(
    claims["patient_id"], errors="coerce"
).astype("Int64")

claims["provider_id"] = pd.to_numeric(
    claims["provider_id"], errors="coerce"
).astype("Int64")


patients["patient_id"] = pd.to_numeric(
    patients["patient_id"], errors="coerce"
).astype("Int64")

providers["provider_id"] = pd.to_numeric(
    providers["provider_id"], errors="coerce"
).astype("Int64")

payments["claim_id"] = pd.to_numeric(
    payments["claim_id"], errors="coerce"
).astype("Int64")

payments["patient_id"] = pd.to_numeric(
    payments["patient_id"], errors="coerce"
).astype("Int64")

payments["provider_id"] = pd.to_numeric(
    payments["provider_id"], errors="coerce"
).astype("Int64")

payments["payment_id"] = pd.to_numeric(
    payments["payment_id"], errors="coerce"
).astype("Int64")


# ============================================================
# 5. CONVERT DATES
# ============================================================

claims["claim_date"] = pd.to_datetime(
    claims["claim_date"], errors="coerce"
)

payments["claim_date"] = pd.to_datetime(
    payments["claim_date"], errors="coerce"
)

payments["payment_date"] = pd.to_datetime(
    payments["payment_date"], errors="coerce"
)


# ============================================================
# 6. CONVERT FINANCIAL AMOUNTS
# ============================================================

claims["claim_amount"] = pd.to_numeric(
    claims["claim_amount"], errors="coerce"
)

payments["claim_amount"] = pd.to_numeric(
    payments["claim_amount"], errors="coerce"
)

payments["payment_amount"] = pd.to_numeric(
    payments["payment_amount"], errors="coerce"
)


# ============================================================
# 7. BASIC DATA QUALITY CHECKS
# ============================================================

print("\nMissing values:")

for name, df in {
    "Claims": claims,
    "Patients": patients,
    "Providers": providers,
    "Payments": payments
}.items():

    print(f"\n{name}")
    print(df.isnull().sum())


# ============================================================
# 8. INVALID FINANCIAL VALUES
# ============================================================

print("\nInvalid claim amounts:")
print((claims["claim_amount"] <= 0).sum())

print("\nInvalid payment amounts:")
print((payments["payment_amount"] < 0).sum())


# ============================================================
# 9. PAYMENT DATE QUALITY CHECK
# ============================================================

payments["payment_date_issue"] = (
    payments["payment_date"] < payments["claim_date"]
)

print("\nPayment dates before claim dates:")
print(payments["payment_date_issue"].sum())


print("\nCleaning and validation stage completed.")

# ============================================================
# 10. REFERENTIAL INTEGRITY CHECKS
# ============================================================

print("\n" + "=" * 50)
print("REFERENTIAL INTEGRITY CHECKS")
print("=" * 50)

# Claims → Patients
missing_patients = (
    ~claims["patient_id"].isin(patients["patient_id"])
).sum()

print("Claims with missing patient IDs:", missing_patients)


# Claims → Providers
missing_providers = (
    ~claims["provider_id"].isin(providers["provider_id"])
).sum()

print("Claims with missing provider IDs:", missing_providers)


# Claims → Payments
claims_with_payment = (
    claims["claim_id"].isin(payments["claim_id"])
).sum()

claims_without_payment = len(claims) - claims_with_payment

print("Claims with payment records:", claims_with_payment)
print("Claims without payment records:", claims_without_payment)

# ============================================================
# 11. CREATE ANALYTICAL DATASET
# ============================================================

print("\n" + "=" * 50)
print("CREATING PAYMENT INTEGRITY DATASET")
print("=" * 50)

# Select useful patient fields only
patients_analysis = patients[
    [
        "patient_id",
        "age",
        "gender",
        "city",
        "state"
    ]
].copy()

# Select useful provider fields only
providers_analysis = providers[
    [
        "provider_id",
        "name",
        "specialty",
        "city",
        "state"
    ]
].copy()

# Select payment fields
payments_analysis = payments[
    [
        "claim_id",
        "payment_id",
        "payment_date",
        "payment_amount",
        "payment_date_issue"
    ]
].copy()

# Join claims with patient information
analysis = claims.merge(
    patients_analysis,
    on="patient_id",
    how="left",
    suffixes=("", "_patient")
)

# Join provider information
analysis = analysis.merge(
    providers_analysis,
    on="provider_id",
    how="left",
    suffixes=("", "_provider")
)

# Join payment information
analysis = analysis.merge(
    payments_analysis,
    on="claim_id",
    how="left"
)

print("Final analytical dataset shape:", analysis.shape)

print("\nAnalytical dataset columns:")
print(analysis.columns.tolist())
# Check whether any claim has multiple payment records
payment_counts = payments.groupby("claim_id").size()

multiple_payment_claims = (
    payment_counts[payment_counts > 1]
)

print(
    "\nClaims with multiple payment records:",
    len(multiple_payment_claims)
)

print(
    "Maximum payments for one claim:",
    payment_counts.max()
)

# ============================================================
# 12. PAYMENT INTEGRITY METRICS
# ============================================================

print("\n" + "=" * 50)
print("CREATING PAYMENT INTEGRITY METRICS")
print("=" * 50)

# Payment variance
analysis["payment_variance"] = (
    analysis["claim_amount"] - analysis["payment_amount"]
)

# Payment ratio
analysis["payment_ratio"] = (
    analysis["payment_amount"] / analysis["claim_amount"]
)

# Overpayment flag
analysis["overpayment_flag"] = (
    analysis["payment_amount"] > analysis["claim_amount"]
).astype(int)

# Missing payment flag
analysis["missing_payment_flag"] = (
    analysis["payment_amount"].isna()
).astype(int)

# Payment date issue
analysis["payment_date_issue"] = (
    analysis["payment_date_issue"]
    .fillna(False)
    .astype(int)
)

# Claim month
analysis["claim_month"] = (
    analysis["claim_date"]
    .dt.to_period("M")
    .astype(str)
)

print("\nPayment integrity metrics created.")

print("\nOverpayment cases:")
print(analysis["overpayment_flag"].sum())

print("\nMissing payment cases:")
print(analysis["missing_payment_flag"].sum())

print("\nPayment date issues:")
print(analysis["payment_date_issue"].sum())

# ============================================================
# 13. PROVIDER RISK ANALYSIS
# ============================================================

print("\n" + "=" * 50)
print("CREATING PROVIDER RISK ANALYSIS")
print("=" * 50)

# ------------------------------------------------------------
# Create one unique provider record per provider_id
# ------------------------------------------------------------

provider_dimension = (
    providers[
        [
            "provider_id",
            "name",
            "specialty",
            "state"
        ]
    ]
    .drop_duplicates(subset=["provider_id"])
)

# ------------------------------------------------------------
# Calculate provider-level metrics
# ------------------------------------------------------------

provider_metrics = (
    analysis
    .groupby("provider_id", as_index=False)
    .agg(
        claim_count=("claim_id", "count"),
        total_claim_amount=("claim_amount", "sum"),
        average_claim_amount=("claim_amount", "mean"),
        total_payment_amount=("payment_amount", "sum"),
        average_payment_amount=("payment_amount", "mean"),
        missing_payment_claims=("missing_payment_flag", "sum"),
        payment_date_issues=("payment_date_issue", "sum")
    )
)

# ------------------------------------------------------------
# Calculate rates
# ------------------------------------------------------------

provider_metrics["missing_payment_rate"] = (
    provider_metrics["missing_payment_claims"]
    / provider_metrics["claim_count"]
)

provider_metrics["payment_date_issue_rate"] = (
    provider_metrics["payment_date_issues"]
    / provider_metrics["claim_count"]
)

# ------------------------------------------------------------
# Create provider risk score
# ------------------------------------------------------------

provider_metrics["risk_score"] = (
    provider_metrics["missing_payment_rate"] * 50
    +
    provider_metrics["payment_date_issue_rate"] * 50
)

# ------------------------------------------------------------
# Assign risk category
# ------------------------------------------------------------

provider_metrics["risk_category"] = pd.cut(
    provider_metrics["risk_score"],
    bins=[-0.01, 20, 50, 100],
    labels=["Low", "Medium", "High"]
)

# ------------------------------------------------------------
# Attach provider information
# ------------------------------------------------------------

provider_analysis = provider_metrics.merge(
    provider_dimension,
    on="provider_id",
    how="left"
)

# ------------------------------------------------------------
# Display top providers
# ------------------------------------------------------------

print("\nUnique providers analyzed:", len(provider_analysis))

print("\nTop 10 providers by risk score:")

print(
    provider_analysis
    .sort_values(
        ["risk_score", "claim_count"],
        ascending=[False, False]
    )
    [
        [
            "provider_id",
            "name",
            "specialty",
            "claim_count",
            "total_claim_amount",
            "total_payment_amount",
            "missing_payment_rate",
            "payment_date_issue_rate",
            "risk_score",
            "risk_category"
        ]
    ]
    .head(10)
)
# ============================================================
# 14. CLAIM-LEVEL ANOMALY ANALYSIS
# ============================================================

print("\n" + "=" * 50)
print("CREATING CLAIM ANOMALY ANALYSIS")
print("=" * 50)

# ------------------------------------------------------------
# 1. High-value claim threshold
# ------------------------------------------------------------

high_value_threshold = analysis["claim_amount"].quantile(0.95)

print(
    "\n95th percentile claim amount:",
    round(high_value_threshold, 2)
)

analysis["high_value_claim_flag"] = (
    analysis["claim_amount"] >= high_value_threshold
).astype(int)


# ------------------------------------------------------------
# 2. Provider average claim amount
# ------------------------------------------------------------

provider_avg_claim = (
    analysis
    .groupby("provider_id")["claim_amount"]
    .transform("mean")
)

analysis["provider_average_claim"] = provider_avg_claim


# ------------------------------------------------------------
# 3. Provider deviation
# ------------------------------------------------------------

analysis["provider_claim_deviation"] = (
    analysis["claim_amount"]
    / analysis["provider_average_claim"]
)


# ------------------------------------------------------------
# 4. Provider unusually high claim
# ------------------------------------------------------------

analysis["provider_high_claim_flag"] = (
    analysis["provider_claim_deviation"] >= 2
).astype(int)


# ------------------------------------------------------------
# 5. Total anomaly indicators
# ------------------------------------------------------------

analysis["anomaly_indicator_count"] = (
    analysis["payment_date_issue"]
    + analysis["missing_payment_flag"]
    + analysis["high_value_claim_flag"]
    + analysis["provider_high_claim_flag"]
)


# ------------------------------------------------------------
# 6. Claim risk category
# ------------------------------------------------------------

analysis["claim_risk_category"] = pd.cut(
    analysis["anomaly_indicator_count"],
    bins=[-1, 0, 1, 2, 4],
    labels=[
        "Low",
        "Medium",
        "High",
        "Critical"
    ]
)


print("\nHigh-value claims:")
print(analysis["high_value_claim_flag"].sum())

print("\nProvider-high-value claims:")
print(analysis["provider_high_claim_flag"].sum())

print("\nAnomaly indicator distribution:")
print(
    analysis["anomaly_indicator_count"]
    .value_counts()
    .sort_index()
)

print("\nClaim risk distribution:")
print(
    analysis["claim_risk_category"]
    .value_counts()
)
# ============================================================
# 15. EXPORT CLEAN ANALYTICAL DATASETS
# ============================================================

OUTPUT_DIR = Path("data/processed")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Export cleaned base datasets
claims.to_csv(
    OUTPUT_DIR / "claims_clean.csv",
    index=False
)

patients.to_csv(
    OUTPUT_DIR / "patients_clean.csv",
    index=False
)

providers.to_csv(
    OUTPUT_DIR / "providers_clean.csv",
    index=False
)

payments.to_csv(
    OUTPUT_DIR / "payments_clean.csv",
    index=False
)

# Export main analytical dataset
analysis.to_csv(
    OUTPUT_DIR / "payment_integrity_analysis.csv",
    index=False
)

# Export provider-level analysis
provider_analysis.to_csv(
    OUTPUT_DIR / "provider_risk_analysis.csv",
    index=False
)

print("\n" + "=" * 50)
print("DATA EXPORT COMPLETED")
print("=" * 50)

print("\nFiles created:")

for file in OUTPUT_DIR.iterdir():
    print(file)