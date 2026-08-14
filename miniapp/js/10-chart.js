/* chart: натальная карта — форма, построение, SVG, шаринг, планеты/стихии */
  app.featureChart = async function() {
    if (this.chat.pending && this.chat.pending.kind === 'chart') return;
    this.prepareChartOnboarding();
    const key = this.chat.key, view = this.view;
    const pend = this.chat.pending = {
      kind: 'chart',
      loading: true,
      html: this.chartLoadingHtml('restore')
    };
    this.renderChat(document.getElementById('app-main'));
    try {
      const c = await api('/api/chart');
      if (!widAlive(key, view, pend)) return;
      this.chat.pending = { kind: 'chart', loading: false, html: this.chartHtml(c) };
      haptic('soft');
    } catch (e) {
      if (!widAlive(key, view, pend)) return;
      // Карты ещё нет — собираем её прямо в чате, не отправляя в тупик профиля.
      this.chart = null;
      this.chat.pending = { kind: 'chart', loading: false, html: this.chartForm() };
    }
    this.renderChat(document.getElementById('app-main'));
  };


  // Onboarding показывается только на первом входе в сценарий карты и не мешает
  // человеку, который уже возвращается к сохранённому разбору.
  app.prepareChartOnboarding = function() {
    try {
      this._chartIntroPending = localStorage.getItem('oracle_chart_intro_seen') !== '1';
    } catch (e) {
      this._chartIntroPending = false;
    }
  };

  app.chartOnboardingHtml = function() {
    if (!this._chartIntroPending) return '';
    this._chartIntroPending = false;
    try { localStorage.setItem('oracle_chart_intro_seen', '1'); } catch (e) { /* private mode: guide is simply not persisted */ }
    return `<aside class="chart-onboarding" aria-label="Как читать карту">
      <span class="chart-onboarding__mark" aria-hidden="true">✦</span>
      <span class="chart-onboarding__copy"><b>Твоя карта — в три спокойных шага</b><small>Собери данные, тапни планету на колесе и затем спроси о том, что важно именно сейчас.</small></span>
    </aside>`;
  };

  app.chartLoadingHtml = function(mode) {
    const restoring = mode === 'restore';
    return `<section class="chart-loading" role="status" aria-live="polite" aria-label="${restoring ? 'Открываем сохранённую натальную карту' : 'Рассчитываем натальную карту'}">
      <span class="chart-loading__halo" aria-hidden="true"><i></i><i></i><i></i><b>✦</b></span>
      <span class="chart-loading__copy"><b>${restoring ? 'Открываем твою карту' : 'Собираем твою карту'}</b><small>${restoring ? 'Возвращаемся к твоим небесным ориентирам…' : 'Проверяем дату, место и собираем колесо…'}</small></span>
    </section>`;
  };


  app.chartSectionHtml = function(section, first) {
    if (!section) return '';
    const items = Array.isArray(section.items) ? section.items : [];
    return `<details class="chart-insight"${first ? ' open' : ''}>
      <summary><span class="chart-insight__title">${esc(section.title || 'Раздел карты')}</span><span class="chart-insight__chevron" aria-hidden="true">⌄</span></summary>
      <div class="chart-insight__body">
        ${section.intro ? `<p class="chart-insight__intro">${esc(section.intro)}</p>` : ''}
        <div class="chart-insight__items">
          ${items.map(item => `<article class="chart-insight__item${item.available ? '' : ' is-muted'}">
            <div class="chart-insight__item-head"><b>${esc(item.label || '')}</b><span>${esc(item.value || 'нет данных')}</span></div>
            <p>${esc(item.meaning || '')}</p>
          </article>`).join('')}
        </div>
        ${section.note ? `<p class="chart-insight__note">${esc(section.note)}</p>` : ''}
      </div>
    </details>`;
  };

  app.chartSectionsHtml = function(sections) {
    const map = sections && sections.sections ? sections.sections : {};
    const order = ['identity', 'mind_career', 'relationships', 'nodes'];
    return `<section class="chart-insights" aria-label="Понятный разбор натальной карты">
      <div class="chart-insights__kicker">КАК ЧИТАТЬ КАРТУ</div>
      <h3 class="chart-insights__title">Не только колесо — четыре смысловых слоя</h3>
      <p class="chart-insights__copy">Сначала смотри на факт размещения, затем на объяснение. Это символический инструмент самонаблюдения, а не диагноз и не приговор.</p>
      ${order.map((key, i) => this.chartSectionHtml(map[key], i === 0)).join('')}
    </section>`;
  };

  app.chartHtml = function(c) {
    this.chart = c;
    const sun = c.sun || {};
    const asc = c.ascendant || {};
    const planets = c.planets || [];
    const anglesAvailable = c.precision === 'exact';
    const precisionNotice = c.note ? `
      <div role="status" style="margin:9px 0 10px;padding:9px 10px;border:1px solid rgba(201,160,255,.26);border-radius:12px;color:var(--text-dim);font-size:11.5px;line-height:1.45">
        <b style="color:var(--gold-bright)">Точность карты</b> · ${esc(c.note)}
        ${!c.birth?.time_known ? '<br><span style="color:var(--text-faint)">Укажи время рождения в профиле, чтобы открыть ASC, MC и дома.</span>' : ''}
      </div>` : '';
    const aspects = c.aspects || [];
    const glyph = p => planetGlyph(p.name) || (p.sign ? SIGNS[p.sign] : '');
    const lines = planets.map(p => `
      <div class="planet-line">
        <div class="p-ico">${glyph(p)}</div>
        <div class="p-name">${esc(p.name)}</div>
        <div class="p-val">${esc(p.sign)}${p.house ? ' · дом ' + p.house : ''}${p.retro ? ' ☍' : ''}</div>
      </div>`).join('');
    // T6: легенда аспектов — цветные чипы, чтобы линии в колесе читались
    const legend = aspects.length ? `<div class="asp-legend">
        ${['☌ соединение', '⚹ секстиль', '△ трин'].map(a => `<span class="asp-chip" style="color:var(--gold)">${a}</span>`).join('')}
        ${[['□ квадрат', 'var(--violet)'], ['☍ оппозиция', '#ff6b6b']].map(([a, col]) => `<span class="asp-chip" style="color:${col}">${a}</span>`).join('')}
      </div>` : '';
    // легенда стихий: тап фильтрует планеты в колесе (добавлено в v2)
    const elLegend = `<div class="el-legend">
        ${[['fire','🔥 Огонь'],['earth','🌍 Земля'],['air','💨 Воздух'],['water','💧 Вода']].map(([k, l]) =>
          `<span class="el-chip" data-act="el-filter" data-el="${k}">${l}</span>`).join('')}
      </div>`;
    // «акценты карты» от бэкенда — если придут, покажем мягкими чипами; нет — тихо скроем
    const accents = Array.isArray(c.accents) ? c.accents : [];
    const accentChips = accents.length ? `<div class="asp-legend" style="margin:6px 0 8px">
        ${accents.map(a => `<span class="asp-chip" style="color:var(--violet)">${esc(a)}</span>`).join('')}
      </div>` : '';
    const takeaway = anglesAvailable
      ? `Солнце в ${esc(sun.sign || '—')} встречается с Асцендентом в ${esc(asc.sign || '—')}. Начни с этого дуэта: он помогает бережно связать внутреннее ощущение себя с тем, как ты проявляешься в мире.`
      : `Солнце в ${esc(sun.sign || '—')} — твоя надёжная точка опоры. Даже без времени рождения можно начать спокойный разговор о твоих планетах и вернуться к точным углам позже.`;
    return `
      <section class="chart-result" aria-live="polite">
        <div class="w-title">🌌 Натальная карта</div>
        ${this.chartOnboardingHtml()}
        <div class="nw" data-act="full-chart" title="Открыть полную карту">
          ${this.chart ? nativitySvg(this.chart, 210) : ''}
          <div class="nw-plaque" id="nw-plaque" aria-live="polite"></div>
        </div>
        <div class="chart-wheel-hint">Тапни планету — она расскажет о себе · тап по колесу — полный разбор</div>
        ${elLegend}
        ${accentChips}
        <div class="chart-signature">Солнце в ${esc(sun.sign || '—')}${anglesAvailable ? ' · Асцендент ' + esc(asc.sign || '—') : ''}</div>
        ${precisionNotice}
        <div class="chart-takeaway">
          <span class="chart-takeaway__label">ТВОЯ ОТПРАВНАЯ ТОЧКА</span>
          <p>${takeaway}</p>
          <small>Это ориентир для личного исследования, а не готовый ярлык.</small>
        </div>
        ${this.chartSectionsHtml(c.sections)}
      </section>
      <details class="chart-details">
        <summary>Планеты, аспекты и детали карты</summary>
        <div class="chart-details__body">
          ${legend}
          <div>${lines || '<div style="color:var(--text-faint);font-size:12.5px">Планеты ещё не рассчитаны</div>'}</div>
        </div>
      </details>
      <div style="color:var(--text-faint);font-size:11.5px;margin:10px 0">✓ Сохранена в твоём профиле — всегда под рукой.</div>
      <div style="display:flex;gap:8px;margin-top:6px">
        <button class="btn btn-primary" style="flex:1" data-act="ask-chart">Спросить про карту</button>
        <button class="btn btn-ghost" data-act="share-chart" title="Сохранить картинку для сторис">📸</button>
        <button class="btn btn-ghost" data-act="go" data-goto="profile">В профиль</button>
      </div>`;
  };


  app.chartForm = function(opts) {
    const me = this.me || {};
    const values = opts || {};
    const date = values.date != null ? values.date : (me.birth_date || '');
    const city = values.city != null ? values.city : (me.birth_city || '');
    const time = values.time != null ? values.time : (me.birth_time_known ? (me.birth_time || '') : '');
    const loading = !!values.loading;
    const disabled = loading ? ' disabled' : '';
    return `
      <div class="w-title">🌌 Построить натальную карту</div>
      ${this.chartOnboardingHtml()}
      <div class="chart-form-intro"><b>Начнём с даты и города.</b><span>Время рождения — по желанию: без него покажем планеты и аспекты, но честно не будем добавлять ASC, MC и дома.</span></div>
      <div class="chart-form"${loading ? ' aria-busy="true"' : ''}>
        ${values.error ? `<div class="chart-form-error" role="alert"><b>Нужна маленькая поправка</b><span>${esc(values.error)}</span></div>` : ''}
        <label class="chart-form__field" for="ch-date"><span>Дата рождения <em>обязательно</em></span><input class="ipt" id="ch-date" type="date" value="${esc(date)}" required${disabled}></label>
        <label class="chart-form__field" for="ch-city"><span>Город рождения <em>обязательно</em></span><input class="ipt" id="ch-city" value="${esc(city)}" placeholder="Например, Москва" autocomplete="address-level2"${disabled}></label>
        <label class="chart-form__field" for="ch-time"><span>Время рождения <em>если знаешь</em></span><input class="ipt" id="ch-time" type="time" value="${esc(time)}" placeholder="14:30"${disabled}></label>
        <button class="btn btn-primary chart-form__submit${loading ? ' is-loading' : ''}" data-act="build"${disabled}${loading ? ' aria-busy="true"' : ''}>${loading ? '<span class="chart-form__spinner" aria-hidden="true"></span><span>Собираю твою карту…</span>' : '<span>Рассчитать мою карту</span><span aria-hidden="true">✦</span>'}</button>
        ${loading ? this.chartLoadingHtml('build') : ''}
      </div>`;
  };


  app.doBuildChart = async function() {
    const date = (document.getElementById('ch-date') || {}).value || '';
    const time = (document.getElementById('ch-time') || {}).value || '';
    const city = (document.getElementById('ch-city') || {}).value || '';
    const cleanCity = city.trim();
    const validationError = !date ? 'Добавь дату рождения — она нужна для расчёта.' : (!cleanCity ? 'Добавь город рождения, чтобы корректно рассчитать карту.' : '');
    if (validationError) {
      haptic('error');
      this.chat.pending = { kind: 'chart', loading: false, html: this.chartForm({ date, time, city, error: validationError }) };
      this.renderChat(document.getElementById('app-main'));
      return;
    }
    this.chat.busy = true;
    const key = this.chat.key, view = this.view;
    const pend = this.chat.pending = { kind: 'chart', loading: true, html: this.chartForm({ date, time, city, loading: true }) };
    this.renderChat(document.getElementById('app-main'));
    try {
      const c = await api('/api/chart', {
        method: 'POST',
        body: JSON.stringify({ birth_date: date, birth_time: time.trim() || null, birth_city: cleanCity }),
      });
      if (!widAlive(key, view, pend)) { this.chat.busy = false; return; }
      this.chat.pending = { kind: 'chart', loading: false, html: this.chartHtml(c) };
      haptic('soft');
    } catch (e) {
      if (!widAlive(key, view, pend)) { this.chat.busy = false; return; }
      this.chat.pending = {
        kind: 'chart',
        loading: false,
        html: this.chartForm({ date, time, city, error: friendlyError(e, 'Не удалось построить карту прямо сейчас. Проверь соединение и попробуй ещё раз.') })
      };
      haptic('error');
    }
    this.chat.busy = false;
    this.renderChat(document.getElementById('app-main'));
  };


  app.chatAsk = function(text) {
    if (!text || !text.trim()) return;
    this.chat.messages.push({ role: 'user', text });
    this.chat.busy = true;
    this.renderChat(document.getElementById('app-main'));
    this.chatPost(text)
      .then(r => { this.chat.messages.push({ role: 'assistant', text: r.answer }); })
      .catch(e => { this.chat.messages.push({ role: 'assistant', text: '😔 ' + friendlyError(e) }); })
      .finally(() => { this.chat.busy = false; this.renderChat(document.getElementById('app-main')); });
  };

  // Шаблон-фраза: вставляется в поле ввода для редактирования (не авто-отправка).

  app.fillInput = function(text) {
    const input = document.getElementById('chat-input');
    if (!input) return;
    const value = text || '';
    this.chat.draft = value;
    input.value = value;
    input.style.height = 'auto';
    input.style.height = Math.min(input.scrollHeight, 132) + 'px';
    input.focus();
    input.setSelectionRange(input.value.length, input.value.length);
  };

  // Вопрос по натальной карте из виджета — prompt вынесен из inline-хендлера.

  app.askChart = function() {
    const q = prompt('О чём спросить карту?', 'моих отношениях');
    if (q && q.trim()) this.chatAsk('Что в моей натальной карте говорит о ' + q.trim());
  };

  /* B2 — «Сохранить в сторис»: SVG-колесо → canvas → PNG.
     Фронт-рендер без новых зависимостей; nativitySvg уже использует литеральные
     цвета (не var()), чтобы standalone-SVG в <img> не терял палитру. */

  app.downloadPng = function(dataUrl, name) {
    const a = document.createElement('a');
    a.href = dataUrl; a.download = name || 'oracle-natal-card.png';
    document.body.appendChild(a); a.click(); a.remove();
    this.toast('Картинка сохранена — добавь её в сторис ✨');
  };
  // G004 «в сторис»: готовый PNG расклада с бэка (/api/share/reading/{id}.png)

  app.downloadUrl = function(url, name) {
    const a = document.createElement('a');
    a.href = url; a.download = name || 'oracle-card.png';
    document.body.appendChild(a); a.click(); a.remove();
    this.toast('Картинка сохранена — добавь её в сторис ✨');
  };
  // G004 рефералка: скопировать ссылку приглашения

  app.shareChart = function() {
    const c = this.chart;
    if (!c || !(c.planets || []).length) { this.toast('Сначала построй карту ✨'); return; }
    const size = 560; // 2× для чёткости
    let svg = nativitySvg(c, size);
    svg = svg.replace('style="width:100%;max-width:280px;height:auto;margin:0 auto;display:block;"',
      `width="${size}" height="${size}"`);
    const blob = new Blob([svg], { type: 'image/svg+xml;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const img = new Image();
    img.onload = () => {
      const canvas = document.createElement('canvas');
      canvas.width = size; canvas.height = size;
      const ctx = canvas.getContext('2d');
      ctx.fillStyle = '#08070f'; ctx.fillRect(0, 0, size, size); // ночной фон
      ctx.drawImage(img, 0, 0, size, size);
      URL.revokeObjectURL(url);
      const png = canvas.toDataURL('image/png');
      if (navigator.share && navigator.canShare && this.me && this.me.flags && this.me.flags.share_cards) {
        fetch(png).then(r => r.blob()).then(b => {
          const f = new File([b], 'oracle-natal-card.png', { type: 'image/png' });
          navigator.share({ title: 'Моя натальная карта', files: [f] }).catch(() => this.downloadPng(png));
        }).catch(() => this.downloadPng(png));
      } else {
        this.downloadPng(png);
      }
    };
    img.onerror = () => { URL.revokeObjectURL(url); this.toast('Не удалось собрать картинку 🌙'); };
    img.src = url;
  };

  /* ═══ ФИЧА: ПРОГНОЗ / НЕБО ═══ */

  app.selectPlanet = function(i) {
    const c = this.chart;
    const p = (c && c.planets) ? c.planets[i] : null;
    if (!p) return;
    haptic('light');
    vb(15);
    const svg = document.querySelector('.nw svg');
    if (svg) {
      svg.querySelectorAll('.n-planet.active').forEach(g => g.classList.remove('active'));
      const g = svg.querySelector('.n-planet[data-p="' + i + '"]');
      if (g) g.classList.add('active');
    }
    const pl = document.getElementById('nw-plaque');
    if (pl) {
      const glyph = planetGlyph(p.name) || (SIGNS[p.sign] || '');
      pl.classList.remove('is-visible');
      pl.innerHTML = `<span class="pl-glyph">${glyph}</span><span><b>${esc(p.name)}</b> · ${esc(p.sign || '—')}${p.house ? ' · дом ' + p.house : ''}${p.retro ? ' ☍' : ''}</span>`;
      window.requestAnimationFrame(() => {
        if (pl.isConnected) pl.classList.add('is-visible');
      });
    }
  };
  // стихия-фильтр: тап подсвечивает планеты этой стихии в колесе, повторный тап — сброс

  app.filterElement = function(el) {
    haptic('light');
    vb(10);
    const c = this.chart;
    const svg = document.querySelector('.nw svg');
    if (!svg || !c || !c.planets) return;
    const chips = document.querySelectorAll('.el-chip');
    if (document.querySelector('.el-chip[data-el="' + el + '"].on')) {
      chips.forEach(ch => ch.classList.remove('on'));
      svg.querySelectorAll('.n-planet').forEach(g => g.classList.remove('el-off'));
      return;
    }
    chips.forEach(ch => ch.classList.toggle('on', ch.dataset.el === el));
    svg.querySelectorAll('.n-planet').forEach(g => {
      const idx = parseInt(g.dataset.p, 10);
      const p = c.planets[idx];
      g.classList.toggle('el-off', signElement(p && p.sign) !== el);
    });
  };

  /* ═══ ПРОФИЛЬ: данные + натальная карта + расклады + отчёты ═══ */

