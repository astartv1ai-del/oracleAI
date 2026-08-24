from __future__ import annotations

import json
import subprocess
import time
import urllib.request
from pathlib import Path

import websocket

ROOT = Path(__file__).resolve().parents[1]
URL = "http://127.0.0.1:8080/?dev_user=1&ux=mobile-qa"
PORT = 9225
OUT = ROOT / "docs/assets/ux-qa/mobile-overflow-metrics.json"


def command(ws, method, params=None):
    command.counter += 1
    ident = command.counter
    ws.send(json.dumps({"id": ident, "method": method, "params": params or {}}))
    while True:
        msg = json.loads(ws.recv())
        if msg.get("id") == ident:
            return msg.get("result", {})


command.counter = 0


def evaluate(ws, expression):
    result = command(ws, "Runtime.evaluate", {
        "expression": expression,
        "returnByValue": True,
        "awaitPromise": True,
    })
    return result.get("result", {}).get("value")


def wait_for_page(ws):
    for _ in range(40):
        ready = evaluate(ws, "Boolean(document.body && window.app)")
        if ready:
            time.sleep(0.8)
            return
        time.sleep(0.2)
    raise RuntimeError("page DOM/app did not become available")


def metrics(ws, stage, width, height):
    expression = f"""(() => {{
      const selectors = ['#app-root', '.screen', '.agent-card', '.agent-card__more', '.tarot-picker-widget', '.palm-result', '.compat-flow', '.compat-result', '.placement-explorer', '.chart-form', '.chart-result', '.tool-expand'];
      const rows = [];
      const inspect = (el, selector, index) => {{
        if (!el) return;
        const cs = getComputedStyle(el);
        rows.push({{
          selector, index,
          tag: el.tagName.toLowerCase(),
          className: typeof el.className === 'string' ? el.className : '',
          text: (el.innerText || '').replace(/\\s+/g, ' ').trim().slice(0, 120),
          clientWidth: el.clientWidth,
          scrollWidth: el.scrollWidth,
          rectWidth: Math.round(el.getBoundingClientRect().width * 100) / 100,
          rectHeight: Math.round(el.getBoundingClientRect().height * 100) / 100,
          rectLeft: Math.round(el.getBoundingClientRect().left * 100) / 100,
          rectRight: Math.round(el.getBoundingClientRect().right * 100) / 100,
          overflowX: cs.overflowX,
          clipped: el.scrollWidth > el.clientWidth + 1,
          isScrollContainer: (cs.overflowX === 'auto' || cs.overflowX === 'scroll') && el.scrollWidth > el.clientWidth + 1,
        }});
      }};
      selectors.forEach(sel => document.querySelectorAll(sel).forEach((el, i) => inspect(el, sel, i)));
      document.querySelectorAll('.agent-card *, .tarot-picker-widget *').forEach((el, i) => {{
        if (el.scrollWidth > el.clientWidth + 1) inspect(el, 'descendant-overflow', i);
      }});
      const palm = document.querySelector('.palm-result');
      const palmChildren = palm ? Array.from(palm.children).map((el, i) => ({{i, tag: el.tagName.toLowerCase(), className: typeof el.className === 'string' ? el.className : '', height: Math.round(el.getBoundingClientRect().height * 100) / 100, text: (el.innerText || '').replace(/\\s+/g, ' ').trim().slice(0, 90)}})) : [];
      return {{
        stage: {stage!r}, width: {width}, height: {height},
        viewport: {{innerWidth: window.innerWidth, innerHeight: window.innerHeight}},
        document: {{clientWidth: document.documentElement.clientWidth, scrollWidth: document.documentElement.scrollWidth, bodyScrollWidth: document.body.scrollWidth}},
        rows,
        palmChildren,
        scrollContainers: rows.filter(r => r.isScrollContainer),
        horizontalOverflow: document.documentElement.scrollWidth > document.documentElement.clientWidth + 1 || document.body.scrollWidth > document.documentElement.clientWidth + 1 || rows.some(r => r.isScrollContainer)
      }};
    }})()"""
    return evaluate(ws, expression)


def main():
    profile = "/tmp/oracleai-mobile-qa-profile"
    proc = subprocess.Popen([
        "/usr/bin/chromium", "--headless=new", "--no-sandbox", "--disable-gpu",
        f"--remote-debugging-port={PORT}", "--remote-allow-origins=*", f"--user-data-dir={profile}", "about:blank",
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        endpoint = None
        for _ in range(40):
            try:
                tabs = json.load(urllib.request.urlopen(f"http://127.0.0.1:{PORT}/json/list", timeout=1))
                if tabs:
                    endpoint = tabs[0]["webSocketDebuggerUrl"]
                    break
            except Exception:
                time.sleep(0.25)
        if not endpoint:
            raise RuntimeError("CDP endpoint unavailable")
        ws = websocket.create_connection(endpoint, timeout=10)
        command(ws, "Page.enable")
        command(ws, "Runtime.enable")
        command(ws, "Network.enable")
        command(ws, "Network.setCacheDisabled", {"cacheDisabled": True})
        results = []
        for width, height in ((320, 844), (375, 812), (390, 844)):
            command(ws, "Emulation.setDeviceMetricsOverride", {
                "width": width, "height": height, "deviceScaleFactor": 1, "mobile": True,
            })
            command(ws, "Page.navigate", {"url": URL})
            wait_for_page(ws)
            results.append(metrics(ws, "home", width, height))
            evaluate(ws, "window.app.go('hub')")
            time.sleep(0.4)
            results.append(metrics(ws, "hub", width, height))
            evaluate(ws, "window.app.openChat('tarot', () => window.app.featureTarot())")
            time.sleep(1.2)
            results.append(metrics(ws, "tarot-picker", width, height))
            evaluate(ws, "window.app.openChat('chiromant', () => window.app.featurePalm())")
            time.sleep(0.3)
            results.append(metrics(ws, "palm-picker", width, height))
            evaluate(ws, "window.app.openChat('oracle', () => window.app.featureCompat())")
            time.sleep(0.3)
            results.append(metrics(ws, "compat-form", width, height))
            evaluate(ws, "window.app.openChat('astro', () => window.app.featurePlacements())")
            time.sleep(0.3)
            results.append(metrics(ws, "placements", width, height))
            evaluate(ws, "window.app.openChat('astro', () => window.app.featureChart())")
            time.sleep(1.0)
            results.append(metrics(ws, "chart", width, height))
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps({"url": URL, "results": results}, ensure_ascii=False, indent=2) + "\n")
        print(OUT)
        print(json.dumps(results, ensure_ascii=False))
        ws.close()
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()


if __name__ == "__main__":
    main()
