# OpenClaw Monitor v0.1.0

[中文](#中文) | [English](#english)

## 中文

### 首版内容

- 提供独立的 OpenClaw 可视化监控台
- 提供总览、Agent、任务、Token / 成本、事件流、告警页面
- 提供 FastAPI + SQLite + JSONL 后端基础
- 提供 node-side collector，本机可自动轮询 JSONL 事件文件
- 提供本机优先的 Gateway 探测与配置
- 提供 Windows、Ubuntu、macOS 安装 / 启动 / 停止 / 更新脚本
- 提供 `curl` / `irm` 一键拉取安装入口

### 推荐使用方式

- 将 Monitor 与 OpenClaw node 部署在同一台机器
- 使用本机浏览器访问 Monitor
- 通过 node-side collector 从本机 JSONL 事件文件采集数据

### 当前边界

- v0.1.0 不把跨设备直连 Gateway 作为首发硬要求
- 对需要 `device identity` 的远程 Gateway，暂未完成完整适配
- node-side collector 当前优先支持 JSONL 文件输入
- 暂未提供界面内一键自更新，当前推荐使用脚本更新

## English

### Initial Release

- Standalone OpenClaw monitoring dashboard
- Overview, Agents, Tasks, Token / Cost, Events, and Alerts pages
- FastAPI + SQLite + JSONL backend foundation
- Node-side collector with automatic local JSONL polling
- Local-first Gateway probing and configuration
- Install / start / stop / update scripts for Windows, Ubuntu, and macOS
- One-line bootstrap installers via `curl` and `irm`

### Recommended Usage

- Run Monitor on the same machine as the OpenClaw node
- Access Monitor from a local browser
- Feed local JSONL events into the node-side collector

### Current Boundaries

- Cross-device direct Gateway access is not a v0.1.0 requirement
- Remote Gateways requiring device identity are not fully adapted yet
- The node-side collector currently focuses on JSONL input first
- In-app one-click self-update is not included yet; script-based update is the recommended path for now
