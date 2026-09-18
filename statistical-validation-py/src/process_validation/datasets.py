"""內建製程改善範例資料（與 HTML 版工具的範例相同，方便交叉比對）。"""
from __future__ import annotations

import pandas as pd

# F 檢定：改善前後的尺寸量測（改善後變異縮小）
F_BEFORE = [25.31, 25.02, 24.68, 25.45, 24.87, 25.60, 24.51, 25.22, 24.95, 25.38, 24.72, 25.11]
F_AFTER = [25.05, 25.12, 24.98, 25.08, 25.02, 24.95, 25.10, 25.00, 25.06, 24.97, 25.09, 25.03]

# 成對 t：同 10 台設備調機前後的節拍時間（秒）
PAIRED_BEFORE = [58.2, 61.5, 55.0, 63.1, 59.8, 57.4, 60.9, 62.0, 56.7, 58.8]
PAIRED_AFTER = [55.9, 59.7, 53.8, 60.5, 58.2, 55.1, 59.0, 59.8, 55.2, 56.6]

# 等變異 t：新舊治具各一批的良率（%）
EQVAR_OLD = [93.1, 94.5, 92.8, 95.0, 93.6, 94.2, 92.5, 93.9, 94.8, 93.3]
EQVAR_NEW = [95.2, 96.1, 94.8, 96.5, 95.7, 94.9, 96.3, 95.5, 95.0, 96.0]

# Welch t：改善前後良率（變異明顯不同）
WELCH_BEFORE = [92.5, 89.1, 94.8, 87.6, 95.2, 90.3, 88.4, 93.9, 91.7, 86.9, 94.1, 90.8]
WELCH_AFTER = [95.6, 96.2, 95.1, 96.8, 95.9, 96.4, 95.3, 96.0, 95.7, 96.5, 95.4, 96.1]

# 卡方獨立性：改善前後 × 良/不良（2×2 列聯表）
CHI_IND_TABLE = pd.DataFrame(
    [[460, 40], [482, 18]],
    index=["改善前", "改善後"],
    columns=["良品", "不良品"],
)

# 卡方適合度：缺陷類型觀察數 vs 歷史比例
CHI_GOF_OBSERVED = [52, 31, 12, 5]
CHI_GOF_EXPECTED = [0.40, 0.35, 0.15, 0.10]  # 比例，會自動換算

# 單因子 ANOVA：三種退火溫度 vs 硬度
ANOVA1_GROUPS = {
    "180度": [62.1, 63.5, 61.8, 62.9, 62.4],
    "200度": [65.2, 66.0, 64.8, 65.5, 65.1],
    "220度": [64.1, 63.8, 64.6, 64.0, 63.5],
}

# 雙因子 ANOVA（重複試驗）：溫度 × 壓力 vs 接著強度，每組合 3 筆
ANOVA2_REP = pd.DataFrame(
    [
        ("低溫", "低壓", 42.1), ("低溫", "低壓", 41.8), ("低溫", "低壓", 42.5),
        ("低溫", "高壓", 43.0), ("低溫", "高壓", 42.6), ("低溫", "高壓", 43.4),
        ("高溫", "低壓", 43.8), ("高溫", "低壓", 44.2), ("高溫", "低壓", 43.5),
        ("高溫", "高壓", 47.9), ("高溫", "高壓", 48.5), ("高溫", "高壓", 47.6),
    ],
    columns=["A", "B", "y"],
)

# 雙因子 ANOVA（無重複）：操作員 × 機台 vs 產出
ANOVA2_NOREP = pd.DataFrame(
    [
        ("甲", "機台1", 88.2), ("甲", "機台2", 90.1), ("甲", "機台3", 86.5),
        ("乙", "機台1", 89.5), ("乙", "機台2", 91.4), ("乙", "機台3", 88.0),
        ("丙", "機台1", 87.1), ("丙", "機台2", 89.0), ("丙", "機台3", 85.8),
    ],
    columns=["A", "B", "y"],
)


def make_sample_workbook(path: str) -> None:
    """產生範例輸入檔 sample_data.xlsx（一種檢定一個工作表）。"""
    with pd.ExcelWriter(path, engine="openpyxl") as xw:
        pd.DataFrame({"改善前": F_BEFORE, "改善後": F_AFTER}).to_excel(xw, sheet_name="F檢定", index=False)
        pd.DataFrame({"改善前": PAIRED_BEFORE, "改善後": PAIRED_AFTER}).to_excel(xw, sheet_name="成對t", index=False)
        pd.DataFrame({"舊治具": EQVAR_OLD, "新治具": EQVAR_NEW}).to_excel(xw, sheet_name="等變異t", index=False)
        pd.DataFrame({"改善前": WELCH_BEFORE, "改善後": WELCH_AFTER}).to_excel(xw, sheet_name="Welch_t", index=False)
        CHI_IND_TABLE.to_excel(xw, sheet_name="卡方獨立性")
        pd.DataFrame({"觀察次數": CHI_GOF_OBSERVED, "期望比例": CHI_GOF_EXPECTED},
                     index=["刮傷", "尺寸NG", "髒污", "其他"]).to_excel(xw, sheet_name="卡方適合度")
        pd.DataFrame(ANOVA1_GROUPS).to_excel(xw, sheet_name="單因子ANOVA", index=False)
        ANOVA2_REP.rename(columns={"A": "溫度", "B": "壓力", "y": "強度"}).to_excel(xw, sheet_name="雙因子_重複", index=False)
        ANOVA2_NOREP.rename(columns={"A": "操作員", "B": "機台", "y": "產出"}).to_excel(xw, sheet_name="雙因子_無重複", index=False)
