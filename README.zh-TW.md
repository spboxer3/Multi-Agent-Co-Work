# Multi-Agent Co-Work（多角色協作工作流）

一個結構化的多角色工作流 Plugin，專為非瑣碎的程式碼任務設計。將工作拆分為明確的角色 — **協調、探索、實作、驗證、審查** — 以防止角色混淆並提高可靠性。

## 安裝

```bash
# 透過 claude plugins add 安裝
claude plugins add /path/to/multi-agent-cowork

# 或手動複製到 ~/.claude/plugins/ 後註冊 plugin
```

Plugin 設定檔位於 `.claude-plugin/plugin.json`。

## 兩種執行模式

### Subagent 模式（Claude Code 預設）

由 Claude 直接調度 subagent，無需外部 CLI。

觸發方式：`/maw` 或描述一個涉及多檔案、根因不明或共享抽象的任務。

### Runtime 模式（跨 CLI 調度）

使用 `runtime/maw.py` 將任務分派給 **Claude CLI**、**Codex CLI** 和 **Gemini CLI**。

```bash
# 檢查環境
python3 runtime/maw.py doctor

# 分派任務
python3 runtime/maw.py dispatch --task "修復設定面板的 Escape 鍵問題"

# 查看狀態 / 續跑 / 報告
python3 runtime/maw.py status --run-id <id>
python3 runtime/maw.py resume --run-id <id>
python3 runtime/maw.py report --run-id <id>

# 路由管理（哪個 AI 負責哪個階段）
python3 runtime/maw.py routing show
python3 runtime/maw.py routing set --profile balanced
python3 runtime/maw.py routing set --phase implement=codex --phase review=claude,gemini
python3 runtime/maw.py routing clear
```

## 預設路由設定

| 階段 | balanced | fast |
|------|----------|------|
| 探索（Explore） | Claude + Gemini | Claude |
| 規劃（Plan） | Claude | Claude |
| 實作（Implement） | Codex | Codex |
| 驗證（Verify） | Shell + Claude | Shell |
| 審查（Review） | Claude + Gemini | Claude |

設定檔：`config/default.toml`

## 工作流程階段

```
接收 → 探索 → 規劃 → 實作 → 驗證 → 審查 → 報告
```

每次階段轉換都有門檻（gate）— 當證據不足時，orchestrator 會阻擋進度。詳見 `references/decision-gates.md`。

## 核心設計原則

- **先讀後寫**：探索階段僅讀不寫，先確認影響範圍再動手。
- **基線驗證**：實作前先跑測試，以區分新引入的失敗和原本就存在的失敗。
- **盲審**：審查者只看 diff 和任務描述，不看規劃或探索報告，避免確認偏誤。
- **禁止直接溝通**：各 agent 透過 orchestrator 產生的 handoff 封包協調，不直接對話。
- **最小差異**：實作滿足目標的最小修改，將範圍擴張記錄為延後項目。

## 子指令

本 Plugin 提供以下子指令（使用冒號語法）：

| 指令 | 說明 |
|------|------|
| `/maw:dispatch` | 分派任務 |
| `/maw:status` | 查看狀態 |
| `/maw:resume` | 續跑任務 |
| `/maw:show-routing` | 顯示路由 |
| `/maw:assign-routing` | 設定路由 |
| `/maw:clear-routing` | 清除路由 |
| `/maw:list-profiles` | 列出可用路由設定檔 |

## 目錄結構

```
multi-agent-cowork/
├── .claude-plugin/
│   └── plugin.json              # Plugin 設定檔
├── SKILL.md                     # Skill 入口（Claude Code 載入）
├── AGENTS.md                    # 專案層級指引
├── config/
│   └── default.toml             # Provider 設定與路由設定檔
├── prompts/                     # 各角色的 system prompt
│   ├── orchestrator.md          # 協調者
│   ├── explorer.md              # 探索者
│   ├── planner.md               # 規劃者
│   ├── implementer.md           # 實作者
│   ├── verifier.md              # 驗證者
│   └── reviewer.md              # 審查者
├── templates/                   # 結構化輸出模板
│   ├── task-brief.md            # 任務摘要
│   ├── exploration-report.md    # 探索報告
│   ├── implementation-plan.md   # 實作計畫
│   ├── verification-report.md   # 驗證報告
│   └── review-report.md         # 審查報告
├── references/                  # 專家知識文件
│   ├── decision-gates.md        # 階段門檻條件
│   └── communication-protocol.md # 通訊協議
├── scripts/                     # Shell 工具腳本
│   ├── collect_context.sh       # 收集 repo 資訊
│   ├── run_checks.sh            # 執行驗證
│   └── summarize_diff.sh        # 摘要 diff
├── schemas/
│   └── agent_result.schema.json # Provider 輸出的 JSON schema
├── runtime/                     # Python 調度器（跨 CLI 模式）
│   ├── maw.py                   # CLI 入口
│   ├── orchestrator.py          # 調度邏輯
│   ├── config.py                # 設定載入
│   ├── models.py                # 資料模型
│   ├── prompting.py             # Prompt 組裝
│   ├── artifacts.py             # 產出物管理
│   ├── routing_memory.py        # 路由記憶
│   ├── state_machine.py         # 狀態機
│   ├── utils.py                 # 工具函式
│   └── providers/               # AI CLI 呼叫器
│       ├── base.py              # 抽象基底
│       ├── claude_code.py       # Claude CLI
│       ├── codex_cli.py         # Codex CLI
│       ├── gemini_cli.py        # Gemini CLI
│       └── shell_verifier.py    # Shell 驗證
└── skills/                      # 子指令（slash commands）
    ├── multi-agent-cowork/      # 主指令
    ├── dispatch/                # 分派任務
    ├── status/                  # 查看狀態
    ├── resume/                  # 續跑任務
    ├── show-routing/            # 顯示路由
    ├── assign-routing/          # 設定路由
    ├── clear-routing/           # 清除路由
    └── list-profiles/           # 列出路由設定檔
```

## 策略（Policies）

- `forbid_self_review`：實作者和審查者必須是不同的 provider（預設：true）
- `require_shell_verifier`：驗證階段必須包含 Shell 驗證（預設：true）

## 授權

自由使用。請根據你的工程標準調整角色 prompt 和驗證腳本。
