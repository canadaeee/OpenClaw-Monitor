# OpenClaw Monitor

OpenClaw Monitor 是一个独立的只读观测系统，用来把 OpenClaw 的黑盒执行过程变成可视化的任务、Agent、事件和告警面板。

当前 v1 路线：

- 本机访问优先
- node 侧旁路采集优先
- 默认监听 `127.0.0.1:12888`
- 默认界面语言为中文

## 技术栈

- 后端：Python + FastAPI + SQLite + JSONL
- 前端：React + Vite

## 快速开始

### Windows

```powershell
.\scripts\install-windows.ps1
.\scripts\start-windows.ps1
```

### Ubuntu

```bash
bash ./scripts/install-ubuntu.sh
bash ./scripts/start-ubuntu.sh
```

### macOS

```bash
bash ./scripts/install-macos.sh
bash ./scripts/start-macos.sh
```

## 开发模式

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

## node-side collector

推荐从 OpenClaw node 本机输出 JSONL 事件文件，再由 Monitor 导入。

相关文档见：

- `docs/node-side-collector 接入文档.md`

## GitHub 发布建议

1. 在 GitHub 创建空仓库
2. 本地执行 `git init -b main`
3. `git add .`
4. `git commit -m "Initial OpenClaw Monitor release"`
5. `git remote add origin <your-repo-url>`
6. `git push -u origin main`
