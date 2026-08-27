#!/usr/bin/env node
import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { launch } from '/home/ubuntu/oracleai-qa-tools/node_modules/chrome-launcher/dist/chrome-launcher.js';
import lighthouse from '/home/ubuntu/oracleai-qa-tools/node_modules/lighthouse/core/index.js';
import { chromium } from '/home/ubuntu/oracleai-qa-tools/node_modules/playwright-core/index.mjs';
import axe from '/home/ubuntu/oracleai-qa-tools/node_modules/axe-core/axe.js';

const ROOT = path.dirname(path.dirname(fileURLToPath(import.meta.url)));
const OUT = path.join(ROOT, 'artifacts', process.env.QA_OUT_DIR || 'lighthouse-axe');
const LH_CATEGORIES = (process.env.LH_CATEGORIES || 'performance,accessibility,best-practices,seo').split(',').filter(Boolean);
const BASE = 'http://127.0.0.1:8080/';
const VIEWPORT = { width: 1440, height: 900 };
const STATES = [
  { id: 'home', view: 'home' },
  { id: 'guides', view: 'hub' },
  { id: 'chat-oracle', view: 'chat', agent: 'oracle' },
  { id: 'chat-astro', view: 'chat', agent: 'astro' },
  { id: 'chat-tarot', view: 'chat', agent: 'tarot' },
  { id: 'chat-chiromant', view: 'chat', agent: 'chiromant' },
  { id: 'profile-summary', view: 'profile', tab: 'summary' },
  { id: 'profile-chart', view: 'profile', tab: 'chart' },
  { id: 'profile-history', view: 'profile', tab: 'history' },
  { id: 'profile-memory', view: 'profile', tab: 'memory' },
];

function stateUrl(state) {
  const url = new URL(BASE);
  url.searchParams.set('dev_user', '10001');
  url.searchParams.set('qa', '1');
  url.searchParams.set('qa_view', state.view);
  if (state.agent) url.searchParams.set('qa_agent', state.agent);
  if (state.tab) url.searchParams.set('qa_tab', state.tab);
  return url.toString();
}

function categoryScore(categories, id) {
  const score = categories?.[id]?.score;
  return typeof score === 'number' ? Math.round(score * 100) : null;
}

async function run() {
  await fs.rm(OUT, { recursive: true, force: true });
  await fs.mkdir(OUT, { recursive: true });
  const chrome = await launch({
    chromePath: '/usr/bin/chromium',
    chromeFlags: ['--headless=new', '--no-sandbox', '--disable-gpu', '--disable-dev-shm-usage'],
  });
  const browser = await chromium.launch({
    executablePath: '/usr/bin/chromium',
    headless: true,
    args: ['--no-sandbox', '--disable-dev-shm-usage'],
  });
  const axeContext = await browser.newContext({ viewport: VIEWPORT, locale: 'ru-RU', reducedMotion: 'reduce' });
  const page = await axeContext.newPage();
  const summary = { generatedAt: new Date().toISOString(), viewport: VIEWPORT, states: [] };

  try {
    for (const state of STATES) {
      const url = stateUrl(state);
      await page.goto(url, { waitUntil: 'networkidle' });
      await page.waitForTimeout(state.view === 'chat' ? 1200 : 600);
      await page.addScriptTag({ content: axe.source });
      const axeResults = await page.evaluate(async () => {
        const result = await window.axe.run(document, {
          runOnly: { type: 'tag', values: ['wcag2a', 'wcag2aa', 'best-practice'] },
        });
        return {
          violations: result.violations,
          incomplete: result.incomplete,
          passes: result.passes,
          inapplicable: result.inapplicable,
        };
      });
      await fs.writeFile(path.join(OUT, `${state.id}.axe.json`), JSON.stringify(axeResults, null, 2) + '\n');

      const lh = await lighthouse(url, {
        port: chrome.port,
        logLevel: 'silent',
        output: 'json',
        onlyCategories: LH_CATEGORIES,
        formFactor: 'desktop',
        screenEmulation: { mobile: false, width: VIEWPORT.width, height: VIEWPORT.height, deviceScaleFactor: 1 },
        throttlingMethod: 'provided',
        disableStorageReset: true,
      });
      const lhr = lh.lhr;
      await fs.writeFile(path.join(OUT, `${state.id}.lighthouse.json`), JSON.stringify(lhr, null, 2) + '\n');
      summary.states.push({
        ...state,
        url,
        lighthouse: {
          performance: categoryScore(lhr.categories, 'performance'),
          accessibility: categoryScore(lhr.categories, 'accessibility'),
          bestPractices: categoryScore(lhr.categories, 'best-practices'),
          seo: categoryScore(lhr.categories, 'seo'),
          runtimeError: lhr.runtimeError || null,
        },
        axe: {
          violations: axeResults.violations.length,
          incomplete: axeResults.incomplete.length,
          passes: axeResults.passes.length,
          violationIds: axeResults.violations.map((item) => item.id),
          incompleteIds: axeResults.incomplete.map((item) => item.id),
        },
      });
      console.log(`${state.id}: Lighthouse a${summary.states.at(-1).lighthouse.accessibility ?? 'n/a'} / Axe violations ${axeResults.violations.length}`);
    }
  } finally {
    await axeContext.close();
    await browser.close();
    await chrome.kill();
  }
  await fs.writeFile(path.join(OUT, 'summary.json'), JSON.stringify(summary, null, 2) + '\n');
  console.log(JSON.stringify(summary, null, 2));
}

run().catch((error) => {
  console.error(error.stack || error);
  process.exitCode = 1;
});
