# OpenClaw Monitor v1.1.0

发布日期：2026-03-18

## 亮点

- 打通 Gateway WebSocket 实时状态：总览页可看到 Gateway WS/Reatime 连接状态、最近 health 快照。
- Agent / 任务分页不再为空：从 Gateway `health` 事件自动落库并生成任务视图。
- Token / 成本 / 耗时同步：
  - Token：从本机 `~/.openclaw/agents/*/sessions/sessions.json` 持续采集快照。
  - 耗时：从 session `.jsonl` 的首尾时间戳推导 `durationMs`。
  - 成本：优先从 session `.jsonl` 的 `message.usage.cost` 汇总；若没有 cost 字段则可选用 `config/pricing.json` 进行估算。

## 配置与兼容性

- 不需要修改 OpenClaw 代码（Monitor 仅通过 Gateway + 本机 session 文件读取实现可视化）。
- 如果你使用的模型本身不产生费用（例如 `*:free`），金额消耗可能始终为 0，这属于正常现象。

## 脱敏与安全

- `config/gateway.json`、`backend/config/`、`config/pricing.json`、`data/*.db`、`data/*events*.jsonl` 均不会被提交到 git。
- API 返回 Gateway 配置时只暴露 `hasToken/hasPassword`，不会返回 token/password 明文。

