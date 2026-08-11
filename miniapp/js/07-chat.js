/* chat: чат-агент, сессии, лунная неделя, тулбокс, отправка */
  app.openChat = function(key, after) {
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
    this.maybeChatGuide();
  };

  // список чатов-сессий агента (до 5)

  app.refreshSessions = async function() {
    try { this.chat.sessions = await api('/api/chat/' + this.chat.key + '/sessions'); }
    catch (e) { this.chat.sessions = this.chat.sessions || []; }
  };


  app.loadThread = async function(key) {
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
  };


  app.toast = function(msg) {
    const t = document.createElement('div');
    t.className = 'toast'; t.textContent = msg;
    document.body.appendChild(t);
    setTimeout(() => t.remove(), 2400);
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
    const p = document.getElementById('sess-panel');
    if (p) p.style.display = p.style.display === 'none' ? 'block' : 'none';
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
    const a = this.chat.spec;
    const messages = this.chat.messages;
    const busy = this.chat.busy;
    const pending = this.chat.pending;
    const features = FEATURES[a.code] || [];
    const agents = this.agents.length ? this.agents : AGENT_FALLBACK;
    const suggest = (TEMPLATES[a.code] || a.suggestions || []).slice(0, 3);
    const last = messages[messages.length - 1];
    const cheer = messages.length > 1 && last.role === 'assistant' && !busy && !last.text.startsWith('😔');

    // виджет-сообщение (спидометр любви и т.п.) — это готовый HTML, не текст:
    // rich() его экранировал бы, поэтому рендерим как есть в .msg.assistant
    const body = messages.map(m =>
      m.widget ? `<div class="msg assistant">${m.widget}</div>`
        : `<div class="msg ${m.role === 'user' ? 'user' : 'assistant'}">${rich(m.text)}</div>`).join('');

    // первый экран чата: портрет агента + кто он (когда истории ещё нет)
    const introHtml = messages.length <= 1 ? `
      <div class="agent-intro" style="--ac:${esc(a.accent || 'var(--gold)')}">
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
          <div class="agent-avatar" style="--ac:${esc(a.accent || 'var(--gold)')}">${agentSprite(a, cheer)}</div>
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
        <div class="agent-tabs">
          ${agents.slice(0, 3).map(b => `
            <span class="atab ${b.code === a.code ? 'active' : ''}" style="--ac:${esc(b.accent || 'var(--gold)')}" data-act="chat" data-chat="${b.code}">
              <span class="atab-face"><img src="/static/img/agents/${esc(b.code)}.jpg" alt="" loading="lazy"></span>${esc(b.name.split(' ')[0])}
            </span>`).join('')}
          <span class="atab atab-x" data-act="tool-toggle" title="Все инструменты">🧰</span>
        </div>
        ${features.length ? `
        <div class="toolbar" id="chat-toolbar">
          ${features.map(f => `
            <span class="tchip" data-act="tool-fn" data-fn="${f.h}">
              <span class="tchip-ico">${f.e}</span>${esc(f.t)}
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
            <input class="ipt" id="chat-input" placeholder="Спроси ${esc(a.name)}…" autocomplete="off" value="${esc(this.chat.draft || '')}"/>
            <button class="send-btn" id="send-btn" data-act="send">➤</button>
          </div>
          ${suggest.length ? `
          <div class="suggest-chips">
            ${suggest.map(s => `<span class="chip tpl" data-act="fill" data-val="${esc(s)}">${esc(s)}</span>`).join('')}
          </div>` : ''}
        </div>
        <div class="tool-expand" id="tool-expand">
          <div class="te-mask" data-act="tool-toggle"></div>
          <div class="te-sheet">
            <div class="te-handle"></div>
            <div class="te-title">🧰 Инструменты<button class="te-close" data-act="tool-toggle">✕</button></div>
            ${agents.map(b => `
              <div class="te-group">
                <div class="te-agent" style="--ac:${esc(b.accent || 'var(--gold)')}">${esc(b.name)}</div>
                <div class="te-grid">
                  ${(FEATURES[b.code] || []).map(f => `
                    <button class="te-chip" data-act="chat-fn" data-chat="${b.code}" data-fn="${f.h}">
                      <span class="te-ico">${f.e}</span>${esc(f.t)}
                    </button>`).join('')}
                </div>
              </div>`).join('')}
          </div>
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
          return `<div class="msg assistant">
            <div class="chat-widget">
              <div class="w-title" style="margin:0">🎴 Схема расклада</div>
              <button class="pick-sel-btn" data-act="pick-open">
                <span class="pick-sel-ico">${esc(cur.emoji || '🎴')}</span>
                <span class="pick-sel-txt">
                  <span class="pick-sel-t">${esc(cur.title)}</span>
                  <span class="pick-sel-d">${esc(cur.hint || cur.desc || 'Выбрать схему расклада')}</span>
                </span>
                <span class="pick-sel-go">›</span>
              </button>
              <div class="swipe-hint">Тапни — откроется весь список раскладов</div>
              ${p.err ? `<div class="s-err">${esc(p.err)}</div>` : ''}
              <textarea class="ipt" id="tarot-q" rows="1" placeholder="Твой вопрос к картам…"
                style="margin-top:8px;resize:none">${q(p.q || '')}</textarea>
              <button class="btn btn-primary" style="margin-top:8px" data-act="draw">Потянула карты 🎴</button>
            </div></div>`;
        })();

      case 'tarot-cards':
        return `<div class="msg assistant">
          Карты вытянуты. Твой вопрос: <b>«${esc(p.question)}»</b>
          <div class="chat-widget">
            <div class="tarot-grid sh-${esc(p.spread || 'three')}">
              ${p.positions.map((pos, i) => {
                const c = p.cards[i] || {};
                return `
                <div class="tpos" data-i="${i}">
                  <div class="tcard ${p.revealed[i] ? 'open' : 'dealt'}" style="${p.revealed[i] ? '' : 'animation-delay:' + (i * 80) + 'ms'}" data-act="flip" data-i="${i}" title="Перевернуть">
                    <div class="tcard-inner">
                      <div class="tcard-face tcard-back"><img src="/static/img/card-back.jpg" alt="" loading="lazy"></div>
                      <div class="tcard-face tcard-front${c.reversed ? ' rev' : ''}"><img src="/static/img/tarot/${esc(c.img || 'm00')}.jpg" alt="${esc(c.name)}" loading="lazy">
                        ${c.reversed ? '<span class="t-rev">↺ перевёрнута</span>' : ''}</div>
                    </div>
                  </div>
                  <div class="tpos-pos">${esc(pos)}</div>
                  <div class="tpos-mean">${esc(c.name)}${c.reversed ? ' ↺' : ''}</div>
                  <div class="tpos-desc">${esc(c.meaning)}</div>
                </div>`;
              }).join('')}
            </div>
            ${p.allRevealed ? `<button class="btn btn-primary" style="margin-top:14px" data-act="interpret">Что это значит для меня?</button>`
              : `<div class="t-hint">Тапни карты — они раскроются ↻</div>`}
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
            <div class="rel-chips">
              ${[['love','💞','Вторая половинка'],['friend','💛','Подруга / Друг'],['work','💼','Коллега / Дело'],['family','🏡','Родные']].map(([k, e, t]) =>
                `<span class="rel-chip${p.relation === k ? ' sel' : ''}" data-act="compat-rel" data-rel="${k}">${e} ${t}</span>`).join('')}
            </div>
            <input class="ipt" id="cp-name" placeholder="Имя (необязательно)" style="margin-top:10px;margin-bottom:8px"/>
            <input class="ipt" id="cp-date" placeholder="Дата рождения партнёра · ГГГГ-ММ-ДД" style="margin-bottom:8px"/>
            <button class="btn btn-primary" data-act="compat">Проверить совместимость 💞</button>
          </div></div>`;

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
    this.go('hub');
  };
  // свайп по табам агентов: вбок листаем Оракул → Астролог → Таролог → …

  app.cycleAgent = function(dir) {
    const list = this.agents.length ? this.agents.map(b => b.code) : ['oracle', 'astro', 'tarot'];
    const i = list.indexOf(this.chat.key);
    if (i < 0) return;
    this.openChat(list[(i + dir + list.length) % list.length]);
  };
  // панель «Все инструменты» (bottom sheet): свайп вверх у нижнего края ленты

  app.setToolbox = function(open) {
    const el = document.getElementById('tool-expand');
    if (!el) return;
    el.classList.toggle('open', open);
    if (open) haptic('soft');
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
    if (navigator.vibrate) { try { navigator.vibrate(15); } catch (e) {} }
    const input = document.getElementById('chat-input');
    if (input) input.value = '';
    this.chat.draft = '';
    this.chat.messages.push({ role: 'user', text: val });
    this.chat.busy = true;
    this.renderChat(document.getElementById('app-main'));
    try {
      const r = await this.chatPost(val);
      haptic('success');
      if (navigator.vibrate) { try { navigator.vibrate([10, 40, 14]); } catch (e) {} }
      this.chat.messages.push({ role: 'assistant', text: r.answer });
    } catch (e) {
      this.chat.messages.push({ role: 'assistant', text: '😔 ' + e.message });
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

