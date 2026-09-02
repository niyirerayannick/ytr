// Shared fixtures for the PWA smoke suite. Credentials and content slugs come
// from apps/core/management/commands/seed_demo_content.py, which the webServer
// (scripts/run-e2e-server.js) runs before every test run.

const MEMBER_USERNAME = "member_demo";
const MEMBER_PASSWORD = "demo-pass-123";

const SEEDED_ARTICLE_PATH = "/articles/not-in-the-masses/";
const SEEDED_DEVOTION_PATH = "/devotions/";

const PUBLIC_PAGES = [
  "/",
  "/articles/",
  SEEDED_ARTICLE_PATH,
  "/devotions/",
  "/podcasts/",
  "/videos/",
  "/library/",
  "/about/",
  "/faq/",
  "/contact/",
  "/accounts/login/",
];

const VIEWPORT_WIDTHS = [320, 375, 390, 768, 1024, 1280, 1440];

async function loginAsMember(page) {
  await page.goto("/accounts/login/");
  await page.fill("#id_username", MEMBER_USERNAME);
  await page.fill("#id_password", MEMBER_PASSWORD);
  await Promise.all([
    page.waitForURL(/\/dashboard\//),
    page.click('button[type="submit"]'),
  ]);
}

async function readAllCacheEntries(page) {
  return page.evaluate(async () => {
    const names = await caches.keys();
    const entries = [];
    for (const name of names) {
      const cache = await caches.open(name);
      const requests = await cache.keys();
      for (const request of requests) entries.push({ cache: name, url: request.url });
    }
    return entries;
  });
}

module.exports = {
  MEMBER_USERNAME,
  MEMBER_PASSWORD,
  SEEDED_ARTICLE_PATH,
  SEEDED_DEVOTION_PATH,
  PUBLIC_PAGES,
  VIEWPORT_WIDTHS,
  loginAsMember,
  readAllCacheEntries,
};
