const { test, expect } = require('playwright/test');
const fs = require('fs');
const path = require('path');
const { execFileSync } = require('child_process');

test.beforeAll(() => {
  const python = process.platform === 'win32' ? 'venv/Scripts/python.exe' : 'venv/bin/python';
  execFileSync(python, ['manage.py', 'shell', '-c', "from pathlib import Path; exec(Path('scripts/render-hero-qa.py').read_text())"], { stdio: 'pipe' });
});

for (const width of [320, 375, 390, 768, 1024, 1440]) {
  for (const reduced of [false, true]) {
    test(`spiritual hero ${width}px ${reduced ? 'reduced' : 'animated'}`, async ({ page }) => {
      test.setTimeout(60000);
      await page.setViewportSize({ width, height: 1000 });
      await page.emulateMedia({ reducedMotion: reduced ? 'reduce' : 'no-preference' });
      const errors = [];
      page.on('pageerror', error => errors.push(String(error)));
      page.on('console', message => { if (message.type() === 'error') errors.push(message.text()); });
      let state = 'live';
      await page.route('http://127.0.0.1:8799/', route => {
        const html = fs.readFileSync(path.join('test-results/hero-fixtures', state + '.html'), 'utf8')
          .replace(/<link[^>]+href="https:\/\/fonts\.[^"]+"[^>]*>/g, '');
        return route.fulfill({ status: 200, contentType: 'text/html', body: html });
      });
      for (state of ['live', 'upcoming', 'none']) {
        await page.goto('/', { waitUntil: 'networkidle' });
        const hero = page.locator('.hero-spiritual');
        await expect(hero.locator('h1')).toContainText('The altar comes before the platform.');
        await expect(hero.locator('.hero-spiritual-background')).toHaveAttribute('aria-hidden', 'true');
        const watermark = hero.locator('.hero-logo-watermark');
        await expect(watermark).toHaveAttribute('alt', '');
        await expect(watermark).toHaveAttribute('src', /branding\/ytr-logo-hero.webp/);
        const logo = await watermark.evaluate(el => ({
          loaded: el.complete && el.naturalWidth > 0,
          ratio: el.getBoundingClientRect().width / el.getBoundingClientRect().height,
        }));
        expect(logo.loaded).toBe(true);
        expect(logo.ratio).toBeCloseTo(1, 2);

        expect(await page.evaluate(() => document.documentElement.scrollWidth - innerWidth)).toBeLessThanOrEqual(0);
        if (state === 'live') await expect(hero.getByRole('link', { name: 'Join Morning Devotion' })).toBeVisible();
        if (state === 'upcoming') {
          await expect(hero.getByRole('link', { name: 'View Morning Devotion' })).toBeVisible();
          await expect(hero.getByRole('link', { name: 'Join Morning Devotion' })).toHaveCount(0);
        }
        if (state === 'none') {
          await expect(hero.getByRole('link', { name: 'Our story' })).toBeVisible();
          await expect(hero.locator('.hero-session-state')).toHaveCount(0);
        }
        if (reduced) expect(await hero.evaluate(el => el.getAnimations({ subtree: true }).length)).toBe(0);
        else {
          expect(await hero.evaluate(el => el.getAnimations({ subtree: true }).length)).toBeGreaterThan(0);
          await hero.evaluate(el => el.getAnimations({ subtree: true }).forEach(a => { a.pause(); a.currentTime = 0; }));
          if (state === 'live') await hero.screenshot({ path: `test-results/hero-${width}-initial.png` });
          await hero.evaluate(el => el.getAnimations({ subtree: true }).forEach(a => { a.currentTime = a.effect.target.closest('.hero-inner') ? 1500 : 10000; }));
        }
        await hero.screenshot({ path: `test-results/hero-${width}-${state}-${reduced ? 'reduced' : 'mid'}.png` });
        const cta = hero.locator('.hero-ctas a').first();
        await cta.focus();
        await expect(cta).toBeFocused();
        const focus = await cta.evaluate(el => getComputedStyle(el).outlineStyle);
        expect(focus).not.toBe('none');
      }
      expect(errors).toEqual([]);
      await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
      await expect(page.locator('.hero-spiritual')).toHaveClass(/hero-motion-paused/);
    });
  }
}
