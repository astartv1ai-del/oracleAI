/*
 * OracleAI payments surface.
 * The browser only requests server-created orders and opens provider links.
 * Prices, SKU, asset and entitlement are never trusted from rendered markup.
 */
(function () {
  'use strict';

  const ASSETS = [
    { code: 'TON', label: 'TON', icon: '◆', copy: 'Прямо в TON через Crypto Pay' },
    { code: 'USDT', label: 'USDT', icon: '₮', copy: 'Стабильная цена в долларах' },
    { code: 'BTC', label: 'BTC', icon: '₿', copy: 'Для оплаты в Bitcoin' },
  ];

  const money = value => {
    const number = Number(value || 0);
    return Number.isFinite(number) && number > 0 ? `$${number.toFixed(2)}` : '—';
  };

  const stars = value => `✦ ${Number(value || 0).toLocaleString('ru-RU')}`;
  const paymentState = () => app.payment || (app.payment = {
    data: null, loading: false, error: '', method: 'stars', asset: 'TON', busy: '', orders: [],
  });

  function activeAsset() {
    const state = paymentState();
    return ASSETS.find(item => item.code === state.asset) || ASSETS[0];
  }

  function methodCard(method, icon, title, copy, active) {
    return `<button class="pay-method${active ? ' is-active' : ''}" data-act="payment-method" data-method="${method}" aria-pressed="${active ? 'true' : 'false'}">
      <span class="pay-method__icon">${icon}</span><span class="pay-method__copy"><b>${title}</b><small>${copy}</small></span><span class="pay-method__check">${active ? '✓' : ''}</span>
    </button>`;
  }

  function planCard(plan, featured) {
    const price = Number(plan.price_stars || 0);
    return `<article class="pay-plan${featured ? ' pay-plan--featured' : ''}">
      ${featured ? '<span class="pay-plan__badge">Самый популярный</span>' : ''}
      <div class="pay-plan__top"><div><span class="pay-kicker">${esc(plan.code || plan.sku || 'ACCESS')}</span><h3>${esc(plan.title || 'Подписка')}</h3></div><span class="pay-plan__sigil">✦</span></div>
      <p>${esc(plan.tagline || 'Больше глубины, памяти и личного ритма.')}</p>
      <div class="pay-price"><strong>${price ? stars(price) : 'По запросу'}</strong><small>за период</small></div>
      <button class="btn btn-primary pay-cta" data-act="pay-stars" data-plan="${esc(plan.code || plan.sku || '')}" ${price ? '' : 'disabled'}>Открыть оплату Stars</button>
    </article>`;
  }

  function productCard(product, method, asset) {
    const crypto = method !== 'stars';
    const price = crypto ? money(product.price_usd || 0) : stars(product.price_stars || 0);
    const sku = esc(product.sku || '');
    const disabled = crypto ? !product.price_usd : !product.price_stars;
    return `<article class="pay-product">
      <div class="pay-product__icon">${crypto ? asset.icon : '✦'}</div>
      <div class="pay-product__body"><h3>${esc(product.title || 'Пакет')}</h3><p>${esc(product.description || 'Добавь немного запаса для важных вопросов и разборов.')}</p><span class="pay-product__meta">${crypto ? `${price} · ${asset.label}` : price}</span></div>
      <button class="pay-product__button" data-act="${crypto ? 'pay-crypto' : 'pay-stars'}" data-sku="${sku}" data-asset="${asset.code}" ${disabled ? 'disabled' : ''} aria-label="Оплатить ${esc(product.title || 'пакет')}">›</button>
    </article>`;
  }

  app.renderPayment = function (main) {
    const state = paymentState();
    const data = state.data || {};
    const method = state.method || 'stars';
    const asset = activeAsset();
    const plans = (data.plans || []).filter(plan => plan.is_active !== 0 && plan.is_public !== 0);
    const allProducts = Object.values(data.products || {}).flat();
    const crystalProducts = allProducts.filter(product => product.kind === 'crystals');
    const otherProducts = allProducts.filter(product => product.kind !== 'crystals');
    const busy = state.busy ? '<div class="pay-busy" role="status"><span class="loader-ring"></span><span>Создаю защищённый заказ…</span></div>' : '';
    const error = state.error ? `<div class="pay-alert pay-alert--error" role="alert">${esc(state.error)}<button class="btn btn-ghost" data-act="payment-retry">Повторить</button></div>` : '';
    const balance = Number(data.crystals || 0).toLocaleString('ru-RU');
    main.innerHTML = `<div class="screen pay-screen">
      <section class="pay-hero"><div class="pay-hero__orb">✦</div><div><span class="pay-kicker">ТВОЁ ПРОСТРАНСТВО</span><h1>Выбери свой ритм</h1><p>Оплата без лишних шагов. Доступ откроется только после подтверждения провайдера.</p></div></section>
      <section class="pay-balance"><span class="pay-balance__icon">✦</span><div><small>Твои Кристаллы</small><strong>${balance}</strong></div><span class="pay-balance__hint">для разовых разборов</span></section>
      <div class="pay-methods" role="tablist" aria-label="Способ оплаты">
        ${methodCard('stars', '★', 'Telegram Stars', 'Быстро внутри Telegram', method === 'stars')}
        ${methodCard('crypto', '₿', 'TON и крипта', 'TON, USDT или BTC', method === 'crypto')}
      </div>
      ${method === 'crypto' ? `<section class="pay-asset-picker"><div class="pay-section-head"><div><span class="pay-kicker">КРИПТОКОШЕЛЁК</span><h2>Чем оплатить?</h2></div><span class="pay-safe">Защищённый invoice</span></div><div class="pay-assets">${ASSETS.map(item => `<button class="pay-asset${item.code === asset.code ? ' is-active' : ''}" data-act="payment-asset" data-asset="${item.code}" aria-pressed="${item.code === asset.code ? 'true' : 'false'}"><b>${item.icon}</b><span>${item.label}</span></button>`).join('')}</div><p class="pay-note">Сумма фиксируется в USD на сервере, а Crypto Pay показывает эквивалент в выбранной монете. Seed-фраза и приватные ключи не нужны.</p></section>` : `<section class="pay-trust"><span>✓</span><p><b>Оплата Stars внутри Telegram</b><br>Никаких карт и лишних данных. Подписка и покупки активируются только после успешного платежа.</p></section>`}
      ${busy}${error}
      <section class="pay-section"><div class="pay-section-head"><div><span class="pay-kicker">ПОДПИСКА</span><h2>Больше глубины каждый день</h2></div><span class="pay-section-count">${plans.length} тарифа</span></div><div class="pay-plans">${plans.length ? plans.map((plan, index) => planCard(plan, index === 1 || (plans.length === 1))).join('') : '<div class="pay-empty">Тарифы временно недоступны.</div>'}</div></section>
      <section class="pay-section"><div class="pay-section-head"><div><span class="pay-kicker">РАЗОВЫЕ ПАКЕТЫ</span><h2>Запас для важных вопросов</h2></div></div><div class="pay-products">${(method === 'crypto' ? crystalProducts : [...crystalProducts, ...otherProducts]).slice(0, 5).map(product => productCard(product, method, asset)).join('') || '<div class="pay-empty">Пакеты скоро появятся.</div>'}</div></section>
      <section class="pay-footer-note"><span>◌</span><p>OracleAI не хранит данные карты или ключи кошелька. По вопросам оплаты можно открыть историю заказов и обратиться в поддержку.</p><button class="btn btn-ghost" data-act="payment-orders">История заказов</button></section>
    </div>`;
  };

  app.loadPayments = async function () {
    const state = paymentState();
    state.loading = true; state.error = '';
    const main = document.getElementById('app-main');
    if (main) this.renderPayment(main);
    try {
      state.data = await api('/api/shop');
    } catch (e) {
      state.error = friendlyError(e, 'Не удалось открыть оплату. Попробуй ещё раз.');
    } finally {
      state.loading = false;
      if (this.view === 'payment' && main) this.renderPayment(main);
    }
  };

  app.goPayment = function () {
    this.view = 'payment';
    this.chat.key = null;
    this.renderNav();
    this.renderPayment(document.getElementById('app-main'));
    if (!paymentState().data && !paymentState().loading) this.loadPayments();
  };

  app.selectPaymentMethod = function (method) {
    const state = paymentState();
    state.method = method === 'crypto' ? 'crypto' : 'stars';
    state.error = '';
    this.renderPayment(document.getElementById('app-main'));
  };

  app.selectPaymentAsset = function (asset) {
    const state = paymentState();
    state.asset = ASSETS.some(item => item.code === asset) ? asset : 'TON';
    this.renderPayment(document.getElementById('app-main'));
  };

  async function openProviderLink(link) {
    if (!link) throw new Error('Ссылка на оплату не создана');
    const telegram = tg && tg();
    if (telegram && typeof telegram.openLink === 'function') telegram.openLink(link);
    else window.open(link, '_blank', 'noopener,noreferrer');
  }

  app.payStars = async function (el, data) {
    const state = paymentState();
    if (state.busy) return;
    state.busy = 'stars'; state.error = '';
    this.renderPayment(document.getElementById('app-main'));
    try {
      const body = data.plan ? { plan: data.plan } : { sku: data.sku };
      const invoice = await api('/api/shop/invoice', { method: 'POST', body: JSON.stringify(body) });
      const telegram = tg && tg();
      if (telegram && typeof telegram.openInvoice === 'function') {
        telegram.openInvoice(invoice.link, status => {
          if (status === 'paid') this.toast('Оплата прошла — доступ уже открывается ✦');
          else if (status === 'failed') this.toast('Telegram не подтвердил оплату. Попробуй ещё раз.');
          state.busy = ''; this.loadPayments();
        });
      } else {
        await openProviderLink(invoice.link);
        this.toast('Счёт открыт в Telegram');
        state.busy = '';
      }
    } catch (e) {
      state.busy = ''; state.error = friendlyError(e, 'Stars сейчас недоступны. Попробуй чуть позже.');
    }
    if (this.view === 'payment') this.renderPayment(document.getElementById('app-main'));
  };

  app.payCrypto = async function (el, data) {
    const state = paymentState();
    if (state.busy) return;
    const asset = ASSETS.some(item => item.code === data.asset) ? data.asset : state.asset;
    state.busy = 'crypto'; state.error = '';
    this.renderPayment(document.getElementById('app-main'));
    try {
      const invoice = await api('/api/shop/crypto-invoice', {
        method: 'POST', body: JSON.stringify({ sku: data.sku, asset }),
      });
      await openProviderLink(invoice.link);
      this.toast(`Счёт ${invoice.asset || asset} открыт. После оплаты заказ появится в истории.`);
    } catch (e) {
      state.error = friendlyError(e, 'Крипто-оплата сейчас недоступна. Попробуй чуть позже.');
    } finally {
      state.busy = '';
      if (this.view === 'payment') this.renderPayment(document.getElementById('app-main'));
    }
  };

  app.retryPayments = function () { paymentState().data = null; this.loadPayments(); };

  app.showPaymentOrders = async function () {
    try {
      const orders = await api('/api/shop/orders');
      const rows = (orders || []).slice(0, 10).map(order => `<div class="pay-order"><span>${esc(order.title || order.sku || 'Покупка')}</span><b>${esc(order.status || 'pending')}</b></div>`).join('');
      this.showModal(`<h3>История заказов</h3><button class="m-close" data-act="modal-close">✕</button><div class="pay-orders">${rows || '<p class="pay-note">Заказов пока нет.</p>'}</div>`);
    } catch (e) { this.toast(friendlyError(e)); }
  };
}());
