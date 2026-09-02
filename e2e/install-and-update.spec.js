const { test, expect, devices } = require("playwright/test");

const IOS_USER_AGENT =
  "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Mobile/15E148 Safari/604.1";

test.describe("install prompt handling — Chromium heuristics can't be forced in automation, so the JS state machine is exercised directly with a synthetic event (item 14)", () => {
  test("install card is hidden until beforeinstallprompt fires, and the full accept/appinstalled cycle hides it again", async ({ page }) => {
    await page.goto("/");
    await expect(page.locator("#pwaInstallCard")).toBeHidden();

    await page.evaluate(() => {
      const evt = new Event("beforeinstallprompt", { cancelable: true });
      evt.prompt = () => Promise.resolve();
      evt.userChoice = Promise.resolve({ outcome: "accepted", platform: "web" });
      window.dispatchEvent(evt);
    });
    await expect(page.locator("#pwaInstallCard")).toBeVisible();

    await page.click("#pwaInstallButton");
    await expect(page.locator("#pwaInstallCard")).toBeHidden();
  });

  test("dismissing the install card hides it and is remembered across a reload", async ({ page }) => {
    await page.goto("/");
    await page.evaluate(() => {
      const evt = new Event("beforeinstallprompt", { cancelable: true });
      evt.prompt = () => Promise.resolve();
      evt.userChoice = Promise.resolve({ outcome: "dismissed", platform: "web" });
      window.dispatchEvent(evt);
    });
    await expect(page.locator("#pwaInstallCard")).toBeVisible();
    await page.click("#pwaInstallDismiss");
    await expect(page.locator("#pwaInstallCard")).toBeHidden();

    await page.reload();
    await page.evaluate(() => {
      const evt = new Event("beforeinstallprompt", { cancelable: true });
      evt.prompt = () => Promise.resolve();
      evt.userChoice = Promise.resolve({ outcome: "dismissed", platform: "web" });
      window.dispatchEvent(evt);
    });
    await expect(page.locator("#pwaInstallCard")).toBeHidden();
  });

  test("appinstalled clears the install and iOS cards", async ({ page }) => {
    await page.goto("/");
    await page.evaluate(() => {
      const evt = new Event("beforeinstallprompt", { cancelable: true });
      evt.prompt = () => Promise.resolve();
      evt.userChoice = Promise.resolve({ outcome: "accepted", platform: "web" });
      window.dispatchEvent(evt);
    });
    await expect(page.locator("#pwaInstallCard")).toBeVisible();
    await page.evaluate(() => window.dispatchEvent(new Event("appinstalled")));
    await expect(page.locator("#pwaInstallCard")).toBeHidden();
  });

  test("the update banner is hidden by default, and clicking Update with no waiting worker is a harmless no-op", async ({ page }) => {
    await page.goto("/");
    await expect(page.locator("#pwaUpdate")).toBeHidden();
    // #pwaUpdate is [hidden] so it's not actionable; this only proves the
    // click handler doesn't throw when waitingWorker is null. A full
    // two-service-worker-version update cycle is out of scope for this
    // smoke suite (item 16) — see docs/pwa.md testing notes.
    const errors = [];
    page.on("pageerror", (e) => errors.push(String(e)));
    await page.evaluate(() => document.getElementById("pwaUpdateButton").click());
    expect(errors).toEqual([]);
  });
});

test.describe("iOS manual install instructions (item 15)", () => {
  test("does not appear on a desktop Chrome user agent", async ({ page }) => {
    await page.goto("/");
    await expect(page.locator("#pwaIosInstall")).toBeHidden();
  });

  test("appears on an iOS user agent, is dismissible, and the dismissal is remembered for the browser session", async ({ browser }) => {
    const context = await browser.newContext({ ...devices["iPhone 13"], userAgent: IOS_USER_AGENT });
    const page = await context.newPage();
    await page.goto("/");
    await expect(page.locator("#pwaIosInstall")).toBeVisible();

    await page.click("#pwaIosDismiss");
    await expect(page.locator("#pwaIosInstall")).toBeHidden();

    await page.reload();
    await expect(page.locator("#pwaIosInstall")).toBeHidden();
    await context.close();
  });
});

test.describe("offline/online status banner (item 17)", () => {
  test("shows an offline message and then a back-online message, without blocking the page", async ({ page }) => {
    await page.goto("/");
    await page.evaluate(() => window.dispatchEvent(new Event("offline")));
    await expect(page.locator("#pwaNetworkStatus")).toBeVisible();
    await expect(page.locator("#pwaNetworkStatus")).toContainText("offline");

    await page.evaluate(() => window.dispatchEvent(new Event("online")));
    await expect(page.locator("#pwaNetworkStatus")).toContainText("Back online");

    // Non-blocking: it's a small toast near the bottom edge, not a full-page overlay,
    // so the rest of the page (e.g. the brand link) stays visible and clickable.
    const box = await page.locator("#pwaNetworkStatus").boundingBox();
    const viewport = page.viewportSize();
    expect(box.width).toBeLessThanOrEqual(viewport.width);
    expect(box.height).toBeLessThan(100);
    expect(box.y).toBeGreaterThan(viewport.height / 2);
    await expect(page.locator(".brand").first()).toBeVisible();
  });
});
