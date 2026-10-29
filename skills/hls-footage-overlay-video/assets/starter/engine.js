'use strict';
const canvas=document.getElementById('c'),g=canvas.getContext('2d');
let cfg, videos={};
const ease=x=>1-Math.pow(1-Math.max(0,Math.min(1,x)),3);
function box(x,y,w,h,alpha=.62){g.fillStyle=`rgba(0,0,0,${alpha})`;g.beginPath();g.roundRect(x,y,w,h,20);g.fill();}
function font(size){g.font=`700 ${size}px "${cfg.font_family}",sans-serif`;}
function text(str,x,y,size,color,maxWidth){font(size);if(g.measureText(str).width>maxWidth)throw Error(`Text overflows: ${str}`);g.fillStyle=color;g.textBaseline='top';g.fillText(str,x,y);}
function sceneAt(t){const s=cfg.scenes.find(s=>t>=s.start&&t<s.end);if(!s)throw Error(`No scene at ${t}`);return s;}
async function seek(v,t){
 if(Math.abs(v.currentTime-t)<.002&&v.readyState>=2)return;
 await new Promise((resolve,reject)=>{
  const done=()=>{clearTimeout(timer);v.removeEventListener('seeked',done);resolve();};
  const timer=setTimeout(()=>{v.removeEventListener('seeked',done);reject(Error(`Video seek timeout at ${t}`));},7000);
  v.addEventListener('seeked',done);v.currentTime=t;
 });
 if(Math.abs(v.currentTime-t)>.04)throw Error(`Video seek mismatch: wanted ${t}, got ${v.currentTime}`);
}
window.prepare=async t=>{
 const s=sceneAt(t),v=videos[s.asset];let target=t-s.start+(s.offset||0);
 if(s.loop)target%=Math.max(.01,v.duration-.05);
 if(target>v.duration-.01)throw Error(`Clip too short: ${s.asset}, ${target}/${v.duration}`);
 await seek(v,target);
};
window.renderFrame=(t,caption=true)=>{
 const s=sceneAt(t),v=videos[s.asset],m=cfg.media[s.asset],lt=t-s.start;
 g.setTransform(canvas.width/1080,0,0,canvas.height/1920,0,0);g.globalAlpha=1;
 const scale=Math.max(1080/v.videoWidth,1920/v.videoHeight),sw=1080/scale,sh=1920/scale;
 g.drawImage(v,(v.videoWidth-sw)*(m.focus_x??.5),(v.videoHeight-sh)*(m.focus_y??.5),sw,sh,0,0,1080,1920);
 if(s.chapter){font(38);const w=g.measureText(s.chapter).width+44;box(80,110,w,70,.55);text(s.chapter,102,125,38,'#FFFFFF',900);}
 const p=s.panel;
 if(p){
  box(p.x,p.y,p.w,p.h,p.opacity??.62);g.strokeStyle='rgba(105,219,210,.48)';g.lineWidth=2;g.stroke();
  let yy=p.y+32,active=-1;p.rows.forEach((r,i)=>{if(lt>=r.at)active=i;});
  p.rows.forEach((r,i)=>{
   const size=r.size||76,line=r.line_height||size*1.4,phase=ease((lt-r.at)/.22);
   if(yy+size>p.y+p.h-20)throw Error(`Panel too short in ${s.id}`);
   if(phase>0){
    g.save();g.globalAlpha=phase*(p.active_only&&i!==active?.65:1);
    const color=p.active_only&&i===active?'#FFE36C':(r.color||'#FFFFFF');
    text(r.text,p.x+36,yy+(1-phase)*12,size,color,p.w-72);
    if(r.mark){font(size);const w=g.measureText(r.text).width,y=yy+size*(r.mark==='strike'?.55:1.12);g.beginPath();g.moveTo(p.x+36,y);g.lineTo(p.x+36+w*phase,y);g.lineWidth=5;g.strokeStyle='#FFE36C';g.stroke();}
    g.restore();
   }
   yy+=line;
  });
 }
 if(caption){
  const row=cfg.captions.find(r=>t>=r[0]&&t<r[1]);
  if(row){
   font(54);let lines=[],buf='';
   for(const ch of row[2]){if(ch==='\n'||g.measureText(buf+ch).width>872){lines.push(buf);buf=ch==='\n'?'':ch;}else buf+=ch;}
   if(buf)lines.push(buf);if(lines.length>2)throw Error('Caption exceeds two lines; split the cue');
   const w=Math.max(...lines.map(x=>g.measureText(x).width))+48,y=lines.length>1?1510:1540;
   box((1080-w)/2,y-16,w,lines.length*74+28,.66);
   lines.forEach((line,i)=>{font(54);text(line,(1080-g.measureText(line).width)/2,y+i*74,54,'#FFFFFF',872);});
  }
 }
 return canvas.toDataURL('image/jpeg',.95).split(',')[1];
};
(async()=>{
 cfg=await(await fetch('config.json')).json();canvas.width=cfg.width;canvas.height=cfg.height;
 if(cfg.font_url){const face=new FontFace('OverlayFont',`url(${cfg.font_url})`);await face.load();document.fonts.add(face);cfg.font_family='OverlayFont';}
 await document.fonts.ready;
 await Promise.all(Object.entries(cfg.media).map(async([key,m])=>{
  const response=await fetch(m.file);if(!response.ok)throw Error(`Media fetch failed: ${key}`);
  const v=document.createElement('video');v.muted=true;v.preload='auto';v.playsInline=true;
  v.src=URL.createObjectURL(await response.blob());videos[key]=v;
  await new Promise((resolve,reject)=>{const timer=setTimeout(()=>reject(Error(`Load timeout ${key}`)),30000);v.onloadeddata=()=>{clearTimeout(timer);resolve();};v.onerror=()=>{clearTimeout(timer);reject(Error(`Load failed ${key}`));};v.load();});
 }));
 window.__durations=Object.fromEntries(Object.entries(videos).map(([k,v])=>[k,v.duration]));
 await window.prepare(0);window.renderFrame(0);window.__ready=true;
})().catch(e=>{window.__bootFailed=String(e);console.error(e);});
