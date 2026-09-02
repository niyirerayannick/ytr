const { test, expect } = require("playwright/test");
const { loginAsMember, readAllCacheEntries, SEEDED_ARTICLE_PATH, SEEDED_DEVOTION_PATH } = require("./helpers");

test.describe("public content offline (items 10-11)", () => {
  test("a published article is cached while online and readable offline", async ({ page, context }) => {
    await page.goto("/");
    await page.evaluate(() => navigator.serviceWorker.ready);

    // The very first navigation (above) registers the worker but isn't
    // controlled by it yet. This second navigation is controlled, so the
    // worker's fetch handler actually sees and caches it.
    await page.goto(SEEDED_ARTICLE_PATH);
    await page.waitForTimeout(300);

    const entries = await readAllCacheEntries(page);
    const cachedArticle = entries.find((e) => e.cache === "ytr-public-pages-v1" && e.url.endsWith(SEEDED_ARTICLE_PATH));
    expect(cachedArticle, "article should be present in the bounded public-page cache").toBeTruthy();

    await context.setOffline(true);
    await page.reload();
    await expect(page.locator("h1")).toContainText("Not in the Masses");
    await context.setOffline(false);
  });

  test("the devotions page is cached while online and readable offline, but a paginated request is not cached", async ({ page, context, request }) => {
    await page.goto("/");
    await page.evaluate(() => navigator.serviceWorker.ready);
    await page.goto(SEEDED_DEVOTION_PATH);
    await page.waitForTimeout(300);

    const entries = await readAllCacheEntries(page);
    const cachedDevotions = entries.find((e) => e.cache === "ytr-public-pages-v1" && e.url.endsWith(SEEDED_DEVOTION_PATH));
    expect(cachedDevotions, "devotions page should be present in the bounded public-page cache").toBeTruthy();

    const paginated = await request.get(`${SEEDED_DEVOTION_PATH}?page=2`);
    expect(paginated.headers()["x-ytr-public-cache"]).toBeUndefined();

    await context.setOffline(true);
    await page.reload();
    await expect(page.locator("body")).not.toContainText("You're offline");
    await context.setOffline(false);
  });
});

test.describe("private content is never served offline from cache (item 12, security-critical)", () => {
  test("the member dashboard is never written to any YTR cache and fails closed when offline", async ({ page, context }) => {
    await page.goto("/");
    await page.evaluate(() => navigator.serviceWorker.ready);
    await loginAsMember(page);
    await page.goto("/dashboard/member/");
    await page.waitForTimeout(300);

    const entries = await readAllCacheEntries(page);
    const leaked = entries.filter((e) => /\/dashboard\//.test(e.url));
    expect(leaked, "no /dashboard/ response should ever be written to a YTR cache").toEqual([]);

    await context.setOffline(true);
    let reloadFailed = false;
    try {
      await page.reload({ timeout: 10_000 });
    } catch (e) {
      reloadFailed = true;
    }
    const bodyText = reloadFailed ? "" : await page.locator("body").innerText().catch(() => "");
    expect(
      reloadFailed || !bodyText.toLowerCase().includes("bookmark"),
      "an offline reload of the dashboard must not silently succeed from a cached copy"
    ).toBe(true);
    await context.setOffline(false);
  });

  test("the login page is network-only and fails closed when offline", async ({ page, context }) => {
    await page.goto("/accounts/login/");
    await page.evaluate(() => navigator.serviceWorker.ready);
    await page.waitForTimeout(300);

    const entries = await readAllCacheEntries(page);
    const leaked = entries.filter((e) => /\/accounts\//.test(e.url));
    expect(leaked, "no /accounts/ response should ever be written to a YTR cache").toEqual([]);

    await context.setOffline(true);
    let reloadFailed = false;
    try {
      await page.reload({ timeout: 10_000 });
    } catch (e) {
      reloadFailed = true;
    }
    expect(reloadFailed, "an offline reload of the login page must not be served from cache").toBe(true);
    await context.setOffline(false);
  });
});

test.describe("logout leaves no authenticated HTML behind (item 13)", () => {
  test("no /dashboard or /accounts response is present in cache storage after logging out", async ({ page }) => {
    await page.goto("/");
    await page.evaluate(() => navigator.serviceWorker.ready);
    await loginAsMember(page);
    await page.goto("/dashboard/member/");

    await page.evaluate(() => {
      const form = document.querySelector('form[action*="logout"]');
      if (form) form.submit();
    });
    await page.waitForURL(/\/$|\/accounts\/logout/);

    const entries = await readAllCacheEntries(page);
    const leaked = entries.filter((e) => /\/(dashboard|accounts)\//.test(e.url));
    expect(leaked).toEqual([]);
  });
});
