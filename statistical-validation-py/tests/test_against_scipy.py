"""交叉驗證：本套件的手寫公式 vs scipy 官方檢定函數。

兩者演算法獨立（本套件按 Excel 公式組裝、scipy 為通用實作），
數值一致即可確認實作正確。
"""
import numpy as np
import pytest
from scipy import stats

import process_validation as pv
from process_validation import datasets as ds


def test_t_paired_matches_scipy():
    r = pv.t_test_paired(ds.PAIRED_BEFORE, ds.PAIRED_AFTER)
    t, p = stats.ttest_rel(ds.PAIRED_BEFORE, ds.PAIRED_AFTER)
    assert r.statistic == pytest.approx(t, rel=1e-12)
    assert r.p_value == pytest.approx(p, rel=1e-10)
    assert r.significant


def test_t_equal_var_matches_scipy():
    r = pv.t_test_equal_var(ds.EQVAR_OLD, ds.EQVAR_NEW)
    t, p = stats.ttest_ind(ds.EQVAR_OLD, ds.EQVAR_NEW, equal_var=True)
    assert r.statistic == pytest.approx(t, rel=1e-12)
    assert r.p_value == pytest.approx(p, rel=1e-10)


def test_t_welch_matches_scipy():
    r = pv.t_test_welch(ds.WELCH_BEFORE, ds.WELCH_AFTER)
    t, p = stats.ttest_ind(ds.WELCH_BEFORE, ds.WELCH_AFTER, equal_var=False)
    assert r.statistic == pytest.approx(t, rel=1e-12)
    assert r.p_value == pytest.approx(p, rel=1e-10)


def test_t_one_tail_is_half_of_two_tail():
    r2 = pv.t_test_welch(ds.WELCH_BEFORE, ds.WELCH_AFTER, tail="two")
    r1 = pv.t_test_welch(ds.WELCH_BEFORE, ds.WELCH_AFTER, tail="one")
    assert r1.p_value == pytest.approx(r2.p_value / 2, rel=1e-12)


def test_f_test_statistic_and_p():
    x1, x2 = np.asarray(ds.F_BEFORE), np.asarray(ds.F_AFTER)
    r = pv.f_test(x1, x2)
    F = x1.var(ddof=1) / x2.var(ddof=1)
    assert r.statistic == pytest.approx(F, rel=1e-12)
    # 雙尾 p = 2 × min(兩側尾機率)
    cdf = stats.f.cdf(F, len(x1) - 1, len(x2) - 1)
    assert r.p_value == pytest.approx(2 * min(cdf, 1 - cdf), rel=1e-10)


def test_f_test_symmetry():
    """交換兩組後，雙尾 p 值不變（F 變成倒數）。"""
    r12 = pv.f_test(ds.F_BEFORE, ds.F_AFTER)
    r21 = pv.f_test(ds.F_AFTER, ds.F_BEFORE)
    assert r12.p_value == pytest.approx(r21.p_value, rel=1e-9)
    assert r12.statistic == pytest.approx(1 / r21.statistic, rel=1e-12)


def test_chi_independence_matches_scipy():
    r = pv.chi_square_independence(ds.CHI_IND_TABLE)
    chi2, p, dof, _ = stats.chi2_contingency(ds.CHI_IND_TABLE, correction=False)
    assert r.statistic == pytest.approx(chi2, rel=1e-12)
    assert r.p_value == pytest.approx(p, rel=1e-10)
    assert r.df == str(dof)


def test_chi_independence_known_value():
    """HTML 版與手算驗證過的 2×2 表：χ² = 8.8586、p = 0.0029。"""
    r = pv.chi_square_independence([[460, 40], [482, 18]])
    assert r.statistic == pytest.approx(8.858578, abs=1e-4)
    assert r.p_value == pytest.approx(0.002917, abs=1e-5)


def test_chi_gof_matches_scipy():
    obs = ds.CHI_GOF_OBSERVED
    exp = [p * sum(obs) for p in ds.CHI_GOF_EXPECTED]  # 比例 → 次數
    r = pv.chi_square_gof(obs, ds.CHI_GOF_EXPECTED)     # 套件內自動換算
    chi2, p = stats.chisquare(obs, exp)
    assert r.statistic == pytest.approx(chi2, rel=1e-12)
    assert r.p_value == pytest.approx(p, rel=1e-10)


def test_anova_oneway_matches_scipy():
    r = pv.anova_oneway(ds.ANOVA1_GROUPS)
    F, p = stats.f_oneway(*ds.ANOVA1_GROUPS.values())
    assert r.statistic == pytest.approx(F, rel=1e-12)
    assert r.p_value == pytest.approx(p, rel=1e-10)
    assert r.significant


def test_anova_oneway_equals_t_squared_for_two_groups():
    """兩組時 ANOVA 與等變異 t 檢定等價：F = t²，p 相同。"""
    g = {"A": ds.EQVAR_OLD, "B": ds.EQVAR_NEW}
    ra = pv.anova_oneway(g)
    rt = pv.t_test_equal_var(ds.EQVAR_OLD, ds.EQVAR_NEW)
    assert ra.statistic == pytest.approx(rt.statistic**2, rel=1e-10)
    assert ra.p_value == pytest.approx(rt.p_value, rel=1e-9)
