import { useEffect, useRef, useState } from 'react'

const initialOverview = {
  generatedAt: null,
  dataLatencySeconds: null,
  agentOnlineCount: 0,
  agentOfflineCount: 0,
  nodeOnlineCount: 0,
  nodeOfflineCount: 0,
  taskRunningCount: 0,
  taskWaitingCount: 0,
  taskFailedCount: 0,
  taskTimeoutCount: 0,
  openAlertCount: 0,
  todayTokenTotal: 0,
  todayEstimatedCost: null,
  todayErrorCount: 0,
}

const themeModes = [
  { value: 'system', label: '跟随系统' },
  { value: 'light', label: '浅色' },
  { value: 'dark', label: '深色' },
]

const navItems = [
  { id: 'overview', label: '总览' },
  { id: 'agents', label: 'Agent' },
  { id: 'tasks', label: '任务' },
  { id: 'token', label: 'Token / 成本' },
  { id: 'events', label: '事件流' },
  { id: 'alerts', label: '告警' },
]

const pageMeta = {
  overview: {
    title: '系统总览',
    description: '将 OpenClaw 的任务链路、节点状态、Token 消耗和异常告警集中可视化。',
  },
  agents: {
    title: 'Agent 观察',
    description: '查看执行单元的连接状态、运行状态与今日消耗情况。',
  },
  tasks: {
    title: '任务列表',
    description: '围绕任务生命周期、执行节点、耗时与 Token 使用量进行追踪。',
  },
  token: {
    title: 'Token / 成本',
    description: '从任务与 Agent 两个维度观察消耗趋势与成本分布。',
  },
  events: {
    title: '事件流',
    description: '查看标准化事件时间线，定位状态变化与异常触发顺序。',
  },
  alerts: {
    title: '告警中心',
    description: '集中处理离线、失败和异常消耗等故障导向提醒。',
  },
}

const initialGatewayDraft = {
  enabled: 'true',
  mode: 'local-first',
  defaultPort: '18789',
  discoveryPorts: '18789',
  baseUrl: '',
  origin: '',
  remoteUrl: '',
  sessionKey: 'agent:main:main',
  probeIntervalSeconds: '15',
  token: '',
  password: '',
}

export default function App() {
  const [overview, setOverview] = useState(initialOverview)
  const [agents, setAgents] = useState([])
  const [tasks, setTasks] = useState([])
  const [alerts, setAlerts] = useState([])
  const [events, setEvents] = useState([])
  const [status, setStatus] = useState('loading')
  const [activePage, setActivePage] = useState('overview')
  const [themeMode, setThemeMode] = useState(() => {
    if (typeof window === 'undefined') {
      return 'system'
    }
    return window.localStorage.getItem('openclaw-monitor-theme') ?? 'system'
  })
  const [gatewayStatus, setGatewayStatus] = useState(null)
  const [gatewayDraft, setGatewayDraft] = useState(initialGatewayDraft)
  const [gatewayMessage, setGatewayMessage] = useState('')
  const [gatewayOpen, setGatewayOpen] = useState(false)
  const [nodeCollectorStatus, setNodeCollectorStatus] = useState(null)
  const [updateStatus, setUpdateStatus] = useState(null)
  const refreshRef = useRef(false)

  useEffect(() => {
    void loadAll()
    const interval = window.setInterval(() => {
      void loadAll()
    }, 3000)
    return () => window.clearInterval(interval)
  }, [])

  useEffect(() => {
    if (typeof document === 'undefined') {
      return
    }

    document.documentElement.dataset.theme = themeMode
    document.documentElement.lang = 'zh-CN'
    window.localStorage.setItem('openclaw-monitor-theme', themeMode)
  }, [themeMode])

  async function loadAll() {
    if (refreshRef.current) {
      return
    }
    refreshRef.current = true
    try {
      const [
        overviewJson,
        agentsJson,
        tasksJson,
        alertsJson,
        eventsJson,
        gatewayStatusJson,
        gatewayConfigJson,
        nodeCollectorJson,
        updateStatusJson,
      ] = await Promise.all([
        fetchJson('/api/overview'),
        fetchJson('/api/agents'),
        fetchJson('/api/tasks'),
        fetchJson('/api/alerts'),
        fetchJson('/api/events?limit=200'),
        fetchJson('/api/gateway/status'),
        fetchJson('/api/gateway/config'),
        fetchJson('/api/node-collector/status'),
        fetchJson('/api/system/update-status'),
      ])

      setOverview(overviewJson)
      setAgents(agentsJson.items ?? [])
      setTasks(tasksJson.items ?? [])
      setAlerts(alertsJson.items ?? [])
      setEvents(eventsJson.items ?? [])
      setGatewayStatus(gatewayStatusJson)
      setGatewayDraft(toGatewayDraft(gatewayConfigJson))
      setNodeCollectorStatus(nodeCollectorJson)
      setUpdateStatus(updateStatusJson)
      setStatus('ready')
    } catch {
      setStatus('error')
    } finally {
      refreshRef.current = false
    }
  }

  const gatewayLabel = getGatewayLabel()

  return (
    <div className="layout">
      <aside className="sidebar">
        <div className="logo-area">
          <div className="logo-copy">
            <strong>OpenClaw Monitor</strong>
            <span>Openclaw可视化监控台</span>
          </div>
        </div>

        <nav className="nav-menu" aria-label="主导航">
          {navItems.map((item) => (
            <button
              key={item.id}
              type="button"
              className={activePage === item.id ? 'nav-link active' : 'nav-link'}
              onClick={() => setActivePage(item.id)}
            >
              <span>{item.label}</span>
            </button>
          ))}
        </nav>

        <div className="sidebar-footer">
          <div className="user-profile">
            <div className="user-info">
              <strong>{gatewayLabel}</strong>
              <span>默认语言：中文</span>
            </div>
          </div>

          <div className="switch-group">
            <p className="switch-title">主题模式</p>
            <div className="theme-switcher">
              {themeModes.map((mode) => (
                <button
                  key={mode.value}
                  type="button"
                  className={themeMode === mode.value ? 'switch-opt active' : 'switch-opt'}
                  onClick={() => setThemeMode(mode.value)}
                >
                  {mode.label}
                </button>
              ))}
            </div>
          </div>

          <div className="switch-group">
            <p className="switch-title">系统语言</p>
            <div className="lang-switcher">
              <button type="button" className="switch-opt active">
                中文
              </button>
              <button type="button" className="switch-opt" disabled>
                English
              </button>
            </div>
          </div>
        </div>
      </aside>

      <main className="main-content">
        <PageHeader
          activePage={activePage}
          status={status}
          snapshot={overview.generatedAt}
          gatewayStatus={gatewayStatus}
          onOpenGateway={() => setGatewayOpen(true)}
        />

        {activePage === 'overview' && (
          <OverviewPage
            overview={overview}
            tasks={tasks}
            agents={agents}
            alerts={alerts}
            events={events}
            gatewayStatus={gatewayStatus}
            gatewayLabel={gatewayLabel}
            nodeCollectorStatus={nodeCollectorStatus}
            updateStatus={updateStatus}
          />
        )}
        {activePage === 'agents' && <AgentsPage agents={agents} overview={overview} />}
        {activePage === 'tasks' && <TasksPage tasks={tasks} />}
        {activePage === 'token' && <TokenPage overview={overview} tasks={tasks} agents={agents} />}
        {activePage === 'events' && <EventsPage events={events} />}
        {activePage === 'alerts' && <AlertsPage alerts={alerts} overview={overview} />}

        {gatewayOpen && (
          <GatewayModal
            draft={gatewayDraft}
            message={gatewayMessage}
            onClose={() => {
              setGatewayOpen(false)
              setGatewayMessage('')
            }}
            onChange={(patch) => setGatewayDraft((current) => ({ ...current, ...patch }))}
            onSave={async () => {
              try {
                const response = await fetch('/api/gateway/config', {
                  method: 'PUT',
                  headers: { 'Content-Type': 'application/json' },
                  body: JSON.stringify(fromGatewayDraft(gatewayDraft)),
                })
                if (!response.ok) {
                  throw new Error('save failed')
                }
                const payload = await response.json()
                setGatewayDraft(toGatewayDraft(payload.config))
                setGatewayStatus(await fetchJson('/api/gateway/status'))
                setGatewayMessage('Gateway 配置已保存，后端已重新加载探测配置。')
              } catch {
                setGatewayMessage('Gateway 配置保存失败，请检查输入后重试。')
              }
            }}
          />
        )}
      </main>
    </div>
  )
}

function PageHeader({ activePage, status, snapshot, gatewayStatus, onOpenGateway }) {
  const page = pageMeta[activePage]
  const runtime = gatewayStatus?.runtime ?? {}
  const detected = Boolean(runtime.detected)
  const wsConnected = Boolean(gatewayStatus?.stream?.runtime?.connected)

  return (
    <header className="header">
      <div className="page-title">
        <h1>{page.title}</h1>
        <p>{page.description}</p>
      </div>
      <div className="header-actions">
        <div className="status-badge">
          <span className={`status-dot ${status}`} />
          <span>{statusText(status)}</span>
        </div>
        <div className={detected ? 'status-badge gateway-ok' : 'status-badge gateway-warn'}>
          <span className={`status-dot ${detected ? 'ready' : ''}`} />
          <span>{detected ? '已发现 Gateway' : '未发现 Gateway'}</span>
        </div>
        <div className={wsConnected ? 'status-badge gateway-ok' : 'status-badge gateway-warn'}>
          <span className={`status-dot ${wsConnected ? 'ready' : ''}`} />
          <span>{wsConnected ? 'Gateway WS 已连接' : 'Gateway WS 未连接'}</span>
        </div>
        <button type="button" className="btn btn-outline" onClick={onOpenGateway}>
          Gateway 设置
        </button>
        <button type="button" className="btn btn-outline">
          默认端口 12888
        </button>
        <button type="button" className="btn btn-primary">
          快照 {snapshot ? formatTime(snapshot) : '--'}
        </button>
      </div>
    </header>
  )
}

function OverviewPage({
  overview,
  tasks,
  agents,
  alerts,
  events,
  gatewayStatus,
  gatewayLabel,
  nodeCollectorStatus,
  updateStatus,
}) {
  const gatewayAgents = gatewayStatus?.stream?.runtime?.lastHealthSummary?.agents ?? []
  const statCards = [
    {
      label: '在线 Agent',
      value: formatValue(overview.agentOnlineCount),
      change: `${formatValue(overview.agentOfflineCount)} 个离线`,
      tone: overview.agentOfflineCount > 0 ? 'danger' : 'success',
    },
    {
      label: '在线节点',
      value: formatValue(overview.nodeOnlineCount),
      change: `${formatValue(overview.nodeOfflineCount)} 个离线`,
      tone: overview.nodeOfflineCount > 0 ? 'danger' : 'success',
    },
    {
      label: '运行中任务',
      value: formatValue(overview.taskRunningCount),
      change: `${formatValue(overview.taskWaitingCount)} 个等待中`,
      tone: overview.taskWaitingCount > 0 ? 'warning' : 'success',
    },
    {
      label: '今日 Token',
      value: formatValue(overview.todayTokenTotal),
      change: formatCurrency(overview.todayEstimatedCost),
      tone: 'neutral',
    },
  ]

  return (
    <>
      {updateStatus?.updateAvailable && (
        <section className="update-banner">
          <div>
            <strong>检测到新版本可更新</strong>
            <p>
              当前版本 {updateStatus.currentVersion}，远端主分支已有新提交。建议使用
              <code>{updateStatus.updateCommand}</code>
              完成更新。
            </p>
          </div>
          <span className="update-badge">需要手动更新</span>
        </section>
      )}

      <section className="hero-banner">
        <div>
          <p className="banner-tag">{gatewayLabel} / 本机优先 / 只读观测</p>
          <h2>让任务流转、Agent 活跃度和故障现场都能被看见</h2>
          <p className="banner-text">
            不介入调度，只做黑盒可视化。通过统一事件、状态推导和告警视图，把 OpenClaw
            的运行过程变成可追踪、可定位、可回放的观测界面。
          </p>
        </div>
        <div className="banner-meta">
          <div className="meta-item">
            <span>数据延迟</span>
            <strong>{formatLatency(overview.dataLatencySeconds)}</strong>
          </div>
          <div className="meta-item">
            <span>活跃告警</span>
            <strong>{formatValue(overview.openAlertCount)}</strong>
          </div>
          <div className="meta-item">
            <span>失败任务</span>
            <strong>{formatValue(overview.taskFailedCount)}</strong>
          </div>
        </div>
      </section>

      <section className="grid-dashboard">
        {statCards.map((card) => (
          <article className="stat-card" key={card.label}>
            <div className="stat-header">
              <div className="stat-value">{card.value}</div>
              <div className="stat-label">{card.label}</div>
            </div>
            <div className={`stat-change ${card.tone}`}>
              <span className="change-dot" />
              <span>{card.change}</span>
            </div>
          </article>
        ))}
      </section>

      <section className="collector-strip">
        <article className="panel collector-panel">
          <div className="panel-head">
            <div>
              <h2>Gateway Realtime</h2>
              <p>来自 OpenClaw Gateway WebSocket 的实时健康与连接状态。</p>
            </div>
            <span className="panel-note">
              {gatewayStatus?.stream?.runtime?.connected ? '实时连接中' : '未连接'}
            </span>
          </div>
          <div className="collector-grid">
            <div className="summary-card">
              <span>连接状态</span>
              <strong>{gatewayStatus?.stream?.runtime?.connected ? 'Connected' : 'Disconnected'}</strong>
              <p>{gatewayStatus?.stream?.runtime?.lastError || '当前未报告错误'}</p>
            </div>
            <div className="summary-card">
              <span>健康状态</span>
              <strong>
                {gatewayStatus?.stream?.runtime?.lastHealthSummary?.ok === true
                  ? 'OK'
                  : gatewayStatus?.stream?.runtime?.lastHealthSummary?.ok === false
                    ? 'Degraded'
                    : '--'}
              </strong>
              <p>最近健康包：{formatDateTime(gatewayStatus?.stream?.runtime?.lastHealthAt)}</p>
            </div>
            <div className="summary-card">
              <span>Agent / Session</span>
              <strong>
                {formatValue(gatewayStatus?.stream?.runtime?.lastHealthSummary?.agentCount)} /{' '}
                {formatValue(gatewayStatus?.stream?.runtime?.lastHealthSummary?.sessionCount)}
              </strong>
              <p>channels：{formatValue(gatewayStatus?.stream?.runtime?.lastHealthSummary?.channelCount)}</p>
            </div>
            <div className="summary-card">
              <span>心跳间隔</span>
              <strong>{formatValue(gatewayStatus?.stream?.runtime?.lastHealthSummary?.heartbeatSeconds)} 秒</strong>
              <p>duration：{formatValue(gatewayStatus?.stream?.runtime?.lastHealthSummary?.durationMs)} ms</p>
            </div>
          </div>
          <div className="table-list">
            {gatewayAgents.map((agent) => (
              <div className="table-row" key={agent.agentId}>
                <div className="table-main">
                  <strong>{agent.agentId}</strong>
                  <span>
                    sessions {formatValue(agent.sessionsCount)} / last {formatEpoch(agent.lastSessionUpdatedAt || agent.heartbeatTs)}
                  </span>
                </div>
                <div className="table-meta">
                  <span className={`badge ${agent.isDefault ? 'online' : 'unknown'}`}>
                    {agent.isDefault ? '默认' : 'Agent'}
                  </span>
                </div>
              </div>
            ))}
            {gatewayAgents.length === 0 && <EmptyState text="暂未收到 Gateway health agents 列表。" />}
          </div>
        </article>

        <article className="panel collector-panel">
          <div className="panel-head">
            <div>
              <h2>Node Collector</h2>
              <p>本机 node-side collector 运行状态与最近采集结果。</p>
            </div>
            <span className="panel-note">
              {nodeCollectorStatus?.autoPolling ? '自动轮询中' : '未启用轮询'}
            </span>
          </div>
          <div className="collector-grid">
            <div className="summary-card">
              <span>采集模式</span>
              <strong>{nodeCollectorStatus?.mode ?? '--'}</strong>
              <p>{nodeCollectorStatus?.sourceType ?? 'jsonl'}</p>
            </div>
            <div className="summary-card">
              <span>累计导入</span>
              <strong>{formatValue(nodeCollectorStatus?.ingestedCount)}</strong>
              <p>最近一次导入：{formatDateTime(nodeCollectorStatus?.lastIngestAt)}</p>
            </div>
            <div className="summary-card">
              <span>轮询间隔</span>
              <strong>{formatValue(nodeCollectorStatus?.pollIntervalSeconds)} 秒</strong>
              <p>文件偏移：{formatValue(nodeCollectorStatus?.lastFileOffset)}</p>
            </div>
            <div className="summary-card">
              <span>数据源</span>
              <strong>{shortPath(nodeCollectorStatus?.sourcePath || nodeCollectorStatus?.recommendedPath)}</strong>
              <p>{nodeCollectorStatus?.lastError || '当前未报告错误'}</p>
            </div>
          </div>
        </article>
      </section>

      <section className="content-columns">
        <section className="panel wide">
          <div className="panel-head">
            <div>
              <h2>任务追踪</h2>
              <p>当前活跃任务与链路摘要</p>
            </div>
            <span className="panel-note">{tasks.length} 个任务</span>
          </div>
          <div className="table-list">
            {tasks.map((task) => (
              <div className="table-row" key={task.id}>
                <div className="table-main">
                  <strong>{task.id}</strong>
                  <span>
                    {task.taskType || '未命名任务'} / {task.executorNodeId || '未知节点'}
                  </span>
                </div>
                <div className="table-meta">
                  <span>{formatValue(task.tokenUsage?.total)} Token</span>
                  <span>{formatDuration(task.durationMs)}</span>
                  <span className={`badge ${task.status}`}>{statusLabel(task.status)}</span>
                </div>
              </div>
            ))}
            {tasks.length === 0 && <EmptyState text="当前还没有任务数据。" />}
          </div>
        </section>

        <section className="panel">
          <div className="panel-head">
            <div>
              <h2>Agent 状态</h2>
              <p>连接状态与运行状态</p>
            </div>
            <span className="panel-note">{agents.length} 个可见</span>
          </div>
          <div className="stack-list">
            {agents.map((agent) => (
              <div className="stack-item" key={agent.id}>
                <div>
                  <strong>{agent.name || agent.id}</strong>
                  <p>{agent.derivedStatusReason || '暂无状态说明'}</p>
                </div>
                <div className="stack-tags">
                  <span className={`badge ${agent.connectivityStatus}`}>
                    {connectivityLabel(agent.connectivityStatus)}
                  </span>
                  <span className="badge subtle">{statusLabel(agent.runtimeStatus)}</span>
                </div>
              </div>
            ))}
            {agents.length === 0 && <EmptyState text="当前还没有 Agent 数据。" />}
          </div>
        </section>
      </section>

      <section className="content-columns lower">
        <section className="panel">
          <div className="panel-head">
            <div>
              <h2>活跃告警</h2>
              <p>故障导向的重点提醒</p>
            </div>
            <span className="panel-note">{alerts.length} 条</span>
          </div>
          <div className="stack-list">
            {alerts.map((alert) => (
              <div className="stack-item" key={alert.id}>
                <div>
                  <strong>{alert.title}</strong>
                  <p>{alert.description}</p>
                </div>
                <div className="stack-tags">
                  <span className={`badge ${alert.severity}`}>{severityLabel(alert.severity)}</span>
                  <span className="time-text">{formatDateTime(alert.triggeredAt)}</span>
                </div>
              </div>
            ))}
            {alerts.length === 0 && <EmptyState text="当前没有活跃告警。" />}
          </div>
        </section>

        <section className="panel">
          <div className="panel-head">
            <div>
              <h2>健康摘要</h2>
              <p>节点、任务与成本当前态势</p>
            </div>
            <span className="panel-note">{events.length} 条事件</span>
          </div>
          <div className="summary-grid">
            <div className="summary-card">
              <span>在线率</span>
              <strong>{calcRatio(overview.agentOnlineCount, overview.agentOfflineCount)}</strong>
              <p>Agent 存活情况</p>
            </div>
            <div className="summary-card">
              <span>等待压力</span>
              <strong>{formatValue(overview.taskWaitingCount)}</strong>
              <p>等待资源的任务数</p>
            </div>
            <div className="summary-card">
              <span>今日成本</span>
              <strong>{formatCurrency(overview.todayEstimatedCost)}</strong>
              <p>Token 消耗折算</p>
            </div>
            <div className="summary-card">
              <span>异常数</span>
              <strong>{formatValue(overview.todayErrorCount)}</strong>
              <p>今日错误事件</p>
            </div>
          </div>
        </section>
      </section>
    </>
  )
}

function formatEpoch(value) {
  if (value === null || value === undefined || value === '') {
    return '--'
  }
  const raw = typeof value === 'number' ? value : Number(value)
  if (!Number.isFinite(raw)) {
    return '--'
  }
  const ms = raw > 1e12 ? raw : raw * 1000
  const date = new Date(ms)
  if (Number.isNaN(date.getTime())) {
    return '--'
  }
  return date.toLocaleString()
}

function AgentsPage({ agents, overview }) {
  return (
    <>
      <section className="grid-dashboard">
        <StatCard label="Agent 总数" value={agents.length} note={`${formatValue(overview.agentOnlineCount)} 个在线`} tone="neutral" />
        <StatCard label="离线 Agent" value={overview.agentOfflineCount} note="需要优先排查" tone="danger" />
        <StatCard
          label="运行中"
          value={agents.filter((item) => item.runtimeStatus === 'running').length}
          note="执行链路活跃"
          tone="success"
        />
        <StatCard
          label="今日 Agent Token"
          value={agents.reduce((sum, item) => sum + (item.todayTokenTotal || 0), 0)}
          note="按 Agent 聚合"
          tone="neutral"
        />
      </section>

      <section className="panel">
        <div className="panel-head">
          <div>
            <h2>Agent 观察列表</h2>
            <p>用于定位谁在线、谁正在执行、谁需要恢复。</p>
          </div>
          <span className="panel-note">{agents.length} 个 Agent</span>
        </div>
        <div className="stack-list">
          {agents.map((agent) => (
            <div className="stack-item" key={agent.id}>
              <div>
                <strong>{agent.name || agent.id}</strong>
                <p>{agent.derivedStatusReason || '暂无状态说明'}</p>
              </div>
              <div className="stack-tags">
                <span className={`badge ${agent.connectivityStatus}`}>
                  {connectivityLabel(agent.connectivityStatus)}
                </span>
                <span className="badge subtle">{statusLabel(agent.runtimeStatus)}</span>
                <span className="time-text">{formatValue(agent.todayTokenTotal)} Token</span>
              </div>
            </div>
          ))}
          {agents.length === 0 && <EmptyState text="当前还没有 Agent 数据。" />}
        </div>
      </section>
    </>
  )
}

function TasksPage({ tasks }) {
  return (
    <section className="panel">
      <div className="panel-head">
        <div>
          <h2>任务列表</h2>
          <p>聚焦任务生命周期、耗时、Token 与执行节点。</p>
        </div>
        <span className="panel-note">{tasks.length} 个任务</span>
      </div>
      <div className="table-list">
        {tasks.map((task) => (
          <div className="table-row table-row-block" key={task.id}>
            <div className="table-main">
              <strong>{task.id}</strong>
              <span>
                {task.taskType || '未命名任务'} / 来源 {task.sourceAgentId || '--'} / 执行{' '}
                {task.executorAgentId || '--'}
              </span>
            </div>
            <div className="table-grid">
              <MiniStat label="状态" value={statusLabel(task.status)} />
              <MiniStat label="耗时" value={formatDuration(task.durationMs)} />
              <MiniStat label="Token" value={formatValue(task.tokenUsage?.total)} />
              <MiniStat label="节点" value={task.executorNodeId || '--'} />
            </div>
          </div>
        ))}
        {tasks.length === 0 && <EmptyState text="当前还没有任务数据。" />}
      </div>
    </section>
  )
}

function TokenPage({ overview, tasks, agents }) {
  const topAgents = [...agents].sort((a, b) => (b.todayTokenTotal || 0) - (a.todayTokenTotal || 0))
  const costUnavailable = (overview.todayTokenTotal || 0) > 0 && (overview.todayEstimatedCost || 0) === 0

  return (
    <>
      {costUnavailable && (
        <section className="update-banner">
          <div>
            <strong>金额消耗暂无法估算</strong>
            <p>
              当前 OpenClaw 本机数据只包含 Token 计数，未包含模型单价 / provider 账单信息。若需要金额估算，请在
              <code>config/pricing.json</code> 配置 per-1M token 单价（参考 <code>config/pricing.example.json</code>）。
            </p>
          </div>
          <span className="update-badge">需要价格表</span>
        </section>
      )}
      <section className="grid-dashboard">
        <StatCard label="今日总 Token" value={overview.todayTokenTotal} note={formatCurrency(overview.todayEstimatedCost)} tone="neutral" />
        <StatCard
          label="输入 Token"
          value={tasks.reduce((sum, task) => sum + (task.tokenUsage?.input || 0), 0)}
          note="请求侧消耗"
          tone="success"
        />
        <StatCard
          label="输出 Token"
          value={tasks.reduce((sum, task) => sum + (task.tokenUsage?.output || 0), 0)}
          note="响应侧消耗"
          tone="warning"
        />
        <StatCard label="预估成本" value={formatCurrency(overview.todayEstimatedCost)} note="美元折算" tone="neutral" />
      </section>

      <section className="content-columns lower">
        <section className="panel">
          <div className="panel-head">
            <div>
              <h2>按任务查看</h2>
              <p>识别哪些任务产生了主要消耗。</p>
            </div>
          </div>
          <div className="stack-list">
            {tasks.map((task) => (
              <div className="stack-item" key={task.id}>
                <div>
                  <strong>{task.id}</strong>
                  <p>{task.taskType || '未命名任务'}</p>
                </div>
                <div className="stack-tags">
                  <span className="time-text">{formatValue(task.tokenUsage?.input)} 输入</span>
                  <span className="time-text">{formatValue(task.tokenUsage?.output)} 输出</span>
                  <span className="badge subtle">{formatValue(task.tokenUsage?.total)} 总计</span>
                </div>
              </div>
            ))}
            {tasks.length === 0 && <EmptyState text="当前还没有 Token 数据。" />}
          </div>
        </section>

        <section className="panel">
          <div className="panel-head">
            <div>
              <h2>按 Agent 查看</h2>
              <p>快速识别高消耗执行单元。</p>
            </div>
          </div>
          <div className="stack-list">
            {topAgents.map((agent) => (
              <div className="stack-item" key={agent.id}>
                <div>
                  <strong>{agent.name || agent.id}</strong>
                  <p>{statusLabel(agent.runtimeStatus)}</p>
                </div>
                <div className="stack-tags">
                  <span className="badge subtle">{formatValue(agent.todayTokenTotal)} Token</span>
                </div>
              </div>
            ))}
            {topAgents.length === 0 && <EmptyState text="当前还没有 Agent Token 排名。" />}
          </div>
        </section>
      </section>
    </>
  )
}

function EventsPage({ events }) {
  return (
    <section className="panel">
      <div className="panel-head">
        <div>
          <h2>事件时间线</h2>
          <p>展示任务、Agent、告警等关键事件的标准化记录。</p>
        </div>
        <span className="panel-note">{events.length} 条事件</span>
      </div>
      <div className="timeline">
        {events.map((event) => (
          <div className="timeline-item" key={event.id || `${event.type}-${event.occurredAt}`}>
            <div className="timeline-dot" />
            <div className="timeline-body">
              <div className="timeline-top">
                <strong>{event.title || event.type}</strong>
                <span className="time-text">{formatDateTime(event.occurredAt)}</span>
              </div>
              <p>{event.detail || '暂无详细描述。'}</p>
              <span className="badge subtle">{event.type}</span>
            </div>
          </div>
        ))}
        {events.length === 0 && <EmptyState text="当前还没有事件数据。" />}
      </div>
    </section>
  )
}

function AlertsPage({ alerts, overview }) {
  return (
    <>
      <section className="grid-dashboard">
        <StatCard label="当前告警" value={alerts.length} note="待处理项" tone="danger" />
        <StatCard label="失败任务相关" value={overview.taskFailedCount} note="需结合任务视图排查" tone="warning" />
        <StatCard label="离线相关" value={overview.agentOfflineCount} note="检查 Agent 连通性" tone="danger" />
        <StatCard label="今日错误事件" value={overview.todayErrorCount} note="排障证据基础" tone="neutral" />
      </section>

      <section className="panel">
        <div className="panel-head">
          <div>
            <h2>告警列表</h2>
            <p>集中查看当前打开的故障项与触发时间。</p>
          </div>
          <span className="panel-note">{alerts.length} 条告警</span>
        </div>
        <div className="stack-list">
          {alerts.map((alert) => (
            <div className="stack-item" key={alert.id}>
              <div>
                <strong>{alert.title}</strong>
                <p>{alert.description}</p>
              </div>
              <div className="stack-tags">
                <span className={`badge ${alert.severity}`}>{severityLabel(alert.severity)}</span>
                <span className="time-text">{formatDateTime(alert.triggeredAt)}</span>
              </div>
            </div>
          ))}
          {alerts.length === 0 && <EmptyState text="当前没有告警。" />}
        </div>
      </section>
    </>
  )
}

function GatewayModal({ draft, message, onClose, onChange, onSave }) {
  return (
    <div className="modal-backdrop" onClick={onClose}>
      <section className="modal-card" onClick={(event) => event.stopPropagation()}>
        <div className="panel-head">
          <div>
            <h2>Gateway 设置</h2>
            <p>默认优先探测本机 18789，也支持自定义端口、Origin、认证信息和远程候选地址。</p>
          </div>
          <button type="button" className="btn btn-outline" onClick={onClose}>
            关闭
          </button>
        </div>

        <div className="form-grid">
          <FieldSelect
            label="启用自动捕捉"
            value={draft.enabled}
            onChange={(value) => onChange({ enabled: value })}
            options={[
              { value: 'true', label: '启用' },
              { value: 'false', label: '禁用' },
            ]}
          />
          <FieldSelect
            label="自动探测模式"
            value={draft.mode}
            onChange={(value) => onChange({ mode: value })}
            options={[
              { value: 'local-first', label: '本机优先' },
              { value: 'manual', label: '手动指定' },
            ]}
          />
          <FieldInput label="默认端口" value={draft.defaultPort} onChange={(value) => onChange({ defaultPort: value })} />
          <FieldInput label="探测端口列表" value={draft.discoveryPorts} onChange={(value) => onChange({ discoveryPorts: value })} />
          <FieldInput
            label="手动指定地址"
            value={draft.baseUrl}
            onChange={(value) => onChange({ baseUrl: value })}
            placeholder="例如 http://127.0.0.1:18789"
            wide
          />
          <FieldInput
            label="Origin 覆盖（可选）"
            value={draft.origin}
            onChange={(value) => onChange({ origin: value })}
            placeholder="留空则自动使用 Gateway 地址"
            wide
          />
          <FieldInput
            label="远程候选地址"
            value={draft.remoteUrl}
            onChange={(value) => onChange({ remoteUrl: value })}
            placeholder="例如 https://example.tailnet.ts.net"
            wide
          />
          <FieldInput label="会话键" value={draft.sessionKey} onChange={(value) => onChange({ sessionKey: value })} />
          <FieldInput
            label="探测间隔（秒）"
            value={draft.probeIntervalSeconds}
            onChange={(value) => onChange({ probeIntervalSeconds: value })}
          />
          <FieldInput
            label="Gateway Token"
            value={draft.token}
            onChange={(value) => onChange({ token: value })}
            placeholder="可选"
          />
          <FieldInput
            label="Password"
            type="password"
            value={draft.password}
            onChange={(value) => onChange({ password: value })}
            placeholder="可选"
          />
        </div>

        <div className="modal-footer">
          <span className="form-message">{message || '保存后后端会立即重新加载 Gateway 探测配置。'}</span>
          <button type="button" className="btn btn-primary" onClick={onSave}>
            保存配置
          </button>
        </div>
      </section>
    </div>
  )
}

function StatCard({ label, value, note, tone }) {
  return (
    <article className="stat-card">
      <div className="stat-header">
        <div className="stat-value">{typeof value === 'string' ? value : formatValue(value)}</div>
        <div className="stat-label">{label}</div>
      </div>
      <div className={`stat-change ${tone}`}>
        <span className="change-dot" />
        <span>{note}</span>
      </div>
    </article>
  )
}

function MiniStat({ label, value }) {
  return (
    <div className="mini-stat">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  )
}

function FieldInput({ label, value, onChange, placeholder, type = 'text', wide = false }) {
  return (
    <label className={wide ? 'form-field form-field-wide' : 'form-field'}>
      <span>{label}</span>
      <input type={type} value={value} onChange={(event) => onChange(event.target.value)} placeholder={placeholder} />
    </label>
  )
}

function FieldSelect({ label, value, onChange, options }) {
  return (
    <label className="form-field">
      <span>{label}</span>
      <select value={value} onChange={(event) => onChange(event.target.value)}>
        {options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
    </label>
  )
}

function EmptyState({ text }) {
  return <div className="empty-state">{text}</div>
}

async function fetchJson(url) {
  const response = await fetch(url)
  if (!response.ok) {
    throw new Error(`Request failed: ${url}`)
  }
  return response.json()
}

function formatValue(value) {
  if (value === null || value === undefined || value === '') {
    return '--'
  }
  if (typeof value === 'number') {
    return value.toLocaleString('zh-CN')
  }
  return String(value)
}

function formatCurrency(value) {
  if (value === null || value === undefined) {
    return '--'
  }
  return new Intl.NumberFormat('zh-CN', {
    style: 'currency',
    currency: 'USD',
    maximumFractionDigits: 2,
  }).format(value)
}

function formatDateTime(value) {
  if (!value) {
    return '--'
  }
  return new Date(value).toLocaleString('zh-CN')
}

function formatTime(value) {
  if (!value) {
    return '--'
  }
  return new Date(value).toLocaleTimeString('zh-CN', {
    hour: '2-digit',
    minute: '2-digit',
  })
}

function formatLatency(value) {
  if (value === null || value === undefined) {
    return '--'
  }
  return `${Math.round(value * 1000)} ms`
}

function formatDuration(value) {
  if (value === null || value === undefined) {
    return '--'
  }
  const minutes = Math.floor(value / 60000)
  const seconds = Math.floor((value % 60000) / 1000)
  return `${minutes} 分 ${seconds} 秒`
}

function statusText(status) {
  if (status === 'ready') {
    return '数据已连接'
  }
  if (status === 'error') {
    return '连接失败'
  }
  return '数据加载中'
}

function statusLabel(status) {
  switch (status) {
    case 'running':
      return '运行中'
    case 'waiting':
      return '等待中'
    case 'completed':
    case 'done':
      return '已完成'
    case 'failed':
    case 'error':
      return '失败'
    case 'queued':
      return '排队中'
    case 'idle':
      return '空闲'
    case 'offline':
      return '离线'
    case 'online':
      return '在线'
    case 'unknown':
      return '未知'
    default:
      return status || '--'
  }
}

function connectivityLabel(status) {
  if (status === 'online') {
    return '在线'
  }
  if (status === 'offline') {
    return '离线'
  }
  return '未知'
}

function severityLabel(severity) {
  if (severity === 'critical') {
    return '严重'
  }
  if (severity === 'warning') {
    return '警告'
  }
  if (severity === 'info') {
    return '信息'
  }
  return severity || '--'
}

function calcRatio(online, offline) {
  const total = Number(online || 0) + Number(offline || 0)
  if (!total) {
    return '--'
  }
  return `${Math.round((online / total) * 100)}%`
}

function shortPath(path) {
  if (!path) {
    return '--'
  }
  const normalized = String(path).replaceAll('\\', '/')
  const segments = normalized.split('/')
  if (segments.length <= 3) {
    return normalized
  }
  return segments.slice(-3).join('/')
}

function getGatewayLabel() {
  if (typeof navigator === 'undefined') {
    return 'Gateway'
  }
  const source = `${navigator.userAgent || ''} ${navigator.platform || ''}`.toLowerCase()
  if (source.includes('mac')) {
    return 'Mac Gateway'
  }
  if (source.includes('win')) {
    return 'Windows Gateway'
  }
  if (source.includes('linux') || source.includes('ubuntu') || source.includes('x11')) {
    return 'Ubuntu Gateway'
  }
  return 'Gateway'
}

function toGatewayDraft(config) {
  const remoteCandidate = (config.discovery_candidates || []).find((item) => item.name === 'remote-tailnet')
  return {
    enabled: config.enabled ? 'true' : 'false',
    mode: config.mode || 'local-first',
    defaultPort: String(config.default_port ?? 18789),
    discoveryPorts: Array.isArray(config.discovery_ports) ? config.discovery_ports.join(',') : '18789',
    baseUrl: config.base_url || '',
    origin: config.origin || '',
    remoteUrl: remoteCandidate?.base_url || '',
    sessionKey: config.session_key || 'agent:main:main',
    probeIntervalSeconds: String(config.probe_interval_seconds ?? 15),
    token: '',
    password: '',
  }
}

function fromGatewayDraft(draft) {
  const ports = String(draft.discoveryPorts || '')
    .split(',')
    .map((item) => Number(item.trim()))
    .filter((item) => Number.isInteger(item) && item > 0)

  const remoteCandidates = draft.remoteUrl
    ? [
        {
          name: 'remote-tailnet',
          base_url: draft.remoteUrl.trim(),
          ws_url: '',
          origin: '',
          session_key: draft.sessionKey.trim() || 'agent:main:main',
          token: '',
          password: '',
          priority: 100,
        },
      ]
    : []

  return {
    enabled: draft.enabled === 'true',
    auto_capture: true,
    probe_interval_seconds: Number(draft.probeIntervalSeconds) || 15,
    mode: draft.mode,
    default_port: Number(draft.defaultPort) || 18789,
    discovery_ports: ports.length > 0 ? ports : [18789],
    base_url: draft.baseUrl.trim(),
    ws_url: '',
    origin: draft.origin.trim(),
    session_key: draft.sessionKey.trim() || 'agent:main:main',
    token: draft.token.trim(),
    password: draft.password.trim(),
    language: 'zh-CN',
    discovery_candidates: remoteCandidates,
  }
}
