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
        const avatar = pill.querySelector('.avatar');
        const name = pill.querySelector('.user-name');
        if (avatar) avatar.textContent = this.me.name[0].toUpperCase();
        if (name) name.textContent = this.me.name;
        pill.setAttribute('aria-label', 'Открыть профиль: ' + this.me.name);
      }
    } catch (e) { /* вход по dev_user в БД уже есть */ }
    this.loadAgents();
    this.loadToday();
    this.go('home');
    this.initSwipe();
    this.initViewport();
    if (this.me && !this.me.age_confirmed) this.showAgeGate();
    else this.maybeIntro();
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
  // P0: самоподтверждение 16+ без сбора даты рождения. Это не верификация личности,
  // а ясная граница продукта и путь к безопасным настройкам приватности.
  app.showAgeGate = function() {
    if (document.getElementById('age-gate')) return;
    const ov = document.createElement('div');
    ov.id = 'age-gate';
    ov.innerHTML = `<div class="age-gate-card">
      <img src="/static/img/oracle-mark.png" class="age-gate-mark" alt="OracleAI">
      <div class="age-gate-kicker">Твоё безопасное пространство</div>
      <h2>Сначала — бережная граница</h2>
      <p>OracleAI создан для пользователей от 16 лет. Здесь есть развлекательные астрологические практики и поддерживающие диалоги, но не медицинская, юридическая или психологическая помощь.</p>
      <button class="btn btn-primary" data-age-accept>Мне есть 16 лет · продолжить</button>
      <button class="age-gate-leave" data-age-leave>Мне нет 16 · закрыть</button>
      <div class="age-gate-note">Продолжая, ты подтверждаешь возраст и принимаешь бережный формат сервиса. Настройки памяти всегда доступны в разделе «Моё».</div>
    </div>`;
    document.body.appendChild(ov);
    ov.querySelector('[data-age-accept]').addEventListener('click', async () => {
      try {
        await api('/api/profile', { method: 'POST', body: JSON.stringify({ age_confirmed: true }) });
        this.me = await api('/api/me');
        ov.remove();
        haptic('success');
        this.maybeIntro();
      } catch (e) { alert('Не удалось сохранить подтверждение. Проверь соединение и попробуй снова.'); }
    });
    ov.querySelector('[data-age-leave]').addEventListener('click', () => {
      try { tg() && tg().close && tg().close(); } catch (e) {}
      ov.querySelector('.age-gate-card').innerHTML = '<div class="age-gate-kicker">Спасибо за честность</div><h2>Вернись, когда тебе исполнится 16</h2><p>Береги себя. Если тебе тревожно или нужна срочная поддержка, пожалуйста, обратись к близкому взрослому или в местную службу помощи.</p>';
    });
  };

  // G002 Онбординг: вау-интро 3 скрина для первого входа (1 раз на клиента)

  app.maybeIntro = function() {
    if (localStorage.getItem('oracle_intro_seen')) return;
    // первый день + дата рождения уже есть, а карты нет — в финал интро
    // добавляем CTA «собрать натальную карту» (строится у Астролога в чате)
    const needChart = !!(this.me && this.me.birth_date && !this.me.chart_mode);
    const firstName = this.me && this.me.name ? esc(this.me.name.split(' ')[0]) : '';
    const slides = [
      `<div class="intro-slide"><div class="intro-emoji">🔮</div><div class="intro-title">Твоё небо уже ждёт</div><div class="intro-sub">Личный Оракул читает твою карту, Луну и расклады — честно, по звёздам.</div></div>`,
      `<div class="intro-slide"><div class="intro-emoji">🎴</div><div class="intro-title">Карты отвечают на твой вопрос</div><div class="intro-sub">Настоящая колода Райдера-Уэйта придёт прямо в чат. Задай вопрос — карты лягут в расклад.</div></div>`,
      `<div class="intro-slide"><div class="intro-emoji">✨</div><div class="intro-title">Прогноз каждый день</div><div class="intro-sub">Натальная карта, лунный календарь и карта дня — утро начинается с опоры.</div></div>`,
    ];
    if (needChart) {
      slides.push(`<div class="intro-slide">
        <div class="intro-emoji">🌌</div>
        <div class="intro-title">Собери натальную карту</div>
        <div class="intro-sub">${firstName ? 'Лилит посмотрит на твою карту, ' + firstName + '.' : 'Твоя карта рождения откроет характер и путь.'} Планеты, дома и предназначение — по дате и времени рождения.</div>
        <button class="btn btn-primary" style="margin-top:14px;width:100%" data-act="chat-fn" data-chat="astro" data-fn="featureChart" data-intro-chart>Собрать мою натальную карту ✨</button>
      </div>`);
    }
    const last = slides.length - 1;
    const ov = document.createElement('div');
    ov.id = 'intro';
    ov.innerHTML = `
      <div class="intro-track">
        ${slides.join('')}
      </div>
      <div class="intro-dots">${slides.map((_, k) => `<span${k === 0 ? ' class="active"' : ''}></span>`).join('')}</div>
      <button class="btn btn-primary intro-start" data-intro-start>Начать ✨</button>
      <button class="intro-skip" data-intro-skip>Пропустить</button>`;
    document.body.appendChild(ov);
    const track = ov.querySelector('.intro-track');
    const dots = ov.querySelectorAll('.intro-dots span');
    const sync = () => {
      const i = Math.max(0, Math.min(last, Math.round(track.scrollLeft / (track.clientWidth || 1))));
      dots.forEach((d, k) => d.classList.toggle('active', k === i));
      ov.querySelector('.intro-start').textContent = i === last ? 'Начать ✨' : 'Дальше →';
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
    // CTA финального слайда: гасим интро здесь, сам же клик ловит
    // делегированный обработчик 13-events (data-act="chat-fn") и открывает
    // чат Астролога с формой построения карты
    if (needChart) {
      ov.querySelector('[data-intro-chart]').addEventListener('click', () => {
        try { localStorage.setItem('oracle_intro_seen', '1'); } catch (e) {}
        ov.remove();
      });
    }
  };

  // Гайд первого захода в чат: лёгкий оверлей по окну чата, 4 шага, 1 раз.
  // Флаг отдельный от глобального интро (или больше, или меньше — не мешаем).

  app.maybeChatGuide = function() {
    // Первый диалог уже объясняется тёплым intro-блоком в самом чате.
    // Полноэкранный туториал оставлен только для ручной QA-проверки по ?guide=1,
    // чтобы не прерывать момент, когда пользовательница готова написать.
    if (!new URLSearchParams(location.search).has('guide')) return;
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
    const name = this.me && this.me.name ? this.me.name : 'Мой профиль';
    const initial = this.me && this.me.name ? esc(this.me.name[0].toUpperCase()) : 'О';
    root.innerHTML = `
      <header class="app-header">
        <button class="user-pill" data-act="go" data-goto="profile" aria-label="Открыть профиль: ${esc(name)}">
          <span class="avatar" aria-hidden="true">${initial}</span>
          <span class="user-name">${esc(name)}</span>
        </button>
        <div class="brand-lockup" aria-label="OracleAI — личное пространство ритуалов">
          <span class="brand-mark"><img src="/static/img/oracle-mark.png" alt="" aria-hidden="true"></span>
          <span class="brand-title">ORACLE<small>AI</small></span>
        </div>
        <button class="bell" data-act="bell" aria-label="Открыть уведомления" title="Уведомления">
          ${sigilIcon('bell')}<span class="bell-dot" aria-hidden="true"></span>
        </button>
      </header>
      <div id="app-main"></div>
      <nav class="app-nav" aria-label="Основная навигация"><div class="main-nav" id="main-nav"></div></nav>`;
    this.renderNav();
  };


  app.navItems = function() {
    return [
      { k: 'home', ico: 'home', t: t('today'), hint: t('ritual') },
      { k: 'hub', ico: 'hub', t: t('chats'), hint: t('guides') },
      { k: 'profile', ico: 'profile', t: t('mine'), hint: t('profile') }
    ];
  };

  app.renderNav = function() {
    const active = this.chat.key ? 'hub' : this.view;
    document.getElementById('main-nav').innerHTML = this.navItems().map(n => `
      <button class="nav-btn ${active === n.k ? 'active' : ''}" data-act="go" data-goto="${n.k}" aria-current="${active === n.k ? 'page' : 'false'}" aria-label="${esc(n.t)}: ${esc(n.hint)}">
        <span class="nav-ico">${sigilIcon(n.ico)}</span>
        <span class="nav-copy"><b>${esc(n.t)}</b><small>${esc(n.hint)}</small></span>
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
    try {
      const [diary, prompt, practices] = await Promise.all([
        api('/api/diary'),
        api('/api/diary/prompt').catch(() => null),
        api('/api/practices').catch(() => null)
      ]);
      this.dailyPulse = { diary, prompt, practices };
    } catch (e) { this.dailyPulse = null; }
    if (this.view === 'home') this.renderHome(document.getElementById('app-main'));
  };


  const AGENT_BRAND = {
    oracle: { name: 'Лилит', title: 'Личный Оракул', emoji: '🔮', accent: '#e6c178', tagline: 'Мягко помогает услышать себя и увидеть следующий шаг.' },
    astro:  { name: 'Урания', title: 'Астролог', emoji: '🌠', accent: '#b9a6ff', tagline: 'Переводит язык звёзд в ясные опоры на каждый день.' },
    tarot:  { name: 'Мадам Ленорман', title: 'Таролог', emoji: '🃏', accent: '#e7a8c2', tagline: 'Читает символы карт бережно и без категоричных ответов.' }
  };

  app.normalizeAgent = function(raw, key) {
    const code = (raw && raw.code) || key || 'oracle';
    const brand = AGENT_BRAND[code] || {};
    const agent = Object.assign({}, brand, raw || {}, { code });
    // API может вернуть служебное имя вида «oracle» — оно не является именем персонажа.
    if (!agent.name || String(agent.name).toLowerCase() === code) agent.name = brand.name || 'Твой Оракул';
    if (!agent.title) agent.title = brand.title || 'Проводник';
    if (!agent.emoji) agent.emoji = brand.emoji || '✦';
    if (!agent.accent) agent.accent = brand.accent || '#e6c178';
    if (!agent.tagline && brand.tagline) agent.tagline = brand.tagline;
    return agent;
  };

  app.agentSpec = function(key) {
    const a = this.agents.find(x => x.code === key);
    return this.normalizeAgent(a, key);
  };

  /* ═══ ЭКРАН «СЕГОДНЯ» — статичная база ═══ */

