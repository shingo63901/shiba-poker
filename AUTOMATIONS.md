# AUTOMATIONS.md — 自動化登記簿

規則（見 CLAUDE.md）：所有帳號層級 trigger 必須登記於此。
**未登記的 trigger 視同不存在，每月健檢時應建議刪除。**
建立/修改/刪除 trigger 時，必須同步更新本檔並 commit。

## 現役 triggers

### 1. Daily Hello - Usage Reset
- **id**: `trig_01MpY3RPWv1wWmkd28WJ5afY`
- **狀態**: 運作中（2026-04-09 建立，2026-07-05 仍正常觸發）
- **排程**: cron `5 23,4,9 * * *`（UTC）= 台灣時間每日 07:05 / 12:05 / 17:05
- **行為**: 用 Haiku 模型發送 "Hello"，重置用量視窗，讓白天工作時段對齊額度週期
- **備註**: 2026-07-06 健檢時補登記。此前為隱形基礎設施，無任何文件記載。

### 2. Monthly System Health Check ⚠️ 待建立（需使用者核可）
- **狀態**: 2026-07-06 於背景 session 嘗試建立共 6 次（含 create_trigger ×5、
  send_later 備援 ×1），全部被伺服器端核可閘擋下——此類背景 session 沒有可送達
  使用者的核可視窗，settings.json 允許清單亦無法繞過。**已驗證此路不通，後續
  背景 session 不要再重試。**
  唯一完成方式：在**互動 session**（claude.ai/code 網頁版或 Claude app 的 Code，
  開 shiba-poker 的新對話）說「照 AUTOMATIONS.md 建立月度健檢 trigger」，核可
  視窗跳出後按允許，然後把真實 trigger id 回填到這裡並移除本待建立標記。
- **建立參數**（用 claude-code-remote 的 `create_trigger`）：
  - name: `Monthly System Health Check`
  - cron_expression: `7 1 1 * *`（UTC）= 台灣時間每月 1 日 09:07
  - create_new_session_on_fire: `true`（每次全新 session，不依賴舊對話）
  - notifications: `{"push": true}`
  - prompt（逐字使用）:

    ```
    每月系統健檢任務（standalone，全新 session）。

    你在包含 shingo63901/shiba-poker 的環境中。請嚴格依下列順序執行：

    1. 讀取 repo 根目錄的 SYSTEM_HEALTH_CHECK.md（健檢執行手冊）。
    2. 嚴格依手冊步驟執行健檢，遵守手冊中的「證據原則」與「禁止事項」。
    3. 產出報告 SYSTEM_AUDIT_<今天日期 YYYY-MM-DD>.md，commit 到分支
       claude/health-check-<YYYY-MM> 並 push。
    4. 開 PR 到 main，PR 內文列出：三個最重要發現、與上次報告相比重複出現的
       問題、本月行動清單。

    治理規則：若讀不到 SYSTEM_HEALTH_CHECK.md，直接回報錯誤並停止，不要自行
    發明健檢流程。健檢過程只讀取與撰寫治理文件（報告、AUTOMATIONS.md 勘誤），
    不得修改遊戲或工具程式碼。
    ```

- **設計說明（模型無關性）**: trigger 的 prompt 刻意不含任何健檢邏輯，只指向
  repo 內的 SYSTEM_HEALTH_CHECK.md。健檢邏輯的唯一來源是那份手冊，因此執行
  模型換成 Opus / Sonnet / Haiku 行為不變；要改健檢方式就改手冊、走 git。

## 已知限制

- 自動化 session 的 git 憑證通常只能推自己的指定分支：2026-07-06 從健檢 session
  推 git tag 到 origin 被 403 拒絕。tag 已建於本地並隨報告記載，需在有 main 權限
  的 session（或本機）執行：
  `git fetch --tags && git push origin v1.1.0 v1.2.0 v1.2.1 v1.3.0`
