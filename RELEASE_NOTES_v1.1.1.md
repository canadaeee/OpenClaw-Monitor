# OpenClaw Monitor v1.1.1

发布日期：2026-03-18

## 改动

- 默认启用 Gateway 订阅：未提供 `config/gateway.json` / 未设置环境变量时，Monitor 启动即按本机候选地址自动探测并订阅 Gateway WS（无需手动点开开关）。
- 跨平台一致性：依赖的本机 OpenClaw 数据路径统一使用 `~/.openclaw/...`（Windows/macOS/Linux 都可通过用户目录解析）。

## 说明

- 不会提交或返回任何 token/password 明文；token 仍可从 `~/.openclaw/openclaw.json` 自动读取或由环境变量提供。
- 如需关闭订阅：设置 `OPENCLAW_GATEWAY_ENABLED=0` 或在 UI 中关闭（保存到本地 `config/gateway.json`，该文件默认被 git 忽略）。

