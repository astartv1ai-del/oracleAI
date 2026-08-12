/* home: домашний экран + хаб */
  app.renderHome = function(main) {
    const t = this.today;
    const pulse = this.dailyPulse || {};
    const diary = pulse.diary || {};
    const prompt = pulse.prompt || {};
    const practices = (pulse.practices && pulse.practices.items) || [];
    const activePractice = practices.find(p => p.started && !p.finished) || practices.find(p => !p.finished) || null;
    // Домашний экран должен оставаться полезным даже при временной недоступности API.
    const homeAgents = this.agents.length
      ? this.agents
      : AGENT_FALLBACK.map(a => this.normalizeAgent(a, a.code));
    const diaryDone = !!prompt.written_today;
    const ritualCompleted = (diaryDone ? 1 : 0) + (activePractice && activePractice.last_done ? 1 : 0);
    const ritualTone = ritualCompleted === 2
      ? 'Ты уже выбрала себя сегодня. Можно просто побыть в этом ощущении.'
      : ritualCompleted === 1
        ? 'Одна опора уже есть. Второй шаг — только если захочется.'
        : 'Выбери одну маленькую точку опоры. Этого достаточно.';
    const seasonalVariant = experimentVariant('home_ritual_entry', ['control', 'seasonal']);
    trackExperiment('home_ritual_entry', seasonalVariant);
    const seasonIndex = Math.floor(((new Date().getMonth() + 1) % 12) / 3);
    const seasonalMoments = [
      { title: 'Зимний свет', copy: 'Разреши себе меньше спешки и больше тёплых пауз.' },
      { title: 'Время расцветать', copy: 'Выбери один маленький шаг, который хочется начать для себя.' },
      { title: 'Сезон полноты', copy: 'Заметь, что уже стало твоей опорой, и поблагодари себя.' },
      { title: 'Время бережно отпустить', copy: 'Освободи место для того, что действительно важно сейчас.' },
    ];
    const seasonal = seasonalMoments[seasonIndex];
    main.innerHTML = `
      <div class="screen">
        <div class="hero-orb">
          <div class="orb"></div>
          <div class="hero-moon-orb" aria-hidden="true">${t && t.moon ? moonSvg(t.moon.emoji) : moonSvg('🌙')}</div>
          <div class="hero-body" style="position:relative;z-index:2">
            <div class="hero-date">${fmtDate()}</div>
            <div class="hero-ritual-label">Твой мягкий ритуал дня</div>
            <div class="hero-title">${this.me && this.me.name ? `Рада видеть тебя, <em>${esc(this.me.name.split(' ')[0])}</em>.` : 'Рада, что ты здесь.'}</div>
            ${t && t.moon ? `<div class="hero-moon-txt">${esc(t.moon.name)} · ${t.moon.day}-й лунный день<br><em>${esc(t.moon.advice)}</em></div>` : '<div class="hero-moon-txt">Сегодня можно не искать идеальный ответ.<br><em>Выбери один бережный шаг для себя.</em></div>'}
          </div>
          <button class="ritual-cta" data-act="chat" data-chat="oracle" aria-label="Открыть личный ритуал с Оракулом"><span>Получить мой знак дня</span><span aria-hidden="true">→</span></button>
        </div>

        ${seasonalVariant === 'seasonal' ? `<section class="seasonal-moment" aria-label="Сезонный ритуал"><div class="seasonal-moment__sigil" aria-hidden="true">✦</div><div><div class="section-kicker">Сезонный знак</div><h2>${seasonal.title}</h2><p>${seasonal.copy}</p></div></section>` : ''}
        <section class="daily-ritual daily-ritual--${ritualCompleted === 2 ? 'complete' : ritualCompleted ? 'in-progress' : 'begin'}" aria-label="Твой ритм на сегодня">
          <div class="daily-ritual-head"><div><div class="section-kicker">Твой ритм</div><h2>Вернуться к себе</h2></div><div class="daily-ritual-score" aria-label="${ritualCompleted} из 2 бережных шагов">${ritualCompleted}<span>/2</span></div></div>
          <div class="daily-ritual-progress" aria-hidden="true"><i style="--ritual-progress:${ritualCompleted / 2}"></i></div>
          <p class="daily-ritual-status">${ritualTone}</p>
          <div class="daily-ritual-grid">
            <button class="daily-step ${diaryDone ? 'is-done' : ''}" data-act="chat-fn" data-chat="oracle" data-fn="featureDiary" aria-label="${diaryDone ? 'Дневник заполнен, открыть записи' : 'Открыть дневник состояния'}">
              <span class="daily-step-mark">${diaryDone ? '✓' : '◌'}</span><span class="daily-step-copy"><b>${diaryDone ? 'Ты уже услышала себя' : 'Отметить своё состояние'}</b><small>${diaryDone ? 'Дневник уже ждёт тебя в личной библиотеке.' : esc(prompt.prompt || 'Одно честное предложение о том, как ты сейчас.')}</small></span><span class="daily-step-arrow">›</span>
            </button>
            ${activePractice ? `<button class="daily-step ${activePractice.last_done ? 'is-done' : ''}" data-act="p-action" data-code="${esc(activePractice.code)}" data-a="${activePractice.started ? 'done' : 'start'}" aria-label="${activePractice.started ? 'Отметить шаг практики' : 'Начать практику'}">
              <span class="daily-step-mark">${activePractice.last_done ? '✓' : esc(activePractice.emoji || '✦')}</span><span class="daily-step-copy"><b>${esc(activePractice.title)}</b><small>${esc(activePractice.started ? (activePractice.today_step || 'Отметить маленький шаг') : (activePractice.goal || activePractice.about || 'Мягкая практика на сегодня'))}</small></span><span class="daily-step-arrow">›</span>
            </button>` : ''}
          </div>
          <p class="daily-ritual-note">Без штрафов за пропуски. Это не чек-лист «идеальной жизни», а две мягкие точки опоры для тебя.</p>
        </section>

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
        <div class="section-kicker">Только для тебя</div>
        <div class="section-title">Знак на сегодня</div>
        <div class="forecast-flow">
          ${t ? esc(t.forecast) : '<div class="forecast-fallback"><b>Начни с того, что уже чувствуешь.</b><span>Открой личный знак дня или задай Оракулу вопрос — это тоже хороший способ вернуться к себе.</span></div>'}
        </div>

        ${t && t.card ? `
        <div class="spacer"></div>
        <div class="section-kicker">Символ дня</div>
        <div class="section-title">Карта, которая рядом</div>
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
        <div class="section-kicker">Один бережный шаг</div>
        <div class="section-title">Продолжить ритуал</div>
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
        <div class="section-kicker">Выбери настроение</div>
        <div class="section-title">С кем поговорим?</div>
        <div class="dock-grid">
          ${homeAgents.map(a => `
            <button class="dock-item" type="button" data-act="chat" data-chat="${a.code}" aria-label="Открыть диалог с ${esc(a.name)}">
              <span class="dock-orb" style="--ac:${esc(a.accent || 'var(--gold)')}"><img class="dock-face" src="/static/img/agents/${esc(a.code)}.jpg" alt="" loading="lazy"></span>
              <span class="dock-name">${esc(a.name.split(' ')[0])}</span>
              ${a.title ? `<span class="dock-role">${esc(a.title)}</span>` : ''}
            </button>`).join('')}
        </div>
        <div class="home-agent-note">Каждый проводник смотрит на твою историю по-своему. Начни с того, чей голос откликается сегодня.</div>
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
          <h1>Твои проводники</h1>
          <p>Не нужно знать «правильный» вопрос. Выбери того, с кем хочется побыть сегодня — он поможет разложить мысли по местам.</p>
        </div>
        <div class="agent-list">
          ${list.map(a => `
            <div class="agent-card ${this.chat.key === a.code ? 'glow' : ''}" style="--ac:${esc(a.accent || 'var(--gold)')}" data-act="chat" data-chat="${a.code}">
              <div class="ac-top">
                <div class="agent-avatar">${agentSprite(a)}</div>
                <div style="flex:1;min-width:0">
                  <div class="ac-head">
                    <div class="agent-title">${esc(a.name)}</div>
                  </div>
                  <div class="agent-role">${esc(a.title || a.code)}</div>
                  <div class="agent-last">${esc(a.last_text || a.tagline || 'Готова выслушать тебя')}</div>
                  <span class="online-label">рядом для тебя</span>
                </div>
                <button class="btn btn-ghost" style="padding:7px 12px;font-size:12px" data-act="chat" data-chat="${a.code}" aria-label="Открыть диалог с ${esc(a.name)}">Начать</button>
              </div>
              ${(a.suggestions && a.suggestions.length) ? `
              <div class="agent-ask-chips">
                ${a.suggestions.slice(0, 3).map(s => `
                  <span class="ask-chip" data-act="ask" data-chat="${a.code}" data-q="${esc(s)}">${esc(s)}</span>`).join('')}
              </div>` : ''}
              <div class="section-kicker" style="margin:15px 0 7px;color:var(--ac)">Можно спросить</div>
              <div class="agent-chips">
                ${(FEATURES[a.code] || []).slice(0, 4).map(f => `
                  <button class="tool" style="--ac2:${esc(a.accent || 'var(--gold)')}" data-act="chat-fn" data-chat="${a.code}" data-fn="${f.h}" aria-label="${esc(f.t)}: ${esc(f.d || '')}">
                    <span class="tool-ico" aria-hidden="true">${sigilIcon(f.id)}</span>
                    <span class="tool-txt"><span class="tool-t">${esc(f.t)}</span>${f.d ? `<span class="tool-d">${esc(f.d)}</span>` : ''}</span>
                  </button>`).join('')}
              </div>
            </div>`).join('')}
        </div>
      </div>`;
  };

  /* ═══ ЧАТ — ГЛАВНЫЙ ИНСТРУМЕНТ ═══ */

