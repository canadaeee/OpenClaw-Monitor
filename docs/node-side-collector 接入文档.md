# node-side collector 接入文档 - OpenClaw Monitor

## 1. 目标

本文件说明 v1 阶段如何从 **OpenClaw node 本机** 采集事件，并导入 OpenClaw Monitor。

当前推荐路径：

- Monitor 与 OpenClaw node 运行在同一台机器
- node 侧将事件写成本机 JSONL 文件
- Monitor 通过 node-side collector 读取 JSONL 并导入标准事件

## 2. 当前可用接口

### 2.1 查看 collector 状态

`GET /api/node-collector/status`

用于查看：

- collector 是否启用
- 推荐文件路径
- 已导入数量
- 最后读取时间
- 最后错误

### 2.2 获取样例 JSONL

`GET /api/node-collector/sample`

返回：

- 推荐路径
- 可直接保存为文件的样例 JSONL 内容

### 2.3 导入本机 JSONL 文件

`POST /api/node-collector/ingest-file`

请求体：

```json
{
  "path": "D:/CodexWorkspace/OpenClaw Monitor/data/node-events.jsonl"
}
```

返回：

- 导入数量
- 文件路径
- 当前 collector 状态

## 3. 推荐文件路径

当前推荐使用：

`D:/CodexWorkspace/OpenClaw Monitor/data/node-events.jsonl`

后续如果 OpenClaw node 能稳定输出事件文件，建议默认落到这个位置，便于 Monitor 统一读取。

## 4. 推荐事件类型

建议 node 本机优先输出：

- `agent_heartbeat`
- `node_heartbeat`
- `task_started`
- `task_waiting`
- `task_completed`
- `task_failed`
- `token_usage`
- `artifact_emitted`
- `error_event`

## 5. 说明

- v1 不要求 Monitor 自身重新参与 Gateway 设备配对
- 如果 node 已与 Gateway 配对，Monitor 只作为 node 本机旁路观测器
- 当前最稳的实现方式是“本机生成 JSONL -> 本机导入 Monitor”
