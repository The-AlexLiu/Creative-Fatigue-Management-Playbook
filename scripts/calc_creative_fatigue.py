#!/usr/bin/env python3
"""Calculate creative fatigue and portfolio concentration metrics.

Input CSV should be a daily creative-level report. The script does not delete
invalid rows. Rows with missing required fields or invalid dates are written to
output/error_rows.csv for manual review.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


REQUIRED_COLUMNS = [
    "date",
    "platform",
    "campaign_name",
    "adset_name",
    "ad_name",
    "creative_id",
    "creative_name",
    "launch_date",
    "spend",
    "impressions",
    "reach",
    "clicks",
    "purchases",
    "gmv",
]

NUMERIC_COLUMNS = ["spend", "impressions", "reach", "clicks", "purchases", "gmv"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Calculate creative fatigue metrics from a daily creative CSV."
    )
    parser.add_argument("--input", required=True, help="Input CSV path.")
    parser.add_argument(
        "--output-dir",
        default="output",
        help="Directory for generated CSV outputs. Default: output",
    )
    parser.add_argument(
        "--target-roas",
        type=float,
        default=1.5,
        help="Target ROAS used for action suggestions. Default: 1.5",
    )
    parser.add_argument(
        "--target-cpa",
        type=float,
        default=None,
        help="Optional target CPA used for action suggestions.",
    )
    return parser.parse_args()


def safe_div(numerator: pd.Series, denominator: pd.Series) -> pd.Series:
    denominator = denominator.replace({0: pd.NA})
    return numerator / denominator


def validate_and_prepare(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    missing = [column for column in REQUIRED_COLUMNS if column not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {', '.join(missing)}")

    work = df.copy()
    work["date"] = pd.to_datetime(work["date"], errors="coerce")
    work["launch_date"] = pd.to_datetime(work["launch_date"], errors="coerce")

    for column in NUMERIC_COLUMNS:
        work[column] = pd.to_numeric(work[column], errors="coerce")

    invalid_mask = work[REQUIRED_COLUMNS].isna().any(axis=1)
    invalid = work.loc[invalid_mask].copy()
    valid = work.loc[~invalid_mask].copy()

    if not invalid.empty:
        reasons = []
        for _, row in invalid.iterrows():
            row_reasons = [
                column for column in REQUIRED_COLUMNS if pd.isna(row.get(column))
            ]
            reasons.append("; ".join(row_reasons))
        invalid["error_reason"] = reasons

    valid["age_days"] = (valid["date"] - valid["launch_date"]).dt.days + 1
    negative_age = valid["age_days"] < 0
    if negative_age.any():
        age_errors = valid.loc[negative_age].copy()
        age_errors["error_reason"] = "launch_date is after date"
        invalid = pd.concat([invalid, age_errors], ignore_index=True)
        valid = valid.loc[~negative_age].copy()

    return valid, invalid


def aggregate_creatives(valid: pd.DataFrame, latest_date: pd.Timestamp) -> pd.DataFrame:
    group_cols = [
        "platform",
        "campaign_name",
        "adset_name",
        "ad_name",
        "creative_id",
        "creative_name",
        "launch_date",
    ]

    agg = (
        valid.groupby(group_cols, dropna=False)
        .agg(
            first_seen_date=("date", "min"),
            last_seen_date=("date", "max"),
            spend=("spend", "sum"),
            impressions=("impressions", "sum"),
            reach=("reach", "sum"),
            clicks=("clicks", "sum"),
            purchases=("purchases", "sum"),
            gmv=("gmv", "sum"),
        )
        .reset_index()
    )

    agg["age_days"] = (latest_date - agg["launch_date"]).dt.days + 1
    agg["frequency"] = safe_div(agg["impressions"], agg["reach"])
    agg["ctr"] = safe_div(agg["clicks"], agg["impressions"])
    agg["cvr"] = safe_div(agg["purchases"], agg["clicks"])
    agg["cpc"] = safe_div(agg["spend"], agg["clicks"])
    agg["cpm"] = safe_div(agg["spend"] * 1000, agg["impressions"])
    agg["cpa"] = safe_div(agg["spend"], agg["purchases"])
    agg["roas"] = safe_div(agg["gmv"], agg["spend"])
    agg["gmv_share"] = safe_div(agg["gmv"], pd.Series([agg["gmv"].sum()] * len(agg)))
    agg["spend_share"] = safe_div(
        agg["spend"], pd.Series([agg["spend"].sum()] * len(agg))
    )

    return agg.sort_values(["gmv", "spend"], ascending=False)


def window_metrics(valid: pd.DataFrame, latest_date: pd.Timestamp) -> pd.DataFrame:
    recent_3_start = latest_date - pd.Timedelta(days=2)
    recent_7_start = latest_date - pd.Timedelta(days=6)

    def calc_window(prefix: str, start_date: pd.Timestamp) -> pd.DataFrame:
        window = valid.loc[valid["date"] >= start_date].copy()
        grouped = (
            window.groupby("creative_id", dropna=False)
            .agg(
                **{
                    f"{prefix}_spend": ("spend", "sum"),
                    f"{prefix}_impressions": ("impressions", "sum"),
                    f"{prefix}_clicks": ("clicks", "sum"),
                    f"{prefix}_purchases": ("purchases", "sum"),
                    f"{prefix}_gmv": ("gmv", "sum"),
                }
            )
            .reset_index()
        )
        grouped[f"{prefix}_ctr"] = safe_div(
            grouped[f"{prefix}_clicks"], grouped[f"{prefix}_impressions"]
        )
        grouped[f"{prefix}_cvr"] = safe_div(
            grouped[f"{prefix}_purchases"], grouped[f"{prefix}_clicks"]
        )
        grouped[f"{prefix}_cpa"] = safe_div(
            grouped[f"{prefix}_spend"], grouped[f"{prefix}_purchases"]
        )
        grouped[f"{prefix}_roas"] = safe_div(
            grouped[f"{prefix}_gmv"], grouped[f"{prefix}_spend"]
        )
        return grouped

    recent_3 = calc_window("r3", recent_3_start)
    recent_7 = calc_window("r7", recent_7_start)
    merged = recent_7.merge(recent_3, on="creative_id", how="outer")

    merged["roas_decay_rate"] = safe_div(merged["r3_roas"], merged["r7_roas"]) - 1
    merged["ctr_decay_rate"] = safe_div(merged["r3_ctr"], merged["r7_ctr"]) - 1
    merged["cpa_increase_rate"] = safe_div(merged["r3_cpa"], merged["r7_cpa"]) - 1
    return merged


def portfolio_metrics(creatives: pd.DataFrame) -> pd.DataFrame:
    total_gmv = creatives["gmv"].sum()
    total_spend = creatives["spend"].sum()
    total_impressions = creatives["impressions"].sum()

    sorted_gmv = creatives.sort_values("gmv", ascending=False)
    top1_gmv_share = sorted_gmv["gmv"].iloc[0] / total_gmv if total_gmv else pd.NA
    top3_gmv_share = sorted_gmv["gmv"].head(3).sum() / total_gmv if total_gmv else pd.NA

    shares = safe_div(creatives["gmv"], pd.Series([total_gmv] * len(creatives)))
    hhi = (shares.fillna(0) ** 2).sum()
    effective_count = 1 / hhi if hhi else pd.NA

    metrics = {
        "active_creatives": int(len(creatives)),
        "total_spend": total_spend,
        "total_gmv": total_gmv,
        "portfolio_roas": total_gmv / total_spend if total_spend else pd.NA,
        "gmv_weighted_age_days": (
            (creatives["age_days"] * creatives["gmv"]).sum() / total_gmv
            if total_gmv
            else pd.NA
        ),
        "spend_weighted_age_days": (
            (creatives["age_days"] * creatives["spend"]).sum() / total_spend
            if total_spend
            else pd.NA
        ),
        "impression_weighted_age_days": (
            (creatives["age_days"] * creatives["impressions"]).sum()
            / total_impressions
            if total_impressions
            else pd.NA
        ),
        "top1_gmv_share": top1_gmv_share,
        "top3_gmv_share": top3_gmv_share,
        "hhi": hhi,
        "effective_creative_count": effective_count,
    }
    return pd.DataFrame([metrics])


def suggest_action(row: pd.Series, target_roas: float, target_cpa: float | None) -> str:
    roas = row.get("roas", pd.NA)
    cpa = row.get("cpa", pd.NA)
    r3_roas = row.get("r3_roas", pd.NA)
    frequency = row.get("frequency", pd.NA)
    roas_decay = row.get("roas_decay_rate", pd.NA)
    ctr_decay = row.get("ctr_decay_rate", pd.NA)
    cpa_increase = row.get("cpa_increase_rate", pd.NA)
    spend_share = row.get("spend_share", 0)
    gmv_share = row.get("gmv_share", 0)

    if (
        pd.notna(gmv_share)
        and gmv_share >= 0.15
        and (
            (pd.notna(roas_decay) and roas_decay <= -0.2)
            or (pd.notna(cpa_increase) and cpa_increase >= 0.2)
        )
    ):
        return "主力衰退预警：保留但停止继续加压，立即补同角度变体"

    if (
        pd.notna(frequency)
        and frequency >= 2.5
        and pd.notna(roas_decay)
        and roas_decay <= -0.2
    ):
        return "衰退预警：新增同角度变体，优先刷新 hook/封面/前三秒"

    if (
        pd.notna(ctr_decay)
        and ctr_decay <= -0.2
        and pd.notna(cpa_increase)
        and cpa_increase >= 0.2
    ):
        return "暂停或降预算：点击吸引力和转化效率同时走弱"

    if pd.notna(roas) and roas < target_roas and pd.notna(spend_share) and spend_share >= 0.1:
        return "检查预算浪费：ROAS 低且花费占比高，需复查受众和落地页"

    if pd.notna(r3_roas) and r3_roas >= target_roas and pd.notna(gmv_share) and gmv_share >= 0.15:
        return "放量保留：主力素材，补同角度变体，避免一次性替换"

    if target_cpa is not None and pd.notna(cpa) and cpa > target_cpa * 1.2:
        return "CPA 预警：超过目标 CPA 20%，观察转化质量或降预算"

    return "继续观察：样本不足或表现未触发强动作"


def main() -> None:
    args = parse_args()
    input_path = Path(args.input)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(input_path)
    valid, invalid = validate_and_prepare(df)

    if valid.empty:
        invalid.to_csv(output_dir / "error_rows.csv", index=False)
        raise ValueError("No valid rows found. See output/error_rows.csv.")

    latest_date = valid["date"].max()
    creatives = aggregate_creatives(valid, latest_date)
    windows = window_metrics(valid, latest_date)
    creative_scores = creatives.merge(windows, on="creative_id", how="left")
    creative_scores["suggested_action"] = creative_scores.apply(
        suggest_action, axis=1, target_roas=args.target_roas, target_cpa=args.target_cpa
    )

    portfolio = portfolio_metrics(creatives)

    creative_scores.to_csv(output_dir / "creative_scores.csv", index=False)
    portfolio.to_csv(output_dir / "portfolio_metrics.csv", index=False)
    invalid.to_csv(output_dir / "error_rows.csv", index=False)

    print(f"Generated: {output_dir / 'creative_scores.csv'}")
    print(f"Generated: {output_dir / 'portfolio_metrics.csv'}")
    print(f"Generated: {output_dir / 'error_rows.csv'}")


if __name__ == "__main__":
    main()
