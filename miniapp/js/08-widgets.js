/* widgets: лунная неделя, карта дня, матрица, практики, дневник, карьера */
/* оболочка виджета-сообщения: msg.assistant > chat-widget > title + loader|error|body.
   loading → loader-ring, error → строка с esc(p.error), иначе body. title/body — строка или fn(p). */
const widgetShell = (p, { title, body, tail = '' }) => {
  const head = typeof title === 'function' ? title(p) : title;
  const content = p.loading ? '<div class="loader-ring"></div>'
    : p.error ? '<div style="color:var(--text-faint);font-size:12.5px">' + esc(p.error) + '</div>'
    : (typeof body === 'function' ? body() : body);
  return `<div class="msg assistant">
    <div class="chat-widget">
      <div class="w-title">${head}</div>
      ${content}
      ${tail}
    </div>
  </div>`;
};
  app.moonWidget = function(p) {
    const wd = WD_LOWER;
    const days = p.days || [];
    return widgetShell(p, {
      title: '🌙 Лунная неделя',
      body: days.length ? days.map((d, i) => `
          <div class="planet-line pw-mline${p.exp === i ? ' exp' : ''}" data-act="moon-expand" data-i="${i}">
            <div class="p-ico moon-orb mini-moon">${moonSvg(d.emoji)}</div>
            <div class="p-name">${d.date.slice(8)} ${wd[d.weekday]} · <b>${esc(d.name)}</b></div>
            <div class="p-val" style="font-size:11.5px">${d.day}-й д.</div>
            ${p.exp === i ? `<div class="moon-adv">${esc(d.advice)}</div>` : ''}
          </div>`).join('')
        : '<div style="color:var(--text-faint);font-size:12.5px">' + esc(p.error || 'Нет данных') + '</div>',
      tail: '<div style="font-size:11.5px;color:var(--text-faint);margin-top:8px">Тапни день — раскроется совет фазы</div>',
    });
  };


  app.todayWidget = function(p) {
    if (p.loading) return `<div class="msg assistant"><div class="chat-widget"><div class="typing"><span></span><span></span><span></span></div></div></div>`;
    const card = p.card || {};
    const moon = p.moon || {};
    const sphere = p.sphere || '';
    const sphereTxt = { love: '💞 Любовь и отношения', work: '💼 Работа и дела', energy: '⚡ Энергия и состояние' }[sphere] || (sphere ? esc(sphere) : '');
    const name = (this.me && this.me.name ? this.me.name.split(' ')[0] : 'милая');
    return `<div class="msg assistant">
      <div class="chat-widget day-card">
        <div class="dc-head"><span class="dc-date">${fmtDate()}</span><span class="dc-hi">доброе утро, ${esc(name)} ✨</span></div>
        ${card.img ? `
        <div class="dc-row">
          <div class="dc-card${p.flipped ? ' flipped' : ''}" data-act="day-flip" title="Тапни — раскроется смысл">
            <div class="dc-card-inner">
              <div class="dc-face dc-back"><img src="/static/img/card-back.jpg" alt="" loading="lazy"></div>
              <div class="dc-face dc-front"><img src="/static/img/tarot/${esc(card.img)}.jpg" alt="${esc(card.name || '')}" loading="lazy"></div>
            </div>
          </div>
          <div class="dc-card-txt">
            <div class="dc-label">Карта дня${card.reversed ? ' ↺' : ''}</div>
            <div class="dc-name">${esc(card.name || '')}</div>
            ${p.flipped ? `<div class="dc-mean">${esc(card.meaning || '')}</div>` : '<div class="dc-hint">Тапни карту — раскроется смысл ↻</div>'}
          </div>
        </div>` : ''}
        ${moon.name ? `
        <div class="dc-moon">
          <span class="dc-moon-orb">${moonSvg(moon.emoji || '🌑')}</span>
          <div class="dc-moon-txt">
            <b>${esc(moon.name || '')}</b>${moon.day ? ' · ' + moon.day + '-й лунный день' : ''}
            <div class="dc-moon-adv">${esc(moon.advice || '')}</div>
          </div>
        </div>` : ''}
        ${sphereTxt ? `<span class="dc-sphere">${sphereTxt}</span>` : ''}
        ${p.forecast ? `<div class="dc-forecast">${esc(p.forecast)}</div>` : ''}
        <button class="btn btn-primary" data-act="today-ask">Спросить подробнее ✨</button>
      </div></div>`;
  };


  app.matrixWidget = function(p) {
    const d = p.data || {};
    const sel = p.selected;
    const colors = { love: '#ff8fa3', money: '#e6c178', rod: '#7fd4a8', destiny: '#a78bfa' };
    const nodeGroup = { personal: 'love', spirit: 'love', love: 'love', family: 'rod', money: 'money', destiny: 'destiny', center: 'destiny' };
    const nodes = [
      ['personal', 120, 30], ['spirit', 206, 120], ['family', 34, 120],
      ['destiny', 120, 210], ['center', 120, 120], ['love', 156, 62], ['money', 84, 178],
    ];
    const groups = {
      love: [['personal', 120, 30, 'destiny', 120, 210], ['center', 120, 120, 'love', 156, 62]],
      money: [['family', 34, 120, 'destiny', 120, 210], ['center', 120, 120, 'money', 84, 178]],
      rod: [['center', 120, 120, 'family', 34, 120], ['personal', 120, 30, 'family', 34, 120]],
      destiny: [['center', 120, 120, 'destiny', 120, 210], ['personal', 120, 30, 'destiny', 120, 210], ['family', 34, 120, 'destiny', 120, 210]],
    };
    const active = sel ? (nodeGroup[sel] || null) : null;
    const seen = {};
    const segs = [];
    Object.values(groups).forEach(ls => ls.forEach(([a, x1, y1, b, x2, y2]) => {
      const k = [x1, y1, x2, y2].sort((p, q) => p - q).join(',');
      if (seen[k]) return; seen[k] = 1;
      segs.push([x1, y1, x2, y2, nodeGroup[a] || nodeGroup[b]]);
    }));
    const segHtml = segs.map(([x1, y1, x2, y2, g]) =>
      `<line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" class="m-seg${active === g ? ' on' : ''}" stroke="${colors[g]}" stroke-width="${active === g ? 3 : 1.4}" opacity="${active === g ? 0.95 : 0.28}"/>`).join('');
    const nodeHtml = nodes.map(([k, x, y]) => {
      const a = d[k] || {};
      const g = nodeGroup[k];
      return `<g class="m-node${active === g ? ' on' : ''}" data-act="matrix-node" data-key="${k}" transform="translate(${x},${y})">
        <circle r="${k === 'center' ? 20 : 16}" class="m-ring"${active === g ? ' style="--mc:' + colors[g] + '"' : ''}></circle>
        <text class="m-num" dy="5" text-anchor="middle">${a.n != null ? a.n : '·'}</text>
      </g>`;
    }).join('');
    const summary = [['love', '💞', 'Любовь'], ['money', '💛', 'Деньги'], ['rod', '🌿', 'Род'], ['destiny', '🌟', 'Предназначение']]
      .map(([g, e, t]) => {
        const key = { love: 'love', money: 'money', rod: 'family', destiny: 'destiny' }[g];
        const a = d[key] || {};
        return `<span class="m-ln${active === g ? ' on' : ''}" style="--lc:${colors[g]}" data-act="matrix-node" data-key="${key}">${e} ${t} · ${a.n != null ? a.n + ' — ' : ''}${esc(a.arcana || '—')}</span>`;
      }).join('');
    let cardHtml = '<div class="m-hint">Тапни узел — раскроется аркан и его линия ✨</div>';
    if (sel && d[sel]) {
      const a = d[sel];
      const g = nodeGroup[sel];
      const label = { love: 'Любовная линия', money: 'Денежная линия', rod: 'Родовая линия', destiny: 'Линия предназначения', spirit: 'Духовный план', personal: 'Личность', center: 'Центр матрицы' }[sel] || sel;
      cardHtml = `
        <div class="m-card" style="--mc:${colors[g]}">
          <div class="m-card-head"><b>${a.n != null ? a.n : ''}</b> ${esc(a.arcana || '')}<span class="m-card-t">${esc(a.title || label)}</span></div>
          ${a.keywords ? `<div class="m-keys">${esc(a.keywords)}</div>` : ''}
          ${a.plus ? `<div class="m-block plus"><b>В плюсе</b><div>${esc(a.plus)}</div></div>` : ''}
          ${a.minus ? `<div class="m-block minus"><b>В минусе</b><div>${esc(a.minus)}</div></div>` : ''}
          ${a.advice ? `<div class="m-block advice"><b>Задача</b><div>${esc(a.advice)}</div></div>` : ''}
          <button class="btn btn-primary" style="width:100%;margin-top:10px" data-act="matrix-ask" data-key="${sel}">Хочу разбор подробнее ✨</button>
        </div>`;
    }
    return widgetShell(p, {
      title: '🔢 Матрица Судьбы',
      body: `<div class="m-diamond">
          <svg viewBox="0 0 240 240" class="m-svg" aria-hidden="true">${segHtml}${nodeHtml}</svg>
        </div>
        <div class="m-lines">${summary}</div>
        ${cardHtml}`,
    });
  };


  app.practicesWidget = function(p) {
    const items = p.items || [];
    return widgetShell(p, {
      title: t => '🧘 Практики' + (t.loading ? '' : ' · ' + items.length + ' программ'),
      body: items.map(it => {
      const st = it.status;
      const active = st === 'active';
      const done = st === 'completed';
      return `
        <div class="pr-card">
          <div class="pr-top">
            <span class="pr-ico">${esc(it.emoji || '✨')}</span>
            <div style="flex:1;min-width:0">
              <div class="pr-t">${esc(it.title || it.code)}</div>
              <div class="pr-fit">${esc(it.fit || it.goal || '')}</div>
            </div>
            <div class="pr-ring">${ringSvg(it.percent)}<span class="pr-pct">${it.percent || 0}%</span></div>
          </div>
          <div class="pr-meta">
            <span class="pr-days">${it.day_index || 0}/${it.days || 0} дней</span>
            ${it.streak_alive ? `<span class="pr-fire">🔥 ${it.streak || 0}</span>` : (it.streak > 0 ? '<span class="pr-fire off">🔥 погас</span>' : '')}
            ${active && it.today_step ? `<span class="pr-step">Сегодня: ${esc(it.today_step)}</span>` : ''}
          </div>
          <div class="pr-actions">
            ${(!active && !done) ? `<button class="btn btn-primary" data-act="p-action" data-code="${it.code}" data-a="start">Начать</button>` : ''}
            ${active ? `<button class="btn btn-primary" data-act="p-action" data-code="${it.code}" data-a="done">Отметить день ✓</button>
              <button class="btn btn-ghost" data-act="p-action" data-code="${it.code}" data-a="stop">Стоп</button>` : ''}
            ${done ? `<span class="pr-done">✓ Завершена — горжусь тобой</span>` : ''}
          </div>
        </div>`;
    }).join('') || '<div style="color:var(--text-faint);font-size:12.5px">Практики не загрузились — попробуй ещё раз.</div>',
    });
  };


  app.diaryWidget = function(p) {
    const entries = p.entries || [];
    const streak = p.streak || 0;
    return widgetShell(p, {
      title: '📖 Книга судьбы',
      body: `
      <div class="dy-head">
        <span class="dy-streak${streak ? ' on' : ''}">${streak ? '🔥 ' + streak + ' дней подряд' : '🔥 начни серию'}</span>
        <span class="dy-count">${entries.length} записей</span>
      </div>
      ${p.prompt ? `
        <div class="dy-prompt">
          <div class="dy-pq">Вечерний вопрос Оракула</div>
          <div class="dy-pt">${esc(p.prompt)}</div>
          ${p.wroteToday ? '' : `
          <div class="dy-add">
            <input class="ipt" id="diary-in" placeholder="Запиши строчку…" autocomplete="off"/>
            <button class="send-btn" data-act="diary-add">+</button>
          </div>`}
        </div>` : ''}
      ${entries.length ? `<div class="dy-list">
        ${entries.slice(0, 8).map(e => `
          <div class="dy-row"><span class="dy-date">${esc((e.created_at || '').slice(0, 10))}</span><span class="dy-txt">${esc((e.text || '').slice(0, 90))}</span></div>`).join('')}
      </div>` : '<div style="color:var(--text-faint);font-size:12.5px">Пока пусто — начни с вечернего вопроса ✨</div>'}
      ${p.summary ? this.diarySummaryHtml(p.summary) : ''}
      <button class="btn btn-ghost" style="width:100%;margin-top:10px" data-act="diary-summary">${p.summary ? 'Обновить сводку' : 'Что показала Вселенная? 🌌'}</button>`,
    });
  };


  app.diarySummaryHtml = function(s) {
    const moods = s.moods ? Object.entries(s.moods).map(([k, v]) => `<span class="dy-mood">${esc(k)} ${v}</span>`).join('') : '';
    return `<div class="dy-sum">
      <div class="dy-sum-title">🌌 Что показала Вселенная · ${esc(s.month || '')}</div>
      <div class="dy-nums"><span>${s.count || 0} записей</span><span>${s.days_written || 0} дней</span><span>🔥 макс. ${s.streak_max || 0}</span></div>
      ${s.repeated_themes && s.repeated_themes.length ? `<div class="dy-th"><b>Повторялось:</b> ${s.repeated_themes.map(t => esc(t)).join(', ')}</div>` : ''}
      ${s.trend ? `<div class="dy-tr"><b>Динамика:</b> ${esc(s.trend.direction === 'up' ? 'вверх ↑' : s.trend.direction === 'down' ? 'вниз ↓' : 'стабильно →')}</div>` : ''}
      ${s.changes ? `<div class="dy-ch"><b>Перемен:</b> ${s.changes} записей «наконец/решила/перестала»</div>` : ''}
      ${moods ? `<div class="dy-moods">${moods}</div>` : ''}
    </div>`;
  };


  app.careerWidget = function(p) {
    const days = p.days || [];
    const sel = p.sel != null ? days[p.sel] : null;
    const legend = [['#7fd4a8', 'Действие · старт'], ['#e6c178', 'Решение'], ['#ff8fa3', 'Осторожно'], ['#8b86a3', 'Пауза']];
    return widgetShell(p, {
      title: t => '💼 Карьерные окна' + (t.loading ? '' : ' · ' + fmtDate()),
      body: `
      <div class="cw-legend">${legend.map(([c, t]) => `<span class="cw-lg" style="--lc:${c}">${t}</span>`).join('')}</div>
      <div class="cw-grid">
        ${days.map((d, i) => {
          const w = careerWindow(d);
          return `<div class="cw-cell${p.sel === i ? ' sel' : ''}" style="--lc:${w.c}" data-act="career-day" data-i="${i}">
            <span class="cw-dn">${d.day_num}</span><span class="cw-e">${d.emoji}</span><span class="cw-t">${esc(w.t)}</span>
          </div>`;
        }).join('')}
      </div>
      ${sel ? `
      <div class="cw-detail">
        <div class="cw-dt">${sel.date.slice(8, 10)}.${sel.date.slice(5, 7)} · <b>${esc(sel.name)}</b> — ${careerWindow(sel).t}</div>
        <div class="cw-da">${esc(sel.advice)}</div>
      </div>` : '<div class="cw-hint">Тапни день — покажу, что делать в это окно</div>'}
      <button class="btn btn-primary" style="width:100%;margin-top:10px" data-act="career-ask">Спросить Астролога про окна 💼</button>`,
    });
  };

  /* ── интерактив виджетов ── */

  app.todayFlip = function() {
    const p = this.chat.pending;
    if (!p || p.kind !== 'today') return;
    haptic('light');
    p.flipped = !p.flipped;
    this.renderChat(document.getElementById('app-main'));
  };

  app.todayAsk = function() {
    haptic('light');
    const p = this.chat.pending;
    const name = p && p.card && p.card.name ? p.card.name : 'дня';
    this.doSend('Расскажи подробнее про сегодняшнюю карту «' + name + '» — как она связана с моим днём и что мне сейчас важно.');
  };

  app.selectMatrixNode = function(key) {
    const p = this.chat.pending;
    if (!p || p.kind !== 'matrix' || !p.data || !p.data[key]) return;
    haptic('light');
    vb(30);
    p.selected = key;
    this.renderChat(document.getElementById('app-main'));
  };

  app.matrixAsk = function(key) {
    const p = this.chat.pending;
    if (!p || p.kind !== 'matrix' || !p.data || !p.data[key]) return;
    const a = p.data[key];
    const labels = { personal: 'личность', spirit: 'дух', family: 'род', destiny: 'предназначение', center: 'центр', love: 'любовь', money: 'деньги' };
    haptic('light');
    this.doSend('Разбери подробнее мой аркан «' + (a.arcana || '') + '» — линия «' + (labels[key] || key) + '». Что он значит для меня сейчас: в плюсе, в минусе, и что делать.');
  };

  app.expandMoonDay = function(i) {
    const p = this.chat.pending;
    if (!p || p.kind !== 'moon' || !p.days) return;
    haptic('light');
    p.exp = p.exp === i ? null : i;
    this.renderChat(document.getElementById('app-main'));
  };

  app.practiceAction = async function(code, a) {
    haptic('light');
    const p = this.chat.pending;
    if (!p || p.kind !== 'practices') return;
    try {
      await api('/api/practices/' + code + '/' + a, { method: 'POST' });
      const r = await api('/api/practices');
      p.items = (r && r.items) || p.items || [];
      if (a === 'done') {
        haptic('success');
        vb([10, 40, 20]);
      }
    } catch (e) {
      this.toast(e.message || 'Не получилось — попробуй ещё раз');
    }
    this.renderChat(document.getElementById('app-main'));
  };

  app.diaryAdd = async function() {
    const val = ((document.getElementById('diary-in') || {}).value || '').trim();
    if (!val) { this.toast('Напиши строчку — даже одна мысль считается ✨'); return; }
    haptic('light');
    const p = this.chat.pending;
    try {
      await api('/api/diary', { method: 'POST', body: JSON.stringify({ text: val }) });
      haptic('success');
      vb([10, 40, 20]);
      const r = await api('/api/diary');
      if (p) { p.entries = (r && r.entries) || []; p.streak = (r && r.streak) || 0; p.wroteToday = true; p.prompt = ''; }
    } catch (e) {
      this.toast(e.message || 'Не сохранилось — попробуй ещё раз');
    }
    if (p) this.renderChat(document.getElementById('app-main'));
  };

  app.diarySummary = async function() {
    const p = this.chat.pending;
    if (!p || p.kind !== 'diary') return;
    haptic('light');
    try {
      const r = await api('/api/diary/summary');
      if (p) p.summary = r;
    } catch (e) {
      this.toast(e.message || 'Сводка пока не собралась');
    }
    if (p) this.renderChat(document.getElementById('app-main'));
  };

  app.careerDay = function(i) {
    const p = this.chat.pending;
    if (!p || p.kind !== 'career' || !p.days || !p.days[i]) return;
    haptic('light');
    vb(20);
    p.sel = i;
    this.renderChat(document.getElementById('app-main'));
  };

  app.careerAsk = function() {
    haptic('light');
    this.doSend('Разбери мои карьерные окна по натальной карте: когда лучше начинать важные дела, менять направление или обсуждать деньги.');
  };


  app.featureToday = async function() {
    if (this.chat.pending && this.chat.pending.kind === 'today') return;
    const key = this.chat.key, view = this.view;
    const pend = this.chat.pending = { kind: 'today', loading: true, forecast: '', card: null, moon: null, sphere: '', flipped: false };
    this.renderChat(document.getElementById('app-main'));
    try {
      const t = await api('/api/today');
      if (!widAlive(key, view, pend)) return;
      this.chat.pending = { kind: 'today', loading: false,
        forecast: t.forecast || '', card: t.card || null, moon: t.moon || null,
        sphere: t.sphere || '', flipped: false };
    } catch (e) {
      if (!widAlive(key, view, pend)) return;
      this.chat.pending = { kind: 'today', loading: false, forecast: '😔 ' + e.message, card: null, moon: null, sphere: '', flipped: false };
    }
    this.renderChat(document.getElementById('app-main'));
  };

  /* ═══ ФИЧА: ЛУННАЯ НЕДЕЛЯ ═══ */

  app.featureMoon = async function() {
    if (this.chat.pending && this.chat.pending.kind === 'moon') return; // B4 re-entry
    const key = this.chat.key, view = this.view;
    const pend = this.chat.pending = { kind: 'moon', loading: true, days: [], exp: null, error: '' };
    this.renderChat(document.getElementById('app-main'));
    try {
      const days = await api('/api/moon/week');
      if (!widAlive(key, view, pend)) return;
      this.chat.pending = { kind: 'moon', loading: false, days, exp: null, error: '' };
    } catch (e) {
      if (!widAlive(key, view, pend)) return;
      this.chat.pending = { kind: 'moon', loading: false, days: [], exp: null, error: e.message };
    }
    this.renderChat(document.getElementById('app-main'));
  };

  /* ═══ ФИЧА: МАТРИЦА ═══ */

  app.featureMatrix = async function() {
    if (this.chat.pending && this.chat.pending.kind === 'matrix') return; // B4 re-entry
    const key = this.chat.key, view = this.view;
    const pend = this.chat.pending = { kind: 'matrix', loading: true, data: null, selected: null, error: '' };
    this.renderChat(document.getElementById('app-main'));
    try {
      const m = await api('/api/matrix');
      if (!widAlive(key, view, pend)) return;
      this.chat.pending = { kind: 'matrix', loading: false, data: m, selected: null, error: '' };
    } catch (e) {
      if (!widAlive(key, view, pend)) return;
      this.chat.pending = { kind: 'matrix', loading: false, data: null, selected: null, error: e.message };
    }
    this.renderChat(document.getElementById('app-main'));
  };

  /* ═══ ФИЧА: СОВМЕСТИМОСТЬ (Спидометр любви v2) ═══ */

  app.chatPractice = async function() {
    if (this.chat.pending && this.chat.pending.kind === 'practices') return; // B4 re-entry
    const key = this.chat.key, view = this.view;
    const pend = this.chat.pending = { kind: 'practices', loading: true, items: [], error: '' };
    this.renderChat(document.getElementById('app-main'));
    try {
      const r = await api('/api/practices');
      if (!widAlive(key, view, pend)) return;
      this.chat.pending = { kind: 'practices', loading: false, items: (r && r.items) || [], error: '' };
    } catch (e) {
      if (!widAlive(key, view, pend)) return;
      this.chat.pending = { kind: 'practices', loading: false, items: [], error: e.message };
    }
    this.renderChat(document.getElementById('app-main'));
  };
  // «Книга судьбы» — дневник со стриком, вечерним вопросом и месячной сводкой

  app.chatMonthly = async function() {
    if (this.chat.pending && this.chat.pending.kind === 'diary') return; // B4 re-entry
    const key = this.chat.key, view = this.view;
    const pend = this.chat.pending = { kind: 'diary', loading: true, entries: [], streak: 0, prompt: '', wroteToday: false, summary: null, error: '' };
    this.renderChat(document.getElementById('app-main'));
    try {
      const [r, pr] = await Promise.all([
        api('/api/diary'),
        api('/api/diary/prompt').catch(() => null),
      ]);
      if (!widAlive(key, view, pend)) return;
      const wroteToday = !!(pr && pr.written_today);
      this.chat.pending = { kind: 'diary', loading: false,
        entries: (r && r.entries) || [], streak: (r && r.streak) || 0,
        prompt: wroteToday ? (pr.prompt || '') : ((pr && pr.prompt) || ''),
        wroteToday, summary: null, error: '' };
    } catch (e) {
      if (!widAlive(key, view, pend)) return;
      this.chat.pending = { kind: 'diary', loading: false, entries: [], streak: 0, prompt: '', wroteToday: false, summary: null, error: e.message };
    }
    this.renderChat(document.getElementById('app-main'));
  };
  // Карьерные окна: календарный гайд по лунным фазам (тип окна = фаза, код считает)

  app.featureCareer = async function() {
    if (this.chat.pending && this.chat.pending.kind === 'career') return; // B4 re-entry
    const key = this.chat.key, view = this.view;
    const pend = this.chat.pending = { kind: 'career', loading: true, days: [], sel: null, error: '' };
    this.renderChat(document.getElementById('app-main'));
    try {
      const days = await api('/api/moon/week?days=30');
      if (!widAlive(key, view, pend)) return;
      this.chat.pending = { kind: 'career', loading: false, days: (days || []).slice(0, 16), sel: null, error: '' };
    } catch (e) {
      if (!widAlive(key, view, pend)) return;
      this.chat.pending = { kind: 'career', loading: false, days: [], sel: null, error: e.message };
    }
    this.renderChat(document.getElementById('app-main'));
  };

  /* ═══ ИНТЕРАКТИВ НАТАЛЬНОЙ КАРТЫ: тап по планете + фильтр по стихиям ═══ */

