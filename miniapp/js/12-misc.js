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

  app.softEmpty = function({ icon = '✦', eyebrow = '', title, copy, action = '', tone = '' }) {
    return `<div class="soft-empty ${tone ? 'soft-empty--' + tone : ''}">
      <div class="soft-empty__orb" aria-hidden="true">${icon}</div>
      ${eyebrow ? `<span class="soft-empty__eyebrow">${eyebrow}</span>` : ''}
      <div class="soft-empty__title">${title}</div>
      <div class="soft-empty__copy">${copy}</div>
      ${action ? `<div class="soft-empty__action">${action}</div>` : ''}
    </div>`;
  };

  app.renderProfile = async function(main) {
    const me = this.me;
    const firstName = me && me.name ? esc(me.name.split(' ')[0]) : 'Ты';
    const streak = me && me.global_streak ? me.global_streak : 0;
    const questions = me && me.allowance && typeof me.allowance.left !== 'undefined' ? me.allowance.left : '—';
    const genderLabel = gendered(me, t('female'), t('male'), t('notSpecified'));
    const identityBlock = me && me.birth_date ? `
      <div class="glass" style="padding:14px 16px;font-size:13px">
        <div class="planet-line"><div class="p-ico">◌</div><div class="p-name">Рождение</div><div class="p-val">${esc(me.birth_date)}</div></div>
        <div class="planet-line"><div class="p-ico">⌁</div><div class="p-name">Время</div><div class="p-val">${esc(me.birth_time_known ? me.birth_time : 'не известно')}</div></div>
        <div class="planet-line"><div class="p-ico">⌖</div><div class="p-name">Город</div><div class="p-val">${esc(me.birth_city || '—')}</div></div>
      </div>` : `
      <div class="profile-empty">
        <div class="profile-empty-title">Соберём твою карту?</div>
        <div class="profile-empty-copy">Три коротких шага — и Оракул сможет говорить с тобой точнее, бережнее и по твоему ритму.</div>
        <div class="profile-empty-steps"><span class="profile-empty-step"><b>01</b>дата</span><span class="profile-empty-step"><b>02</b>время</span><span class="profile-empty-step"><b>03</b>город</span></div>
        <button class="btn btn-primary" style="width:100%;margin-top:14px" data-act="chat" data-chat="astro">Открыть мою карту</button>
      </div>`;
    main.innerHTML = `
      <div class="screen">
        <div class="profile-hero">
          <div class="profile-kicker">Твоё пространство</div>
          <div class="profile-name">${firstName}, твой путь</div>
          <div class="profile-copy">Здесь собираются знаки, вопросы и мысли, которые хочется оставить рядом.</div>
          <div class="ritual-meter"><span class="ritual-meter-label">${streak ? 'Серия: ' + streak + ' дн.' : 'Первый ритуал'}</span><span class="ritual-meter-track"><span class="ritual-meter-fill" style="width:${Math.min(100, Math.max(18, streak ? 18 + streak * 8 : 18))}%"></span></span></div>
        </div>

        <div class="ptab-bar">
          <button class="ptab active" data-act="ptab" data-tab="summary">Сводка</button>
          <button class="ptab" data-act="ptab" data-tab="chart">Карта</button>
          <button class="ptab" data-act="ptab" data-tab="history">История</button>
          <button class="ptab" data-act="ptab" data-tab="memory">Память</button>
        </div>

        <div class="ptab-pane active" id="ptab-summary">
          <div class="section-kicker">Твоя серия</div>
          <div class="glass" style="display:flex;align-items:center;gap:12px;padding:14px 16px;margin-bottom:11px">
            <span style="width:43px;height:43px;display:grid;place-items:center;border-radius:14px;background:rgba(245,212,139,.13);color:var(--champagne-300);font-size:21px;flex-shrink:0">✦</span>
            <div style="flex:1;min-width:0">
              <div style="color:var(--text-main);font-family:var(--font-serif);font-weight:700;font-size:17px">${streak ? 'Ты уже ' + streak + ' ' + (streak === 1 ? 'день' : streak < 5 ? 'дня' : 'дней') + ' рядом с собой' : 'Твой первый знак уже ждёт'}</div>
              <div style="font-size:12.5px;color:var(--text-soft);line-height:1.45;margin-top:3px">${streak ? 'Завтра откроется новый прогноз, чтобы мягко продолжить серию.' : 'Начни с одного вопроса — так рождается личный ритуал.'}</div>
            </div>
          </div>
          <div class="stat-row">
            <div class="stat"><div class="sv">${streak || '—'}</div><div class="sl">Ритуалы</div></div>
            <div class="stat"><div class="sv">${me && typeof me.crystals !== 'undefined' ? me.crystals : '—'}</div><div class="sl">Искры</div></div>
            <div class="stat"><div class="sv">${questions}</div><div class="sl">Вопросы</div></div>
            <div class="stat"><div class="sv">${me && me.diary_streak ? me.diary_streak : '—'}</div><div class="sl">Заметки</div></div>
          </div>
          <div class="spacer"></div>
          <div class="section-kicker">Твоя основа</div>
          <div class="section-title">Данные рождения</div>
          ${identityBlock}
          <button class="glass language-row" data-act="gender" type="button" aria-label="${esc(t('changeGender'))}">
            <span class="language-row__copy"><b>${esc(t('gender'))}</b><small>${esc(genderLabel)}</small></span>
            <span class="language-row__chevron" aria-hidden="true">›</span>
          </button>
          <button class="glass language-row" data-act="language" type="button" aria-label="${esc(t('changeLanguage'))}">
            <span class="language-row__copy"><b>${esc(t('language'))}</b><small>${esc((me && me.lang) === 'en' ? t('english') : t('russian'))}</small></span>
            <span class="language-row__chevron" aria-hidden="true">›</span>
          </button>
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
      const exactChart = c.precision === 'exact';
      const precisionCopy = exactChart
        ? `Асцендент ${esc(asc.sign || '—')}`
        : esc(c.note || 'Время рождения не указано — ASC, MC и дома не показываем.');
      const planets = (c.planets || []).slice(0, 8).map(p => `
        <div class="planet-line">
          <div class="p-ico">${SIGNS[p.sign] || ''}</div>
          <div class="p-name">${esc(p.name)}</div>
          <div class="p-val">${esc(p.sign)}${exactChart && p.house ? ' · ' + p.house : ''}</div>
        </div>`).join('');
      if (chartEl) chartEl.innerHTML = `
        <div class="glass" style="padding:16px">
          <div style="display:flex;align-items:center;gap:16px">
            <div class="chart-wheel" style="width:110px;height:110px">
              <div class="wheel-center"><div class="wc-s">${sun.symbol || '☉'}</div><div class="wc-t">${esc(sun.sign || '')}</div></div>
            </div>
            <div style="flex:1;font-size:13px">
              <div style="font-family:var(--font-serif);color:var(--gold-bright);font-size:14.5px">${esc(sun.sign || '—')}</div>
              <div style="color:var(--text-dim);font-size:12px;line-height:1.4">${precisionCopy}</div>
              <div style="margin-top:10px;display:flex;gap:8px">
                <button class="btn btn-ghost" style="padding:8px 12px;font-size:12px" data-act="chat" data-chat="astro">Спросить</button>
                <button class="btn btn-ghost" style="padding:8px 12px;font-size:12px" data-act="full-chart">Полная карта</button>
              </div>
            </div>
          </div>
          <div style="margin-top:10px">${planets}</div>
          <div style="color:var(--text-faint);font-size:11px;margin-top:6px">${exactChart ? 'Раху · Кету · дома · аспекты — в «Полной карте»' : 'Планеты и аспекты доступны без времени; ASC, MC и дома — после уточнения времени рождения.'}</div>
        </div>`;
    } catch (e) {
      if (chartEl) chartEl.innerHTML = this.softEmpty({
        icon: '🌌', eyebrow: 'Твоя основа', title: 'Карта ещё не собрана',
        copy: 'Укажи дату и город рождения. Время — только если ты его знаешь.',
        action: '<button class="btn btn-primary" data-act="chat" data-chat="astro">Собрать карту</button>'
      });
    }

    try {
      const rows = await pTarot;
      // компактно: до 3 строк + «Все N →» (тап открывает модал со всем списком)
      if (tarotEl) {
        if (!rows.length) {
          tarotEl.innerHTML = this.softEmpty({
            icon: '🎴', eyebrow: 'Твой первый расклад', title: 'Карты ждут твой вопрос',
            copy: 'Выбери бережный расклад — он сохранится здесь, чтобы к нему можно было вернуться.',
            action: '<button class="btn btn-primary" data-act="chat-fn" data-chat="tarot" data-fn="featureTarot">Задать вопрос картам</button>'
          });
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
    } catch (e) {
      if (tarotEl) tarotEl.innerHTML = this.softEmpty({
        icon: '🎴', eyebrow: 'История раскладов', title: 'Не получилось открыть историю',
        copy: 'Это временно. Новый расклад по-прежнему можно сделать в чате.', tone: 'recovery',
        action: '<button class="btn btn-ghost" data-act="chat-fn" data-chat="tarot" data-fn="featureTarot">Открыть Таролога</button>'
      });
    }

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
        </div>`).join('') : this.softEmpty({
          icon: '✦', eyebrow: 'Личный архив', title: 'Здесь появятся твои разборы',
          copy: 'Сохраняй важные ответы из диалогов, чтобы возвращаться к ним в нужный момент.'
        });
    } catch (e) {
      if (repEl) repEl.innerHTML = this.softEmpty({
        icon: '✦', eyebrow: 'Личный архив', title: 'Разборы временно недоступны',
        copy: 'Попробуй открыть этот раздел немного позже.', tone: 'recovery'
      });
    }

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
      // «На паузе» означает, что Оракул не использует и не сохраняет новые факты.
      // Это не скрывает уже сохранённое от её владелицы: архив всегда остаётся доступен.
      const rows = await api('/api/memories');
      this._memFull = rows;
      this._memSearch = '';
      this.renderMemModal();
    } catch (e) {
      const body = document.getElementById('mem-body');
      if (body) body.innerHTML = this.softEmpty({
        icon: '🧠', eyebrow: 'Личная память', title: 'Память пока недоступна',
        copy: 'Твои сохранённые факты остаются под защитой. Попробуй открыть их чуть позже.', tone: 'recovery'
      });
    }
  };


  app.renderMemModal = function() {
    const el = document.getElementById('mem-body');
    if (!el) return;
    const enabled = !(this.me && this.me.memory_enabled === false);
    const rows = this._memFull || [];
    const list = rows.map((m, index) => {
      const fact = String(m.fact || '');
      const haystack = esc(fact.toLowerCase());
      return `<article class="mem-manage-row" data-mem-item data-mem-text="${haystack}">
        <div class="mem-manage-row__top">
          <span class="mem-manage-index" aria-hidden="true">${String(index + 1).padStart(2, '0')}</span>
          <time class="mem-manage-meta">${esc((m.created_at || '').slice(0, 10)) || 'без даты'}</time>
          <button class="mem-del" data-act="del-mem" data-id="${m.id}" title="Удалить факт" aria-label="Удалить факт">${sigilIcon('spark')}</button>
        </div>
        <div class="mem-manage-txt">${esc(fact)}</div>
      </article>`;
    }).join('');
    const stateCopy = enabled
      ? 'Лилит использует только этот список, чтобы помнить важное между диалогами.'
      : 'Память на паузе: новые факты не сохраняются и не попадают в ответы. Этот архив видишь только ты.';
    const archive = rows.length ? `
      <div class="mem-search">
        ${sigilIcon('spark')}
        <input class="ipt" id="mem-search" type="search" placeholder="Найти в ${rows.length} ${rows.length === 1 ? 'факте' : 'фактах'}" autocomplete="off" aria-label="Найти факт в памяти">
        <span class="mem-search-count" data-mem-count>${rows.length}</span>
      </div>
      <div class="mem-manage-list" data-mem-list>${list}</div>
      <div class="memory-search-empty" data-mem-empty hidden>Ничего не нашлось. Попробуй другое слово или очисти поиск.</div>`
      : `<div class="memory-empty">
          <span class="memory-empty__sigil">${sigilIcon('spark')}</span>
          <b>Здесь пока тихо</b>
          <p>${enabled ? 'Добавь один факт сама или расскажи о важном в диалоге — Лилит спросит разрешение сохранить его.' : 'Включи память, когда захочешь сохранять важное между диалогами.'}</p>
        </div>`;
    el.innerHTML = `
      <section class="memory-hero ${enabled ? 'is-enabled' : 'is-paused'}">
        <div class="memory-hero__top">
          <div>
            <span class="memory-eyebrow">Личный контекст</span>
            <h4>Память о тебе</h4>
          </div>
          <button class="memory-switch ${enabled ? 'is-on' : ''}" data-act="toggle-memory" type="button" role="switch" aria-checked="${enabled}" aria-label="${enabled ? 'Поставить память на паузу' : 'Включить память'}">
            <span class="memory-switch__track" aria-hidden="true"><span></span></span>
            <span>${enabled ? 'Активна' : 'На паузе'}</span>
          </button>
        </div>
        <p>${stateCopy}</p>
        <div class="memory-hero__foot"><span>${rows.length} ${rows.length === 1 ? 'факт' : rows.length < 5 ? 'факта' : 'фактов'}</span><span>Ты можешь удалить любой</span></div>
      </section>
      ${enabled ? `<div class="mem-add memory-add">
        <input class="ipt" id="mem-new" placeholder="Например: я люблю тихие утра" autocomplete="off" maxlength="500"/>
        <button class="send-btn" data-act="add-mem" title="Добавить факт" aria-label="Добавить факт">${sigilIcon('spark')}</button>
      </div>` : ''}
      <div class="memory-archive-head"><b>Твой архив</b><span>${enabled ? 'используется в новых ответах' : 'сохранён и скрыт от Оракула'}</span></div>
      ${archive}`;

    const search = el.querySelector('#mem-search');
    if (search) search.addEventListener('input', event => this.filterMemories(event.target.value));
  };

  app.filterMemories = function(query) {
    const normalized = String(query || '').trim().toLowerCase();
    const rows = Array.from(document.querySelectorAll('[data-mem-item]'));
    let visible = 0;
    rows.forEach(row => {
      const matched = !normalized || String(row.dataset.memText || '').includes(normalized);
      row.hidden = !matched;
      if (matched) visible += 1;
    });
    const count = document.querySelector('[data-mem-count]');
    const empty = document.querySelector('[data-mem-empty]');
    if (count) count.textContent = normalized ? visible + ' / ' + rows.length : rows.length;
    if (empty) empty.hidden = visible !== 0;
  };


  app.toggleMemory = async function() {
    const current = !(this.me && this.me.memory_enabled === false);
    try {
      await api('/api/profile', { method: 'POST', body: JSON.stringify({ memory_enabled: !current }) });
      this.me = await api('/api/me');
      // Факты остаются доступны владелице, даже когда новые сохранения и recall поставлены на паузу.
      this._memFull = await api('/api/memories');
      this._memSearch = '';
      this.renderMemModal();
      haptic('light');
    } catch (e) { alert(e.message); }
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
      const exactChart = c.precision === 'exact';
      const precisionNotice = !exactChart ? `<div class="chart-precision-note"><b>Точность карты</b><span>${esc(c.note || 'Время рождения не указано.')}</span><small>Планеты и аспекты рассчитаны по дате. ASC, MC и дома не отображаются без времени рождения.</small></div>` : '';
      const row = (ico, name, val) => `<div class="fc-row"><span class="fc-ico">${ico}</span><span class="fc-name">${esc(name)}</span><span class="fc-val">${val}</span></div>`;
      const pRows = (c.planets || []).map(p =>
        row(SIGNS[p.sign] || '•', p.name, `${esc(p.sign)} ${p.deg}°${exactChart && p.house ? ' · дом ' + p.house : ''}${p.retro ? ' ℞' : ''}`)).join('');
      const nRows = (c.nodes || []).map(n =>
        row('☊', n.name, `${esc(n.sign)} ${n.deg}°${exactChart && n.house ? ' · дом ' + n.house : ''}${n.retro ? ' ℞' : ''}`)).join('');
      const hRows = (c.houses || []).map(h =>
        row(`${h.n}`, `${h.n}-й дом`, `${esc(h.sign)} ${h.deg}°`)).join('');
      const aRows = (c.aspects || []).slice(0, 12).map(a =>
        row(a.glyph || '◈', `${a.p1} — ${a.p2}`, `${a.aspect}${a.orb != null ? ' · орб ' + a.orb + '°' : ''}`)).join('');
      document.getElementById('fc-body').innerHTML = `
        ${precisionNotice}
        <div class="fc-hero" style="margin-bottom:6px;display:flex;justify-content:center;align-items:center;background:rgba(14,13,30,.7);border-radius:var(--r-m);padding:10px;box-shadow:var(--sh-card);">
          <div style="width:260px;height:260px;">${nativitySvg(c, 260)}</div>
        </div>
        <div class="fc-card">
          <span class="fc-ico">☉</span>
          <div class="fc-card-body">
            <h4 class="fc-t">${exactChart ? 'Твой знак и восход' : 'Твоя солнечная основа'}</h4>
            <div class="fc-desc"><b>Солнце ${esc(c.sun && c.sun.sign || '')}</b> (${esc(c.sun && c.sun.element || '')}) — твоя суть, воля и энергия.${exactChart ? ` <b>Асцендент ${esc(c.ascendant && c.ascendant.sign || '—')}</b> (${esc(c.ascendant && c.ascendant.deg ? Math.round(c.ascendant.deg) : '—')}°) — как тебя видят со стороны. <b>MC ${esc(c.mc && c.mc.sign || '—')}</b> — направление и цель.` : ' Время рождения не указано, поэтому не добавляем предположения об асценденте и направлении MC.'}</div>
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
                <span class="pl-info"><span class="pl-t">${esc(p.name)} · ${esc(p.sign)}${exactChart && p.house ? ' · дом ' + p.house : ''}${p.retro ? ' ℞' : ''}</span><span class="pl-d">${p.deg ? p.deg + '°' : ''}</span></span>
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
                  <span class="pl-info"><span class="pl-t">${esc(n.sign)} ${n.deg}°${exactChart && n.house ? ' · дом ' + n.house : ''}${n.retro ? ' ℞' : ''}</span>
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
        ${exactChart ? `<div class="fc-card">
          <span class="fc-ico">🏠</span>
          <div class="fc-card-body">
            <h4 class="fc-t">Дома</h4>
            <div style="font-size:12px;color:var(--text-dim);line-height:1.55">
              ${(c.houses || []).map((h, i) => `<b style="color:var(--gold-bright)">${i + 1}-й дом · ${esc(h.sign || '')}</b> ${h.deg ? h.deg + '°' : ''}${i < 11 ? ' · ' : ''}`).join('')}
            </div>
          </div>
        </div>` : ''}
        <button class="btn btn-primary" style="margin-top:14px" data-act="chat" data-chat="astro">Спросить Астролога про карту</button>
        <button class="btn btn-primary" style="width:100%;margin-top:8px" data-act="share-chart">📸 Сохранить карту в сторис</button>
        <button class="btn btn-ghost" style="width:100%;margin-top:8px" data-act="fc-explain">🧠 Разбор простыми словами</button>
        <div id="fc-explain" style="margin-top:12px"></div>`;
    } catch (e) {
      const body = document.getElementById('fc-body');
      if (body) body.innerHTML = this.softEmpty({
        icon: '🌌', eyebrow: 'Полная карта', title: 'Карта пока недоступна',
        copy: 'Проверь соединение и попробуй открыть её чуть позже.', tone: 'recovery',
        action: '<button class="btn btn-ghost" data-act="modal-close">Закрыть</button>'
      });
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
      box.innerHTML = this.softEmpty({
        icon: '✦', eyebrow: 'Разбор карты', title: 'Смысл пока не раскрылся',
        copy: 'Попробуй ещё раз немного позже — твоя карта никуда не исчезнет.', tone: 'recovery'
      });
    }
  };

  app.openGender = function() {
    const current = (this.me && this.me.gender) || null;
    this.showModal(`<h3>${esc(t('gender'))}</h3><button class="m-close" data-act="modal-close" aria-label="Close">✕</button>
      <p class="modal-soft-copy">${esc(t('genderCopy'))}</p>
      <div class="language-picker gender-picker">
        <button class="language-choice ${current === 'f' ? 'active' : ''}" data-act="set-gender" data-gender="f"><b>${esc(t('female'))} ♀</b><small>${esc(t('femaleCopy'))}</small></button>
        <button class="language-choice ${current === 'm' ? 'active' : ''}" data-act="set-gender" data-gender="m"><b>${esc(t('male'))} ♂</b><small>${esc(t('maleCopy'))}</small></button>
        <button class="language-choice gender-choice--skip ${current === null ? 'active' : ''}" data-act="set-gender" data-gender=""><b>${esc(t('notSpecified'))}</b><small>${esc(t('notSpecifiedCopy'))}</small></button>
      </div>`);
  };

  app.setGender = async function(gender) {
    const next = ['f', 'm'].includes(gender) ? gender : null;
    const previous = (this.me && this.me.gender) || null;
    if (next === previous) { this.closeModal(); return; }
    haptic('light');
    try {
      await api('/api/profile', { method: 'PATCH', body: JSON.stringify({ gender: next }) });
      this.me = Object.assign({}, this.me, { gender: next });
      this.closeModal();
      this.go('profile');
      this.toast(t('saved'));
    } catch (e) { this.toast(e.message || 'Не удалось сохранить пол'); }
  };

  app.openLanguage = function() {
    const current = (this.me && this.me.lang) || 'ru';
    this.showModal(`<h3>${esc(t('language'))}</h3><button class="m-close" data-act="modal-close" aria-label="Закрыть">✕</button>
      <p class="modal-soft-copy">${esc(t('languageCopy'))}</p>
      <div class="language-picker">
        <button class="language-choice ${current === 'ru' ? 'active' : ''}" data-act="set-lang" data-lang="ru"><b>${esc(t('russian'))}</b><small>Русский</small></button>
        <button class="language-choice ${current === 'en' ? 'active' : ''}" data-act="set-lang" data-lang="en"><b>${esc(t('english'))}</b><small>English</small></button>
      </div>`);
  };

  app.setLanguage = async function(lang) {
    if (!['ru', 'en'].includes(lang)) return;
    const previous = (this.me && this.me.lang) || 'ru';
    if (lang === previous) { this.closeModal(); return; }
    try {
      await api('/api/profile', { method: 'POST', body: JSON.stringify({ lang }) });
      localStorage.setItem('oracle_lang', lang);
      this.me = Object.assign({}, this.me, { lang });
      this.closeModal();
      this.renderFrame();
      this.go(this.view || 'profile');
      this.toast(t('saved'));
    } catch (e) { this.toast(e.message || 'Не удалось сменить язык'); }
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
      const body = document.getElementById('bell-body');
      if (body) body.innerHTML = this.softEmpty({
        icon: '🌙', eyebrow: 'Уведомления', title: 'Пока тихо',
        copy: 'Когда появится новый знак дня или важное напоминание, оно будет ждать тебя здесь.', tone: 'quiet'
      });
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

