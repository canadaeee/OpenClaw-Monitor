# OpenClaw Monitor v1.1.3

发布日期：2026-03-18

## 修复

- Token 动态更新：从 `~/.openclaw/agents/*/sessions/sessions.json` 采集时，`totalTokensFresh/totalTokens` 与 `inputTokens+outputTokens+cache*` 可能不同步。
  现在对总量取 `max(computed_total, reported_total)`，避免出现“启动时读到一次，后续不增长”的情况。

