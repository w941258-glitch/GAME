const {chromium}=require('playwright');
const assert=require('node:assert/strict');
(async()=>{
 const browser=await chromium.launch({executablePath:process.env.CHROMIUM_PATH||'/usr/bin/chromium',headless:true,args:['--no-sandbox']});
 const page=await browser.newPage({viewport:{width:1440,height:1000}});
 const errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.goto(process.env.GAME_TEST_URL||'http://127.0.0.1:8000');
 const button=(name)=>page.getByRole('button',{name,exact:true});
 async function click(name){console.log('click',name);await button(name).click();await page.waitForFunction(()=>!document.querySelector('#notice').textContent.includes('處理中'));}
 async function menu(name){console.log('menu',name);await page.getByRole('navigation').getByRole('button',{name,exact:true}).click();await page.waitForFunction(()=>!document.querySelector('#notice').textContent.includes('處理中'));}
 await click('開始新遊戲');if(await page.locator('dialog').count())await click('確認');await page.getByLabel('姓名',{exact:true}).fill('網頁玩家');await click('展開新人生');
 await page.getByRole('heading',{name:'網頁玩家的第二人生'}).waitFor();
 await menu('故事');await click('幫忙搬運（30 分鐘，心情 +8）');
 await menu('城市');await click('前往辦公室');
 await menu('社交');await page.locator('.card').filter({has:page.getByRole('heading',{name:'林予晴 · 初識'})}).getByRole('button',{name:'聊天',exact:true}).click();
 await page.getByRole('heading',{name:'網頁玩家的第二人生'}).waitFor();
 await menu('公司');await click('成立公司');await menu('公司');await click('聘用 陳可欣 · $1,000');
 for(let i=0;i<2;i++){await menu('公司');await click('研發兩小時');}
 await menu('公司');await page.getByText('資金 $8,000 / 員工 1 / 產品 1',{exact:true}).waitFor();
 await menu('城市');await click('前往咖啡廳');await menu('生活');await click('用餐 · $150');await menu('生活');await click('購買明信片 · $200');
 await menu('存檔');await page.locator('.card').filter({has:page.getByRole('heading',{name:'存檔 1',exact:true})}).getByRole('button',{name:/儲存至此槽|覆蓋此存檔/}).click();await click('確認');await page.getByText('已儲存至槽 1',{exact:true}).waitFor();
 await menu('城市');await click('前往餐廳');
 await menu('存檔');await page.locator('.card').filter({has:page.getByRole('heading',{name:'存檔 1',exact:true})}).getByRole('button',{name:'讀取此存檔',exact:true}).click();await click('確認');
 await page.getByRole('heading',{name:'網頁玩家的第二人生'}).waitFor();
 assert((await page.locator('#status').textContent()).includes('咖啡廳'));
 await menu('設定');await page.getByLabel('顯示模式',{exact:true}).selectOption('B');
 await page.reload();await menu('設定');assert.equal(await page.getByLabel('顯示模式',{exact:true}).inputValue(),'B');
 await page.getByLabel('顯示模式',{exact:true}).selectOption('C');
 await page.setViewportSize({width:390,height:844});await menu('首頁');
 assert(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth));
 await page.screenshot({path:'/workspace/GAME/.local/web-mobile.png',fullPage:true});
 await page.setViewportSize({width:1440,height:1000});await menu('遊戲');
 await page.screenshot({path:'/workspace/GAME/.local/web-desktop.png',fullPage:true});
 console.log('WEB_SMOKE_PASS: character, stories, social, company, life, saves, settings, mobile');
 await browser.close();
 assert.deepEqual(errors,[]);
})().catch(e=>{console.error(e);process.exit(1)});
