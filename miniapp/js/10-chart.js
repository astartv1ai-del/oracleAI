/* chart: натальная карта — форма, построение, SVG, шаринг, планеты/стихии */
  app.featureChart = async function() {
    if (this.chat.pending && this.chat.pending.kind === 'chart') return;
    this.chat.pending = { kind: 'chart', loading: true, html: '' };
    this.renderChat(document.getElementById('app-main'));
    try {
      const c = await api('/api/chart');
      this.chat.pending = { kind: 'chart', loading: false, html: this.chartHtml(c) };
    } catch (e) {
      // карты ещё нет — даём собрать её прямо здесь (время и город)
      this.chart = null;
      this.chat.pending = { kind: 'chart', loading: false, html: this.chartForm() };
    }
    this.renderChat(document.getElementById('app-main'));
  };


  app.chartHtml = function(c) {
    this.chart = c;
    const sun = c.sun || {};
    const asc = c.ascendant || {};
    const planets = c.planets || [];
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
    return `
      <div class="w-title">🌌 Натальная карта</div>
      <div class="nw" data-act="full-chart" title="Открыть полную карту">${this.chart ? nativitySvg(this.chart, 210) : ''}
        <div class="nw-plaque" id="nw-plaque" hidden></div>
      </div>
      <div style="text-align:center;color:var(--text-faint);font-size:10.5px;margin-bottom:6px">Тапни планету — она расскажет о себе · тап по колесу — полный разбор ↻</div>
      ${elLegend}
      ${accentChips}
      <div style="font-family:var(--font-serif);color:var(--gold-bright);font-size:13px;margin-bottom:8px">Солнце в ${esc(sun.sign || '—')} · Асцендент ${esc(asc.sign || '—')}</div>
      ${legend}
      <div>${lines || '<div style="color:var(--text-faint);font-size:12.5px">Планеты ещё не рассчитаны</div>'}</div>
      <div style="color:var(--text-faint);font-size:11.5px;margin:10px 0">✓ Сохранена в твоём профиле — всегда под рукой.</div>
      <div style="display:flex;gap:8px;margin-top:6px">
        <button class="btn btn-primary" style="flex:1" data-act="ask-chart">Спросить про карту</button>
        <button class="btn btn-ghost" data-act="share-chart" title="Сохранить картинку для сторис">📸</button>
        <button class="btn btn-ghost" data-act="go" data-goto="profile">В профиль</button>
      </div>`;
  };


  app.chartForm = function() {
    const me = this.me || {};
    return `
      <div class="w-title">🌌 Построить натальную карту</div>
      <div style="color:var(--text-dim);font-size:12.5px;margin-bottom:10px">
        Дата рождения: <b style="color:var(--text)">${esc(me.birth_date || '—')}</b>. Уточни время и город — и я рассчитаю карту прямо здесь.
      </div>
      <input class="ipt" id="ch-time" placeholder="Время рождения · 14:30 (если не знаешь — пусто)" style="margin-bottom:8px"/>
      <input class="ipt" id="ch-city" placeholder="Город рождения · Москва" style="margin-bottom:8px"/>
      <button class="btn btn-primary" data-act="build">Рассчитать карту ✨</button>`;
  };


  app.doBuildChart = async function() {
    const time = (document.getElementById('ch-time') || {}).value || '';
    const city = (document.getElementById('ch-city') || {}).value || '';
    this.chat.busy = true;
    this.chat.pending = { kind: 'chart', loading: true, html: '' };
    this.renderChat(document.getElementById('app-main'));
    try {
      const c = await api('/api/chart', {
        method: 'POST',
        body: JSON.stringify({ birth_time: time.trim() || null, birth_city: city.trim() || null }),
      });
      this.chat.pending = { kind: 'chart', loading: false, html: this.chartHtml(c) };
    } catch (e) {
      this.chat.pending = { kind: 'chart', loading: false, html: '<div style="color:#ff9e9e;font-size:13px">😔 ' + esc(e.message) + '</div>' };
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
      .catch(e => { this.chat.messages.push({ role: 'assistant', text: '😔 ' + e.message }); })
      .finally(() => { this.chat.busy = false; this.renderChat(document.getElementById('app-main')); });
  };

  // Шаблон-фраза: вставляется в поле ввода для редактирования (не авто-отправка).

  app.fillInput = function(text) {
    const input = document.getElementById('chat-input');
    if (!input) return;
    input.value = text || '';
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
    if (navigator.vibrate) { try { navigator.vibrate(15); } catch (e) {} }
    const svg = document.querySelector('.nw svg');
    if (svg) {
      svg.querySelectorAll('.n-planet.active').forEach(g => g.classList.remove('active'));
      const g = svg.querySelector('.n-planet[data-p="' + i + '"]');
      if (g) g.classList.add('active');
    }
    const pl = document.getElementById('nw-plaque');
    if (pl) {
      const glyph = planetGlyph(p.name) || (SIGNS[p.sign] || '');
      pl.innerHTML = `<span class="pl-glyph">${glyph}</span><span><b>${esc(p.name)}</b> · ${esc(p.sign || '—')}${p.house ? ' · дом ' + p.house : ''}${p.retro ? ' ☍' : ''}</span>`;
      pl.hidden = false;
    }
  };
  // стихия-фильтр: тап подсвечивает планеты этой стихии в колесе, повторный тап — сброс

  app.filterElement = function(el) {
    haptic('light');
    if (navigator.vibrate) { try { navigator.vibrate(10); } catch (e) {} }
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

