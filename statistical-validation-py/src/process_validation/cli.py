"""指令列介面：pv <檢定> --input 檔案.xlsx ...

範例：
    pv demo                     # 用內建範例資料跑全部八種檢定
    pv sample-data 範例.xlsx     # 產生範例輸入檔
    pv f       --input 量測.xlsx --col1 改善前 --col2 改善後
    pv t-welch --input 量測.xlsx --col1 改善前 --col2 改善後 --tail one --out 報告.xlsx
    pv t-paired --values1 "58.2,61.5" --values2 "55.9,59.7"
    pv chi-ind --rows "460,40;482,18"
    pv anova1  --input 量測.xlsx --sheet 單因子ANOVA
    pv anova2  --input 量測.xlsx --sheet 雙因子_重複 --factor-a 溫度 --factor-b 壓力 --value 強度
    pv advisor                  # 問答式檢定選擇指引
"""
from __future__ import annotations

import argparse
import sys

import pandas as pd

from . import (
    anova_oneway,
    anova_twoway,
    chi_square_gof,
    chi_square_independence,
    datasets as ds,
    f_test,
    t_test_equal_var,
    t_test_paired,
    t_test_welch,
)
from .advisor import run_advisor


def _parse_values(text: str) -> list[float]:
    return [float(v) for v in text.replace("，", ",").replace(";", ",").split(",") if v.strip()]


def _read_sheet(args) -> pd.DataFrame:
    if args.input.endswith(".csv"):
        return pd.read_csv(args.input)
    return pd.read_excel(args.input, sheet_name=args.sheet or 0)


def _two_samples(args) -> tuple[list[float], list[float]]:
    """兩樣本檢定的資料來源：--input+--col1/--col2，或 --values1/--values2。"""
    if args.values1 and args.values2:
        return _parse_values(args.values1), _parse_values(args.values2)
    if not args.input:
        raise SystemExit("請提供 --input 檔案（配合 --col1/--col2），或 --values1/--values2 直接輸入數值")
    df = _read_sheet(args)
    c1 = args.col1 or df.columns[0]
    c2 = args.col2 or df.columns[1]
    return df[c1].dropna().tolist(), df[c2].dropna().tolist()


def _output(result, args) -> None:
    print(result)
    if args.out:
        result.to_excel(args.out)
        print(f"\n📄 已輸出 Excel 報告：{args.out}")


def _add_common(p: argparse.ArgumentParser, tail: bool = False, delta0: bool = False) -> None:
    p.add_argument("--alpha", type=float, default=0.05, help="顯著水準（預設 0.05）")
    p.add_argument("--out", help="輸出 Excel 報告的路徑")
    p.add_argument("--input", help="輸入資料檔（.xlsx 或 .csv）")
    p.add_argument("--sheet", help="工作表名稱（預設第一張）")
    if tail:
        p.add_argument("--tail", choices=["one", "two"], default="two", help="單尾或雙尾（預設雙尾）")
    if delta0:
        p.add_argument("--delta0", type=float, default=0.0, help="H₀ 假設的均數差（預設 0）")


def _add_two_sample(sub, name: str, help_text: str) -> argparse.ArgumentParser:
    p = sub.add_parser(name, help=help_text)
    _add_common(p, tail=True, delta0=True)
    p.add_argument("--col1", help="第一組的欄名（預設第 1 欄）")
    p.add_argument("--col2", help="第二組的欄名（預設第 2 欄）")
    p.add_argument("--values1", help='直接輸入第一組數值，如 "1.2,3.4,5.6"')
    p.add_argument("--values2", help="直接輸入第二組數值")
    return p


def _run_demo() -> None:
    print(f"\n{'█' * 8} 以內建製程範例資料執行全部檢定 {'█' * 8}")
    print(f"\n※ 各檢定的使用時機與前提假設，請看函數 docstring（help(pv.f_test)）或 README。")
    print(str(f_test(ds.F_BEFORE, ds.F_AFTER)))
    print(str(t_test_paired(ds.PAIRED_BEFORE, ds.PAIRED_AFTER)))
    print(str(t_test_equal_var(ds.EQVAR_OLD, ds.EQVAR_NEW)))
    print(str(t_test_welch(ds.WELCH_BEFORE, ds.WELCH_AFTER)))
    print(str(chi_square_independence(ds.CHI_IND_TABLE)))
    print(str(chi_square_gof(ds.CHI_GOF_OBSERVED, ds.CHI_GOF_EXPECTED)))
    print(str(anova_oneway(ds.ANOVA1_GROUPS)))
    print(str(anova_twoway(ds.ANOVA2_REP)))
    print(str(anova_twoway(ds.ANOVA2_NOREP)))
    from .posthoc import tukey_hsd
    print("\n[事後檢定] 單因子 ANOVA 顯著 → Tukey HSD 兩兩比較：")
    print(tukey_hsd(ds.ANOVA1_GROUPS).to_string())


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="pv",
        description="製程改善統計檢定工具（對照 Excel 資料分析工具箱）",
        epilog=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("f", help="F 檢定：兩個常態母體變異數")
    _add_common(p, tail=True)
    for flag in ("--col1", "--col2", "--values1", "--values2"):
        p.add_argument(flag)

    _add_two_sample(sub, "t-paired", "成對 t 檢定（同一批對象前後量測）")
    _add_two_sample(sub, "t-equal", "等變異 t 檢定（兩批獨立樣本）")
    _add_two_sample(sub, "t-welch", "不等變異 t 檢定 Welch（變異數不同時）")

    p = sub.add_parser("chi-gof", help="卡方適合度檢定（觀察 vs 期望分布）")
    _add_common(p)
    p.add_argument("--obs", help='觀察次數，如 "52,31,12,5"')
    p.add_argument("--exp", help='期望次數或比例，如 "0.4,0.35,0.15,0.1"')
    p.add_argument("--obs-col", help="輸入檔中觀察次數的欄名")
    p.add_argument("--exp-col", help="輸入檔中期望次數的欄名")

    p = sub.add_parser("chi-ind", help="卡方獨立性檢定（列聯表）")
    _add_common(p)
    p.add_argument("--rows", help='直接輸入列聯表，每列以分號隔開，如 "460,40;482,18"')

    p = sub.add_parser("anova1", help="單因子 ANOVA（每欄一組）")
    _add_common(p)
    p.add_argument("--group", action="append",
                   help='直接輸入一組資料，可重複使用，如 --group "180度:62.1,63.5"')
    p.add_argument("--posthoc", action="store_true", help="顯著時加做 Tukey HSD 事後比較")

    p = sub.add_parser("anova2", help="雙因子 ANOVA（長格式：因子A、因子B、數值）")
    _add_common(p)
    p.add_argument("--factor-a", default=None, help="因子 A 欄名（預設第 1 欄）")
    p.add_argument("--factor-b", default=None, help="因子 B 欄名（預設第 2 欄）")
    p.add_argument("--value", default=None, help="數值欄名（預設第 3 欄）")

    sub.add_parser("advisor", help="問答式檢定選擇指引")
    sub.add_parser("demo", help="用內建製程範例資料跑全部檢定")
    p = sub.add_parser("sample-data", help="產生範例輸入檔")
    p.add_argument("path", nargs="?", default="sample_data.xlsx")

    args = parser.parse_args(argv)

    if args.cmd == "advisor":
        run_advisor()
        return 0
    if args.cmd == "demo":
        _run_demo()
        return 0
    if args.cmd == "sample-data":
        ds.make_sample_workbook(args.path)
        print(f"📄 已產生範例輸入檔：{args.path}")
        return 0

    if args.cmd == "f":
        x1, x2 = _two_samples(args)
        _output(f_test(x1, x2, alpha=args.alpha, tail=args.tail), args)
    elif args.cmd == "t-paired":
        x1, x2 = _two_samples(args)
        _output(t_test_paired(x1, x2, alpha=args.alpha, mu0=args.delta0, tail=args.tail), args)
    elif args.cmd == "t-equal":
        x1, x2 = _two_samples(args)
        _output(t_test_equal_var(x1, x2, alpha=args.alpha, delta0=args.delta0, tail=args.tail), args)
    elif args.cmd == "t-welch":
        x1, x2 = _two_samples(args)
        _output(t_test_welch(x1, x2, alpha=args.alpha, delta0=args.delta0, tail=args.tail), args)
    elif args.cmd == "chi-gof":
        if args.obs and args.exp:
            O, E = _parse_values(args.obs), _parse_values(args.exp)
        elif args.input:
            df = _read_sheet(args)
            O = df[args.obs_col or df.columns[0]].dropna().tolist()
            E = df[args.exp_col or df.columns[1]].dropna().tolist()
        else:
            raise SystemExit("請提供 --obs/--exp，或 --input 檔案")
        _output(chi_square_gof(O, E, alpha=args.alpha), args)
    elif args.cmd == "chi-ind":
        if args.rows:
            table = [_parse_values(r) for r in args.rows.split(";") if r.strip()]
        elif args.input:
            table = _read_sheet(args)
            table = table.set_index(table.columns[0])  # 第一欄視為列名
        else:
            raise SystemExit("請提供 --rows，或 --input 檔案（第一欄為列名）")
        _output(chi_square_independence(table, alpha=args.alpha), args)
    elif args.cmd == "anova1":
        if args.group:
            groups = {}
            for i, g in enumerate(args.group):
                name, _, vals = g.partition(":")
                groups[name if vals else f"第{i + 1}組"] = _parse_values(vals or name)
        elif args.input:
            df = _read_sheet(args)
            groups = {c: df[c].dropna().tolist() for c in df.columns}
        else:
            raise SystemExit("請提供 --group（可重複），或 --input 檔案（每欄一組）")
        result = anova_oneway(groups, alpha=args.alpha)
        _output(result, args)
        if args.posthoc and result.significant:
            from .posthoc import tukey_hsd
            print("\n[事後檢定] Tukey HSD 兩兩比較：")
            print(tukey_hsd(groups, alpha=args.alpha).to_string())
    elif args.cmd == "anova2":
        if not args.input:
            raise SystemExit("雙因子 ANOVA 請以 --input 提供長格式資料檔（因子A、因子B、數值）")
        df = _read_sheet(args)
        fa = args.factor_a or df.columns[0]
        fb = args.factor_b or df.columns[1]
        val = args.value or df.columns[2]
        _output(anova_twoway(df, alpha=args.alpha, factor_a=fa, factor_b=fb, value=val), args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
