# ✈️ 出國旅遊小幫手

一個手機用的單一 HTML 旅遊工具：**行程表、匯率換算、記帳分帳、行李清單、常用外語會話（日/韓/英/泰，可朗讀、可放大給店員看）、各國緊急電話**。資料只存在你的手機瀏覽器（localStorage），可匯出／匯入 JSON 備份分享給旅伴。

- 線上網址（開啟 GitHub Pages 後）：`https://shingo63901.github.io/shiba-poker/travel/`
- 本機使用：直接用瀏覽器打開 `travel/index.html`

## 放進 Notion 變成網站

Notion 本身不能執行自訂 HTML/JavaScript，所以做法是「HTML 放在 GitHub Pages，Notion 用嵌入（Embed）顯示」：

1. GitHub repo → **Settings → Pages** → Source 選 `Deploy from a branch`，Branch 選 `main` / `(root)` → Save。
2. 等 1～2 分鐘，確認 `https://shingo63901.github.io/shiba-poker/travel/` 打得開。
3. 在 Notion 新增頁面，輸入 `/embed`，貼上上面的網址，把嵌入框拉高（約 800px）。
4. 右上角 **Share → Publish → Publish to web**，就會得到一個公開的 Notion 網站網址，可以分享給旅伴。

> 小提醒：在 Notion 嵌入框內，每個瀏覽器的資料各自獨立；若要在手機上當 App 用，直接開 GitHub Pages 網址並「加入主畫面」最順。
