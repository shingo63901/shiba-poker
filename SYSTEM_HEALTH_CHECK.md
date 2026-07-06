# 系統健檢執行手冊（SYSTEM_HEALTH_CHECK.md）

> 本手冊是每月系統健檢的**唯一**流程來源。由帳號 trigger「Monthly System Health Check」
> 自動發起，也可隨時手動要求 Claude 執行。
> 執行者可以是任何 Claude 模型（Opus / Sonnet / Haiku 皆可）。手冊刻意把每一步寫成
> 可照抄的指令與可打勾的清單，**不依賴執行模型的臨場判斷力**。
> 修改健檢邏輯 = 修改本檔案並走 git，不要改 trigger 的 prompt。

## 0. 設計原則（執行前先讀，違反任一條即為不合格的健檢）

1. **證據優先**：每個結論必須附上得出它的指令與輸出摘要（或檔案路徑+行號）。
   查不到就寫「查不到」。禁止推測、禁止「應該是」「可能是」。
2. **先枚舉，後判斷**：先把所有持久層的實際內容列完（第 1 節），才開始找問題。
   不要帶著預設問題去找證據。
3. **迴圈框架**：每個工作流一律用六環節評估——
   `輸入 → 判斷 → 執行 → 驗收 → 記錄 → 修正`，逐環節標記 ✅/⚠️/❌ 並寫斷點在哪。
4. **時間序列**：必須與上一份 `SYSTEM_AUDIT_*.md` 比對。同一問題出現第 2 次即列為
   「結構性問題」，處置方式必須是**修改流程/文件**，不得只是再提醒一次。
5. **唯讀原則**：健檢只產出報告與治理文件勘誤（AUTOMATIONS.md），不修改任何
   遊戲或工具程式碼。

## 1. 盤點持久層（照抄指令執行，全部貼證據）

### 1a. Git repo

```bash
git log --oneline -30
git tag -l
git status
ls *.md
```

### 1b. 帳號 triggers

呼叫 MCP 工具 `list_triggers`（claude-code-remote server）。
把結果與 `AUTOMATIONS.md` 逐一比對。

### 1c. Google Drive（若此 session 有 Drive 工具；沒有就寫「本次無 Drive 權限」）

- `list_recent_files`
- 以關鍵字搜尋交付物：`title contains '.zip'`
- 對每個工作用 zip（如 FQC_Analyzer、AlloyIQC、AE1152D），確認是否已有對應 git repo。

### 1d. 規則檔

- repo 根目錄 `CLAUDE.md` 是否存在？內容是否與現行做法矛盾（例如規則說要 tag 但
  最近發版沒 tag）？

## 2. 一致性檢查清單（逐項打勾，附證據）

| # | 檢查項 | 判定方式 |
|---|---|---|
| C1 | 每個 git tag 都有對應 CHANGELOG 條目？ | `git tag -l` 對照 CHANGELOG.md |
| C2 | HEAD 的版本號（index.html `<title>`）== 最新 tag == CHANGELOG 最新條目？ | `grep -n "<title>" index.html` |
| C3 | 上月每個 `deploy:` commit 都有 tag 與 CHANGELOG 條目？ | `git log --since="1 month ago" --oneline` |
| C4 | 有無「無聲回退」？（抽查：相鄰版本 diff 是否為空或互為反向） | `git diff <tagA> <tagB> --stat` |
| C5 | `AUTOMATIONS.md` 與 `list_triggers` 實況一致？未登記的 trigger 列出並建議刪除 | 逐一比對 id |
| C6 | Drive 上的工作交付物 zip 是否都有 repo 對應？ | 1c 的結果 |
| C7 | 上次報告的行動清單，完成幾項？列出**連續兩次**未完成的項目 | 讀上一份 SYSTEM_AUDIT_*.md |

## 3. 迴圈評估表（每個活躍工作流一列）

| 迴圈 | 輸入 | 判斷 | 執行 | 驗收 | 記錄 | 修正 | 斷點說明（附證據） |
|---|---|---|---|---|---|---|---|
| （範例）遊戲開發 | ✅ | ✅ | ✅ | ⚠️ | ✅ | ⚠️ | 驗收仍靠手動玩 |

「活躍」定義：過去 60 天內有 commit、有檔案異動、或有 trigger 觸發的工作流。
已死的迴圈（60 天零活動）單獨列一節「應廢棄或重啟」，二選一給建議，不得放著不管。

## 4. 報告輸出

- 檔名：`SYSTEM_AUDIT_YYYY-MM-DD.md`（當天日期），放 repo 根目錄。
- 固定結構（缺一節即不合格）：
  1. 本次讀了哪些資料（含指令）
  2. 一致性檢查結果（第 2 節的表，全部打勾狀態）
  3. 迴圈評估表（第 3 節）
  4. **與上次報告比對**：新增問題 / 已解決問題 / 重複問題（重複 ≥2 次者標「結構性」）
  5. 結構性問題的流程修改提案（改哪個文件、改成什麼）
  6. 下月行動清單（≤5 項，每項可在 30 分鐘內完成或明確拆解）

## 5. 收尾（完成定義）

以下全部完成才算健檢結束：

1. 報告已 commit 到分支 `claude/health-check-YYYY-MM` 並 push。
2. 已開 PR 到 main，PR 內文含：三個最重要發現、重複問題清單、下月行動清單。
3. 若發現未登記 trigger 或 AUTOMATIONS.md 過時，勘誤一併放進同一個 PR。

## 6. 禁止事項

- 禁止在沒有證據時下結論；禁止通用建議（「建議建立良好文件習慣」這類話一律不准出現，
  必須具體到檔案與指令）。
- 禁止安撫性措辭。
- 禁止修改 index.html 或任何產品程式碼。
- 讀不到本手冊或 repo 時：回報錯誤並停止，**不要自行發明健檢流程**。
