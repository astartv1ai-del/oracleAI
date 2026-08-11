/* ── приложение ─────────────────────────────────────────────────────────── */
const app = window.app = {};

app.me = null; app.agents = []; app.today = null; app.spreads = null;
app.view = 'home';
app.chat = { key: null, spec: null, messages: [], pending: null, busy: false, tid: null, sessions: [], draft: '' };

  app.boot = async function() {
    if (tg()) {
      tg().ready && tg().ready();
      tg().expand && tg().expand();
      try { tg().setHeaderColor && tg().setHeaderColor('#08070f'); } catch (e) {}
    }
    this.renderFrame();
    try {
      this.me = await api('/api/me');
      if (this.me) {
        const flags = this.me.flags ? this.me.flags : {};
        this.me.flags = flags;
      }
      const pill = document.querySelector('.user-pill');
      if (pill && this.me.name) {
        pill.innerHTML = `<span class="avatar">${esc(this.me.name[0].toUpperCase())}</span>${esc(this.me.name)}`;
      }
    } catch (e) { /* вход по dev_user в БД уже есть */ }
    this.loadAgents();
    this.loadToday();
    this.go('home');
    this.initSwipe();
    this.initViewport();
    this.maybeIntro();
  };
  // G001 клавиатура: композер поднимается, когда Telegram раскрывает клавиатуру

  app.initViewport = function() {
    if (!window.visualViewport) return;
    window.visualViewport.addEventListener('resize', () => {
      const vv = window.visualViewport;
      const composer = document.querySelector('.composer');
      if (!composer) return;
      const kb = Math.max(0, (window.innerHeight || vv.height) - vv.height);
      if (kb > 0) composer.style.paddingBottom = (kb + 8) + 'px';
      else composer.style.paddingBottom = '';
    }, { passive: true });
  };
  // G003 Свайпы: назад в чате (вправо) + переключение экранов (влево/вправо).
  // Нижний бар остаётся подстраховкой; горизонтальные скролл-ленты не задеваем.

  app.initSwipe = function() {
    let sx = 0, sy = 0;
    const skipSel = '.toolbar, .tool-expand, .rc-strip-row, .agent-chips, .suggest-chips, .chat-widget';
    document.addEventListener('touchstart', e => {
      const t = e.changedTouches[0]; sx = t.clientX; sy = t.clientY;
    }, { passive: true });
    document.addEventListener('touchend', e => {
      const t = e.changedTouches[0];
      const dx = t.clientX - sx, dy = t.clientY - sy;
      if (Math.abs(dx) < 70 && Math.abs(dy) < 70) return;
      if (e.target && e.target.closest && e.target.closest(skipSel)) return;
      const inChat = !!(e.target && e.target.closest && e.target.closest('.chat-shell'));
      if (inChat) {
        // свайп вбок по переключателю агентов → листаем агентов
        if (e.target.closest('.agent-tabs') && Math.abs(dx) > Math.abs(dy)) {
          this.cycleAgent(dx < 0 ? 1 : -1);
          return;
        }
        // вертикальный свайп: вверх у нижнего края ленты — открыть панель
        // инструментов, вниз — закрыть открытую. Прокрутку сообщений не трогаем:
        // у края скролл уже мёртв, поэтому жест безопасно переназначаем.
        if (Math.abs(dy) > Math.abs(dx) && Math.abs(dy) >= 70) {
          const box = document.querySelector('.chat-messages');
          const open = document.getElementById('tool-expand');
          if (dy < 0 && (!box || (box.scrollTop + box.clientHeight >= box.scrollHeight - 2))) {
            this.setToolbox(true);
          } else if (dy > 0 && open && open.classList.contains('open')) {
            this.setToolbox(false);
          }
          return;
        }
        if (dx > 0) { this.closeChat(); haptic('light'); }  // вправо → из чата
        return;
      }
      if (this.view === 'chat' || this.view === 'home' || this.view === 'hub' || this.view === 'profile') {
        if (dx < 0) this.go(this.view === 'home' ? 'hub' : 'profile');
        else this.go(this.view === 'profile' ? 'hub' : 'home');
      }
    }, { passive: true });
  };
  // G002 Онбординг: вау-интро 3 скрина для первого входа (1 раз на клиента)

  app.maybeIntro = function() {
    if (localStorage.getItem('oracle_intro_seen')) return;
    const ov = document.createElement('div');
    ov.id = 'intro';
    ov.innerHTML = `
      <div class="intro-track">
        <div class="intro-slide"><div class="intro-emoji">🔮</div><div class="intro-title">Твоё небо уже ждёт</div><div class="intro-sub">Личный Оракул читает твою карту, Луну и расклады — честно, по звёздам.</div></div>
        <div class="intro-slide"><div class="intro-emoji">🎴</div><div class="intro-title">Карты отвечают на твой вопрос</div><div class="intro-sub">Настоящая колода Райдера-Уэйта придёт прямо в чат. Задай вопрос — карты лягут в расклад.</div></div>
        <div class="intro-slide"><div class="intro-emoji">✨</div><div class="intro-title">Прогноз каждый день</div><div class="intro-sub">Натальная карта, лунный календарь и карта дня — утро начинается с опоры.</div></div>
      </div>
      <div class="intro-dots"><span class="active"></span><span></span><span></span></div>
      <button class="btn btn-primary intro-start" data-intro-start>Начать ✨</button>
      <button class="intro-skip" data-intro-skip>Пропустить</button>`;
    document.body.appendChild(ov);
    const track = ov.querySelector('.intro-track');
    const dots = ov.querySelectorAll('.intro-dots span');
    const sync = () => {
      const i = Math.max(0, Math.min(2, Math.round(track.scrollLeft / (track.clientWidth || 1))));
      dots.forEach((d, k) => d.classList.toggle('active', k === i));
      ov.querySelector('.intro-start').textContent = i === 2 ? 'Начать ✨' : 'Дальше →';
    };
    track.addEventListener('scroll', sync, { passive: true });
    const done = () => {
      try { localStorage.setItem('oracle_intro_seen', '1'); } catch (e) {}
      ov.remove();
      haptic('success');
    };
    ov.querySelector('[data-intro-start]').addEventListener('click', () => {
      if (!ov.querySelector('.intro-start').textContent.startsWith('Начать')) {
        track.scrollBy({ left: track.clientWidth, behavior: 'smooth' });
      } else done();
    });
    ov.querySelector('[data-intro-skip]').addEventListener('click', done);
  };

  // Гайд первого захода в чат: лёгкий оверлей по окну чата, 4 шага, 1 раз.
  // Флаг отдельный от глобального интро (или больше, или меньше — не мешаем).

  app.maybeChatGuide = function() {
    try { if (localStorage.getItem('oracle_chat_guide')) return; } catch (e) { return; }
    if (document.getElementById('intro') || document.getElementById('chat-guide')) return;
    const steps = [
      { e: '💬', t: 'Задай вопрос', d: 'Напиши агенту о своей ситуации — он ответит по твоей карте, Луне и звёздам, как живому собеседнику.' },
      { e: '🧰', t: 'Быстрые инструменты', d: 'Над полем ввода — чипы: таро, натальная карта, совместимость. Тапни — инструмент придёт прямо в чат.' },
      { e: '🔄', t: 'Переключай агентов', d: 'Табы с аватарами меняют агента, свайп по ним листает: Оракул, Астролог, Таролог.' },
      { e: '🪶', t: 'Он помнит тебя', d: 'Агент запоминает важное из разговоров — всё сохранённое можно увидеть в Профиле.' },
    ];
    const ov = document.createElement('div');
    ov.id = 'chat-guide';
    let i = 0;
    const render = () => {
      const s = steps[i];
      ov.innerHTML = `
        <div class="cg-card">
          <div class="cg-emoji">${s.e}</div>
          <div class="cg-title">${s.t}</div>
          <div class="cg-sub">${s.d}</div>
          <div class="cg-dots">${steps.map((_, k) => `<span class="${k === i ? 'active' : ''}"></span>`).join('')}</div>
          <div class="cg-btns">
            <button class="btn btn-ghost" data-cg-skip>Пропустить</button>
            <button class="btn btn-primary" data-cg-next>${i === steps.length - 1 ? 'Понятно ✨' : 'Дальше'}</button>
          </div>
        </div>`;
      ov.querySelector('[data-cg-skip]').addEventListener('click', done);
      ov.querySelector('[data-cg-next]').addEventListener('click', () => {
        haptic('light');
        if (i < steps.length - 1) { i++; render(); }
        else done();
      });
    };
    const done = () => {
      try { localStorage.setItem('oracle_chat_guide', '1'); } catch (e) {}
      ov.remove();
      haptic('success');
    };
    render();
    document.body.appendChild(ov);
  };

  /* ── каркас ── */

  app.renderFrame = function() {
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
  };


  app.navItems = function() {
    return [
      { k: 'home', ico: '✨', t: 'Сегодня' },
      { k: 'hub', ico: '🪐', t: 'Агенты' },
      { k: 'profile', ico: '🌙', t: 'Профиль' },
    ];
  };

  app.renderNav = function() {
    const active = this.chat.key ? 'hub' : this.view;
    document.getElementById('main-nav').innerHTML = this.navItems().map(n => `
      <button class="nav-btn ${active === n.k ? 'active' : ''}" data-act="go" data-goto="${n.k}">
        <span class="nav-ico">${n.ico}</span><span>${n.t}</span>
      </button>`).join('');
  };

  app.go = function(v) {
    if (v === 'chat') v = 'hub';
    if (v !== 'hub') this.chat.key = null;
    this.view = v;
    this.renderNav();
    const main = document.getElementById('app-main');
    if (v === 'home') this.renderHome(main);
    else if (v === 'hub') this.renderHub(main);
    else if (v === 'profile') { this.renderProfile(main); }
  };


  app.scrollToBottom = function() {
    const box = document.querySelector('.chat-messages, .screen');
    if (box) {
      box.scrollTop = box.scrollHeight;
      // параллакс только на экранах (Сегодня/Агенты/Профиль) — в чате фон
      // не должен двигаться при скролле ленты (иначе выглядит «битым»)
      const sf = document.querySelector('.starfield');
      if (sf && !box.classList.contains('chat-messages')) {
        sf.style.transform = 'translateY(' + (box.scrollTop * 0.08) + 'px)';
      }
    }
  };

  /* ── данные ── */

  app.loadAgents = async function() {
    try { this.agents = await api('/api/agents'); } catch (e) { this.agents = []; }
    if (this.view === 'hub') this.renderHub(document.getElementById('app-main'));
    if (this.view === 'home') this.renderHome(document.getElementById('app-main'));
  };

  app.loadToday = async function() {
    try { this.today = await api('/api/today'); } catch (e) { this.today = null; }
    try { this.moonWeek = await api('/api/moon/week'); } catch (e) { this.moonWeek = null; }
    if (this.view === 'home') this.renderHome(document.getElementById('app-main'));
  };


  app.agentSpec = function(key) {
    const a = this.agents.find(x => x.code === key);
    return a || { code: key, name: key, emoji: '✦', accent: '#e6c178' };
  };

  /* ═══ ЭКРАН «СЕГОДНЯ» — статичная база ═══ */

