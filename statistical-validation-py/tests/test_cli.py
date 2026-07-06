"""CLI 端到端測試：inline 輸入、Excel 檔輸入、報告輸出。"""
import pandas as pd
import pytest

from process_validation import datasets as ds
from process_validation.cli import main


def test_cli_inline_values(capsys):
    assert main(["t-welch",
                 "--values1", ",".join(map(str, ds.WELCH_BEFORE)),
                 "--values2", ",".join(map(str, ds.WELCH_AFTER))]) == 0
    out = capsys.readouterr().out
    assert "t 統計量" in out and "拒絕 H₀" in out


def test_cli_chi_ind_rows(capsys):
    assert main(["chi-ind", "--rows", "460,40;482,18"]) == 0
    out = capsys.readouterr().out
    assert "χ² 統計量" in out


def test_cli_excel_roundtrip(tmp_path, capsys):
    sample = tmp_path / "sample.xlsx"
    report = tmp_path / "report.xlsx"
    ds.make_sample_workbook(str(sample))

    # 從範例檔讀「F檢定」工作表跑 F 檢定並輸出報告
    assert main(["f", "--input", str(sample), "--sheet", "F檢定",
                 "--col1", "改善前", "--col2", "改善後", "--out", str(report)]) == 0
    assert "F 統計量" in capsys.readouterr().out
    assert (pd.read_excel(report, sheet_name="檢定摘要")["項目"] == "結論").any()


def test_cli_anova2_from_excel(tmp_path, capsys):
    sample = tmp_path / "sample.xlsx"
    ds.make_sample_workbook(str(sample))
    assert main(["anova2", "--input", str(sample), "--sheet", "雙因子_重複",
                 "--factor-a", "溫度", "--factor-b", "壓力", "--value", "強度"]) == 0
    out = capsys.readouterr().out
    assert "交互作用" in out


def test_cli_anova1_groups_with_posthoc(capsys):
    args = ["anova1", "--posthoc"]
    for name, vals in ds.ANOVA1_GROUPS.items():
        args += ["--group", f"{name}:{','.join(map(str, vals))}"]
    assert main(args) == 0
    out = capsys.readouterr().out
    assert "ANOVA 表" in out and "Tukey" in out


def test_cli_demo_runs_everything(capsys):
    assert main(["demo"]) == 0
    out = capsys.readouterr().out
    for kw in ["F 檢定", "成對母體", "變異數相等", "變異數不相等",
               "獨立性", "適合度", "One-Way", "重複試驗", "Tukey"]:
        assert kw in out, f"demo 輸出缺少：{kw}"
