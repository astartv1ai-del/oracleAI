const fs = require('fs');
const vm = require('vm');
const source = fs.readFileSync('miniapp/js/04-nativity.js', 'utf8');
const context = {
  planetGlyph: name => ({Солнце:'☉', Луна:'☽', Меркурий:'☿', Марс:'♂', 'Раху (Северный узел)':'☊'}[name] || ''),
  signElement: sign => ({Овен:'fire', Телец:'earth', Весы:'air', Рак:'water'}[sign] || ''),
  esc: value => String(value).replace(/[&<>"']/g, ch => ({'&':'&amp;', '<':'&lt;', '>':'&gt;', '"':'&quot;', "'":'&#39;'}[ch])),
};
vm.createContext(context);
vm.runInContext(`${source}\nthis.nativitySvg = nativitySvg;`, context);
const chart = {
  calculation: {contract_version: 1},
  sun: {symbol: '☉', sign: 'Овен'},
  ascendant: {sign: 'Весы'},
  planets: [
    {name: 'Солнце', sign: 'Овен', abs_deg: 0, house: 1},
    {name: 'Луна', sign: 'Овен', abs_deg: 1, house: 1},
    {name: 'Меркурий', sign: 'Овен', abs_deg: 2, house: 1},
    {name: 'Марс', sign: 'Весы', abs_deg: 180, house: 7},
  ],
  nodes: [{name: 'Раху (Северный узел)', sign: 'Телец', abs_deg: 34}],
  houses: Array.from({length: 12}, (_, i) => ({n: i + 1, abs_deg: i * 30})),
  aspects: [
    {p1: 'Солнце', p2: 'Марс', aspect: 'оппозиция', orb: 1},
    {p1: 'Луна', p2: 'Меркурий', aspect: 'соединение', orb: 1},
  ],
};
const svg = context.nativitySvg(chart, 210);
for (const token of ['viewBox="0 0 320 320"', 'n-sign-glyph', 'n-house', 'n-aspect', 'n-node', 'data-contract-version="1"']) {
  if (!svg.includes(token)) throw new Error(`missing SVG token: ${token}`);
}
if (!svg.includes('x1="') || !svg.includes('x2="')) throw new Error('aspect geometry missing');
console.log(`nativity SVG smoke ok (${svg.length} chars)`);
