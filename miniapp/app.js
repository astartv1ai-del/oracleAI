/* ══════ Оракул · Mini App ══════
   Шесть экранов: Сегодня, Чаты с агентами, Таро, Карта, Дневник, Профиль.

   Без сборки и фреймворка намеренно: приложение отдаёт тот же процесс, что и API,
   поэтому нет шага сборки, нет CDN и нет расхождения версий. Все правила
   (лимиты, цены, доступы) считает сервер — клиент только показывает.            */

const tg = window.Telegram?.WebApp;
tg?.ready();
tg?.expand();
tg?.setHeaderColor?.('#0b0722');
tg?.setBackgroundColor?.('#0b0722');
tg?.disableVerticalSwipes?.();      // свайп вниз не закрывает окно посреди расклада

/* Уважаем системную настройку «меньше движения» */
const CALM = matchMedia('(prefers-reduced-motion: reduce)').matches;
if (CALM) document.documentElement.classList.add('calm');

const haptic = (kind = 'light') => tg?.HapticFeedback?.impactOccurred(kind);
const notify = (kind = 'success') => tg?.HapticFeedback?.notificationOccurred(kind);
const selectHaptic = () => tg?.HapticFeedback?.selectionChanged();

const qs = new URLSearchParams(location.search);
const DEV_USER = qs.get('dev_user');

/* ── состояние ── */
const S = {
  me: null,
  agents: [],
  agent: 'oracle',
  spreads: [],
  spread: null,
  chart: null,
  shopTab: 'plans',
  shop: null,
  diaryMood: null,
  drawn: null,
  shuffled: false,
  compat: null,
  practices: null,
  practiceCat: null,
  shareCards: false,
};

/* ══════ сеть ══════ */
const API_MESSAGES = {
  401: 'Открой приложение из бота — нужна подпись Telegram 🌙',
  402: 'Доступ завершён 🌙 Продли его в разделе «Я».',
  403: 'Доступ приостановлен. Напиши в поддержку 🌙',
  404: 'Открой бота и нажми /start — я ещё не знаю тебя ✨',
  429: 'Слишком часто или вопросы исчерпаны. Звёзды ждут рассвета 🌘',
  503: 'Оплата сейчас недоступна, попробуй чуть позже 🌙',
};

class ApiError extends Error {
  constructor(status, detail) {
    super(detail || API_MESSAGES[status] || 'Связь со звёздами прервалась…');
    this.status = status;
  }
}

async function api(path, opts = {}) {
  const url = new URL(path, location.origin);
  if (DEV_USER) url.searchParams.set('dev_user', DEV_USER);
  const res = await fetch(url, {
    ...opts,
    headers: {
      'Content-Type': 'application/json',
      'X-Init-Data': tg?.initData || '',
      ...(opts.headers || {}),
    },
  });
  if (!res.ok) {
    let detail = null;
    try { detail = (await res.json()).detail; } catch { /* не JSON */ }
    throw new ApiError(res.status, detail);
  }
  return res.json();
}

const post = (p, body) => api(p, { method: 'POST', body: JSON.stringify(body ?? {}) });
const del = (p) => api(p, { method: 'DELETE' });

/* ── мелкие помощники ── */
const $ = (id) => document.getElementById(id);
const esc = (s) => { const d = document.createElement('div'); d.textContent = s ?? ''; return d.innerHTML; };
const plural = (n, one, few, many) => {
  const mod10 = n % 10, mod100 = n % 100;
  if (mod10 === 1 && mod100 !== 11) return one;
  if (mod10 >= 2 && mod10 <= 4 && (mod100 < 10 || mod100 >= 20)) return few;
  return many;
};
const dateRu = (iso) => iso ? new Date(iso).toLocaleDateString('ru-RU') : '';

let toastTimer;
function toast(text) {
  const el = $('toast');
  el.textContent = text;
  el.classList.add('show');
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => el.classList.remove('show'), 3600);
}

function reportError(e) {
  toast(e instanceof ApiError ? e.message : 'Связь со звёздами прервалась…');
  notify('error');
}

/* ── модальный лист для длинных текстов ── */
function openSheet(title, text) {
  $('sheet-content').innerHTML =
    `<div class="sheet-title">${esc(title)}</div>
     <div class="sheet-text">${esc(text)}</div>`;
  $('sheet').classList.remove('hidden');
}
document.querySelectorAll('[data-sheet-close]').forEach((el) =>
  el.addEventListener('click', () => $('sheet').classList.add('hidden')));

/* ══════ звёздное небо ══════ */
(function starfield() {
  const c = $('stars');
  const ctx = c.getContext('2d');
  let stars = [];
  function resize() {
    c.width = innerWidth; c.height = innerHeight;
    stars = Array.from({ length: 120 }, () => ({
      x: Math.random() * c.width,
      y: Math.random() * c.height,
      r: Math.random() * 1.3 + .2,
      tw: Math.random() * Math.PI * 2,
      sp: .003 + Math.random() * .012,
    }));
  }
  resize();
  addEventListener('resize', resize);

  function paint(twinkle) {
    ctx.clearRect(0, 0, c.width, c.height);
    for (const s of stars) {
      if (twinkle) s.tw += s.sp * 16;
      const a = .25 + Math.abs(Math.sin(s.tw)) * .75;
      ctx.beginPath();
      ctx.arc(s.x, s.y, s.r, 0, 7);
      ctx.fillStyle = `rgba(232,215,255,${a})`;
      ctx.fill();
    }
  }

  if (CALM) { paint(false); return; }
  let running = true;
  function loop() {
    if (!running) return;
    paint(true);
    requestAnimationFrame(loop);
  }
  loop();
  // свёрнутое окно не должно жечь батарею
  document.addEventListener('visibilitychange', () => {
    if (document.hidden) { running = false; return; }
    if (!running) { running = true; requestAnimationFrame(loop); }
  });
})();

/* ══════ навигация ══════ */
const LOADED = new Set();
const TAB_LOADERS = {
  chats: loadAgents,
  tarot: loadSpreads,
  chart: loadChart,
  practices: loadPractices,
  diary: loadDiary,
  profile: loadProfile,
};

function switchTab(name) {
  document.querySelectorAll('.nav-btn').forEach((b) =>
    b.classList.toggle('active', b.dataset.tab === name));
  document.querySelectorAll('.tab').forEach((t) => t.classList.remove('active'));
  $('tab-' + name).classList.add('active');
  if (name === 'today') tg?.BackButton?.hide(); else tg?.BackButton?.show();
  window.scrollTo({ top: 0, behavior: 'smooth' });

  // экраны грузим по первому открытию: незачем тянуть всё сразу
  if (!LOADED.has(name) && TAB_LOADERS[name]) {
    LOADED.add(name);
    TAB_LOADERS[name]().catch(reportError);
  }
}

document.querySelectorAll('.nav-btn').forEach((btn) =>
  btn.addEventListener('click', () => { switchTab(btn.dataset.tab); haptic('light'); }));
document.querySelectorAll('[data-goto]').forEach((btn) =>
  btn.addEventListener('click', () => { switchTab(btn.dataset.goto); haptic('light'); }));
tg?.BackButton?.onClick(() => {
  if (!$('chat-thread-view').classList.contains('hidden')) { showAgentList(); return; }
  switchTab('today');
});

/* ══════ ЭКРАН: СЕГОДНЯ ══════ */
async function loadMe() {
  S.me = await api('/api/me');
  const hour = new Date().getHours();
  const hello = hour < 5 ? 'Тихой ночи' : hour < 12 ? 'Доброе утро'
    : hour < 18 ? 'Светлого дня' : 'Мягкого вечера';
  $('greeting').textContent = `${hello}, ${S.me.name} ✨`;
  if (S.me.sun) {
    $('sub-line').textContent =
      `${S.me.sun.symbol} Солнце в ${S.me.sun.sign} · стихия ${S.me.sun.element}`;
  }
  renderLimits();
  renderProfileHead();
  return S.me;
}

function renderLimits() {
  const a = S.me.allowance;
  $('limit-label').textContent = a.period === 'week'
    ? 'Вопросы Оракулу на этой неделе' : 'Вопросы Оракулу сегодня';

  const flames = $('flames');
  flames.innerHTML = '';
  const total = Math.min(a.limit || 0, 10);
  for (let i = 0; i < total; i++) {
    const s = document.createElement('span');
    s.textContent = '🔥';
    if (i >= a.left) s.className = 'used';
    flames.appendChild(s);
  }
  if (!total) flames.textContent = '🌘';

  const notes = [];
  if (a.extra_questions) notes.push(`куплено сверх лимита: ${a.extra_questions}`);
  if (!a.limit && !a.extra_questions) {
    notes.push(a.can_ask ? `можно открыть за ✦${a.emergency_cost}`
      : 'доступ завершён — продли в разделе «Я»');
  }
  $('limit-note').textContent = notes.join(' · ');
}

async function loadToday() {
  try {
    const t = await api('/api/today');
    $('forecast').textContent = t.forecast;
    $('cod-emoji').textContent = t.card.emoji;
    $('cod-name').textContent = t.card.name;
    $('cod-meaning').textContent = t.card.meaning;
    if (t.moon) {
      $('moon-line').innerHTML =
        `<span class="m-emoji">${esc(t.moon.emoji)}</span>
         <span>${esc(t.moon.name)}, ${esc(String(t.moon.day))}-й лунный день —
         ${esc(t.moon.advice)}</span>`;
    }
  } catch (e) {
    // молчать нельзя: клиентка должна понимать, почему прогноза нет
    $('forecast').textContent = e instanceof ApiError ? e.message
      : 'Небо сейчас затянуто — загляни чуть позже 🌙';
  }
  loadMoonWeek();
  loadHoroscope();
  initShare();
}

async function loadHoroscope() {
  try {
    const h = await api('/api/horoscope');
    $('horoscope-text').textContent = h.text;
    $('horoscope-card').querySelector('.label').textContent =
      `Гороскоп · ${h.symbol} ${h.sign}`;
    $('horoscope-card').classList.remove('hidden');
  } catch { /* не критично для экрана */ }
}

/* Картинки для сторис: рисует сервер, клиент только открывает готовый PNG.
   Кнопку показываем, только если рисовать есть чем — иначе она обманывает. */
async function initShare() {
  try {
    const state = await api('/api/share/enabled');
    S.shareCards = Boolean(state.cards && state.flag);
  } catch { S.shareCards = false; }
  $('share-today').classList.toggle('hidden', !S.shareCards);
}

/* Картинку тянем fetch-ом, а не ссылкой: подпись Telegram живёт в заголовке,
   и открыть URL напрямую нельзя — сервер не узнает, кто пришёл. Показываем
   внутри приложения: сохранить в сторис проще всего долгим нажатием. */
async function openCard(path, btn) {
  const url = new URL(path, location.origin);
  if (DEV_USER) url.searchParams.set('dev_user', DEV_USER);
  if (btn) btn.disabled = true;
  try {
    const res = await fetch(url, {
      headers: { 'X-Init-Data': tg?.initData || '' },
    });
    if (!res.ok) {
      let detail = null;
      try { detail = (await res.json()).detail; } catch { /* не JSON */ }
      throw new ApiError(res.status, detail);
    }
    const blobUrl = URL.createObjectURL(await res.blob());
    $('sheet-content').innerHTML =
      `<div class="sheet-title">Картинка для сторис</div>
       <img class="share-img" src="${blobUrl}" alt="Карточка Оракула">
       <p class="muted small center">Нажми и удерживай картинку, чтобы
          сохранить, — и выкладывай ✨</p>`;
    $('sheet').classList.remove('hidden');
    // отзываем ссылку при закрытии листа: иначе картинки копятся в памяти
    $('sheet').addEventListener('click', () => URL.revokeObjectURL(blobUrl),
                                { once: true });
    notify('success');
  } catch (e) {
    reportError(e);
  } finally {
    if (btn) btn.disabled = false;
  }
}

$('share-today').addEventListener('click', (ev) =>
  openCard('/api/share/today.png', ev.currentTarget));

async function loadMoonWeek() {
  try {
    const days = await api('/api/moon/week?days=7');
    const names = ['пн', 'вт', 'ср', 'чт', 'пт', 'сб', 'вс'];
    $('moon-strip').innerHTML = days.map((d, i) => `
      <div class="moon-day ${i === 0 ? 'today' : ''}" title="${esc(d.advice)}">
        <div class="md-e">${esc(d.emoji)}</div>
        <div class="md-d">${i === 0 ? 'сегодня' : esc(names[d.weekday] + ' ' + d.day_num)}</div>
      </div>`).join('');
    $('moon-week-card').classList.remove('hidden');
  } catch { /* не критично для экрана */ }
}

$('ask-btn').addEventListener('click', () => {
  haptic('medium');
  switchTab('chats');
  openThread('oracle').catch(reportError);
});

/* ══════ ЭКРАН: ЧАТЫ ══════ */
async function loadAgents() {
  S.agents = await api('/api/agents');
  $('agent-list').innerHTML = S.agents.map((a) => `
    <button class="agent-card" data-agent="${esc(a.code)}"
            style="--agent-accent:${esc(a.accent)}">
      <div class="agent-emoji">${esc(a.emoji)}</div>
      <div class="agent-body">
        <div class="agent-name">${esc(a.name)}
          <span class="agent-role">${esc(a.title)}</span></div>
        <div class="agent-last">${esc(a.last_text || a.tagline)}</div>
      </div>
      <div class="agent-count">${a.msg_count ? a.msg_count : ''}</div>
    </button>`).join('');
  $('agent-list').querySelectorAll('.agent-card').forEach((el) =>
    el.addEventListener('click', () => openThread(el.dataset.agent).catch(reportError)));
}

function showAgentList() {
  $('chat-thread-view').classList.add('hidden');
  $('chat-list-view').classList.remove('hidden');
  loadAgents().catch(reportError);
}
$('chat-back').addEventListener('click', showAgentList);

const chatLog = $('chat-log');
const chatInput = $('chat-input');
const chatSend = $('chat-send');
let chatBusy = false;

function bubble(role, text) {
  const b = document.createElement('div');
  b.className = 'bubble ' + (role === 'user' ? 'me' : 'oracle');
  b.textContent = text;
  chatLog.appendChild(b);
  b.scrollIntoView({ behavior: 'smooth', block: 'end' });
  return b;
}

function thinking() {
  const b = document.createElement('div');
  b.className = 'bubble oracle typing';
  b.innerHTML = '<i></i><i></i><i></i>';
  chatLog.appendChild(b);
  b.scrollIntoView({ behavior: 'smooth', block: 'end' });
  return b;
}

function renderChatLeft() {
  const a = S.me?.allowance;
  if (!a) return;
  const unit = a.period === 'week' ? 'на этой неделе' : 'сегодня';
  $('chat-left').textContent = a.left > 0
    ? `осталось вопросов ${unit}: ${a.left}`
    : a.extra_questions ? `купленных вопросов: ${a.extra_questions}`
      : a.can_ask ? `лимит исчерпан — следующий вопрос за ✦${a.emergency_cost}`
        : 'вопросы исчерпаны — вернись на рассвете 🌘';
}

async function openThread(code) {
  const data = await api(`/api/chat/${code}`);
  S.agent = code;
  const spec = data.agent;
  $('chat-list-view').classList.add('hidden');
  $('chat-thread-view').classList.remove('hidden');
  $('chat-agent-name').textContent = `${spec.emoji} ${spec.name}`;
  $('chat-agent-tagline').textContent = spec.tagline;
  chatInput.placeholder = `Спроси ${spec.name}…`;

  chatLog.innerHTML = '';
  if (!data.messages.length) bubble('assistant', spec.greeting);
  else data.messages.forEach((m) => bubble(m.role, m.text));

  $('chat-suggestions').innerHTML = (spec.suggestions || [])
    .map((s) => `<button class="sugg">${esc(s)}</button>`).join('');
  $('chat-suggestions').querySelectorAll('.sugg').forEach((btn) =>
    btn.addEventListener('click', () => {
      chatInput.value = btn.textContent;
      sendQuestion();
    }));
  renderChatLeft();
  chatLog.scrollIntoView({ block: 'end' });
}

/* textarea растёт под текст, но не бесконечно */
chatInput.addEventListener('input', () => {
  chatInput.style.height = 'auto';
  chatInput.style.height = Math.min(chatInput.scrollHeight, 120) + 'px';
});
chatInput.addEventListener('keydown', (e) => {
  if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendQuestion(); }
});
chatSend.addEventListener('click', sendQuestion);

async function sendQuestion() {
  const text = chatInput.value.trim();
  if (!text || chatBusy) return;
  chatBusy = true;
  chatSend.disabled = true;
  chatInput.value = '';
  chatInput.style.height = 'auto';
  $('chat-suggestions').innerHTML = '';
  bubble('user', text);
  haptic('medium');
  const dots = thinking();
  try {
    const res = await post(`/api/chat/${S.agent}`, { text });
    dots.remove();
    bubble('assistant', res.answer);
    if (S.me) S.me.allowance = res.allowance;
    renderChatLeft();
    renderLimits();
    notify('success');
  } catch (e) {
    dots.remove();
    reportError(e);
    chatInput.value = text;         // не теряем вопрос клиентки
    if (e.status === 402 || e.status === 429) {
      bubble('assistant', e.message + '\n\nВ разделе «Я» можно продлить доступ '
        + 'или взять дополнительные вопросы.');
    }
  } finally {
    chatBusy = false;
    chatSend.disabled = false;
  }
}

$('chat-clear').addEventListener('click', async () => {
  if (!confirm('Начать этот диалог заново? Память обо мне сохранится.')) return;
  try {
    await del(`/api/chat/${S.agent}`);
    await openThread(S.agent);
    toast('Начали с чистого листа ✨');
  } catch (e) { reportError(e); }
});

/* ══════ ЭКРАН: ТАРО ══════ */
const deckEl = $('deck');
const rowEl = $('tarot-row');
const posEl = $('pos-row');
const hintEl = $('deck-hint');
const drawBtn = $('draw-btn');

async function loadSpreads() {
  S.spreads = await api('/api/tarot/spreads');
  renderSpreadChips();
  loadHistory();
}

function renderSpreadChips() {
  const chips = S.spreads.map((s) => {
    const locked = s.tier === 'premium' && !s.owned;
    const price = locked
      ? `<span class="chip-price">${s.price_stars ? '⭐' + s.price_stars : '✦' + s.price_crystals}</span>`
      : s.owned ? '<span class="chip-price">✓</span>' : '';
    return `<button class="chip ${locked ? 'locked' : ''}" data-spread="${esc(s.code)}">
      ${esc(s.emoji)} ${esc(s.title)}${price}</button>`;
  }).join('');
  $('spread-chips').innerHTML = chips;
  $('spread-chips').querySelectorAll('.chip').forEach((chip) =>
    chip.addEventListener('click', () => pickSpread(chip.dataset.spread)));
  if (!S.spread && S.spreads.length) pickSpread(S.spreads[0].code);
}

function currentSpread() {
  return S.spreads.find((s) => s.code === S.spread);
}

function pickSpread(code) {
  S.spread = code;
  $('spread-chips').querySelectorAll('.chip').forEach((c) =>
    c.classList.toggle('active', c.dataset.spread === code));
  const s = currentSpread();
  resetTarot();
  selectHaptic();
  if (!s) return;
  const locked = s.tier === 'premium' && !s.owned;
  $('spread-hint').textContent = `${s.hint} · ${s.cards} `
    + plural(s.cards, 'карта', 'карты', 'карт')
    + (locked ? ' · большой расклад, открывается отдельно' : '');
  drawBtn.textContent = locked ? '🔓 Открыть расклад' : '✨ Вытянуть карты';
  drawBtn.disabled = !locked && !S.shuffled;
  if (locked) drawBtn.disabled = false;
}

function resetTarot() {
  rowEl.innerHTML = '';
  posEl.innerHTML = '';
  $('tarot-result').classList.add('hidden');
  deckEl.classList.remove('dealt');
  S.shuffled = false;
  S.drawn = null;
  drawBtn.disabled = true;
  hintEl.textContent = 'Сосредоточься на вопросе…';
}

$('shuffle-btn').addEventListener('click', async () => {
  if (deckEl.classList.contains('shuffling')) return;
  deckEl.classList.remove('dealt');
  rowEl.innerHTML = ''; posEl.innerHTML = '';
  $('tarot-result').classList.add('hidden');
  hintEl.textContent = 'Колода слушает тебя…';
  deckEl.classList.add('shuffling');
  // вибрация в ритм разлёта карт
  const beats = CALM ? 0 : 8;
  for (let i = 0; i < beats; i++) {
    setTimeout(() => haptic(i === beats - 1 ? 'medium' : 'light'), i * 175);
  }
  await new Promise((r) => setTimeout(r, CALM ? 300 : 1500));
  deckEl.classList.remove('shuffling');
  S.shuffled = true;
  drawBtn.disabled = false;
  hintEl.textContent = 'Колода готова. Тяни ✨';
  notify('success');
});

function sparks(el) {
  if (CALM) return;
  const r = el.getBoundingClientRect();
  const cx = r.left + r.width / 2, cy = r.top + r.height / 2;
  for (let i = 0; i < 14; i++) {
    const s = document.createElement('div');
    s.className = 'spark';
    const ang = Math.random() * Math.PI * 2, dist = 40 + Math.random() * 55;
    s.style.left = cx + 'px'; s.style.top = cy + 'px';
    s.style.setProperty('--dx', Math.cos(ang) * dist + 'px');
    s.style.setProperty('--dy', Math.sin(ang) * dist + 'px');
    document.body.appendChild(s);
    setTimeout(() => s.remove(), 750);
  }
}

drawBtn.addEventListener('click', async () => {
  const spread = currentSpread();
  if (!spread) return;

  // платный расклад без права — сначала покупка
  if (spread.tier === 'premium' && !spread.owned) {
    switchTab('profile');
    S.shopTab = 'spread';
    renderShopTabs();
    toast('Открой расклад в лавке — он появится здесь сразу ✨');
    return;
  }
  if (S.drawn) { resetTarot(); return; }
  if (!S.shuffled) { toast('Сначала потасуй колоду 🌀'); return; }

  drawBtn.disabled = true;
  drawBtn.textContent = '🌀 Тяну карты…';
  let res;
  try {
    res = await post(`/api/tarot/draw?spread=${encodeURIComponent(S.spread)}`);
  } catch (e) {
    reportError(e);
    resetTarot();
    drawBtn.textContent = '✨ Вытянуть карты';
    return;
  }
  S.drawn = res.cards;
  loadMe().catch(() => {});          // расклад мог съесть вопрос дня

  deckEl.classList.add('dealt');
  hintEl.textContent = res.title;

  rowEl.innerHTML = S.drawn.map((card, i) => `
    <div class="tcard ${card.reversed ? 'rev' : ''}" data-i="${i}">
      <div class="tcard-inner">
        <div class="tface tback">✦</div>
        <div class="tface tfront">
          <div class="num">${esc(card.num || '✶')}</div>
          <div class="e">${esc(card.emoji)}</div>
          <div>
            <div class="n">${esc(card.name)}</div>
            ${card.reversed ? '<div class="r">перевёрнутая ↩︎</div>' : ''}
          </div>
        </div>
      </div>
    </div>`).join('');
  posEl.innerHTML = res.positions.map((p) => `<span>${esc(p)}</span>`).join('');

  const cardEls = rowEl.querySelectorAll('.tcard');
  cardEls.forEach((c) => c.addEventListener('click', () => {
    c.classList.toggle('flipped'); haptic('light');
  }));

  // ждём раздачу, затем поочерёдный переворот
  await new Promise((r) => setTimeout(r, CALM ? 150 : 700));
  const pause = cardEls.length > 6 ? 260 : 620;
  for (const c of cardEls) {
    c.classList.add('flipped', 'glow');
    sparks(c);
    haptic('medium');
    await new Promise((r) => setTimeout(r, CALM ? 60 : pause));
    c.classList.remove('glow');
  }

  const box = $('tarot-result');
  box.classList.remove('hidden');
  box.innerHTML = `<div class="label">${esc(res.title)}</div>
    <div class="typing"><i></i><i></i><i></i></div>`;
  try {
    const { answer } = await post(`/api/tarot/interpret/${res.reading_id}`);
    box.innerHTML = `<div class="label">${esc(res.title)}</div>
      <div class="hist-body">${esc(answer)}</div>
      ${outcomeRow(res.reading_id)}`;
    wireOutcome(box, res.reading_id);
    notify('success');
    loadHistory();
    loadSpreads().catch(() => {});   // право могло списаться
  } catch (e) {
    const key = S.drawn[Math.floor(S.drawn.length / 2)];
    box.innerHTML = `<div class="label">${esc(res.title)}</div>
      <div class="hist-body">Сердце расклада — ${esc(key.emoji)} <b>${esc(key.name)}</b>: `
      + `${esc(key.meaning)}.\n\nГлубокую трактовку спрошу у звёзд чуть позже — `
      + `связь сейчас неровная 🌙</div>`;
    reportError(e);
  }
  drawBtn.disabled = false;
  drawBtn.textContent = '↺ Новый расклад';
});

function outcomeRow(readingId, current = null) {
  const marks = [['came_true', '✅ Сбылось'], ['partly', '🤔 Частично'], ['no', '➖ Нет']];
  const share = S.shareCards
    ? `<button class="btn-ghost" data-card="${readingId}">🖼 Картинка для сторис</button>`
    : '';
  return `<div class="outcome-row" data-reading="${readingId}">
    ${marks.map(([code, label]) =>
      `<button data-outcome="${code}" class="${current === code ? 'done' : ''}">${label}</button>`
    ).join('')}</div>${share}`;
}

function wireOutcome(root, readingId) {
  root.querySelectorAll(`[data-reading="${readingId}"] button`).forEach((btn) =>
    btn.addEventListener('click', async () => {
      try {
        await post(`/api/tarot/outcome/${readingId}`, { outcome: btn.dataset.outcome });
        btn.parentElement.querySelectorAll('button').forEach((b) =>
          b.classList.toggle('done', b === btn));
        toast('Записала — это помогает читать твои карты точнее 🌙');
        notify('success');
      } catch (e) { reportError(e); }
    }));
  root.querySelectorAll(`[data-card="${readingId}"]`).forEach((btn) =>
    btn.addEventListener('click', () =>
      openCard(`/api/share/reading/${readingId}.png`, btn)));
}

async function loadHistory() {
  let list;
  try { list = await api('/api/tarot/history'); } catch { return; }
  const box = $('tarot-history');
  $('history-title').classList.toggle('hidden', !list.length);
  box.innerHTML = list.map((r) => {
    const cards = r.cards.map((c) => `${c.emoji} ${c.name}${c.reversed ? ' ↩︎' : ''}`).join(' · ');
    const title = (r.question || '').replace(/^Расклад «|»$/g, '');
    return `<div class="glass hist" data-id="${r.id}">
      <div class="hist-head">
        <span class="hist-title">${esc(title)}</span>
        <span class="hist-date">${dateRu(r.created_at)}</span>
      </div>
      <div class="hist-cards">${esc(cards)}</div>
      <div class="hist-body hidden">${esc(r.answer)}${outcomeRow(r.id, r.outcome)}</div>
    </div>`;
  }).join('');

  box.querySelectorAll('.hist').forEach((el) => {
    const body = el.querySelector('.hist-body');
    el.querySelector('.hist-head').addEventListener('click', () => {
      body.classList.toggle('hidden');
      selectHaptic();
    });
    wireOutcome(el, +el.dataset.id);
  });
}

/* ══════ ЭКРАН: КАРТА ══════ */
const SIGN_GLYPHS = ['♈', '♉', '♊', '♋', '♌', '♍', '♎', '♏', '♐', '♑', '♒', '♓'];
const PLANET_GLYPHS = {
  'Солнце': '☉', 'Луна': '☽', 'Меркурий': '☿', 'Венера': '♀', 'Марс': '♂',
  'Юпитер': '♃', 'Сатурн': '♄', 'Уран': '♅', 'Нептун': '♆', 'Плутон': '♇',
};

async function loadChart() {
  try {
    S.chart = await api('/api/chart');
  } catch (e) {
    $('chart-note').textContent = e.message;
    return;
  }
  drawWheel(S.chart);
  renderChartDetail('planets');
  $('sun-badge').textContent = S.chart.sun
    ? `${S.chart.sun.symbol} Солнце в ${S.chart.sun.sign}` : '';
  const notes = [];
  if (S.chart.mode !== 'full') notes.push(S.chart.note || 'Упрощённый расчёт');
  if (!S.chart.birth?.time_known) notes.push('время рождения неточное — дома как ориентир');
  $('chart-note').textContent = notes.join(' · ');

  loadMatrix();
  loadPartners();
  loadReports();
}

/* Колесо: планеты по абсолютной долготе + куспиды домов.
   Близкие планеты разводим по радиусу, иначе символы наезжают друг на друга. */
function drawWheel(chart) {
  const svg = $('wheel');
  const cx = 150, cy = 150, R = 142, Rin = 108;
  let s = `<circle cx="${cx}" cy="${cy}" r="${R}" fill="none" stroke="rgba(232,197,107,.4)"/>
           <circle cx="${cx}" cy="${cy}" r="${Rin}" fill="none" stroke="rgba(255,255,255,.15)"/>
           <circle cx="${cx}" cy="${cy}" r="50" fill="none" stroke="rgba(255,255,255,.1)"/>`;

  for (let i = 0; i < 12; i++) {
    const a = (i * 30 - 90) * Math.PI / 180;
    s += `<line x1="${cx + Rin * Math.cos(a)}" y1="${cy + Rin * Math.sin(a)}"
           x2="${cx + R * Math.cos(a)}" y2="${cy + R * Math.sin(a)}"
           stroke="rgba(255,255,255,.18)"/>`;
    const am = (i * 30 + 15 - 90) * Math.PI / 180;
    s += `<text x="${cx + (R - 16) * Math.cos(am)}" y="${cy + (R - 16) * Math.sin(am)}"
           fill="#e8c56b" font-size="13" text-anchor="middle"
           dominant-baseline="middle" opacity=".85">${SIGN_GLYPHS[i]}</text>`;
  }

  for (const h of (chart.houses || [])) {
    const a = ((h.abs_deg ?? 0) - 90) * Math.PI / 180;
    s += `<line x1="${cx + 50 * Math.cos(a)}" y1="${cy + 50 * Math.sin(a)}"
           x2="${cx + Rin * Math.cos(a)}" y2="${cy + Rin * Math.sin(a)}"
           stroke="rgba(255,255,255,.10)" stroke-dasharray="3 3"/>
          <text x="${cx + 60 * Math.cos(a)}" y="${cy + 60 * Math.sin(a)}"
           fill="#a99fc9" font-size="8" text-anchor="middle"
           dominant-baseline="middle">${h.n}</text>`;
  }

  const planets = chart.planets || [];
  const used = [];
  for (const p of planets) {
    const deg = p.abs_deg ?? 0;
    let radius = 84;
    while (used.some((u) => Math.abs(u.deg - deg) < 9 && Math.abs(u.radius - radius) < 9)) {
      radius -= 15;                      // сдвигаем вглубь, пока не освободится место
      if (radius < 56) { radius = 84; break; }
    }
    used.push({ deg, radius });
    const a = (deg - 90) * Math.PI / 180;
    const px = cx + radius * Math.cos(a), py = cy + radius * Math.sin(a);
    s += `<circle cx="${px}" cy="${py}" r="9" fill="rgba(232,197,107,.12)"/>
          <text x="${px}" y="${py}" fill="#f4efff" font-size="12" text-anchor="middle"
           dominant-baseline="middle">${PLANET_GLYPHS[p.name] || '•'}</text>`;
    if (p.retro) {
      s += `<text x="${px + 8}" y="${py - 7}" fill="#e88f8f" font-size="7">R</text>`;
    }
  }
  if (!planets.length && chart.sun) {
    s += `<text x="${cx}" y="${cy}" fill="#e8c56b" font-size="40" text-anchor="middle"
           dominant-baseline="middle">${chart.sun.symbol}</text>`;
  }
  svg.innerHTML = s;
}

document.querySelectorAll('#chart-seg .seg').forEach((btn) =>
  btn.addEventListener('click', () => {
    document.querySelectorAll('#chart-seg .seg').forEach((b) =>
      b.classList.toggle('active', b === btn));
    renderChartDetail(btn.dataset.seg);
    selectHaptic();
  }));

function renderChartDetail(kind) {
  const box = $('chart-detail');
  const chart = S.chart || {};
  if (kind === 'planets') {
    const rows = chart.planets || [];
    box.innerHTML = rows.length ? rows.map((p) => `
      <div class="planet-line">
        <span>${PLANET_GLYPHS[p.name] || '•'} ${esc(p.name)}</span>
        <span>${esc(p.sign)} ${p.deg}°${p.house ? ' · ' + p.house + ' дом' : ''}${p.retro ? ' ↩︎' : ''}</span>
      </div>`).join('')
      : '<p class="muted">Упрощённый расчёт: полные эфемериды на сервере покажут все 10 планет ✨</p>';
    return;
  }
  if (kind === 'houses') {
    const rows = chart.houses || [];
    box.innerHTML = rows.length ? rows.map((h) => `
      <div class="house-line"><span>${h.n} дом</span>
        <span>${esc(h.sign)} ${h.deg}°</span></div>`).join('')
      : '<p class="muted">Дома считаются, когда известно время рождения 🌙</p>';
    return;
  }
  const rows = chart.aspects || [];
  box.innerHTML = rows.length ? rows.map((a) => `
    <div class="aspect-line">
      <span>${esc(a.p1)} <span class="aspect-glyph">${esc(a.glyph)}</span> ${esc(a.p2)}</span>
      <span>${esc(a.aspect)} <span class="orb">орб ${a.orb}°</span></span>
    </div>`).join('')
    : '<p class="muted">Аспекты появятся в полном расчёте карты 🌌</p>';
}

async function loadMatrix() {
  try {
    const m = await api('/api/matrix');
    $('matrix-list').innerHTML = Object.values(m).map((v) =>
      `<div class="matrix-line"><b>${v.n} · ${esc(v.arcana)}</b> — ${esc(v.title)}<br>
       <span class="muted">${esc(v.meaning)}</span></div>`).join('');
    drawMatrixStar(m);
  } catch { /* нет даты рождения */ }
}

function drawMatrixStar(m) {
  const svg = $('matrix-star');
  const cx = 150, cy = 150, R = 116;
  const keys = ['personal', 'spirit', 'family', 'destiny', 'love', 'money'];
  const items = keys.filter((k) => m[k]).map((k) => m[k]);
  let s = '';
  for (const rot of [0, 45]) {
    const pts = [0, 90, 180, 270].map((a) => {
      const r = (a + rot - 90) * Math.PI / 180;
      return `${cx + R * Math.cos(r)},${cy + R * Math.sin(r)}`;
    }).join(' ');
    s += `<polygon points="${pts}" fill="none" stroke="rgba(232,197,107,.35)" stroke-width="1.2"/>`;
  }
  s += `<circle cx="${cx}" cy="${cy}" r="${R}" fill="none" stroke="rgba(255,255,255,.08)"/>`;
  if (m.center) {
    s += `<circle cx="${cx}" cy="${cy}" r="26" class="mx-circle"/>
          <text x="${cx}" y="${cy - 2}" text-anchor="middle" class="mx-num">${m.center.n}</text>
          <text x="${cx}" y="${cy + 13}" text-anchor="middle" class="mx-lab">центр</text>`;
  }
  items.forEach((v, i) => {
    const a = (i * 60 - 90) * Math.PI / 180;
    const x = cx + R * Math.cos(a), y = cy + R * Math.sin(a);
    const lab = v.title.replace('Аркан ', '').replace('Линия ', '').split(' ')[0];
    s += `<circle cx="${x}" cy="${y}" r="21" class="mx-circle"/>
          <text x="${x}" y="${y + 1}" text-anchor="middle" class="mx-num">${v.n}</text>
          <text x="${x}" y="${y + 33}" text-anchor="middle" class="mx-lab">${esc(lab)}</text>`;
  });
  svg.innerHTML = s;
}

/* ── спидометр любви ── */
$('compat-btn').addEventListener('click', async () => {
  const value = $('compat-date').value;
  if (!value) { toast('Выбери дату рождения партнёра 🌙'); return; }
  const name = $('compat-name').value.trim();
  let data;
  try {
    data = await post('/api/compat', {
      partner_date: value, partner_name: name, save: Boolean(name),
    });
  } catch (e) { reportError(e); return; }

  S.compat = data;
  const box = $('compat-result');
  box.classList.remove('hidden');
  $('compat-deep').textContent = '';
  $('gauge-arc').style.strokeDashoffset = 251 - (251 * data.score / 100);
  animateNum($('gauge-num'), data.score);
  $('compat-text').innerHTML =
    `<b>${esc(data.you.sign)}</b> (${esc(data.you.element)}) + ` +
    `<b>${esc(data.partner.sign)}</b> (${esc(data.partner.element)})<br>` +
    `<span class="muted">${esc(data.verdict)}</span>`;
  $('compat-breakdown').innerHTML = (data.breakdown || []).map((b) =>
    `<div><span>${esc(b.title)}: ${esc(b.note)}</span>
     <b>${b.value > 0 ? '+' : ''}${b.value}</b></div>`).join('');
  notify('success');
  if (name) loadPartners();
});

$('compat-full').addEventListener('click', async (ev) => {
  const value = $('compat-date').value;
  if (!value) return;
  const btn = ev.currentTarget;
  const out = $('compat-deep');
  btn.disabled = true;
  out.innerHTML = '<span class="typing"><i></i><i></i><i></i></span>';
  haptic('medium');
  try {
    const { answer } = await post('/api/compat/full', {
      partner_date: value, partner_name: $('compat-name').value.trim(), save: true,
    });
    out.textContent = answer;
    notify('success');
    loadMe().catch(() => {});
  } catch (e) {
    out.textContent = '';
    reportError(e);
  } finally {
    btn.disabled = false;
  }
});

function animateNum(el, to) {
  if (CALM) { el.textContent = to; return; }
  let v = 0;
  const step = () => {
    v = Math.min(to, v + Math.ceil(to / 30));
    el.textContent = v;
    if (v < to) requestAnimationFrame(step);
  };
  requestAnimationFrame(step);
}

async function loadPartners() {
  let list;
  try { list = await api('/api/partners'); } catch { return; }
  const box = $('partners-list');
  if (!list.length) { box.innerHTML = ''; return; }
  box.innerHTML = '<div class="label">Сохранённые люди</div>' + list.map((p) =>
    `<div class="partner" data-id="${p.id}">
       <span>${esc(p.name)} · ${esc(p.birth_date)}</span>
       <span><button data-use="${esc(p.birth_date)}" data-name="${esc(p.name)}">↻</button>
         <button data-del="${p.id}">✕</button></span>
     </div>`).join('');

  box.querySelectorAll('[data-use]').forEach((btn) => btn.addEventListener('click', () => {
    $('compat-date').value = btn.dataset.use;
    $('compat-name').value = btn.dataset.name;
    $('compat-btn').click();
  }));
  box.querySelectorAll('[data-del]').forEach((btn) => btn.addEventListener('click', async () => {
    try { await del(`/api/partners/${btn.dataset.del}`); loadPartners(); }
    catch (e) { reportError(e); }
  }));
}

/* ── большие разборы ── */
const REPORT_TITLES = {
  natal: 'Натальная карта — полный разбор',
  matrix: 'Матрица Судьбы — полный разбор',
  synastry: 'Синастрия: совместимость пары',
  career: 'Карьера и предназначение',
  solar: 'Годовой прогноз по картам',
  monthly: 'Итог месяца',
};

async function loadReports() {
  let data;
  try { data = await api('/api/reports'); } catch { return; }
  const box = $('reports-box');
  const parts = [];

  if (data.available.length) {
    parts.push('<div class="label">Оплачено — можно собрать</div>');
    parts.push(data.available.map((e) => `
      <div class="report-item">
        <div><div class="report-title">${esc(REPORT_TITLES[e.code] || e.code)}</div>
          <div class="report-when">осталось ${e.qty_total - e.qty_used}</div></div>
        <button class="btn-price" data-build="${esc(e.code)}">Собрать</button>
      </div>`).join(''));
  }
  if (data.ready.length) {
    parts.push('<div class="label">Готовые разборы</div>');
    parts.push(data.ready.map((r) => `
      <div class="report-item">
        <div><div class="report-title">${esc(r.title)}</div>
          <div class="report-when">${dateRu(r.created_at)}${r.period ? ' · ' + esc(r.period) : ''}</div></div>
        <button class="btn-price ghost" data-open="${esc(r.kind)}"
          data-period="${esc(r.period || '')}">Читать</button>
      </div>`).join(''));
  }
  if (!parts.length) {
    parts.push('<p class="muted">Большой разбор — длинный текст, который остаётся '
      + 'у тебя навсегда. Взять можно в лавке, раздел «Я» → «Разборы».</p>');
  }
  box.innerHTML = parts.join('');

  box.querySelectorAll('[data-build]').forEach((btn) =>
    btn.addEventListener('click', () => buildReport(btn, btn.dataset.build)));
  box.querySelectorAll('[data-open]').forEach((btn) =>
    btn.addEventListener('click', async () => {
      try {
        const period = btn.dataset.period;
        const r = await api(`/api/reports/${btn.dataset.open}`
          + (period ? `?period=${encodeURIComponent(period)}` : ''));
        openSheet(r.title, r.body.replace(/<[^>]+>/g, ''));
      } catch (e) { reportError(e); }
    }));
}

async function buildReport(btn, kind) {
  const body = {};
  if (kind === 'synastry') {
    const value = $('compat-date').value;
    if (!value) { toast('Сначала укажи дату партнёра в разделе «Спидометр любви»'); return; }
    body.partner_date = value;
    body.partner_name = $('compat-name').value.trim();
  }
  btn.disabled = true;
  btn.textContent = 'Собираю…';
  try {
    const r = await post(`/api/reports/${kind}`, body);
    openSheet(r.title, (r.body || '').replace(/<[^>]+>/g, ''));
    notify('success');
    loadReports();
  } catch (e) {
    reportError(e);
    btn.disabled = false;
    btn.textContent = 'Собрать';
  }
}

/* ══════ ЭКРАН: ПРАКТИКИ ══════ */

async function loadPractices() {
  const data = await api('/api/practices');
  S.practices = data;
  renderPracticeCats(data.categories);
  renderPractices();
}

function renderPracticeCats(categories) {
  const chips = [{ code: null, emoji: '✦', title: 'Все' }, ...categories];
  $('practice-cats').innerHTML = chips.map((c) => `
    <button class="chip ${c.code === S.practiceCat ? 'active' : ''}"
            data-cat="${esc(c.code || '')}">${esc(c.emoji)} ${esc(c.title)}</button>`
  ).join('');
  $('practice-cats').querySelectorAll('.chip').forEach((chip) =>
    chip.addEventListener('click', () => {
      S.practiceCat = chip.dataset.cat || null;
      renderPracticeCats(S.practices.categories);
      renderPractices();
      selectHaptic();
    }));
}

function practiceRow(p) {
  const bar = p.started && !p.finished
    ? `<div class="pbar"><i style="width:${p.percent}%"></i></div>` : '';
  const meta = p.finished ? '✓ пройдена'
    : p.started ? `день ${p.day_index} из ${p.days}`
      + (p.streak >= 2 ? ` · стрик ${p.streak} 🔥` : '')
      : `${p.days} ${plural(p.days, 'день', 'дня', 'дней')}`;
  return `
    <button class="practice-card ${p.started && !p.finished ? 'running' : ''}"
            data-practice="${esc(p.code)}">
      <div class="pc-emoji">${esc(p.emoji)}</div>
      <div class="pc-body">
        <div class="pc-title">${esc(p.title)}</div>
        <div class="pc-goal">${esc(p.goal || p.about || '')}</div>
        <div class="pc-meta">${esc(meta)}</div>
        ${bar}
      </div>
    </button>`;
}

function renderPractices() {
  if (!S.practices) return;
  const all = S.practices.items;
  const running = all.filter((p) => p.started && !p.finished);
  $('practice-running').innerHTML = running.length
    ? `<div class="glass"><div class="label">Ты сейчас проходишь</div>
        ${running.map(practiceRow).join('')}</div>`
    : '';

  const list = all.filter((p) => (!S.practiceCat || p.category === S.practiceCat)
    && !(p.started && !p.finished));
  $('practice-list').innerHTML = list.length
    ? list.map(practiceRow).join('')
    : '<p class="muted center">В этом разделе пока пусто</p>';

  document.querySelectorAll('[data-practice]').forEach((el) =>
    el.addEventListener('click', () => openPractice(el.dataset.practice)));
}

function practiceSheet(p) {
  const steps = (p.steps || []).map((s, i) =>
    `<li><b>${i + 1}.</b> ${esc(s)}</li>`).join('');
  const signs = (p.signs || []).map((s) => `<li>${esc(s)}</li>`).join('');
  const meta = [
    `⏳ ${p.days} ${plural(p.days, 'день', 'дня', 'дней')}`,
    p.best_time ? `🕐 ${esc(p.best_time)}` : '',
    p.moon ? `🌙 ${esc(p.moon)}` : '',
  ].filter(Boolean).join(' · ');

  const today = p.started && !p.finished && p.today_step
    ? `<div class="pc-today"><b>Сегодня — день ${p.day_index + 1}</b><br>
       ${esc(p.today_step)}</div>` : '';
  const mantra = p.text
    ? `<div class="mantra">${esc(p.text)}</div>` : '';

  const action = p.finished
    ? `<button class="btn-gold" data-p-start="${esc(p.code)}">🔁 Пройти заново</button>`
    : p.started
      ? `<button class="btn-gold" data-p-done="${esc(p.code)}">
           ✅ Отметить день ${p.day_index + 1}</button>
         <button class="btn-ghost" data-p-stop="${esc(p.code)}">Остановить</button>`
      : `<button class="btn-gold" data-p-start="${esc(p.code)}">
           ▶️ Начать · ${p.days} ${plural(p.days, 'день', 'дня', 'дней')}</button>`;

  return `
    <div class="sheet-title">${esc(p.emoji)} ${esc(p.title)}</div>
    <p class="muted">${esc(p.goal || '')}</p>
    <p class="pc-meta">${meta}</p>
    ${today}
    ${p.about ? `<p class="sheet-text">${esc(p.about)}</p>` : ''}
    ${mantra}
    <div class="label">Что делать</div>
    <ol class="steps">${steps}</ol>
    ${signs ? `<div class="label">По чему поймёшь, что работает</div>
               <ul class="signs">${signs}</ul>` : ''}
    ${p.warning ? `<p class="warn">⚠️ ${esc(p.warning)}</p>` : ''}
    ${action}`;
}

function openPractice(code) {
  const p = (S.practices?.items || []).find((x) => x.code === code);
  if (!p) return;
  $('sheet-content').innerHTML = practiceSheet(p);
  $('sheet').classList.remove('hidden');
  haptic('light');
  wirePracticeActions();
}

function wirePracticeActions() {
  const box = $('sheet-content');
  const call = async (path, btn, done) => {
    btn.disabled = true;
    try {
      const res = await post(path);
      await loadPractices();
      done(res);
    } catch (e) { reportError(e); btn.disabled = false; }
  };
  box.querySelectorAll('[data-p-start]').forEach((btn) =>
    btn.addEventListener('click', () =>
      call(`/api/practices/${btn.dataset.pStart}/start`, btn, () => {
        toast('Начали ✨ Я напомню утром');
        notify('success');
        openPractice(btn.dataset.pStart);
      })));
  box.querySelectorAll('[data-p-done]').forEach((btn) =>
    btn.addEventListener('click', () =>
      call(`/api/practices/${btn.dataset.pDone}/done`, btn, (res) => {
        toast(res.message);
        notify('success');
        openPractice(btn.dataset.pDone);
      })));
  box.querySelectorAll('[data-p-stop]').forEach((btn) =>
    btn.addEventListener('click', () =>
      call(`/api/practices/${btn.dataset.pStop}/stop`, btn, () => {
        toast('Практика остановлена 🌙');
        $('sheet').classList.add('hidden');
      })));
}

/* ══════ ЭКРАН: ДНЕВНИК ══════ */
document.querySelectorAll('#mood-row .mood').forEach((btn) =>
  btn.addEventListener('click', () => {
    const same = S.diaryMood === btn.dataset.mood;
    S.diaryMood = same ? null : btn.dataset.mood;
    document.querySelectorAll('#mood-row .mood').forEach((b) =>
      b.classList.toggle('active', !same && b === btn));
    selectHaptic();
  }));

async function loadDiary() {
  try {
    const data = await api('/api/diary');
    $('diary-list').innerHTML = data.entries.map((e) => `
      <div class="glass diary-entry">
        <div class="diary-date">${dateRu(e.created_at)}${e.mood ? ' · ' + esc(e.mood) : ''}</div>
        <div>${esc(e.text)}</div></div>`).join('')
      || '<p class="muted center">Первая запись — самая важная ✨</p>';
    const badge = $('streak-badge');
    if (data.streak >= 2) {
      badge.textContent = `🔥 ${data.streak} дн. подряд`;
      badge.classList.remove('hidden');
    } else badge.classList.add('hidden');
  } catch { /* профиль ещё не создан */ }
  loadDiaryPrompt();
}

/* Вечерний вопрос от Оракула: пустое поле «расскажи о дне» не заполняют,
   а конкретный вопрос — заполняют. */
async function loadDiaryPrompt() {
  try {
    const p = await api('/api/diary/prompt');
    $('diary-prompt').textContent = p.prompt;
    $('diary-text').placeholder = p.written_today
      ? 'Добавить ещё…' : p.prompt;
  } catch { /* не критично */ }
}

$('diary-save').addEventListener('click', async (ev) => {
  const ta = $('diary-text');
  const text = ta.value.trim();
  if (!text) return;
  const btn = ev.currentTarget;
  btn.disabled = true;
  try {
    const res = await post('/api/diary', { text, mood: S.diaryMood });
    ta.value = '';
    S.diaryMood = null;
    document.querySelectorAll('#mood-row .mood').forEach((b) => b.classList.remove('active'));
    notify('success');
    toast(res.streak >= 3 ? `Записала 📖 Ты пишешь ${res.streak} дней подряд 🔥`
      : 'Записала в твою книгу судьбы 📖');
    loadDiary();
  } catch (e) {
    reportError(e);          // текст остаётся в поле, ничего не теряем
  } finally {
    btn.disabled = false;
  }
});

/* ══════ ЭКРАН: ПРОФИЛЬ ══════ */
function renderProfileHead() {
  const me = S.me;
  if (!me) return;
  $('p-name').textContent = me.name;
  $('p-oracle').textContent = `Твой Оракул — ${me.oracle_name}`;
  $('p-crystals').textContent = me.crystals;
  $('p-days').textContent = me.sub_days_left;
  $('p-q').textContent = me.allowance.left;
  $('avatar').textContent = me.sun?.symbol || '🔮';
  const plan = $('p-plan');
  plan.textContent = me.sub_active ? me.plan.title : 'без подписки';
  plan.style.display = 'inline-block';
  $('memories').innerHTML = me.memories.length
    ? me.memories.map((m) => `<li>${esc(m)}</li>`).join('')
    : '<li class="muted">я только начинаю узнавать тебя…</li>';
  $('set-push').checked = Boolean(me.morning_push);
  $('set-oracle-name').value = me.oracle_name || '';
}

async function loadProfile() {
  renderProfileHead();
  await Promise.all([loadShop(), loadReferral(), loadPersonas(), loadFaq()]);
}

document.querySelectorAll('#shop-seg .seg').forEach((btn) =>
  btn.addEventListener('click', () => {
    S.shopTab = btn.dataset.shop;
    renderShopTabs();
    selectHaptic();
  }));

function renderShopTabs() {
  document.querySelectorAll('#shop-seg .seg').forEach((b) =>
    b.classList.toggle('active', b.dataset.shop === S.shopTab));
  renderShop();
}

async function loadShop() {
  S.shop = await api('/api/shop');
  renderShop();
}

function renderShop() {
  const box = $('shop-items');
  if (!S.shop) { box.innerHTML = '<div class="skeleton"></div><div class="skeleton"></div>'; return; }

  if (S.shopTab === 'plans') {
    box.innerHTML = S.shop.plans.filter((p) => p.price_stars).map((p) => `
      <div class="plan-card ${p.code === S.shop.current_plan ? 'current' : ''}">
        <div class="plan-top">
          <span class="plan-title">${esc(p.title)}</span>
          <span class="plan-price">⭐${p.price_stars}</span>
        </div>
        ${p.badge ? `<div class="plan-badge">${esc(p.badge)}</div>` : ''}
        <div class="plan-tagline">${esc(p.tagline || '')} · ${p.period_days} дн.</div>
        <ul class="plan-features">${(p.features || []).map((f) => `<li>${esc(f)}</li>`).join('')}</ul>
        <button class="btn-gold" data-plan="${esc(p.code)}" style="margin-top:10px">
          ${p.code === S.shop.current_plan ? 'Продлить' : 'Выбрать'}</button>
      </div>`).join('');
    box.querySelectorAll('[data-plan]').forEach((btn) =>
      btn.addEventListener('click', () => payStars({ plan: btn.dataset.plan }, btn)));
    return;
  }

  const items = S.shop.products[S.shopTab] || [];
  if (!items.length) { box.innerHTML = '<p class="muted">Здесь пока пусто</p>'; return; }
  box.innerHTML = items.map((p) => `
    <div class="shop-item">
      <div class="shop-body">
        <div class="shop-title">${esc(p.title)}</div>
        <div class="shop-desc">${esc(p.description || '')}</div>
      </div>
      <div class="shop-buy">
        ${p.price_stars ? `<button class="btn-price" data-sku="${esc(p.sku)}">⭐${p.price_stars}</button>` : ''}
        ${p.price_crystals ? `<button class="btn-price ghost" data-crystals="${esc(p.sku)}">✦${p.price_crystals}</button>` : ''}
      </div>
    </div>`).join('');

  box.querySelectorAll('[data-sku]').forEach((btn) =>
    btn.addEventListener('click', () => payStars({ sku: btn.dataset.sku }, btn)));
  box.querySelectorAll('[data-crystals]').forEach((btn) =>
    btn.addEventListener('click', () => payCrystals(btn.dataset.crystals, btn)));
}

/* Оплата Stars: сервер создаёт заказ и ссылку, Telegram проводит платёж,
   выдачу делает бот по апдейту successful_payment. Поэтому после 'paid'
   просто перечитываем состояние — оно уже обновлено сервером. */
async function payStars(body, btn) {
  btn.disabled = true;
  try {
    const { link } = await post('/api/shop/invoice', body);
    if (!tg?.openInvoice) { toast('Оплата доступна только внутри Telegram 🌙'); return; }
    tg.openInvoice(link, async (status) => {
      if (status === 'paid') {
        notify('success');
        toast('Оплата прошла ✨ Открываю…');
        // боту нужен момент, чтобы обработать апдейт и выдать покупку
        setTimeout(async () => {
          await Promise.all([loadMe(), loadShop(), loadSpreads(), loadReports()]
            .map((p) => Promise.resolve(p).catch(() => {})));
        }, 1200);
      } else if (status === 'failed') {
        toast('Платёж не прошёл 🌙');
      }
    });
  } catch (e) {
    reportError(e);
  } finally {
    btn.disabled = false;
  }
}

async function payCrystals(sku, btn) {
  btn.disabled = true;
  try {
    const res = await post('/api/shop/crystals', { sku });
    notify('success');
    toast(`Открыто: ${res.granted.title || 'покупка'} ✨`);
    await Promise.all([loadMe(), loadShop()]);
    loadSpreads().catch(() => {});
    loadReports().catch(() => {});
  } catch (e) {
    reportError(e);
  } finally {
    btn.disabled = false;
  }
}

async function loadReferral() {
  try {
    const r = await api('/api/referral');
    $('ref-text').textContent =
      `За каждую подругу — по ✦${r.bonus_per_invite} вам обеим. `
      + `Когда она оформит доступ — тебе ещё ✦${r.revenue_share}.`;
    $('ref-link').textContent = r.link;
    $('ref-link').onclick = () => {
      navigator.clipboard?.writeText(r.link);
      toast('Ссылка скопирована ✨');
      selectHaptic();
    };
    $('ref-share').onclick = () => {
      const url = 'https://t.me/share/url?url=' + encodeURIComponent(r.link)
        + '&text=' + encodeURIComponent(r.share_text);
      tg?.openTelegramLink ? tg.openTelegramLink(url) : window.open(url, '_blank');
    };
    $('ref-stats').innerHTML = r.level1
      ? `<span>пришло: <b>${r.level1}</b></span>
         ${r.level2 ? `<span>подруг подруг: <b>${r.level2}</b></span>` : ''}
         <span>оформили доступ: <b>${r.paying}</b></span>
         <span>начислено: <b>✦${r.bonus_total}</b></span>`
      : '<span>пока никто не пришёл — самое время поделиться ✨</span>';
  } catch { /* не критично */ }
}

async function loadPersonas() {
  try {
    const list = await api('/api/personas');
    $('set-persona').innerHTML = list.map((p) =>
      `<option value="${esc(p.code)}">${esc(p.emoji)} ${esc(p.title)}</option>`).join('');
    if (S.me?.persona) $('set-persona').value = S.me.persona;
  } catch { /* не критично */ }
}

$('set-save').addEventListener('click', async (ev) => {
  ev.currentTarget.disabled = true;
  try {
    await post('/api/profile', {
      oracle_name: $('set-oracle-name').value.trim() || null,
      persona: $('set-persona').value || null,
      morning_push: $('set-push').checked,
    });
    toast('Сохранила ✨');
    notify('success');
    await loadMe();
    LOADED.delete('chats');          // имя и образ агента изменились
  } catch (e) { reportError(e); } finally { ev.currentTarget.disabled = false; }
});

$('set-push').addEventListener('change', async (e) => {
  try { await post('/api/profile', { morning_push: e.target.checked }); }
  catch (err) { reportError(err); }
});

async function loadFaq() {
  try {
    const items = await api('/api/faq');
    if (!items.length) { $('faq-box').innerHTML = ''; return; }
    $('faq-box').innerHTML = '<div class="label">Вопросы и ответы</div>' + items.map((f) => `
      <div class="faq-item">
        <div class="faq-q">${esc(f.title)}<span>＋</span></div>
        <div class="faq-a hidden">${esc(f.body)}</div>
      </div>`).join('');
    $('faq-box').querySelectorAll('.faq-q').forEach((q) =>
      q.addEventListener('click', () => {
        q.nextElementSibling.classList.toggle('hidden');
        q.querySelector('span').textContent =
          q.nextElementSibling.classList.contains('hidden') ? '＋' : '－';
        selectHaptic();
      }));
  } catch { /* не критично */ }
}

/* ══════ старт ══════ */
(async function boot() {
  try {
    await loadMe();
  } catch (e) {
    $('greeting').textContent = e.status === 404
      ? 'Открой бота и нажми /start 🌙' : e.message;
    return;
  }
  loadToday();
})();
