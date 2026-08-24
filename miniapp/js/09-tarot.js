/* tarot: расклад, выбор схемы, переворот карт, интерпретация */
  app.featureTarot = async function() {
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
  };


  app.openSpreadPicker = function() {
    const p = this.chat.pending;
    if (!p || !p.spreads || !p.spreads.length) { this.toast('Схемы ещё подгружаются…'); return; }
    haptic('light');
    const sel = p.spread || 'three';
    const rows = p.spreads.map(s => `
      <div class="sp-pick-row ${s.code === sel ? 'sel' : ''} ${s.tier === 'premium' ? 'premium' : ''}"
           data-act="pick-choose" data-code="${s.code}" data-owned="${s.owned ? 1 : 0}">
        <div class="sp-pick-ico sp-pick-scheme">${spreadScheme(s.code)}</div>
        <div class="sp-pick-main">
          <div class="sp-pick-title">${esc(s.title)}${s.tier === 'premium' ? `<span class="sp-pick-lock">🔒 ${s.price_crystals ? s.price_crystals + ' ✦' : 'премиум'}</span>` : ''}</div>
          <div class="sp-pick-desc">${esc(s.hint || s.desc || '')}</div>
        </div>
        <div class="sp-pick-meta">
          <span class="sp-pick-cards">${s.cards} карт</span>
          ${s.code === sel ? '<span class="sp-pick-check">✓</span>' : '<span class="sp-pick-radio"></span>'}
        </div>
      </div>`).join('');
    this.showModal(`
      <div class="picker-head">
        <div>
          <div class="picker-title">🎴 Схема расклада</div>
          <div class="picker-sub">Листай, читай описание и выбирай</div>
        </div>
        <button class="m-close" data-act="modal-close">✕</button>
      </div>
      <div class="picker-schemes">${rows}</div>
      <div class="picker-note">Выбор вернёт тебя к вопросу в чате — задай его и тяни карты ✨</div>`, 'full');
  };
  // Выбор схемы из полноэкранного списка (премиум → мягкий модал «как открыть»)

  app.chooseSpread = function(code) {
    const p = this.chat.pending;
    if (!p || !p.spreads) return;
    haptic('soft');
    const s = p.spreads.find(x => x.code === code);
    if (s && s.tier === 'premium' && !s.owned) {
      this.showModal(`<h3>✨ ${esc(s.title)}</h3>
        <button class="m-close" data-act="modal-close">✕</button>
        <div class="fc-adv" style="margin-top:4px">
          Это премиум-расклад. Купи Кристаллы в лавке 💎 или приведи подругу — и получи доступ к нему.
        </div>
        <button class="btn btn-primary" style="margin-top:14px" data-act="modal-close">Понятно ✨</button>`);
      return;
    }
    p.spread = code;
    this.closeModal();
    this.renderChat(document.getElementById('app-main'));
  };


  app.setTarotQuestion = function(value) {
    const p = this.chat.pending;
    if (!p || p.kind !== 'tarot-pick' || p.drawing) return;
    const field = document.getElementById('tarot-q');
    if (field) {
      field.value = value;
      field.focus();
    }
    p.q = value;
    document.querySelectorAll('[data-act="tarot-question"]').forEach(el => {
      el.classList.toggle('is-active', el.dataset.value === value);
    });
    haptic('light');
    vb(12);
  };

  app.doDraw = async function() {
    const p = this.chat.pending;
    if (!p || p.kind !== 'tarot-pick' || p.drawing) return;
    const q = (document.getElementById('tarot-q') || {}).value || p.q;
    const qv = (q || '').trim();
    if (!qv) {
      // Inline-валидация: вопрос остаётся в фокусе сценария и не теряется.
      p.err = 'Сформулируй вопрос картам — чем точнее, тем яснее ответ ✨';
      this.renderChat(document.getElementById('app-main'));
      return;
    }
    const spread = p.spread || 'three';
    const spreads = p.spreads;
    this.chat.busy = true;
    this.chat.pending = { kind: 'tarot-pick', spreads, spread, q: qv, err: '', drawing: true };
    this.renderChat(document.getElementById('app-main'));
    try {
      const r = await api('/api/tarot/draw?spread=' + spread, {
        method: 'POST',
        body: JSON.stringify({ question: qv }),
      });
      this.chat.messages.push({ role: 'user', text: 'Мой вопрос к картам: ' + qv });
      this.chat.pending = {
        kind: 'tarot-cards', question: qv, cards: r.cards, spread,
        positions: r.positions, ledger: r.ledger || null,
        revealed: r.cards.map(() => false), nextReveal: 0,
        turning: false, allRevealed: false, reading_id: r.reading_id,
      };
      haptic('soft');
    } catch (e) {
      this.chat.pending = {
        kind: 'tarot-pick', spreads, spread, q: qv,
        err: 'Колода пока не ответила. Попробуй ещё раз — вопрос уже сохранён.', drawing: false,
      };
    }
    this.chat.busy = false;
    this.renderChat(document.getElementById('app-main'));
  };

  // Переворот карты БЕЗ полного ререндера ленты — иначе скролл прыгает наверх.
  // Работаем точечно: класс .open на конкретной карте + кнопка интерпретации.

  app.flipCard = function(i) {
    const p = this.chat.pending;
    if (!p || p.kind !== 'tarot-cards' || p.revealed[i] || p.turning) return;
    const next = Number.isInteger(p.nextReveal) ? p.nextReveal : p.revealed.filter(Boolean).length;
    if (i !== next) {
      haptic('soft');
      this.toast('Открывай карты по порядку — так нить расклада собирается бережно.');
      return;
    }
    const card = document.querySelector('.tcard[data-i="' + i + '"]');
    if (!card) return;
    const key = this.chat.key, tid = this.chat.tid;
    p.turning = true;
    card.classList.add('is-turning');
    haptic('light');
    vb(25);
    setTimeout(() => {
      if (this.chat.key !== key || this.chat.tid !== tid || this.chat.pending !== p) return;
      card.classList.remove('is-turning');
      card.classList.add('open');
      p.revealed[i] = true;
      p.nextReveal = i + 1;
      p.turning = false;
      p.allRevealed = p.revealed.every(Boolean);
      this.updateTarotProgress();
      if (p.allRevealed) {
        haptic('success');
        this.addInterpretBtn();
      }
    }, 130);
  };

  app.updateTarotProgress = function() {
    const p = this.chat.pending;
    const el = document.querySelector('.tarot-card-progress');
    if (!p || p.kind !== 'tarot-cards' || !el) return;
    const opened = p.revealed.filter(Boolean).length;
    el.innerHTML = `<span>${opened} из ${p.cards.length}</span><i style="--tarot-progress:${(opened / p.cards.length) * 100}%"></i>`;
  };

  app.addInterpretBtn = function() {
    const p = this.chat.pending;
    const w = document.querySelector('.chat-widget');
    const hint = document.querySelector('.t-hint');
    if (hint) hint.remove();
    if (!p || p.kind !== 'tarot-cards' || !w || w.querySelector('[data-act="interpret"]')) return;
    const thread = document.createElement('section');
    thread.className = 'tarot-thread tarot-thread--revealed';
    thread.setAttribute('aria-label', 'Нить расклада');
    const ledger = p.ledger || {};
    const pairs = Array.isArray(ledger.adjacent_combinations) ? ledger.adjacent_combinations : [];
    thread.innerHTML = `<div class="tarot-thread-kicker">НИТЬ РАСКЛАДА</div>
      <p>Карты раскрылись. Сначала почувствуй, как роли откликаются вместе, а затем соберём личный смысл без поспешных выводов.</p>
      <div class="tarot-thread-map">${p.positions.map((pos, i) => {
        const c = p.cards[i] || {};
        const orientation = c.reversed ? ' · перевёрнутая' : ' · прямая';
        return `<span><b>${esc(pos)}:</b> ${esc(c.name || 'карта')}${esc(orientation)}</span>`;
      }).join('')}</div>
      <div class="tarot-proof"><b>Доказательная карточка</b><span>Колода: ${esc(ledger.deck_id || 'RWS')}</span><span>Ledger: ${esc(ledger.version || 'не указан')} · checksum ${esc(ledger.checksum || '—')}</span>${pairs.length ? `<div class="tarot-proof__pairs">${pairs.map(pair => `<span>${esc(pair.left)} + ${esc(pair.right)} · ${esc(pair.rule)}</span>`).join('')}</div>` : ''}<small>Это подтверждает состав и порядок расклада, но не делает символическое толкование фактом.</small></div>`;
    w.appendChild(thread);
    const b = document.createElement('button');
    b.className = 'btn btn-primary tarot-interpret-btn';
    b.style.marginTop = '14px';
    b.dataset.act = 'interpret';
    b.textContent = 'Собрать личный смысл';
    w.appendChild(b);
  };

  // Карта дня: переворот раскрывает смысл

  app.flipDayCard = function(el) {
    haptic('light');
    const c = el && el.closest ? el.closest('.tarot-card-big') : null;
    if (c) c.classList.toggle('flipped');
  };


  app.doInterpret = async function() {
    const p = this.chat.pending;
    if (!p || p.kind !== 'tarot-cards') return;
    this.chat.busy = true;
    this.renderChat(document.getElementById('app-main'));
    try {
      const r = await api('/api/tarot/interpret/' + p.reading_id, { method: 'POST' });
      // B3: гард гонки — если юзер ушёл/переключил чат, не вливаем ответ в чужой тред
      const key = this.chat.key, tid = this.chat.tid;
      const inThread = () => this.chat.key === key && this.chat.tid === tid;
      // Эффект «раскрытия смысла»: карты переворачиваются одна за другой с задержкой 120 мс
      // (даже если все уже открыты — визуальный ритуал перед трактовкой)
      p.revealed.forEach((_, i) => {
        setTimeout(() => {
          if (!inThread()) return;
          const cards = document.querySelectorAll('.tcard[data-i="' + i + '"]');
          if (cards[0]) cards[0].classList.add('open');
        }, i * 120);
      });
      // Ждём завершения анимации (max delay + transition time) перед показом ответа
      setTimeout(() => {
        if (!inThread()) return;
        this.chat.messages.push({ role: 'assistant', text: r.answer });
        this.chat.pending = null;
        this.chat.busy = false;
        this.renderChat(document.getElementById('app-main'));
      }, p.revealed.length * 120 + 750);
      // Во время ожидания показываем индикатор «раскрываю смысл…»
      if (inThread()) {
        this.chat.messages.push({ role: 'assistant', text: '✨ Раскрываю смысл карт по очереди…' });
        this.renderChat(document.getElementById('app-main'));
      }
    } catch (e) {
      this.chat.messages.push({ role: 'assistant', text: '😔 ' + friendlyError(e) });
      this.chat.pending = null;
      this.chat.busy = false;
      this.renderChat(document.getElementById('app-main'));
    }
  };


  app.featureTarotHistory = async function() {
    if (this.chat.pending && this.chat.pending.kind === 'history') return; // B4 re-entry
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
      this.chat.pending = { kind: 'history', loading: false, rows: '<div style="color:var(--text-faint)">' + esc(friendlyError(e)) + '</div>' };
    }
    this.renderChat(document.getElementById('app-main'));
  };

  /* ═══ ФИЧА: НАТАЛЬНАЯ КАРТА → строится и сохраняется в профиль ═══ */

