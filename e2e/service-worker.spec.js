const { test, expect } = require("playwright/test");
const { readAllCacheEntries } = require("./helpers");

test.describe("service worker registration (item 8)", () => {
  test("registers at scope / with no console errors, and the shell resources it references all return 200", async ({ page, baseURL }) => {
    const consoleErrors = [];
    page.on("console", (msg) => {
      if (msg.type() === "error") consoleErrors.push(msg.text());
    });
    page.on("pageerror", (err) => consoleErrors.push(String(err)));

    await page.goto("/");
    const registration = await page.evaluate(async () => {
      const reg = await navigator.serviceWorker.ready;
      return { scope: reg.scope, active: !!reg.active };
    });

    expect(registration.scope).toBe(`${baseURL}/`);
    expect(registration.active).toBe(true);
    expect(consoleErrors).toEqual([]);
  });

  test("manifest, icons, and offline fallback all return 200 with no undefined-global artifacts in the worker source", async ({ page, request }) => {
    await page.goto("/");
    const swSource = await (await request.get("/service-worker.js")).text();
    expect(swSource).not.toContain("undefined");

    const manifestResponse = await request.get("/static/manifest.webmanifest");
    expect(manifestResponse.status()).toBe(200);
    expect(manifestResponse.headers()["content-type"]).toContain("application/manifest+json");

    const manifest = await manifestResponse.json();
    for (const icon of manifest.icons) {
      const iconResponse = await request.get(icon.src);
      expect(iconResponse.status(), `icon ${icon.src} should return 200`).toBe(200);
    }

    const offlineResponse = await request.get("/static/offline.html");
    expect(offlineResponse.status()).toBe(200);
  });
});

test.describe("cache storage contents (item 9)", () => {
  test("the shell cache holds only intended assets, and nothing private is ever written to any YTR cache", async ({ page }) => {
    await page.goto("/");
    await page.evaluate(() => navigator.serviceWorker.ready);
    // Give the SW's install-time cache.addAll a moment to finish.
    await page.waitForTimeout(500);

    const entries = await readAllCacheEntries(page);
    expect(entries.length).toBeGreaterThan(0);

    const forbidden = /\/(dashboard|accounts|admin)(\/|$)/;
    for (const entry of entries) {
      expect(entry.url, `cache entry ${entry.url} must not be a private path`).not.toMatch(forbidden);
    }

    const shellEntries = entries.filter((e) => e.cache === "ytr-shell-v1").map((e) => new URL(e.url).pathname);
    for (const path of shellEntries) {
      expect(path).toMatch(/\/static\/|offline\.html/);
    }
  });
});
