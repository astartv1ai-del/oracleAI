/* ============================================================================
   ОРАКУЛ — Mini App, chat-first
   Главный инструмент — чат с ИИ-агентом. У каждого агента — кнопки-функции
   (фичи), которые живут прямо в диалоге: расклад Таро начинается с вопроса,
   натальная карта строится и сохраняется в профиль, всё остальное отвечает
   на вопрос через агента. Домашний экран — статичная база: прогноз дня.
   ============================================================================ */

const tg = () => window.Telegram && window.Telegram.WebApp;

/* ── API-клиент ─────────────────────────────────────────────────────────── */
async function api(path, opts = {}) {
  const headers = Object.assign({ 'Content-Type': 'application/json' }, opts.headers || {});
  const initData = tg() && tg().initData;
  if (initData) headers['X-Init-Data'] = initData;
  let url = path;
  const dev = new URLSearchParams(location.search).get('dev_user');
  if (dev) url += (url.includes('?') ? '&' : '?') + 'dev_user=' + dev;
  const res = await fetch(url, Object.assign({ headers }, opts));
  let body = null;
  try { body = await res.json(); } catch (e) { /* пустое тело */ }
  if (!res.ok) {
    const detail = body && (body.detail || JSON.stringify(body));
    const err = new Error(detail || 'Связь прервалась 🌙');
    err.status = res.status;
    throw err;
  }
  return body;
}

const esc = s => String(s == null ? '' : s).replace(/[&<>"]/g,
  c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));

// Rich-escape для серверного текста (чат-история, ответы LLM, отчёты):
// сначала всё экранируем, затем восстанавливаем ТОЛЬКО закрытые пары <b>/<i>
// из их экранированной формы. <script>, onerror=, атрибуты остаются текстом.
const rich = s => esc(s).replace(/&lt;(\/?)(b|i)&gt;/g, '<$1$2>');

const fmtDate = () => new Date().toLocaleDateString('ru-RU',
  { weekday: 'long', day: 'numeric', month: 'long' });

const fmtDay = iso => {
  const d = new Date(iso + 'T00:00:00');
  return d.toLocaleDateString('ru-RU', { day: 'numeric', month: 'short' });
};

/* ── реестр фич-кнопок агентов: chat-first, функции живут в диалоге ────── */
const FEATURES = {
  oracle: [
    { id: 'draw_tarot', e: '🎴', t: 'Расклад Таро', h: 'featureTarot' },
    { id: 'today', e: '🌅', t: 'Прогноз дня', h: 'featureToday' },
    { id: 'chart', e: '🌌', t: 'Натальная карта', h: 'featureChart' },
    { id: 'moon', e: '🌙', t: 'Лунная неделя', h: 'featureMoon' },
    { id: 'compat', e: '💞', t: 'Совместимость', h: 'featureCompat' },
    { id: 'matrix', e: '🔢', t: 'Матрица', h: 'featureMatrix' },
  ],
  tarot: [
    { id: 'tar', e: '🎴', t: 'Расклад Таро', h: 'featureTarot' },
    { id: 'hist', e: '📚', t: 'История', h: 'featureTarotHistory' },
  ],
  astro: [
    { id: 'chart', e: '🌌', t: 'Натальная карта', h: 'featureChart' },
    { id: 'today', e: '🔭', t: 'Небо сегодня', h: 'featureToday' },
    { id: 'moon', e: '🌙', t: 'Лунная неделя', h: 'featureMoon' },
    { id: 'compat', e: '💞', t: 'Совместимость', h: 'featureCompat' },
  ],
  numero: [
    { id: 'matrix', e: '🔢', t: 'Матрица Судьбы', h: 'featureMatrix' },
  ],
  coach: [
    { id: 'practice', e: '🧘', t: 'Подобрать практику', h: 'chatPractice' },
  ],
  keeper: [
    { id: 'monthly', e: '📖', t: 'Итог месяца', h: 'chatMonthly' },
  ],
};

/* ── приложение ─────────────────────────────────────────────────────────── */
const app = {
  me: null, agents: [], today: null, spreads: null,
  view: 'home',
  chat: { key: null, spec: null, messages: [], pending: null, busy: false },

  async boot() {
    if (tg()) {
      tg().ready && tg().ready();
      tg().expand && tg().expand();
      try { tg().setHeaderColor && tg().setHeaderColor('#08070f'); } catch (e) {}
    }
    this.renderFrame();
    try {
      this.me = await api('/api/me');
      const pill = document.querySelector('.user-pill');
      if (pill && this.me.name) {
        pill.innerHTML = `<span class="avatar">${esc(this.me.name[0].toUpperCase())}</span>${esc(this.me.name)}`;
      }
    } catch (e) { /* вход по dev_user в БД уже есть */ }
    this.loadAgents();
    this.loadToday();
    this.go('home');
  },

  /* ── каркас ── */
  renderFrame() {
    const root = document.getElementById('app-root');
    root.innerHTML = `
      <header class="app-header">
        <div class="brand-title">ОРАКУЛ<small>·AI</small></div>
        <div class="user-pill" data-act="go" data-goto="profile">
          <span class="avatar">${this.me && this.me.name ? esc(this.me.name[0].toUpperCase()) : '✦'}</span>
          ${this.me && this.me.name ? esc(this.me.name) : 'Гость'}
        </div>
      </header>
      <div id="app-main"></div>
      <nav class="app-nav"><div class="main-nav" id="main-nav"></div></nav>`;
    this.renderNav();
  },

  navItems() {
    return [
      { k: 'home', ico: '✨', t: 'Сегодня' },
      { k: 'hub', ico: '🪐', t: 'Агенты' },
      { k: 'profile', ico: '🌙', t: 'Профиль' },
    ];
  },
  renderNav() {
    const active = this.chat.key ? 'hub' : this.view;
    document.getElementById('main-nav').innerHTML = this.navItems().map(n => `
      <button class="nav-btn ${active === n.k ? 'active' : ''}" data-act="go" data-goto="${n.k}">
        <span class="nav-ico">${n.ico}</span><span>${n.t}</span>
      </button>`).join('');
  },
  go(v) {
    if (v === 'chat') v = 'hub';
    if (v !== 'hub') this.chat.key = null;
    this.view = v;
    this.renderNav();
    const main = document.getElementById('app-main');
    if (v === 'home') this.renderHome(main);
    else if (v === 'hub') this.renderHub(main);
    else if (v === 'profile') { this.renderProfile(main); }
  },

  scrollToBottom() {
    const box = document.querySelector('.chat-messages, .screen');
    if (box) box.scrollTop = box.scrollHeight;
  },

  /* ── данные ── */
  async loadAgents() {
    try { this.agents = await api('/api/agents'); } catch (e) { this.agents = []; }
    if (this.view === 'hub') this.renderHub(document.getElementById('app-main'));
    if (this.view === 'home') this.renderHome(document.getElementById('app-main'));
  },
  async loadToday() {
    try { this.today = await api('/api/today'); } catch (e) { this.today = null; }
    if (this.view === 'home') this.renderHome(document.getElementById('app-main'));
  },

  agentSpec(key) {
    const a = this.agents.find(x => x.code === key);
    return a || { code: key, name: key, emoji: '✦', accent: '#e6c178' };
  },

  /* ═══ ЭКРАН «СЕГОДНЯ» — статичная база ═══ */
  renderHome(main) {
    const t = this.today;
    main.innerHTML = `
      <div class="screen">
        <div class="hero-orb">
          <div class="orb"></div>
          <div style="position:relative;z-index:2">
            <div class="hero-date">${fmtDate()}</div>
            <div style="font-family:var(--font-serif);font-size:24px;font-weight:700;letter-spacing:.5px">Твой день, ${this.me && this.me.name ? esc(this.me.name.split(' ')[0]) : 'милая'}</div>
            <div style="color:var(--text-dim);font-size:12.5px;margin-top:6px">Луна ${t ? `${t.moon.emoji} ${t.moon.name} · ${t.moon.day}-й день` : '…'}</div>
          </div>
        </div>

        <div class="spacer"></div>
        <div class="section-title">✨ Прогноз на сегодня</div>
        <div class="glass" style="padding:16px;font-size:13.8px;line-height:1.65">
          ${t ? esc(t.forecast) : '<div class="skeleton" style="height:90px;border-radius:12px"></div>'}
        </div>

        ${t && t.card ? `
        <div class="spacer"></div>
        <div class="section-title">🂠 Карта дня</div>
        <div class="card-day">
          <div class="cd-row">
            <div class="cd-emoji">${t.card.emoji}</div>
            <div>
              <div style="font-family:var(--font-serif);color:var(--gold-bright);font-size:15px">${esc(t.card.name)}</div>
              <div style="color:var(--text-dim);font-size:12.5px;margin-top:3px">${esc(t.card.meaning)}</div>
            </div>
          </div>
        </div>` : ''}

        <div class="spacer"></div>
        <div class="section-title">🪐 Твои агенты</div>
        <div class="agent-dock">
          ${this.agents.length ? this.agents.map(a => `
            <div class="dock-chip" data-act="chat" data-chat="${a.code}">
              <div class="dock-orb" style="--ac:${esc(a.accent || '#e6c178')}">${a.emoji}</div>
              <div>${esc(a.name.split(' ')[0])}</div>
            </div>`).join('') : '<div class="skeleton" style="height:74px;border-radius:16px;flex:1"></div>'}
        </div>
        <div style="color:var(--text-faint);font-size:11.5px;text-align:center;margin-top:6px">Открой агента — задай вопрос или используй его функцию прямо в чате</div>
      </div>`;
  },

  /* ═══ ХАБ АГЕНТОВ ═══ */
  renderHub(main) {
    if (this.chat.key) return this.renderChat(main);
    const list = this.agents.length ? this.agents : [
      { code: 'oracle', name: 'Лилит', title: 'Личный Оракул', emoji: '🔮', accent: '#e8c56b' },
      { code: 'astro', name: 'Урания', title: 'Астролог', emoji: '🌌', accent: '#7fb4e8' },
      { code: 'tarot', name: 'Мадам Ленорман', title: 'Таролог', emoji: '🎴', accent: '#c58bd8' },
      { code: 'numero', name: 'Пифия', title: 'Нумеролог', emoji: '🔢', accent: '#e8a87f' },
    ];
    main.innerHTML = `
      <div class="screen">
        <div class="hub-head">
          <h1>Твой Оракул</h1>
          <p>Чат — главный инструмент. Выбери агента: задай вопрос или нажми его функцию.</p>
        </div>
        <div class="agent-list">
          ${list.map(a => `
            <div class="agent-card" style="--ac:${esc(a.accent || '#e6c178')}" data-act="chat" data-chat="${a.code}">
              <div class="ac-top">
                <div class="agent-avatar">${a.emoji}</div>
                <div style="flex:1;min-width:0">
                  <div class="agent-title">${esc(a.name)}</div>
                  <div class="agent-role">${esc(a.title || a.code)}</div>
                  <div class="agent-last">${esc(a.last_text || a.tagline || '')}</div>
                </div>
                <span style="color:var(--text-faint);font-size:18px">›</span>
              </div>
              <div class="agent-chips">
                ${(FEATURES[a.code] || []).slice(0, 4).map(f => `
                  <span class="chip" style="--ac2:${esc(a.accent || '#e6c178')}" data-act="chat-fn" data-chat="${a.code}" data-fn="${f.h}">
                    <span class="c-emoji">${f.e}</span>${f.t}
                  </span>`).join('')}
              </div>
            </div>`).join('')}
        </div>
      </div>`;
  },

  /* ═══ ЧАТ — ГЛАВНЫЙ ИНСТРУМЕНТ ═══ */
  openChat(key, after) {
    if (this.chat.key !== key) {
      this.chat.key = key;
      this.chat.spec = this.agentSpec(key);
      this.chat.messages = [];
      this.chat.pending = null;
      this.loadThread(key);
    }
    this.view = 'hub';
    this.renderNav();
    this.renderChat(document.getElementById('app-main'));
    if (after) setTimeout(after, 60);
  },

  async loadThread(key) {
    try {
      const r = await api('/api/chat/' + key);
      this.chat.spec = r.agent;
      this.chat.messages = (r.messages || []).map(m => ({ role: m.role, text: m.text }));
    } catch (e) {
      this.chat.messages = [{ role: 'assistant', text: '😔 Связь прервалась. Попробуй ещё раз.' }];
    }
    if (this.chat.key === key) this.renderChat(document.getElementById('app-main'));
  },

  renderChat(main) {
    const a = this.chat.spec;
    const messages = this.chat.messages;
    const busy = this.chat.busy;
    const pending = this.chat.pending;
    const features = FEATURES[a.code] || [];
    const suggest = (a.suggestions || []).slice(0, 3);

    const body = messages.map(m =>
      `<div class="msg ${m.role === 'user' ? 'user' : 'assistant'}">${rich(m.text)}</div>`).join('');

    const pendHtml = pending ? this.pendingHtml(pending) : '';

    main.innerHTML = `
      <div class="chat-shell">
        <div class="chat-head">
          <button class="back" data-act="back">‹</button>
          <div class="agent-avatar" style="--ac:${esc(a.accent || '#e6c178')}">${a.emoji}</div>
          <div style="flex:1;min-width:0">
            <div class="cname">${esc(a.name)}</div>
            <div class="tsub">${esc(a.title || a.role || '')}</div>
          </div>
          <span style="color:var(--text-faint);font-size:12px" data-act="clear">↺</span>
        </div>
        ${features.length ? `
        <div class="chat-features">
          ${features.map(f => `
            <span class="chip" data-act="feature" data-fn="${f.h}"><span class="c-emoji">${f.e}</span>${f.t}</span>`).join('')}
        </div>` : ''}
        <div class="chat-messages" id="chat-messages">
          ${body}
          ${pendHtml}
          ${busy ? `<div class="msg assistant"><div class="typing"><span></span><span></span><span></span></div></div>` : ''}
        </div>
        <div class="composer">
          <div class="composer-top">
            <input class="ipt" id="chat-input" placeholder="Спроси ${esc(a.name)}…" autocomplete="off"/>
            <button class="send-btn" id="send-btn" data-act="send">➤</button>
          </div>
          ${suggest.length ? `
          <div class="suggest-chips">
            ${suggest.map(s => `<span class="chip" data-act="send" data-val="${esc(s)}">${esc(s)}</span>`).join('')}
          </div>` : ''}
        </div>
      </div>`;
    this.scrollToBottom();
  },

  pendingHtml(p) {
    const q = s => esc(s).replace(/'/g, "&#39;");
    switch (p.kind) {
      case 'tarot-pick':
        return `<div class="msg assistant">
          Давай сделаем расклад. Сначала выбери схему и <b>напиши свой вопрос картам</b> — чем точнее, тем яснее ответ.
          <div class="chat-widget">
            <div class="w-title">Схема расклада</div>
            <div class="spread-grid">${p.spreads.map(s => `
              <div class="spread-cell ${p.spread === s.code ? 'sel' : ''} ${s.tier === 'premium' ? 'premium' : ''}"
                   data-code="${s.code}" data-act="spread" data-spread="${s.code}">
                ${s.tier === 'premium' ? '<span class="lock">🔒</span>' : ''}
                <span class="se">${s.emoji}</span>
                <span class="sn">${esc(s.title)}</span>
              </div>`).join('')}
            </div>
            <textarea class="ipt" id="tarot-q" rows="2" placeholder="Твой вопрос к картам…"
              style="margin-top:10px;resize:none">${q(p.q || '')}</textarea>
            <button class="btn btn-primary" style="margin-top:10px" data-act="draw">Потянула карты 🎴</button>
          </div></div>`;

      case 'tarot-cards':
        return `<div class="msg assistant">
          Карты вытянуты. Твой вопрос: <b>«${esc(p.question)}»</b>
          <div class="chat-widget">
            ${p.positions.map((pos, i) => `
              <div class="card-spot-label">${esc(pos)}</div>
              <div class="tarot-zone">
                <div class="tarot-card ${p.revealed[i] ? 'flipped' : ''}" data-act="flip" data-i="${i}">
                  <div class="face back"><div class="motif">☾</div><div class="lf">ORACLE</div></div>
                  <div class="face front">
                    <div class="fe">${p.cards[i].emoji}${p.cards[i].reversed ? ' ↺' : ''}</div>
                    <div class="fn">${esc(p.cards[i].name)}</div>
                    <div class="fp">${esc(p.cards[i].meaning)}</div>
                  </div>
                </div>
              </div>`).join('')}
            ${p.allRevealed ? `
              <button class="btn btn-primary" style="margin-top:12px" data-act="interpret">Что это значит для меня?</button>`
              : `<div style="text-align:center;color:var(--text-faint);font-size:11.5px;margin-top:10px">Нажми на карты, чтобы перевернуть ✨</div>`}
          </div></div>`;

      case 'chart':
        return `<div class="msg assistant">
          ${p.loading ? '<div class="typing"><span></span><span></span><span></span></div>' : ''}
          <div class="chat-widget">${p.html}</div>
        </div>`;

      case 'compat':
        return `<div class="msg assistant">
          Расскажи, кто твой партнёр — и я разложу вашу совместимость по картам.
          <div class="chat-widget">
            <input class="ipt" id="cp-name" placeholder="Имя (необязательно)" style="margin-bottom:8px"/>
            <input class="ipt" id="cp-date" placeholder="Дата рождения партнёра · ГГГГ-ММ-ДД" style="margin-bottom:8px"/>
            <button class="btn btn-primary" data-act="compat">Проверить совместимость 💞</button>
          </div></div>`;

      case 'moon':
        return `<div class="msg assistant">
          <div class="chat-widget">
            <div class="w-title">🌙 Лунная неделя</div>
            ${p.loading ? '<div class="loader-ring"></div>' : p.rows}
          </div></div>`;

      case 'matrix':
        return `<div class="msg assistant">
          <div class="chat-widget">
            <div class="w-title">🔢 Матрица Судьбы</div>
            ${p.loading ? '<div class="loader-ring"></div>' : p.rows}
          </div></div>`;

      case 'today':
        return `<div class="msg assistant">
          ${p.loading ? '<div class="typing"><span></span><span></span><span></span></div>' : esc(p.forecast)}
        </div>`;

      case 'history':
        return `<div class="msg assistant">
          <div class="chat-widget">
            <div class="w-title">📚 Твои расклады</div>
            ${p.loading ? '<div class="loader-ring"></div>' : (p.rows || '<div style="color:var(--text-faint);font-size:12.5px">Пока пусто — первый расклад ждёт тебя ✨</div>')}
          </div></div>`;

      default: return '';
    }
  },

  closeChat() {
    this.chat.key = null;
    this.go('hub');
  },
  async clearThread() {
    const key = this.chat.key;
    if (!confirm('Начать новый чат с чистого листа?')) return;
    try { await api('/api/chat/' + key, { method: 'DELETE' }); } catch (e) {}
    this.chat.messages = [];
    this.chat.pending = null;
    this.renderChat(document.getElementById('app-main'));
  },

  /* ── отправка вопроса агенту ── */
  async doSend(text) {
    const a = this.chat.spec;
    const val = (text || (document.getElementById('chat-input') || {}).value || '').trim();
    if (!val || this.chat.busy) return;
    const input = document.getElementById('chat-input');
    if (input) input.value = '';
    this.chat.messages.push({ role: 'user', text: val });
    this.chat.busy = true;
    this.renderChat(document.getElementById('app-main'));
    try {
      const r = await api('/api/chat/' + a.code, { method: 'POST', body: JSON.stringify({ text: val }) });
      this.chat.messages.push({ role: 'assistant', text: r.answer });
    } catch (e) {
      this.chat.messages.push({ role: 'assistant', text: '😔 ' + e.message });
    }
    this.chat.busy = false;
    this.renderChat(document.getElementById('app-main'));
  },

  /* ═══ ФИЧА: РАСКЛАД ТАРО (вопрос → карты → LLM) ═══ */
  async featureTarot() {
    if (this.chat.pending && this.chat.pending.kind.startsWith('tarot')) return;
    this.chat.pending = { kind: 'tarot-pick', spreads: [], spread: 'three', q: '' };
    this.renderChat(document.getElementById('app-main'));
    try {
      this.spreads = this.spreads || await api('/api/tarot/spreads');
      this.chat.pending.spreads = this.spreads;
    } catch (e) {
      this.chat.pending.spreads = [
        { code: 'one', title: 'Одна карта', emoji: '🂠', tier: 'included' },
        { code: 'three', title: 'Прошлое·Наст·Будущее', emoji: '🂠🂠🂠', tier: 'included' },
        { code: 'love', title: 'На отношения', emoji: '💞', tier: 'included' },
      ];
    }
    this.renderChat(document.getElementById('app-main'));
  },

  pendingQ(v) { if (this.chat.pending) this.chat.pending.q = v; },

  pickSpread(code) {
    if (!this.chat.pending || !this.chat.pending.spreads) return;
    this.chat.pending.spread = code;
    document.querySelectorAll('.spread-cell').forEach(el => el.classList.toggle('sel', el.dataset.code === code));
  },

  async doDraw() {
    const q = (document.getElementById('tarot-q') || {}).value;
    const qv = (q || '').trim();
    if (!qv) { alert('Сформулируй свой вопрос картам — я передам его в расклад'); return; }
    const spread = this.chat.pending.spread || 'three';
    this.chat.busy = true;
    this.chat.pending = { kind: 'tarot-pick', spreads: this.chat.pending.spreads, spread, q: qv };
    this.renderChat(document.getElementById('app-main'));
    try {
      const r = await api('/api/tarot/draw?spread=' + spread, {
        method: 'POST',
        body: JSON.stringify({ question: qv }),
      });
      this.chat.messages.push({ role: 'user', text: 'Мой вопрос к картам: ' + qv });
      this.chat.pending = {
        kind: 'tarot-cards', question: qv, cards: r.cards,
        positions: r.positions, revealed: r.cards.map(() => false),
        allRevealed: false, reading_id: r.reading_id,
      };
    } catch (e) {
      this.chat.pending = null;
      this.chat.messages.push({ role: 'assistant', text: '😔 ' + e.message });
    }
    this.chat.busy = false;
    this.renderChat(document.getElementById('app-main'));
  },

  flipCard(i) {
    const p = this.chat.pending;
    if (!p || p.kind !== 'tarot-cards') return;
    p.revealed[i] = true;
    p.allRevealed = p.revealed.every(Boolean);
    this.renderChat(document.getElementById('app-main'));
  },

  async doInterpret() {
    const p = this.chat.pending;
    if (!p || p.kind !== 'tarot-cards') return;
    this.chat.busy = true;
    this.renderChat(document.getElementById('app-main'));
    try {
      const r = await api('/api/tarot/interpret/' + p.reading_id, { method: 'POST' });
      this.chat.messages.push({ role: 'assistant', text: r.answer });
    } catch (e) {
      this.chat.messages.push({ role: 'assistant', text: '😔 ' + e.message });
    }
    this.chat.pending = null;
    this.chat.busy = false;
    this.renderChat(document.getElementById('app-main'));
  },

  async featureTarotHistory() {
    this.chat.pending = { kind: 'history', loading: true };
    this.renderChat(document.getElementById('app-main'));
    try {
      const rows = await api('/api/tarot/history');
      this.chat.pending = {
        kind: 'history', loading: false,
        rows: rows.map(r => `
          <div class="result-card" style="margin-bottom:8px" data-act="reading" data-id="${r.id}">
            <div class="rc-top">
              <span style="font-size:18px">${r.cards && r.cards[0] ? r.cards[0].emoji : '🎴'}</span>
              <div style="flex:1;min-width:0">
                <div class="rc-title">${esc(r.question || 'Расклад')}</div>
                <div class="rc-meta">${fmtDay(r.created_at.slice(0, 10))} · ${esc(r.spread || '')}</div>
              </div>
              <span class="rc-open">›</span>
            </div>
          </div>`).join(''),
      };
    } catch (e) {
      this.chat.pending = { kind: 'history', loading: false, rows: '<div style="color:var(--text-faint)">' + esc(e.message) + '</div>' };
    }
    this.renderChat(document.getElementById('app-main'));
  },

  /* ═══ ФИЧА: НАТАЛЬНАЯ КАРТА → строится и сохраняется в профиль ═══ */
  async featureChart() {
    if (this.chat.pending && this.chat.pending.kind === 'chart') return;
    this.chat.pending = { kind: 'chart', loading: true, html: '' };
    this.renderChat(document.getElementById('app-main'));
    try {
      const c = await api('/api/chart');
      this.chat.pending = { kind: 'chart', loading: false, html: this.chartHtml(c) };
    } catch (e) {
      // карты ещё нет — даём собрать её прямо здесь (время и город)
      this.chart = null;
      this.chat.pending = { kind: 'chart', loading: false, html: this.chartForm() };
    }
    this.renderChat(document.getElementById('app-main'));
  },

  chartHtml(c) {
    this.chart = c;
    const sun = c.sun || {};
    const asc = c.ascendant || {};
    const planets = c.planets || [];
    const glyph = p => (p.sign ? SIGNS[p.sign] : '');
    const lines = planets.map(p => `
      <div class="planet-line">
        <div class="p-ico">${glyph(p)}</div>
        <div class="p-name">${esc(p.name)}</div>
        <div class="p-val">${esc(p.sign)}${p.house ? ' · дом ' + p.house : ''}${p.retro ? ' ☍' : ''}</div>
      </div>`).join('');
    return `
      <div class="w-title">🌌 Натальная карта</div>
      <div class="chart-wheel" style="width:130px;height:130px;margin:4px auto 12px">
        <div class="wheel-center">
          <div class="wc-s">${sun.symbol || '☉'}</div>
          <div class="wc-t">${esc(sun.sign || '')}</div>
          <div class="wc-t" style="font-size:10px;color:var(--text-dim)">AC ${esc((asc.sign || '').slice(0, 3))}</div>
        </div>
      </div>
      <div style="font-family:var(--font-serif);color:var(--gold-bright);font-size:13px;margin-bottom:8px">Солнце в ${esc(sun.sign || '—')} · Асцендент ${esc(asc.sign || '—')}</div>
      <div>${lines || '<div style="color:var(--text-faint);font-size:12.5px">Планеты ещё не рассчитаны</div>'}</div>
      <div style="color:var(--text-faint);font-size:11.5px;margin:10px 0">✓ Сохранена в твоём профиле — всегда под рукой.</div>
      <div style="display:flex;gap:8px;margin-top:6px">
        <button class="btn btn-primary" style="flex:1" data-act="ask-chart">Спросить про карту</button>
        <button class="btn btn-ghost" data-act="go" data-goto="profile">В профиль</button>
      </div>`;
  },

  chartForm() {
    const me = this.me || {};
    return `
      <div class="w-title">🌌 Построить натальную карту</div>
      <div style="color:var(--text-dim);font-size:12.5px;margin-bottom:10px">
        Дата рождения: <b style="color:var(--text)">${esc(me.birth_date || '—')}</b>. Уточни время и город — и я рассчитаю карту прямо здесь.
      </div>
      <input class="ipt" id="ch-time" placeholder="Время рождения · 14:30 (если не знаешь — пусто)" style="margin-bottom:8px"/>
      <input class="ipt" id="ch-city" placeholder="Город рождения · Москва" style="margin-bottom:8px"/>
      <button class="btn btn-primary" data-act="build">Рассчитать карту ✨</button>`;
  },

  async doBuildChart() {
    const time = (document.getElementById('ch-time') || {}).value || '';
    const city = (document.getElementById('ch-city') || {}).value || '';
    this.chat.busy = true;
    this.chat.pending = { kind: 'chart', loading: true, html: '' };
    this.renderChat(document.getElementById('app-main'));
    try {
      const c = await api('/api/chart', {
        method: 'POST',
        body: JSON.stringify({ birth_time: time.trim() || null, birth_city: city.trim() || null }),
      });
      this.chat.pending = { kind: 'chart', loading: false, html: this.chartHtml(c) };
    } catch (e) {
      this.chat.pending = { kind: 'chart', loading: false, html: '<div style="color:#ff9e9e;font-size:13px">😔 ' + esc(e.message) + '</div>' };
    }
    this.chat.busy = false;
    this.renderChat(document.getElementById('app-main'));
  },

  chatAsk(text) {
    if (!text || !text.trim()) return;
    this.chat.messages.push({ role: 'user', text });
    this.chat.busy = true;
    this.renderChat(document.getElementById('app-main'));
    api('/api/chat/' + this.chat.key, { method: 'POST', body: JSON.stringify({ text }) })
      .then(r => { this.chat.messages.push({ role: 'assistant', text: r.answer }); })
      .catch(e => { this.chat.messages.push({ role: 'assistant', text: '😔 ' + e.message }); })
      .finally(() => { this.chat.busy = false; this.renderChat(document.getElementById('app-main')); });
  },

  // Вопрос по натальной карте из виджета — prompt вынесен из inline-хендлера.
  askChart() {
    const q = prompt('О чём спросить карту?', 'моих отношениях');
    if (q && q.trim()) this.chatAsk('Что в моей натальной карте говорит о ' + q.trim());
  },

  /* ═══ ФИЧА: ПРОГНОЗ / НЕБО ═══ */
  async featureToday() {
    if (this.chat.pending && this.chat.pending.kind === 'today') return;
    this.chat.pending = { kind: 'today', loading: true, forecast: '' };
    this.renderChat(document.getElementById('app-main'));
    try {
      const t = await api('/api/today');
      this.chat.pending = { kind: 'today', loading: false,
        forecast: `🌅 ${fmtDate()}\n\n${t.forecast}\n\n🂠 Карта дня: ${t.card.emoji} ${t.card.name} — ${t.card.meaning}` };
    } catch (e) {
      this.chat.pending = { kind: 'today', loading: false, forecast: '😔 ' + e.message };
    }
    this.renderChat(document.getElementById('app-main'));
  },

  /* ═══ ФИЧА: ЛУННАЯ НЕДЕЛЯ ═══ */
  async featureMoon() {
    this.chat.pending = { kind: 'moon', loading: true, rows: '' };
    this.renderChat(document.getElementById('app-main'));
    try {
      const days = await api('/api/moon/week');
      const wd = ['пн', 'вт', 'ср', 'чт', 'пт', 'сб', 'вс'];
      this.chat.pending = { kind: 'moon', loading: false, rows: days.map(d => `
        <div class="planet-line">
          <div class="p-ico">${d.emoji}</div>
          <div class="p-name">${d.date.slice(8)} ${wd[d.weekday]} · ${d.name}</div>
          <div class="p-val" style="font-size:11.5px">${d.day}-й день</div>
        </div>`).join('') };
    } catch (e) {
      this.chat.pending = { kind: 'moon', loading: false, rows: '<div style="color:var(--text-faint)">' + esc(e.message) + '</div>' };
    }
    this.renderChat(document.getElementById('app-main'));
  },

  /* ═══ ФИЧА: МАТРИЦА ═══ */
  async featureMatrix() {
    this.chat.pending = { kind: 'matrix', loading: true, rows: '' };
    this.renderChat(document.getElementById('app-main'));
    try {
      const m = await api('/api/matrix');
      const keys = [['personal', 'Личный'], ['destiny', 'Судьба'], ['love', 'Любовь'], ['money', 'Деньги']];
      this.chat.pending = { kind: 'matrix', loading: false, rows: keys.map(([k, label]) => {
        const a = m[k] || {};
        return `<div class="planet-line">
          <div class="p-ico">${a.arcana ? '✦' : '·'}</div>
          <div class="p-name">${label} · ${esc(a.arcana || '—')}</div>
          <div class="p-val" style="font-size:11.5px">${a.n != null ? a.n : ''}</div>
        </div>`;
      }).join('') + `<div style="font-size:11.5px;color:var(--text-faint);margin-top:10px">Попроси агента разобрать твои арканы подробнее — просто напиши ему.</div>` };
    } catch (e) {
      this.chat.pending = { kind: 'matrix', loading: false, rows: '<div style="color:var(--text-faint)">' + esc(e.message) + '</div>' };
    }
    this.renderChat(document.getElementById('app-main'));
  },

  /* ═══ ФИЧА: СОВМЕСТИМОСТЬ ═══ */
  featureCompat() {
    if (this.chat.pending && this.chat.pending.kind === 'compat') return;
    this.chat.pending = { kind: 'compat' };
    this.renderChat(document.getElementById('app-main'));
  },
  async doCompat() {
    const name = ((document.getElementById('cp-name') || {}).value || '').trim();
    const date = ((document.getElementById('cp-date') || {}).value || '').trim();
    if (!date) { alert('Введи дату рождения партнёра'); return; }
    this.chat.busy = true;
    this.chat.pending = null;
    this.renderChat(document.getElementById('app-main'));
    try {
      const r = await api('/api/compat/full', { method: 'POST', body: JSON.stringify({ partner_date: date, partner_name: name, save: true }) });
      this.chat.messages.push({ role: 'user', text: 'Моя совместимость с ' + (name || 'партнёром') + ' (' + date + ')' });
      this.chat.messages.push({ role: 'assistant', text: r.answer });
    } catch (e) {
      this.chat.messages.push({ role: 'assistant', text: '😔 ' + e.message });
    }
    this.chat.busy = false;
    this.renderChat(document.getElementById('app-main'));
  },

  /* ═══ ФИЧИ-ВОПРОСЫ (агент решает сам, по скиллам) ═══ */
  chatPractice() { this.doSend('Подбери мне практику под моё состояние — расскажи, зачем она мне и с чего начать.'); },
  chatMonthly() { this.doSend('Подведи итог моего месяца: что менялось, что повторялось, на что обратить внимание.'); },

  /* ═══ ПРОФИЛЬ: данные + натальная карта + расклады + отчёты ═══ */
  async renderProfile(main) {
    const me = this.me;
    main.innerHTML = `
      <div class="screen">
        <div class="hub-head">
          <h1>Профиль</h1>
          <p>Твоё небо и сохранённое</p>
        </div>
        <div class="stat-row">
          <div class="stat"><div class="sv">${me ? (me.sub_active ? '∞' : '—') : '…'}</div><div class="sl">Подписка</div></div>
          <div class="stat"><div class="sv">${me ? me.crystals : '…'}</div><div class="sl">Кристаллы ✦</div></div>
          <div class="stat"><div class="sv">${me ? me.allowance.left : '…'}</div><div class="sl">Вопросы</div></div>
          <div class="stat"><div class="sv">${me ? (me.diary_streak || 0) : '…'}</div><div class="sl">Дневник·дн</div></div>
        </div>

        <div class="spacer"></div>
        <div class="section-title">👤 Твои данные</div>
        <div class="glass" style="padding:14px 16px;font-size:13px">
          <div class="planet-line"><div class="p-ico">🗓</div><div class="p-name">Рождение</div><div class="p-val">${me ? esc(me.birth_date || '—') : '…'}</div></div>
          <div class="planet-line"><div class="p-ico">⏰</div><div class="p-name">Время</div><div class="p-val">${me ? esc(me.birth_time_known ? me.birth_time : 'не известно') : '…'}</div></div>
          <div class="planet-line"><div class="p-ico">🏙</div><div class="p-name">Город</div><div class="p-val">${me ? esc(me.birth_city || '—') : '…'}</div></div>
        </div>

        <div class="spacer"></div>
        <div class="section-title">🌌 Натальная карта</div>
        <div id="profile-chart"><div class="glass"><div class="center-block"><div class="loader-ring"></div></div></div></div>

        <div class="spacer"></div>
        <div class="section-title">🎴 Последние расклады</div>
        <div id="profile-tarot"><div class="skeleton" style="height:80px;border-radius:16px"></div></div>

        <div class="spacer"></div>
        <div class="section-title">📜 Разборы</div>
        <div id="profile-reports"><div class="skeleton" style="height:60px;border-radius:16px"></div></div>

        <div class="spacer"></div>
        <div class="section-title">🧠 Что я помню о тебе</div>
        <div id="profile-memories"><div class="skeleton" style="height:60px;border-radius:16px"></div></div>
      </div>`;
    this.loadProfileSections();
  },

  async loadProfileSections() {
    const chartEl = document.getElementById('profile-chart');
    const tarotEl = document.getElementById('profile-tarot');
    const repEl = document.getElementById('profile-reports');
    const memEl = document.getElementById('profile-memories');

    // натальная карта (по возможности — из /api/me, иначе /api/chart)
    try {
      const c = await api('/api/chart');
      const sun = c.sun || {}, asc = c.ascendant || {};
      const planets = (c.planets || []).slice(0, 8).map(p => `
        <div class="planet-line">
          <div class="p-ico">${SIGNS[p.sign] || ''}</div>
          <div class="p-name">${esc(p.name)}</div>
          <div class="p-val">${esc(p.sign)}${p.house ? ' · ' + p.house : ''}</div>
        </div>`).join('');
      if (chartEl) chartEl.innerHTML = `
        <div class="glass" style="padding:16px">
          <div style="display:flex;align-items:center;gap:16px">
            <div class="chart-wheel" style="width:110px;height:110px">
              <div class="wheel-center"><div class="wc-s">${sun.symbol || '☉'}</div><div class="wc-t">${esc(sun.sign || '')}</div></div>
            </div>
            <div style="flex:1;font-size:13px">
              <div style="font-family:var(--font-serif);color:var(--gold-bright);font-size:14.5px">${esc(sun.sign || '—')}</div>
              <div style="color:var(--text-dim);font-size:12px">Асцендент ${esc(asc.sign || '—')}</div>
              <div style="margin-top:10px;display:flex;gap:8px">
                <button class="btn btn-ghost" style="padding:8px 12px;font-size:12px" data-act="chat" data-chat="astro">Спросить</button>
                <button class="btn btn-ghost" style="padding:8px 12px;font-size:12px" data-act="report" data-kind="natal">Разбор</button>
              </div>
            </div>
          </div>
          <div style="margin-top:10px">${planets}</div>
        </div>`;
    } catch (e) {
      if (chartEl) chartEl.innerHTML = `
        <div class="glass" style="padding:16px;text-align:center">
          <div style="font-size:34px">🌌</div>
          <div style="font-size:13.5px;margin:8px 0 12px">Карта ещё не построена.<br>Собери её у Астролога — прямо в чате.</div>
          <button class="btn btn-primary" data-act="chat" data-chat="astro">Построить карту</button>
        </div>`;
    }

    try {
      const rows = await api('/api/tarot/history');
      if (tarotEl) tarotEl.innerHTML = rows.length ? rows.slice(0, 5).map(r => `
        <div class="result-card" style="margin-bottom:8px" data-act="reading" data-id="${r.id}">
          <div class="rc-top">
            <span style="font-size:16px">${r.cards && r.cards[0] ? r.cards[0].emoji : '🎴'}</span>
            <div style="flex:1;min-width:0">
              <div class="rc-title" style="font-size:13px">${esc(r.question || 'Расклад')}</div>
              <div class="rc-meta">${fmtDay(r.created_at.slice(0, 10))} · ${esc(r.spread || '')}</div>
            </div>
            <span class="rc-open">›</span>
          </div>
        </div>`).join('') : '<div class="glass" style="padding:16px;color:var(--text-faint);font-size:13px">Раскладов пока нет — зайди к Тарологу и задай вопрос картам.</div>';
    } catch (e) { if (tarotEl) tarotEl.innerHTML = ''; }

    try {
      const rep = await api('/api/reports');
      const ready = rep.ready || [];
      if (repEl) repEl.innerHTML = ready.length ? ready.map(r => `
        <div class="result-card" style="margin-bottom:8px" data-act="report" data-kind="${esc(r.kind)}">
          <div class="rc-top">
            <span style="font-size:16px">📜</span>
            <div style="flex:1;min-width:0"><div class="rc-title" style="font-size:13px">${esc(r.title)}</div>
            <div class="rc-meta">${r.period || fmtDay((r.created_at || '').slice(0, 10))}</div></div>
            <span class="rc-open">›</span>
          </div>
        </div>`).join('') : '<div class="glass" style="padding:16px;color:var(--text-faint);font-size:13px">Разборов пока нет — они появляются в лавке.</div>';
    } catch (e) { if (repEl) repEl.innerHTML = ''; }

    if (this.me && this.me.memories && this.me.memories.length) {
      if (memEl) memEl.innerHTML = `<div class="glass" style="padding:14px 16px">${this.me.memories.map(m => `<div style="font-size:12.5px;padding:3px 0;color:var(--text-dim)">✦ ${esc(m)}</div>`).join('')}</div>`;
    } else if (memEl) memEl.innerHTML = '<div class="glass" style="padding:16px;color:var(--text-faint);font-size:13px">Я запомню о тебе важное, когда расскажешь.</div>';
  },

  async openReport(kind) {
    try {
      const r = await api('/api/reports/' + kind);
      this.showModal(`<h3>${esc(r.title)}</h3><button class="m-close" data-act="modal-close">✕</button><div style="font-size:13.5px;line-height:1.65;margin-top:8px">${rich(r.body)}</div>`);
    } catch (e) { alert(e.message); }
  },

  async openReading(id) {
    try {
      const rows = await api('/api/tarot/history');
      const r = rows.find(x => x.id === id) || rows[0];
      const cards = (r.cards || []).map(c => `${c.emoji} ${c.name}${c.reversed ? ' ↺' : ''} — ${c.meaning}`).join('\n');
      this.showModal(`<h3>🎴 ${esc(r.question || 'Расклад')}</h3><button class="m-close" data-act="modal-close">✕</button>
        <div style="font-size:12px;color:var(--text-dim);white-space:pre-wrap;margin:8px 0">${esc(cards)}</div>
        <div style="font-size:13.5px;line-height:1.65;white-space:pre-wrap">${esc(r.answer || '—')}</div>`);
    } catch (e) { alert(e.message); }
  },

  showModal(html) {
    const ov = document.createElement('div');
    ov.className = 'modal-overlay';
    ov.id = 'app-modal';
    ov.innerHTML = `<div class="modal">${html}</div>`;
    ov.addEventListener('click', e => { if (e.target === ov) ov.remove(); });
    document.body.appendChild(ov);
  },
  closeModal() { const el = document.getElementById('app-modal'); if (el) el.remove(); },
};

const SIGNS = {
  Овен: '♈', Телец: '♉', Близнецы: '♊', Рак: '♋', Лев: '♌', Дева: '♍',
  Весы: '♎', Скорпион: '♏', Стрелец: '♐', Козерог: '♑', Водолей: '♒', Рыбы: '♓',
};

window.app = app;

/* ── прод-CSP: вместо inline onclick/oninput/onkeydown — делегирование ──
   data-act на элементе + один обработчик на документе. Вложенные [data-act]
   (чип внутри карточки) берёт ближайший — отдельный stopPropagation не нужен. */
document.addEventListener('click', e => {
  const el = e.target && e.target.closest ? e.target.closest('[data-act]') : null;
  if (!el) return;
  const act = el.dataset.act, v = el.dataset;
  switch (act) {
    case 'go': app.go(v.goto); break;
    case 'chat': app.openChat(v.chat); break;
    case 'chat-fn': app.openChat(v.chat, () => app[v.fn] && app[v.fn]()); break;
    case 'back': app.closeChat(); break;
    case 'clear': app.clearThread(); break;
    case 'feature': app[v.fn] && app[v.fn](); break;
    case 'send': app.doSend(v.val || undefined); break;
    case 'spread': app.pickSpread(v.spread); break;
    case 'draw': app.doDraw(); break;
    case 'flip': app.flipCard(parseInt(v.i, 10)); break;
    case 'interpret': app.doInterpret(); break;
    case 'compat': app.doCompat(); break;
    case 'reading': app.openReading(parseInt(v.id, 10)); break;
    case 'report': app.openReport(v.kind); break;
    case 'build': app.doBuildChart(); break;
    case 'ask-chart': app.askChart(); break;
    case 'modal-close': app.closeModal(); break;
  }
});
document.addEventListener('keydown', e => {
  if (e.key === 'Enter' && e.target && e.target.id === 'chat-input') app.doSend();
});
document.addEventListener('input', e => {
  if (e.target && e.target.id === 'tarot-q') app.pendingQ(e.target.value);
});

app.boot();