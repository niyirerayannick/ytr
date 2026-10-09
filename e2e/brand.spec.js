const {test,expect}=require('playwright/test');
const fs=require('fs');
const {loginAsMember}=require('./helpers');
test('brand responsive visual QA',async({browser})=>{
 test.setTimeout(180000);
 const results=[];
 for(const width of [320,375,390,768,1024,1440]){
  const context=await browser.newContext({viewport:{width,height:900}});const page=await context.newPage();await page.route(/fonts\.(googleapis|gstatic)\.com/,route=>route.abort());
  for(const path of ['/','/devotions/','/morning-devotions/','/articles/','/podcasts/','/videos/','/accounts/login/','/accounts/register/','/accounts/password-reset/']){
   const response=await page.goto(path,{waitUntil:"domcontentloaded"});expect(response.status()).toBe(200);
   const overflow=await page.evaluate(()=>document.documentElement.scrollWidth-window.innerWidth);results.push({width,path,overflow});expect(overflow).toBeLessThanOrEqual(0);
   if([320,390,1440].includes(width)) await page.screenshot({path:`test-results/brand-${width}-${path.replaceAll('/','_')||'home'}.png`});
  }
  if(process.env.YTR_BRAND_ADMIN_SESSION) await context.addCookies([{name:'sessionid',value:process.env.YTR_BRAND_ADMIN_SESSION,domain:'127.0.0.1',path:'/'}]);
  else await loginAsMember(page);
  await page.goto('/dashboard/');expect(page.url()).toContain('/dashboard/');
  const overflow=await page.evaluate(()=>document.documentElement.scrollWidth-window.innerWidth);results.push({width,path:'/dashboard/',overflow});expect(overflow).toBeLessThanOrEqual(0);
  await page.screenshot({path:`test-results/brand-${width}-dashboard.png`});
  if(width>=1024){const collapse=page.locator('.dash-sidebar-collapse-btn');if(await collapse.count()){await collapse.click();await expect(page.locator('.dash-sidebar')).toHaveClass(/is-collapsed/);await collapse.click();}}
  else {await page.locator('[data-dash-menu-button]').click();await expect(page.locator('.dash-sidebar')).toHaveClass(/is-open/);}
  if(process.env.YTR_BRAND_ADMIN_SESSION && width===1440){
   await page.locator('.dash-topbar .dash-topbar-search-btn').click();
   await expect(page.getByRole('dialog',{name:'Command palette'})).toBeVisible();
   await page.keyboard.press('Escape');
   await page.locator('.dash-topbar .dash-create-btn').click();
   await expect(page.locator('.dash-topbar .dash-dropdown-panel').first()).toBeVisible();
   await page.keyboard.press('Escape');
   await page.locator('.dash-topbar .dash-bell-btn').click();
   await expect(page.locator('.dash-topbar .dash-notification-item').first()).toBeVisible();
   await page.keyboard.press('Escape');
  }
  await context.close();
 }
 fs.writeFileSync('test-results/brand-responsive.json',JSON.stringify(results,null,2));
});
