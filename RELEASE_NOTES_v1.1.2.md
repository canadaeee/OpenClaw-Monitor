# OpenClaw Monitor v1.1.2

发布日期：2026-03-18

## 新手体验改进

- 新增一键运行入口：
  - Ubuntu / macOS：`bash ./scripts/run.sh`
  - Windows：`.\scripts\run-windows.ps1`
- 安装脚本幂等：
  - macOS / Ubuntu：重复执行不会每次重建 venv
  - Windows：改为使用 `backend/.venv`，避免污染全局 Python
- 更新脚本更安全：由 `reset --hard` 改为 `pull --rebase`，并在工作区不干净时直接中止提示。
- 端口占用提示更明确：启动前检测 `12888/12889`，避免 Vite 自动换端口导致“打开地址不一致”的困惑。
- bootstrap 脚本支持自动启动：
  - `bootstrap-install.sh` 增加 `--start`
  - `bootstrap-install.ps1` 增加 `-Start`

