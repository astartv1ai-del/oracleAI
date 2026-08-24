/* nativity: premium SVG-колесо натальной карты */
function nativitySvg(c, size = 260) {
  const planets = Array.isArray(c.planets) ? c.planets : [];
  const houses = Array.isArray(c.houses) ? c.houses : [];
  const aspects = Array.isArray(c.aspects) ? c.aspects : [];
  const nodes = Array.isArray(c.nodes) ? c.nodes.filter(n => /Раху|Кету/.test(n.name || '')) : [];
  const sun = c.sun || {};
  const asc = c.ascendant || {};
  const cx = size / 2, cy = size / 2;
  const scale = size / 260;
  const outer = size * .455;
  const zodiac = size * .385;
  const houseRing = size * .315;
  const aspectRing = size * .255;
  const markerBase = size * .285;
  const markerStep = Math.max(7 * scale, size * .035);
  const clamp = (value, min, max) => Math.max(min, Math.min(max, value));
  const norm = value => ((Number(value) || 0) % 360 + 360) % 360;
  const angle = deg => (norm(deg) - 90) * Math.PI / 180;
  const polar = (deg, radius) => {
    const a = angle(deg);
    return [cx + Math.cos(a) * radius, cy + Math.sin(a) * radius];
  };
  const delta = (a, b) => Math.abs(((norm(a) - norm(b) + 540) % 360) - 180);
  const fmt = value => Number(value).toFixed(1);
  const arcPath = (start, end, r0, r1) => {
    let sweep = (norm(end) - norm(start) + 360) % 360;
    if (sweep < .1) sweep = 30;
    const large = sweep > 180 ? 1 : 0;
    const a0 = polar(start, r1), b0 = polar(start + sweep, r1);
    const a1 = polar(start, r0), b1 = polar(start + sweep, r0);
    return `M ${fmt(a0[0])} ${fmt(a0[1])} A ${fmt(r1)} ${fmt(r1)} 0 ${large} 1 ${fmt(b0[0])} ${fmt(b0[1])} L ${fmt(b1[0])} ${fmt(b1[1])} A ${fmt(r0)} ${fmt(r0)} 0 ${large} 0 ${fmt(a1[0])} ${fmt(a1[1])} Z`;
  };

  const signOrder = ['Овен','Телец','Близнецы','Рак','Лев','Дева','Весы','Скорпион','Стрелец','Козерог','Водолей','Рыбы'];
  const signGlyphs = { Овен:'♈', Телец:'♉', Близнецы:'♊', Рак:'♋', Лев:'♌', Дева:'♍', Весы:'♎', Скорпион:'♏', Стрелец:'♐', Козерог:'♑', Водолей:'♒', Рыбы:'♓' };
  const elementColor = { огонь:'#e9b27e', земля:'#c8b58a', воздух:'#b9b9d8', вода:'#9cc7d8' };

  // Place close points on deterministic radial and angular lanes. The label remains
  // a glyph; the full name appears in the separate interactive plaque after a tap.
  // Deterministic 2D collision avoidance: radial lanes are supplemented by
  // angular fan-out, so an extreme cluster cannot collapse onto one fallback point.
  const distribute = (entries, baseRadiusFor) => {
    const placed = [];
    const radialLanes = [0, -1, 1, -2, 2, -3, 3, -4, 4, -5, 5];
    const angleOffsets = [0];
    for (let step = 8; step <= 176; step += 8) angleOffsets.push(-step, step);
    const radiusFor = typeof baseRadiusFor === 'function' ? baseRadiusFor : () => baseRadiusFor;
    const markerRadius = entry => entry.isNode ? Math.max(6, size * .034) : Math.max(7, size * .042);
    const sorted = entries.map((entry, index) => ({
      ...entry, index: entry.index ?? index,
      deg: norm(entry.point.abs_deg_exact ?? entry.point.abs_deg ?? 0),
    })).sort((a, b) => a.deg - b.deg);
    sorted.forEach(entry => {
      const candidates = [];
      for (const offset of angleOffsets) {
        for (const lane of radialLanes) {
          const radius = clamp(radiusFor(entry) + lane * markerStep, size * .17, size * .39);
          const displayDeg = norm(entry.deg + offset);
          const [x, y] = polar(displayDeg, radius);
          const minClearance = markerRadius(entry) + size * .012;
          const collision = placed.some(item => {
            const distance = Math.hypot(item.x - x, item.y - y);
            return distance < markerRadius(item) + minClearance;
          });
          candidates.push({ ...entry, radius, displayDeg, x, y, collision });
          if (!collision) break;
        }
        if (candidates[candidates.length - 1] && !candidates[candidates.length - 1].collision) break;
      }
      const valid = candidates.find(candidate => !candidate.collision);
      if (valid) {
        placed.push(valid);
        return;
      }
      // Defensive deterministic fallback: choose the candidate with the greatest
      // minimum distance, never silently reusing the same coordinates.
      const best = candidates.reduce((winner, candidate) => {
        const nearest = placed.length ? Math.min(...placed.map(item => Math.hypot(item.x - candidate.x, item.y - candidate.y))) : Infinity;
        return !winner || nearest > winner.nearest ? { candidate, nearest } : winner;
      }, null);
      placed.push(best.candidate);
    });
    return placed;
  };

  const parts = [];
  parts.push(`<circle class="n-wheel-ring" cx="${cx}" cy="${cy}" r="${fmt(outer)}" fill="none" stroke="rgba(230,193,120,.52)" stroke-width=".8"/>`);
  parts.push(`<circle class="n-wheel-ring n-wheel-ring--inner" cx="${cx}" cy="${cy}" r="${fmt(zodiac)}" fill="none" stroke="rgba(218,211,240,.24)" stroke-width=".7"/>`);
  parts.push(`<circle class="n-wheel-ring n-wheel-ring--core" cx="${cx}" cy="${cy}" r="${fmt(size * .16)}" fill="rgba(8,7,18,.28)" stroke="rgba(218,211,240,.16)" stroke-width=".7"/>`);

  // Zodiac sectors and restrained elemental accents.
  for (let i = 0; i < 12; i += 1) {
    const start = i * 30;
    const mid = start + 15;
    const glyphPoint = polar(mid, outer - size * .045);
    const sign = signOrder[i];
    const color = elementColor[{ огонь:'огонь', земля:'земля', воздух:'воздух', вода:'вода' }[(['огонь','земля','воздух','вода'][i % 4])] || 'воздух'];
    parts.push(`<path class="n-sign-sector" d="${arcPath(start, start + 30, zodiac, outer - size * .022)}" fill="${color}" opacity=".055"/>`);
    const tickA = polar(start, zodiac), tickB = polar(start, outer - size * .025);
    parts.push(`<line class="n-zodiac-tick" x1="${fmt(tickA[0])}" y1="${fmt(tickA[1])}" x2="${fmt(tickB[0])}" y2="${fmt(tickB[1])}" stroke="rgba(218,211,240,.26)" stroke-width=".65"/>`);
    parts.push(`<text class="n-sign-glyph" x="${fmt(glyphPoint[0])}" y="${fmt(glyphPoint[1] + size * .014)}" text-anchor="middle" fill="${color}" font-size="${Math.max(10, size * .052)}">${signGlyphs[sign]}</text>`);
  }

  const houseMap = new Map(houses.map(h => [Number(h.n), h]));
  const housePoints = houses.length ? houses : Array.from({ length: 12 }, (_, i) => ({ n: i + 1, abs_deg: i * 30 }));
  housePoints.forEach((house, i) => {
    const start = Number.isFinite(Number(house.abs_deg)) ? Number(house.abs_deg) : i * 30;
    const p0 = polar(start, size * .16), p1 = polar(start, houseRing);
    parts.push(`<line class="n-house-line" style="animation-delay:${i * 24}ms" x1="${fmt(p0[0])}" y1="${fmt(p0[1])}" x2="${fmt(p1[0])}" y2="${fmt(p1[1])}" stroke="rgba(218,211,240,.18)" stroke-width=".6" stroke-dasharray="${houses.length ? '2 2' : '1 3'}"/>`);
    if (houses.length) {
      const label = polar(start + 13, size * .205);
      parts.push(`<text class="n-house-label" x="${fmt(label[0])}" y="${fmt(label[1] + size * .01)}" text-anchor="middle" font-size="${Math.max(7, size * .031)}" fill="rgba(180,169,210,.76)">${house.n || i + 1}</text>`);
    }
  });

  const allEntries = [
    ...planets.map((point, index) => ({ point, index, isNode: false })),
    ...nodes.map((point, index) => ({ point, index, isNode: true })),
  ];
  const placedAll = distribute(allEntries, entry => entry.isNode ? size * .335 : markerBase);
  const placedPlanets = placedAll.filter(item => !item.isNode);
  const placedNodes = placedAll.filter(item => item.isNode);
  const planetPositions = new Map();
  placedPlanets.forEach(item => {
    const p = item.point;
    const [x, y] = [item.x, item.y];
    planetPositions.set(p.name, [x, y]);
    const glyph = planetGlyph(p.name) || '•';
    const color = elementColor[p.element] || '#e6c178';
    const retro = p.retro ? '℞' : '';
    parts.push(`<g class="n-in n-planet" data-act="planet" data-p="${item.index}" data-el="${signElement(p.sign)}" aria-label="${esc(p.name || '')}" style="animation-delay:${360 + item.index * 42}ms;cursor:pointer">
      <circle cx="${fmt(x)}" cy="${fmt(y)}" r="${Math.max(7, size * .042)}" fill="rgba(18,17,34,.94)" stroke="${color}" stroke-width="${Math.max(.8, size * .004)}"/>
      <text x="${fmt(x)}" y="${fmt(y + size * .015)}" text-anchor="middle" font-family="Cinzel, Georgia, serif" font-size="${Math.max(10, size * .05)}" fill="${color}">${glyph}</text>
      ${retro ? `<text x="${fmt(x + size * .027)}" y="${fmt(y - size * .025)}" font-size="${Math.max(6, size * .027)}" fill="#e99b96">℞</text>` : ''}
    </g>`);
  });

  placedNodes.forEach(item => {
    const n = item.point;
    const [x, y] = [item.x, item.y];
    const glyph = planetGlyph(n.name) || (n.name && n.name.startsWith('Кету') ? '☋' : '☊');
    parts.push(`<g class="n-in n-node" aria-label="${esc(n.name || '')}" style="animation-delay:${620 + item.index * 70}ms">
      <circle cx="${fmt(x)}" cy="${fmt(y)}" r="${Math.max(6, size * .034)}" fill="rgba(20,16,39,.94)" stroke="#a78bfa" stroke-width=".9"/>
      <text x="${fmt(x)}" y="${fmt(y + size * .012)}" text-anchor="middle" font-family="Cinzel, Georgia, serif" font-size="${Math.max(8, size * .037)}" fill="#c7b1ff">${glyph}</text>
    </g>`);
  });

  // Aspect geometry uses the exact same planet coordinates as markers.
  aspects.slice(0, 10).forEach((a, i) => {
    const p1 = planetPositions.get(a.p1), p2 = planetPositions.get(a.p2);
    if (!p1 || !p2) return;
    const color = a.glyph === '△' ? '#e6c178' : a.glyph === '□' ? '#a78bfa' : a.glyph === '☍' ? '#e99b96' : '#b8b1c9';
    const dash = a.glyph === '△' || a.glyph === '⚹' ? 'none' : '3 3';
    parts.push(`<line class="n-aspect-line n-in" style="animation-delay:${820 + i * 50}ms" x1="${fmt(cx + (p1[0] - cx) * aspectRing / markerBase)}" y1="${fmt(cy + (p1[1] - cy) * aspectRing / markerBase)}" x2="${fmt(cx + (p2[0] - cx) * aspectRing / markerBase)}" y2="${fmt(cy + (p2[1] - cy) * aspectRing / markerBase)}" stroke="${color}" stroke-width="${Math.max(.55, size * .003)}" stroke-dasharray="${dash}" opacity=".55"/>`);
  });

  const sunPoint = sun.symbol || '☉';
  parts.push(`<g class="n-in n-core" style="animation-delay:240ms">
    <circle cx="${cx}" cy="${cy}" r="${fmt(size * .105)}" fill="rgba(230,193,120,.08)" stroke="rgba(230,193,120,.62)" stroke-width=".9"/>
    <text x="${cx}" y="${fmt(cy - size * .018)}" text-anchor="middle" font-family="Cinzel, Georgia, serif" font-size="${Math.max(16, size * .085)}" fill="#ffd98f">${esc(sunPoint)}</text>
    <text x="${cx}" y="${fmt(cy + size * .045)}" text-anchor="middle" font-size="${Math.max(7, size * .034)}" fill="#aaa0c9">${esc(sun.sign || '')}</text>
  </g>`);
  if (asc && asc.sign) {
    parts.push(`<text class="n-asc-label" x="${cx}" y="${fmt(cy - outer + size * .075)}" text-anchor="middle" font-size="${Math.max(7, size * .034)}" fill="#c7b1ff" letter-spacing=".7">AC · ${esc(asc.sign)}</text>`);
  }

  return `<svg viewBox="0 0 ${size} ${size}" preserveAspectRatio="xMidYMid meet" xmlns="http://www.w3.org/2000/svg" aria-hidden="true" style="width:100%;max-width:360px;height:auto;margin:0 auto;display:block;overflow:visible">${parts.join('')}</svg>`;
}
