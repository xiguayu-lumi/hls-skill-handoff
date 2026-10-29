// Render authored local HTML only; no remote browser control or publishing.
import fs from 'node:fs/promises';
import path from 'node:path';
import {pathToFileURL} from 'node:url';
function arg(name){const i=process.argv.indexOf(name);if(i<0||!process.argv[i+1])throw new Error(`Missing ${name}`);return path.resolve(process.argv[i+1]);}
const html=arg('--html'),out=arg('--output');
await fs.access(html);
const modules=process.env.CODEX_NODE_MODULES||path.join(process.env.USERPROFILE||'','.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules');
const {chromium}=await import(pathToFileURL(path.join(modules,'playwright/index.mjs')).href);
const browser=await chromium.launch({channel:'msedge',headless:true});
try{
 const page=await browser.newPage({viewport:{width:1400,height:1800},deviceScaleFactor:1});
 const errors=[];page.on('pageerror',e=>errors.push(e.message));page.on('requestfailed',r=>errors.push(`${r.url()}: ${r.failure()?.errorText}`));
 await page.goto(pathToFileURL(html).href,{waitUntil:'networkidle'});
 await page.evaluate(()=>document.fonts.ready);
 const report=await page.evaluate(()=>{
  const images=[...document.images].map(i=>({src:i.getAttribute('src'),loaded:i.complete&&i.naturalWidth>0}));
  const fonts=[...document.fonts].map(f=>({family:f.family,status:f.status}));
  const pages=[...document.querySelectorAll('.page')].map((p,i)=>{
   const r=p.getBoundingClientRect();
   const overflow=[...p.querySelectorAll('*')].filter(e=>!e.closest('svg')).filter(e=>{
    const b=e.getBoundingClientRect(),s=getComputedStyle(e);const clips=['hidden','clip','auto','scroll'];return b.width&&b.height&&(b.left<r.left-1||b.right>r.right+1||b.top<r.top-1||b.bottom>r.bottom+1||(clips.includes(s.overflowX)&&e.scrollWidth>e.clientWidth+1)||(clips.includes(s.overflowY)&&e.scrollHeight>e.clientHeight+1));
   }).map(e=>e.tagName+'.'+e.className);
   return {page:i+1,width:r.width,height:r.height,overflow};
  });return {images,fonts,pages};
 });
 if(!report.pages.length||report.pages.some(p=>p.overflow.length)||report.images.some(i=>!i.loaded)||report.fonts.some(f=>f.status!=='loaded')||errors.length)throw new Error(JSON.stringify({errors,...report}));
 await fs.mkdir(path.dirname(out),{recursive:true});await fs.mkdir(out); // EEXIST deliberately prevents overwrite.
 for(let i=0;i<report.pages.length;i++)await page.locator('.page').nth(i).screenshot({path:path.join(out,`${String(i+1).padStart(2,'0')}.png`)});
 await fs.writeFile(path.join(out,'render-report.json'),JSON.stringify(report,null,2));
 console.log(JSON.stringify({output:out,...report},null,2));
}finally{await browser.close();}
