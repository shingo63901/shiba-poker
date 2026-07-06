# 自動化排程慣例（AUTOMATIONS.md）

本文件定義 shiba-poker 專案中所有排程自動化（scheduled trigger）的建立慣例、規範與現行清單。所有新建立的 trigger 都必須依此文件登記於 `AUTOMATIONS_REGISTRY.md`。

## 命名慣例

- Trigger 名稱格式：`<週期>-<用途>-<專案>`
  - 範例：`monthly-health-check-shiba-poker`
- 週期用詞：`monthly`、`weekly`、`daily`

## 建立流程

1. 確認自動化的目的與範圍（要檢查什麼、多久一次）。
2. 決定執行頻率（cron expression，最小間隔為每小時一次）。
3. 決定執行模式：
   - 綁定既有 session（持續對話）
   - 每次觸發建立全新 session（`create_new_session_on_fire=true`，適合週期性、彼此獨立的健檢任務）
4. 建立 trigger 後，立即將以下資訊登記到 `AUTOMATIONS_REGISTRY.md`：
   - Trigger 名稱
   - Trigger ID（`trig_...`）
   - Cron 表達式
   - 用途說明
   - 建立日期
   - 狀態（啟用 / 停用）
5. 任何自動化流程若涉及推送程式碼變更，預設「僅提出建議、不自動推送」，除非另有明確授權。

## 目前已定義的自動化類型

### 月度健檢（monthly-health-check）

- **頻率**：每月 1 號 09:00（UTC）
- **檢查內容**：
  1. 程式碼掃描：檢查 `index.html` 是否有明顯錯誤、壞死程式碼或邏輯問題。
  2. 安全掃描：檢查 XSS、CSP（Content-Security-Policy）設定、注入風險等安全疑慮。
- **執行方式**：每次觸發建立全新 session，對 `shingo63901/shiba-poker` 主分支進行掃描，並將發現的問題摘要回報給使用者（不自動推送修正）。
- **通知設定**：完成後推播通知（push）給使用者。

## 登記簿

所有 trigger 的詳細記錄請見 [`AUTOMATIONS_REGISTRY.md`](./AUTOMATIONS_REGISTRY.md)。
