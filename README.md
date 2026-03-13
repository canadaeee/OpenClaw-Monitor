# OpenClaw Monitor

[中文](#中文) | [English](#english)

OpenClaw Monitor is a standalone observability dashboard for OpenClaw. Its goal is simple: turn a black-box runtime into a readable surface for tasks, agents, events, alerts, and token usage.

This project is designed as a read-only monitor, not a control plane.

## 中文

### 项目定位

OpenClaw Monitor 是一个独立的只读监控系统，用于把 OpenClaw 的运行过程从“黑盒”变成“可观察、可追踪、可排障”的可视化界面。

当前 v1 的产品边界非常明确：

- 以本机访问为主
- 以 node 侧旁路采集为主
- 不把跨设备直连 Gateway 作为首发硬要求
- 聚焦任务、Agent、事件、告警、Token / 成本的观测能力

### 当前状态

目前仓库已经具备这些能力：

- FastAPI 后端基础
- React 前端控制台
- SQLite + JSONL 数据层
- Gateway 探测与基础配置能力
- node-side collector
- 本机 JSONL 导入与自动轮询
- Windows / Ubuntu / macOS 安装脚本
- GitHub 发布用的一键安装 bootstrap 入口

这意味着它已经进入“可持续开发 + 可开始内部测试”的阶段，但还不是最终发布版。

### 技术栈

- 后端：Python + FastAPI
- 前端：React + Vite
- 存储：SQLite + JSONL

说明：

- 本项目不会因为 OpenClaw 本体使用 Swift 就强制转向 Swift
- 当前监控系统更适合 Python 的脚本能力、日志处理能力和快速迭代节奏

### 架构方向

v1 推荐架构：

- Monitor 与 OpenClaw node 运行在同一台机器
- node 本机输出 JSONL 事件
- Monitor 通过 node-side collector 读取并标准化入库
- 前端通过 Monitor 自己的只读 API 展示数据

默认监听地址：

- `127.0.0.1:12888`

### 一键安装

发布到 GitHub 后，可直接提供以下安装命令。

#### Ubuntu

```bash
curl -fsSL https://raw.githubusercontent.com/<owner>/<repo>/main/scripts/bootstrap-install.sh | bash -s -- --repo https://github.com/<owner>/<repo>.git
```

#### macOS

```bash
curl -fsSL https://raw.githubusercontent.com/<owner>/<repo>/main/scripts/bootstrap-install.sh | bash -s -- --repo https://github.com/<owner>/<repo>.git
```

#### Windows PowerShell

```powershell
irm https://raw.githubusercontent.com/<owner>/<repo>/main/scripts/bootstrap-install.ps1 | iex
Install-OpenClawMonitor -RepoUrl https://github.com/<owner>/<repo>.git
```

安装后可使用对应平台脚本启动：

- Windows: `scripts/start-windows.ps1`
- Ubuntu: `scripts/start-ubuntu.sh`
- macOS: `scripts/start-macos.sh`

### 本地开发

后端：

```bash
cd backend
python -m uvicorn app.main:app --host 127.0.0.1 --port 12888 --reload
```

前端：

```bash
cd frontend
npm install
npm run dev -- --host 127.0.0.1 --port 12889
```

### node-side collector

当前已提供这些接口：

- `GET /api/node-collector/status`
- `GET /api/node-collector/sample`
- `POST /api/node-collector/ingest-file`
- `POST /api/node-collector/poll`

推荐事件文件路径：

- `data/node-events.jsonl`

首选接入方式：

1. OpenClaw node 在本机输出 JSONL 事件
2. Monitor 自动轮询该文件
3. 事件被标准化后进入任务、Agent、告警和总览视图

### GitHub 发布建议

1. 在 GitHub 创建空仓库
2. 本地执行：

```bash
git remote add origin <your-repo-url>
git push -u origin main
```

3. 把本文中的 `<owner>/<repo>` 替换成真实仓库地址
4. 在 GitHub Release 中使用 `RELEASE_NOTES_v0.1.0.md`

### 仓库说明

- `docs/` 目录仅本地保留，不会 push 到 GitHub
- 发布说明见 `RELEASE_NOTES_v0.1.0.md`

### 致敬

本项目的监控对象是 OpenClaw。

在这里，向 OpenClaw 的原作者与项目贡献者致敬。OpenClaw 本身提供了非常强的代理式工作流和工程体验，而 OpenClaw Monitor 的出发点，是在尊重其原有设计的前提下，为运行过程补上一层可观测性与排障视图。

如果你正在使用 OpenClaw，也建议优先关注并支持原项目的发展。

## English

### Project Positioning

OpenClaw Monitor is a standalone read-only monitoring system that makes OpenClaw easier to observe, trace, and debug.

The current v1 scope is intentionally narrow:

- local-first access
- node-side sidecar collection first
- cross-device direct Gateway access is not a launch requirement
- focus on tasks, agents, events, alerts, and token / cost visibility

### Current Status

The repository already includes:

- FastAPI backend foundation
- React dashboard frontend
- SQLite + JSONL storage
- Gateway probing and basic configuration
- node-side collector
- local JSONL ingestion and polling
- install scripts for Windows / Ubuntu / macOS
- bootstrap entrypoints for GitHub-based one-line install

That means the project is already in an internal-testable stage, even though it is not the final release yet.

### Stack

- Backend: Python + FastAPI
- Frontend: React + Vite
- Storage: SQLite + JSONL

Notes:

- This monitor does not switch to Swift just because OpenClaw itself uses Swift heavily
- Python is currently the better fit for logs, event normalization, and fast iteration

### Architecture Direction

Recommended v1 architecture:

- run Monitor on the same machine as the OpenClaw node
- emit local JSONL events from the node
- let the node-side collector normalize and ingest them
- keep the frontend talking only to Monitor’s read-only API

Default listener:

- `127.0.0.1:12888`

### One-Line Install

After publishing to GitHub, you can expose these install commands.

#### Ubuntu

```bash
curl -fsSL https://raw.githubusercontent.com/<owner>/<repo>/main/scripts/bootstrap-install.sh | bash -s -- --repo https://github.com/<owner>/<repo>.git
```

#### macOS

```bash
curl -fsSL https://raw.githubusercontent.com/<owner>/<repo>/main/scripts/bootstrap-install.sh | bash -s -- --repo https://github.com/<owner>/<repo>.git
```

#### Windows PowerShell

```powershell
irm https://raw.githubusercontent.com/<owner>/<repo>/main/scripts/bootstrap-install.ps1 | iex
Install-OpenClawMonitor -RepoUrl https://github.com/<owner>/<repo>.git
```

Startup scripts:

- Windows: `scripts/start-windows.ps1`
- Ubuntu: `scripts/start-ubuntu.sh`
- macOS: `scripts/start-macos.sh`

### Local Development

Backend:

```bash
cd backend
python -m uvicorn app.main:app --host 127.0.0.1 --port 12888 --reload
```

Frontend:

```bash
cd frontend
npm install
npm run dev -- --host 127.0.0.1 --port 12889
```

### Node-Side Collector

Current endpoints:

- `GET /api/node-collector/status`
- `GET /api/node-collector/sample`
- `POST /api/node-collector/ingest-file`
- `POST /api/node-collector/poll`

Recommended event file path:

- `data/node-events.jsonl`

Preferred workflow:

1. the OpenClaw node emits local JSONL events
2. Monitor polls the file
3. events are normalized into tasks, agents, alerts, and overview snapshots

### GitHub Publishing

1. Create an empty GitHub repository
2. Run:

```bash
git remote add origin <your-repo-url>
git push -u origin main
```

3. Replace `<owner>/<repo>` in this README
4. Use `RELEASE_NOTES_v0.1.0.md` for the first GitHub Release

### Repository Notes

- `docs/` is intentionally kept local and excluded from GitHub
- release notes live in `RELEASE_NOTES_v0.1.0.md`

### Respect

This project exists to observe OpenClaw.

Respect and thanks to the original OpenClaw author and contributors. OpenClaw itself provides the foundation; OpenClaw Monitor is meant to complement it with observability, not replace it.

If you use OpenClaw, please support and follow the original project as well.
