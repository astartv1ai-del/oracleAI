/* misc: профиль, памяти, чтения, отчёты, полная карта, колокол, модалы */
  app.shareReading = async function(id) {
    try {
      const res = await fetch('/api/share/reading/' + id + '.png');
      if (!res.ok) { this.toast('Картинка сейчас недоступна 🌙'); return; }
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const file = new File([blob], 'oracle-tarot.png', { type: 'image/png' });
      if (navigator.share && navigator.canShare && navigator.canShare({ files: [file] })) {
        navigator.share({ title: 'Мой расклад Таро', files: [file] })
          .catch(() => this.downloadUrl(url, 'oracle-tarot.png'));
      } else {
        this.downloadUrl(url, 'oracle-tarot.png');
      }
      setTimeout(() => URL.revokeObjectURL(url), 60000);
    } catch (e) { this.toast('Картинка сейчас недоступна 🌙'); }
  };

  app.refCopy = async function() {
    const link = this._refLink;
    if (!link) { this.toast('Ссылка ещё готовится…'); return; }
    haptic('light');
    try {
      if (navigator.clipboard && navigator.clipboard.writeText) {
        await navigator.clipboard.writeText(link);
        this.toast('Ссылка скопирована — отправь подруге ✨');
      } else {
        this.toast(link);
      }
    } catch (e) { this.toast('Ссылка: ' + link); }
  };
  // G004 «сбылось» на раскладе: обратная связь ценности

  app.setOutcome = async function(id, val) {
    haptic('soft');
    try {
      await api('/api/tarot/outcome/' + id, { method: 'POST', body: JSON.stringify({ outcome: val }) });
      this.toast(val === 'came_true' ? 'Рада, что сбылось! Возвращайся за следующим раскладом ✨'
        : val === 'partly' ? 'Отметим частично — главное, что откликнулось 🌙' : 'Поняла — жизнь вносит коррективы 🌙');
    } catch (e) { this.toast(e.message); }
  };

  app.renderProfile = async function(main) {
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
          <div class="glass" style="display:flex;align-items:center;gap:12px;padding:12px 16px;margin-bottom:10px">
            <span style="font-size:24px;flex-shrink:0">${(me && me.global_streak) ? '🔥' : '🌅'}</span>
            <div style="flex:1;min-width:0">
              <div style="font-weight:600;font-size:14px">${(me && me.global_streak) ? 'День ' + me.global_streak + ' с Оракулом' : 'Начни свой путь с Оракулом'}</div>
              <div style="font-size:12px;color:var(--text-dim);margin-top:2px">${(me && me.global_streak) ? 'Не разрывай цепочку — завтра новый прогноз и карта дня' : 'Вернись завтра — заглянем в твоё небо вместе'}</div>
            </div>
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
          <div id="profile-referral"></div>
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
  };


  app.loadProfileSections = async function() {
    const refEl = document.getElementById('profile-referral');
    if (refEl) {
      try {
        const ref = await api('/api/referral');
        if (ref && ref.link) {
          refEl.innerHTML = `
            <div class="ref-card">
              <div class="ref-ico">🌙</div>
              <div class="ref-body">
                <div class="ref-title">Пригласи подругу — получи ${ref.bonus_per_invite || ''} ✦</div>
                <div class="ref-desc">${esc(ref.share_text || 'Поделись ссылкой — и обе получите бонус')}</div>
              </div>
              <button class="btn btn-primary ref-btn" data-act="ref-copy">Скопировать</button>
            </div>`;
          this._refLink = ref.link;
        } else {
          refEl.innerHTML = '';
        }
      } catch (e) { refEl.innerHTML = ''; }
    }
    const chartEl = document.getElementById('profile-chart');
    const tarotEl = document.getElementById('profile-tarot');
    const repEl = document.getElementById('profile-reports');
    const memEl = document.getElementById('profile-memories');

    // G001: три независимых запроса идут параллельно (.catch — чтобы не было
    // unhandledrejection до их await в блоках ниже)
    const pChart = api('/api/chart'); pChart.catch(() => {});
    const pTarot = api('/api/tarot/history'); pTarot.catch(() => {});
    const pReps = api('/api/reports'); pReps.catch(() => {});

    // натальная карта (по возможности — из /api/me, иначе /api/chart)
    try {
      const c = await pChart;
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
      const rows = await pTarot;
      // компактно: до 3 строк + «Все N →» (тап открывает модал со всем списком)
      if (tarotEl) {
        if (!rows.length) {
          tarotEl.innerHTML = `<div class="glass" style="padding:16px;text-align:center">
            <div style="font-size:24px">🎴</div>
            <div style="color:var(--text-faint);font-size:13px;margin:6px 0 10px">Раскладов пока нет — зайди к Тарологу и задай вопрос картам.</div>
            <button class="btn btn-primary" data-act="chat-fn" data-chat="tarot" data-fn="featureTarot">Задать вопрос картам ✨</button>
          </div>`;
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
      const rep = await pReps;
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
  };


  app.openReport = async function(kind) {
    try {
      const r = await api('/api/reports/' + kind);
      this.showModal(`<h3>${esc(r.title)}</h3><button class="m-close" data-act="modal-close">✕</button><div style="font-size:13.5px;line-height:1.65;margin-top:8px">${rich(r.body)}</div>`);
    } catch (e) { alert(e.message); }
  };


  app.openReading = async function(id) {
    try {
      const rows = await api('/api/tarot/history');
      const r = rows.find(x => x.id === id) || rows[0];
      const cardStrip = (r.cards || []).map(c => `
        <div class="rc-strip"><img src="/static/img/tarot/${esc(c.img || 'm00')}.jpg" alt="${esc(c.name)}" loading="lazy">
          <span>${esc(c.name)}${c.reversed ? ' ↺' : ''}</span></div>`).join('');
      const cards = (r.cards || []).map(c => `${c.emoji} ${c.name}${c.reversed ? ' ↺' : ''} — ${c.meaning}`).join('\n');
      this.showModal(`<h3>🎴 ${esc(r.question || 'Расклад')}</h3><button class="m-close" data-act="modal-close">✕</button>
        <div class="rc-strip-row">${cardStrip}</div>
        <div style="font-size:12px;color:var(--text-dim);white-space:pre-wrap;margin:8px 0">${esc(cards)}</div>
        <div style="font-size:13.5px;line-height:1.65;white-space:pre-wrap">${esc(r.answer || '—')}</div>
        <button class="btn btn-primary" style="margin-top:14px" data-act="share-reading" data-id="${id}">📸 Сохранить в сторис</button>
        <div class="outcome-row">
          <span class="outcome-q">Сбылось?</span>
          <button class="outcome-chip" data-act="outcome" data-id="${id}" data-val="came_true">✓ Да</button>
          <button class="outcome-chip" data-act="outcome" data-id="${id}" data-val="partly">Частично</button>
          <button class="outcome-chip" data-act="outcome" data-id="${id}" data-val="no">Нет</button>
        </div>`);
    } catch (e) { alert(e.message); }
  };

  // тап по подсказке на карте агента: открывает чат и сразу отправляет вопрос

  app.askAgent = function(key, q) {
    this.openChat(key, () => this.doSend(q));
  };

  // Память: управление — просмотр с датой, удалить, добавить вручную.

  app.openMemories = async function() {
    this.showModal(`<h3>Что я помню о тебе</h3><button class="m-close" data-act="modal-close">✕</button>
      <div id="mem-body" style="margin-top:6px"><div class="loader-ring"></div></div>`);
    try {
      const rows = await api('/api/memories');
      this._memFull = rows;
      this.renderMemModal();
    } catch (e) {
      document.getElementById('mem-body').innerHTML = '<div style="color:var(--text-faint)">😔 ' + esc(e.message) + '</div>';
    }
  };


  app.renderMemModal = function() {
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
  };


  app.delMem = async function(id) {
    try {
      await api('/api/memories/' + id, { method: 'DELETE' });
      this._memFull = (this._memFull || []).filter(m => m.id !== id);
      this.renderMemModal();
      this.me = null; this.me = await api('/api/me');   // обновить счётчик памяти
    } catch (e) { alert(e.message); }
  };


  app.addMem = async function() {
    const input = document.getElementById('mem-new');
    const fact = (input && input.value || '').trim();
    if (fact.length < 3) { if (input) input.focus(); return; }
    try {
      await api('/api/memories', { method: 'POST', body: JSON.stringify({ fact }) });
      this._memFull = await api('/api/memories');
      this.renderMemModal();
      this.me = await api('/api/me');
    } catch (e) { alert(e.message); }
  };

  // «Все N раскладов»: полный список в модале

  app.openAllReadings = async function() {
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
      <div style="margin-top:8px">${items || `<div style="color:var(--text-faint);font-size:13px;text-align:center;padding:6px 0">Раскладов пока нет</div>
        <button class="btn btn-primary" style="width:100%;margin-top:10px" data-act="chat-fn" data-chat="tarot" data-fn="featureTarot">Вытянуть первую карту 🎴</button>`}</div>`);
  };

  // Полная натальная карта: планеты, узлы (Раху/Кету/Лилит), дома, аспекты, ASC/MC

  app.openFullChart = async function() {
    this.showModal(`<h3>🌌 Полная натальная карта</h3><button class="m-close" data-act="modal-close">✕</button>
      <div id="fc-body" style="margin-top:8px"><div class="loader-ring"></div></div>`);
    try {
      const c = await api('/api/chart');
      this.chart = c; // B2: для шаринга из полной карты
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
        <div class="fc-hero" style="margin-bottom:6px;display:flex;justify-content:center;align-items:center;background:rgba(14,13,30,.7);border-radius:var(--r-m);padding:10px;box-shadow:var(--sh-card);">
          <div style="width:260px;height:260px;">${nativitySvg(c, 260)}</div>
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
            <div class="asp-legend" style="margin-bottom:8px">
              <span class="asp-chip" style="color:var(--gold)">☌ соединение</span><span class="asp-chip" style="color:var(--gold)">⚹ секстиль</span><span class="asp-chip" style="color:var(--gold)">△ трин</span>
              <span class="asp-chip" style="color:var(--violet)">□ квадрат</span><span class="asp-chip" style="color:#ff6b6b">☍ оппозиция</span>
            </div>
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
        <button class="btn btn-primary" style="width:100%;margin-top:8px" data-act="share-chart">📸 Сохранить карту в сторис</button>
        <button class="btn btn-ghost" style="width:100%;margin-top:8px" data-act="fc-explain">🧠 Разбор простыми словами</button>
        <div id="fc-explain" style="margin-top:12px"></div>`;
    } catch (e) {
      document.getElementById('fc-body').innerHTML = '<div style="color:var(--text-faint)">😔 ' + esc(e.message) + '</div>';
    }
  };

  // Разбор карты простыми словами: ИИ-объяснение по разделам (кэш на сервере).

  app.explainChart = async function() {
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
  };

  // панель уведомлений: прогноз дня + утреннее напоминание

  app.openBell = async function() {
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
  };


  app.showModal = function(html, variant = '') {
    const old = document.getElementById('app-modal');
    if (old) old.remove();   // один модал за раз — без дублей id и наложений
    const ov = document.createElement('div');
    ov.className = 'modal-overlay' + (variant === 'full' ? ' full' : '');
    ov.id = 'app-modal';
    ov.innerHTML = `<div class="modal${variant === 'full' ? ' full' : ''}">${html}</div>`;
    ov.addEventListener('click', e => { if (e.target === ov) ov.remove(); });
    document.body.appendChild(ov);
  };

  app.closeModal = function() { const el = document.getElementById('app-modal'); if (el) el.remove(); };

