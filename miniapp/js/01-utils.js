/* utils: Telegram WebApp, haptic, API-клиент, escaping, даты */
const tg = () => window.Telegram && window.Telegram.WebApp;

/* haptic-отклик Telegram (безопасно — если WebApp/HapticFeedback нет, молча). */
function haptic(kind) {
  try {
    const H = tg() && tg().HapticFeedback;
    if (!H) return;
    if (kind === 'success') H.notificationOccurred('success');
    else if (kind === 'error') H.notificationOccurred('error');
    else if (kind === 'soft') H.impactOccurred('soft');
    else H.impactOccurred('light');
  } catch (e) {}
}

/* вибро-отклик (безопасно): vibrate может отсутствовать или бросать — тихо глотаем.
   Заменяет повсюду копии `if (navigator.vibrate) { try { navigator.vibrate(...) } catch (e) {} }`. */
const vb = p => { try { navigator.vibrate && navigator.vibrate(p); } catch (e) {} };

/* гонка-предохранитель для виджетов: активен ли всё ещё тот же виджет в том же
   чате/экране. Если юзер успел открыть другой виджет/агента, закрыть чат или уйти
   с экрана — late-ответ от api() надо бросить, а не затирать чужой рендер. */
function widAlive(key, view, pend) {
  return app.chat.key === key && app.view === view && app.chat.pending === pend;
}

/* ── API-клиент ─────────────────────────────────────────────────────────── */
async function api(path, opts = {}) {
  const headers = Object.assign({ 'Content-Type': 'application/json' }, opts.headers || {});
  const initData = tg() && tg().initData;
  if (initData) headers['X-Init-Data'] = initData;
  let url = path;
  const dev = new URLSearchParams(location.search).get('dev_user');
  if (dev) url += (url.includes('?') ? '&' : '?') + 'dev_user=' + dev;
  const doFetch = async () => {
    const res = await fetch(url, Object.assign({ headers }, opts));
    let body = null;
    try { body = await res.json(); } catch (e) { /* пустое тело */ }
    if (!res.ok) {
      const detail = body && (body.detail || JSON.stringify(body));
      const err = new Error(detail || 'Связь прервалась 🌙');
      err.status = res.status;
      throw err;
    }
    return body;
  };
  try {
    return await doFetch();
  } catch (err) {
    // ретрай: сетевой сбой — всегда; 5xx — только для GET (мутации не ретраим,
    // чтобы не задвоить эффект на сервере)
    const method = (opts.method || 'GET').toUpperCase();
    const network = !err || !err.status;
    const retriable = network || (method === 'GET' && err.status >= 500);
    if (retriable) {
      await new Promise(r => setTimeout(r, 600));
      try { return await doFetch(); } catch (e2) { throw err; }
    }
    throw err;
  }
}

const esc = s => String(s == null ? '' : s).replace(/[&<>"]/g,
  c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));

// Rich-escape для серверного текста (чат-история, ответы LLM, отчёты):
// сначала всё экранируем, затем восстанавливаем ТОЛЬКО закрытые пары <b>/<i>
// из их экранированной формы. <script>, onerror=, атрибуты остаются текстом.
const rich = s => esc(s).replace(/&lt;(\/?)(b|i)&gt;/g, '<$1$2>');
// rich + markdown-жирный **...** → <b> (для ИИ-разборов).
const richMd = s => rich(s).replace(/\*\*(.+?)\*\*/g, '<b>$1</b>');

const fmtDate = () => new Date().toLocaleDateString('ru-RU',
  { weekday: 'long', day: 'numeric', month: 'long' });

const fmtDay = iso => {
  const d = new Date(iso + 'T00:00:00');
  return d.toLocaleDateString('ru-RU', { day: 'numeric', month: 'short' });
};

// арабский номер аркана → римская цифра (для «настоящей» карты)
function toRoman(n) {
  let v = parseInt(n, 10);
  if (!isFinite(v) || v < 0) return String(n || '');
  const map = [[1000,'M'],[900,'CM'],[500,'D'],[400,'CD'],[100,'C'],[90,'XC'],[50,'L'],[40,'XL'],[10,'X'],[9,'IX'],[5,'V'],[4,'IV'],[1,'I']];
  let out = '';
  for (const [num, sym] of map) { while (v >= num) { out += sym; v -= num; } }
  return out || '0';
}

