/* compat: совместимость пары — форма, сферы, спидометр, разбор */
  app.featureCompat = function() {
    if (this.chat.pending && this.chat.pending.kind === 'compat') return;
    this.chat.pending = { kind: 'compat', relation: 'love' };
    this.renderChat(document.getElementById('app-main'));
  };
  // выбор типа связи чипами (love/friend/work/family) — не отправляет, только красит виджет

  app.setCompatRel = function(rel) {
    haptic('light');
    if (this.chat.pending) this.chat.pending.relation = rel;
    this.renderChat(document.getElementById('app-main'));
  };

  app.doCompat = async function() {
    const name = ((document.getElementById('cp-name') || {}).value || '').trim();
    const date = ((document.getElementById('cp-date') || {}).value || '').trim();
    const rel = (this.chat.pending && this.chat.pending.relation) || 'love';
    if (!date) { this.toast('Введи дату рождения партнёра · ГГГГ-ММ-ДД'); return; }
    this.chat.busy = true;
    this.chat.pending = null;
    this.renderChat(document.getElementById('app-main'));
    try {
      const r = await api('/api/compat/full', { method: 'POST', body: JSON.stringify({ partner_date: date, partner_name: name, relation: rel, save: true }) });
      this.chat.messages.push({ role: 'user', text: 'Моя совместимость с ' + (name || 'партнёром') + ' (' + date + ')' });
      // новый бэкенд вернёт scores — рисуем спидометр; старый — просто текст
      if (r && r.scores) {
        this.chat.messages.push({ role: 'assistant', widget: this.compatWidgetHtml(r.scores, r.answer, { partner_name: name, partner_date: date, relation: rel }) });
      } else {
        this.chat.messages.push({ role: 'assistant', text: r.answer });
      }
    } catch (e) {
      this.chat.messages.push({ role: 'assistant', text: '😔 ' + e.message });
    }
    this.chat.busy = false;
    this.renderChat(document.getElementById('app-main'));
  };

  // «Спидометр любви»: кольцо из 5 сегментов-сфер, общий балл в центре, стрелка на total.

  app.compatWidgetHtml = function(scores, answer, ctx) {
    const gid = 'spdGlow' + (++spdSeq); // уникальный id фильтра: несколько спидометров в ленте не конфликтуют
    const total = Math.round(scores && scores.total != null ? scores.total : 0);
    const verdict = (scores && scores.verdict) || '';
    const spheres = (scores && Array.isArray(scores.spheres)) ? scores.spheres : [];
    ctx = ctx || {};
    const colors = ['#e6c178', '#a78bfa', '#ff9e9e', '#7fd4a8', '#8ab6ff'];
    const n = Math.max(1, spheres.length);
    const cx = 110, cy = 110, R = 84, sw = 15;
    const seg = 360 / n;
    // deg отсчитывается от 3 часов против часовой (как в nativitySvg)
    const pol = (deg, rad) => [cx + Math.cos(deg * Math.PI / 180) * rad, cy - Math.sin(deg * Math.PI / 180) * rad];
    const arc = (a1, a2) => {
      const [x1, y1] = pol(a1, R);
      const [x2, y2] = pol(a2, R);
      return `M ${x1} ${y1} A ${R} ${R} 0 0 1 ${x2} ${y2}`;
    };
    const segs = spheres.map((s, i) => {
      const a1 = i * seg;
      const [mx, my] = pol(a1 + seg / 2, R + 11); // % чуть снаружи кольца
      return `<path class="spd-seg" data-sphere="${i}" d="${arc(a1, a1 + seg)}" stroke="${colors[i % colors.length]}" stroke-width="${sw}" fill="none"/>
        <text x="${mx}" y="${my}" text-anchor="middle" class="spd-pct">${Math.round(s.value || 0)}</text>`;
    }).join('');
    // шкала 0-100: деления каждые 25, крупные на 0/50/100
    const ticks = [0, 25, 50, 75, 100].map(t => {
      const [x1, y1] = pol(t / 100 * 360, 61);
      const [x2, y2] = pol(t / 100 * 360, t % 50 === 0 ? 70 : 65);
      return `<line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" class="spd-tick${t % 50 === 0 ? ' big' : ''}"/>`;
    }).join('');
    // стрелка на общий балл
    const [nx, ny] = pol(Math.max(0, Math.min(100, total)) / 100 * 360, R - 24);
    const verdictTxt = verdict ? `<div class="spd-verdict">${esc(verdict)}</div>` : '';
    const more = answer ? `
      <button class="spd-more" data-act="spd-toggle">Разбор ✨</button>
      <div class="spd-answer" hidden>${richMd(answer || '')}</div>` : '';
    // «в сторис»: серверный PNG открытки (/api/share/compat.png) — тот же путь,
    // что у расклада; данные пары живут в data-атрибутах кнопки
    const share = ctx.partner_date ? `
      <button class="btn btn-ghost" data-act="share-compat" data-pdate="${esc(ctx.partner_date)}" data-pname="${esc(ctx.partner_name || '')}" data-rel="${esc(ctx.relation || 'love')}" title="Открытка для сторис" style="margin-top:8px">📸 Поделиться</button>` : '';
    return `<div class="chat-widget">
      <div class="w-title" style="margin:0">💞 Спидометр любви</div>
      <div class="spd-wrap">
        <svg viewBox="0 0 220 220" class="spd-ring" aria-hidden="true">
          <defs>
            <filter id="${gid}" x="-40%" y="-40%" width="180%" height="180%">
              <feGaussianBlur stdDeviation="2.4" result="blur"/>
              <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
            </filter>
          </defs>
          <circle cx="${cx}" cy="${cy}" r="${R}" fill="none" stroke="rgba(255,255,255,.05)" stroke-width="${sw}"/>
          ${ticks}
          ${segs}
          <line x1="${cx}" y1="${cy}" x2="${nx}" y2="${ny}" class="spd-needle" filter="url(#${gid})"/>
          <circle cx="${cx}" cy="${cy}" r="5" class="spd-hub"/>
          <circle cx="${cx}" cy="${cy}" r="34" class="spd-center"/>
          <text x="${cx}" y="${cy + 6}" text-anchor="middle" class="spd-total">${total}</text>
        </svg>
        ${verdictTxt}
      </div>
      <div class="spd-cards">
        ${spheres.map((s, i) => `
          <div class="spd-card" data-act="sphere" data-sphere="${i}" style="--sc:${colors[i % colors.length]}">
            <span class="spd-dot"></span>
            <span class="spd-card-t">${esc(s.title || '')}</span>
            <span class="spd-card-v">${Math.round(s.value || 0)}</span>
          </div>`).join('')}
        ${spheres.map((s, i) => s.note ? `<div class="spd-note">${esc(s.note)}</div>` : '').join('')}
      </div>
      ${more}
      ${share}
    </div>`;
  };
  // тап по карточке сферы → подсветка её сегмента в кольце

  app.selectSphere = function(i) {
    haptic('light');
    vb(30);
    const cards = document.querySelector('.spd-cards');
    if (cards) cards.querySelectorAll('.spd-card').forEach(c =>
      c.classList.toggle('spd-active', parseInt(c.dataset.sphere, 10) === i));
    const ring = document.querySelector('.spd-ring');
    if (ring) ring.querySelectorAll('.spd-seg').forEach(s =>
      s.classList.toggle('spd-active', parseInt(s.dataset.sphere, 10) === i));
  };

  app.toggleSpdAnswer = function() {
    const a = document.querySelector('.spd-answer');
    if (a) a.hidden = !a.hidden;
  };

  // «в сторис» для совместимости: серверный PNG открытки → системный share или
  // скачивание. Данные пары приходят из data-атрибутов кнопки (13-events).
  app.shareCompat = async function(partnerDate, partnerName, relation) {
    if (!partnerDate) { this.toast('Введи дату рождения партнёра ✨'); return; }
    haptic('light');
    const qs = new URLSearchParams({
      partner_date: partnerDate,
      partner_name: partnerName || '',
      relation: relation || 'love',
    }).toString();
    try {
      const res = await fetch('/api/share/compat.png?' + qs);
      if (!res.ok) { this.toast('Картинка сейчас недоступна 🌙'); return; }
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const file = new File([blob], 'oracle-compat.png', { type: 'image/png' });
      if (navigator.share && navigator.canShare && navigator.canShare({ files: [file] })) {
        navigator.share({ title: 'Наша совместимость', files: [file] })
          .catch(() => this.downloadUrl(url, 'oracle-compat.png'));
      } else {
        this.downloadUrl(url, 'oracle-compat.png');
      }
      setTimeout(() => URL.revokeObjectURL(url), 60000);
    } catch (e) { this.toast('Картинка сейчас недоступна 🌙'); }
  };

  /* ═══ ВИДЖЕТЫ: ПРАКТИКИ / КНИГА СУДЬБЫ / КАРЬЕРНЫЕ ОКНА ═══ */
  // Практики — каталог с прогрессом: круг 0–100%, стрик-огонь, отметка дня

