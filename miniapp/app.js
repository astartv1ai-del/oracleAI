/* ============================================================================
   ОРАКУЛ — Mini App, chat-first
   Главный инструмент — чат с ИИ-агентом. У каждого агента — кнопки-функции
   (фичи), которые живут прямо в диалоге: расклад Таро начинается с вопроса,
   натальная карта строится и сохраняется в профиль, всё остальное отвечает
   на вопрос через агента. Домашний экран — статичная база: прогноз дня.
   ============================================================================ */

const tg = () => window.Telegram && window.Telegram.WebApp;

/* haptic-отклик Telegram (безопасно — если WebApp/HapticFeedback нет, молча). */
function haptic(kind) {
  try {
    const H = tg() && tg().HapticFeedback;
    if (!H) return;
    if (kind === 'success') H.notificationOccurred('success');
    else if (kind === 'error') H.notificationOccurred('error');
    else if (kind === 'soft') H.impactOccurred('soft');
    else H.impactOccurred('light');
  } catch (e) {}
}

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
// rich + markdown-жирный **...** → <b> (для ИИ-разборов).
const richMd = s => rich(s).replace(/\*\*(.+?)\*\*/g, '<b>$1</b>');

const fmtDate = () => new Date().toLocaleDateString('ru-RU',
  { weekday: 'long', day: 'numeric', month: 'long' });

const fmtDay = iso => {
  const d = new Date(iso + 'T00:00:00');
  return d.toLocaleDateString('ru-RU', { day: 'numeric', month: 'short' });
};
/* SVG-фаза луны по эмодзи от сервера (🌑…🌘): освещённая доля и терминатор.
   Почти точная визуализация классического цикла без эфемерид. */
const MOON_DISC = {
  '🌑': { lit: 0.0, right: true  },
  '🌒': { lit: 0.22, right: true },
  '🌓': { lit: 0.5, right: true  },
  '🌔': { lit: 0.72, right: true },
  '🌕': { lit: 1.0, right: true  },
  '🌖': { lit: 0.72, right: false },
  '🌗': { lit: 0.5, right: false },
  '🌘': { lit: 0.22, right: false },
};
// Персонаж агента: портрет-арт из /static/img/agents/{code}.jpg + анимированный
// проп-атрибут. cheer=true — персонаж «радуется» свежему ответу агента.
const AGENT_PROPS = {
  oracle: '🔮', astro: '🌠', tarot: '🃏', coach: '🍃', numero: '🌀', keeper: '🪶',
};
function agentSprite(a, cheer) {
  if (!a) return '';
  const ac = a.accent || '#e6c178';
  const prop = AGENT_PROPS[a.code] || a.emoji;
  return `<span class="agent-sprite${cheer ? ' cheer' : ''}" style="--ac:${esc(ac)}" role="img" aria-label="${esc(a.name || '')}">
      <img class="agent-face" src="/static/img/agents/${esc(a.code)}.jpg" alt="${esc(a.name || '')}" loading="eager">
      <span class="as-prop">${esc(prop)}</span>
    </span>`;
}
// арабский номер аркана → римская цифра (для «настоящей» карты)
function toRoman(n) {
  let v = parseInt(n, 10);
  if (!isFinite(v) || v < 0) return String(n || '');
  const map = [[1000,'M'],[900,'CM'],[500,'D'],[400,'CD'],[100,'C'],[90,'XC'],[50,'L'],[40,'XL'],[10,'X'],[9,'IX'],[5,'V'],[4,'IV'],[1,'I']];
  let out = '';
  for (const [num, sym] of map) { while (v >= num) { out += sym; v -= num; } }
  return out || '0';
}
// Истинная фаза луны как SVG: внешняя дуга диска + терминатор-эллипс.
// lit=0 новолуние, 1 полнолуние; right=false — свет слева (убывающая).
// Уникальный id сквозного градиента луны на каждый SVG: несколько лун на странице
// (сегодня/профиль/док) не должны конфликтовать за один #mg, иначе fill не резолвится.
let moonGradSeq = 0;
function moonSvg(emoji, cls) {
  const gid = 'mg' + (++moonGradSeq);
  const ph = MOON_DISC[emoji] || { lit: 0.5, right: true };
  const r = 45, lit = Math.max(0, Math.min(1, ph.lit));
  let d;
  if (lit <= 0) d = '';
  else if (lit >= 1) d = `M0,-${r} A${r} ${r} 0 1 1 0,${r} A${r} ${r} 0 1 1 0,-${r} Z`;
  else {
    const ex = (lit >= 0.5 ? 1 : lit * 2) * r;
    d = `M0,-${r} A${r} ${r} 0 0 1 0,${r} L0,${r} A${ex} ${r} 0 0 1 0,-${r} Z`;
  }
  const flip = ph.right ? '' : ' scale(-1,1)';
  return `<svg viewBox="0 0 100 100" class="${cls || ''}" aria-hidden="true"><defs>
    <radialGradient id="${gid}" cx="45%" cy="38%" r="75%">
      <stop offset="0%" stop-color="#f8edcf"/><stop offset="55%" stop-color="#ddc795"/>
      <stop offset="100%" stop-color="#a9966a"/>
    </radialGradient></defs>
    <circle cx="50" cy="50" r="${r}" fill="#1d1838" stroke="rgba(230,193,120,.35)" stroke-width="2"/>
    ${d ? `<g transform="translate(50,50)${flip}"><path d="${d}" fill="url(#${gid})"/></g>` : ''}</svg>`;
}


/* ── реестр фич-кнопок агентов: chat-first, функции живут в диалоге ────── */
const FEATURES = {
  // Лилит — общий ассистент (всё, кроме Таро: оно у Мадам Ленорман, иначе дубль).
  oracle: [
    { id: 'today', e: '🌅', t: 'Прогноз дня', d: 'Что звёзды и карты готовят тебе сегодня', h: 'featureToday' },
    { id: 'chart', e: '🌌', t: 'Натальная карта', d: 'Построй и разбери карту рождения', h: 'featureChart' },
    { id: 'moon', e: '🌙', t: 'Лунная неделя', d: 'Фазы Луны и лучшие дни недели', h: 'featureMoon' },
    { id: 'compat', e: '💞', t: 'Совместимость', d: 'Твоя связь с человеком — балл и разбор', h: 'featureCompat' },
    { id: 'matrix', e: '🔢', t: 'Матрица Судьбы', d: 'Предназначение и энергии по дате', h: 'featureMatrix' },
  ],
  tarot: [
    { id: 'tar', e: '🎴', t: 'Расклад Таро', d: 'Задай вопрос и вытяни карты', h: 'featureTarot' },
    { id: 'hist', e: '📚', t: 'История', d: 'Твои прошлые расклады', h: 'featureTarotHistory' },
  ],
  astro: [
    { id: 'chart', e: '🌌', t: 'Натальная карта', d: 'Планеты, дома, аспекты рождения', h: 'featureChart' },
    { id: 'today', e: '🔭', t: 'Небо сегодня', d: 'Что происходит сейчас на небе', h: 'featureToday' },
    { id: 'moon', e: '🌙', t: 'Лунная неделя', d: 'Лунный календарь на неделю', h: 'featureMoon' },
    { id: 'compat', e: '💞', t: 'Совместимость', d: 'Разбор вашей пары по датам', h: 'featureCompat' },
  ],
  numero: [
    { id: 'matrix', e: '🔢', t: 'Матрица Судьбы', d: 'Предназначение, деньги, род — по дате', h: 'featureMatrix' },
  ],
  coach: [
    { id: 'practice', e: '🧘', t: 'Подобрать практику', d: 'Мантра или ритуал под твоё состояние', h: 'chatPractice' },
  ],
  keeper: [
    { id: 'monthly', e: '📖', t: 'Итог месяца', d: 'Что менялось и повторялось в дневнике', h: 'chatMonthly' },
  ],
};

/* Богатые шаблоны-промпты по агенту: тап заполняет поле ввода для правки,
   а не отправляет сразу. Длиннее и конкретнее «что меня ждёт в любви». */
const TEMPLATES = {
  oracle: [
    'Что мне сейчас важно понять про себя и мою ситуацию?',
    'Разбери мой день по моей карте: на что обратить внимание?',
    'Я думаю о … — помоги принять решение с точки зрения моей карты.',
  ],
  tarot: [
    'Мой вопрос к картам: …',
    'Стоит ли мне сейчас … ? Разложи, пожалуйста.',
    'Что говорят карты о моих отношениях с … ?',
  ],
  astro: [
    'Что моя натальная карта говорит о моих сильных сторонах?',
    'Объясни мой Асцендент и как меня видят со стороны.',
    'Когда в ближайшие две недели лучше начать важное дело?',
  ],
  numero: [
    'В чём моё предназначение по Матрице Судьбы?',
    'Разбери мою денежную линию — что помогает и что мешает.',
    'Какая у меня родовая задача и как с ней работать?',
  ],
  coach: [
    'Подбери мне практику: хочу больше спокойствия и энергии.',
    'Хочу мантру на … — подскажи, что выбрать и как проходить.',
    'Помоги отпустить … — с чего начать практику?',
  ],
  keeper: [
    'Подведи итог моего месяца: что менялось и что повторялось?',
    'О чём я чаще всего пишу в дневнике и что это значит?',
    'Как я меняюсь последние недели — по моим записям.',
  ],
};

/* ── приложение ─────────────────────────────────────────────────────────── */
const app = {
  me: null, agents: [], today: null, spreads: null,
  view: 'home',
  chat: { key: null, spec: null, messages: [], pending: null, busy: false, tid: null, sessions: [] },

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
        <div style="display:flex;align-items:center;gap:10px">
          <button class="bell" data-act="bell" aria-label="Уведомления">🔔<span class="bell-dot"></span></button>
          <div class="user-pill" data-act="go" data-goto="profile">
            <span class="avatar">${this.me && this.me.name ? esc(this.me.name[0].toUpperCase()) : '✦'}</span>
            ${this.me && this.me.name ? esc(this.me.name) : 'Гость'}
          </div>
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
    try { this.moonWeek = await api('/api/moon/week'); } catch (e) { this.moonWeek = null; }
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
          <div class="hero-body" style="position:relative;z-index:2">
            <div class="hero-date">${fmtDate()}</div>
            <div style="font-family:var(--font-serif);font-size:26px;font-weight:700;letter-spacing:.5px">Твой день, ${this.me && this.me.name ? esc(this.me.name.split(' ')[0]) : 'милая'}</div>
            ${t && t.moon ? `<div class="hero-moon-txt">${esc(t.moon.name)} · ${t.moon.day}-й лунный день — <em>${esc(t.moon.advice)}</em></div>` : ''}
          </div>
        </div>

        ${this.moonWeek && this.moonWeek[0] ? (() => {
          const wd = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс'];
          const mon = ['января', 'февраля', 'марта', 'апреля', 'мая', 'июня', 'июля', 'августа', 'сентября', 'октября', 'ноября', 'декабря'];
          const tv = t && t.moon ? t.moon : { name: this.moonWeek[0].name, day: this.moonWeek[0].day, advice: this.moonWeek[0].advice, emoji: this.moonWeek[0].emoji };
          const tIdx = this.moonWeek.findIndex(d => d.day === tv.day);
          const rows = this.moonWeek.map((d, i) => {
            const wdS = wd[d.weekday];
            const monS = mon[parseInt(d.date.slice(5, 7), 10) - 1] || '';
            const today = t && t.moon && d.day === t.moon.day;
            return `<div class="mc-day${today ? ' today' : ''}" data-i="${i}" data-act="moon-day">
              <div class="mc-row">
                <span class="mc-ico">${moonSvg(d.emoji)}</span>
                <span class="mc-main">
                  <span class="mc-wd">${wdS} · ${d.day_num} ${monS}${today ? ' <b>· сегодня</b>' : ''}</span>
                  <span class="mc-nm">${esc(d.name)} <em class="mc-ln">${d.day}-й день</em></span>
                </span>
                <span class="mc-chev">▾</span>
              </div>
              <div class="mc-detail" hidden><div class="mc-adv">${esc(d.advice)}</div></div>
            </div>`;
          }).join('');
          const atEmoji = e => e && e.includes('🌕') ? 'Полнолуния' : e && e.includes('🌑') ? 'Новолуния' : null;
          const key = this.moonWeek.find(d => atEmoji(d.emoji));
          const note = key ? `<div class="moon-note">${atEmoji(key.emoji)} — <b>${key.day_num} ${mon[Number(key.date.slice(5, 7), 10) - 1]}</b>. ${atEmoji(key.emoji) === 'Новолуния' ? 'Хорошее время начинать и загадывать.' : 'Энергия на подъёме — закрепляй начатое.'}</div>` : '';
          return `<div class="spacer"></div>
            <div class="moon-section">
              <div class="moon-head">
                <div class="section-title" style="margin:0">🌙 Лунный календарь</div>
                <button class="moon-toggle" data-act="moon-week"><span class="mt-lbl">Вся неделя</span><span class="mo-chev">▾</span></button>
              </div>
              <div class="moon-today" data-act="moon-week">
                <span class="mc-ico mc-ico-sm">${moonSvg(tv.emoji)}</span>
                <div class="mt-main">
                  <div class="mt-name">${esc(tv.name)} · ${tv.day}-й лунный день</div>
                  <div class="mt-adv">${esc(tv.advice)}</div>
                </div>
                <span class="mt-cta">Неделя<span class="mo-chev">›</span></span>
              </div>
              <div class="moon-week" id="moon-week">${rows}${note}</div>
            </div>`;
        })() : ''}

        <div class="spacer"></div>
        <div class="section-title">✨ Прогноз на сегодня</div>
        <div class="forecast-flow">
          ${t ? esc(t.forecast) : '<div class="skeleton" style="height:90px;border-radius:12px"></div>'}
        </div>

        ${t && t.card ? `
        <div class="spacer"></div>
        <div class="section-title">🂠 Карта дня</div>
        <div class="card-day card-day-big">
          <div class="tarot-card-big" data-act="flip-card" title="Перевернуть карту">
            <div class="tb-inner">
              <div class="tb-face tb-front">
                <div class="tb-scrim"></div>
                <span class="tb-arc">${esc(toRoman(t.card.num))}</span>
                <span class="tb-emoji">${t.card.emoji}</span>
                <svg class="tb-namepath" viewBox="0 0 116 36" preserveAspectRatio="none" aria-hidden="true">
                  <path id="tbArcPath" d="M 8 4 Q 58 26 108 4" fill="none"/>
                  <text class="tb-pathtext" dy="11"><textPath href="#tbArcPath" xlink:href="#tbArcPath" startOffset="50%" text-anchor="middle">${esc(t.card.name)}</textPath></text>
                </svg>
              </div>
              <div class="tb-face tb-back">
                <span class="tb-arc tb-back-arc">${esc(toRoman(t.card.num))}</span>
                <span class="tb-mean">${esc(t.card.meaning)}</span>
                <span class="tb-hint2">✦</span>
              </div>
            </div>
          </div>
          <div style="flex:1;min-width:0">
            <div class="cd-name">${esc(t.card.name)}</div>
            <div class="cd-note">Носи эту энергию сегодня — карта дня задаёт тон всему: от решений до встреч.</div>
            <div class="cd-hint">Тапни карту — она развернётся со смыслом ↻</div>
          </div>
        </div>` : ''}

        <div class="spacer"></div>
        <div class="section-title">🪐 Твои агенты</div>
        <div class="dock-grid">
          ${this.agents.length ? this.agents.map(a => `
            <div class="dock-item" data-act="chat" data-chat="${a.code}">
              <div class="dock-orb" style="--ac:${esc(a.accent || '#e6c178')}"><img class="dock-face" src="/static/img/agents/${esc(a.code)}.jpg" alt="${esc(a.name)}"></div>
              <div class="dock-name">${esc(a.name.split(' ')[0])}</div>
              ${a.title ? `<div class="dock-role">${esc(a.title)}</div>` : ''}
            </div>`).join('') : '<div class="skeleton" style="height:74px;border-radius:16px;grid-column:1/-1"></div>'}
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
                <div class="agent-avatar">${agentSprite(a)}</div>
                <div style="flex:1;min-width:0">
                  <div class="ac-head">
                    <div class="agent-title">${esc(a.name)}</div>
                    <span class="online-dot" title="в сети"></span>
                  </div>
                  <div class="agent-role">${esc(a.title || a.code)}</div>
                  <div class="agent-last">${esc(a.last_text || a.tagline || '')}</div>
                </div>
                <button class="btn btn-ghost" style="padding:7px 12px;font-size:12px" data-act="chat" data-chat="${a.code}">Написать</button>
              </div>
              ${(a.suggestions && a.suggestions.length) ? `
              <div class="agent-ask-chips">
                ${a.suggestions.slice(0, 3).map(s => `
                  <span class="ask-chip" data-act="ask" data-chat="${a.code}" data-q="${esc(s)}">${esc(s)}</span>`).join('')}
              </div>` : ''}
              <div class="agent-chips">
                ${(FEATURES[a.code] || []).slice(0, 4).map(f => `
                  <span class="tool" style="--ac2:${esc(a.accent || '#e6c178')}" data-act="chat-fn" data-chat="${a.code}" data-fn="${f.h}">
                    <span class="tool-ico">${f.e}</span>
                    <span class="tool-txt"><span class="tool-t">${esc(f.t)}</span>${f.d ? `<span class="tool-d">${esc(f.d)}</span>` : ''}</span>
                  </span>`).join('')}
              </div>
            </div>`).join('')}
        </div>
      </div>`;
  },

  /* ═══ ЧАТ — ГЛАВНЫЙ ИНСТРУМЕНТ ═══ */
  openChat(key, after) {
    haptic('soft');
    if (this.chat.key !== key) {
      this.chat.key = key;
      this.chat.spec = this.agentSpec(key);
      this.chat.messages = [];
      this.chat.pending = null;
      this.chat.tid = null;
      this.chat.sessions = [];
      this.loadThread(key);
    }
    this.view = 'hub';
    this.renderNav();
    this.renderChat(document.getElementById('app-main'));
    if (after) setTimeout(after, 60);
  },

  // список чатов-сессий агента (до 5)
  async refreshSessions() {
    try { this.chat.sessions = await api('/api/chat/' + this.chat.key + '/sessions'); }
    catch (e) { this.chat.sessions = this.chat.sessions || []; }
  },

  async loadThread(key) {
    try {
      const r = await api('/api/chat/' + key);
      this.chat.spec = r.agent;
      this.chat.tid = r.thread_id || null;
      this.chat.messages = (r.messages || []).map(m => ({ role: m.role, text: m.text }));
      // если истории нет — приветствие агента, чат не выглядит пустым
      if (!this.chat.messages.length && (r.agent && r.agent.greeting)) {
        this.chat.messages = [{ role: 'assistant', text: r.agent.greeting }];
      }
    } catch (e) {
      this.chat.messages = [{ role: 'assistant', text: '😔 Связь прервалась. Попробуй ещё раз.' }];
    }
    await this.refreshSessions();
    if (this.chat.key === key) this.renderChat(document.getElementById('app-main'));
  },

  toast(msg) {
    const t = document.createElement('div');
    t.className = 'toast'; t.textContent = msg;
    document.body.appendChild(t);
    setTimeout(() => t.remove(), 2400);
  },

  // отправка в активную сессию (если есть) — иначе первый вопрос создаёт тред
  async chatPost(text) {
    const a = this.chat.spec;
    if (this.chat.tid) {
      return await api(`/api/chat/${a.code}/sessions/${this.chat.tid}`,
        { method: 'POST', body: JSON.stringify({ text }) });
    }
    const r = await api(`/api/chat/${a.code}`, { method: 'POST', body: JSON.stringify({ text }) });
    if (r.thread_id) this.chat.tid = r.thread_id;
    return r;
  },

  toggleSessions() {
    const p = document.getElementById('sess-panel');
    if (p) p.style.display = p.style.display === 'none' ? 'block' : 'none';
  },

  // Лунный календарь: компакт — «кратко о сегодня» + раскрытие всей недели по кнопке
  toggleMoonWeek() {
    haptic('light');
    const wk = document.getElementById('moon-week');
    if (!wk) return;
    const open = wk.classList.toggle('show');
    document.querySelectorAll('.moon-toggle, .moon-today').forEach(el => {
      if (!el.closest('#moon-week')) el.classList.toggle('open', open);
    });
    if (!open) this.collapseMoonDays();
  },
  collapseMoonDays() {
    document.querySelectorAll('#moon-week .mc-day').forEach(d => {
      d.classList.remove('open');
      const det = d.querySelector('.mc-detail');
      if (det) det.hidden = true;
    });
  },
  toggleMoonDay(i) {
    haptic('soft');
    const day = Array.from(document.querySelectorAll('#moon-week .mc-day'))
      .find(d => d.dataset.i === String(i));
    if (!day) return;
    const det = day.querySelector('.mc-detail');
    const open = day.classList.toggle('open');
    if (det) det.hidden = !open;
  },

  // Лунный календарь: детальный модал со всей неделей (загружена в moonWeek)
  openMoon() {
    haptic('light');
    const arr = this.moonWeek || [];
    if (!arr.length) { this.toast('Лунный календарь скоро подтянет свет 🌙'); return; }
    const wd = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс'];
    const months = ['января', 'февраля', 'марта', 'апреля', 'мая', 'июня',
                    'июля', 'августа', 'сентября', 'октября', 'ноября', 'декабря'];
    const rows = arr.map((d, i) => {
      const today = i === 0;
      const m = months[parseInt(d.date.slice(5, 7), 10) - 1] || '';
      return `<div class="md-row${today ? ' today' : ''}">
        <span class="md-ico">${moonSvg(d.emoji)}</span>
        <div class="md-main">
          <div class="md-wd">${wd[d.weekday]} · ${d.day_num} ${m}${today ? ' <em>· сегодня</em>' : ''}</div>
          <div class="md-name"><b>${esc(d.name)}</b> · ${d.day}-й лунный день</div>
          <div class="md-adv">${esc(d.advice)}</div>
        </div>
      </div>`;
    }).join('');
    this.showModal(`<h3>🌙 Лунный календарь</h3><button class="m-close" data-act="modal-close">✕</button>
      <div class="moon-detail">${rows}</div>`);
  },

  switchPTab(tab) {
    haptic('light');
    document.querySelectorAll('.ptab').forEach(b => b.classList.toggle('active', b.dataset.tab === tab));
    document.querySelectorAll('.ptab-pane').forEach(p => p.classList.toggle('active', p.id === 'ptab-' + tab));
  },

  async newSession() {
    haptic('light');
    if ((this.chat.sessions || []).length >= 5) {
      this.toast('Максимум 5 чатов — удали один или заверши 🌙');
      return;
    }
    const r = await api(`/api/chat/${this.chat.key}/sessions`, { method: 'POST' });
    this.chat.tid = r.thread_id;
    this.chat.messages = [];
    this.chat.pending = null;
    await this.refreshSessions();
    this.renderChat(document.getElementById('app-main'));
  },

  async openSession(id) {
    try {
      const r = await api(`/api/chat/${this.chat.key}/sessions/${id}`);
      this.chat.spec = r.agent;
      this.chat.tid = r.thread_id;
      this.chat.messages = (r.messages || []).map(m => ({ role: m.role, text: m.text }));
      if (!this.chat.messages.length && r.agent && r.agent.greeting) {
        this.chat.messages = [{ role: 'assistant', text: r.agent.greeting }];
      }
    } catch (e) {
      this.chat.messages = [{ role: 'assistant', text: '😔 ' + e.message }];
    }
    await this.refreshSessions();
    this.renderChat(document.getElementById('app-main'));
  },

  async delSession(id) {
    await api(`/api/chat/${this.chat.key}/sessions/${id}`, { method: 'DELETE' });
    await this.refreshSessions();
    if (id === this.chat.tid) {
      const next = (this.chat.sessions || [])[0];
      if (next) { await this.openSession(next.id); return; }
      await this.newSession();
    } else {
      this.renderChat(document.getElementById('app-main'));
    }
  },

  renderChat(main) {
    const a = this.chat.spec;
    const messages = this.chat.messages;
    const busy = this.chat.busy;
    const pending = this.chat.pending;
    const features = FEATURES[a.code] || [];
    const suggest = (TEMPLATES[a.code] || a.suggestions || []).slice(0, 3);
    const last = messages[messages.length - 1];
    const cheer = messages.length > 1 && last.role === 'assistant' && !busy && !last.text.startsWith('😔');

    const body = messages.map(m =>
      `<div class="msg ${m.role === 'user' ? 'user' : 'assistant'}">${rich(m.text)}</div>`).join('');

    // первый экран чата: портрет агента + кто он (когда истории ещё нет)
    const introHtml = messages.length <= 1 ? `
      <div class="agent-intro" style="--ac:${esc(a.accent || '#e6c178')}">
        <div class="ai-face">${agentSprite(a, false)}</div>
        <div class="ai-name">${esc(a.name)}</div>
        <div class="ai-role">${esc(a.title || '')}</div>
        ${a.tagline ? `<div class="ai-tag">${esc(a.tagline)}</div>` : ''}
      </div>` : '';

    const pendHtml = pending ? this.pendingHtml(pending) : '';

    main.innerHTML = `
      <div class="chat-shell">
        <div class="chat-head">
          <button class="back" data-act="sessions" title="Мои чаты">☰</button>
          <button class="back" data-act="back">‹</button>
          <div class="agent-avatar" style="--ac:${esc(a.accent || '#e6c178')}">${agentSprite(a, cheer)}</div>
          <div style="flex:1;min-width:0">
            <div class="cname">${esc(a.name)}</div>
            <div class="tsub">${esc(a.title || a.role || '')}</div>
          </div>
          <span style="color:var(--text-faint);font-size:12px" data-act="clear">↺</span>
        </div>
        <div class="sess-panel" id="sess-panel" style="display:none">
          <div class="sess-head">
            <span>Чаты · ${(this.chat.sessions || []).length}/5</span>
            <button class="btn btn-ghost" style="padding:6px 12px;font-size:12px" data-act="new-session">＋ Новый чат</button>
          </div>
          ${(this.chat.sessions || []).map(s => `
            <div class="sess-row ${s.id === this.chat.tid ? 'active' : ''}" data-act="open-session" data-tid="${s.id}">
              <div class="sess-t">${esc(s.title || 'Новый чат')}</div>
              <div class="sess-prev">${esc(s.last_text || '')}</div>
              <button class="sess-del" data-act="del-session" data-tid="${s.id}" title="Удалить">✕</button>
            </div>`).join('')}
        </div>
        ${features.length ? `
        <div class="chat-features">
          ${features.map(f => `
            <span class="tool" data-act="feature" data-fn="${f.h}">
              <span class="tool-ico">${f.e}</span>
              <span class="tool-txt"><span class="tool-t">${esc(f.t)}</span>${f.d ? `<span class="tool-d">${esc(f.d)}</span>` : ''}</span>
            </span>`).join('')}
        </div>` : ''}
        <div class="chat-messages" id="chat-messages">
          ${introHtml}
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
            ${suggest.map(s => `<span class="chip tpl" data-act="fill" data-val="${esc(s)}">${esc(s)}</span>`).join('')}
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
                ${s.desc ? `<span class="s-desc">${esc(s.desc)}</span>` : ''}
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
    if (this.chat.tid) {
      try { await api(`/api/chat/${key}/sessions/${this.chat.tid}`, { method: 'DELETE' }); } catch (e) {}
      await this.refreshSessions();
      await this.newSession();
      return;
    }
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
    haptic('light');
    const input = document.getElementById('chat-input');
    if (input) input.value = '';
    this.chat.messages.push({ role: 'user', text: val });
    this.chat.busy = true;
    this.renderChat(document.getElementById('app-main'));
    try {
      const r = await this.chatPost(val);
      haptic('success');
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
        { code: 'one', title: 'Одна карта', emoji: '🂠', tier: 'included', desc: 'Один ясный ответ на конкретный вопрос' },
        { code: 'three', title: 'Прошлое · Наст · Будущее', emoji: '🂠🂠🂠', tier: 'included', desc: 'Как развивалась ситуация — и куда ведёт' },
        { code: 'love', title: 'На отношения', emoji: '💞', tier: 'included', desc: 'Твоё чувство, партнёр и связь между вами' },
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

  // Карта дня: переворот раскрывает смысл
  flipDayCard(el) {
    haptic('light');
    const c = el && el.closest ? el.closest('.tarot-card-big') : null;
    if (c) c.classList.toggle('flipped');
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
    this.chatPost(text)
      .then(r => { this.chat.messages.push({ role: 'assistant', text: r.answer }); })
      .catch(e => { this.chat.messages.push({ role: 'assistant', text: '😔 ' + e.message }); })
      .finally(() => { this.chat.busy = false; this.renderChat(document.getElementById('app-main')); });
  },

  // Шаблон-фраза: вставляется в поле ввода для редактирования (не авто-отправка).
  fillInput(text) {
    const input = document.getElementById('chat-input');
    if (!input) return;
    input.value = text || '';
    input.focus();
    input.setSelectionRange(input.value.length, input.value.length);
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
          <div class="p-ico moon-orb mini-moon">${moonSvg(d.emoji)}</div>
          <div class="p-name">${d.date.slice(8)} ${wd[d.weekday]} · <b>${esc(d.name)}</b></div>
          <div class="p-val" style="font-size:11.5px">${d.day}-й д.</div>
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

        <div class="ptab-bar">
          <button class="ptab active" data-act="ptab" data-tab="summary">Сводка</button>
          <button class="ptab" data-act="ptab" data-tab="chart">Карта</button>
          <button class="ptab" data-act="ptab" data-tab="history">История</button>
          <button class="ptab" data-act="ptab" data-tab="memory">Память</button>
        </div>

        <div class="ptab-pane active" id="ptab-summary">
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
        </div>

        <div class="ptab-pane" id="ptab-chart">
          <div class="section-title">🌌 Натальная карта</div>
          <div id="profile-chart"><div class="glass"><div class="center-block"><div class="loader-ring"></div></div></div></div>
        </div>

        <div class="ptab-pane" id="ptab-history">
          <div class="section-title">🎴 Последние расклады</div>
          <div id="profile-tarot"><div class="skeleton" style="height:80px;border-radius:16px"></div></div>
          <div class="spacer"></div>
          <div class="section-title">📜 Разборы</div>
          <div id="profile-reports"><div class="skeleton" style="height:60px;border-radius:16px"></div></div>
        </div>

        <div class="ptab-pane" id="ptab-memory">
          <div class="section-title">🧠 Что я помню о тебе</div>
          <div id="profile-memories"><div class="skeleton" style="height:60px;border-radius:16px"></div></div>
        </div>
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
                <button class="btn btn-ghost" style="padding:8px 12px;font-size:12px" data-act="full-chart">Полная карта</button>
              </div>
            </div>
          </div>
          <div style="margin-top:10px">${planets}</div>
          <div style="color:var(--text-faint);font-size:11px;margin-top:6px">Раху · Кету · дома · аспекты — в «Полной карте»</div>
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
      // компактно: до 3 строк + «Все N →» (тап открывает модал со всем списком)
      if (tarotEl) {
        if (!rows.length) {
          tarotEl.innerHTML = '<div class="glass" style="padding:16px;color:var(--text-faint);font-size:13px">Раскладов пока нет — зайди к Тарологу и задай вопрос картам.</div>';
        } else {
          const shown = rows.slice(0, 3).map(r => `
            <div class="tight-card" data-act="reading" data-id="${r.id}">
              <span class="tc-emoji">${r.cards && r.cards[0] ? r.cards[0].emoji : '🎴'}</span>
              <div style="flex:1;min-width:0">
                <div class="tc-title">${esc(r.question || 'Расклад')}</div>
                <div class="tc-meta">${fmtDay(r.created_at.slice(0, 10))} · ${esc(r.spread || '')}</div>
              </div>
              <span class="tc-open">›</span>
            </div>`).join('');
          const more = rows.length > 3
            ? `<button class="more-row" data-act="all-readings">Все ${rows.length} раскладов ›</button>` : '';
          tarotEl.innerHTML = shown + more;
        }
      }
      this._readingsCache = rows;
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

    const mems = this.me && this.me.memories ? this.me.memories : [];
      // кнопка открывает модал управления памятью (просмотр/дата/удалить/добавить)
      if (memEl) memEl.innerHTML = `
        <button class="memory-open" data-act="memories">
          <span style="font-size:18px">🧠</span>
          <span style="flex:1;text-align:left">
            <div style="font-weight:600;font-size:14px">Что я помню о тебе</div>
            <div style="font-size:12px;color:var(--text-dim);margin-top:2px">${mems.length ? mems.length + ' записей · нажми, чтобы посмотреть и править' : 'Пока пусто — нажми, чтобы добавить первое'}</div>
          </span>
          <span style="color:var(--gold)">›</span>
        </button>`;
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

  // тап по подсказке на карте агента: открывает чат и сразу отправляет вопрос
  askAgent(key, q) {
    this.openChat(key, () => this.doSend(q));
  },

  // Память: управление — просмотр с датой, удалить, добавить вручную.
  async openMemories() {
    this.showModal(`<h3>Что я помню о тебе</h3><button class="m-close" data-act="modal-close">✕</button>
      <div id="mem-body" style="margin-top:6px"><div class="loader-ring"></div></div>`);
    try {
      const rows = await api('/api/memories');
      this._memFull = rows;
      this.renderMemModal();
    } catch (e) {
      document.getElementById('mem-body').innerHTML = '<div style="color:var(--text-faint)">😔 ' + esc(e.message) + '</div>';
    }
  },

  renderMemModal() {
    const el = document.getElementById('mem-body');
    if (!el) return;
    const rows = this._memFull || [];
    const list = rows.map(m => `
      <div class="mem-manage-row">
        <div class="mem-manage-txt">${esc(m.fact)}</div>
        <div class="mem-manage-meta">${esc((m.created_at || '').slice(0, 10))}</div>
        <button class="mem-del" data-act="del-mem" data-id="${m.id}" title="Удалить">✕</button>
      </div>`).join('');
    el.innerHTML = `
      <div class="mem-add">
        <input class="ipt" id="mem-new" placeholder="Добавь важное о себе…" autocomplete="off"/>
        <button class="send-btn" data-act="add-mem" title="Добавить">+</button>
      </div>
      ${rows.length ? `<div class="mem-manage-list">${list}</div>`
                    : '<div style="color:var(--text-faint);font-size:13px;padding:8px 2px">Пока ничего не помню. Добавь первый факт выше или просто расскажи мне в чате.</div>'}`;
  },

  async delMem(id) {
    try {
      await api('/api/memories/' + id, { method: 'DELETE' });
      this._memFull = (this._memFull || []).filter(m => m.id !== id);
      this.renderMemModal();
      this.me = null; this.me = await api('/api/me');   // обновить счётчик памяти
    } catch (e) { alert(e.message); }
  },

  async addMem() {
    const input = document.getElementById('mem-new');
    const fact = (input && input.value || '').trim();
    if (fact.length < 3) { if (input) input.focus(); return; }
    try {
      await api('/api/memories', { method: 'POST', body: JSON.stringify({ fact }) });
      this._memFull = await api('/api/memories');
      this.renderMemModal();
      this.me = await api('/api/me');
    } catch (e) { alert(e.message); }
  },

  // «Все N раскладов»: полный список в модале
  async openAllReadings() {
    let rows = this._readingsCache;
    if (!rows) { try { rows = await api('/api/tarot/history'); } catch (e) { rows = []; } }
    const items = (rows || []).map(r => `
      <div class="tight-card" data-act="reading" data-id="${r.id}">
        <span class="tc-emoji">${r.cards && r.cards[0] ? r.cards[0].emoji : '🎴'}</span>
        <div style="flex:1;min-width:0">
          <div class="tc-title">${esc(r.question || 'Расклад')}</div>
          <div class="tc-meta">${fmtDay(r.created_at.slice(0, 10))} · ${esc(r.spread || '')}</div>
        </div>
        <span class="tc-open">›</span>
      </div>`).join('');
    this.showModal(`<h3>Все расклады</h3><button class="m-close" data-act="modal-close">✕</button>
      <div style="margin-top:8px">${items || '<div style="color:var(--text-faint);font-size:13px">Раскладов пока нет</div>'}</div>`);
  },

  // Полная натальная карта: планеты, узлы (Раху/Кету/Лилит), дома, аспекты, ASC/MC
  async openFullChart() {
    this.showModal(`<h3>🌌 Полная натальная карта</h3><button class="m-close" data-act="modal-close">✕</button>
      <div id="fc-body" style="margin-top:8px"><div class="loader-ring"></div></div>`);
    try {
      const c = await api('/api/chart');
      const row = (ico, name, val) => `<div class="fc-row"><span class="fc-ico">${ico}</span><span class="fc-name">${esc(name)}</span><span class="fc-val">${val}</span></div>`;
      const pRows = (c.planets || []).map(p =>
        row(SIGNS[p.sign] || '•', p.name, `${esc(p.sign)} ${p.deg}°${p.house ? ' · дом ' + p.house : ''}${p.retro ? ' ℞' : ''}`)).join('');
      const nRows = (c.nodes || []).map(n =>
        row('☊', n.name, `${esc(n.sign)} ${n.deg}°${n.house ? ' · дом ' + n.house : ''}${n.retro ? ' ℞' : ''}`)).join('');
      const hRows = (c.houses || []).map(h =>
        row(`${h.n}`, `${h.n}-й дом`, `${esc(h.sign)} ${h.deg}°`)).join('');
      const aRows = (c.aspects || []).slice(0, 12).map(a =>
        row(a.glyph || '◈', `${a.p1} — ${a.p2}`, `${a.aspect}${a.orb != null ? ' · орб ' + a.orb + '°' : ''}`)).join('');
      document.getElementById('fc-body').innerHTML = `
        <div class="fc-hero">
          <img src="/static/img/card-art.jpg" alt="" aria-hidden="true" loading="lazy">
          <div class="fc-hero-overlay">
            <h2 class="fc-modal-h" style="font-size:20px">🌌 Полная натальная карта</h2>
            <div style="font-size:12.5px;color:var(--text-dim);margin-top:2px">Планеты · Узлы · Дома · Аспекты — простым языком</div>
          </div>
        </div>
        <div class="fc-card">
          <span class="fc-ico">☉</span>
          <div class="fc-card-body">
            <h4 class="fc-t">Твой знак и восход</h4>
            <div class="fc-desc"><b>Солнце ${esc(c.sun && c.sun.sign || '')}</b> (${esc(c.sun && c.sun.element || '')}) — твоя суть, воля и энергия. <b>Асцендент ${esc(c.ascendant && c.ascendant.sign || '—')}</b> (${esc(c.ascendant && c.ascendant.deg ? Math.round(c.ascendant.deg) : '—')}°) — как тебя видят со стороны. <b>MC ${esc(c.mc && c.mc.sign || '—')}</b> — направление и цель.</div>
          </div>
        </div>
        <div class="fc-card">
          <span class="fc-ico">🌌</span>
          <div class="fc-card-body">
            <h4 class="fc-t">Планеты</h4>
            <div class="fc-planets-grid">
              ${(c.planets || []).map(p => `
              <div class="fc-planet">
                <span class="pl-ico">${SIGNS[p.sign] || '•'}</span>
                <span class="pl-info"><span class="pl-t">${esc(p.name)} · ${esc(p.sign)}${p.house ? ' · дом ' + p.house : ''}${p.retro ? ' ℞' : ''}</span><span class="pl-d">${p.deg ? p.deg + '°' : ''}</span></span>
              </div>`).join('')}
            </div>
          </div>
        </div>
        <div class="fc-card">
          <span class="fc-ico">☊</span>
          <div class="fc-card-body">
            <h4 class="fc-t">Узлы и точки</h4>
            <div class="fc-planets-grid">
              ${(c.nodes || []).map(n => {
                const label = n.name && n.name.includes('Раху') ? 'Предназначение этой жизни (Раху — северный узел)' : (n.name && n.name.includes('Кету') ? 'Кармический багаж (Кету — южный узел)' : n.name);
                return `<div class="fc-planet" style="min-width:190px;max-width:none">
                  <span class="pl-ico">☊</span>
                  <span class="pl-info"><span class="pl-t">${esc(n.sign)} ${n.deg}° · дом ${n.house || '—'}${n.retro ? ' ℞' : ''}</span>
                  <span class="pl-d">${label}</span>
                </span>
                </div>`;
              }).join('')}
              ${(c.nodes || []).find(n => n.name && n.name.includes('Лилит')) ? `
              <div class="fc-planet" style="min-width:190px;max-width:none">
                <span class="pl-ico">⚫</span>
                <span class="pl-info"><span class="pl-t">Лилит · тёмная Луна</span>
                <span class="pl-d">Зона подсознательных желаний, тени, страсти и скрытой силы.</span>
                </span>
              </div>` : ''}
            </div>
          </div>
        </div>
        <div class="fc-card">
          <span class="fc-ico">◈</span>
          <div class="fc-card-body">
            <h4 class="fc-t">Аспекты (до 8)</h4>
            <div style="font-size:11px;color:var(--text-faint);margin-bottom:6px">Ключевые углы между планетами — как они разговаривают друг с другом.</div>
            <div style="display:flex;flex-wrap:wrap;gap:5px">
              ${(c.aspects || []).slice(0, 8).map(a => `
              <span class="chip" style="font-size:11.5px;padding:4px 8px">${esc(a.glyph || '◈')} <b>${esc(a.p1)} — ${esc(a.p2)}</b> · <em style="color:var(--text-faint)">${esc(a.aspect)}</em> · орб ${esc(a.orb != null ? a.orb + '°' : '')}</span>`).join('')}
            </div>
          </div>
        </div>
        <div class="fc-card">
          <span class="fc-ico">🏠</span>
          <div class="fc-card-body">
            <h4 class="fc-t">Дома</h4>
            <div style="font-size:12px;color:var(--text-dim);line-height:1.55">
              ${(c.houses || []).map((h, i) => `<b style="color:var(--gold-bright)">${i + 1}-й дом · ${esc(h.sign || '')}</b> ${h.deg ? h.deg + '°' : ''}${i < 11 ? ' · ' : ''}`).join('')}
            </div>
          </div>
        </div>
        <button class="btn btn-primary" style="margin-top:14px" data-act="chat" data-chat="astro">Спросить Астролога про карту</button>
        <button class="btn btn-ghost" style="width:100%;margin-top:8px" data-act="fc-explain">🧠 Разбор простыми словами</button>
        <div id="fc-explain" style="margin-top:12px"></div>`;
    } catch (e) {
      document.getElementById('fc-body').innerHTML = '<div style="color:var(--text-faint)">😔 ' + esc(e.message) + '</div>';
    }
  },

  // Разбор карты простыми словами: ИИ-объяснение по разделам (кэш на сервере).
  async explainChart() {
    const box = document.getElementById('fc-explain');
    if (!box) return;
    if (box.dataset.loaded) {
      box.style.display = box.style.display === 'none' ? 'block' : 'none';
      return;
    }
    box.innerHTML = '<div class="loader-ring" style="margin:10px auto"></div>';
    try {
      const r = await api('/api/chart/interpret', { method: 'POST' });
      box.dataset.loaded = '1';
      box.innerHTML = '<div class="glass fc-explain">' + richMd(r.text) + '</div>';
    } catch (e) {
      box.innerHTML = '<div style="color:var(--text-faint)">😔 ' + esc(e.message) + '</div>';
    }
  },

  // панель уведомлений: прогноз дня + утреннее напоминание
  async openBell() {
    this.showModal(`<h3>Уведомления</h3><button class="m-close" data-act="modal-close">✕</button>
      <div id="bell-body" style="margin-top:8px"><div class="loader-ring"></div></div>`);
    try {
      if (!this.today) this.today = await api('/api/today');
      const t = this.today;
      const push = this.me && this.me.morning_push;
      document.getElementById('bell-body').innerHTML = `
        <div class="glass" style="padding:14px 16px">
          <div style="font-size:12px;color:var(--text-faint);letter-spacing:1px;text-transform:uppercase;margin-bottom:6px">Сегодня · ${fmtDate()}</div>
          <div style="font-size:13.5px;line-height:1.6">${esc(t.forecast)}</div>
        </div>
        <div class="mem-row" style="margin-top:10px;align-items:center">
          <span class="mem-dot">🌅</span>
          <span class="mem-txt" style="flex:1">Утренний прогноз в боте</span>
          <span style="color:${push ? '#58d68d' : 'var(--text-faint)'};font-size:12px">${push ? 'вкл' : 'выкл'}</span>
        </div>
        <div style="color:var(--text-faint);font-size:11.5px;margin-top:10px">Напоминания и прогнозы приходят в Telegram-боте. Включить их можно там же.</div>`;
    } catch (e) {
      document.getElementById('bell-body').innerHTML = '<div style="color:var(--text-faint);font-size:13px">😔 ' + esc(e.message) + '</div>';
    }
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
    case 'feature': haptic('light'); app[v.fn] && app[v.fn](); break;
    case 'sessions': app.toggleSessions(); break;
    case 'moon': app.openMoon(); break;
    case 'moon-week': app.toggleMoonWeek(); break;
    case 'moon-day': app.toggleMoonDay(parseInt(v.i, 10)); break;
    case 'ptab': app.switchPTab(v.tab); break;
    case 'new-session': app.newSession(); break;
    case 'open-session': app.openSession(parseInt(v.tid, 10)); break;
    case 'del-session': app.delSession(parseInt(v.tid, 10)); break;
    case 'send': app.doSend(v.val || undefined); break;
    case 'fill': app.fillInput(v.val); break;
    case 'memories': app.openMemories(); break;
    case 'full-chart': app.openFullChart(); break;
    case 'fc-explain': app.explainChart(); break;
    case 'del-mem': app.delMem(parseInt(v.id, 10)); break;
    case 'add-mem': app.addMem(); break;
    case 'spread': app.pickSpread(v.spread); break;
    case 'draw': app.doDraw(); break;
    case 'flip': app.flipCard(parseInt(v.i, 10)); break;
    case 'flip-card': app.flipDayCard(el); break;
    case 'interpret': app.doInterpret(); break;
    case 'compat': app.doCompat(); break;
    case 'reading': app.openReading(parseInt(v.id, 10)); break;
    case 'report': app.openReport(v.kind); break;
    case 'build': app.doBuildChart(); break;
    case 'ask': app.askAgent(v.chat, v.q); break;
    case 'all-readings': app.openAllReadings(); break;
    case 'bell': app.openBell(); break;
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