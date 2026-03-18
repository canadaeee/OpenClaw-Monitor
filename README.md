# OpenClaw Monitor

[中文](#中文) | [English](#english)

OpenClaw Monitor is a standalone observability dashboard for OpenClaw. It focuses on one thing: turning OpenClaw's black-box runtime into a readable, queryable, and debuggable surface for tasks, agents, events, alerts, and token usage.

This project is a read-only monitor, not a control plane.

## 中文

### 快速开始（推荐）

安装完成后会自动启动（可选），打开浏览器访问 `http://127.0.0.1:12889`。

#### Ubuntu / macOS

```bash
curl -fsSL https://raw.githubusercontent.com/canadaeee/OpenClaw-Monitor/main/scripts/bootstrap-install.sh | bash -s -- --repo https://github.com/canadaeee/OpenClaw-Monitor.git --start
```

#### Windows PowerShell

```powershell
irm https://raw.githubusercontent.com/canadaeee/OpenClaw-Monitor/main/scripts/bootstrap-install.ps1 | iex
Install-OpenClawMonitor -RepoUrl https://github.com/canadaeee/OpenClaw-Monitor.git -Start
```

如果你已拉取仓库到本地：

- Ubuntu / macOS：`bash ./scripts/run.sh`
- Windows：`.\scripts\run-windows.ps1`

如果提示端口被占用：

- Ubuntu / macOS：`bash ./scripts/stop.sh` 后再启动
- Windows：`.\scripts\stop-windows.ps1` 后再启动

### 项目定位

OpenClaw Monitor 是一个独立的只读监控系统，用来把 OpenClaw 的运行过程从“黑盒”变成“可观察、可追踪、可排障”的可视化界面。

当前版本的设计边界很明确：

- 本机优先访问
- Gateway 同机优先
- 不把跨设备直连 Gateway 作为首发硬要求
- 聚焦任务、Agent、事件、告警、Token / 成本观测

### 当前能力

当前仓库已经具备这些基础能力：

- FastAPI 后端服务
- React + Vite 前端控制台
- SQLite + JSONL 存储层
- Gateway 探测与手动配置
- Gateway 本机探测与读取
- node-side collector（补充方案）
- 本机 JSONL 自动轮询与导入
- Windows / Ubuntu / macOS 安装、启动、停止、更新脚本
- GitHub 一键拉取安装入口

这意味着它已经进入“可持续开发 + 可开始内部测试”的阶段，但还不是最终正式版。

### 技术栈

- 后端：Python + FastAPI
- 前端：React + Vite
- 存储：SQLite + JSONL

说明：

- 本项目不会因为 OpenClaw 本体大量使用 Swift 就强制转向 Swift
- 监控系统更适合 Python 的脚本能力、日志处理能力和快速迭代效率

### 架构方向

推荐的 v1 路径：

1. OpenClaw Gateway 与 Monitor 运行在同一台机器
2. Monitor 优先通过本机 `127.0.0.1:18789` 探测并读取 Gateway
3. 当前无法直接从 Gateway 获取的场景，再退回 node-side collector / JSONL 补充
4. 前端只访问 Monitor 自己的只读 API

默认监听地址：

- 后端：`127.0.0.1:12888`
- 前端预览：`127.0.0.1:12889`

### 一键安装

发布到 GitHub 后，可以直接提供下面的安装命令。

#### Ubuntu / macOS

```bash
curl -fsSL https://raw.githubusercontent.com/canadaeee/OpenClaw-Monitor/main/scripts/bootstrap-install.sh | bash -s -- --repo https://github.com/canadaeee/OpenClaw-Monitor.git --start
```

说明：

- 安装脚本会自动在 `backend/.venv` 下创建后端虚拟环境
- 不依赖系统级 `pip install`
- 如果系统缺少 `python3-venv`，请先安装后再执行脚本

#### Windows PowerShell

```powershell
irm https://raw.githubusercontent.com/canadaeee/OpenClaw-Monitor/main/scripts/bootstrap-install.ps1 | iex
Install-OpenClawMonitor -RepoUrl https://github.com/canadaeee/OpenClaw-Monitor.git -Start
```

### 安装后常用命令

#### Windows

- 安装：`.\scripts\install-windows.ps1`
- 启动：`.\scripts\run-windows.ps1`
- 停止：`.\scripts\stop-windows.ps1`
- 更新：`.\scripts\update-windows.ps1`

#### Ubuntu

- 安装：`bash ./scripts/install-ubuntu.sh`
- 启动：`bash ./scripts/run.sh`
- 停止：`bash ./scripts/stop-ubuntu.sh`
- 更新：`bash ./scripts/update-ubuntu.sh`

#### macOS

- 安装：`bash ./scripts/install-macos.sh`
- 启动：`bash ./scripts/run.sh`
- 停止：`bash ./scripts/stop-macos.sh`
- 更新：`bash ./scripts/update-macos.sh`

### 本地开发

#### 后端

```bash
cd backend
python -m uvicorn app.main:app --host 127.0.0.1 --port 12888 --reload
```

#### 前端

```bash
cd frontend
npm install
npm run dev -- --host 127.0.0.1 --port 12889
```

### Node-Side Collector

当前已提供接口：

- `GET /api/node-collector/status`
- `GET /api/node-collector/sample`
- `POST /api/node-collector/ingest-file`
- `POST /api/node-collector/poll`

推荐事件文件路径：

- `data/node-events.jsonl`

补充接入方式：

1. OpenClaw node 在本机输出 JSONL 事件
2. Monitor 自动轮询该文件
3. 事件被标准化后进入任务、Agent、告警和总览视图

### 发布到 GitHub

1. 创建空仓库
2. 本地执行：

```bash
git remote add origin <your-repo-url>
git push -u origin main
```

3. 仓库默认远端地址为 `https://github.com/canadaeee/OpenClaw-Monitor.git`
4. 使用根目录的 [`RELEASE_NOTES_v1.1.4.md`](./RELEASE_NOTES_v1.1.4.md) 作为最新 Release 文案（历史版本见 `RELEASE_NOTES_v1.*.md`）

### 仓库说明

- `docs/` 目录仅本地保留，不会推送到 GitHub
- 版本发布说明位于 [`RELEASE_NOTES_v1.1.4.md`](./RELEASE_NOTES_v1.1.4.md)

### 致敬

OpenClaw Monitor 的观测对象是 OpenClaw。

在这里，向 OpenClaw 原作者和所有贡献者致敬。OpenClaw 本身提供了非常优秀的代理式工作流体验，而 OpenClaw Monitor 的目标是在尊重其原有设计的前提下，为运行过程补上一层可观测性与排障视图。

如果你正在使用 OpenClaw，也建议优先关注并支持原项目的发展。

## English

### Quick Start (Recommended)

After install, open `http://127.0.0.1:12889`.

#### Ubuntu / macOS

```bash
curl -fsSL https://raw.githubusercontent.com/canadaeee/OpenClaw-Monitor/main/scripts/bootstrap-install.sh | bash -s -- --repo https://github.com/canadaeee/OpenClaw-Monitor.git --start
```

#### Windows PowerShell

```powershell
irm https://raw.githubusercontent.com/canadaeee/OpenClaw-Monitor/main/scripts/bootstrap-install.ps1 | iex
Install-OpenClawMonitor -RepoUrl https://github.com/canadaeee/OpenClaw-Monitor.git -Start
```

If you already cloned the repo:

- Ubuntu / macOS: `bash ./scripts/run.sh`
- Windows: `.\scripts\run-windows.ps1`

### Project Positioning

OpenClaw Monitor is a standalone read-only monitoring system that makes OpenClaw easier to observe, trace, and debug.

The current v1 scope is intentionally narrow:

- local-first access
- same-machine Gateway first
- cross-device direct Gateway access is not a launch requirement
- focus on tasks, agents, events, alerts, and token / cost visibility

### Current Capabilities

The repository already includes:

- FastAPI backend service
- React + Vite dashboard frontend
- SQLite + JSONL storage
- Gateway probing and manual configuration
- local Gateway probing and reading
- node-side collector as fallback
- local JSONL polling and ingestion
- install / start / stop / update scripts for Windows, Ubuntu, and macOS
- GitHub bootstrap entrypoints for one-line install

This means the project is already in an internal testing stage, even though it is not the final release yet.

### Stack

- Backend: Python + FastAPI
- Frontend: React + Vite
- Storage: SQLite + JSONL

Notes:

- This project does not switch to Swift just because OpenClaw itself uses Swift heavily
- Python is a better fit here for scripting, log parsing, event normalization, and fast iteration

### Architecture Direction

Recommended v1 path:

1. Run Monitor on the same machine as the OpenClaw Gateway
2. Let Monitor probe and read the local Gateway on `127.0.0.1:18789`
3. Use the node-side collector / JSONL path only as a fallback when Gateway-side observability is insufficient
4. Keep the frontend talking only to Monitor's read-only API

Default listeners:

- Backend: `127.0.0.1:12888`
- Frontend preview: `127.0.0.1:12889`

### One-Line Install

After publishing to GitHub, you can expose these commands.

#### Ubuntu / macOS

```bash
curl -fsSL https://raw.githubusercontent.com/canadaeee/OpenClaw-Monitor/main/scripts/bootstrap-install.sh | bash -s -- --repo https://github.com/canadaeee/OpenClaw-Monitor.git --start
```

#### Windows PowerShell

```powershell
irm https://raw.githubusercontent.com/canadaeee/OpenClaw-Monitor/main/scripts/bootstrap-install.ps1 | iex
Install-OpenClawMonitor -RepoUrl https://github.com/canadaeee/OpenClaw-Monitor.git -Start
```

### Common Commands After Install

#### Windows

- Install: `.\scripts\install-windows.ps1`
- Start: `.\scripts\run-windows.ps1`
- Stop: `.\scripts\stop-windows.ps1`
- Update: `.\scripts\update-windows.ps1`

#### Ubuntu

- Install: `bash ./scripts/install-ubuntu.sh`
- Start: `bash ./scripts/run.sh`
- Stop: `bash ./scripts/stop-ubuntu.sh`
- Update: `bash ./scripts/update-ubuntu.sh`

#### macOS

- Install: `bash ./scripts/install-macos.sh`
- Start: `bash ./scripts/run.sh`
- Stop: `bash ./scripts/stop-macos.sh`
- Update: `bash ./scripts/update-macos.sh`

### Local Development

#### Backend

```bash
cd backend
python -m uvicorn app.main:app --host 127.0.0.1 --port 12888 --reload
```

#### Frontend

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

Fallback flow:

1. The OpenClaw node emits local JSONL events
2. Monitor polls the file automatically
3. Events are normalized into task, agent, alert, and overview views

### Publishing to GitHub

1. Create an empty repository
2. Run:

```bash
git remote add origin <your-repo-url>
git push -u origin main
```

3. The default repository remote is `https://github.com/canadaeee/OpenClaw-Monitor.git`
4. Use [`RELEASE_NOTES_v1.1.4.md`](./RELEASE_NOTES_v1.1.4.md) for the latest release notes (historical notes: `RELEASE_NOTES_v1.*.md`)

### Repository Notes

- `docs/` is intentionally kept local and excluded from GitHub
- release notes live in [`RELEASE_NOTES_v1.1.4.md`](./RELEASE_NOTES_v1.1.4.md)

### Respect

OpenClaw Monitor exists to observe OpenClaw.

Respect and thanks to the original OpenClaw author and contributors. OpenClaw provides the foundation; OpenClaw Monitor is meant to complement it with observability, not replace it.

If you use OpenClaw, please support and follow the original project as well.
