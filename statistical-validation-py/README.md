# 製程改善統計檢定工具（Python 版）

以 Python（`scipy` + `pandas`）實作 Excel「資料分析」工具箱的各項假設檢定，
用來**驗證製程改善的有效性**。與同 repo 的 HTML 版（`../statistical-validation/`）
使用相同的範例資料，數值結果一致；Python 版額外提供 Excel 做不到的
**前提假設檢查、Tukey HSD 事後比較、批次 Excel 讀寫**。

## 安裝

```bash
cd statistical-validation-py
pip install -e .          # 安裝套件與 pv 指令
pip install -e ".[dev]"   # 若要跑測試（pytest）
```

## 快速開始

### 指令列（CLI）

```bash
pv demo                                    # 用內建製程範例資料跑全部八種檢定
pv sample-data 範例.xlsx                    # 產生範例輸入檔（一種檢定一個工作表）
pv advisor                                 # 問答式引導：告訴你該用哪個檢定

# 從 Excel 檔讀資料做檢定，並輸出 Excel 報告
pv t-welch --input 量測.xlsx --col1 改善前 --col2 改善後 --out 報告.xlsx
pv f       --input 量測.xlsx --col1 改善前 --col2 改善後 --tail one
pv anova1  --input 量測.xlsx --sheet 單因子ANOVA --posthoc
pv anova2  --input 量測.xlsx --sheet 雙因子_重複 --factor-a 溫度 --factor-b 壓力 --value 強度

# 不用檔案，直接給數值
pv t-paired --values1 "58.2,61.5,55.0" --values2 "55.9,59.7,53.8"
pv chi-ind  --rows "460,40;482,18"         # 改善前後 × 良/不良 的 2×2 表
```

### Python API

```python
import process_validation as pv

result = pv.t_test_welch(before, after, alpha=0.05, tail="two")
print(result)             # Excel 風格報表：敘述統計、t、df、單/雙尾 p、臨界值、白話結論
result.significant        # True / False
result.p_value            # 依 tail 選定的 p 值
result.to_excel("報告.xlsx")

help(pv.f_test)           # 每個檢定的「什麼情形下使用／如何使用／前提假設」都在 docstring
```

## 檢定總覽（對照 Excel 資料分析工具箱）

| 函數 / CLI | Excel 資料分析項目 | 什麼情形下使用 |
|---|---|---|
| `f_test` / `pv f` | F 檢定：兩個常態母體變異數 | 改善後**變異（穩定度）**是否縮小；t 檢定前判斷等/不等變異 |
| `t_test_paired` / `pv t-paired` | t 檢定：成對母體平均數差異 | **同一批對象**改善前後各量一次（同設備、同樣品） |
| `t_test_equal_var` / `pv t-equal` | t 檢定：兩母體平均數差（變異數相等） | 改善前後**各抽一批**，且 F 檢定顯示變異數相等 |
| `t_test_welch` / `pv t-welch` | t 檢定：兩母體平均數差（變異數不相等） | 同上但變異數不等；不確定時的**安全預設** |
| `chi_square_gof` / `pv chi-gof` | （Excel 為 CHISQ.TEST 函數） | 類別計數 vs 期望分布：缺陷組成是否改變 |
| `chi_square_independence` / `pv chi-ind` | （同上） | 兩類別變數是否相關；**改善前後×良/不良＝不良率比較** |
| `anova_oneway` / `pv anova1` | 單因子變異數分析 | **三組以上**平均比較（多水準/多機台/多供應商） |
| `anova_twoway` / `pv anova2` | 雙因子變異數分析（無重複／重複試驗） | 兩因子同時評估；重複試驗可檢定**交互作用** |

各檢定的詳細說明（使用時機、公式、前提假設、判讀範例）見
[`../statistical-validation/README.md`](../statistical-validation/README.md)，
或直接在 Python 內 `help()` 查閱函數 docstring——兩處內容一致。

## Excel 做不到的加值功能

```python
# 1. 前提假設檢查：跑 t / F / ANOVA 前先確認
pv.check_normality({"改善前": before, "改善後": after})       # Shapiro-Wilk 常態性
pv.check_equal_variance({"改善前": before, "改善後": after})  # Levene（比 F 檢定穩健）

# 2. 事後多重比較：ANOVA 顯著後找出「是哪幾組不同」
r = pv.anova_oneway(groups)
if r.significant:
    print(pv.tukey_hsd(groups))   # 每對組合的平均差、信賴區間、p 值
```

## 假設檢定通用流程

1. **設定假設**：H₀＝「無差異／改善無效」，H₁＝「有差異／改善有效」。
2. **選 α**：常用 0.05（容許 5% 的型一錯誤風險）。
3. **算統計量與 p 值**：p＝在 H₀ 為真下，看到目前或更極端資料的機率。
4. **結論**：p < α → 拒絕 H₀（顯著）；p ≥ α → 證據不足（≠ 證明沒差異）。

> ⚠ 統計顯著 ≠ 實務重要。p 值小只代表差異不是巧合；改善幅度是否值得投資，
> 仍要看平均差、變異縮小量與成本效益。

## 專案結構與測試

```
src/process_validation/
├── f_test.py / t_tests.py / chi_square.py / anova.py   # 八種檢定（docstring 含備註說明）
├── assumptions.py   # Shapiro-Wilk 常態性、Levene 變異數同質
├── posthoc.py       # Tukey HSD 事後比較
├── advisor.py       # 問答式檢定選擇指引
├── datasets.py      # 內建製程範例資料（與 HTML 版相同）
├── result.py        # TestResult：統一結果容器 + Excel 報告輸出
└── cli.py           # pv 指令
tests/               # 26 項測試
examples/            # demo.ipynb 示範筆記本、sample_data.xlsx 範例輸入檔
```

```bash
python -m pytest     # 執行測試
```

測試策略：手寫公式（比照 Excel 演算法）與 `scipy` 官方檢定函數交叉比對
（`ttest_rel` / `ttest_ind` / `chi2_contingency` / `f_oneway`），
雙因子 ANOVA 以手算案例與 SS 分解恆等式驗證，
另含 2×2 卡方已知值（χ²=8.8586）與「兩組 ANOVA = t²」等價性檢查。
