# OpenClaw Monitor v1.1.4

发布日期：2026-03-18

## 修复

- 更新提醒恢复：当后端无法访问远端仓库进行更新检查时（例如无网络/无 git/无 remote），总览页会显示“更新检查不可用”的提示与建议命令。
- 更新状态信息增强：`/api/system/update-status` 增加 `currentTag/currentDescribe` 字段，便于定位版本与 tag 不一致的问题。

