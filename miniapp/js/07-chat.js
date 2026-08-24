/* chat: чат-агент, сессии, лунная неделя, тулбокс, отправка */
  app.openChat = function(key, after) {
    haptic('soft');
    // Панель инструментов не должна оставаться поверх нового диалога.
    if (typeof this.setToolbox === 'function') this.setToolbox(false);
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
    if (after) {
      setTimeout(() => {
        after();
        // Tool flows explain themselves; the generic guide must not cover them.
        if (!this.chat.pending) this.maybeChatGuide();
      }, 60);
    } else {
      this.maybeChatGuide();
    }
  };

  // список чатов-сессий агента (до 5)

  app.refreshSessions = async function() {
    try { this.chat.sessions = await api('/api/chat/' + this.chat.key + '/sessions'); }
    catch (e) { this.chat.sessions = this.chat.sessions || []; }
  };


  app.loadThread = async function(key) {
    try {
      const r = await api('/api/chat/' + key);
      this.chat.spec = this.normalizeAgent(r.agent, key);
      this.chat.tid = r.thread_id || null;
      this.chat.messages = (r.messages || []).map(m => ({ role: m.role, text: m.text }));
      // если истории нет — приветствие агента, чат не выглядит пустым
      if (!this.chat.messages.length && (r.agent && r.agent.greeting)) {
        this.chat.messages = [{ role: 'assistant', text: r.agent.greeting }];
      }
    } catch (e) {
      this.chat.messages = [{ role: 'assistant', widget: this.chatRecoveryHtml('history') }];
    }
    await this.refreshSessions();
    if (this.chat.key === key) this.renderChat(document.getElementById('app-main'));
  };


  app.toast = function(msg) {
    const t = document.createElement('div');
    t.className = 'toast'; t.textContent = msg;
    document.body.appendChild(t);
    setTimeout(() => t.remove(), 2400);
  };

  app.proofHtml = function(proof) {
    if (!proof) return '';
    const en = oracleLang() === 'en';
    const mode = proof.mode === 'deterministic'
      ? (en ? 'Grounded in calculated tools' : 'Проверено по расчётным инструментам')
      : proof.mode === 'safety'
        ? (en ? 'Safety-first response' : 'Ответ по safety-протоколу')
        : (en ? 'Offline reflective mode' : 'Офлайн-рефлексия');
    const labels = en ? {
      get_chart: 'Natal chart', get_all_placements: 'All placements', get_placement: 'Single placement',
      get_matrix: 'Matrix', get_life_path: 'Life path', get_chinese_zodiac: 'Chinese zodiac',
      get_transits: 'Current sky', get_moon_week: 'Moon week', get_career_windows: 'Career windows',
      get_compatibility: 'Compatibility', list_partners: 'Saved partners', draw_tarot: 'Tarot draw',
      palm_scanner: 'Palm evidence', palm_photo_guide: 'Photo guide', palm_history: 'Palm history',
      suggest_practice: 'Practice catalogue', recall_diary: 'Diary', recall_memory: 'Memory', save_memory: 'Memory'
    } : {
      get_chart: 'Натальная карта', get_all_placements: 'Все placements', get_placement: 'Один placement',
      get_matrix: 'Матрица', get_life_path: 'Число пути', get_chinese_zodiac: 'Китайский зодиак',
      get_transits: 'Текущее небо', get_moon_week: 'Лунная неделя', get_career_windows: 'Окна решений',
      get_compatibility: 'Совместимость', list_partners: 'Сохранённые люди', draw_tarot: 'Расклад Таро',
      palm_scanner: 'Evidence ладони', palm_photo_guide: 'Гид по фото', palm_history: 'История ладони',
      suggest_practice: 'Каталог практик', recall_diary: 'Дневник', recall_memory: 'Память', save_memory: 'Память'
    };
    const used = (proof.tools_used || []).map(name => labels[name] || name).slice(0, 4);
    return `<div class="message-proof" aria-label="${esc(mode)}"><span class="message-proof__mode">✦ ${esc(mode)}</span>${used.length ? `<span class="message-proof__tools">${used.map(item => esc(item)).join(' · ')}</span>` : ''}</div>`;
  };

  // Ошибки остаются отдельными бережными состояниями, без технического текста.
  app.chatRecoveryHtml = function(kind) {
    const history = kind === 'history';
    return `<div class="chat-recovery" role="status">
      <strong>${history ? 'История сейчас не открылась' : 'Ответ пока не пришёл'}</strong>
      <p>${history ? 'Можно начать разговор прямо сейчас или попробовать загрузить сохранённые сообщения ещё раз.' : 'Твой вопрос не потерялся в этом диалоге. Проверь соединение и отправь его ещё раз, когда будешь готов(а).'}</p>
      ${history ? '<button class="chat-retry" data-act="retry-chat">Загрузить историю</button>' : ''}
    </div>`;
  };

  // отправка в активную сессию (если есть) — иначе первый вопрос создаёт тред

  app.chatPost = async function(text) {
    const a = this.chat.spec;
    if (this.chat.tid) {
      return await api(`/api/chat/${a.code}/sessions/${this.chat.tid}`,
        { method: 'POST', body: JSON.stringify({ text }) });
    }
    const r = await api(`/api/chat/${a.code}`, { method: 'POST', body: JSON.stringify({ text }) });
    if (r.thread_id) this.chat.tid = r.thread_id;
    return r;
  };


  app.toggleSessions = function() {
    haptic('light');
    const panel = document.getElementById('sess-panel');
    const trigger = document.querySelector('.chat-thread-toggle');
    if (!panel) return;
    const open = panel.style.display === 'none';
    panel.style.display = open ? 'block' : 'none';
    if (trigger) trigger.setAttribute('aria-expanded', String(open));
  };

  // Лунный календарь: компакт — «кратко о сегодня» + раскрытие всей недели по кнопке

  app.toggleMoonWeek = function() {
    haptic('light');
    const wk = document.getElementById('moon-week');
    if (!wk) return;
    const open = wk.classList.toggle('show');
    document.querySelectorAll('.moon-toggle, .moon-today').forEach(el => {
      if (!el.closest('#moon-week')) el.classList.toggle('open', open);
    });
    if (!open) this.collapseMoonDays();
  };

  app.collapseMoonDays = function() {
    document.querySelectorAll('#moon-week .mc-day').forEach(d => {
      d.classList.remove('open');
      const det = d.querySelector('.mc-detail');
      if (det) det.hidden = true;
    });
  };

  app.toggleMoonDay = function(i) {
    haptic('soft');
    const day = Array.from(document.querySelectorAll('#moon-week .mc-day'))
      .find(d => d.dataset.i === String(i));
    if (!day) return;
    const det = day.querySelector('.mc-detail');
    const open = day.classList.toggle('open');
    if (det) det.hidden = !open;
  };

  // Лунный календарь: детальный модал со всей неделей (загружена в moonWeek)

  app.openMoon = function() {
    haptic('light');
    const arr = this.moonWeek || [];
    if (!arr.length) { this.toast('Лунный календарь скоро подтянет свет 🌙'); return; }
    const wd = WD_SHORT, months = MON_RU;
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
  };


  app.switchPTab = function(tab) {
    haptic('light');
    document.querySelectorAll('.ptab').forEach(b => b.classList.toggle('active', b.dataset.tab === tab));
    document.querySelectorAll('.ptab-pane').forEach(p => p.classList.toggle('active', p.id === 'ptab-' + tab));
  };


  app.newSession = async function() {
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
  };


  app.openSession = async function(id) {
    try {
      const r = await api(`/api/chat/${this.chat.key}/sessions/${id}`);
      this.chat.spec = this.normalizeAgent(r.agent, this.chat.key);
      this.chat.tid = r.thread_id;
      this.chat.messages = (r.messages || []).map(m => ({ role: m.role, text: m.text }));
      if (!this.chat.messages.length && r.agent && r.agent.greeting) {
        this.chat.messages = [{ role: 'assistant', text: r.agent.greeting }];
      }
    } catch (e) {
      this.chat.messages = [{ role: 'assistant', widget: this.chatRecoveryHtml('history') }];
    }
    await this.refreshSessions();
    this.renderChat(document.getElementById('app-main'));
  };


  app.delSession = async function(id) {
    await api(`/api/chat/${this.chat.key}/sessions/${id}`, { method: 'DELETE' });
    await this.refreshSessions();
    if (id === this.chat.tid) {
      const next = (this.chat.sessions || [])[0];
      if (next) { await this.openSession(next.id); return; }
      await this.newSession();
    } else {
      this.renderChat(document.getElementById('app-main'));
    }
  };


  app.renderChat = function(main) {
    const a = this.chat.spec || this.agentSpec(this.chat.key || 'oracle');
    const messages = this.chat.messages;
    const busy = this.chat.busy;
    const pending = this.chat.pending;
    const agents = this.agents.length ? this.agents : AGENT_FALLBACK;
    const suggest = (TEMPLATES[a.code] || a.suggestions || []).slice(0, 3);
    const currentFeatures = FEATURES[a.code] || [];
    const sessionCount = (this.chat.sessions || []).length;
    const last = messages[messages.length - 1];
    const cheer = messages.length > 1 && last.role === 'assistant' && !busy && !(last.text || '').startsWith('😔') && !last.widget;

    // виджет-сообщение (спидометр любви и т.п.) — это готовый HTML, не текст:
    // rich() его экранировал бы, поэтому рендерим как есть в .msg.assistant
    const body = messages.map(m =>
      m.widget ? `<div class="msg assistant">${m.widget}</div>`
        : `<div class="msg ${m.role === 'user' ? 'user' : 'assistant'}">${richMd(m.text)}${m.proof ? this.proofHtml(m.proof) : ''}</div>`).join('');

    // Первый экран чата — короткая, персональная точка входа вместо универсального hero-текста.
    const introGuides = {
      oracle: { kicker: 'ТВОЁ ПРОСТРАНСТВО ДЛЯ ЯСНОСТИ', title: 'Начни с того, что сейчас важнее всего', text: 'Можно написать одну мысль, чувство или вопрос — вместе найдём бережный ориентир.' },
      astro: { kicker: 'АСТРОЛОГИЧЕСКИЙ ОРИЕНТИР', title: 'Посмотри на свой ритм через карту', text: 'Собери натальную карту или задай вопрос о ближайшем периоде — только на основе доступных данных.' },
      tarot: { kicker: 'РАСКЛАД БЕЗ КАТЕГОРИЧНЫХ ОТВЕТОВ', title: 'Сформулируй вопрос к картам', text: 'Выберем схему и спокойно посмотрим на ситуацию с разных сторон.' },
      chiromant: { kicker: 'БЕРЕЖНОЕ ЧТЕНИЕ ЛАДОНИ', title: 'Сначала — что действительно видно', text: 'Пришли фото ладони: Мира отделит наблюдение от символической гипотезы и покажет границы точности.' }
    };
    const introGuide = introGuides[a.code] || introGuides.oracle;
    const introHtml = messages.length <= 1 ? `
        <section class="agent-intro agent-intro--compact agent-intro--${esc(a.code)}" style="${this.agentThemeStyle(a, a.code)}" aria-label="Знакомство с проводником">
          <span class="ai-kicker">${introGuide.kicker}</span>
          <div class="ai-persona">
            <div class="ai-face">${agentSprite(a, false)}</div>
            <div class="ai-persona-copy">
              <div class="ai-name">${esc(a.name || 'Лилит')}</div>
              <div class="ai-role">${esc(a.title || 'Личный Оракул')}</div>
            </div>
          </div>
          <div class="ai-next">
            <b>${introGuide.title}</b>
            <span>${introGuide.text}</span>
          </div>
        </section>` : '';

    const pendHtml = pending ? this.pendingHtml(pending) : '';

    main.innerHTML = `
      <div class="chat-shell chat-shell--${esc(a.code)}" style="${this.agentThemeStyle(a, a.code)}">
        <div class="chat-head">
          <button class="back" data-act="back" aria-label="Вернуться к проводникам" title="К проводникам">‹</button>
          <div class="agent-avatar" style="${this.agentThemeStyle(a, a.code)}">${agentSprite(a, cheer)}</div>
          <div style="flex:1;min-width:0">
            <div class="cname">${esc(a.name || 'Лилит')}</div>
            <div class="tsub">${esc(a.title || a.role || 'Личный Оракул')}</div>
            <div class="chat-proof-strip" aria-label="${homeT('profileQuality')}">
              <span>✦ ${homeT('evidenceFirst')}</span>${(a.capabilities && a.capabilities.length) ? `<span>· ${homeFormat('toolCount', { count: a.capabilities.length })}</span>` : ''}
            </div>
          </div>
          <button type="button" class="chat-thread-toggle" data-act="sessions" aria-expanded="false" aria-controls="sess-panel" aria-label="Открыть мои чаты">
            <span class="chat-thread-toggle__icon">${sigilIcon('monthly')}</span>
            <span class="chat-thread-toggle__copy"><small>МОИ ЧАТЫ</small><b>${sessionCount || 1} из 5</b></span>
            <span class="chat-thread-toggle__chevron" aria-hidden="true">⌄</span>
          </button>
          <button type="button" class="chat-new-session" data-act="new-session" aria-label="Начать новый чат" title="Начать новый чат">
            ${sigilIcon('spark')}<span>Новый</span>
          </button>
        </div>
        <section class="sess-panel" id="sess-panel" style="display:none" aria-label="Мои чаты с ${esc(a.name || 'проводником')}">
          <div class="sess-head">
            <div><span>Твои разговоры</span><small>${sessionCount || 0} из 5 · каждый чат хранит свой контекст</small></div>
            <button type="button" class="sess-create" data-act="new-session">${sigilIcon('spark')}<span>Новый</span></button>
          </div>
          <div class="sess-list">
            ${sessionCount ? (this.chat.sessions || []).map(s => `
              <div class="sess-row ${s.id === this.chat.tid ? 'active' : ''}" data-act="open-session" data-tid="${s.id}">
                <span class="sess-status" aria-hidden="true"></span>
                <div class="sess-copy"><div class="sess-t">${esc(s.title || 'Новый разговор')}</div><div class="sess-prev">${esc(s.last_text || 'Здесь можно продолжить диалог.')}</div></div>
                <button type="button" class="sess-del" data-act="del-session" data-tid="${s.id}" aria-label="Удалить этот чат" title="Удалить чат">✕</button>
              </div>`).join('') : '<div class="sess-empty">Первый разговор создастся, когда ты отправишь сообщение.</div>'}
          </div>
        </section>
        <div class="agent-tabs" role="tablist" aria-label="Выбор проводника">
          ${agents.slice(0, 4).map(b => `
            <button type="button" class="atab ${b.code === a.code ? 'active' : ''}" style="${this.agentThemeStyle(b, b.code)}" data-act="chat" data-chat="${b.code}" role="tab" aria-selected="${b.code === a.code ? 'true' : 'false'}">
              <span class="atab-face"><img src="${esc(b.avatar || `/static/img/agents/${b.code}.jpg`)}" alt="" loading="lazy" onerror="this.onerror=null;this.src='/static/img/oracle-mark.png'"></span><span>${esc(b.name.split(' ')[0])}</span>
            </button>`).join('')}
        </div>
        <div class="chat-messages" id="chat-messages">
          ${introHtml}
          ${body}
          ${pendHtml}
          ${busy ? `<div class="msg assistant"><div class="typing"><span></span><span></span><span></span></div></div>` : ''}
        </div>
        <div class="composer">
                      <div class="composer-context">
            <span class="composer-presence"><i aria-hidden="true"></i>${esc(a.name || 'Проводник')} рядом</span>
            <div class="composer-context-actions">
              ${a.code === 'chiromant' ? '<button type="button" class="palm-quick-upload" data-act="palm-start" aria-label="Добавить фото ладони"><span aria-hidden="true">✋</span><span>Фото ладони</span></button>' : ''}
              <button type="button" class="composer-tools-copy" data-act="tool-toggle" aria-label="Открыть палитру инструментов" aria-expanded="false" aria-controls="tool-expand"><span class="composer-tools-copy__icon">${sigilIcon('spark')}</span><span>Инструменты</span><span class="composer-tools-copy__chevron" aria-hidden="true">↑</span></button>
            </div>
          </div>

          <div class="composer-top">
            <textarea class="ipt" id="chat-input" rows="1" maxlength="1600" placeholder="Напиши ${esc(a.name || 'Лилит')} — как есть…" autocomplete="off" spellcheck="true" aria-label="Сообщение для ${esc(a.name || 'Лилит')}">${esc(this.chat.draft || '')}</textarea>
            <button class="send-btn" id="send-btn" data-act="send" aria-label="Отправить сообщение"${busy ? ' disabled aria-disabled="true"' : ''}>${busy ? '…' : '➤'}</button>
          </div>
          ${suggest.length ? `
          <div class="suggest-chips" aria-label="Идеи для своего вопроса">
            ${suggest.map(s => `<button type="button" class="chip tpl" data-act="fill" data-val="${esc(s)}">${esc(s)}</button>`).join('')}
          </div>` : ''}
        </div>
        <div class="tool-expand" id="tool-expand" aria-hidden="true">
          <div class="te-mask" data-act="tool-toggle"></div>
          <section class="te-sheet" role="dialog" aria-modal="true" aria-label="Инструменты текущего проводника">
            <div class="te-handle" aria-hidden="true"></div>
            <div class="te-head">
              <div><span class="te-eyebrow">ИНСТРУМЕНТЫ ДИАЛОГА</span><span class="te-title">С чем поработаем?</span><p class="te-intro">Выбери один точный шаг — результат появится прямо в этом разговоре.</p></div>
              <button class="te-close" data-act="tool-toggle" aria-label="Закрыть инструменты">✕</button>
            </div>
            <div class="te-body">
              ${currentFeatures.length ? `
                <div class="te-group te-current">
                  <div class="te-current-title" style="${this.agentThemeStyle(a, a.code)}">
                    <span>С ${esc(a.name || 'проводником')}</span><small>в этом диалоге</small>
                  </div>
                  <div class="te-grid">
                    ${currentFeatures.map(f => `
                      <button class="te-chip" data-act="chat-fn" data-chat="${a.code}" data-fn="${f.h}" data-testid="fn-${f.id}">
                        <span class="te-ico">${sigilIcon(f.id)}</span><span class="te-chip-copy"><b>${esc(f.t)}</b><small>${esc(f.d)}${f.m ? ' · ' + esc(f.m) : ''}</small></span><span class="te-arrow" aria-hidden="true">›</span>
                      </button>`).join('')}
                  </div>
                </div>` : ''}
            </div>
          </section>
        </div>
      </div>`;
    this.scrollToBottom();
  };


  app.pendingHtml = function(p) {
    const q = s => esc(s).replace(/'/g, "&#39;");
    switch (p.kind) {
      case 'tarot-pick':
        return (() => {
          const cur = p.spreads.find(s => s.code === p.spread) || { title: 'Расклад', emoji: '🎴', hint: 'Тапни, чтобы выбрать схему' };
          const prompts = [
            'Что сейчас важнее всего увидеть в этой ситуации?',
            'Как мне бережно действовать в отношениях?',
            'На что направить энергию в ближайшую неделю?',
          ];
          return `<div class="msg assistant">
            <div class="chat-widget tarot-picker-widget ${p.drawing ? 'is-drawing' : ''}">
              <div class="tarot-kicker">ЛИЧНЫЙ РИТУАЛ</div>
              <div class="w-title" style="margin:0">🎴 Выбери схему и вопрос</div>
              <div class="w-sub tarot-picker-sub">Символический взгляд на ситуацию — без готовых приказов.</div>
              <button class="pick-sel-btn tarot-deck-select" data-act="deck-open" ${p.drawing ? 'disabled' : ''}>
                <span class="pick-sel-ico">${p.deck && p.deck.tradition === 'Petit Lenormand' ? '◇' : '🎴'}</span>
                <span class="pick-sel-txt"><span class="pick-sel-t">${esc(tarotDeckLabel(p.deck))}</span><span class="pick-sel-d">${esc((p.deck && p.deck.card_count) || 78)} карт · сменить школу</span></span><span class="pick-sel-go">⚙</span>
              </button>
              <div class="tarot-deck-source"><span aria-hidden="true">●</span>${esc(tarotDeckStatus(p.deck))}</div>
              <button class="pick-sel-btn" data-act="pick-open" ${p.drawing ? 'disabled' : ''}>
                <span class="pick-sel-ico">${esc(cur.emoji || '🎴')}</span>
                <span class="pick-sel-txt">
                  <span class="pick-sel-t">${esc(cur.title)}</span>
                  <span class="pick-sel-d">${esc(cur.hint || cur.desc || 'Выбрать схему расклада')}</span>
                </span>
                <span class="pick-sel-go">›</span>
              </button>
              <div class="swipe-hint">Нажми на строку, чтобы изменить выбор</div>
              <div class="tarot-question-label">О чём спросить?</div>
              <div class="tarot-question-prompts">${prompts.slice(0, 2).map(value => `<button class="tarot-question-prompt${p.q === value ? ' is-active' : ''}" data-act="tarot-question" data-value="${q(value)}" ${p.drawing ? 'disabled' : ''}>${esc(value)}</button>`).join('')}</div>
              ${p.err ? `<div class="s-err">${esc(p.err)}</div>` : ''}
              <textarea class="ipt" id="tarot-q" rows="2" placeholder="Твой вопрос к картам…" ${p.drawing ? 'disabled' : ''}
                style="margin-top:10px;resize:none">${q(p.q || '')}</textarea>
              <div class="tarot-draw-status" aria-live="polite">${p.drawing ? '<span class="tarot-draw-orbit" aria-hidden="true"></span><span>Колода собирает твой расклад…</span>' : '<span class="tarot-draw-dot" aria-hidden="true"></span><span>После вопроса вытянем карты по одной.</span>'}</div>
              <button class="btn btn-primary tarot-draw-btn" style="margin-top:10px" data-act="draw" ${p.drawing ? 'disabled aria-busy="true"' : ''}>${p.drawing ? 'Собираем расклад…' : 'Потянуть карты'}</button>
            </div></div>`;
        })();

      case 'tarot-cards': {
        const opened = p.revealed.filter(Boolean).length;
        const total = p.cards.length;
        return `<div class="msg assistant">
          <div class="chat-widget tarot-cards-widget">
            <div class="tarot-kicker">ТВОЙ РАСКЛАД</div>
            <div class="tarot-cards-head">
              <div>
                <div class="w-title">Открой карты по одной</div>
                ${p.question ? `<div class="w-sub">Твой вопрос: <b>«${esc(p.question)}»</b></div>` : ''}
              </div>
              <div class="tarot-card-progress" aria-label="Открыто карт: ${opened} из ${total}"><span>${opened} из ${total}</span><i style="--tarot-progress:${(opened / total) * 100}%"></i></div>
            </div>
            <div class="tarot-grid sh-${esc(p.spread || 'three')}">
              ${p.positions.map((pos, i) => {
                const c = p.cards[i] || {};
                const canReveal = i === (Number.isInteger(p.nextReveal) ? p.nextReveal : opened);
                return `
                <div class="tpos${canReveal && !p.revealed[i] ? ' is-next' : ''}" data-i="${i}">
                  <button type="button" class="tcard ${p.revealed[i] ? 'open' : 'dealt'}" style="${p.revealed[i] ? '' : 'animation-delay:' + (i * 80) + 'ms'}" data-act="flip" data-i="${i}" aria-label="${p.revealed[i] ? esc(c.name) : 'Открыть карту: ' + esc(pos)}" ${p.revealed[i] ? 'aria-pressed="true"' : 'aria-pressed="false"'}>
                    <span class="tcard-inner">
                      <span class="tcard-face tcard-back"><img src="/static/img/card-back.jpg" alt="" loading="lazy"></span>
                      <span class="tcard-face tcard-front${c.reversed ? ' rev' : ''}"><img src="${tarotAssetUrl(c, p.ledger || p.deck)}" alt="${p.revealed[i] ? esc(c.name) : 'Закрытая карта'}" loading="lazy">
                        ${c.reversed ? '<span class="t-rev">↺ перевёрнута</span>' : ''}</span>
                    </span>
                  </button>
                  <div class="tpos-pos">${esc(pos)}</div>
                  <div class="tpos-mean">${p.revealed[i] ? `${esc(c.name)}${c.reversed ? ' ↺' : ''}` : 'Нажми, чтобы открыть'}</div>
                  ${p.revealed[i] ? `<div class="tpos-desc">${esc(c.meaning)}</div>` : ''}
                </div>`;
              }).join('')}
            </div>
            ${p.allRevealed ? `<section class="tarot-thread tarot-thread--revealed" aria-label="Нить расклада">
                <div class="tarot-thread-kicker">НИТЬ РАСКЛАДА</div>
                <p>Карты раскрылись. Сначала почувствуй, как роли откликаются вместе, а затем соберём личный смысл без поспешных выводов.</p>
                <div class="tarot-thread-map">${p.positions.map((pos, i) => {
                  const c = p.cards[i] || {};
                  return `<span><b>${esc(pos)}:</b> ${esc(c.name || 'карта')}</span>`;
                }).join('')}</div>
              </section>
              <button class="btn btn-primary tarot-interpret-btn" style="margin-top:14px" data-act="interpret">Собрать личный смысл</button>`
              : `<div class="t-hint">Открывай карты по порядку: каждая роль подскажет, как читать следующую.</div>`}
          </div></div>`;
      }

      case 'chart':
        return `<div class="msg assistant">
          <div class="chat-widget">${p.html || (p.loading ? '<div class="typing"><span></span><span></span><span></span></div>' : '')}</div>
        </div>`;

      case 'compat':
        return `<div class="msg assistant compat-message">
          <section class="chat-widget compat-flow" aria-label="Проверка совместимости">
            <div class="compat-flow__head"><span class="compat-flow__sigil" aria-hidden="true">${sigilIcon('compat')}</span><div><span class="result-kicker">ЛИЧНЫЙ РАЗБОР</span><div class="w-title">Посмотрим на ритм связи</div></div></div>
            <div class="w-sub">Выбери контекст и дату рождения. Это ориентир для разговора, а не оценка вас или ваших отношений.</div>
            <div class="compat-steps" aria-label="Три спокойных шага">
              <span class="is-current"><i>1</i> Связь</span><span><i>2</i> Дата</span><span><i>3</i> Ориентир</span>
            </div>
            <p class="compat-flow__prompt">Как вы связаны сейчас?</p>
            <div class="rel-chips" role="group" aria-label="Тип связи">
              ${[['love','compat','Пара'],['friend','spark','Дружба'],['work','career','Дело'],['family','home','Семья']].map(([k, icon, t]) =>
                `<button type="button" class="rel-chip${p.relation === k ? ' sel' : ''}" data-act="compat-rel" data-rel="${k}" aria-pressed="${p.relation === k ? 'true' : 'false'}"><span>${sigilIcon(icon)}</span>${t}</button>`).join('')}
            </div>
            <div class="compat-flow__fields">
              <label class="compat-field"><span>Имя человека <em>необязательно</em></span><input class="ipt" id="cp-name" value="${esc(p.name || '')}" placeholder="Например, Аня" autocomplete="name"/></label>
              <label class="compat-field"><span>Дата рождения <em>обязательно</em></span><input class="ipt" id="cp-date" type="date" value="${esc(p.date || '')}" required aria-describedby="compat-date-help"/></label>
            </div>
            <small id="compat-date-help" class="compat-help"><span aria-hidden="true">✦</span> Дата нужна для расчёта; имя только добавит тепла в обращение.</small>
            <button class="btn btn-primary compat-submit" data-act="compat"><span>Открыть мой ориентир</span><span aria-hidden="true">→</span></button>
          </section></div>`;

      case 'compat-processing':
        return `<div class="msg assistant compat-message">
          <section class="chat-widget compat-processing" role="status" aria-live="polite">
            <div class="compat-processing__orb" aria-hidden="true"><span></span><span></span><span>${sigilIcon('compat')}</span></div>
            <div><span class="result-kicker">СОВМЕСТИМОСТЬ</span><strong>Собираю ритм вашей связи</strong><p>Сопоставляю основные сферы. Через несколько секунд здесь появится спокойный ориентир.</p><span class="compat-processing__note">Можно просто остаться в этом диалоге</span></div>
          </section></div>`;

      case 'moon':
        return this.moonWidget(p);

      case 'matrix':
        return this.matrixWidget(p);

      case 'today':
        return this.todayWidget(p);

      case 'practices':
        return this.practicesWidget(p);

      case 'diary':
        return this.diaryWidget(p);

      case 'career':
        return this.careerWidget(p);

      case 'palm':
        return p.html ? `<div class="msg assistant">${p.html}</div>` : '';

      case 'history':
        return `<div class="msg assistant">
          <div class="chat-widget">
            <div class="w-title">📚 Твои расклады</div>
            ${p.loading ? '<div class="loader-ring"></div>' : (p.rows || '<div style="color:var(--text-faint);font-size:12.5px">Пока пусто — первый расклад ждёт тебя ✨</div>')}
          </div></div>`;

      default: return '';
    }
  };

  /* ═══ ВИДЖЕТЫ v5.3: утро, луна, матрица, карьерные окна, практики, дневник ═══ */


  app.closeChat = function() {
    this.chat.key = null;
    this.chat.pending = null; // гонка B1: закрыли чат — несозревший виджет никому не нужен
    this.go('hub');
  };
  // свайп по табам агентов: вбок листаем Оракул → Астролог → Таролог → …

  app.cycleAgent = function(dir) {
    const list = this.agents.length ? this.agents.map(b => b.code) : ['oracle', 'astro', 'tarot', 'chiromant'];
    const i = list.indexOf(this.chat.key);
    if (i < 0) return;
    this.openChat(list[(i + dir + list.length) % list.length]);
  };
  // панель «Все инструменты» (bottom sheet): свайп вверх у нижнего края ленты

  app.setToolbox = function(open) {
    const el = document.getElementById('tool-expand');
    const triggers = document.querySelectorAll('.composer-tools-copy');
    const next = !!open;
    if (!el) return;

    el.classList.toggle('open', next);
    el.setAttribute('aria-hidden', next ? 'false' : 'true');
    document.body.classList.toggle('toolbox-open', next);
    triggers.forEach(trigger => trigger.setAttribute('aria-expanded', next ? 'true' : 'false'));

    if (!this._toolboxKeydownReady) {
      this._toolboxKeydownReady = true;
      document.addEventListener('keydown', event => {
        if (event.key === 'Escape' && document.getElementById('tool-expand')?.classList.contains('open')) {
          event.preventDefault();
          this.setToolbox(false);
        }
      });
    }

    if (next) {
      haptic('soft');
      const first = el.querySelector('.te-chip, .te-close');
      if (first) setTimeout(() => first.focus(), 180);
    } else if (triggers[0]) {
      triggers[0].focus();
    }
  };

  app.toggleToolbox = function() {
    const el = document.getElementById('tool-expand');
    this.setToolbox(el ? !el.classList.contains('open') : false);
  };

  app.clearThread = async function() {
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
  };

  /* ── отправка вопроса агенту ── */

  app.doSend = async function(text) {
    const a = this.chat.spec;
    const val = (text || (document.getElementById('chat-input') || {}).value || '').trim();
    if (!val || this.chat.busy) return;
    haptic('light');
    vb(15);
    const input = document.getElementById('chat-input');
    if (input) input.value = '';
    this.chat.draft = '';
    this.chat.messages.push({ role: 'user', text: val });
    this.chat.busy = true;
    this.renderChat(document.getElementById('app-main'));
    try {
      const r = await this.chatPost(val);
      haptic('success');
      vb([10, 40, 14]);
      this.chat.messages.push({ role: 'assistant', text: r.answer, proof: r.proof || null });
    } catch (e) {
      this.chat.messages.push({ role: 'assistant', widget: this.chatRecoveryHtml('reply') });
    }
    this.chat.busy = false;
    this.renderChat(document.getElementById('app-main'));
    // деликатная подсветка только что пришедшего ответа
    const lastMsg = document.querySelector('.chat-messages .msg:last-child');
    if (lastMsg) lastMsg.classList.add('fresh');
  };

  /* ═══ ФИЧА: РАСКЛАД ТАРО (вопрос → карты → LLM) ═══ */

  app.pendingQ = function(v) { if (this.chat.pending) { this.chat.pending.q = v; this.chat.pending.err = ''; } };

  // Полноэкранный выбор схемы расклада — весь список с описаниями (премium)

