# OpenClaw Monitor

[中文](#中文) | [English](#english)

## 中文

OpenClaw Monitor 是一个独立的只读观测系统，用来把 OpenClaw 的黑盒执行过程变成可视化的任务、Agent、事件和告警面板。

### 当前路线

- 本机访问优先
- node 侧旁路采集优先
- 默认监听 `127.0.0.1:12888`
- 默认界面语言为中文

### 技术栈

- 后端：Python + FastAPI + SQLite + JSONL
- 前端：React + Vite

### 一键安装

发布到 GitHub 后，可以直接提供下面这种入口。

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

安装完成后，再执行对应平台的 `start-*` 脚本。

### 快速开始

#### Windows

```powershell
.\scripts\install-windows.ps1
.\scripts\start-windows.ps1
```

#### Ubuntu

```bash
bash ./scripts/install-ubuntu.sh
bash ./scripts/start-ubuntu.sh
```

#### macOS

```bash
bash ./scripts/install-macos.sh
bash ./scripts/start-macos.sh
```

### 开发模式

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

推荐从 OpenClaw node 本机输出 JSONL 事件文件，再由 Monitor 导入。

当前接口：

- `GET /api/node-collector/status`
- `GET /api/node-collector/sample`
- `POST /api/node-collector/ingest-file`
- `POST /api/node-collector/poll`

推荐文件路径：

- `data/node-events.jsonl`

### GitHub 发布

1. 在 GitHub 创建空仓库
2. 本地执行 `git remote add origin <your-repo-url>`
3. 执行 `git push -u origin main`
4. 把 README 中的 `<owner>/<repo>` 替换成真实仓库地址

### 注意

- `docs/` 目录仅本地保留，不进入 GitHub 仓库
- 首版发布说明见 `RELEASE_NOTES_v0.1.0.md`

## English

OpenClaw Monitor is a standalone read-only observability system that turns OpenClaw’s black-box execution into a visible dashboard for tasks, agents, events, and alerts.

### Current Direction

- Local access first
- Node-side sidecar collection first
- Default listener: `127.0.0.1:12888`
- Default UI language: Chinese

### Stack

- Backend: Python + FastAPI + SQLite + JSONL
- Frontend: React + Vite

### One-Line Install

After publishing to GitHub, you can expose the following entrypoints.

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

Run the matching `start-*` script after installation.

### Quick Start

#### Windows

```powershell
.\scripts\install-windows.ps1
.\scripts\start-windows.ps1
```

#### Ubuntu

```bash
bash ./scripts/install-ubuntu.sh
bash ./scripts/start-ubuntu.sh
```

#### macOS

```bash
bash ./scripts/install-macos.sh
bash ./scripts/start-macos.sh
```

### Development

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

Recommended approach:

- output local JSONL events from the OpenClaw node
- ingest them into Monitor on the same machine

Available endpoints:

- `GET /api/node-collector/status`
- `GET /api/node-collector/sample`
- `POST /api/node-collector/ingest-file`
- `POST /api/node-collector/poll`

### GitHub Publishing

1. Create an empty GitHub repository
2. Run `git remote add origin <your-repo-url>`
3. Run `git push -u origin main`
4. Replace `<owner>/<repo>` in this README with the real repository path

### Note

- `docs/` is kept locally and should not be pushed to GitHub
- First release notes: `RELEASE_NOTES_v0.1.0.md`
