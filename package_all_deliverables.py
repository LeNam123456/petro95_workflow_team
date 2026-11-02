# -*- coding: utf-8 -*-
"""Package all canonical deliverables for SPAFS V5.2 into ZIP and folder."""

import os
import shutil
import zipfile
from pathlib import Path

def main():
    root = Path(".")
    pkg_dir = root / "SPAFS_DELIVERABLES_PACKAGE"
    mh_sub = pkg_dir / "06_multi_horizon_and_deep_learning"
    mh_sub.mkdir(parents=True, exist_ok=True)

    # 1. Copy multi-horizon parquet
    mh_parquet = root / "data/processed/stream2_multi_horizon_2017_2025.parquet"
    if mh_parquet.exists():
        shutil.copy2(mh_parquet, mh_sub / "stream2_multi_horizon_2017_2025.parquet")

    # 2. Copy scripts
    scripts = [
        root / "src/data_proccessing/data_handling/multi_horizon_targets.py",
        root / "src/models/runner_multi_horizon_traditional.py",
        root / "src/models/dl/sequence_models.py",
        root / "src/models/evaluation/consolidate_multi_horizon_analysis.py",
    ]
    for s in scripts:
        if s.exists():
            shutil.copy2(s, mh_sub / s.name)

    # 3. Copy results & tables
    results = [
        root / "artifacts/master_consolidation/master_multi_horizon_leaderboard.csv",
        root / "artifacts/master_consolidation/master_pairwise_hac_tests.csv",
        root / "artifacts/master_consolidation/master_shock_error_analysis.csv",
        root / "artifacts/master_consolidation/master_oos_predictions_daily.csv",
        root / "artifacts/master_consolidation/master_oos_predictions_weekly.csv",
        root / "artifacts/master_consolidation/master_oos_predictions_monthly.csv",
        root / "artifacts/deep_learning/deep_learning_benchmark_summary.csv",
        root / "artifacts/deep_learning/deep_learning_benchmark_summary.json",
    ]
    for r in results:
        if r.exists():
            shutil.copy2(r, mh_sub / r.name)

    # 4. Copy report and word docs to package root
    reports_to_copy = [
        (root / "reports/SPAFS_V5_2_BAO_CAO_KHOA_HOC_HOAN_CHINH.md", pkg_dir / "SPAFS_V5_2_BAO_CAO_KHOA_HOC_HOAN_CHINH.md"),
        (root / "reports/SPAFS_V5_2_Bao_Cao_Hoan_Chinh.docx", pkg_dir / "SPAFS_V5_2_Bao_Cao_Hoan_Chinh.docx"),
        (Path("C:/Users/LeeNam/Downloads/SPAFS.docx"), pkg_dir / "SPAFS.docx"),
        (Path("C:/Users/LeeNam/Downloads/SPAFS_V5_2_Master_Research_Plan_and_Audit.docx"), pkg_dir / "SPAFS_V5_2_Master_Research_Plan_and_Audit.docx"),
    ]
    for src, dst in reports_to_copy:
        if src.exists():
            shutil.copy2(src, dst)

    # 5. Build ZIP
    zip_path = root / "SPAFS_DELIVERABLES_PACKAGE.zip"
    if zip_path.exists():
        zip_path.unlink()

    print(f"Building {zip_path}...")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for r, dirs, files in os.walk(pkg_dir):
            for file in files:
                full_path = Path(r) / file
                arcname = full_path.relative_to(pkg_dir)
                zipf.write(full_path, arcname)

    print(f"Successfully packaged {zip_path} (Size: {zip_path.stat().st_size:,} bytes)")

if __name__ == "__main__":
    main()
