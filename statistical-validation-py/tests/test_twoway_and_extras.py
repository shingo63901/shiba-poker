"""雙因子 ANOVA 手算驗證、前提檢查、事後檢定與報表輸出。"""
import numpy as np
import pandas as pd
import pytest
from scipy import stats

import process_validation as pv
from process_validation import datasets as ds


def test_twoway_replicated_hand_computed():
    """2×2、每格 2 筆的手算案例：

    A1B1: 1,3  A1B2: 5,7  A2B1: 9,11  A2B2: 13,15（總平均 8）
    SS_A = 128、SS_B = 32、SS_AB = 0、SS_E = 8、df_E = 4 → F_A = 64。
    """
    data = pd.DataFrame(
        [("A1", "B1", 1), ("A1", "B1", 3), ("A1", "B2", 5), ("A1", "B2", 7),
         ("A2", "B1", 9), ("A2", "B1", 11), ("A2", "B2", 13), ("A2", "B2", 15)],
        columns=["A", "B", "y"],
    )
    r = pv.anova_twoway(data)
    table = r.tables["ANOVA 表"]
    assert table.loc["因子 A（A）", "SS"] == pytest.approx(128)
    assert table.loc["因子 B（B）", "SS"] == pytest.approx(32)
    assert table.loc["交互作用 A×B", "SS"] == pytest.approx(0, abs=1e-9)
    assert table.loc["誤差（組內）", "SS"] == pytest.approx(8)
    assert table.loc["因子 A（A）", "F"] == pytest.approx(64)
    assert table.loc["因子 A（A）", "P 值"] == pytest.approx(stats.f.sf(64, 1, 4), rel=1e-10)


def test_twoway_ss_decomposition():
    """SS 分解恆等式：SS_A + SS_B + SS_AB + SS_E = SS_T。"""
    r = pv.anova_twoway(ds.ANOVA2_REP)
    t = r.tables["ANOVA 表"]
    parts = t["SS"].iloc[:-1].sum()  # 總和列以外
    assert parts == pytest.approx(t.loc["總和", "SS"], rel=1e-10)


def test_twoway_no_replication():
    r = pv.anova_twoway(ds.ANOVA2_NOREP)
    assert "無重複試驗" in r.name
    t = r.tables["ANOVA 表"]
    assert "交互作用 A×B" not in t.index
    assert t.loc["誤差", "df"] == 4  # (3-1)(3-1)
    # 分解恆等式
    assert t["SS"].iloc[:-1].sum() == pytest.approx(t.loc["總和", "SS"], rel=1e-10)


def test_twoway_rejects_unbalanced():
    data = ds.ANOVA2_REP.iloc[:-1]  # 拿掉一筆 → 不平衡
    with pytest.raises(ValueError, match="平衡"):
        pv.anova_twoway(data)


def test_chi_low_expected_warning():
    r = pv.chi_square_independence([[8, 2], [5, 5]])
    assert any("期望次數" in w for w in r.warnings)


def test_assumptions():
    rng = np.random.default_rng(7)
    normal = rng.normal(10, 1, 50)
    skewed = rng.exponential(1, 50)
    norm_check = pv.check_normality({"常態": normal, "偏態": skewed})
    assert "✓" in norm_check.loc["常態", "判定"]
    assert "⚠" in norm_check.loc["偏態", "判定"]

    lev = pv.check_equal_variance({"a": rng.normal(0, 1, 40), "b": rng.normal(0, 5, 40)})
    assert "⚠" in lev["判定"].iloc[0]


def test_tukey_hsd():
    out = pv.tukey_hsd(ds.ANOVA1_GROUPS)
    assert len(out) == 3  # C(3,2) 組比較
    assert "180度 − 200度" in out.index
    # 與 scipy 原始結果一致
    raw = stats.tukey_hsd(*ds.ANOVA1_GROUPS.values())
    assert out.loc["180度 − 200度", "p 值"] == pytest.approx(raw.pvalue[0, 1], rel=1e-12)


def test_result_str_and_excel(tmp_path):
    r = pv.t_test_welch(ds.WELCH_BEFORE, ds.WELCH_AFTER)
    text = str(r)
    assert "t 統計量" in text and "結論" in text and "敘述統計" in text
    out = tmp_path / "report.xlsx"
    r.to_excel(str(out))
    summary = pd.read_excel(out, sheet_name="檢定摘要")
    assert (summary["項目"] == "結論").any()


def test_paired_length_mismatch():
    with pytest.raises(ValueError, match="筆數相同"):
        pv.t_test_paired([1, 2, 3], [1, 2])
