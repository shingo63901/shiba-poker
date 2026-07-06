# 系統健檢報告（2026-07-06）

> 本次健檢範圍：shingo63901/shiba-poker repo（含全部 git 歷史）、遠端環境的 Claude 設定
> （~/.claude、hooks、skills、launcher-settings）、帳號層級的排程 triggers、Google Drive
> （最近檔案 + 關鍵字搜尋：日誌/SOP/規則/知識庫/筆記/流程/專案/zip）。

## 一、實際讀到的資料

| 來源 | 內容 | 狀態 |
|---|---|---|
| shiba-poker repo | 僅 1 個檔案 `index.html`（約 1,100 行單檔遊戲），5 個 commit，全部集中在 7/5–7/6 | 無 README、無 CLAUDE.md、無 .github、無測試 |
| git 歷史 | v1.1.0 ×2、v1.2.0、v1.2.1、v1.3.0，全為 `deploy:` 前綴 | 見「已證實盲點」#2 |
| ~/.claude | 只有平台內建 hooks（git identity、stop-hook）與內建 session-start-hook skill | **零自訂規則、零自訂技能、零記憶檔** |
| 排程 triggers | 僅 1 個：`Daily Hello - Usage Reset`（2026-04-09 建立，每日台灣時間 07:05 / 12:05 / 17:05 用 Haiku 發 "Hello"） | 正常運作中（最後觸發 7/5） |
| Google Drive | `FQC_Analyzer_v1.3.0.zip`（7/5）、`AlloyIQC_v1.1.0.zip`（6/25）、`AE1152D_v1.1.0.zip`（5/20）、`記帳筆記2026.xlsm`（4/15 後未動）、`記帳_iPhone版` sheet | 搜尋不到任何日誌/SOP/知識庫/規則文件 |
| 記帳_iPhone版 sheet | 只有表頭一列（日期/類型/分類/金額/帳戶/備註），**零筆資料**，4/3 建立後未再使用 | 死迴圈 |

## 二、目前系統地圖（真實樣貌，不是想像中的樣貌）

```
[對話 session]──執行──▶ shiba-poker (git)──"deploy:"──▶ GitHub Pages(未能從容器驗證)
      │
      ├──執行──▶ FQC_Analyzer / AlloyIQC / AE1152D ──zip──▶ Drive 根目錄（無源碼版控）
      │
      ├──(設計過但沒用過)──▶ 記帳 sheet
      │
      └──(什麼都沒留下)──▶ ∅  ← 知識、規則、教訓的去向
[Daily Hello trigger]──▶ 重置用量視窗（唯一在自動跑的東西）
```

## 三、已證實的盲點（每條都有證據）

1. **「系統」不存在於任何持久層。** 全部可存取範圍內找不到任何知識庫、工作日誌、
   規則檔、SOP、自訂 skill。所有規則只存在於每次對話當下，session 結束即蒸發。
   這就是為什麼「哪些規則沒沉進流程」無法逐條回答——**規則從未被寫下來過**。

2. **版本號與內容脫鉤（鐵證）。** `git diff 05e1fab(第一個v1.1.0) 36312f2(v1.2.0)` 為
   **空**：v1.2.0 的內容與最早的 v1.1.0 逐位元相同。也就是「v1.1.0（正式發版內容）」
   （85558bf，+90/−56）被整包退掉，再掛上 v1.2.0 的新版本號重新發佈，過程無任何記錄。
   另：兩個 commit 同名 v1.1.0；檔內 changelog（index.html:233-234）只記了 v1.3.0 與
   v1.2.1，v1.1.0/v1.2.0 發生過什麼已不可考；版本號在檔內至少 3 處（title、gameTitle、
   註解）靠手動同步。

3. **交付物無源碼管控。** 三個工作用工具（FQC_Analyzer、AlloyIQC、AE1152D）只以
   zip 形式存在 Drive 根目錄，各只有最新一版。舊版不存在，源碼 repo 在本 session
   可及範圍內看不到。zip 一旦覆蓋或誤刪，唯一回復方式是重新請 AI 生一次。

4. **記帳迴圈在第一步（輸入）就死了。** 4/3 特地建了「記帳_iPhone版」sheet 降低輸入
   門檻，93 天後仍是零筆資料；xlsm 4/15 之後也沒動過。這是「重新設計工具、但沒有
   改變輸入摩擦」的典型失敗痕跡。

5. **自動化能力只用來繞額度，沒有用在工作上。** 帳號唯一的 trigger 是 usage-reset
   hack（它確實有效、一直在跑）。日誌、備份、驗收、體檢——真正該自動化的環節，
   一個 trigger 都沒有。且這個 trigger 不記載於任何文件，屬隱形基礎設施：今天若不是
   直接列 triggers，沒有任何文件會告訴你它存在。

6. **驗收無標準、無工具。** repo 無測試、無 CI、無 .github；commit 全叫 `deploy:` 但
   Pages 是否真的上線無法自動確認。v1.1.0→v1.2.0 的整包無聲回退，正是「發版後才
   發現不對、只能退版、且退版不留痕」的直接後果。

## 四、迴圈狀態總表

| 迴圈 | 輸入 | 判斷 | 執行 | 驗收 | 記錄 | 修正 | 診斷 |
|---|---|---|---|---|---|---|---|
| 遊戲開發（shiba-poker） | ✅對話 | ✅ | ✅ | ⚠️手動玩 | ⚠️只剩 commit msg | ❌整包退版不留痕 | 半殘 |
| 工具交付（3 個 zip） | ✅ | ✅ | ✅ | ⚠️ | ❌zip 檔名即全部歷史 | ❌無法 diff 上一版 | 斷在記錄 |
| 記帳 | ❌零輸入 | – | – | – | – | – | 已死 |
| 知識沉澱 | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | 不存在 |
| Usage reset | ✅cron | ✅ | ✅ | – | ❌無文件 | – | 唯一全自動，但服務額度不服務工作 |

## 五、新的迴圈設計

核心原則：**記錄必須是執行的副產品，不能是額外步驟**。可用的持久層只有兩個：
git repo 與 triggers。所以一切設計都掛在這兩個上面。

1. **規則層 = CLAUDE.md（每個 repo 一份）。** Claude 每次開 session 自動載入 repo 的
   CLAUDE.md——這是唯一「不需要人記得」的規則落地點。規則寫在對話裡=沒寫。
2. **記錄層 = CHANGELOG.md + git tag。** 發版動作重定義為：改版本號（單一來源）→
   補 CHANGELOG 一行 → commit → tag。四步綁成一個流程寫進 CLAUDE.md，讓 Claude
   在每次「發版」請求時自動執行，人不用記。
3. **交付層 = repo 優先，zip 是產物。** 三個工具各自入 repo（或一個 tools monorepo），
   Drive zip 改為從 repo 打包的 release 附件。下次改版就能 diff、能回滾。
4. **治理層 = 把這次健檢變成 trigger。** 每月一次自動 session：列 triggers、檢查各
   repo 版本號/tag/changelog 一致性、檢查 Drive 交付物是否有 repo 對應、檢查上月
   CHANGELOG 是否有斷版。健檢從「想到才做」變成系統自己跑。

## 六、行動清單

**今天（半小時內可完成）**
- [ ] 本報告入 repo（本 commit 已完成——這就是第一筆落地的記錄）
- [ ] 給 shiba-poker 加 CLAUDE.md：版本號單一來源（`APP_VERSION` 常數）、發版四步
      流程、「回退必須 revert commit + changelog 註記」規則
- [ ] 補建 CHANGELOG.md：如實記錄 v1.1.0 正式版被 v1.2.0 回退的事實
- [ ] 對現有 5 個 commit 補 git tag（v1.1.0 指向 85558bf、v1.2.0 指向 36312f2…）

**一週內**
- [ ] FQC_Analyzer / AlloyIQC / AE1152D 三個工具入 git（從現有 zip 解包起步即可）
- [ ] index.html 版本號收斂到單一常數，title/畫面標題改由 JS 帶入
- [ ] 記帳迴圈二選一：verdict 週期試用（iPhone 捷徑一鍵寫入 sheet）或正式廢棄刪檔
      ——留著一個零資料的表格只會持續製造「我有系統」的錯覺

**一個月內（治理機制）**
- [ ] 建立每月「系統體檢」trigger（fresh session），檢查項目如第五節第 4 點
- [ ] 為 Daily Hello trigger 與所有未來 trigger 建一份 `AUTOMATIONS.md`（放在任一
      主 repo），規則：**沒有寫進這份文件的 trigger 視同不存在，體檢時刪除**
- [ ] 體檢報告固定 commit 回 repo，形成可比對的時間序列——三個月後就能回答
      「哪些問題反覆出現」這個這次因為沒有日誌而無法回答的問題
