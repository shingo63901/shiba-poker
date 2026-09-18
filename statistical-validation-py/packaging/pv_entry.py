"""PyInstaller 打包入口：等同於安裝後的 pv 指令。"""
import sys

# Windows 傳統 cmd 的編碼（如 cp950）缺少 χ、✅ 等字元時以 ? 代替，避免整個程式當掉
for stream in (sys.stdout, sys.stderr):
    if stream is not None and hasattr(stream, "reconfigure"):
        stream.reconfigure(errors="replace")

from process_validation.cli import main

if __name__ == "__main__":
    sys.exit(main())
