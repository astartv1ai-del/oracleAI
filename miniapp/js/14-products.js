/* structured chart products: synastry and transits */
(function () {
  'use strict';

  const labelPrecision = value => value === 'instant' ? 'точный момент' :
    value === 'day' ? 'дневной срез' : value === 'exact' ? 'точная карта' : value || 'ограниченная точность';

  const pointRow = point => `<div class="product-point"><span>${esc(point.label || point.name || '')}</span>` +
    `<span>${esc(point.sign || '')} ${point.deg == null ? '' : esc(String(point.deg)) + '°'}</span></div>`;

  const aspectRow = item => `<div class="product-aspect"><strong>${esc(item.first_label || item.p1_label || '')}</strong>` +
    ` <span class="product-aspect__glyph">${esc(item.glyph || '')}</span> ` +
    `<strong>${esc(item.second_label || item.p2_label || '')}</strong>` +
    `<span class="product-muted"> · орб ${esc(String(item.orb_deg ?? item.orb ?? '—'))}°</span></div>`;

  app.synastrySelectHtml = function (partners) {
    const saved = partners && partners.length ? `<div class="product-partners">${partners.map(p => {
      const ready = Boolean(p.synastry_ready);
      return `<button class="product-partner${ready ? '' : ' is-disabled'}" data-act="synastry-load" data-id="${esc(String(p.id))}" ${ready ? '' : 'disabled'}>
        <span class="product-partner__name">${esc(p.name || 'Партнёр')}</span>
        <span class="product-muted">${esc(p.birth_date || '')}${p.birth_city ? ' · ' + esc(p.birth_city) : ''}</span>
        <span class="product-muted">${ready ? 'Точная карта готова' : 'Нужны время и город рождения'}</span>
      </button>`;
    }).join('')}</div>` : '<p class="product-muted">Сохранённых партнёров пока нет.</p>';
    return `<section class="chart-product" aria-label="Выбор партнёра для синастрии">
      <div class="w-title">Полная синастрия</div>
      <p class="product-muted">Выбери партнёра с точной картой — я покажу положения двух карт и реальные межпланетные аспекты.</p>
      ${saved}
      <div class="product-subtitle product-subtitle--spaced">Добавить точную карту партнёра</div>
      <div class="product-form-grid">
        <input class="ipt" id="sp-name" placeholder="Имя" autocomplete="name">
        <input class="ipt" id="sp-date" type="date" aria-label="Дата рождения">
        <input class="ipt" id="sp-time" type="time" aria-label="Время рождения">
        <input class="ipt" id="sp-city" placeholder="Город рождения" autocomplete="address-level2">
      </div>
      <p class="product-muted">Время и город нужны, чтобы корректно проверить точность карты. Эти данные не попадают в URL результата.</p>
      <button class="btn btn-primary" data-act="synastry-create">Сохранить и рассчитать</button>
    </section>`;
  };

  app.synastryProductHtml = function (data) {
    const person = data.person || {}, partner = data.partner || {};
    const aspects = data.aspects || [];
    return `<section class="chart-product" data-result-anchor role="status" aria-label="Полная синастрия">
      <div class="w-title">${esc(person.label || 'Я')} × ${esc(partner.label || 'Партнёр')}</div>
      <div class="product-meta">${esc(labelPrecision(data.precision))} · ${esc(String(aspects.length))} мажорных аспектов</div>
      <div class="product-columns"><div><div class="product-subtitle">Моя карта</div>${(person.planets || []).map(pointRow).join('')}</div>
      <div><div class="product-subtitle">${esc(partner.label || 'Партнёр')}</div>${(partner.planets || []).map(pointRow).join('')}</div></div>
      <div class="product-subtitle product-subtitle--spaced">Аспекты между картами</div>
      <div class="product-aspects">${aspects.length ? aspects.slice(0, 10).map(aspectRow).join('') : '<p class="product-muted">Мажорных аспектов в выбранной политике орбов не найдено.</p>'}</div>
      <p class="product-muted">${(data.limitations || []).map(esc).join(' ')}</p>
      <button class="btn btn-ghost" data-act="chat-fn" data-chat="oracle" data-fn="featureSynastry">Выбрать другого партнёра</button>
    </section>`;
  };

  app.transitProductHtml = function (data) {
    const planets = data.transit_planets || [], aspects = data.aspects_to_natal || [];
    return `<section class="chart-product" data-result-anchor role="status" aria-label="Транзиты к натальной карте">
      <div class="w-title">Транзиты к моей карте</div>
      <div class="product-meta">${esc(data.as_of || '')} · ${esc(labelPrecision(data.precision))}</div>
      <div class="product-subtitle">Положения планет</div>
      <div class="product-points">${planets.map(pointRow).join('')}</div>
      <div class="product-subtitle product-subtitle--spaced">Аспекты к натальным планетам</div>
      <div class="product-aspects">${aspects.length ? aspects.slice(0, 10).map(aspectRow).join('') : '<p class="product-muted">На выбранном срезе мажорных аспектов не найдено.</p>'}</div>
      <p class="product-muted">${(data.limitations || []).map(esc).join(' ')}</p>
      <div class="product-date-row"><label for="transit-date">Другой день</label><input id="transit-date" type="date" value="${esc(data.as_of || '')}"><button class="btn btn-primary" data-act="transit-load">Рассчитать</button></div>
    </section>`;
  };

  app.featureSynastry = async function () {
    if (this.chat.pending && ['synastry-select', 'synastry-loading'].includes(this.chat.pending.kind)) return;
    const key = this.chat.key, view = this.view;
    const pending = this.chat.pending = { kind: 'synastry-select', loading: true, partners: [] };
    this.renderChat(document.getElementById('app-main'));
    try {
      const partners = await api('/api/partners');
      if (!widAlive(key, view, pending)) return;
      this.chat.pending = { kind: 'synastry-select', loading: false, partners: partners || [] };
    } catch (e) {
      if (!widAlive(key, view, pending)) return;
      this.chat.pending = { kind: 'synastry-select', loading: false, partners: [], error: friendlyError(e) };
    }
    this.renderChat(document.getElementById('app-main'));
  };

  app.createSynastryPartner = async function () {
    const name = document.getElementById('sp-name')?.value.trim();
    const birthDate = document.getElementById('sp-date')?.value;
    const birthTime = document.getElementById('sp-time')?.value;
    const birthCity = document.getElementById('sp-city')?.value.trim();
    if (!name || !birthDate || !birthTime || !birthCity) {
      this.toast('Для точной синастрии нужны имя, дата, время и город рождения');
      return;
    }
    try {
      const created = await api('/api/partners', { method: 'POST', body: JSON.stringify({
        name, birth_date: birthDate, birth_time: birthTime, birth_city: birthCity,
      }) });
      if (created && created.id) await this.loadSynastry(created.id);
    } catch (e) {
      this.toast(friendlyError(e));
    }
  };

  app.loadSynastry = async function (partnerId) {
    const key = this.chat.key, view = this.view;
    const pending = this.chat.pending = { kind: 'synastry-loading', loading: true, partners: [] };
    this.renderChat(document.getElementById('app-main'));
    try {
      const data = await api('/api/synastry', { method: 'POST', body: JSON.stringify({ partner_id: Number(partnerId) }) });
      if (!widAlive(key, view, pending)) return;
      this.chat.pending = { kind: 'synastry-result', loading: false, data };
    } catch (e) {
      if (!widAlive(key, view, pending)) return;
      this.chat.pending = { kind: 'synastry-select', loading: false, partners: [], error: friendlyError(e) };
    }
    this.renderChat(document.getElementById('app-main'));
  };

  app.featureTransits = async function () {
    const dateValue = new Date().toISOString().slice(0, 10);
    return this.loadTransits(dateValue);
  };

  app.loadTransits = async function (asOf) {
    if (!/^\d{4}-\d{2}-\d{2}$/.test(asOf || '')) asOf = new Date().toISOString().slice(0, 10);
    const key = this.chat.key, view = this.view;
    const pending = this.chat.pending = { kind: 'transits-loading', loading: true };
    this.renderChat(document.getElementById('app-main'));
    try {
      const data = await api('/api/transits', { method: 'POST', body: JSON.stringify({ as_of: asOf }) });
      if (!widAlive(key, view, pending)) return;
      this.chat.pending = { kind: 'transits-result', loading: false, data };
    } catch (e) {
      if (!widAlive(key, view, pending)) return;
      this.chat.pending = { kind: 'transits-result', loading: false, data: null, error: friendlyError(e) };
    }
    this.renderChat(document.getElementById('app-main'));
  };
}());
