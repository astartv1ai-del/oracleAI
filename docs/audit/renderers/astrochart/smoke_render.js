const fs = require('fs');
const path = require('path');
const { JSDOM } = require('jsdom');

const root = path.resolve(__dirname, 'package');
const dom = new JSDOM('<!doctype html><body><div id="chart"></div></body>');
global.window = dom.window;
global.document = dom.window.document;
global.self = dom.window;
const pkg = require(path.join(root, 'dist', 'astrochart.js'));
const Chart = pkg.default || pkg;

const profiles = {
  sparse: {
    Sun: [12.4], Moon: [78.1], Mercury: [25.8], Venus: [142.3], Mars: [201.2],
    Jupiter: [265.4], Saturn: [311.9], NNode: [44.2], SNode: [224.2],
  },
  clustered: {
    Sun: [29.2], Moon: [0.8], Mercury: [1.5], Venus: [3.1], Mars: [5.4],
    Jupiter: [8.2], Saturn: [181.5], Uranus: [182.4], Neptune: [183.8],
    Pluto: [184.9, -0.12], NNode: [0.2], SNode: [180.2], Chiron: [4.7], Lilith: [6.1],
  },
  spread: {
    Sun: [2.2], Moon: [41.7], Mercury: [83.5], Venus: [126.8], Mars: [169.4],
    Jupiter: [212.0], Saturn: [254.6], Uranus: [298.3], Neptune: [333.7], Pluto: [355.1],
    NNode: [110.6], SNode: [290.6], Fortune: [72.5],
  },
};
const cusps = [350, 22, 54, 86, 116, 146, 170, 202, 234, 266, 298, 326];

function render(name, planets) {
  document.body.innerHTML = '<div id="chart"></div>';
  const settings = {
    COLOR_BACKGROUND: '#0b0722',
    LINE_COLOR: '#e8c56b',
    CUSPS_FONT_COLOR: '#c8b9e8',
    COLOR_AXIS: '#a78bfa',
    COLOR_ASPECTS: '#9edfc8',
    COLORS_SIGNS: ['#34264f', '#2a2445', '#34264f', '#2a2445', '#34264f', '#2a2445', '#34264f', '#2a2445', '#34264f', '#2a2445', '#34264f', '#2a2445'],
    SYMBOL_SCALE: 0.85,
    MARGIN: 20,
    PADDING: 12,
    ADD_CLICK_AREA: false,
  };
  const chart = new Chart('chart', 760, 760, settings);
  chart.radix({ planets, cusps });
  const svg = document.querySelector('svg');
  const xml = svg.outerHTML;
  const out = path.join(__dirname, `${name}.svg`);
  fs.writeFileSync(out, xml, 'utf8');
  return {
    profile: name,
    file: out,
    bytes: Buffer.byteLength(xml),
    width: svg.getAttribute('width'),
    height: svg.getAttribute('height'),
    viewBox: svg.getAttribute('viewBox'),
    lines: svg.querySelectorAll('line').length,
    circles: svg.querySelectorAll('circle').length,
    paths: svg.querySelectorAll('path').length,
    text: svg.querySelectorAll('text').length,
    planetGroups: svg.querySelectorAll('[id*="planets"]').length,
    hasCuspLabels: /CUSPS|cusps|cusp/i.test(xml),
    hasPremiumGold: xml.includes('#e8c56b'),
    hasPremiumViolet: xml.includes('#a78bfa'),
  };
}

const results = Object.entries(profiles).map(([name, points]) => render(name, points));
fs.writeFileSync(path.join(__dirname, 'astrochart_smoke_results.json'), JSON.stringify({ package: '3.0.2', results }, null, 2) + '\n');
console.log(JSON.stringify({ package: '3.0.2', results }, null, 2));
