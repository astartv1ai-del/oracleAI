/*
 * OracleAI payments surface.
 * The browser only requests server-created orders and opens provider links.
 * Prices, SKU, asset and entitlement are never trusted from rendered markup.
 */
(function () {
  'use strict';

  const ASSETS = [
    { code: 'TON', label: 'TON', icon: '◆' },
    { code: 'USDT', label: 'USDT', icon: '₮' },
    { code: 'BTC', label: 'BTC', icon: '₿' },
  ];

  const PAYMENT_I18N = {
    ru: {
      popular: 'Самый популярный', subscription: 'Подписка', period: 'за период',
      openStars: 'Открыть оплату Stars', unavailable: 'По запросу',
      createOrder: 'Создаю защищённый заказ…', space: 'ТВОЁ ПРОСТРАНСТВО',
      chooseRhythm: 'Выбери свой ритм', heroCopy: 'Оплата без лишних шагов. Доступ откроется только после подтверждения провайдера.',
      crystals: 'Твои Кристаллы', crystalHint: 'для разовых разборов', paymentMethod: 'Способ оплаты',
      starsTitle: 'Telegram Stars', starsCopy: 'Быстро внутри Telegram', cryptoTitle: 'TON и крипта', cryptoCopy: 'TON, USDT или BTC',
      cryptoWallet: 'КРИПТОКОШЕЛЁК', payWith: 'Чем оплатить?', protectedInvoice: 'Защищённый invoice',
      cryptoNote: 'Сумма фиксируется в USD на сервере, а Crypto Pay показывает эквивалент в выбранной монете. Seed-фраза и приватные ключи не нужны.',
      starsTrust: 'Оплата Stars внутри Telegram', starsTrustCopy: 'Никаких карт и лишних данных. Подписка и покупки активируются только после успешного платежа.',
      plans: 'ПОДПИСКА', plansTitle: 'Больше глубины каждый день', planCount: '{count} тарифа', plansEmpty: 'Тарифы временно недоступны.',
      products: 'РАЗОВЫЕ ПАКЕТЫ', productsTitle: 'Запас для важных вопросов', productsEmpty: 'Пакеты скоро появятся.',
      footer: 'OracleAI не хранит данные карты или ключи кошелька. По вопросам оплаты можно открыть историю заказов и обратиться в поддержку.',
      orderHistory: 'История заказов', retry: 'Повторить', payProduct: 'Оплатить {title}',
      loadingFailed: 'Не удалось открыть оплату. Попробуй ещё раз.', starsUnavailable: 'Stars сейчас недоступны. Попробуй чуть позже.',
      cryptoUnavailable: 'Крипто-оплата сейчас недоступна. Попробуй чуть позже.',
      paymentPassed: 'Оплата прошла — доступ уже открывается ✦', paymentFailed: 'Telegram не подтвердил оплату. Попробуй ещё раз.',
      invoiceOpened: 'Счёт открыт в Telegram', cryptoInvoiceOpened: 'Счёт {asset} открыт. После оплаты заказ появится в истории.',
      invoiceMissing: 'Ссылка на оплату не создана', ordersTitle: 'История заказов', noOrders: 'Заказов пока нет.', purchase: 'Покупка', pending: 'Ожидает оплаты', paid: 'Оплачен', failed: 'Не подтверждён', expired: 'Истёк',
    },
    en: {
      popular: 'Most popular', subscription: 'Subscription', period: 'per period', openStars: 'Open Stars checkout', unavailable: 'On request',
      createOrder: 'Creating a protected order…', space: 'YOUR SPACE', chooseRhythm: 'Choose your rhythm',
      heroCopy: 'Payment without extra steps. Access opens only after provider confirmation.', crystals: 'Your Crystals', crystalHint: 'for one-off readings', paymentMethod: 'Payment method',
      starsTitle: 'Telegram Stars', starsCopy: 'Fast inside Telegram', cryptoTitle: 'TON and crypto', cryptoCopy: 'TON, USDT or BTC',
      cryptoWallet: 'CRYPTO WALLET', payWith: 'Choose an asset', protectedInvoice: 'Protected invoice',
      cryptoNote: 'The server fixes the amount in USD, while Crypto Pay shows the equivalent in the selected coin. No seed phrase or private key is needed.',
      starsTrust: 'Pay with Stars inside Telegram', starsTrustCopy: 'No cards or extra data. Your subscription or purchase activates only after successful payment.',
      plans: 'SUBSCRIPTION', plansTitle: 'More depth every day', planCount: '{count} plans', plansEmpty: 'Plans are temporarily unavailable.',
      products: 'ONE-OFF PACKAGES', productsTitle: 'A reserve for important questions', productsEmpty: 'Packages are coming soon.',
      footer: 'OracleAI does not store card data or wallet keys. Open order history or contact support if you have a payment question.',
      orderHistory: 'Order history', retry: 'Retry', payProduct: 'Pay for {title}',
      loadingFailed: 'Payment could not be opened. Please try again.', starsUnavailable: 'Stars are unavailable right now. Please try again later.',
      cryptoUnavailable: 'Crypto payment is unavailable right now. Please try again later.',
      paymentPassed: 'Payment confirmed — access is opening ✦', paymentFailed: 'Telegram did not confirm the payment. Please try again.',
      invoiceOpened: 'Invoice opened in Telegram', cryptoInvoiceOpened: '{asset} invoice opened. The order will appear in history after payment.',
      invoiceMissing: 'Payment link was not created', ordersTitle: 'Order history', noOrders: 'No orders yet.', purchase: 'Purchase', pending: 'Pending', paid: 'Paid', failed: 'Not confirmed', expired: 'Expired',
    },
  };
  const pt = key => (PAYMENT_I18N[oracleLang()] || PAYMENT_I18N.ru)[key] || key;
  const pf = (key, values = {}) => Object.entries(values).reduce(
    (text, [name, value]) => text.replaceAll(`{${name}}`, String(value)), pt(key));
  const orderStatus = status => pt({ paid: 'paid', failed: 'failed', expired: 'expired' }[status] || 'pending');

  const money = value => {
    const number = Number(value || 0);
    return Number.isFinite(number) && number > 0 ? `$${number.toFixed(2)}` : '—';
  };

  const stars = value => `✦ ${Number(value || 0).toLocaleString(oracleLang() === 'en' ? 'en-US' : 'ru-RU')}`;
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
      ${featured ? `<span class="pay-plan__badge">${pt('popular')}</span>` : ''}
      <div class="pay-plan__top"><div><span class="pay-kicker">${esc(plan.code || plan.sku || 'ACCESS')}</span><h3>${esc(plan.title || pt('subscription'))}</h3></div><span class="pay-plan__sigil">✦</span></div>
      <p>${esc(plan.tagline || (oracleLang() === 'en' ? 'More depth, memory and a personal rhythm.' : 'Больше глубины, памяти и личного ритма.'))}</p>
      <div class="pay-price"><strong>${price ? stars(price) : pt('unavailable')}</strong><small>${pt('period')}</small></div>
      <button class="btn btn-primary pay-cta" data-act="pay-stars" data-plan="${esc(plan.code || plan.sku || '')}" ${price ? '' : 'disabled'}>${pt('openStars')}</button>
    </article>`;
  }

  function productCard(product, method, asset) {
    const crypto = method !== 'stars';
    const price = crypto ? money(product.price_usd || 0) : stars(product.price_stars || 0);
    const sku = esc(product.sku || '');
    const disabled = crypto ? !product.price_usd : !product.price_stars;
    return `<article class="pay-product">
      <div class="pay-product__icon">${crypto ? asset.icon : '✦'}</div>
      <div class="pay-product__body"><h3>${esc(product.title || (oracleLang() === 'en' ? 'Package' : 'Пакет'))}</h3><p>${esc(product.description || (oracleLang() === 'en' ? 'Add a little reserve for important questions and readings.' : 'Добавь немного запаса для важных вопросов и разборов.'))}</p><span class="pay-product__meta">${crypto ? `${price} · ${asset.label}` : price}</span></div>
      <button class="pay-product__button" data-act="${crypto ? 'pay-crypto' : 'pay-stars'}" data-sku="${sku}" data-asset="${asset.code}" ${disabled ? 'disabled' : ''} aria-label="${esc(pf('payProduct', { title: product.title || (oracleLang() === 'en' ? 'package' : 'пакет') }))}">›</button>
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
    const busy = state.busy ? `<div class="pay-busy" role="status"><span class="loader-ring"></span><span>${pt('createOrder')}</span></div>` : '';
    const error = state.error ? `<div class="pay-alert pay-alert--error" role="alert">${esc(state.error)}<button class="btn btn-ghost" data-act="payment-retry">${pt('retry')}</button></div>` : '';
    const balance = Number(data.crystals || 0).toLocaleString(oracleLang() === 'en' ? 'en-US' : 'ru-RU');
    main.innerHTML = `<div class="screen pay-screen">
      <section class="pay-hero"><div class="pay-hero__orb">✦</div><div><span class="pay-kicker">${pt('space')}</span><h1>${pt('chooseRhythm')}</h1><p>${pt('heroCopy')}</p></div></section>
      <section class="pay-balance"><span class="pay-balance__icon">✦</span><div><small>${pt('crystals')}</small><strong>${balance}</strong></div><span class="pay-balance__hint">${pt('crystalHint')}</span></section>
      <div class="pay-methods" role="tablist" aria-label="${pt('paymentMethod')}">
        ${methodCard('stars', '★', pt('starsTitle'), pt('starsCopy'), method === 'stars')}
        ${methodCard('crypto', '₿', pt('cryptoTitle'), pt('cryptoCopy'), method === 'crypto')}
      </div>
      ${method === 'crypto' ? `<section class="pay-asset-picker"><div class="pay-section-head"><div><span class="pay-kicker">${pt('cryptoWallet')}</span><h2>${pt('payWith')}</h2></div><span class="pay-safe">${pt('protectedInvoice')}</span></div><div class="pay-assets">${ASSETS.map(item => `<button class="pay-asset${item.code === asset.code ? ' is-active' : ''}" data-act="payment-asset" data-asset="${item.code}" aria-pressed="${item.code === asset.code ? 'true' : 'false'}" aria-label="${esc(item.label)}"><b>${item.icon}</b><span>${item.label}</span></button>`).join('')}</div><p class="pay-note">${pt('cryptoNote')}</p></section>` : `<section class="pay-trust"><span>✓</span><p><b>${pt('starsTrust')}</b><br>${pt('starsTrustCopy')}</p></section>`}
      ${busy}${error}
      <section class="pay-section"><div class="pay-section-head"><div><span class="pay-kicker">${pt('plans')}</span><h2>${pt('plansTitle')}</h2></div><span class="pay-section-count">${pf('planCount', { count: plans.length })}</span></div><div class="pay-plans">${plans.length ? plans.map((plan, index) => planCard(plan, index === 1 || (plans.length === 1))).join('') : `<div class="pay-empty">${pt('plansEmpty')}</div>`}</div></section>
      <section class="pay-section"><div class="pay-section-head"><div><span class="pay-kicker">${pt('products')}</span><h2>${pt('productsTitle')}</h2></div></div><div class="pay-products">${(method === 'crypto' ? crystalProducts : [...crystalProducts, ...otherProducts]).slice(0, 5).map(product => productCard(product, method, asset)).join('') || `<div class="pay-empty">${pt('productsEmpty')}</div>`}</div></section>
      <section class="pay-footer-note"><span>◌</span><p>${pt('footer')}</p><button class="btn btn-ghost" data-act="payment-orders">${pt('orderHistory')}</button></section>
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
      state.error = friendlyError(e, pt('loadingFailed'));
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
    if (!link) throw new Error(pt('invoiceMissing'));
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
          if (status === 'paid') this.toast(pt('paymentPassed'));
          else if (status === 'failed') this.toast(pt('paymentFailed'));
          state.busy = ''; this.loadPayments();
        });
      } else {
        await openProviderLink(invoice.link);
        this.toast(pt('invoiceOpened'));
        state.busy = '';
      }
    } catch (e) {
      state.busy = ''; state.error = friendlyError(e, pt('starsUnavailable'));
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
      this.toast(pf('cryptoInvoiceOpened', { asset: invoice.asset || asset }));
    } catch (e) {
      state.error = friendlyError(e, pt('cryptoUnavailable'));
    } finally {
      state.busy = '';
      if (this.view === 'payment') this.renderPayment(document.getElementById('app-main'));
    }
  };

  app.retryPayments = function () { paymentState().data = null; this.loadPayments(); };

  app.showPaymentOrders = async function () {
    this.showModal(`<h3>История оплат</h3><button class="m-close" data-act="modal-close" aria-label="Закрыть">✕</button><div id="payment-history-body" class="pay-orders"><div class="loader-ring"></div></div>`);
    await this.loadPaymentHistory();
  };

  app.loadPaymentHistory = async function () {
    const body = document.getElementById('payment-history-body');
    if (!body) return;
    try {
      const orders = await api('/api/shop/payment-history');
      const labels = { created: 'Заказ создан', paid: 'Платёж подтверждён', entitlement: 'Доступ или покупка выданы', refunded: 'Оформлен возврат' };
      const rows = (orders || []).slice(0, 10).map(order => `<article class="pay-order pay-order--timeline"><div class="pay-order__head"><strong>${esc(order.title || order.sku || pt('purchase'))}</strong><span>${esc(orderStatus(order.status))}</span></div><div class="pay-order__meta">${order.amount_stars ? stars(order.amount_stars) : '—'} · ${esc(order.provider || 'ожидается')}</div><ol class="pay-timeline">${(order.stages || []).map(stage => `<li class="pay-timeline__item is-${esc(stage.state)}"><span class="pay-timeline__dot" aria-hidden="true"></span><span><b>${esc(labels[stage.key] || stage.key)}</b><small>${stage.at ? esc(new Date(stage.at).toLocaleString(oracleLang() === 'en' ? 'en-US' : 'ru-RU')) : 'Ожидается подтверждение сервера'}</small></span></li>`).join('')}</ol></article>`).join('');
      body.innerHTML = rows || `<p class="pay-note">${pt('noOrders')}</p>`;
      if (rows) body.insertAdjacentHTML('afterbegin', `<p class="pay-note">${oracleLang() === 'en' ? 'Status is updated by the server. Closing this window does not change the payment.' : 'Статус обновляется с сервера. Закрытие окна не меняет платёж.'}</p>`);
    } catch (e) { body.innerHTML = `<p class="pay-note">${esc(friendlyError(e, oracleLang() === 'en' ? 'Order history is temporarily unavailable.' : 'История оплат временно недоступна.'))}</p><button class="btn btn-ghost" data-act="payment-history-refresh">${pt('retry')}</button>`; }
  };
}());
