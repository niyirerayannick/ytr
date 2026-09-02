const { test, expect } = require("playwright/test");

test("debug controller + header", async ({ page, request }) => {
  await page.addInitScript(() => {
    window.__swDebug = [];
    navigator.serviceWorker.addEventListener("message", (e) => {
      window.__swDebug.push(e.data);
    });
  });

  await page.goto("/");
  await page.evaluate(() => navigator.serviceWorker.ready);

  await page.goto("/articles/not-in-the-masses/");
  await page.waitForTimeout(800);

  const debugMsgs = await page.evaluate(() => window.__swDebug);
  console.log("SW DEBUG MSGS:", JSON.stringify(debugMsgs, null, 2));

  const entries = await page.evaluate(async () => {
    const names = await caches.keys();
    const out = [];
    for (const n of names) {
      const c = await caches.open(n);
      const reqs = await c.keys();
      for (const r of reqs) out.push({ cache: n, url: r.url });
    }
    return out;
  });
  console.log("CACHE ENTRIES:", JSON.stringify(entries, null, 2));
});
