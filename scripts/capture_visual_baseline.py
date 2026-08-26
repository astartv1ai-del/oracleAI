"""Capture synthetic Mini App visual baselines and lightweight accessibility signals.

The harness is intentionally deterministic: it uses the local dev identity,
accepts the self-confirmed age gate, never stores real user data, and writes only
screenshots plus aggregate DOM checks.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts" / "visual-baseline"
BASE_URL = "http://127.0.0.1:8080/?dev_user=10001"
VIEWPORTS = {
    "mobile-360": (360, 800),
    "reference-390": (390, 844),
    "large-430": (430, 932),
}
LOCALES = {"ru": "ru-RU", "en": "en-US"}


def dom_contract(page) -> dict:
    return page.evaluate(
        """
        () => {
          const body = document.body;
          const focusable = [...document.querySelectorAll(
            'button, a[href], input, textarea, select, [tabindex]:not([tabindex="-1"])'
          )];
          const unnamed = focusable.filter((el) => {
            const label = (el.getAttribute('aria-label') || el.innerText || el.value || '').trim();
            return !label;
          });
          const imagesWithoutAlt = [...document.images].filter((img) =>
            !img.hasAttribute('alt')
          );
          return {
            viewportWidth: window.innerWidth,
            scrollWidth: Math.max(body.scrollWidth, document.documentElement.scrollWidth),
            horizontalOverflow: Math.max(body.scrollWidth, document.documentElement.scrollWidth) > window.innerWidth + 1,
            unnamedFocusableCount: unnamed.length,
            unnamedFocusable: unnamed.map((el) => ({tag: el.tagName, className: el.className, text: (el.innerText || '').slice(0, 80)})),
            imagesWithoutAltCount: imagesWithoutAlt.length,
            visiblePrimaryActions: [...document.querySelectorAll('.btn-primary, [data-primary]')]
              .filter((el) => !!(el.offsetWidth || el.offsetHeight || el.getClientRects().length)).length,
            reducedMotionPreference: window.matchMedia('(prefers-reduced-motion: reduce)').matches,
          };
        }
        """
    )


def capture() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    results: dict[str, dict] = {}
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True, executable_path='/usr/bin/chromium', args=['--no-sandbox'])
        for locale_key, locale in LOCALES.items():
            for name, (width, height) in VIEWPORTS.items():
                context = browser.new_context(
                    viewport={"width": width, "height": height}, locale=locale,
                    reduced_motion="reduce" if name == "reference-390" else "no-preference")
                context.add_init_script(
                    "localStorage.setItem('oracle_lang', %r); "
                    "localStorage.removeItem('oracle_intro_seen'); "
                    "localStorage.removeItem('oracle_age_confirmed');" % locale_key
                )
                page = context.new_page()
                page.goto(BASE_URL, wait_until="networkidle")
                page.screenshot(path=str(OUT / f"{locale_key}-{name}-age-gate.png"), full_page=True)
                accept = page.locator("[data-age-accept]")
                if accept.count():
                    accept.first.click()
                    page.wait_for_timeout(250)
                skip = page.locator("[data-intro-skip]")
                if skip.count() and skip.first.is_visible():
                    skip.first.click()
                    page.wait_for_timeout(250)
                page.screenshot(path=str(OUT / f"{locale_key}-{name}-home.png"), full_page=True)
                states = {"home": dom_contract(page)}
                try:
                    nav = page.locator(".nav-btn")
                    if nav.count() >= 2:
                        nav.nth(1).click(force=True)
                        page.wait_for_timeout(250)
                        page.screenshot(path=str(OUT / f"{locale_key}-{name}-chat.png"), full_page=True)
                        states["chat"] = dom_contract(page)
                    if nav.count() >= 3:
                        nav.nth(2).click(force=True)
                        page.wait_for_timeout(250)
                        page.screenshot(path=str(OUT / f"{locale_key}-{name}-profile.png"), full_page=True)
                        states["profile"] = dom_contract(page)

                        # Navigate through the actual profile tabs before capturing their states.
                        for tab_name, state_name in (("chart", "chart-tab"), ("history", "history"), ("memory", "memory-tab")):
                            tab = page.locator(f'.ptab[data-tab="{tab_name}"]')
                            if tab.count() and tab.first.is_visible():
                                tab.first.click(force=True)
                                page.wait_for_timeout(350)
                                page.screenshot(path=str(OUT / f"{locale_key}-{name}-{state_name}.png"), full_page=True)
                                states[state_name] = dom_contract(page)
                                if tab_name == "chart":
                                    full_chart = page.locator('[data-act="full-chart"]')
                                    if full_chart.count() and full_chart.first.is_visible():
                                        full_chart.first.click(force=True)
                                        page.wait_for_timeout(250)
                                        page.screenshot(path=str(OUT / f"{locale_key}-{name}-chart-modal.png"), full_page=True)
                                        states["chart-modal"] = dom_contract(page)
                                        page.evaluate("window.app && app.closeModal && app.closeModal()")
                                        page.wait_for_timeout(100)
                                elif tab_name == "memory":
                                    memory_button = page.locator('[data-act="memories"]')
                                    if memory_button.count() and memory_button.first.is_visible():
                                        memory_button.first.click(force=True)
                                        page.wait_for_timeout(250)
                                        page.screenshot(path=str(OUT / f"{locale_key}-{name}-memory-modal.png"), full_page=True)
                                        states["memory-modal"] = dom_contract(page)
                                        page.evaluate("window.app && app.closeModal && app.closeModal()")
                                        page.wait_for_timeout(100)

                    # Tarot is a chat action from the home surface; invoke the same callback directly.
                    page.evaluate("window.app && app.go && app.go('home')")
                    page.wait_for_timeout(250)
                    page.evaluate("window.app && app.openChat && app.openChat('tarot', () => app.featureTarot())")
                    page.wait_for_timeout(450)
                    page.screenshot(path=str(OUT / f"{locale_key}-{name}-tarot.png"), full_page=True)
                    states["tarot"] = dom_contract(page)
                    page.evaluate("window.app && app.closeChat && app.closeChat()")
                except PlaywrightError as exc:
                    states["navigation_error"] = str(exc)
                results[f"{locale_key}-{name}"] = states
                context.close()
        browser.close()
    report = {
        "base_url": BASE_URL,
        "synthetic_identity": True,
        "viewports": results,
        "pass": not any("navigation_error" in states for states in results.values()) and all(
            state.get("horizontalOverflow") is False
            and state.get("unnamedFocusableCount", 0) == 0
            and state.get("imagesWithoutAltCount", 0) == 0
            for states in results.values()
            for state in states.values()
            if isinstance(state, dict) and "horizontalOverflow" in state
        ),
    }
    (OUT / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["pass"] else 1


if __name__ == "__main__":
    sys.exit(capture())
