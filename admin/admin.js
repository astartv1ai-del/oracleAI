/* ══════ Панель Оракула ══════
   Ванильный JS без сборки: панель живёт рядом с API на том же VPS, и лишний
   шаг сборки только удлинял бы деплой. Графики рисуем сами в SVG — внешние
   библиотеки требуют CDN, а панель должна открываться и без интернета у сервера.

   Вход — по подписи Telegram WebApp: панель открывается кнопкой из бота, своего
   пароля у неё нет, поэтому и утекать нечему. */

const tg = window.Telegram?.WebApp;
tg?.ready();
tg?.expand();

const qs = new URLSearchParams(location.search);
const DEV_USER = qs.get('dev_user');

const state = {
  role: null,
  tgId: null,
  permissions: [],
  period: 30,
  demo: false,
  view: 'dashboard',
  users: { q: '', segment: 'all', order: 'created_at', offset: 0, limit: 50, total: 0 },
  segments: [],
  content: { kind: '', items: [], current: null },
  promoBatch: '',
  plans: [],
};

/* ── сеть ── */
async function api(path, opts = {}) {
  const url = new URL(path, location.origin);
  if (DEV_USER) url.searchParams.set('dev_user', DEV_USER);
  const res = await fetch(url, {
    ...opts,
    headers: {
      'Content-Type': 'application/json',
      'X-Init-Data': tg?.initData || '',
      ...(opts.headers || {}),
    },
  });
  if (!res.ok) {
    let detail = `Ошибка ${res.status}`;
    try { detail = (await res.json()).detail || detail; } catch { /* не JSON */ }
    const err = new Error(detail);
    err.status = res.status;
    throw err;
  }
  return res.status === 204 ? null : res.json();
}

const get = (p) => api(p);
const post = (p, body) => api(p, { method: 'POST', body: JSON.stringify(body ?? {}) });
const del = (p) => api(p, { method: 'DELETE' });
const patch = (p, body) => api(p, { method: 'PATCH', body: JSON.stringify(body ?? {}) });

/* ── утилиты ── */
const $ = (id) => document.getElementById(id);
const esc = (s) => { const d = document.createElement('div'); d.textContent = s ?? ''; return d.innerHTML; };
const num = (n) => (n ?? 0).toLocaleString('ru-RU');
const pct = (n) => `${(n ?? 0).toFixed(1)}%`;

function date(iso, withTime = false) {
  if (!iso) return '—';
  const d = new Date(iso);
  if (Number.isNaN(+d)) return '—';
  return withTime
    ? d.toLocaleString('ru-RU', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' })
    : d.toLocaleDateString('ru-RU');
}

/* Stars → доллары: ориентир для «сколько это денег», курс из бизнес-плана */
const STARS_TO_USD = 1 / 52;
const usd = (stars) => `$${((stars || 0) * STARS_TO_USD).toFixed(0)}`;

let toastTimer;
function toast(text, bad = false) {
  const el = $('toast');
  el.textContent = text;
  el.className = 'toast show' + (bad ? ' bad' : '');
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => { el.className = 'toast'; }, 3600);
}

function fail(e) {
  toast(e.message || 'Что-то пошло не так', true);
  console.error(e);
}

function can(permission) {
  return state.permissions.includes('*') || state.permissions.includes(permission);
}

function table(columns, rows, opts = {}) {
  if (!rows.length) return `<div class="empty">${esc(opts.empty || 'Пока пусто')}</div>`;
  const head = columns.map((c) => `<th class="${c.num ? 'num' : ''}">${esc(c.title)}</th>`).join('');
  const body = rows.map((row, i) => {
    const cells = columns.map((c) => `<td class="${c.num ? 'num' : ''}">${c.render(row, i)}</td>`).join('');
    return `<tr class="${opts.onRow ? 'clickable' : ''}" data-i="${i}">${cells}</tr>`;
  }).join('');
  return `<table><thead><tr>${head}</tr></thead><tbody>${body}</tbody></table>`;
}

function bindRows(container, rows, handler) {
  container.querySelectorAll('tbody tr').forEach((tr) => {
    tr.addEventListener('click', (ev) => {
      if (ev.target.closest('button,select,input,a')) return;
      handler(rows[+tr.dataset.i]);
    });
  });
}

/* ══════ графики ══════ */

/* Линейный график: несколько серий на общей сетке. Значения нормируем по
   максимуму всех серий, иначе слабая серия сплющивается в ноль. */
function lineChart(el, days, series) {
  const W = 700, H = 190, pad = { l: 34, r: 8, t: 12, b: 20 };
  const max = Math.max(1, ...series.flatMap((s) => s.values));
  const x = (i) => pad.l + (i * (W - pad.l - pad.r)) / Math.max(1, days.length - 1);
  const y = (v) => pad.t + (1 - v / max) * (H - pad.t - pad.b);

  let svg = `<svg viewBox="0 0 ${W} ${H}" preserveAspectRatio="none">`;
  for (let g = 0; g <= 3; g++) {
    const gy = pad.t + (g * (H - pad.t - pad.b)) / 3;
    const label = Math.round(max - (g * max) / 3);
    svg += `<line x1="${pad.l}" y1="${gy}" x2="${W - pad.r}" y2="${gy}"
            stroke="rgba(255,255,255,.07)"/>
            <text x="${pad.l - 6}" y="${gy + 3}" text-anchor="end"
            font-size="9" fill="#9c94bd">${label}</text>`;
  }
  series.forEach((s) => {
    const pts = s.values.map((v, i) => `${x(i)},${y(v)}`).join(' ');
    if (s.fill) {
      svg += `<polygon points="${pad.l},${y(0)} ${pts} ${x(days.length - 1)},${y(0)}"
              fill="${s.color}" opacity=".12"/>`;
    }
    svg += `<polyline points="${pts}" fill="none" stroke="${s.color}"
            stroke-width="2" stroke-linejoin="round" stroke-linecap="round"/>`;
  });
  const step = Math.max(1, Math.ceil(days.length / 7));
  days.forEach((d, i) => {
    if (i % step && i !== days.length - 1) return;
    svg += `<text x="${x(i)}" y="${H - 4}" text-anchor="middle" font-size="9"
            fill="#9c94bd">${d.slice(8, 10)}.${d.slice(5, 7)}</text>`;
  });
  svg += '</svg>';
  el.innerHTML = svg;
}

function barChart(el, days, values, color = '#e8c56b') {
  const W = 700, H = 190, pad = { l: 34, r: 8, t: 12, b: 20 };
  const max = Math.max(1, ...values);
  const bw = Math.max(2, (W - pad.l - pad.r) / Math.max(1, values.length) - 2);
  let svg = `<svg viewBox="0 0 ${W} ${H}" preserveAspectRatio="none">`;
  for (let g = 0; g <= 3; g++) {
    const gy = pad.t + (g * (H - pad.t - pad.b)) / 3;
    svg += `<line x1="${pad.l}" y1="${gy}" x2="${W - pad.r}" y2="${gy}"
            stroke="rgba(255,255,255,.07)"/>
            <text x="${pad.l - 6}" y="${gy + 3}" text-anchor="end" font-size="9"
            fill="#9c94bd">${Math.round(max - (g * max) / 3)}</text>`;
  }
  values.forEach((v, i) => {
    const h = (v / max) * (H - pad.t - pad.b);
    const bx = pad.l + (i * (W - pad.l - pad.r)) / Math.max(1, values.length);
    svg += `<rect x="${bx}" y="${H - pad.b - h}" width="${bw}" height="${h}"
            rx="2" fill="${color}" opacity="${v ? .85 : .2}"/>`;
  });
  const step = Math.max(1, Math.ceil(days.length / 7));
  days.forEach((d, i) => {
    if (i % step && i !== days.length - 1) return;
    const bx = pad.l + (i * (W - pad.l - pad.r)) / Math.max(1, values.length);
    svg += `<text x="${bx + bw / 2}" y="${H - 4}" text-anchor="middle" font-size="9"
            fill="#9c94bd">${d.slice(8, 10)}.${d.slice(5, 7)}</text>`;
  });
  el.innerHTML = svg + '</svg>';
}

/* ══════ навигация ══════ */
function switchView(name) {
  state.view = name;
  document.querySelectorAll('.nav-item').forEach((b) =>
    b.classList.toggle('active', b.dataset.view === name));
  document.querySelectorAll('.view').forEach((v) => v.classList.remove('active'));
  $('view-' + name).classList.add('active');
  $('view-title').textContent =
    document.querySelector(`.nav-item[data-view="${name}"]`)?.textContent.trim() || name;
  loadView(name);
}

document.querySelectorAll('.nav-item').forEach((b) =>
  b.addEventListener('click', () => switchView(b.dataset.view)));
$('refresh').addEventListener('click', () => loadView(state.view));
$('period').addEventListener('change', (e) => {
  state.period = +e.target.value;
  if (state.view === 'dashboard') loadDashboard();
});
$('demo-toggle').addEventListener('click', () => {
  if (state.role !== 'owner') return;
  state.demo = !state.demo;
  $('demo-toggle').textContent = state.demo ? 'ДЕМО: вкл.' : 'ДЕМО: выкл.';
  $('demo-toggle').classList.toggle('active', state.demo);
  loadDashboard().catch(fail);
});

const LOADERS = {
  dashboard: loadDashboard,
  users: loadUsers,
  orders: loadOrders,
  catalog: loadCatalog,
  promo: loadPromo,
  broadcasts: loadBroadcasts,
  content: loadContent,
  horoscopes: loadHoroscopes,
  costs: loadCosts,
  safety: loadSafety,
  settings: loadSettings,
  audit: loadAudit,
};

function loadView(name) {
  (LOADERS[name] || (() => {}))().catch(fail);
}

/* ══════ дашборд ══════ */
async function loadDashboard() {
  const dashboardPath = state.demo
    ? `/api/admin/dashboard/demo?days=${state.period}`
    : `/api/admin/dashboard?days=${state.period}`;
  const [d, health] = await Promise.all([
    get(dashboardPath), get('/api/admin/payment-health'),
  ]);
  const o = d.overview;
  $('demo-banner').classList.toggle('hidden', !state.demo);
  renderPaymentHealth(health);

  const kpis = [
    { label: 'Клиентки', value: num(o.users_total), sub: `+${num(o.users_today)} за сутки`, cls: '' },
    { label: 'Активны за 30 дн.', value: num(o.mau), sub: `${num(o.dau)} сегодня`, cls: '' },
    { label: 'Живые подписки', value: num(o.subs_active), sub: `онбординг: ${num(o.onboarded)}`, cls: 'good' },
    { label: 'Stars всего', value: num(o.stars_total), sub: `${usd(o.stars_total)} · ${num(o.payers)} плательщиц`, cls: 'accent' },
    { label: `Stars за ${state.period} дн.`, value: num(o.stars_30d), sub: usd(o.stars_30d), cls: 'accent' },
    { label: 'Вопросов за 7 дн.', value: num(o.questions_7d), sub: `${num(o.questions_today)} сегодня`, cls: '' },
    { label: 'Раскладов', value: num(o.readings_total), sub: `${num(o.readings_7d)} за неделю`, cls: '' },
    { label: 'Кристаллы в обороте', value: num(o.crystals_outstanding), sub: 'не потрачено клиентками', cls: '' },
  ];
  if (state.demo) {
    kpis.unshift({ label: 'Проект работает', value: '17 дней', sub: 'демо-срез · не production', cls: 'accent' });
  }
  $('kpi').innerHTML = kpis.map((k) => `
    <div class="kpi ${k.cls}">
      <div class="kpi-label">${esc(k.label)}</div>
      <div class="kpi-value">${k.value}</div>
      <div class="kpi-sub">${esc(k.sub)}</div>
    </div>`).join('');

  const days = d.timeseries.map((t) => t.day);
  lineChart($('chart-activity'), days, [
    { values: d.timeseries.map((t) => t.active), color: '#e8c56b', fill: true },
    { values: d.timeseries.map((t) => t.questions), color: '#7fb4e8' },
    { values: d.timeseries.map((t) => t.users), color: '#7fd8a8' },
  ]);
  barChart($('chart-revenue'), days, d.timeseries.map((t) => t.stars));

  const m = d.monetization || {};
  $('kpi-monetization').innerHTML = [
    { label: `ARPPU за ${m.days ?? state.period} дн.`, value: `${num(m.paid_arppu_stars)} ⭐`,
      sub: `${num(m.paid_payers)} плательщиц`, cls: 'accent' },
    { label: 'Повторных оплат', value: pct(m.repeat_payer_rate),
      sub: `${num(m.repeat_payers)} человек`, cls: '' },
    { label: 'Возвраты', value: pct(m.refund_rate),
      sub: `${num(m.refund_orders)} заказов`, cls: m.refund_rate > 5 ? 'bad' : 'good' },
    { label: 'Активаций купонов', value: num(d.promo_batches.reduce((s, b) => s + b.used, 0)),
      sub: `в ${num(d.promo_batches.length)} партиях`, cls: '' },
  ].map((k) => `<div class="kpi ${k.cls}">
      <div class="kpi-label">${esc(k.label)}</div>
      <div class="kpi-value">${k.value}</div>
      <div class="kpi-sub">${esc(k.sub)}</div>
    </div>`).join('');

  const r = d.revenue;
  $('revenue-facts').innerHTML = `
    <span>оплат: <b>${num(r.orders_paid)}</b></span>
    <span>за период: <b>${num(r.orders_period)}</b></span>
    <span>средний чек: <b>${num(r.orders_paid ? Math.round(r.stars_total / r.orders_paid) : 0)} ⭐</b></span>
    <span>возвраты: <b>${num(r.refunds)}</b></span>`;

  // Воронка: рядом со шагом показываем потерю относительно предыдущего —
  // именно она подсказывает, где чинить продукт.
  $('funnel').innerHTML = d.funnel.map((s, i) => {
    const prev = i ? d.funnel[i - 1].value : s.value;
    const drop = prev ? Math.round((1 - s.value / prev) * 100) : 0;
    return `<div class="funnel-step">
      <div class="funnel-top">
        <span>${esc(s.step)}</span>
        <span>${num(s.value)} · ${pct(s.of_total)}
          ${i && drop > 0 ? `<span class="funnel-drop">−${drop}%</span>` : ''}</span>
      </div>
      <div class="funnel-bar"><div class="funnel-fill" style="width:${Math.max(1, s.of_total)}%"></div></div>
    </div>`;
  }).join('');

  $('retention').innerHTML = table([
    { title: 'Когорта', render: (r) => date(r.cohort) },
    { title: 'Людей', num: true, render: (r) => num(r.size) },
    { title: 'D1', num: true, render: (r) => pct(r.d1) },
    { title: 'D3', num: true, render: (r) => pct(r.d3) },
    { title: 'D7', num: true, render: (r) => pct(r.d7) },
    { title: 'D14', num: true, render: (r) => pct(r.d14) },
    { title: 'D30', num: true, render: (r) => pct(r.d30) },
  ], d.retention, { empty: 'Когорт пока нет — нужны первые недели' });

  $('top-products').innerHTML = table([
    { title: 'Товар', render: (p) => esc(p.title || p.sku) },
    { title: 'Продаж', num: true, render: (p) => num(p.sales) },
    { title: 'Stars', num: true, render: (p) => num(p.stars) },
  ], d.top_products, { empty: 'Продаж пока нет' });

  $('sources').innerHTML = table([
    { title: 'Канал', render: (s) => esc(s.source) },
    { title: 'Пришло', num: true, render: (s) => num(s.users) },
    { title: 'Платят', num: true, render: (s) => num(s.payers) },
    { title: 'Stars', num: true, render: (s) => num(s.stars) },
  ], d.sources, { empty: 'Нет данных о каналах' });

  $('referrers').innerHTML = table([
    { title: 'Кто', render: (r) => esc(r.name || r.tg_id) },
    { title: 'Привела', num: true, render: (r) => num(r.invited) },
    { title: '✦', num: true, render: (r) => num(r.bonus) },
  ], d.top_referrers, { empty: 'Приглашений пока нет' });
}

function renderPaymentHealth(h) {
  const checks = h?.checks || {};
  const recon = checks.reconciliation || {};
  const failures = Object.values(checks.webhook_failures_24h || {}).reduce((s, n) => s + (n || 0), 0);
  const anomalies = Object.values(recon).reduce((s, n) => s + (n || 0), 0);
  const status = h?.status || 'unknown';
  const statusLabel = { ok: 'OK', degraded: 'DEGRADED', critical: 'CRITICAL', unknown: 'нет snapshot' }[status] || status;
  const statusClass = status === 'ok' ? 'on' : status === 'critical' ? 'bad' : 'warn';
  const providers = Object.entries(h?.providers || {}).map(([name, p]) => {
    const cls = p.status === 'ok' ? 'on' : p.status === 'degraded' ? 'warn' : 'off';
    const balance = (p.balances || []).map((b) => `${esc(b.asset)}: ${esc(b.available)}`).join(', ');
    return `<span class="health-provider"><b>${esc(name)}</b><span class="badge ${cls}">${esc(p.status || 'unknown')}</span>${balance ? `<span>${balance}</span>` : ''}</span>`;
  }).join('');
  $('payment-health-updated').textContent = h?.checked_at ? `проверено ${date(h.checked_at, true)}` : 'проверка ещё не запускалась';
  $('payment-health').innerHTML = `
    <div class="payment-health-summary"><span class="badge ${statusClass}">${esc(statusLabel)}</span><span class="muted small">Проверки выполняются автоматически каждые 10 минут в активном bot process.</span></div>
    <div class="payment-health-grid">
      <div class="health-stat"><span>Зависшие pending &gt; ${num(h?.stale_pending_threshold_hours || 2)} ч</span><b>${num(checks.pending_orders_stale)}</b></div>
      <div class="health-stat"><span>Ошибки webhook за 24 ч</span><b>${num(failures)}</b></div>
      <div class="health-stat"><span>Ошибки заказов за 24 ч</span><b>${num(checks.failed_orders_24h)}</b></div>
      <div class="health-stat"><span>Аномалии сверки</span><b>${num(anomalies)}</b></div>
    </div>
    <div class="health-provider">Поставщики: ${providers || '<span>не настроены</span>'}</div>`;
}

/* ══════ клиентки ══════ */
function segmentLabel(code) {
  const map = {
    all: 'Все', active_sub: 'С подпиской', expired: 'Без подписки',
    onboarded: 'Прошли знакомство', not_onboarded: 'Не дошли до конца',
    paying: 'Платящие', never_paid: 'Ни разу не платили',
    push_on: 'С утренним прогнозом', active_7d: 'Активны за 7 дней',
    sleeping_14d: 'Спят 14+ дней', expiring_3d: 'Подписка кончается за 3 дня',
  };
  return map[code] || code;
}

async function loadUsers() {
  const u = state.users;
  const params = new URLSearchParams({
    q: u.q, segment: u.segment, order: u.order,
    limit: String(u.limit), offset: String(u.offset),
  });
  const data = await get(`/api/admin/users?${params}`);
  u.total = data.total;
  state.segments = data.segments;

  const sel = $('user-segment');
  if (sel.options.length !== data.segments.length) {
    sel.innerHTML = data.segments.map((s) =>
      `<option value="${s}">${esc(segmentLabel(s))}</option>`).join('');
    sel.value = u.segment;
  }
  fillSegmentSelect($('bc-segment'), data.segments);

  $('user-total').textContent = `найдено: ${num(data.total)}`;
  $('users-page').textContent =
    `${u.offset + 1}–${Math.min(u.offset + u.limit, data.total)} из ${num(data.total)}`;
  $('users-prev').disabled = u.offset === 0;
  $('users-next').disabled = u.offset + u.limit >= data.total;

  const el = $('users-table');
  el.innerHTML = table([
    { title: 'Клиентка', render: (r) => `<b>${esc(r.name || '—')}</b>
        <div class="muted small">${r.username ? '@' + esc(r.username) : r.tg_id}</div>` },
    { title: 'Тариф', render: (r) => r.sub_active
        ? `<span class="badge on">${esc(r.sub_level)}</span>`
        : '<span class="badge off">нет</span>' },
    { title: 'Теги', render: (r) => (r.tags || []).map((t) =>
        `<span class="badge tag">${esc(t)}</span>`).join(' ') || '' },
    { title: '✦', num: true, render: (r) => num(r.crystals) },
    { title: 'Stars', num: true, render: (r) => num(r.ltv_stars) },
    { title: 'Была', render: (r) => date(r.last_seen, true) },
    { title: 'Пришла', render: (r) => date(r.created_at) },
  ], data.items, { onRow: true, empty: 'Никого не нашлось' });
  bindRows(el, data.items, (row) => openUser(row.tg_id));
}

function fillSegmentSelect(sel, segments) {
  if (!sel || sel.options.length === segments.length) return;
  sel.innerHTML = segments.map((s) =>
    `<option value="${s}">${esc(segmentLabel(s))}</option>`).join('');
}

let searchTimer;
$('user-q').addEventListener('input', (e) => {
  clearTimeout(searchTimer);
  searchTimer = setTimeout(() => {
    state.users.q = e.target.value.trim();
    state.users.offset = 0;
    loadUsers().catch(fail);
  }, 350);
});
$('user-segment').addEventListener('change', (e) => {
  state.users.segment = e.target.value;
  state.users.offset = 0;
  loadUsers().catch(fail);
});
$('user-order').addEventListener('change', (e) => {
  state.users.order = e.target.value;
  loadUsers().catch(fail);
});
$('users-prev').addEventListener('click', () => {
  state.users.offset = Math.max(0, state.users.offset - state.users.limit);
  loadUsers().catch(fail);
});
$('users-next').addEventListener('click', () => {
  state.users.offset += state.users.limit;
  loadUsers().catch(fail);
});

/* ── карточка клиентки ── */
document.querySelectorAll('[data-close]').forEach((el) =>
  el.addEventListener('click', () => $('drawer').classList.add('hidden')));

async function openUser(tgId) {
  const c = await get(`/api/admin/users/${tgId}`);
  const u = c.user;
  const sun = c.chart?.sun;
  const tabs = [
    ['profile', 'Профиль'], ['chats', 'Диалоги'], ['money', 'Платежи'],
    ['memory', 'Память'], ['activity', 'События'], ['actions', 'Действия'],
  ];

  $('drawer-content').innerHTML = `
    <div class="u-head">
      <div class="u-avatar">${esc(sun?.symbol || '🔮')}</div>
      <div>
        <div class="u-name">${esc(u.name || 'без имени')}
          ${c.sub_active ? `<span class="badge on">${esc(u.sub_level)}</span>`
                         : '<span class="badge off">без подписки</span>'}</div>
        <div class="u-meta">${u.username ? '@' + esc(u.username) + ' · ' : ''}id ${u.tg_id}
          · с ${date(u.created_at)}${u.source ? ' · ' + esc(u.source) : ''}</div>
      </div>
    </div>

    <div class="u-stats">
      <div class="u-stat"><b>${num(u.crystals)}</b><span>Кристаллы ✦</span></div>
      <div class="u-stat"><b>${num(c.sub_days_left)}</b><span>дней подписки</span></div>
      <div class="u-stat"><b>${num(u.ltv_stars)}</b><span>Stars всего</span></div>
      <div class="u-stat"><b>${num(c.questions_today)}</b><span>вопросов сегодня</span></div>
      <div class="u-stat"><b>${num(c.diary_streak)}</b><span>стрик дневника</span></div>
      <div class="u-stat"><b>${num(c.referrals.level1)}</b><span>привела подруг</span></div>
    </div>

    <div class="chip-row" id="u-tags">
      ${(c.tags || []).map((t) => `<span class="badge tag">${esc(t)}
        <a href="#" data-untag="${esc(t)}">✕</a></span>`).join('')}
      ${can('crm:write') ? '<button class="btn tiny ghost" id="u-add-tag">+ тег</button>' : ''}
    </div>

    <div class="u-tabs">
      ${tabs.map(([k, t], i) =>
        `<button class="u-tab ${i === 0 ? 'active' : ''}" data-pane="${k}">${t}</button>`).join('')}
    </div>

    <div class="u-pane active" data-pane="profile">
      <table>
        <tr><th>Рождение</th><td>${esc(u.birth_date || '—')} ${esc(u.birth_time || '')}
          ${u.birth_time_known ? '' : '<span class="badge">время неточное</span>'}</td></tr>
        <tr><th>Город</th><td>${esc(u.birth_city || '—')} · ${esc(u.tz || '')}</td></tr>
        <tr><th>Солнце</th><td>${sun ? esc(`${sun.sign} (${sun.element})`) : '—'}
          · режим карты: ${esc(c.chart?.mode || '—')}</td></tr>
        <tr><th>Оракул</th><td>${esc(u.oracle_name || '—')} · образ ${esc(u.persona || '—')}</td></tr>
        <tr><th>Тариф</th><td>${esc(c.plan.title || u.sub_level)} · до ${date(u.sub_until, true)}</td></tr>
        <tr><th>Утренний прогноз</th><td>${u.morning_push ? 'включён' : 'выключен'}</td></tr>
        <tr><th>Пригласила её</th><td>${c.referrer ? `id ${c.referrer}` : '—'}</td></tr>
        <tr><th>Права</th><td>${(c.entitlements || []).map((e) =>
          `<span class="badge warn">${esc(e.kind)}:${esc(e.code || '*')}
           ×${e.qty_total - e.qty_used}</span>`).join(' ') || '—'}</td></tr>
      </table>
      <h3 style="margin:16px 0 8px">Заметки</h3>
      <div id="u-notes">${(c.notes || []).map((n) => `
        <div class="timeline"><div>${esc(n.text)}
          <div class="t-when">${date(n.created_at, true)}</div></div></div>`).join('')
        || '<div class="muted small">Заметок нет</div>'}</div>
      ${can('crm:write') ? `<div class="form tight">
        <textarea id="u-note-text" class="input" rows="2" placeholder="Что важно помнить об этой клиентке…"></textarea>
        <button class="btn ghost" id="u-note-add">Добавить заметку</button></div>` : ''}
    </div>

    <div class="u-pane" data-pane="chats">
      ${(c.threads || []).map((t) => `<div class="muted small">
        ${esc(t.agent)} · ${num(t.msg_count)} сообщений · ${date(t.last_at, true)}</div>`).join('')}
      <h3 style="margin:12px 0 8px">Расклады</h3>
      ${table([
        { title: 'Расклад', render: (r) => esc(r.spread || r.question || '—') },
        { title: 'Карты', render: (r) => esc((r.cards || []).map((x) => x.name).join(', ').slice(0, 60)) },
        { title: 'Сбылось', render: (r) => r.outcome ? `<span class="badge on">${esc(r.outcome)}</span>` : '—' },
        { title: 'Когда', render: (r) => date(r.created_at) },
      ], c.readings || [], { empty: 'Раскладов не было' })}
      <h3 style="margin:12px 0 8px">Разборы</h3>
      ${table([
        { title: 'Разбор', render: (r) => esc(r.title) },
        { title: 'Период', render: (r) => esc(r.period || '—') },
        { title: 'Когда', render: (r) => date(r.created_at) },
      ], c.reports || [], { empty: 'Разборов не покупала' })}
    </div>

    <div class="u-pane" data-pane="money">
      ${table([
        { title: 'Заказ', render: (o) => esc(o.title || o.sku || o.kind) },
        { title: 'Stars', num: true, render: (o) => num(o.amount_stars) },
        { title: '✦', num: true, render: (o) => num(o.amount_crystals) },
        { title: 'Статус', render: (o) => `<span class="badge ${o.status === 'paid' ? 'on'
            : o.status === 'refunded' ? 'bad' : 'off'}">${esc(o.status)}</span>` },
        { title: 'Когда', render: (o) => date(o.paid_at || o.created_at, true) },
      ], c.orders || [], { empty: 'Покупок не было' })}
      <h3 style="margin:12px 0 8px">Кристаллы</h3>
      ${table([
        { title: 'Δ', num: true, render: (h) => (h.delta > 0 ? '+' : '') + num(h.delta) },
        { title: 'Причина', render: (h) => esc(h.reason) },
        { title: 'Баланс', num: true, render: (h) => num(h.balance) },
        { title: 'Когда', render: (h) => date(h.created_at, true) },
      ], c.crystals_history || [], { empty: 'Движений не было' })}
    </div>

    <div class="u-pane" data-pane="memory">
      ${(c.memories || []).length ? `<div class="timeline">${c.memories.map((m) =>
        `<div>${esc(m.fact)} <span class="badge">${esc(m.kind)}</span>
         <span class="badge">вес ${m.weight}</span>
         <div class="t-when">${date(m.created_at, true)}</div></div>`).join('')}</div>`
        : '<div class="muted small">Память пуста</div>'}
    </div>

    <div class="u-pane" data-pane="activity">
      <div class="timeline">${(c.events || []).map((e) =>
        `<div><b>${esc(e.name)}</b> ${esc(e.surface || '')}
         ${e.props_json ? `<span class="muted small">${esc(e.props_json)}</span>` : ''}
         <div class="t-when">${date(e.created_at, true)}</div></div>`).join('')
        || '<div class="muted small">Событий нет</div>'}</div>
    </div>

    <div class="u-pane" data-pane="actions">
      ${can('grants') ? `
      <div class="card"><div class="card-head"><h3>Выдать</h3></div>
        <div class="form">
          <div class="row-2 tight">
            <label>Что<select id="g-kind" class="input">
              <option value="plan">Подписку</option>
              <option value="crystals">Кристаллы ✦</option>
              <option value="spread">Право на расклад</option>
              <option value="report">Право на разбор</option>
              <option value="question">Вопросы</option>
            </select></label>
            <label>Код / SKU<input id="g-code" class="input" placeholder="vip, celtic, natal…"></label>
          </div>
          <div class="row-2 tight">
            <label>Количество<input id="g-qty" class="input" type="number" value="1" min="1"></label>
            <label>Дней<input id="g-days" class="input" type="number" placeholder="по умолчанию"></label>
          </div>
          <label>Причина (в аудит)<input id="g-reason" class="input" placeholder="компенсация за сбой"></label>
          <button class="btn gold" id="g-do">Выдать</button>
        </div>
      </div>` : ''}

      ${can('crm:write') ? `
      <div class="card"><div class="card-head"><h3>Написать клиентке</h3></div>
        <div class="form">
          <textarea id="m-text" class="input" rows="4" placeholder="Здравствуйте! Мы разобрались с вашим вопросом…"></textarea>
          <button class="btn ghost" id="m-send">Отправить в Telegram</button>
        </div>
      </div>` : ''}

      ${can('users:write') ? `
      <div class="card"><div class="card-head"><h3>Доступ</h3></div>
        <div class="btn-row">
          <button class="btn ${u.status === 'blocked' ? '' : 'danger'}" id="u-status">
            ${u.status === 'blocked' ? 'Разблокировать' : 'Заблокировать'}</button>
          ${state.role === 'owner' ? '<button class="btn danger" id="u-anon">Удалить данные</button>' : ''}
        </div>
        <p class="muted small" style="margin-top:8px">Блокировка закрывает доступ к API и боту.
          Удаление данных стирает PII и историю, финансовый след остаётся.</p>
      </div>` : ''}
    </div>`;

  $('drawer').classList.remove('hidden');
  wireUserCard(tgId, u);
}

function wireUserCard(tgId, u) {
  const root = $('drawer-content');
  root.querySelectorAll('.u-tab').forEach((btn) => btn.addEventListener('click', () => {
    root.querySelectorAll('.u-tab').forEach((b) => b.classList.toggle('active', b === btn));
    root.querySelectorAll('.u-pane').forEach((p) =>
      p.classList.toggle('active', p.dataset.pane === btn.dataset.pane));
  }));

  root.querySelectorAll('[data-untag]').forEach((a) => a.addEventListener('click', async (ev) => {
    ev.preventDefault();
    try {
      await del(`/api/admin/users/${tgId}/tags/${encodeURIComponent(a.dataset.untag)}`);
      openUser(tgId);
    } catch (e) { fail(e); }
  }));

  $('u-add-tag')?.addEventListener('click', async () => {
    const tag = prompt('Тег (например: vip, вернуть, конфликт)');
    if (!tag) return;
    try { await post(`/api/admin/users/${tgId}/tags`, { tag }); openUser(tgId); }
    catch (e) { fail(e); }
  });

  $('u-note-add')?.addEventListener('click', async () => {
    const text = $('u-note-text').value.trim();
    if (!text) return;
    try {
      await post(`/api/admin/users/${tgId}/notes`, { text });
      toast('Заметка сохранена');
      openUser(tgId);
    } catch (e) { fail(e); }
  });

  $('g-do')?.addEventListener('click', async (ev) => {
    const btn = ev.currentTarget;
    btn.disabled = true;
    try {
      const granted = await post(`/api/admin/users/${tgId}/grant`, {
        kind: $('g-kind').value,
        code: $('g-code').value.trim() || null,
        qty: +$('g-qty').value || 1,
        days: +$('g-days').value || null,
        reason: $('g-reason').value.trim(),
      });
      toast(`Выдано: ${granted.title || granted.kind}`);
      openUser(tgId);
    } catch (e) { fail(e); } finally { btn.disabled = false; }
  });

  $('m-send')?.addEventListener('click', async (ev) => {
    const text = $('m-text').value.trim();
    if (!text) return;
    ev.currentTarget.disabled = true;
    try {
      await post(`/api/admin/users/${tgId}/message`, { text });
      toast('Сообщение отправлено');
      openUser(tgId);
    } catch (e) { fail(e); } finally { ev.currentTarget.disabled = false; }
  });

  $('u-status')?.addEventListener('click', async () => {
    const next = u.status === 'blocked' ? 'active' : 'blocked';
    if (next === 'blocked' && !confirm('Закрыть доступ этой клиентке?')) return;
    try {
      await post(`/api/admin/users/${tgId}/status`, { status: next });
      toast(next === 'blocked' ? 'Доступ закрыт' : 'Доступ открыт');
      openUser(tgId);
      loadUsers().catch(fail);
    } catch (e) { fail(e); }
  });

  $('u-anon')?.addEventListener('click', async () => {
    if (!confirm('Стереть персональные данные и историю? Отменить нельзя.')) return;
    try {
      await post(`/api/admin/users/${tgId}/anonymize`);
      toast('Данные удалены');
      $('drawer').classList.add('hidden');
      loadUsers().catch(fail);
    } catch (e) { fail(e); }
  });
}

/* ══════ заказы ══════ */
async function loadOrders() {
  const status = $('order-status').value;
  const rows = await get(`/api/admin/orders?limit=200${status ? '&status=' + status : ''}`);
  const el = $('orders-table');
  el.innerHTML = table([
    { title: '#', render: (o) => o.id },
    { title: 'Клиентка', render: (o) => `${esc(o.name || o.tg_id)}
        ${o.username ? `<div class="muted small">@${esc(o.username)}</div>` : ''}` },
    { title: 'Что', render: (o) => `${esc(o.title || o.sku || o.kind)}
        <div class="muted small">${esc(o.kind)}</div>` },
    { title: 'Stars', num: true, render: (o) => num(o.amount_stars) },
    { title: '✦', num: true, render: (o) => num(o.amount_crystals) },
    { title: 'Статус', render: (o) => `<span class="badge ${o.status === 'paid' ? 'on'
        : o.status === 'refunded' ? 'bad' : 'off'}">${esc(o.status)}</span>` },
    { title: 'Когда', render: (o) => date(o.paid_at || o.created_at, true) },
    { title: '', render: (o, i) => (o.status === 'paid' && can('grants'))
        ? `<button class="btn tiny danger" data-refund="${o.id}" data-i="${i}">Возврат</button>` : '' },
  ], rows, { onRow: true, empty: 'Заказов нет' });

  el.querySelectorAll('[data-refund]').forEach((btn) =>
    btn.addEventListener('click', async (ev) => {
      ev.stopPropagation();
      if (!confirm('Вернуть Stars клиентке? Telegram проведёт возврат.')) return;
      btn.disabled = true;
      try {
        await post(`/api/admin/orders/${btn.dataset.refund}/refund`);
        toast('Возврат проведён');
        loadOrders().catch(fail);
      } catch (e) { fail(e); btn.disabled = false; }
    }));
  bindRows(el, rows, (o) => openUser(o.tg_id));
}
$('order-status').addEventListener('change', () => loadOrders().catch(fail));

/* ══════ каталог ══════ */
function editableCell(value, { entity, id, field, type = 'text' }) {
  return `<input class="input slim" style="width:${type === 'number' ? '86px' : '160px'}"
    type="${type}" value="${esc(String(value ?? ''))}"
    data-entity="${entity}" data-id="${esc(id)}" data-field="${field}">`;
}

async function loadCatalog() {
  const [plans, products] = await Promise.all([
    get('/api/admin/plans'), get('/api/admin/products'),
  ]);
  state.plans = plans;

  $('plans-table').innerHTML = table([
    { title: 'Код', render: (p) => `<code>${esc(p.code)}</code>` },
    { title: 'Название', render: (p) => editableCell(p.title, { entity: 'plan', id: p.code, field: 'title' }) },
    { title: 'Stars', num: true, render: (p) => editableCell(p.price_stars, { entity: 'plan', id: p.code, field: 'price_stars', type: 'number' }) },
    { title: 'Дней', num: true, render: (p) => editableCell(p.period_days, { entity: 'plan', id: p.code, field: 'period_days', type: 'number' }) },
    { title: 'Вопр./день', num: true, render: (p) => editableCell(p.daily_questions, { entity: 'plan', id: p.code, field: 'daily_questions', type: 'number' }) },
    { title: 'Память', num: true, render: (p) => editableCell(p.memory_depth, { entity: 'plan', id: p.code, field: 'memory_depth', type: 'number' }) },
    { title: '✦ бонус', num: true, render: (p) => editableCell(p.crystals_grant, { entity: 'plan', id: p.code, field: 'crystals_grant', type: 'number' }) },
    { title: 'Витрина', render: (p) => `<label class="switch"><input type="checkbox"
        ${p.is_public ? 'checked' : ''} data-entity="plan" data-id="${esc(p.code)}"
        data-field="is_public"><span></span></label>` },
  ], plans, { empty: 'Тарифов нет' });

  $('products-table').innerHTML = table([
    { title: 'SKU', render: (p) => `<code>${esc(p.sku)}</code>` },
    { title: 'Вид', render: (p) => `<span class="badge">${esc(p.kind)}</span>` },
    { title: 'Название', render: (p) => editableCell(p.title, { entity: 'product', id: p.sku, field: 'title' }) },
    { title: 'Stars', num: true, render: (p) => editableCell(p.price_stars, { entity: 'product', id: p.sku, field: 'price_stars', type: 'number' }) },
    { title: '✦', num: true, render: (p) => editableCell(p.price_crystals, { entity: 'product', id: p.sku, field: 'price_crystals', type: 'number' }) },
    { title: 'Выдаём', render: (p) => `${esc(p.grant_kind || '')}${p.grant_code ? ':' + esc(p.grant_code) : ''} ×${p.grant_qty}` },
    { title: 'Активен', render: (p) => `<label class="switch"><input type="checkbox"
        ${p.is_active ? 'checked' : ''} data-entity="product" data-id="${esc(p.sku)}"
        data-field="is_active"><span></span></label>` },
  ], products, { empty: 'Товаров нет' });

  wireCatalogEdits();
  const promoPlan = $('promo-plan');
  promoPlan.innerHTML = plans.map((p) =>
    `<option value="${esc(p.code)}">${esc(p.title)}</option>`).join('');
  promoPlan.value = plans.some((p) => p.code === 'vip') ? 'vip' : plans[0]?.code;
}

function wireCatalogEdits() {
  if (!can('catalog')) {
    document.querySelectorAll('[data-entity]').forEach((el) => { el.disabled = true; });
    return;
  }
  document.querySelectorAll('[data-entity]').forEach((el) => {
    const commit = async () => {
      const value = el.type === 'checkbox' ? (el.checked ? 1 : 0)
        : el.type === 'number' ? Number(el.value) : el.value;
      const body = { fields: { [el.dataset.field]: value } };
      try {
        if (el.dataset.entity === 'plan') await post('/api/admin/plans', { code: el.dataset.id, ...body });
        else await post('/api/admin/products', { sku: el.dataset.id, ...body });
        toast('Сохранено');
      } catch (e) { fail(e); }
    };
    el.addEventListener(el.type === 'checkbox' ? 'change' : 'blur', commit);
  });
}

/* ══════ промокоды ══════ */
async function loadPromo() {
  if (!state.plans.length) await loadCatalog();
  const unused = $('promo-unused').checked;
  const batch = state.promoBatch;
  const params = new URLSearchParams();
  if (unused) params.set('unused', 'true');
  if (batch) params.set('batch', batch);
  const [data, redemptions] = await Promise.all([
    get(`/api/admin/promo?${params}`),
    get('/api/admin/promo/redemptions?limit=300'),
  ]);

  $('promo-batches').innerHTML = table([
    { title: 'Партия', render: (b) => `<code>${esc(b.batch)}</code>
        ${state.promoBatch === b.batch ? '<span class="badge on">фильтр</span>' : ''}` },
    { title: 'Кодов', num: true, render: (b) => num(b.total) },
    { title: 'Активировано', num: true, render: (b) => num(b.used) },
    { title: 'Конверсия', num: true, render: (b) => pct(b.total ? (b.used * 100) / b.total : 0) },
    { title: 'Создана', render: (b) => date(b.created_at) },
  ], data.batches, { onRow: true, empty: 'Партий пока нет' });
  bindRows($('promo-batches'), data.batches, (b) => {
    state.promoBatch = state.promoBatch === b.batch ? '' : b.batch;
    $('promo-batch-hint').textContent = state.promoBatch
      ? `фильтр: партия «${state.promoBatch}» (клик по партии ещё раз — снять)` : '';
    loadPromo().catch(fail);
  });

  const who = new Map(redemptions.map((r) => [r.code, r]));
  $('promo-codes').innerHTML = table([
    { title: 'Код', render: (c) => `<code>${esc(c.code)}</code>` },
    { title: 'Что даёт', render: (c) => c.kind === 'crystals' ? `✦${c.crystals}`
        : c.kind === 'product' ? esc(c.sku || '') : `${c.days} дн. ${esc(c.plan_code || '')}` },
    { title: 'Партия', render: (c) => esc(c.batch || '—') },
    { title: 'Использован', num: true, render: (c) => `${c.used_count || 0}/${c.max_uses || 1}` },
    { title: 'Кем', render: (c) => { const r = who.get(c.code); return r
        ? `<b>${esc(r.name || r.tg_id)}</b>${r.username ? ` <span class="muted small">@${esc(r.username)}</span>` : ''}`
        : '—'; } },
    { title: 'Когда', render: (c) => { const r = who.get(c.code);
        return r ? date(r.created_at, true) : '—'; } },
    { title: 'Действует до', render: (c) => date(c.expires_at) },
  ], data.codes, { onRow: true, empty: 'Кодов нет' });
  bindRows($('promo-codes'), data.codes, (c) => c.used_by && openUser(c.used_by));

  $('promo-redemptions').innerHTML = table([
    { title: 'Когда', render: (r) => date(r.created_at, true) },
    { title: 'Кто', render: (r) => `<b>${esc(r.name || r.tg_id)}</b>
        ${r.username ? `<div class="muted small">@${esc(r.username)}</div>` : ''}` },
    { title: 'Код', render: (r) => `<code>${esc(r.code)}</code>` },
    { title: 'Партия', render: (r) => esc(r.batch || '—') },
    { title: 'Что дало', render: (r) => r.kind === 'crystals' ? `✦${r.crystals}`
        : r.kind === 'product' ? esc(r.sku || '') : `${r.days} дн. ${esc(r.plan_code || '')}` },
  ], redemptions, { onRow: true, empty: 'Активаций пока не было' });
  bindRows($('promo-redemptions'), redemptions, (r) => openUser(r.tg_id));
}
$('promo-unused').addEventListener('change', () => loadPromo().catch(fail));

$('promo-create').addEventListener('click', async (ev) => {
  const btn = ev.currentTarget;
  btn.disabled = true;
  try {
    const res = await post('/api/admin/promo', {
      count: +$('promo-count').value || 1,
      kind: $('promo-kind').value,
      days: +$('promo-days').value || 30,
      plan_code: $('promo-plan').value,
      crystals: +$('promo-crystals').value || 0,
      sku: $('promo-sku').value.trim() || null,
      batch: $('promo-batch').value.trim() || 'manual',
      max_uses: +$('promo-uses').value || 1,
      valid_days: +$('promo-valid').value || null,
    });
    const out = $('promo-out');
    out.textContent = res.codes.join('\n');
    out.classList.remove('hidden');
    toast(`Создано кодов: ${res.codes.length}`);
    loadPromo().catch(fail);
  } catch (e) { fail(e); } finally { btn.disabled = false; }
});

/* ══════ рассылки ══════ */
async function loadBroadcasts() {
  if (!state.segments.length) await loadUsers();
  fillSegmentSelect($('bc-segment'), state.segments);
  const rows = await get('/api/admin/broadcasts');
  const el = $('bc-list');
  el.innerHTML = table([
    { title: 'Рассылка', render: (b) => `${esc(b.title)}
        <div class="muted small">${esc(b.body || '').slice(0, 60)}…</div>` },
    { title: 'Статус', render: (b) => `<span class="badge ${b.status === 'done' ? 'on'
        : b.status === 'running' ? 'warn' : b.status === 'cancelled' ? 'bad' : 'off'}">${esc(b.status)}</span>` },
    { title: 'Ушло', num: true, render: (b) => `${num(b.progress.sent)}/${num(b.total)}` },
    { title: 'Ошибок', num: true, render: (b) => num(b.progress.failed + b.progress.skipped) },
    { title: 'Когда', render: (b) => date(b.started_at || b.scheduled_at || b.created_at, true) },
    { title: '', render: (b) => (b.status === 'scheduled' || b.status === 'running')
        ? `<button class="btn tiny danger" data-cancel="${b.id}">Отменить</button>`
        : (b.status === 'draft' ? `<button class="btn tiny ghost" data-start="${b.id}">Отправить</button>` : '') },
  ], rows, { empty: 'Рассылок не было' });

  el.querySelectorAll('[data-cancel]').forEach((btn) => btn.addEventListener('click', async () => {
    try { await post(`/api/admin/broadcasts/${btn.dataset.cancel}/cancel`); toast('Отменено'); loadBroadcasts(); }
    catch (e) { fail(e); }
  }));
  el.querySelectorAll('[data-start]').forEach((btn) => btn.addEventListener('click', async () => {
    try { await post(`/api/admin/broadcasts/${btn.dataset.start}/start`); toast('Отправка запущена'); loadBroadcasts(); }
    catch (e) { fail(e); }
  }));
}

function broadcastPayload(sendNow) {
  return {
    title: $('bc-title').value.trim(),
    body: $('bc-body').value.trim(),
    segment: $('bc-segment').value,
    button_text: $('bc-btn-text').value.trim() || null,
    button_url: $('bc-btn-url').value.trim() || null,
    send_now: sendNow,
  };
}

$('bc-preview').addEventListener('click', async () => {
  try {
    const res = await post('/api/admin/broadcasts/preview', broadcastPayload(false));
    $('bc-preview-out').textContent =
      `В сегменте «${segmentLabel(res.segment)}» — ${num(res.count)} человек.`;
  } catch (e) { fail(e); }
});

$('bc-create').addEventListener('click', async (ev) => {
  const payload = broadcastPayload(true);
  if (!payload.title || !payload.body) { toast('Нужны название и текст', true); return; }
  if (!confirm(`Отправить рассылку сегменту «${segmentLabel(payload.segment)}»?`)) return;
  ev.currentTarget.disabled = true;
  try {
    const res = await post('/api/admin/broadcasts', payload);
    toast(`Поставлено в очередь: ${num(res.total)} получателей`);
    $('bc-body').value = '';
    $('bc-title').value = '';
    loadBroadcasts().catch(fail);
  } catch (e) { fail(e); } finally { ev.currentTarget.disabled = false; }
});

/* ══════ контент ══════ */
const CONTENT_HINTS = {
  agent: 'Тело — образ и манера речи агента. В meta можно задать rules и tagline.',
  persona: 'Образ Оракула, который выбирает клиентка при знакомстве.',
  guide: 'Правила трактовки: подмешиваются к данным расчёта перед ответом модели.',
  copy: 'Текст сценария. {name} подставляется автоматически.',
  faq: 'Вопрос-ответ для Mini App.',
  spread: 'Свой расклад. В meta обязательно positions: ["Позиция 1", …].',
  practice: 'Практика с трекером дней.',
};

async function loadContent() {
  const kind = $('content-kind').value;
  state.content.kind = kind;
  const items = await get(`/api/admin/content${kind ? '?kind=' + kind : ''}`);
  state.content.items = items;
  $('content-list').innerHTML = items.map((item, i) => `
    <div class="list-item ${state.content.current === i ? 'active' : ''}" data-i="${i}">
      <div class="li-title">${esc(item.title || item.code)}
        ${item.is_active ? '' : '<span class="badge off">выкл</span>'}</div>
      <div class="li-code">${esc(item.kind)} / ${esc(item.code)}</div>
    </div>`).join('') || '<div class="empty">Нет записей</div>';

  $('content-list').querySelectorAll('.list-item').forEach((el) =>
    el.addEventListener('click', () => openContent(+el.dataset.i)));
  if (items.length) openContent(state.content.current ?? 0);
}
$('content-kind').addEventListener('change', () => {
  state.content.current = null;
  loadContent().catch(fail);
});

function openContent(index) {
  const item = state.content.items[index];
  if (!item) return;
  state.content.current = index;
  $('content-list').querySelectorAll('.list-item').forEach((el) =>
    el.classList.toggle('active', +el.dataset.i === index));
  $('content-editor-title').textContent = `${item.kind} / ${item.code}`;
  const editable = can('content:write');
  $('content-editor').innerHTML = `
    <p class="muted small">${esc(CONTENT_HINTS[item.kind] || '')}</p>
    <label>Заголовок<input id="c-title" class="input" value="${esc(item.title || '')}"></label>
    <label>Текст<textarea id="c-body" class="input" rows="14">${esc(item.body || '')}</textarea></label>
    <label>meta (JSON)<textarea id="c-meta" class="input" rows="4">${esc(item.meta_json || '')}</textarea></label>
    <div class="row-2 tight">
      <label class="check"><input type="checkbox" id="c-active" ${item.is_active ? 'checked' : ''}> активна</label>
      <label>Порядок<input id="c-sort" class="input" type="number" value="${item.sort ?? 100}"></label>
    </div>
    <div class="btn-row">
      <button class="btn gold" id="c-save" ${editable ? '' : 'disabled'}>Сохранить</button>
      <button class="btn danger" id="c-del" ${editable ? '' : 'disabled'}>Удалить</button>
    </div>
    <p class="muted small">Обновлено: ${date(item.updated_at, true)}</p>`;

  $('c-save').addEventListener('click', async () => {
    let meta = null;
    const raw = $('c-meta').value.trim();
    if (raw) {
      try { meta = JSON.parse(raw); }
      catch { toast('meta — не корректный JSON', true); return; }
    }
    try {
      await post('/api/admin/content', {
        kind: item.kind, code: item.code,
        title: $('c-title').value, body: $('c-body').value, meta,
        is_active: $('c-active').checked, sort: +$('c-sort').value || 100,
      });
      toast('Сохранено');
      loadContent().catch(fail);
    } catch (e) { fail(e); }
  });

  $('c-del').addEventListener('click', async () => {
    if (!confirm(`Удалить ${item.kind}/${item.code}?`)) return;
    try {
      await del(`/api/admin/content/${item.kind}/${item.code}`);
      state.content.current = null;
      toast('Удалено');
      loadContent().catch(fail);
    } catch (e) { fail(e); }
  });
}

$('content-new').addEventListener('click', async () => {
  const kind = $('content-kind').value || prompt('Вид (agent, persona, guide, copy, faq, spread, practice)');
  if (!kind) return;
  const code = prompt('Код записи (латиницей, без пробелов)');
  if (!code) return;
  try {
    await post('/api/admin/content', { kind, code, title: code, body: '' });
    $('content-kind').value = kind;
    state.content.current = null;
    toast('Создано');
    loadContent().catch(fail);
  } catch (e) { fail(e); }
});

/* ══════ настройки ══════ */
const SETTING_HINTS = {
  'push.morning_hour': 'Час отправки утреннего прогноза (по времени клиентки)',
  'push.weekly_hour': 'Час воскресного отчёта',
  'push.weekly_weekday': '0 — понедельник, 6 — воскресенье',
  'limits.emergency_cost': 'Сколько ✦ стоит вопрос вне лимита',
  'limits.followup_window_minutes': 'Окно уточнений, которые не тратят лимит',
  'referral.bonus': '✦ обеим за приглашение',
  'referral.bonus_level2': '✦ за подругу подруги',
  'referral.revenue_share_crystals': '✦ пригласившей с первой оплаты',
  'broadcast.rate_per_second': 'Темп рассылки (Telegram допускает ~30/с)',
  'brand.bot_username': 'Имя бота без @ — для реферальных ссылок в Mini App',
};

async function loadSettings() {
  const [values, flags, admins] = await Promise.all([
    get('/api/admin/settings'), get('/api/admin/flags'), get('/api/admin/admins'),
  ]);
  const editable = can('settings:write');

  $('settings-list').innerHTML = Object.entries(values).sort().map(([key, value]) => `
    <label>${esc(key)}
      ${SETTING_HINTS[key] ? `<span class="muted small"> — ${esc(SETTING_HINTS[key])}</span>` : ''}
      <input class="input" data-setting="${esc(key)}"
        value="${esc(typeof value === 'string' ? value : JSON.stringify(value))}"
        ${editable ? '' : 'disabled'}></label>`).join('');

  $('settings-list').querySelectorAll('[data-setting]').forEach((el) =>
    el.addEventListener('blur', async () => {
      const raw = el.value;
      let value = raw;
      // числа и true/false храним типизированно: сервис ждёт число, а не «9»
      if (/^-?\d+(\.\d+)?$/.test(raw)) value = Number(raw);
      else if (raw === 'true' || raw === 'false') value = raw === 'true';
      else if (raw.startsWith('[') || raw.startsWith('{')) {
        try { value = JSON.parse(raw); } catch { /* оставляем строкой */ }
      }
      try { await post('/api/admin/settings', { key: el.dataset.setting, value }); toast('Сохранено'); }
      catch (e) { fail(e); }
    }));

  $('flags-list').innerHTML = flags.map((f) => `
    <div class="flag-row">
      <div class="flag-main">
        <div class="flag-code">${esc(f.code)}</div>
        <div class="flag-desc">${esc(f.description || '')}</div>
      </div>
      <input class="input slim pct" type="number" min="0" max="100" value="${f.rollout_pct ?? 100}"
        data-flag-pct="${esc(f.code)}" ${editable ? '' : 'disabled'} title="Процент раскатки">
      <label class="switch"><input type="checkbox" ${f.is_on ? 'checked' : ''}
        data-flag="${esc(f.code)}" ${editable ? '' : 'disabled'}><span></span></label>
    </div>`).join('');

  const saveFlag = async (code, body) => {
    try { await post('/api/admin/flags', { code, ...body }); toast('Сохранено'); }
    catch (e) { fail(e); }
  };
  $('flags-list').querySelectorAll('[data-flag]').forEach((el) =>
    el.addEventListener('change', () => saveFlag(el.dataset.flag, { is_on: el.checked })));
  $('flags-list').querySelectorAll('[data-flag-pct]').forEach((el) =>
    el.addEventListener('blur', () => saveFlag(el.dataset.flagPct, { rollout_pct: +el.value })));

  $('admins-list').innerHTML = table([
    { title: 'id', render: (a) => a.tg_id },
    { title: 'Роль', render: (a) => {
        if (state.role !== 'owner' || !a.created_at || a.tg_id === state.tgId) return `<span class="badge warn">${esc(a.role)}</span>`;
        return `<select class="input slim" data-role-for="${a.tg_id}">
          ${['analyst', 'support', 'admin', 'owner'].map((r) =>
            `<option value="${r}" ${a.role === r ? 'selected' : ''}>${r}</option>`).join('')}
        </select>`;
      } },
    { title: 'Подпись', render: (a) => esc(a.title || '') },
    { title: '', render: (a) => (state.role === 'owner' && a.created_at && a.tg_id !== state.tgId)
        ? `<button class="btn tiny danger" data-rm-admin="${a.tg_id}">Убрать</button>` : '' },
  ], admins, { empty: 'Только владелец из .env' });

  $('admins-list').querySelectorAll('[data-role-for]').forEach((sel) =>
    sel.addEventListener('change', async () => {
      try { await patch(`/api/admin/admins/${sel.dataset.roleFor}`, { role: sel.value }); toast('Роль обновлена'); }
      catch (e) { fail(e); loadSettings().catch(() => {}); }
    }));

  $('admins-list').querySelectorAll('[data-rm-admin]').forEach((btn) =>
    btn.addEventListener('click', async () => {
      if (!confirm('Убрать администратора?')) return;
      try { await del(`/api/admin/admins/${btn.dataset.rmAdmin}`); toast('Убрано'); loadSettings(); }
      catch (e) { fail(e); }
    }));
}

$('admin-add').addEventListener('click', async () => {
  const tgId = +$('admin-id').value;
  if (!tgId) { toast('Нужен Telegram id', true); return; }
  try {
    await post('/api/admin/admins', {
      tg_id: tgId,
      role: $('admin-role').value,
      title: $('admin-title').value.trim(),
    });
    toast('Добавлен');
    $('admin-id').value = '';
    $('admin-title').value = '';
    loadSettings().catch(fail);
  } catch (e) { fail(e); }
});

/* ══════ аудит ══════ */
async function loadAudit() {
  const rows = await get('/api/admin/audit?limit=300');
  $('audit-table').innerHTML = table([
    { title: 'Когда', render: (a) => date(a.created_at, true) },
    { title: 'Кто', render: (a) => esc(a.admin_name || a.admin_id || '—') },
    { title: 'Действие', render: (a) => `<code>${esc(a.action)}</code>` },
    { title: 'Объект', render: (a) => esc(a.target || '') },
    { title: 'Детали', render: (a) => `<span class="muted small">${esc(a.payload_json || '')}</span>` },
  ], rows, { empty: 'Записей нет' });
}

/* ══════ гороскопы по знакам ══════ */
async function loadHoroscopes() {
  const day = $('horo-day').value || undefined;
  const data = await get('/api/admin/horoscopes' + (day ? `?day=${day}` : ''));
  const channels = Object.keys(data.channels || {}).length;
  $('horo-channels').textContent = channels
    ? `каналов настроено: ${channels}`
    : 'каналы не настроены (HOROSCOPE_CHANNELS в .env)';

  $('horo-list').innerHTML = table([
    { title: 'Знак', render: (h) => `${esc(h.symbol)} ${esc(h.sign)}` },
    { title: 'Стихия', render: (h) => `<span class="muted">${esc(h.element)}</span>` },
    { title: 'Текст', render: (h) => h.text
      ? `<span class="muted small">${esc(h.text.slice(0, 160))}…</span>`
      : '<span class="bad">не собран</span>' },
    { title: 'В канале', render: (h) => h.posted_at
      ? date(h.posted_at, true) : '<span class="muted">—</span>' },
  ], data.items, { empty: 'На этот день ничего нет' });
}

$('horo-build').addEventListener('click', async (ev) => {
  const btn = ev.currentTarget;
  btn.disabled = true;
  try {
    const day = $('horo-day').value;
    const res = await post('/api/admin/horoscopes/build' + (day ? `?day=${day}` : ''));
    toast(res.built ? `Собрано знаков: ${res.built}` : 'Всё уже собрано');
    await loadHoroscopes();
  } catch (e) { fail(e); } finally { btn.disabled = false; }
});
$('horo-day').addEventListener('change', () => loadHoroscopes().catch(fail));

/* ══════ себестоимость LLM ══════
   Вся юнит-экономика построена на «≤ $2.5 на платящую в месяц» — этот экран
   единственное место, где видно, так ли это на самом деле. */
async function loadCosts() {
  const c = await get(`/api/admin/costs?days=${state.period}`);
  const perPaying = c.per_paying_usd;
  $('cost-kpi').innerHTML = [
    { label: `Расход за ${c.days} дн.`, value: `$${c.cost_usd.toFixed(2)}`,
      sub: `${num(c.calls)} вызовов`, cls: '' },
    { label: 'На платящую', value: `$${perPaying.toFixed(2)}`,
      sub: 'цель ≤ $2.50', cls: perPaying > 2.5 ? 'bad' : 'good' },
    { label: 'Сбои', value: pct(c.fail_rate), sub: `${num(c.failed)} вызовов`,
      cls: c.fail_rate > 5 ? 'bad' : 'good' },
  ].map((k) => `<div class="kpi ${k.cls}"><div class="kpi-label">${esc(k.label)}</div>
      <div class="kpi-value">${esc(k.value)}</div>
      <div class="kpi-sub">${esc(k.sub)}</div></div>`).join('');

  $('cost-purpose').innerHTML = table([
    { title: 'На что', render: (r) => `<code>${esc(r.purpose || '—')}</code>` },
    { title: 'Вызовов', num: true, render: (r) => num(r.calls) },
    { title: 'Токенов вход', num: true, render: (r) => num(r.tokens_in) },
    { title: 'Токенов выход', num: true, render: (r) => num(r.tokens_out) },
    { title: 'Стоимость', num: true, render: (r) => `$${(r.cost || 0).toFixed(3)}` },
    { title: 'Среднее, мс', num: true, render: (r) => num(Math.round(r.avg_ms)) },
  ], c.by_purpose, { empty: 'Вызовов ещё не было' });

  $('cost-models').innerHTML = table([
    { title: 'Провайдер', render: (r) => esc(r.provider) },
    { title: 'Модель', render: (r) => `<code>${esc(r.model)}</code>` },
    { title: 'Вызовов', num: true, render: (r) => num(r.calls) },
    { title: 'Стоимость', num: true, render: (r) => `$${(r.cost || 0).toFixed(3)}` },
  ], c.by_model, { empty: 'Вызовов ещё не было' });
}

/* ══════ безопасность ══════ */
const SAFETY_LABELS = {
  suicide: 'Суицидальные мысли', self_harm: 'Самоповреждение',
  violence: 'Насилие', medical: 'Здоровье', high_stakes: 'Крупные решения',
};

async function loadSafety() {
  const data = await get(`/api/admin/safety?days=${state.period}`);
  $('safety-summary').innerHTML = table([
    { title: 'Категория',
      render: (r) => esc(SAFETY_LABELS[r.category] || r.category) },
    { title: 'Реакция', render: (r) => r.action === 'support'
      ? '<span class="bad">поддержка вместо гадания</span>'
      : '<span class="muted">смягчённый ответ</span>' },
    { title: 'Случаев', num: true, render: (r) => num(r.n) },
  ], data.summary, { empty: 'Срабатываний не было' });

  $('safety-recent').innerHTML = table([
    { title: 'Когда', render: (r) => date(r.created_at, true) },
    { title: 'Кто', render: (r) => esc(r.name || r.tg_id || '—') },
    { title: 'Категория',
      render: (r) => esc(SAFETY_LABELS[r.category] || r.category) },
    { title: 'Сообщение',
      render: (r) => `<span class="muted small">${esc(r.excerpt || '')}</span>` },
  ], data.recent, { empty: 'Обращений не было' });
}

/* ══════ старт ══════ */
async function boot() {
  try {
    const me = await get('/api/admin/me');
    state.role = me.role;
    state.tgId = me.tg_id;
    state.permissions = me.permissions;
    $('who').innerHTML = `<b>${esc(me.name)}</b><br>роль: ${esc(me.role)}`;
    if (state.role === 'owner') {
      $('demo-toggle').classList.remove('hidden');
    }
    $('gate').classList.add('hidden');
    $('shell').classList.remove('hidden');

    // разделы не по правам просто скрываем: пустой экран с 403 хуже отсутствия кнопки
    const needs = {
      users: 'users:read', orders: 'dashboard', catalog: 'catalog',
      promo: 'promo', broadcasts: 'broadcast', content: 'content:read',
      settings: 'settings:read', audit: 'dashboard',
    };
    document.querySelectorAll('.nav-item').forEach((b) => {
      const need = needs[b.dataset.view];
      if (need && !can(need)) b.classList.add('hidden');
    });

    get('/api/admin/health').then((h) => {
      $('health').innerHTML =
        `<span>БД: ${h.ok ? '✅' : '⚠️'}</span><span>${num(h.users)} клиенток</span>` +
        (h.telegram_webapp_ready
          ? '<span>Бот: ✅</span>'
          : '<span class="bad" title="Задай HTTPS WEBAPP_URL на сервере">Бот: URL не задан</span>');
    }).catch(() => {});

    switchView('dashboard');
  } catch (e) {
    const msg = e.status === 403
      ? 'У этого аккаунта нет доступа к панели. Добавь свой Telegram id в ADMIN_ID.'
      : e.status === 401
        ? 'Открой панель кнопкой из бота — нужна подпись Telegram.'
        : e.message;
    $('gate-msg').textContent = msg;
  }
}

boot();
