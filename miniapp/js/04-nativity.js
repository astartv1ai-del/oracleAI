/* ── OracleAI natal wheel: canonical chart data → accessible responsive SVG ── */
function nativitySvg(c, size = 260) {
  const planets = Array.isArray(c?.planets) ? c.planets : [];
  const houses = Array.isArray(c?.houses) ? c.houses : [];
  const aspects = Array.isArray(c?.aspects) ? c.aspects : [];
  const nodes = Array.isArray(c?.nodes) ? c.nodes : [];
  const sun = c?.sun || {};
  const asc = c?.ascendant || {};
  const view = 320;
  const cx = view / 2;
  const cy = view / 2;
  const outer = 136;
  const zodiac = 126;
  const planetLane = 101;
  const nodeLane = 119;
  const labelLane = 151;

  const signOrder = ['Овен','Телец','Близнецы','Рак','Лев','Дева','Весы','Скорпион','Стрелец','Козерог','Водолей','Рыбы'];
  const signGlyphs = { Овен:'♈', Телец:'♉', Близнецы:'♊', Рак:'♋', Лев:'♌', Дева:'♍', Весы:'♎', Скорпион:'♏', Стрелец:'♐', Козерог:'♑', Водолей:'♒', Рыбы:'♓' };
  const aspectStyles = {
    'соединение': { color:'#e6c178', dash:'', width:1.8 },
    'оппозиция': { color:'#ff7b86', dash:'5 3', width:1.25 },
    'трин': { color:'#9ee6cf', dash:'2 3', width:1.35 },
    'квадрат': { color:'#b99cff', dash:'1 3', width:1.55 },
    'секстиль': { color:'#7fc8ff', dash:'7 3', width:1.2 },
  };
  const aspectCodeToLabel = {
    conjunction:'соединение', opposition:'оппозиция', trine:'трин', square:'квадрат', sextile:'секстиль',
  };
  const finite = value => Number.isFinite(Number(value));
  const deg = value => {
    const n = Number(value);
    return Number.isFinite(n) ? ((n % 360) + 360) % 360 : null;
  };
  const polar = (degree, radius) => {
    const radians = (degree - 90) * Math.PI / 180;
    return [cx + Math.cos(radians) * radius, cy + Math.sin(radians) * radius];
  };
  const escText = value => (typeof esc === 'function' ? esc(String(value ?? '')) : String(value ?? '').replace(/[&<>"']/g, ch => ({ '&':'&amp;', '<':'&lt;', '>':'&gt;', '"':'&quot;', "'":'&#39;' }[ch])));
  const pointDegree = point => {
    if (finite(point?.abs_deg)) return deg(point.abs_deg);
    const signIndex = signOrder.indexOf(point?.sign);
    return signIndex >= 0 && finite(point?.deg) ? deg(signIndex * 30 + Number(point.deg)) : null;
  };
  const pointName = point => String(point?.name || 'точка');

  // Spread close points into deterministic radial lanes. The angular order is
  // stable, so the same chart always renders the same visual composition.
  const distribute = (items, baseRadius, minGap = 8) => {
    const rows = items.map((item, index) => ({ item, index, degree: pointDegree(item) }))
      .filter(row => row.degree !== null)
      .sort((a, b) => a.degree - b.degree);
    const lanes = [baseRadius, baseRadius - 13, baseRadius + 13];
    rows.forEach((row, index) => {
      const previous = rows[index - 1];
      const gap = previous ? Math.min((row.degree - previous.degree + 360) % 360, 360) : 360;
      row.lane = previous && gap < minGap ? (previous.lane + 1) % lanes.length : 0;
      row.radius = lanes[row.lane];
    });
    return rows;
  };

  const circle = (r, className, extra = '') => `<circle cx="${cx}" cy="${cy}" r="${r}" class="${className}" ${extra}/>`;
  const arcPath = (start, end, r) => {
    const s = polar(start, r);
    const e = polar(end, r);
    const sweep = (end - start + 360) % 360;
    const large = sweep > 180 ? 1 : 0;
    return `M ${s[0].toFixed(2)} ${s[1].toFixed(2)} A ${r} ${r} 0 ${large} 1 ${e[0].toFixed(2)} ${e[1].toFixed(2)}`;
  };

  const signRing = signOrder.map((sign, index) => {
    const angle = index * 30 + 15;
    const [x, y] = polar(angle, labelLane);
    return `<g class="n-sign" aria-label="${escText(sign)}">
      <text x="${x.toFixed(2)}" y="${(y + 4).toFixed(2)}" text-anchor="middle" class="n-sign-glyph">${signGlyphs[sign]}</text>
      <text x="${x.toFixed(2)}" y="${(y + 15).toFixed(2)}" text-anchor="middle" class="n-sign-name">${escText(sign)}</text>
    </g>`;
  }).join('');

  const houseArcs = houses.length === 12 ? houses.map((house, index) => {
    const start = pointDegree(house) ?? index * 30;
    const next = pointDegree(houses[(index + 1) % houses.length]) ?? ((index + 1) * 30);
    const end = next <= start ? next + 360 : next;
    const cusp = polar(start, zodiac + 2);
    return `<g class="n-house" aria-label="${house.n || index + 1}-й дом">
      <path d="${arcPath(start, end, zodiac)}" />
      <line x1="${cx}" y1="${cy}" x2="${cusp[0].toFixed(2)}" y2="${cusp[1].toFixed(2)}" />
    </g>`;
  }).join('') : '';

  const houseLabels = houses.map((house, index) => {
    const angle = pointDegree(house) ?? index * 30;
    const [x, y] = polar(angle + 8, outer - 5);
    return `<text x="${x.toFixed(2)}" y="${(y + 3).toFixed(2)}" text-anchor="middle" class="n-house-number">${escText(house.n || index + 1)}</text>`;
  }).join('');

  const planetRows = distribute(planets, planetLane);
  const planetPositions = new Map();
  const planetDots = planetRows.map((row, index) => {
    const p = row.item;
    const [x, y] = polar(row.degree, row.radius);
    planetPositions.set(pointName(p), [x, y, row.degree]);
    const sym = planetGlyph(p.name) || signGlyphs[p.sign] || '•';
    const retro = p.retro ? '℞' : '';
    const label = `${pointName(p)} — ${p.sign || 'знак неизвестен'}${p.house ? `, ${p.house}-й дом` : ''}`;
    return `<g class="n-in n-planet" data-act="planet" data-p="${row.index}" data-el="${escText(signElement(p.sign))}" tabindex="0" role="button" aria-label="${escText(label)}" style="animation-delay:${360 + index * 45}ms">
      <title>${escText(label)}</title>
      <circle cx="${x.toFixed(2)}" cy="${y.toFixed(2)}" r="13" class="n-planet-orb" />
      <text x="${x.toFixed(2)}" y="${(y + 5).toFixed(2)}" text-anchor="middle" class="n-planet-glyph">${sym}</text>
      <text x="${x.toFixed(2)}" y="${(y + 20).toFixed(2)}" text-anchor="middle" class="n-planet-label">${size >= 190 ? escText(p.name) : ''}</text>
      ${retro ? `<text x="${(x + 9).toFixed(2)}" y="${(y - 9).toFixed(2)}" class="n-retro">${retro}</text>` : ''}
    </g>`;
  }).join('');

  const nodeRows = distribute(nodes, nodeLane, 10);
  const nodeDots = nodeRows.map((row, index) => {
    const n = row.item;
    const [x, y] = polar(row.degree, row.radius);
    const sym = planetGlyph(n.name) || (String(n.name).includes('Кету') ? '☋' : '☊');
    const label = `${pointName(n)} — ${n.sign || 'знак неизвестен'}`;
    return `<g class="n-in n-node" aria-label="${escText(label)}" style="animation-delay:${620 + index * 70}ms">
      <title>${escText(label)}</title>
      <circle cx="${x.toFixed(2)}" cy="${y.toFixed(2)}" r="9" />
      <text x="${x.toFixed(2)}" y="${(y + 3).toFixed(2)}" text-anchor="middle">${sym}</text>
    </g>`;
  }).join('');

  const aspectLines = aspects.slice(0, 12).map((aspect, index) => {
    const p1 = planetPositions.get(aspect.p1);
    const p2 = planetPositions.get(aspect.p2);
    if (!p1 || !p2 || p1[2] === null || p2[2] === null) return '';
    const label = aspectCodeToLabel[aspect.code] || aspect.aspect || '';
    const style = aspectStyles[label] || { color:'#9f9ab7', dash:'2 4', width:1 };
    return `<line class="n-in n-aspect" style="animation-delay:${820 + index * 55}ms" x1="${p1[0].toFixed(2)}" y1="${p1[1].toFixed(2)}" x2="${p2[0].toFixed(2)}" y2="${p2[1].toFixed(2)}" stroke="${style.color}" stroke-width="${style.width}" ${style.dash ? `stroke-dasharray="${style.dash}"` : ''} aria-label="${escText(`${aspect.p1} ${label} ${aspect.p2}`)}" />`;
  }).join('');

  const ascLabel = asc?.sign ? `<text x="${cx}" y="${cy - outer + 16}" text-anchor="middle" class="n-angle">AC · ${escText(asc.sign)}</text>` : '';
  const sunLabel = `<g class="n-in n-core" style="animation-delay:240ms" aria-label="Солнце в ${escText(sun.sign || '')}">
    <title>Солнце в ${escText(sun.sign || '')}</title>
    <circle cx="${cx}" cy="${cy}" r="29" class="n-sun-core" />
    <text x="${cx}" y="${cy - 5}" text-anchor="middle" class="n-sun-glyph">${sun.symbol || '☉'}</text>
    <text x="${cx}" y="${cy + 12}" text-anchor="middle" class="n-sun-sign">${escText(sun.sign || '')}</text>
  </g>`;

  return `<svg viewBox="0 0 ${view} ${view}" role="img" aria-label="Индивидуальное колесо натальной карты" style="width:100%;max-width:${size}px;height:auto;margin:0 auto;display:block;overflow:visible">
    <defs>
      <filter id="oracle-wheel-glow" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="3" result="blur"/><feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
    </defs>
    <g class="n-wheel" data-contract-version="${escText(c?.calculation?.contract_version || '')}">
      ${circle(outer, 'n-wheel-ring')}
      ${circle(zodiac, 'n-zodiac-ring')}
      ${circle(planetLane + 16, 'n-aspect-ring')}
      ${signRing}
      ${houseArcs}
      ${houseLabels}
      ${aspectLines}
      ${planetDots}
      ${nodeDots}
      ${ascLabel}
      ${sunLabel}
    </g>
  </svg>`;
}
