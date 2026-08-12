/* home: домашний экран + хаб */
  app.renderHome = function(main) {
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
          const wd = WD_SHORT, mon = MON_RU;
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
              <div class="tb-face tb-front" style="background-image:url('/static/img/tarot/${esc(t.card.img || 'm00')}.jpg')">
                <span class="tb-arc">${esc(toRoman(t.card.num))}</span>
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

        ${t && t.next_action && t.next_action.kind ? `
        <div class="spacer"></div>
        <div class="section-title">🧭 Что дальше</div>
        <div class="glass na-card">
          <span class="na-ico">${esc(t.next_action.emoji || '✨')}</span>
          <div class="na-body">
            <div class="na-title">${esc(t.next_action.title)}</div>
            <div class="na-text">${esc(t.next_action.text)}</div>
          </div>
          ${t.next_action.fn
            ? `<button class="btn btn-primary na-btn" data-act="chat-fn" data-chat="${esc(t.next_action.chat || 'oracle')}" data-fn="${esc(t.next_action.fn)}">${esc(t.next_action.cta)}</button>`
            : `<span class="na-empty">${esc(t.next_action.cta)}</span>`}
        </div>` : ''}

        <div class="spacer"></div>
        <div class="section-title">🪐 Твои агенты</div>
        <div class="dock-grid">
          ${this.agents.length ? this.agents.map(a => `
            <div class="dock-item" data-act="chat" data-chat="${a.code}">
              <div class="dock-orb" style="--ac:${esc(a.accent || 'var(--gold)')}"><img class="dock-face" src="/static/img/agents/${esc(a.code)}.jpg" alt="${esc(a.name)}"></div>
              <div class="dock-name">${esc(a.name.split(' ')[0])}</div>
              ${a.title ? `<div class="dock-role">${esc(a.title)}</div>` : ''}
            </div>`).join('') : '<div class="skeleton" style="height:74px;border-radius:16px;grid-column:1/-1"></div>'}
        </div>
        <div style="color:var(--text-faint);font-size:11.5px;text-align:center;margin-top:6px">Открой агента — задай вопрос или используй его функцию прямо в чате</div>
      </div>`;
  };

  /* ═══ ХАБ АГЕНТОВ ═══ */

  app.renderHub = function(main) {
    if (this.chat.key) return this.renderChat(main);
    const list = this.agents.length ? this.agents : [
      { code: 'oracle', name: 'Лилит', title: 'Личный Оракул', emoji: '🔮', accent: '#e8c56b' },
      { code: 'astro', name: 'Урания', title: 'Астролог', emoji: '🌌', accent: '#7fb4e8' },
      { code: 'tarot', name: 'Мадам Ленорман', title: 'Таролог', emoji: '🎴', accent: '#c58bd8' },
    ];
    main.innerHTML = `
      <div class="screen">
        <div class="hub-head">
          <h1>Твой Оракул</h1>
          <p>Чат — главный инструмент. Выбери агента: задай вопрос или нажми его функцию.</p>
        </div>
        <div class="agent-list">
          ${list.map(a => `
            <div class="agent-card ${this.chat.key === a.code ? 'glow' : ''}" style="--ac:${esc(a.accent || 'var(--gold)')}" data-act="chat" data-chat="${a.code}">
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
                  <span class="tool" style="--ac2:${esc(a.accent || 'var(--gold)')}" data-act="chat-fn" data-chat="${a.code}" data-fn="${f.h}">
                    <span class="tool-ico">${f.e}</span>
                    <span class="tool-txt"><span class="tool-t">${esc(f.t)}</span>${f.d ? `<span class="tool-d">${esc(f.d)}</span>` : ''}</span>
                  </span>`).join('')}
              </div>
            </div>`).join('')}
        </div>
      </div>`;
  };

  /* ═══ ЧАТ — ГЛАВНЫЙ ИНСТРУМЕНТ ═══ */

