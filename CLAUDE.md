# 柴犬撲克（shiba-poker）— 專案規則

單檔 HTML5 遊戲，全部程式碼在 `index.html`，以 GitHub Pages 部署（main 分支）。

## 版本規則

- **版本號單一來源**：目標是收斂為 `index.html` 內的 `APP_VERSION` 常數，title 與畫面
  標題由 JS 帶入。在收斂完成前，版本號出現在多處（`<title>`、`#gameTitle`、檔頭註解），
  發版前必須執行 `grep -n "v1\." index.html` 確認全部一致。
- 版本語意：破壞性改版 = major、新功能/版面改版 = minor、修正/安全 = patch。

## 發版四步（一體，不可拆）

任何「發版」請求都必須完整走完，缺一步不算發版：

1. 更新版本號（全部出現處）。
2. `CHANGELOG.md` 加一行：版本、日期、一句話摘要。
3. Commit，訊息格式：`deploy: 柴犬撲克 vX.Y.Z（摘要）`。
4. `git tag vX.Y.Z` 並 `git push origin vX.Y.Z`。

## 回退規則

- 回退必須用 `git revert`（保留痕跡），**禁止**把舊內容掛上新版本號重新發佈。
- 回退必須在 CHANGELOG.md 註記：回退了哪個版本、為什麼。
- 歷史教訓：v1.2.0 實為無聲回退「v1.1.0（正式發版內容）」，該次改動內容已不可考。

## 治理

- 所有帳號層級的自動化（triggers）必須登記於 `AUTOMATIONS.md`。**未登記的 trigger
  視同不存在，健檢時應建議刪除。**
- 每月系統健檢依 `SYSTEM_HEALTH_CHECK.md` 執行（由 trigger 自動發起，也可隨時手動
  要求執行）。健檢報告以 `SYSTEM_AUDIT_YYYY-MM-DD.md` 命名，commit 回 repo 形成
  時間序列。
- 健檢為唯讀性質：只產出報告與治理文件勘誤，不修改遊戲程式碼。
- **待辦自癒**：任何 session 開始工作前，先檢查 `AUTOMATIONS.md` 是否有標記
  「待建立／待核可」的項目。若有、且當前是互動 session（核可視窗可送達使用者），
  應主動提出執行並在完成後回填 id、移除待建立標記。背景 session（無核可介面）
  跳過此項，不要空轉重試。
