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

/* Семантический отклик для общих UI-переходов. Локальные сценарии по-прежнему
   могут выбирать свой более выразительный сигнал на успех или ошибку. */
function tactile(event = 'select') {
  const pattern = {
    select: { kind: 'light', pulse: null },
    open: { kind: 'soft', pulse: 12 },
    reveal: { kind: 'soft', pulse: 16 },
    complete: { kind: 'success', pulse: [10, 40, 18] },
    error: { kind: 'error', pulse: null },
  }[event] || { kind: 'light', pulse: null };
  haptic(pattern.kind);
  if (pattern.pulse) vb(pattern.pulse);
}

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

const oracleLang = () => (window.app && app.me && app.me.lang) ||
  localStorage.getItem('oracle_lang') || 'ru';

// Русский род используем только при явном выборе; отсутствие значения не означает женский род.
function gendered(user, feminine, masculine, neutral) {
  if (user && user.gender === 'f') return feminine;
  if (user && user.gender === 'm') return masculine;
  return neutral || feminine;
}

const I18N = {
  ru: {
    today: 'Сегодня', chats: 'Диалоги', mine: 'Моё', ritual: 'Ритуал', guides: 'Проводники', profile: 'Профиль',
    language: 'Язык интерфейса', russian: 'Русский', english: 'English',
    languageCopy: 'Меняет язык основных экранов и новых сообщений. Сохранённые записи остаются на языке, на котором были созданы.',
    gender: 'Пол', female: 'Женский', male: 'Мужской', notSpecified: 'Не указан',
    femaleCopy: 'Обращения в женском роде', maleCopy: 'Обращения в мужском роде',
    notSpecifiedCopy: 'Нейтральные формулировки',
    genderCopy: 'Помогает Оракулу обращаться к тебе в правильном роде. Это можно изменить или не указывать.',
    changeGender: 'Изменить пол', saved: 'Сохранено', changeLanguage: 'Сменить язык',
  },
  en: {
    today: 'Today', chats: 'Guides', mine: 'Mine', ritual: 'Ritual', guides: 'Guides', profile: 'Profile',
    language: 'App language', russian: 'Русский', english: 'English',
    languageCopy: 'Changes the language of core screens and new messages. Saved entries stay in their original language.',
    gender: 'Gender', female: 'Female', male: 'Male', notSpecified: 'Not specified',
    femaleCopy: 'Feminine forms of address', maleCopy: 'Masculine forms of address',
    notSpecifiedCopy: 'Gender-neutral wording',
    genderCopy: 'Helps Oracle use the right form of address. You can change it later or leave it unspecified.',
    changeGender: 'Change gender', saved: 'Saved', changeLanguage: 'Change language',
  },
};
const t = (key, fallback = '') => (I18N[oracleLang()] || I18N.ru)[key] || fallback || key;

// P3: детерминированный вариант без сторонних трекеров. В событие уходят только
// имя эксперимента и вариант; вопрос, дневник и другие личные данные не передаются.
function experimentVariant(experiment, variants = ['control', 'variant']) {
  const subject = String((window.app && app.me && app.me.tg_id) || 'anonymous');
  let hash = 2166136261;
  for (const char of `${experiment}:${subject}`) hash = Math.imul(hash ^ char.charCodeAt(0), 16777619);
  return variants[(hash >>> 0) % variants.length];
}
function trackExperiment(experiment, variant) {
  const key = `oracle_exp:${experiment}:${variant}`;
  if (sessionStorage.getItem(key)) return;
  sessionStorage.setItem(key, '1');
  api('/api/experiment-exposure', { method: 'POST', body: JSON.stringify({ experiment, variant }) }).catch(() => {});
}

const fmtDate = () => new Date().toLocaleDateString(oracleLang() === 'en' ? 'en-US' : 'ru-RU',
  { weekday: 'long', day: 'numeric', month: 'long' });

const fmtDay = iso => {
  const d = new Date(iso + 'T00:00:00');
  return d.toLocaleDateString(oracleLang() === 'en' ? 'en-US' : 'ru-RU', { day: 'numeric', month: 'short' });
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

