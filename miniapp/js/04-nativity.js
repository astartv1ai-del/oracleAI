/* nativity: SVG-колесо натальной карты */
/* ── SVG-колесо натальной карты — полный визуал по данным эфемерид ─── */
function nativitySvg(c, size = 260) {
  const planets = c.planets || [];
  const houses = c.houses || [];
  const aspects = c.aspects || [];
  const nodes = c.nodes || [];
  const sun = c.sun || {};
  const asc = c.ascendant || {};
  const cx = size / 2, cy = size / 2;
  // геометрия пропорциональна viewBox: радиусы захардкожены под 260, при
  // size=160 без scale круг обрезается (B1)
  const scale = size / 260;
  const r = 110 * scale;

  // 12 знаков зодиака по кругу (начиная с Овна в любом месте — используем abs_deg планет для позиционирования)
  const signOrder = ['Овен','Телец','Близнецы','Рак','Лев','Дева','Весы','Скорпион','Стрелец','Козерог','Водолей','Рыбы'];
  const signGlyphs = { Овен:'♈', Телец:'♉', Близнецы:'♊', Рак:'♋', Лев:'♌', Дева:'♍', Весы:'♎', Скорпион:'♏', Стрелец:'♐', Козерог:'♑', Водолей:'♒', Рыбы:'♓' };

  // Позиция по абсолютному градусу (0-360) → угол для SVG (0° справа, против часовой)
  const angleDeg = (absDeg, offset = 0) => (absDeg - offset) * Math.PI / 180;
  const polar = (deg, rad) => [cx + Math.cos(angleDeg(deg, 0)) * rad, cy - Math.sin(angleDeg(deg, 0)) * rad];

  // 12 делений круга (дома) как дуги
  const houseArcs = houses.map((h, i) => {
    const startDeg = h.abs_deg || ((i * 30) % 360);
    const endDeg = ((startDeg + 30) % 360);
    const rOut = r + 6 * scale;
    const rIn = r - 6 * scale;
    // Простая дуга через path (дуга по кругу)
    const p1 = polar(startDeg, rOut);
    const p2 = polar(endDeg, rOut);
    // Упрощённая дуга для визуала (маленький сегмент круга)
    return `<path class="n-in" style="animation-delay:${(i * 30)}ms" d="M ${p1[0]} ${p1[1]} A ${rOut} ${rOut} 0 0 1 ${p2[0]} ${p2[1]} L ${(p2[0] + (polar(endDeg, rIn)[0]-p2[0])*0.7)} ${(p2[1] + (polar(endDeg, rIn)[1]-p2[1])*0.7)} A ${rIn} ${rIn} 0 0 0 ${(p1[0] + (polar(startDeg, rIn)[0]-p1[0])*0.7)} ${(p1[1] + (polar(startDeg, rIn)[1]-p1[1])*0.7)} Z" fill="none" stroke="rgba(167,139,250,.15)" stroke-width=".8"/>`;
  }).join('');

  // Планеты как круги с планетным символом (T5: сразу видно, где какая)
  const planetDots = planets.map((p, i) => {
    const [x, y] = polar(p.abs_deg || 0, r - 22 * scale);
    const sym = planetGlyph(p.name) || signGlyphs[p.sign] || '•';
    const retro = p.retro ? '℞' : '';
    return `<g class="n-in n-planet" data-act="planet" data-p="${i}" data-el="${signElement(p.sign)}" style="animation-delay:${(360 + i * 45)}ms;cursor:pointer">
      <circle cx="${x}" cy="${y}" r="${(13 * scale) + (sym.length > 1 ? 1 : 0)}" fill="rgba(24,22,48,.8)" stroke="#e6c178" stroke-width="1.5" filter="drop-shadow(0 0 5px rgba(230,193,120,.35))"/>
      <text x="${x}" y="${y+4}" text-anchor="middle" font-family="Cinzel, Georgia, serif" font-size="13" fill="#ffd98f" font-weight="700">${sym}</text>
      ${size >= 200 ? `<text x="${x}" y="${y + 16 * scale}" text-anchor="middle" font-size="6.5" fill="#a49cc8" font-family="Arial, sans-serif">${esc(p.name)}</text>` : ''}
      ${retro ? `<text x="${x}" y="${y-7}" text-anchor="middle" font-size="7" fill="#ff6b6b" font-weight="700">${retro}</text>` : ''}
    </g>`;
  }).join('');

  // Узлы (Раху, Кету, Лилит) — меньшие круги своим символом
  const nodeDots = nodes.map((n, i) => {
    const nodeSignIdx = signOrder.indexOf(n.sign);
    const nodeAbs = n.abs_deg || (n.deg != null ? n.deg + (nodeSignIdx >= 0 ? nodeSignIdx * 30 : 0) : 0);
    const [x, y] = polar(nodeAbs, r - 8 * scale);
    const sym = planetGlyph(n.name) || signGlyphs[n.sign] || '☊';
    return `<g class="n-in" style="animation-delay:${(620 + i * 70)}ms">
      <circle cx="${x}" cy="${y}" r="${9 * scale}" fill="rgba(24,22,48,.7)" stroke="#a78bfa" stroke-width="1.2" filter="drop-shadow(0 0 4px rgba(167,139,250,.4))"/>
      <text x="${x}" y="${y+3}" text-anchor="middle" font-family="Cinzel, Georgia, serif" font-size="9" fill="#a78bfa" font-weight="600">${sym}</text>
    </g>`;
  }).join('');

  // Аспекты — простые линии между планетами (берём первые 8 для читаемости)
  const aspectLines = (aspects.slice ? aspects.slice(0, 8).map((a, i) => {
    const p1 = planets.find(pl => pl.name === a.p1);
    const p2 = planets.find(pl => pl.name === a.p2);
    if (!p1 || !p2 || !p1.abs_deg || !p2.abs_deg) return '';
    const [x1, y1] = polar(p1.abs_deg, r - 22 * scale);
    const [x2, y2] = polar(p2.abs_deg, r - 22 * scale);
    const color = a.glyph === '△' ? 'rgba(230,193,120,.55)' : a.glyph === '□' ? 'rgba(167,139,250,.55)' : a.glyph === '☍' ? 'rgba(255,107,107,.55)' : 'rgba(255,255,255,.15)';
    return `<line class="n-in" style="animation-delay:${(820 + i * 60)}ms" x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" stroke="${color}" stroke-width="1.2" stroke-dasharray="3 2" opacity=".9"/>`;
  }).join('') : '');

  // Домашняя круговая сетка с номерами домов
  const houseLabels = houses.map(h => {
    const [lx, ly] = polar(h.abs_deg || 0, r + 14 * scale);
    return `<text x="${lx}" y="${ly}" text-anchor="middle" font-size="7" fill="#a49cc8" font-family="Arial, sans-serif">${h.n || ''}</text>`;
  }).join('');

  // Солнце в центре
  const sunCenter = `<g>
    <circle cx="${cx}" cy="${cy}" r="${28 * scale}" fill="rgba(230,193,120,.08)" stroke="#e6c178" stroke-width="1.5" opacity=".9"/>
    <text x="${cx}" y="${cy-6}" text-anchor="middle" font-family="Cinzel, Georgia, serif" font-size="22" fill="#ffd98f">${sun.symbol || '☉'}</text>
    <text x="${cx}" y="${cy+10}" text-anchor="middle" font-size="10" fill="#a49cc8" font-family="Arial, sans-serif">${sun.sign || ''}</text>
  </g>`;

  // Асцендент — метка в верхней части круга: внутри колеса, чтобы не вылезать
  // за viewBox на малых size (B1)
  const ascHtml = asc && asc.sign ? `<text x="${cx}" y="${cy - r + 14 * scale}" text-anchor="middle" font-size="9" fill="#a78bfa" font-family="Arial, sans-serif" letter-spacing="1px">AC · ${esc(asc.sign)}</text>` : '';

  return `<svg viewBox="0 0 ${size} ${size}" xmlns="http://www.w3.org/2000/svg" aria-hidden="true" style="width:100%;max-width:280px;height:auto;margin:0 auto;display:block;">
    <defs>
      <filter id="glow" x="-50%" y="-50%" width="200%" height="200%">
        <feGaussianBlur stdDeviation="3" result="blur"/>
        <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
      </filter>
    </defs>
    <!-- круг зодиака -->
    <circle cx="${cx}" cy="${cy}" r="${r}" fill="none" stroke="rgba(230,193,120,.15)" stroke-width=".8"/>
    <circle cx="${cx}" cy="${cy}" r="${r-10}" fill="none" stroke="rgba(167,139,250,.1)" stroke-width="1" stroke-dasharray="4 3"/>
    <!-- деления домов -->
    ${houseArcs}
    <!-- аспекты -->
    ${aspectLines}
    <!-- планеты -->
    ${planetDots}
    <!-- узлы -->
    ${nodeDots}
    <!-- номера домов -->
    ${houseLabels}
    <!-- солнце -->
    ${sunCenter}
    ${ascHtml}
  </svg>`;
}

