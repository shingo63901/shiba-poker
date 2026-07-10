"""process_validation：製程改善統計檢定工具。

對照 Excel「資料分析」工具箱的各項假設檢定，驗證製程改善的有效性。
每個檢定函數的 docstring 都包含「什麼情形下使用／如何使用／前提假設」，
可用 help(pv.f_test) 查閱。

>>> import process_validation as pv
>>> result = pv.t_test_welch(before, after, alpha=0.05)
>>> print(result)             # Excel 風格報表 + 白話結論
>>> result.significant        # True/False
>>> result.to_excel("報告.xlsx")
"""
from .anova import anova_oneway, anova_twoway
from .assumptions import check_equal_variance, check_normality
from .chi_square import chi_square_gof, chi_square_independence
from .f_test import f_test
from .posthoc import tukey_hsd
from .result import TestResult
from .t_tests import t_test_equal_var, t_test_paired, t_test_welch

__version__ = "1.0.0"

__all__ = [
    "TestResult",
    "f_test",
    "t_test_paired",
    "t_test_equal_var",
    "t_test_welch",
    "chi_square_gof",
    "chi_square_independence",
    "anova_oneway",
    "anova_twoway",
    "check_normality",
    "check_equal_variance",
    "tukey_hsd",
    "__version__",
]
