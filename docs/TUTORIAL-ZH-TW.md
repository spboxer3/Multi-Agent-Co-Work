# 多代理協作 (Multi-Agent Co-Work) 完整教學

---

## 目錄

1. [這是什麼？](#1-這是什麼)
2. [核心理念](#2-核心理念)
3. [前置需求](#3-前置需求)
4. [安裝設定](#4-安裝設定)
5. [架構總覽](#5-架構總覽)
6. [七階段工作流程](#6-七階段工作流程)
7. [路由設定檔](#7-路由設定檔)
8. [執行模式](#8-執行模式)
9. [指令參考](#9-指令參考)
10. [實戰演練：修復 Bug](#10-實戰演練修復-bug)
11. [實戰演練：新增功能](#11-實戰演練新增功能)
12. [決策閘門詳解](#12-決策閘門詳解)
13. [絕對禁止規則](#13-絕對禁止規則)
14. [邊界情況處理](#14-邊界情況處理)
15. [設定檔深入解析](#15-設定檔深入解析)
16. [輸出產物](#16-輸出產物)
17. [疑難排解](#17-疑難排解)
18. [常見問題](#18-常見問題)

---

## 1. 這是什麼？

Multi-Agent Co-Work（MAW）是一個結構化的多代理協調框架，能夠讓多個 AI 編碼代理 — Claude Code、Codex CLI 和 Gemini CLI — 在非簡單的軟體工程任務上協同合作。MAW 不會讓單一 AI 代理以混亂、交錯的方式完成所有工作（探索、規劃、實作、測試、審查），而是強制在不同階段執行嚴格的角色分離。

可以把它想像成一個運作良好的軟體團隊：一個人調查 Bug，另一個人撰寫修復程式碼，另一個人執行測試，再另一個人審查程式碼 — 每個人之間透過清楚的交接文件溝通，而不是隨意的走廊對話。

---

## 2. 核心理念

### 問題所在：角色模糊（Role Bleed）

AI 輔助編碼中最常見的失敗模式是**角色模糊（Role Bleed）** — 當探索、實作和審查三個角色混在一起時。一個同時在探索程式碼、撰寫修改和檢查自己工作的 AI 會：
- 遺漏沒有仔細查看的檔案
- 在「審查」時替自己的 Bug 找藉口
- 因為「已經知道」修復有效而跳過驗證

### 解決方案：明確階段 + 交接封包

MAW 的解決方案：
1. **將工作分成 7 個明確階段**，每個階段只有一個職責
2. **使用交接封包**（結構化的 JSON 文件）取代代理之間的直接溝通
3. **設置決策閘門** — 協調者在證據不完整時會阻止階段轉換
4. **盲審機制** — 審查者永遠看不到探索報告或計畫，只能看到 diff 和任務描述

---

## 3. 前置需求

| 需求 | 詳情 |
|---|---|
| Python | 3.11 或更新版本 |
| Claude Code CLI | 已安裝且已認證（`claude` 指令可用） |
| Codex CLI | （選用）跨 CLI 實作時需要（`codex` 指令） |
| Gemini CLI | （選用）跨 CLI 探索/審查時需要（`gemini` 指令） |
| Git | 任何近期版本 |
| 作業系統 | Windows、macOS 或 Linux |

> **注意：** 在 **Subagent 模式**（Claude Code 的預設模式）中，你只需要 Claude Code CLI。Codex 和 Gemini 只在 **Runtime 模式**（跨 CLI 協調）中才需要。

---

## 4. 安裝設定

### 方式一：Plugin 安裝（推薦）

此套件現在是一個 Claude Code **plugin**。最簡單的安裝方式是使用 `claude plugins add`：

```bash
claude plugins add multi-agent-cowork
```

安裝完成後，所有子指令會自動以 `/maw:<command>` 的形式可用（例如 `/maw:dispatch`、`/maw:status` 等）。

> **Plugin 系統說明：** 此套件利用 Claude Code 的 plugin 系統，透過 `.claude-plugin/plugin.json` 描述檔註冊自身。Plugin 使用 `plugin:skill` 冒號語法啟用命名空間子指令，避免與其他 plugin 或內建指令衝突。

### 方式二：手動安裝

如果無法使用 `claude plugins add`，可以手動複製套件：

1. 將 `multi-agent-cowork` 目錄複製到你的專案倉庫中的 `.agents/multi-agent-cowork`。

```bash
cp -r /path/to/multi-agent-cowork  your-repo/.agents/multi-agent-cowork
```

2. 確認 `.claude-plugin/plugin.json` 存在。此檔案是 Claude Code 辨識 plugin 的必要描述檔。

安裝後子指令即自動可用。

### 步驟二：安裝 CLI 工具

`scripts/` 目錄中提供了安裝輔助腳本：

```bash
# 安裝 Claude Code CLI
bash .agents/multi-agent-cowork/scripts/install_claude.sh

# 安裝 Codex CLI（選用，Runtime 模式需要）
bash .agents/multi-agent-cowork/scripts/install_codex.sh

# 安裝 Gemini CLI（選用，Runtime 模式需要）
bash .agents/multi-agent-cowork/scripts/install_gemini.sh
```

### 步驟三：驗證安裝

```bash
python runtime/maw.py doctor
```

此指令會檢查：倉庫根目錄偵測、設定檔有效性以及 CLI 工具是否可用。在繼續之前修復它報告的任何問題。

### 步驟四：（選用）設定路由

```bash
# 查看可用的路由設定檔
python runtime/maw.py routing profiles

# 選擇一個設定檔
python runtime/maw.py routing set --profile balanced
```

### 步驟五：（選用）匯入已知失敗

如果你的專案有既存的測試失敗，建立一份基線讓驗證者不會將它們標記為新問題：

```bash
cp .agents/multi-agent-cowork/examples/known-failures.json \
   .multi-agent-cowork/known-failures.json
# 編輯此檔案以列出你實際的已知失敗
```

---

## 5. 架構總覽

### Plugin 系統

Multi-Agent Co-Work 以 Claude Code plugin 的形式發佈。套件根目錄下的 `.claude-plugin/plugin.json` 描述檔告知 Claude Code 此 plugin 的名稱、版本及其提供的子指令。Claude Code 的 plugin 系統採用 `plugin:skill` 冒號語法來註冊命名空間子指令（例如 `/maw:dispatch`），確保不會與其他 plugin 或內建指令產生命名衝突。

### 高層流程

```
┌────────────────────────────────────────────────────────────────┐
│                  ORCHESTRATOR（協調者，主代理）                   │
│   框定任務 → 評估閘門 → 撰寫交接封包                              │
└────┬──────┬──────┬──────┬──────┬──────┬──────┬────────────────┘
     │      │      │      │      │      │      │
     ▼      ▼      ▼      ▼      ▼      ▼      ▼
   收錄   探索    規劃    實作    驗證    審查    報告
          │              │        │      │
          ▼              ▼        ▼      ▼
       Claude          Codex    Shell  Claude
       Gemini                  Claude  Gemini
```

### 關鍵概念

| 概念 | 說明 |
|---|---|
| **Orchestrator（協調者）** | 中央協調器。撰寫所有交接封包、評估決策閘門，且不會自己做實作工作。 |
| **Provider（提供者）** | 一個 AI CLI 工具（Claude、Codex、Gemini）或確定性工具（Shell），負責執行特定階段。 |
| **Handoff Packet（交接封包）** | 協調者在每個階段結束後撰寫的結構化 JSON 文件。它是下一個階段*唯一*允許讀取的東西。 |
| **Decision Gate（決策閘門）** | 一組條件清單，所有條件都必須為真，協調者才允許工作流程推進到下一階段。 |
| **Routing Profile（路由設定檔）** | 一個命名的設定，將每個階段對應到一個或多個提供者。 |

### 溝通模型

```
  ┌──────────┐         ┌──────────┐
  │  探索者   │         │  規劃者   │
  └────┬─────┘         └────┬─────┘
       │ result.json        │ result.json
       ▼                    ▼
  ┌─────────────────────────────────┐
  │           協調者                 │
  │   綜合整理 → 交接封包            │
  └──────────────┬──────────────────┘
                 │ 交接封包
                 ▼
          ┌──────────────┐
          │    實作者     │
          └──────────────┘
```

代理之間**永遠不會**直接溝通。Explorer 不會告訴 Implementer 要修什麼。Reviewer 永遠看不到 Explorer 發現了什麼。所有的溝通都透過協調者的交接封包流轉。

---

## 6. 七階段工作流程

### 階段一：任務收錄（INTAKE）

協調者框定任務。在這裡你需要定義：
- **目標**：任務完成後，什麼狀態應該成立？
- **成功標準**：我們如何確認它有效？
- **約束條件**：什麼東西絕對不能壞掉？

協調者將 `intake.json` 和 `manifest.json` 寫入執行目錄。

---

### 階段二：探索（EXPLORE）

**誰執行：** Claude + Gemini（balanced 設定檔），或僅 Claude（fast 設定檔）
**存取權限：** 唯讀。不允許修改程式碼。
**目的：** 繪製地形圖 — 找出所有相關檔案、進入點、呼叫流程和風險。

Explorer 必須產出：
```
檔案：[路徑:行數範圍 — 在問題中的角色]
進入點：[符號名稱]
呼叫流程：A → B → C
約束條件：[不能被破壞的東西]
風險：[未知項、脆弱區域]
問題：[無法確定的事項]
```

**關鍵規則：** Explorer 只負責辨識問題，**永遠不建議修復方式**。說「我們應該把 X 改成 Y」就是角色模糊。正確的輸出是「X 是處理 Escape 鍵事件的進入點」— 只陳述事實，不開處方。

---

### 階段三：規劃（PLAN）

**誰執行：** Claude
**目的：** 根據 Explorer 的證據建立一份鎖定的實作計畫。

Planner 必須：
1. **鎖定檔案集** — 列出所有將被修改的檔案
2. **掃描消費者** — 誰匯入或呼叫了被變更的程式碼？
3. **定義驗證指令** — 具體的 shell 指令，不是「跑測試」
4. **命名回滾錨點** — 一個 git commit 或 stash，萬一出錯可以回復

> 好的驗證指令範例：`pytest tests/test_modal.py -k "test_escape_nested" -v`
> 不好的範例：「跑相關的測試」

---

### 階段四：實作（IMPLEMENT）

**誰執行：** Codex（預設）
**存取權限：** 可寫入，但受鎖定計畫限制。
**目的：** 套用計畫中定義的修改 — 不多也不少。

關鍵規則：
- 只修改鎖定計畫中列出的檔案
- 如果必須修改未列出的檔案，發出 `scope_extension_needed=true` 並返回 Plan 階段
- 將發現但未處理的問題記錄為「延遲項目」
- 修改超過 2 個檔案時，使用 `isolation: "worktree"` 在隔離的副本上工作

如果計畫在實際操作中行不通，**立刻停止並返回 Plan**。不要自行即興發揮。

---

### 階段五：驗證（VERIFY）

**誰執行：** Shell（確定性執行）+ Claude（分析）
**目的：** 用實際的指令輸出證明實作有效。

此階段執行**兩次**：
1. **基線執行** — 在實作之前，捕獲既有的失敗
2. **驗證執行** — 在實作之後，檢查是否有新的問題

驗證者將每個失敗分類為四種類別之一：

| 分類 | 含義 |
|---|---|
| `task-caused` | 此失敗是由我們的變更引起的 |
| `pre-existing` | 此失敗在我們變更之前就存在（在基線中） |
| `flaky` | 此失敗不穩定地出現（重新執行可確認） |
| `infrastructure` | 網路、Docker、CI 問題 — 與程式碼無關 |

失敗的指令會重新執行一次，然後才被分類為 `flaky`。

---

### 階段六：審查（REVIEW）

**誰執行：** Claude + Gemini（balanced 設定檔）
**存取權限：** 唯讀。**盲審** — 只收到 diff + 任務描述。
**目的：** 獨立的程式碼審查，避免確認偏誤。

Reviewer **永遠看不到**：
- 探索報告
- 實作計畫
- 協調者預期會發生什麼

這是刻意的設計。知道意圖會導致確認偏誤。盲審者能多抓出 2-3 倍的邏輯錯誤，因為他們評估的是程式碼*實際上做了什麼*，而不是*應該做什麼*。

輸出規範：
```
正確性：[問題或「審查 N 個檔案、M 個 hunk 後未發現問題」]
迴歸風險：[具體場景]
邊界案例：[未覆蓋的]
缺少的測試：[應該存在的]
判定：[approve / request changes / block]
```

---

### 階段七：報告（REPORT）

協調者將所有證據彙編成 `final-report.md`：
- 變更了什麼以及為什麼
- 驗證了什麼以及如何驗證
- 剩餘的風險有哪些
- 延遲到未來處理的項目

執行結果標記為 `COMPLETED`（完成）、`PARTIAL`（部分完成）或 `FAILED`（失敗）。

---

## 7. 路由設定檔

路由設定檔決定哪個 AI 提供者處理每個階段。提供三種內建設定檔：

| 階段 | balanced | fast | recovery |
|---|---|---|---|
| 探索 | Claude + Gemini | Claude | Claude + Gemini |
| 規劃 | Claude | Claude | Claude |
| 實作 | Codex | Codex | Codex |
| 驗證 | Shell + Claude | Shell | Shell + Claude + Gemini |
| 審查 | Claude + Gemini | Claude | Claude + Gemini |

- **balanced** — 最佳整體品質。探索和審查時有多重視角。建議用於大多數任務。
- **fast** — 每個階段只有一個提供者。執行最快但冗餘較少。適合理解清楚、影響隔離的變更。
- **recovery** — 最大冗餘。在驗證階段加入 Gemini。用於失敗的執行之後或處理不穩定測試時。

你也可以建立自訂的階段分配：

```bash
# 使用 balanced 設定檔但將實作階段覆蓋為使用 Claude
python3 runtime/maw.py routing set \
  --profile balanced \
  --phase implement=claude \
  --note "前端任務，Claude 更擅長處理 JSX"
```

---

## 8. 執行模式

### 模式一：Subagent 模式（Claude Code 預設）

在此模式下，協調者（你的主 Claude Code 工作階段）為每個角色生成 Claude 子代理。不需要外部 CLI。這是最簡單的入門方式。

**運作方式：**
1. 你向 Claude Code 描述任務
2. Claude Code 作為協調者，遵循 SKILL.md 工作流程
3. 探索階段：生成一個 `subagent_type: "Explore"`、徹底程度 `"very thorough"` 的子代理
4. 實作階段：修改 >2 個檔案時使用 `isolation: "worktree"` 生成子代理
5. 驗證階段：直接執行 shell 指令
6. 審查階段：生成只有 diff 的唯讀子代理

**觸發方式：**
- 描述符合啟動條件的任務，或
- 明確使用 `/maw` 斜線指令

### 模式二：Runtime 模式（跨 CLI）

在此模式下，Python 執行引擎（`maw.py`）跨 Claude CLI、Codex CLI 和 Gemini CLI 進行協調。每個提供者作為獨立的程序執行。

**觸發方式：**
- 透過 plugin 子指令：`/maw:dispatch <任務描述>`
- 或直接使用 Python CLI：`python3 runtime/maw.py dispatch --task "你的任務"`

**運作方式：**
1. 你透過 plugin 子指令或 Python CLI 發起任務
2. 執行引擎建立一個包含所有產物的執行目錄
3. 每個階段透過對應的 CLI 呼叫設定好的提供者
4. 結果以 JSON 格式捕獲，評估閘門，撰寫交接封包
5. 執行持續進行直到完成、失敗或閘門阻擋

**何時使用 Runtime 模式：**
- 你想要不同的 AI 負責不同階段（例如 Codex 負責實作，Gemini 提供額外的審查視角）
- 你需要完整的稽核軌跡和結構化產物
- 你正在設定 CI/CD 整合以進行自動化程式碼審查

---

## 9. 指令參考

### 核心指令

```bash
# 檢查安裝和設定
python3 runtime/maw.py doctor

# 開始完整工作流程
python3 runtime/maw.py dispatch --task "修復登入逾時的 bug"

# 開始但在特定階段後停止
python3 runtime/maw.py dispatch --task "..." --phase-limit implement

# 從特定階段開始（跳過先前的階段）
python3 runtime/maw.py dispatch --task "..." --start-phase plan

# 檢查執行狀態
python3 runtime/maw.py status --run-id <id>

# 繼續被中斷的執行
python3 runtime/maw.py resume --run-id <id>

# 查看最終報告
python3 runtime/maw.py report --run-id <id>
```

### 路由指令

```bash
# 列出可用的設定檔
python3 runtime/maw.py routing profiles

# 顯示當前路由設定
python3 runtime/maw.py routing show

# 設定設定檔
python3 runtime/maw.py routing set --profile balanced

# 覆蓋特定階段
python3 runtime/maw.py routing set \
  --phase implement=codex \
  --phase review=claude,gemini \
  --note "前端預設"

# 重置路由為預設值
python3 runtime/maw.py routing clear
```

### 斜線指令（CLI 工作階段內）

| CLI | 發起任務 | 查看狀態 | 繼續執行 |
|---|---|---|---|
| Claude Code | `/maw:dispatch <任務>` | `/maw:status` | `/maw:resume` |
| Codex | `$dispatch <任務>` | `$status` | `$resume` |
| Gemini | `/dispatch <任務>` | `/status` | `/resume` |

#### 路由子指令（Claude Code）

| 子指令 | 說明 |
|---|---|
| `/maw:show-routing` | 顯示當前路由設定 |
| `/maw:assign-routing` | 設定路由設定檔或覆蓋特定階段 |
| `/maw:clear-routing` | 重置路由為預設值 |
| `/maw:list-profiles` | 列出所有可用的路由設定檔 |

---

## 10. 實戰演練：修復 Bug

讓我們用 MAW 完整走過一個 Bug 修復流程。Bug 描述：在巢狀對話框中按 Escape 鍵會關閉父層的設定面板。

### 步驟一：發起任務

```bash
python3 runtime/maw.py dispatch \
  --task "修復：在巢狀對話框中按 Escape 會關閉父層設定面板。\
          預期：只有巢狀對話框應該關閉。"
```

### 步驟二：任務收錄

協調者寫入：
- **目標：** 當 Escape 被巢狀對話框處理時，保持父層設定面板開啟
- **成功標準：** 巢狀對話框關閉時不會連帶關閉父層覆蓋層
- **約束條件：** 不要讓全域鍵盤快捷鍵發生迴歸

### 步驟三：探索

Claude 和 Gemini 獨立搜尋：
- Modal keydown 處理器 → 找到 `src/components/Modal/useKeyHandler.ts:42-67`
- Escape 鍵事件傳播 → 發現巢狀情況缺少 `event.stopPropagation()`
- 覆蓋層關閉邏輯 → 找到 `src/components/Overlay/Overlay.tsx:128`
- 巢狀對話框的測試 → 找到 `tests/modal.test.tsx`（無巢狀測試案例）

**閘門檢查：** 進入點已確認，surface_coverage=0.85，風險已識別。**通過。**

### 步驟四：規劃

Claude 建立鎖定計畫：
- **檔案：** `useKeyHandler.ts`、`Overlay.tsx`、`modal.test.tsx`
- **消費者掃描：** `SettingsPanel.tsx` 匯入 `Overlay` — 不能壞掉
- **驗證：** `npx jest tests/modal.test.tsx --verbose`
- **回滾：** 當前 HEAD commit `a3f2b1c`

### 步驟五：實作

Codex 套用計畫中的修改：
1. 在巢狀對話框的 Escape 處理器中加入 `event.stopPropagation()`
2. 在 Overlay 中加入守衛以檢查 Escape 是否已被處理
3. 加入巢狀 Escape 行為的新測試案例

### 步驟六：驗證

```
指令：npx jest tests/modal.test.tsx --verbose
結束代碼：0
輸出：Tests: 7 passed, 0 failed
新增失敗：無
評估：通過
```

### 步驟七：審查 + 報告

Reviewer（盲審 — 只看到 diff + 任務）：
- 正確性：事件傳播邏輯看起來正確
- 迴歸風險：如果 stopPropagation 過於激進可能影響全域快捷鍵
- 判定：**approve**（stopPropagation 只限定於巢狀對話框）

最終報告已編譯。執行標記為 **COMPLETED**。

---

## 11. 實戰演練：新增功能

為通知中心新增批量封存功能。

```bash
python3 runtime/maw.py dispatch \
  --task "為通知中心新增批量封存功能。\
          使用者應能選取多則通知並一次封存。\
          必須處理部分失敗和樂觀 UI 更新。"
```

### 階段摘要

| 階段 | 發生什麼 |
|---|---|
| **探索** | 對應通知列表狀態管理、封存異動流程、樂觀更新輔助工具、API 客戶端/後端契約、現有的單一封存測試 |
| **規劃** | 鎖定：選擇狀態模組、批量封存動作、API 客戶端擴展、樂觀狀態處理、新測試 |
| **實作** | Codex 套用所有變更。>5 個檔案 → 分成兩個交付單元 |
| **驗證** | 針對 reducer 狀態的測試、選擇功能的元件測試、整合檢查 |
| **審查** | 檢查：部分失敗處理、刷新後的過期選擇、批量操作控件的無障礙性 |

---

## 12. 決策閘門詳解

決策閘門是品質保障機制。如果任何條件未滿足，協調者將**不會**推進到下一個階段。以下是每個閘門的詳細說明：

### 探索 → 規劃

| # | 條件 | 原因 |
|---|---|---|
| 1 | 至少一個提供者回傳 `status=ok` | 確保探索確實完成 |
| 2 | `entrypoint_status=confirmed`（進入點狀態已確認） | 不知道問題從哪開始就無法規劃 |
| 3 | `surface_coverage >= 0.70`（表面覆蓋率 >= 0.70） | 必須檢查至少 70% 的相關程式碼面 |
| 4 | 具體的檔案或符號清單存在 | 模糊的「在 modal 程式碼的某處」無法執行 |
| 5 | 至少識別一個測試面 | 需要知道用什麼來驗證 |
| 6 | 沒有要求 `re-explore`（重新探索） | 提供者標記覆蓋率不足 |

**如果閘門未通過：** → 帶著識別出的具體缺口送回探索階段。

### 規劃 → 實作

| # | 條件 |
|---|---|
| 1 | 檔案集已鎖定（或有明確理由開放） |
| 2 | 每個共享抽象都完成了消費者掃描 |
| 3 | 驗證指令是具體的 shell 指令 |
| 4 | 已命名回滾錨點 |
| 5 | 沒有要求 `re-plan`（重新規劃） |

### 實作 → 驗證

| # | 條件 |
|---|---|
| 1 | 實作者回傳 `status=ok` |
| 2 | `scope_extension_needed=false`（不需要範圍擴展） |
| 3 | Diff 匹配鎖定的計畫 |

### 驗證 → 審查

| # | 條件 |
|---|---|
| 1 | 每個失敗都已分類（`task-caused` / `pre-existing` / `flaky` / `infrastructure`） |
| 2 | 標記為 `flaky` 前已重新執行失敗指令 |
| 3 | 存在 Shell 驗證 |
| 4 | 沒有要求 `rollback`（回滾） |

### 審查 → 報告

| # | 條件 |
|---|---|
| 1 | 審查者不是實作提供者 |
| 2 | 無未批准的計畫漂移 |
| 3 | 高風險分支有測試、豁免或發布阻擋 |
| 4 | 沒有要求 `block-release`（阻擋發布） |

---

## 13. 絕對禁止規則

這些規則的存在是因為每一條都對應一個具體的、已觀察到的失敗模式。違反任何一條都會降低輸出品質。

| # | 規則 | 原因 |
|---|---|---|
| 1 | **絕對不讓 Explorer 建議修復方式** | Explorer 繪製地形圖；Implementer 決定修改。Explorer 說「我們應該把 X 改成 Y」= 角色模糊。 |
| 2 | **絕對不跳過基線驗證** | 沒有基線，你無法區分「我弄壞了」和「本來就壞了」。最常見的虛假信心來源。 |
| 3 | **絕對不讓 Reviewer 看到計畫** | 知道意圖會導致確認偏誤。盲審多抓出 2-3 倍的 Bug。 |
| 4 | **絕對不在 Implement 期間擴展範圍** | 「順便」會把單檔修復變成三個模組的重構。 |
| 5 | **絕對不接受沒有指令的驗證** | 「沒有錯誤」不是證據。「執行了 `npm test`，exit 0，47 通過」才是證據。 |
| 6 | **絕對不在 Explore 之前執行 Implement** | 沒有探索的「明顯修復」每次都會遺漏第 2 和第 3 個受影響的檔案。 |
| 7 | **絕對不讓代理直接溝通** | 直接對話導致：實作者辯護意圖、審查者繼承框架、探索者污染規劃者。 |

---

## 14. 邊界情況處理

### 當階段卡住時

| 階段 | 信號 | 行動 |
|---|---|---|
| 探索 | 搜尋 3 次後仍找不到進入點 | 擴大：搜尋錯誤字串、設定檔參考、測試檔案 |
| 規劃 | 不確定用哪種方法 | 提出 2 個候選方案，列出取捨，選擇更可逆的 |
| 實作 | 計畫在實際中行不通 | **停止。** 帶著新證據返回規劃。不要即興。 |
| 驗證 | 不清楚失敗是新的還是舊的 | 將失敗輸出與基線逐字比對 |
| 審查 | 發現嚴重問題 | 返回規劃。不要在審查期間修補。 |

### 範圍擴展

當 Implementer 發現需要修改鎖定計畫中沒有的檔案時：

1. **不要**悄悄地修改額外的檔案
2. **不要**把它藏在備註裡或稱之為「風險」
3. **要**發出 `scope_extension_needed=true`，附帶 `requested_files` 和 `decision="request-scope-extension"`
4. 工作流程返回規劃階段，Planner 要麼批准擴展並重新鎖定，要麼拒絕並要求不同的策略

### 範圍蔓延信號

當以下任何情況發生時，暫停並重新界定範圍：
- Implementer 修改了計畫中沒有的檔案
- Diff 超過計畫大小的 3 倍
- 需要理解第 4 個或更多模組
- 驗證者在不相關的區域發現失敗

**應對：** 記錄延遲項目，約束當前範圍，繼續。

---

## 15. 設定檔深入解析

主設定檔是 `config/default.toml`。以下是每個區段的說明：

### [run] — 執行時設定

```toml
[run]
state_dir = ".multi-agent-cowork"          # 執行產物的儲存位置
routing_memory = ".multi-agent-cowork/routing-memory.json"  # 持久化路由設定
known_failures = ".multi-agent-cowork/known-failures.json"  # 既有失敗的基線
max_parallel = 3                            # 每個階段的最大並行提供者數
fail_fast = false                           # 第一個閘門失敗時是否停止？
```

### [policies] — 強制規則

```toml
[policies]
forbid_self_review = true     # 實作者和審查者必須是不同的提供者
require_shell_verifier = true  # 驗證提供者中必須有 Shell（生產環境）
```

### [verification] — 測試指令

```toml
[verification]
commands = [
  "python3 -m compileall runtime tests",   # 語法檢查
  "pytest -q"                               # 執行測試
]
stop_on_failure = false       # 失敗後繼續執行剩餘指令？
rerun_failures_once = true    # 在分類前重新執行失敗的指令一次？
```

### [providers.*] — 提供者設定

```toml
[providers.codex]
command = "codex"                    # CLI 執行檔名稱
model = "gpt-5.2-codex"            # 使用的模型
full_auto = true                     # 不需人工確認即可執行
sandbox_read_only = "read-only"     # 唯讀階段的權限模式
sandbox_write = "workspace-write"   # 寫入階段的權限模式
timeout_seconds = 2400              # 最大執行時間（秒）

[providers.claude]
command = "claude"
model = "sonnet"
read_only_permission_mode = "acceptEdits"
allow_unattended_write = false       # 寫入需要確認
timeout_seconds = 2400

[providers.gemini]
command = "gemini"
read_only_only = true                # 永遠不允許寫入
extra_args = []                      # 額外的 CLI 參數
timeout_seconds = 2400

[providers.shell]
command = "sh"
timeout_seconds = 1800
```

---

## 16. 輸出產物

每次執行都會在 `.multi-agent-cowork/runs/<run-id>/` 下建立一個結構化目錄。以下是每個檔案的說明：

```
.multi-agent-cowork/runs/abc123/
│
├── manifest.json              # 執行元數據：狀態、階段、閘門、時間
├── intake.json                # 任務框定：目標、成功標準、約束條件
├── routing.json               # 此次執行的路由快照
│
├── explore/                   # 探索者的輸出
│   ├── claude/result.json     #   Claude 的探索結果
│   └── gemini/result.json     #   Gemini 的探索結果
│
├── plan/
│   └── claude/result.json     # 鎖定的實作計畫
│
├── implement/
│   └── codex/result.json      # 實作結果 + 偏差
│
├── verify/
│   ├── shell/
│   │   ├── cmd-1.stdout.txt          # 第一個指令的輸出
│   │   ├── cmd-1.rerun.stdout.txt    # 重新執行的輸出（如有失敗）
│   │   └── result.json               # 所有結果的分類
│   └── claude/result.json            # 驗證分析
│
├── review/
│   ├── claude/result.json     # Claude 的盲審結果
│   └── gemini/result.json     # Gemini 的盲審結果
│
├── handoffs/                  # 協調者撰寫的轉換文件
│   ├── explore-to-plan.json   #   探索 → 規劃
│   ├── plan-to-implement.json #   規劃 → 實作
│   ├── implement-to-verify.json   # 實作 → 驗證
│   └── verify-to-review.json     # 驗證 → 審查
│
├── explore-summary.md         # 人類可讀的階段摘要
├── plan-summary.md
├── implement-summary.md
├── verify-summary.md
├── review-summary.md
│
└── final-report.md            # 端到端報告：變更、證據、風險
```

---

## 17. 疑難排解

### "doctor" 報告缺少 CLI

如果 `maw.py doctor` 說找不到某個 CLI，但你只打算使用 Subagent 模式，這沒問題。你只在 Runtime 模式下才需要全部三個 CLI。

### 閘門在探索 → 規劃被阻擋

最常見的原因：`surface_coverage < 0.70`。這意味著探索者沒有檢查足夠多的相關程式碼。協調者會帶著指引將其送回探索階段 — 檢查錯誤字串、設定檔參考或測試檔案。

### 實作者要求範圍擴展

這是正常且預期的行為。工作流程返回規劃階段，Planner 會批准或拒絕擴展。不需要手動介入。

### 驗證失敗被分類為 "task-caused"

這意味著實作引入了迴歸。工作流程會：
1. 分類失敗
2. 可能要求回滾
3. 帶著出錯的證據返回規劃階段

檢查 `verify/shell/cmd-*.stdout.txt` 中的驗證輸出以了解詳情。

### 執行被中斷

使用 `resume` 從中斷處繼續：

```bash
python3 runtime/maw.py resume --run-id <id>
```

manifest 追蹤到達了哪個階段，因此執行會從停止的地方準確繼續。

---

## 18. 常見問題

### 問：什麼時候該用 MAW 而不是直接問 Claude？

當**任何**以下條件成立時使用 MAW：
- 不搜尋就無法列出所有受影響的檔案
- 變更觸及被其他模組使用的程式碼
- 根本原因不確定
- 測試缺失或不穩定

當**所有**以下條件成立時直接使用 Claude：
- 所有受影響的檔案都已知
- 變更是隔離的，沒有下游消費者
- 相關測試存在且通過

---

### 問：可以跳過階段嗎？

可以，使用「壓縮」工作流程：**探索 → 實作 → 驗證**。當所有受影響的檔案已知、變更是隔離的、且相關測試存在時適用。使用 `--start-phase` 和 `--phase-limit` 控制執行哪些階段。

---

### 問：如果我只有 Claude Code，沒有 Codex 或 Gemini 怎麼辦？

使用 Subagent 模式（預設模式）。Claude Code 為每個角色生成子代理。你獲得同樣的結構化工作流程和角色分離，只是全部由 Claude 模型驅動。關鍵好處 — 角色分離和盲審 — 同樣有效。

---

### 問：完整工作流程需要多久？

取決於任務複雜度和程式碼庫大小。每個階段都會呼叫 AI 提供者，它們有自己的處理時間。設定檔中的 `timeout_seconds` 設定（預設：每個提供者 2400 秒）可防止任何單一階段無限期掛起。

---

### 問：可以自訂哪個提供者處理哪個階段嗎？

可以。使用路由指令：

```bash
# 設定基礎設定檔
python3 runtime/maw.py routing set --profile balanced

# 覆蓋特定階段
python3 runtime/maw.py routing set --phase implement=claude --phase review=gemini

# 加上備註提供上下文
python3 runtime/maw.py routing set --phase implement=claude --note "Claude 更擅長處理 TypeScript"
```

路由在你清除之前會跨執行持續存在。

---

### 問：交接封包是什麼？為什麼重要？

交接封包是協調者在每個階段完成後撰寫的結構化 JSON 文件。它們包含：
- 已完成階段的證據
- 下一階段的鎖定上下文
- 閘門評估結果
- 未解決的風險和所需行動

它們之所以重要，是因為它們是下一階段**唯一**讀取的東西。這防止代理繼承彼此的偏見、假設或框架。協調者控制敘事，而不是個別代理。

---

### 問：如何查看過去的執行？

```bash
# 列出執行目錄
ls .multi-agent-cowork/runs/

# 查看特定執行的狀態
python3 runtime/maw.py status --run-id <id>

# 閱讀最終報告
python3 runtime/maw.py report --run-id <id>

# 或直接閱讀報告檔案
cat .multi-agent-cowork/runs/<id>/final-report.md
```

---

## 快速參考卡

```
┌─────────────────────────────────────────────────────────────┐
│              多代理協作 MULTI-AGENT CO-WORK                   │
│                    快速參考                                   │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  階段：收錄 → 探索 → 規劃 → 實作                              │
│              → 驗證 → 審查 → 報告                             │
│                                                              │
│  設定檔：balanced（預設）| fast | recovery                    │
│                                                              │
│  指令：                                                      │
│    doctor              檢查安裝                               │
│    dispatch --task ""   開始工作流程                           │
│    status --run-id      查看進度                              │
│    resume --run-id      繼續執行                              │
│    report --run-id      查看報告                              │
│    routing show         當前路由                              │
│    routing set          變更路由                              │
│                                                              │
│  絕對禁止：                                                   │
│    ✗ Explorer 建議修復方式                                    │
│    ✗ 跳過基線驗證                                             │
│    ✗ 讓 Reviewer 看到計畫                                     │
│    ✗ 在實作中擴展範圍                                         │
│    ✗ 接受「沒有錯誤」作為驗證                                   │
│    ✗ 在探索前實作                                             │
│    ✗ 讓代理直接對話                                            │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

*本教學涵蓋 Multi-Agent Co-Work v4（Claude Code plugin 版）。版本歷史請參見 CHANGELOG.md。*
