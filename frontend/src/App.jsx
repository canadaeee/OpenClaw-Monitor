import { useEffect, useState } from 'react'

const initialState = {
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
    description: '查看执行单元的在线状态、运行状态与今日消耗情况。',
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

export default function App() {
  const [overview, setOverview] = useState(initialState)
  const [agents, setAgents] = useState([])
  const [alerts, setAlerts] = useState([])
  const [tasks, setTasks] = useState([])
  const [status, setStatus] = useState('loading')
  const [activePage, setActivePage] = useState('overview')
  const [gatewayStatus, setGatewayStatus] = useState(null)
  const [gatewayDraft, setGatewayDraft] = useState(null)
  const [gatewayMessage, setGatewayMessage] = useState('')
  const [gatewayOpen, setGatewayOpen] = useState(false)
  const [themeMode, setThemeMode] = useState(() => {
    if (typeof window === 'undefined') {
      return 'system'
    }
    return window.localStorage.getItem('openclaw-monitor-theme') ?? 'system'
  })

  useEffect(() => {
    async function loadDashboard() {
      try {
        const [overviewRes, agentsRes, alertsRes, tasksRes] = await Promise.all([
          fetch('/api/overview'),
          fetch('/api/agents'),
          fetch('/api/alerts'),
          fetch('/api/tasks'),
        ])

        const [overviewJson, agentsJson, alertsJson, tasksJson] = await Promise.all([
          overviewRes.json(),
          agentsRes.json(),
          alertsRes.json(),
          tasksRes.json(),
        ])

        setOverview(overviewJson)
        setAgents(agentsJson.items ?? [])
        setAlerts(alertsJson.items ?? [])
        setTasks(tasksJson.items ?? [])
        setStatus('ready')
      } catch {
        setStatus('error')
      }
    }

    async function loadGateway() {
      try {
        const [statusRes, configRes] = await Promise.all([
          fetch('/api/gateway/status'),
          fetch('/api/gateway/config'),
        ])
        const [statusJson, configJson] = await Promise.all([
          statusRes.json(),
          configRes.json(),
        ])
        setGatewayStatus(statusJson)
        setGatewayDraft(toGatewayDraft(configJson))
      } catch {
        setGatewayMessage('Gateway 配置读取失败')
      }
    }

    loadDashboard()
    loadGateway()
  }, [])

  useEffect(() => {
    if (typeof document === 'undefined') {
      return
    }

    document.documentElement.dataset.theme = themeMode
    document.documentElement.lang = 'zh-CN'
    window.localStorage.setItem('openclaw-monitor-theme', themeMode)
  }, [themeMode])

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
              type="button"
              key={item.id}
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
            gatewayLabel={gatewayLabel}
          />
        )}
        {activePage === 'agents' && <AgentsPage agents={agents} overview={overview} />}
        {activePage === 'tasks' && <TasksPage tasks={tasks} />}
        {activePage === 'token' && <TokenPage overview={overview} tasks={tasks} agents={agents} />}
        {activePage === 'events' && <EventsPage tasks={tasks} alerts={alerts} agents={agents} />}
        {activePage === 'alerts' && <AlertsPage alerts={alerts} overview={overview} />}

        {gatewayOpen && gatewayDraft && (
          <GatewayModal
            draft={gatewayDraft}
            message={gatewayMessage}
            onClose={() => {
              setGatewayOpen(false)
              setGatewayMessage('')
            }}
            onChange={(patch) => setGatewayDraft((current) => ({ ...current, ...patch }))}
            onSave={async () => {
              const payload = fromGatewayDraft(gatewayDraft)
              const response = await fetch('/api/gateway/config', {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload),
              })
              const json = await response.json()
              const statusRes = await fetch('/api/gateway/status')
              setGatewayStatus(await statusRes.json())
              setGatewayDraft(toGatewayDraft(json.config))
              setGatewayMessage('Gateway 配置已保存')
            }}
          />
        )}
      </main>
    </div>
  )
}

function PageHeader({ activePage, status, snapshot, gatewayStatus, onOpenGateway }) {
  const page = pageMeta[activePage]
  const runtime = gatewayStatus?.runtime || {}
  const detected = Boolean(runtime.detected)
  const detectState = detected ? '已发现 Gateway' : '未发现 Gateway'

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
        <button type="button" className="btn btn-outline" onClick={onOpenGateway}>
          Gateway 设置
        </button>
        <div className={detected ? 'status-badge gateway-ok' : 'status-badge gateway-warn'}>
          <span className={`status-dot ${detected ? 'ready' : ''}`} />
          <span>{detectState}</span>
        </div>
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

function GatewayModal({ draft, message, onClose, onChange, onSave }) {
  return (
    <div className="modal-backdrop" onClick={onClose}>
      <section className="modal-card" onClick={(event) => event.stopPropagation()}>
        <div className="panel-head">
          <div>
            <h2>Gateway 设置</h2>
            <p>自动探测默认优先使用 18789，可补充自定义端口、Origin、认证信息或远程地址。</p>
          </div>
          <button type="button" className="btn btn-outline" onClick={onClose}>
            关闭
          </button>
        </div>

        <div className="form-grid">
          <label className="form-field">
            <span>启用自动捕捉</span>
            <select value={draft.enabled} onChange={(e) => onChange({ enabled: e.target.value })}>
              <option value="true">启用</option>
              <option value="false">禁用</option>
            </select>
          </label>

          <label className="form-field">
            <span>自动探测模式</span>
            <select value={draft.mode} onChange={(e) => onChange({ mode: e.target.value })}>
              <option value="local-first">本机优先</option>
              <option value="manual">手动指定</option>
            </select>
          </label>

          <label className="form-field">
            <span>默认端口</span>
            <input value={draft.defaultPort} onChange={(e) => onChange({ defaultPort: e.target.value })} />
          </label>

          <label className="form-field">
            <span>探测端口列表</span>
            <input value={draft.discoveryPorts} onChange={(e) => onChange({ discoveryPorts: e.target.value })} />
          </label>

          <label className="form-field form-field-wide">
            <span>手动指定地址</span>
            <input value={draft.baseUrl} onChange={(e) => onChange({ baseUrl: e.target.value })} placeholder="例如 http://127.0.0.1:18789" />
          </label>

          <label className="form-field form-field-wide">
            <span>Origin 覆盖（可选）</span>
            <input value={draft.origin} onChange={(e) => onChange({ origin: e.target.value })} placeholder="留空则自动使用 Gateway 地址" />
          </label>

          <label className="form-field form-field-wide">
            <span>远程候选地址</span>
            <input value={draft.remoteUrl} onChange={(e) => onChange({ remoteUrl: e.target.value })} placeholder="例如 https://example.tailnet.ts.net" />
          </label>

          <label className="form-field">
            <span>会话键</span>
            <input value={draft.sessionKey} onChange={(e) => onChange({ sessionKey: e.target.value })} />
          </label>

          <label className="form-field">
            <span>探测间隔（秒）</span>
            <input value={draft.probeIntervalSeconds} onChange={(e) => onChange({ probeIntervalSeconds: e.target.value })} />
          </label>

          <label className="form-field">
            <span>Gateway Token</span>
            <input value={draft.token} onChange={(e) => onChange({ token: e.target.value })} placeholder="可选，用于需要 token 的 Gateway" />
          </label>

          <label className="form-field">
            <span>Password</span>
            <input type="password" value={draft.password} onChange={(e) => onChange({ password: e.target.value })} placeholder="可选，不会在页面回显" />
          </label>
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

function OverviewPage({ overview, tasks, agents, alerts, gatewayLabel }) {
  const statCards = [
    {
      label: '在线 Agent',
      value: formatValue(overview.agentOnlineCount),
      change: `${overview.agentOfflineCount} 个离线`,
      tone: overview.agentOfflineCount > 0 ? 'danger' : 'success',
    },
    {
      label: '在线节点',
      value: formatValue(overview.nodeOnlineCount),
      change: `${overview.nodeOfflineCount} 个离线`,
      tone: overview.nodeOfflineCount > 0 ? 'danger' : 'success',
    },
    {
      label: '运行中任务',
      value: formatValue(overview.taskRunningCount),
      change: `${overview.taskWaitingCount} 个等待中`,
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
      <section className="hero-banner">
        <div>
          <p className="banner-tag">{gatewayLabel} / 跨端查看</p>
          <h2>让任务流转、Agent 活跃度和故障现场都能被看见</h2>
          <p className="banner-text">
            只读观测，不介入调度。通过统一的事件、状态推导和告警视图，把 OpenClaw 的黑盒执行过程变成可追踪、可定位、可回放的监控面板。
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
                    {task.taskType} / {task.executorNodeId}
                  </span>
                </div>
                <div className="table-meta">
                  <span>{formatValue(task.tokenUsage?.total)} Token</span>
                  <span>{formatDuration(task.durationMs)}</span>
                  <span className={`badge ${task.status}`}>{statusLabel(task.status)}</span>
                </div>
              </div>
            ))}
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
                  <strong>{agent.name}</strong>
                  <p>{agent.derivedStatusReason}</p>
                </div>
                <div className="stack-tags">
                  <span className={`badge ${agent.connectivityStatus}`}>{connectivityLabel(agent.connectivityStatus)}</span>
                  <span className="badge subtle">{statusLabel(agent.runtimeStatus)}</span>
                </div>
              </div>
            ))}
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
          </div>
        </section>

        <section className="panel">
          <div className="panel-head">
            <div>
              <h2>健康摘要</h2>
              <p>节点、任务与成本当前态势</p>
            </div>
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

function AgentsPage({ agents, overview }) {
  return (
    <>
      <section className="grid-dashboard">
        <article className="stat-card">
          <div className="stat-header">
            <div className="stat-value">{formatValue(agents.length)}</div>
            <div className="stat-label">Agent 总数</div>
          </div>
          <div className="stat-change neutral">
            <span className="change-dot" />
            <span>{formatValue(overview.agentOnlineCount)} 个在线</span>
          </div>
        </article>
        <article className="stat-card">
          <div className="stat-header">
            <div className="stat-value">{formatValue(overview.agentOfflineCount)}</div>
            <div className="stat-label">离线 Agent</div>
          </div>
          <div className="stat-change danger">
            <span className="change-dot" />
            <span>需要优先排查</span>
          </div>
        </article>
        <article className="stat-card">
          <div className="stat-header">
            <div className="stat-value">{formatValue(agents.filter((item) => item.runtimeStatus === 'running').length)}</div>
            <div className="stat-label">运行中</div>
          </div>
          <div className="stat-change success">
            <span className="change-dot" />
            <span>执行链路活跃</span>
          </div>
        </article>
        <article className="stat-card">
          <div className="stat-header">
            <div className="stat-value">{formatValue(agents.reduce((sum, item) => sum + (item.todayTokenTotal || 0), 0))}</div>
            <div className="stat-label">今日 Agent Token</div>
          </div>
          <div className="stat-change neutral">
            <span className="change-dot" />
            <span>按 Agent 聚合</span>
          </div>
        </article>
      </section>

      <section className="panel">
        <div className="panel-head">
          <div>
            <h2>Agent 观察列表</h2>
            <p>用于定位谁在线、谁正在执行、谁需要恢复</p>
          </div>
          <span className="panel-note">{agents.length} 个 Agent</span>
        </div>
        <div className="stack-list">
          {agents.map((agent) => (
            <div className="stack-item" key={agent.id}>
              <div>
                <strong>{agent.name}</strong>
                <p>{agent.derivedStatusReason}</p>
              </div>
              <div className="stack-tags">
                <span className={`badge ${agent.connectivityStatus}`}>{connectivityLabel(agent.connectivityStatus)}</span>
                <span className="badge subtle">{statusLabel(agent.runtimeStatus)}</span>
                <span className="time-text">{formatValue(agent.todayTokenTotal)} Token</span>
              </div>
            </div>
          ))}
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
          <p>聚焦任务生命周期、耗时、Token 与执行节点</p>
        </div>
        <span className="panel-note">{tasks.length} 个任务</span>
      </div>
      <div className="table-list">
        {tasks.map((task) => (
          <div className="table-row table-row-block" key={task.id}>
            <div className="table-main">
              <strong>{task.id}</strong>
              <span>
                {task.taskType} / 来源 {task.sourceAgentId} / 执行 {task.executorAgentId}
              </span>
            </div>
            <div className="table-grid">
              <div className="mini-stat">
                <span>状态</span>
                <strong>{statusLabel(task.status)}</strong>
              </div>
              <div className="mini-stat">
                <span>耗时</span>
                <strong>{formatDuration(task.durationMs)}</strong>
              </div>
              <div className="mini-stat">
                <span>Token</span>
                <strong>{formatValue(task.tokenUsage?.total)}</strong>
              </div>
              <div className="mini-stat">
                <span>节点</span>
                <strong>{task.executorNodeId}</strong>
              </div>
            </div>
          </div>
        ))}
      </div>
    </section>
  )
}

function TokenPage({ overview, tasks, agents }) {
  const topAgents = [...agents].sort((a, b) => (b.todayTokenTotal || 0) - (a.todayTokenTotal || 0))

  return (
    <>
      <section className="grid-dashboard">
        <article className="stat-card">
          <div className="stat-header">
            <div className="stat-value">{formatValue(overview.todayTokenTotal)}</div>
            <div className="stat-label">今日总 Token</div>
          </div>
          <div className="stat-change neutral">
            <span className="change-dot" />
            <span>{formatCurrency(overview.todayEstimatedCost)}</span>
          </div>
        </article>
        <article className="stat-card">
          <div className="stat-header">
            <div className="stat-value">{formatValue(tasks.reduce((sum, task) => sum + (task.tokenUsage?.input || 0), 0))}</div>
            <div className="stat-label">输入 Token</div>
          </div>
          <div className="stat-change success">
            <span className="change-dot" />
            <span>请求侧消耗</span>
          </div>
        </article>
        <article className="stat-card">
          <div className="stat-header">
            <div className="stat-value">{formatValue(tasks.reduce((sum, task) => sum + (task.tokenUsage?.output || 0), 0))}</div>
            <div className="stat-label">输出 Token</div>
          </div>
          <div className="stat-change warning">
            <span className="change-dot" />
            <span>响应侧消耗</span>
          </div>
        </article>
        <article className="stat-card">
          <div className="stat-header">
            <div className="stat-value">{formatCurrency(overview.todayEstimatedCost)}</div>
            <div className="stat-label">预计成本</div>
          </div>
          <div className="stat-change neutral">
            <span className="change-dot" />
            <span>美元折算</span>
          </div>
        </article>
      </section>

      <section className="content-columns lower">
        <section className="panel">
          <div className="panel-head">
            <div>
              <h2>按任务查看</h2>
              <p>识别哪些任务产生了主要消耗</p>
            </div>
          </div>
          <div className="stack-list">
            {tasks.map((task) => (
              <div className="stack-item" key={task.id}>
                <div>
                  <strong>{task.id}</strong>
                  <p>{task.taskType}</p>
                </div>
                <div className="stack-tags">
                  <span className="time-text">{formatValue(task.tokenUsage?.input)} 输入</span>
                  <span className="time-text">{formatValue(task.tokenUsage?.output)} 输出</span>
                  <span className="badge subtle">{formatValue(task.tokenUsage?.total)} 总计</span>
                </div>
              </div>
            ))}
          </div>
        </section>

        <section className="panel">
          <div className="panel-head">
            <div>
              <h2>按 Agent 查看</h2>
              <p>快速识别高消耗执行单元</p>
            </div>
          </div>
          <div className="stack-list">
            {topAgents.map((agent) => (
              <div className="stack-item" key={agent.id}>
                <div>
                  <strong>{agent.name}</strong>
                  <p>{statusLabel(agent.runtimeStatus)}</p>
                </div>
                <div className="stack-tags">
                  <span className="badge subtle">{formatValue(agent.todayTokenTotal)} Token</span>
                </div>
              </div>
            ))}
          </div>
        </section>
      </section>
    </>
  )
}

function EventsPage({ tasks, alerts, agents }) {
  const events = [
    {
      time: '刚刚',
      type: 'task_started',
      title: tasks[0] ? `${tasks[0].id} 开始执行` : '暂无任务启动事件',
      detail: tasks[0] ? `${tasks[0].executorAgentId} 正在 ${tasks[0].executorNodeId} 上执行任务` : '等待更多事件数据',
    },
    {
      time: '1 分钟前',
      type: 'agent_heartbeat',
      title: agents[0] ? `${agents[0].name} 心跳上报` : '暂无 Agent 心跳事件',
      detail: agents[0] ? agents[0].derivedStatusReason : '等待更多事件数据',
    },
    {
      time: '3 分钟前',
      type: 'alert_triggered',
      title: alerts[0] ? alerts[0].title : '暂无告警事件',
      detail: alerts[0] ? alerts[0].description : '等待更多事件数据',
    },
  ]

  return (
    <section className="panel">
      <div className="panel-head">
        <div>
          <h2>事件时间线</h2>
          <p>展示任务、Agent、告警等关键事件的标准化记录</p>
        </div>
      </div>
      <div className="timeline">
        {events.map((event) => (
          <div className="timeline-item" key={`${event.time}-${event.type}`}>
            <div className="timeline-dot" />
            <div className="timeline-body">
              <div className="timeline-top">
                <strong>{event.title}</strong>
                <span className="time-text">{event.time}</span>
              </div>
              <p>{event.detail}</p>
              <span className="badge subtle">{event.type}</span>
            </div>
          </div>
        ))}
      </div>
    </section>
  )
}

function AlertsPage({ alerts, overview }) {
  return (
    <>
      <section className="grid-dashboard">
        <article className="stat-card">
          <div className="stat-header">
            <div className="stat-value">{formatValue(alerts.length)}</div>
            <div className="stat-label">当前告警</div>
          </div>
          <div className="stat-change danger">
            <span className="change-dot" />
            <span>待处理项</span>
          </div>
        </article>
        <article className="stat-card">
          <div className="stat-header">
            <div className="stat-value">{formatValue(overview.taskFailedCount)}</div>
            <div className="stat-label">失败任务相关</div>
          </div>
          <div className="stat-change warning">
            <span className="change-dot" />
            <span>需结合任务视图排查</span>
          </div>
        </article>
        <article className="stat-card">
          <div className="stat-header">
            <div className="stat-value">{formatValue(overview.agentOfflineCount)}</div>
            <div className="stat-label">离线相关</div>
          </div>
          <div className="stat-change danger">
            <span className="change-dot" />
            <span>Agent 连接性检查</span>
          </div>
        </article>
        <article className="stat-card">
          <div className="stat-header">
            <div className="stat-value">{formatValue(overview.todayErrorCount)}</div>
            <div className="stat-label">今日错误事件</div>
          </div>
          <div className="stat-change neutral">
            <span className="change-dot" />
            <span>排障证据基础</span>
          </div>
        </article>
      </section>

      <section className="panel">
        <div className="panel-head">
          <div>
            <h2>告警列表</h2>
            <p>集中查看当前打开的故障项与触发时间</p>
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
        </div>
      </section>
    </>
  )
}

function formatValue(value) {
  if (value === null || value === undefined) {
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
      return status ?? '--'
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
  return severity ?? '--'
}

function calcRatio(online, offline) {
  const total = Number(online || 0) + Number(offline || 0)
  if (!total) {
    return '--'
  }
  return `${Math.round((online / total) * 100)}%`
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
