/* art: SVG/визуал-генераторы — портрет агента, фазы луны, кольца, карьерные окна */
/* SVG-фаза луны по эмодзи от сервера (🌑…🌘): освещённая доля и терминатор.
   Почти точная визуализация классического цикла без эфемерид. */

// Персонаж агента: портрет-арт из /static/img/agents/{code}.jpg + анимированный
// проп-атрибут. cheer=true — персонаж «радуется» свежему ответу агента.
const AGENT_PROPS = {
  oracle: '🔮', astro: '🌠', tarot: '🃏', coach: '🍃', numero: '🌀', keeper: '🪶',
};
function agentSprite(a, cheer) {
  if (!a) return '';
  const ac = a.accent || '#e6c178';
  const prop = AGENT_PROPS[a.code] || a.emoji;
  return `<span class="agent-sprite${cheer ? ' cheer' : ''}" style="--ac:${esc(ac)}" role="img" aria-label="${esc(a.name || '')}">
      <img class="agent-face" src="/static/img/agents/${esc(a.code)}.jpg" alt="${esc(a.name || '')}" loading="eager">
      <span class="as-prop">${esc(prop)}</span>
    </span>`;
}

// Истинная фаза луны как SVG: внешняя дуга диска + терминатор-эллипс.
// lit=0 новолуние, 1 полнолуние; right=false — свет слева (убывающая).
// Уникальный id сквозного градиента луны на каждый SVG: несколько лун на странице
// (сегодня/профиль/док) не должны конфликтовать за один #mg, иначе fill не резолвится.
let moonGradSeq = 0;
// Уникальные id свечения для «Спидометра любви» — несколько виджетов в ленте
// не должны конфликтовать за один id фильтра (аналогично moonGradSeq).
let spdSeq = 0;
function moonSvg(emoji, cls) {
  const gid = 'mg' + (++moonGradSeq);
  const ph = MOON_DISC[emoji] || { lit: 0.5, right: true };
  const r = 45, lit = Math.max(0, Math.min(1, ph.lit));
  let d;
  if (lit <= 0) d = '';
  else if (lit >= 1) d = `M0,-${r} A${r} ${r} 0 1 1 0,${r} A${r} ${r} 0 1 1 0,-${r} Z`;
  else {
    const ex = (lit >= 0.5 ? 1 : lit * 2) * r;
    d = `M0,-${r} A${r} ${r} 0 0 1 0,${r} L0,${r} A${ex} ${r} 0 0 1 0,-${r} Z`;
  }
  const flip = ph.right ? '' : ' scale(-1,1)';
  return `<svg viewBox="0 0 100 100" class="${cls || ''}" aria-hidden="true"><defs>
    <radialGradient id="${gid}" cx="45%" cy="38%" r="75%">
      <stop offset="0%" stop-color="#f8edcf"/><stop offset="55%" stop-color="#ddc795"/>
      <stop offset="100%" stop-color="#a9966a"/>
    </radialGradient></defs>
    <circle cx="50" cy="50" r="${r}" fill="#1d1838" stroke="rgba(230,193,120,.35)" stroke-width="2"/>
    ${d ? `<g transform="translate(50,50)${flip}"><path d="${d}" fill="url(#${gid})"/></g>` : ''}</svg>`;
}

/* Карьерные окна: тип действия по имени лунной фазы (данные — код, трактовка — LLM).
   Имена фаз 1-в-1 с app/core/astro.py MOON_PHASES. */
const CAREER_WIN = {
  'Новолуние': ['🚀 Старт · планируй', '#7fd4a8'],
  'Растущий серп': ['🚀 Старт · переговоры', '#7fd4a8'],
  'Первая четверть': ['⚖️ Решение', '#e6c178'],
  'Растущая Луна': ['⚡ Действие · подпись, рост', '#7fd4a8'],
  'Полнолуние': ['⚠️ Осторожно · не решай судьбоносно', '#ff8fa3'],
  'Убывающая Луна': ['✅ Завершение · долги, финалы', '#e6c178'],
  'Последняя четверть': ['✅ Завершение · отпусти лишнее', '#e6c178'],
  'Старый серп': ['🌙 Пауза · восстановление', '#8b86a3'],
};
const careerWindow = d => {
  const w = CAREER_WIN[d && d.name] || ['·', '#8b86a3'];
  return { t: w[0], c: w[1] };
};

// круговой прогресс 0–100% (маленькое SVG-кольцо)
function ringSvg(pct) {
  const r = 17, c = 2 * Math.PI * r;
  return `<svg viewBox="0 0 44 44" class="pr-svg"><circle class="pr-ring-bg" cx="22" cy="22" r="${r}"></circle><circle class="pr-ring-fg" cx="22" cy="22" r="${r}" stroke-dasharray="${c}" stroke-dashoffset="${c * (1 - Math.max(0, Math.min(100, pct || 0)) / 100)}"></circle></svg>`;
}

