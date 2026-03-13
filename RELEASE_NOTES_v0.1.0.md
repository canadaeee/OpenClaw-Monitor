# OpenClaw Monitor v0.1.0

[中文](#中文) | [English](#english)

## 中文

### 首发内容

- 提供独立的 OpenClaw 可视化监控台
- 提供总览、Agent、任务、Token / 成本、事件流、告警页面
- 提供 FastAPI + SQLite + JSONL 后端基础
- 提供 node-side collector，本机可导入 JSONL 事件
- 支持本机优先的 Gateway 探测与配置
- 提供 Windows、Ubuntu、macOS 安装脚本
- 提供 `curl` / `irm` 一键拉取安装入口

### 当前推荐用法

- 与 OpenClaw node 运行在同一台机器
- 使用本机浏览器访问 `127.0.0.1:12888`
- 通过 node-side collector 从本机 JSONL 文件采集事件

### 已知边界

- v0.1.0 不把跨设备直连 Gateway 作为首发硬要求
- 对需要 `device identity` 的远程 Gateway，尚未做完整旁路适配
- node-side collector 当前优先支持 JSONL 文件输入

## English

### Initial Release

- Standalone OpenClaw monitoring dashboard
- Overview, Agents, Tasks, Token/Cost, Events, and Alerts pages
- FastAPI + SQLite + JSONL backend foundation
- Node-side collector with local JSONL ingestion
- Local-first Gateway probing and configuration
- Install scripts for Windows, Ubuntu, and macOS
- One-line bootstrap installers via `curl` and `irm`

### Recommended Usage

- Run Monitor on the same machine as the OpenClaw node
- Open the UI locally on `127.0.0.1:12888`
- Feed local JSONL events into the node-side collector

### Current Boundaries

- Cross-device direct Gateway access is not a v0.1.0 requirement
- Remote Gateways requiring device identity are not fully adapted yet
- The node-side collector currently focuses on JSONL input first
