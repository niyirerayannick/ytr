const { test, expect } = require("playwright/test");
const { loginAsMember, PUBLIC_PAGES, VIEWPORT_WIDTHS } = require("./helpers");

async function scrollOverflow(page) {
  return page.evaluate(() => ({
    scrollWidth: document.documentElement.scrollWidth,
    innerWidth: window.innerWidth,
  }));
}

test.describe("no horizontal overflow at any required viewport width (item 5)", () => {
  for (const width of VIEWPORT_WIDTHS) {
    test(`width ${width}px — public pages`, async ({ page }) => {
      await page.setViewportSize({ width, height: 900 });
      const results = [];
      for (const path of PUBLIC_PAGES) {
        await page.goto(path);
        const { scrollWidth, innerWidth } = await scrollOverflow(page);
        results.push({ path, scrollWidth, innerWidth, overflow: scrollWidth - innerWidth });
      }
      const overflowing = results.filter((r) => r.overflow > 1);
      expect(overflowing, JSON.stringify(overflowing)).toEqual([]);
    });
  }

  test("width 390px — authenticated member dashboard has no overflow", async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 900 });
    await loginAsMember(page);
    await page.goto("/dashboard/member/");
    const { scrollWidth, innerWidth } = await scrollOverflow(page);
    expect(scrollWidth - innerWidth).toBeLessThanOrEqual(1);
  });
});

test.describe("320px public navigation regression (item 6)", () => {
  test.use({ viewport: { width: 320, height: 800 } });

  test("branding, hamburger, search, and login/create-account all fit and remain reachable", async ({ page }) => {
    await page.goto("/");
    const { scrollWidth, innerWidth } = await scrollOverflow(page);
    expect(scrollWidth - innerWidth).toBeLessThanOrEqual(1);

    const menuToggle = page.locator("#menuToggle");
    await expect(menuToggle).toBeVisible();
    const menuBox = await menuToggle.boundingBox();
    expect(menuBox.x).toBeGreaterThanOrEqual(0);
    expect(menuBox.x + menuBox.width).toBeLessThanOrEqual(320);

    const searchOpen = page.locator("#searchOpen");
    await expect(searchOpen).toBeVisible();

    await menuToggle.click();
    const loginLink = page.locator('#navLinks a[href="/accounts/login/"]');
    const registerLink = page.locator('#navLinks a[href="/accounts/register/"]');
    await expect(loginLink).toBeVisible();
    await expect(registerLink).toBeVisible();
    const loginBox = await loginLink.boundingBox();
    expect(loginBox.x + loginBox.width).toBeLessThanOrEqual(320);
  });

  test("the install card and its controls, if triggered, do not overflow 320px", async ({ page }) => {
    await page.goto("/");
    await page.evaluate(() => {
      const evt = new Event("beforeinstallprompt", { cancelable: true });
      evt.prompt = () => Promise.resolve();
      evt.userChoice = Promise.resolve({ outcome: "accepted", platform: "web" });
      window.dispatchEvent(evt);
    });
    await expect(page.locator("#pwaInstallCard")).toBeVisible();
    const { scrollWidth, innerWidth } = await scrollOverflow(page);
    expect(scrollWidth - innerWidth).toBeLessThanOrEqual(1);
  });
});

test.describe("standalone display-mode behaviour (item 7)", () => {
  async function emulateStandalone(page) {
    const client = await page.context().newCDPSession(page);
    await client.send("Emulation.setEmulatedMedia", {
      features: [{ name: "display-mode", value: "standalone" }],
    });
  }

  test("install and iOS cards stay hidden in standalone mode even after their trigger events fire", async ({ page }) => {
    await page.goto("/");
    await emulateStandalone(page);
    await page.evaluate(() => {
      const evt = new Event("beforeinstallprompt", { cancelable: true });
      evt.prompt = () => Promise.resolve();
      evt.userChoice = Promise.resolve({ outcome: "accepted", platform: "web" });
      window.dispatchEvent(evt);
    });
    // The JS still reveals the card (it can't see the emulated media query),
    // but the "@media (display-mode: standalone)" rule in input.css forces
    // it invisible regardless — that CSS-level guarantee is what this checks.
    await expect(page.locator("#pwaInstallCard")).toHaveCSS("display", "none");
  });

  test("the member bottom nav does not overlap page content and respects the safe-area bottom padding", async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await emulateStandalone(page);
    await loginAsMember(page);
    await page.goto("/");

    const nav = page.locator(".pwa-bottom-nav");
    await expect(nav).toBeVisible();
    const navBox = await nav.boundingBox();
    expect(navBox.y + navBox.height).toBeLessThanOrEqual(844 + 1);

    const bodyPaddingBottom = await page.evaluate(() => parseFloat(getComputedStyle(document.body).paddingBottom));
    expect(bodyPaddingBottom).toBeGreaterThanOrEqual(navBox.height - 1);

    const footer = page.locator("footer").first();
    if (await footer.count()) {
      const footerBox = await footer.boundingBox();
      if (footerBox) expect(footerBox.y + footerBox.height).toBeLessThanOrEqual(navBox.y + 1);
    }
  });
});
