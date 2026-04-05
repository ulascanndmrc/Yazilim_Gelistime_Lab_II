'use strict';

const API = '';  // same origin
const REFRESH_MS = 5000;

let allLogs = [];
let filterService = '';
let filterStatus = '';

// ─── Bootstrap ───────────────────────────────────────────────────────────────
async function refreshAll() {
  await Promise.all([fetchStats(), fetchHealth(), fetchLogs()]);
  document.getElementById('last-update').textContent =
    'Updated ' + new Date().toLocaleTimeString();
}

// ─── Stats ────────────────────────────────────────────────────────────────────
async function fetchStats() {
  try {
    const res = await fetch(`${API}/api/gateway/stats`);
    if (!res.ok) return;
    const d = await res.json();

    setText('total-requests', fmt(d.total_requests));
    setText('success-count',  fmt(d.success_count));
    setText('error-count',    fmt(d.error_count));
    setText('avg-latency',    (d.avg_response_time_ms || 0).toFixed(1));

    renderBarChart(d.requests_per_service || {});
  } catch (e) {
    console.warn('stats error', e);
  }
}

// ─── Service health ──────────────────────────────────────────────────────────
async function fetchHealth() {
  try {
    const res = await fetch(`${API}/api/gateway/health`);
    if (!res.ok) return;
    const data = await res.json();
    renderServices(data);
  } catch (e) {
    console.warn('health error', e);
  }
}

function renderServices(data) {
  const grid = document.getElementById('services-grid');
  grid.innerHTML = '';
  const icons = {
    'login-service':   '🔑',
    'message-service': '💬',
    'user-service':    '👤',
    'product-service': '📦',
    'report-service':  '📈',
  };
  for (const [name, info] of Object.entries(data)) {
    const cls = info.status === 'up' ? 'status-up'
              : info.status === 'down' ? 'status-down' : 'status-degraded';
    const dot = info.status === 'up' ? '● Up'
              : info.status === 'down' ? '● Down' : '● Degraded';
    const card = document.createElement('div');
    card.className = 'service-card';
    card.innerHTML = `
      <div class="svc-name">${icons[name] || '⬡'} ${name}</div>
      <div class="svc-status ${cls}">${dot}</div>`;
    grid.appendChild(card);
  }
}

// ─── Bar chart ────────────────────────────────────────────────────────────────
function renderBarChart(perService) {
  const chart = document.getElementById('bar-chart');
  const entries = Object.entries(perService);
  if (!entries.length) {
    chart.innerHTML = '<div class="chart-loading">No traffic yet</div>';
    return;
  }
  const max = Math.max(...entries.map(([, v]) => v), 1);
  chart.innerHTML = '';
  const colors = {
    'login-service':   'linear-gradient(180deg,#6c8fff,#a78bfa)',
    'message-service': 'linear-gradient(180deg,#22d3a5,#0ea5e9)',
    'user-service':    'linear-gradient(180deg,#fbbf24,#f97316)',
    'product-service': 'linear-gradient(180deg,#f87171,#ec4899)',
    'report-service':  'linear-gradient(180deg,#a78bfa,#6c8fff)',
  };
  entries.forEach(([svc, count]) => {
    const pct = Math.max((count / max) * 140, 4);
    const wrap = document.createElement('div');
    wrap.className = 'bar-wrap';
    wrap.innerHTML = `
      <div class="bar-count">${fmt(count)}</div>
      <div class="bar" style="height:${pct}px;background:${colors[svc] || 'var(--accent)'}"></div>
      <div class="bar-label">${svc.replace('-service','')}</div>`;
    chart.appendChild(wrap);
  });
}

// ─── Logs ─────────────────────────────────────────────────────────────────────
async function fetchLogs() {
  try {
    const res = await fetch(`${API}/api/gateway/logs?limit=200`);
    if (!res.ok) return;
    const { logs } = await res.json();
    allLogs = logs || [];
    renderLogs();
  } catch (e) {
    console.warn('logs error', e);
  }
}

function applyFilter() {
  filterService = document.getElementById('log-filter').value;
  filterStatus  = document.getElementById('status-filter').value;
  renderLogs();
}

function renderLogs() {
  let rows = allLogs;
  if (filterService) rows = rows.filter(l => l.target_service === filterService);
  if (filterStatus)  rows = rows.filter(l => String(l.status_code).startsWith(filterStatus));
  rows = rows.slice(0, 100);

  const tbody = document.getElementById('log-tbody');
  if (!rows.length) {
    tbody.innerHTML = '<tr><td colspan="7" class="loading-row">No logs match the filter</td></tr>';
    return;
  }
  tbody.innerHTML = rows.map(log => {
    const ts   = formatTime(log.timestamp);
    const meth = methodBadge(log.method || '');
    const sc   = statusBadge(log.status_code);
    const lat  = (log.response_time_ms || 0).toFixed(1) + ' ms';
    const usr  = log.user_id ? log.user_id.slice(-8) : '—';
    const path = (log.path || '').slice(0, 40);
    const svc  = log.target_service || '—';
    return `<tr>
      <td>${ts}</td>
      <td>${meth}</td>
      <td title="${log.path}">${path}</td>
      <td>${svc}</td>
      <td>${sc}</td>
      <td>${lat}</td>
      <td>${usr}</td>
    </tr>`;
  }).join('');
}

// ─── Helpers ──────────────────────────────────────────────────────────────────
function setText(id, val) {
  const el = document.getElementById(id);
  if (el) el.textContent = val;
}

function fmt(n) {
  return Number(n || 0).toLocaleString();
}

function formatTime(ts) {
  if (!ts) return '—';
  const d = new Date(ts);
  return isNaN(d) ? ts : d.toLocaleTimeString();
}

function methodBadge(m) {
  return `<span class="method-badge method-${m}">${m}</span>`;
}

function statusBadge(code) {
  const c = Number(code);
  const cls = c >= 500 ? 'status-5xx' : c >= 400 ? 'status-4xx' : 'status-2xx';
  return `<span class="status-badge ${cls}">${code}</span>`;
}

// ─── Init ─────────────────────────────────────────────────────────────────────
refreshAll();
setInterval(refreshAll, REFRESH_MS);
