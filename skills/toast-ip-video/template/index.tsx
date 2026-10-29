import React from 'react';
import {AbsoluteFill, Composition, Img, interpolate, spring, registerRoot, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';

const FPS=30;
const cream='#f5e9c9', ink='#303141',rust='#a84b35',olive='#667047';
type Row={at:number;main:string;sub?:string;label?:string};
type Scene={start:number;end:number;bg:string;mode?:string;toast?:string;title:string;eyebrow?:string;rows?:Row[];accent?:string;accentAt?:number;record?:string;recordDir?:string;recordFrames?:number;size?:number;side?:string;poses?:{at:number;pose:string}[];footer?:string;footerAt?:number};
type Props={label:string;durationInFrames:number;scenes:Scene[];subtitles:{start:number;end:number;text:string}[]};
const reveal=(t:number,at:number,d=.28)=>interpolate(t,[at,at+d],[0,1],{extrapolateLeft:'clamp',extrapolateRight:'clamp'});
const bounce=(t:number,at:number)=>spring({frame:Math.max(0,(t-at)*FPS),fps:FPS,config:{damping:13,stiffness:185,mass:.65}});
const TextIn:React.FC<{at:number;t:number;children:React.ReactNode;style?:React.CSSProperties}>=({at,t,children,style={}})=>{
 const p=reveal(t,at,.16),b=bounce(t,at),kind=Math.round(at*10)%3;
 const motion=kind===0?`translateX(${(1-b)*-60}px) rotate(${(1-b)*-2}deg)`:kind===1?`translateY(${(1-b)*35}px) scale(${.86+.14*b})`:`scale(${.75+.25*b}) rotate(${(1-b)*3}deg)`;
 return <div style={{...style,opacity:p,transform:motion,transformOrigin:'left center'}}>{children}</div>
};
const rightScene=(s:Scene)=>s.side==='right';
// New production sprite: exact 2x2 cells, displayed as clipped layers without altering source PNG.
const Toast:React.FC<{pose:string;size:number}>=({pose,size})=>{
 const cell={pointer:0,startled:1,thinking:2,wink:3}[pose];
 return cell===undefined?<Img src={staticFile('assets/characters/'+pose+'.png')} style={{width:size,height:size,objectFit:'contain'}}/>:<div style={{width:size,height:size,overflow:'hidden',position:'relative'}}><Img src={staticFile('assets/characters/poses-v2.png')} style={{position:'absolute',width:size*2,height:size*2,maxWidth:'none',left:-(cell%2)*size,top:-Math.floor(cell/2)*size}}/></div>
};
const poseAt=(s:Scene,t:number)=>{
 let pose=s.toast||'toast';
 for(const event of s.poses||[])if(t-s.start>=event.at)pose=event.pose;
 return pose;
};
const Paper:React.FC<{s:Scene;t:number}>=({s,t})=>{
 const enter=reveal(t,s.start,.3);
 return <div style={{position:'absolute',left:rightScene(s)?135:405,top:90,width:1370,height:770,transform:`translateY(${(1-enter)*35}px) rotate(-.35deg)`,opacity:enter}}>
  <div style={{position:'absolute',inset:'10px -8px -12px 10px',background:'#bda379',border:'3px solid #755c45',borderRadius:12}}/>
  <div style={{position:'absolute',inset:0,backgroundColor:cream,backgroundImage:`url(${staticFile('assets/textures/paper.png')})`,border:'4px solid #9a6b49',borderRadius:12,boxShadow:'0 22px 55px #0005'}}>
   <div style={{position:'absolute',left:48,top:0,bottom:0,borderLeft:'2px solid #b7665050'}}/>
   {Array.from({length:9},(_,i)=><div key={i} style={{position:'absolute',left:-19,top:42+i*83,width:40,height:12,border:'5px solid #494239',borderRadius:15,background:'#b8a994',boxShadow:'1px 3px 1px #0004'}}/>)}
   <div style={{position:'absolute',top:-17,right:75,width:190,height:39,background:'#c9b476b5',transform:'rotate(3deg)',border:'1px dashed #b3995d90'}}/>
   <div style={{padding:'48px 65px 30px 83px',color:ink}}>
    <div style={{fontSize:25,letterSpacing:3,color:rust,fontWeight:700}}>{s.eyebrow}</div>
    <div style={{fontSize:57,lineHeight:1.35,fontWeight:700,marginTop:13,marginBottom:25,paddingBottom:18,borderBottom:'3px solid #a84b3570'}}>{s.title}</div>
    {s.mode==='classification'? <div style={{display:'flex',gap:30,marginTop:45}}>{s.rows?.map((r,i)=><TextIn key={i} at={s.start+r.at} t={t} style={{width:548,padding:'32px 29px',height:280,background:i===0?'#dedeb6':'#e8d8b7',border:`3px solid ${i===0?olive:'#ae8760'}`,borderRadius:5}}><div style={{fontSize:23,color:i===0?olive:rust,fontWeight:700,marginBottom:27}}>{r.label||String(i+1).padStart(2,'0')}</div><div style={{fontSize:48,fontWeight:700,whiteSpace:'nowrap'}}>{r.main}</div><div style={{fontSize:31,marginTop:27,lineHeight:1.5}}>{r.sub}</div></TextIn>)}</div>:
    <div style={{display:'flex',flexDirection:'column',gap:25}}>{s.rows?.map((r,i)=><TextIn key={i} at={s.start+r.at} t={t} style={{display:'flex',gap:23,alignItems:'flex-start',minHeight:117}}><span style={{fontSize:31,color:rust,borderBottom:'3px solid #aa573e',paddingTop:10,minWidth:45,fontWeight:700}}>0{i+1}</span><div><div style={{fontSize:43,fontWeight:700,lineHeight:1.48}}>{r.main}</div>{r.sub&&<div style={{fontSize:30,color:'#686148',marginTop:5}}>{r.sub}</div>}</div></TextIn>)}</div>}
    {s.footer&&<TextIn at={s.start+(s.footerAt||0)} t={t} style={{marginTop:35,fontSize:35,color:rust,fontWeight:700}}>{s.footer}</TextIn>}
   </div>
   <div style={{position:'absolute',bottom:19,right:34,fontSize:20,color:'#9c8767',letterSpacing:3}}>TOAST'S NOTES</div>
  </div>
 </div>
};
const Video:React.FC<Props>=({scenes,subtitles,label})=>{
 const frame=useCurrentFrame(),t=frame/FPS;
 const {durationInFrames}=useVideoConfig();
 if(!scenes.length)return <AbsoluteFill/>;
 const s=scenes.find(s=>t>=s.start&&t<s.end)||scenes[scenes.length-1];
 const paper=s.mode==='paper'||s.mode==='classification';const record=s.mode==='record';
 const bgZoom=1.035+(t-s.start)/25*.04;
 const right=rightScene(s),index=scenes.indexOf(s),elapsed=t-s.start;
 const toastHeight=paper?370:record?410:480;
 const baseX=paper?(right?1515:12):record?118:(right?1400:105);
 const baseY=paper?(index%2?440:480):record?405:(index%3===0?385:345);
 const entry=bounce(t,s.start),drift=elapsed>1?Math.sin((elapsed-1)*.75)*15:0;
 const toastX=baseX+(1-entry)*(right?250:-230)+drift;
 const toastY=baseY+(1-entry)*95-Math.abs(Math.sin(elapsed*2.5))*9;
 const pose=poseAt(s,t),tilt=pose==='startled'?Math.sin(elapsed*18)*3:Math.sin(elapsed*2.7)*1.8;
 const progress=frame/Math.max(1,durationInFrames-1),miniX=36+progress*1848;
 const subtitle=subtitles.find(x=>t>=x.start&&t<x.end);
 return <AbsoluteFill style={{background:'#27271f',fontFamily:'Toast',color:cream}}>
  <style>{`@font-face{font-family:Toast;src:url('${staticFile('assets/fonts/regular.ttc')}')}@font-face{font-family:Toast;src:url('${staticFile('assets/fonts/bold.ttc')}');font-weight:700}*{box-sizing:border-box}`}</style>
  <Img src={staticFile(s.bg)} style={{width:'100%',height:'100%',objectFit:'cover',transform:`scale(${bgZoom})`,filter:paper?'blur(15px) brightness(.68) saturate(.8)':'brightness(.77) saturate(.9)'}}/>
  <AbsoluteFill style={{background:paper?'#503a1718':'linear-gradient(90deg,#1b211d10,#151c2060 38%,#1b211d80),linear-gradient(0deg,#141916ce,transparent 35%)'}}/>
  {!paper&&<div style={{position:'absolute',left:72,top:46,fontSize:24,letterSpacing:2,color:'#f4e7c9c0'}}>{label}</div>}
  {paper?<Paper s={s} t={t}/>:record?<>
    <div style={{position:'absolute',left:76,top:170,width:510}}><div style={{fontSize:28,color:'#e7bb76',marginBottom:24}}>{s.eyebrow}</div><div style={{fontSize:60,fontWeight:700,lineHeight:1.42,whiteSpace:'pre-line'}}>{s.title}</div></div>
    <div style={{position:'absolute',left:705,top:47,width:958,height:825,border:'7px solid #e7d7b0',borderRadius:8,overflow:'hidden',background:'#eee8dc',boxShadow:'0 20px 50px #0008'}}><Img src={staticFile(`${s.recordDir}/${String(Math.min(s.recordFrames||1,Math.max(1,Math.floor((t-s.start)*FPS)+1))).padStart(5,'0')}.jpg`)} style={{width:'100%',height:'100%',objectFit:'contain'}}/></div>
    <TextIn at={s.start+(s.footerAt||0)} t={t} style={{position:'absolute',left:87,top:825,fontSize:36,fontWeight:700,color:'#f4cc7e'}}>{s.footer}</TextIn>
  </>:<div style={{position:'absolute',left:right?120:650,top:s.mode==='topics'?210:260,width:1175}}>
    {s.eyebrow&&<div style={{fontSize:31,letterSpacing:1,color:'#ebc891',marginBottom:27}}>{s.eyebrow}</div>}
    <div style={{fontSize:s.mode==='topics'?66:s.mode==='versus'?135:s.size||116,fontWeight:700,lineHeight:1.22,textShadow:'0 5px 20px #0006'}}>{s.title.split('\n').map((line,i)=><TextIn key={i} at={s.start+i*.11} t={t} style={{whiteSpace:'nowrap'}}>{line}</TextIn>)}</div>
    {s.mode==='versus'&&s.rows?.map((r,i)=><TextIn key={i} at={s.start+r.at} t={t} style={{fontSize:130,fontWeight:700,color:'#e9b768',marginTop:5}}>{r.main}</TextIn>)}
    {s.accent&&<TextIn at={s.start+(s.accentAt??2.2)} t={t} style={{fontSize:43,display:'inline-block',borderBottom:'5px solid #cf8b54',paddingBottom:12,marginTop:30}}>{s.accent}</TextIn>}
    {s.mode==='topics'&&<div style={{display:'grid',gridTemplateColumns:'1fr 1fr',gap:22,marginTop:44}}>{s.rows?.map((r,i)=><TextIn t={t} at={s.start+r.at} key={i} style={{fontSize:39,padding:'22px 24px',borderLeft:'5px solid #d3a865',background:'#17232180'}}>{r.main}</TextIn>)}</div>}
  </div>}
  <div style={{position:'absolute',left:toastX+35,top:baseY+toastHeight-24,width:toastHeight*.72,height:25,borderRadius:'50%',background:'#10120c50',filter:'blur(9px)'}}/>
  <div style={{position:'absolute',left:toastX,top:toastY,opacity:reveal(t,s.start,.12),transform:`rotate(${tilt}deg) scale(${.92+.08*entry})`,transformOrigin:'50% 90%',filter:'drop-shadow(5px 10px 4px #0004)'}}><div style={{transform:right&&pose==='pointer'?'scaleX(-1)':undefined}}><Toast pose={pose} size={toastHeight}/></div></div>
  {pose==='thinking'&&<TextIn at={s.start+.6} t={t} style={{position:'absolute',left:toastX+toastHeight*.7,top:toastY-8,fontSize:55,fontWeight:700,color:'#f5cc7d',transformOrigin:'center'}}>?</TextIn>}
  {pose==='wink'&&<div style={{position:'absolute',left:toastX+toastHeight*.83,top:toastY+22,fontSize:37,color:'#f4c864',transform:`scale(${.9+Math.sin(t*5)*.15})`}}>✦</div>}
  {subtitle&&<div style={{position:'absolute',bottom:115,left:100,right:100,textAlign:'center',fontSize:51,fontWeight:700,lineHeight:1.3,color:'#fff9e9',textShadow:'0 3px 3px #000, 2px 0 2px #000,-2px 0 2px #000'}}><span style={{background:'#171b1bd9',borderRadius:6,padding:'10px 26px',boxDecorationBreak:'clone'}}>{subtitle.text}</span></div>}
  <div style={{position:'absolute',bottom:18,left:36,right:36,height:5,borderRadius:4,background:'#f5e4bc40'}}/>
  <div style={{position:'absolute',bottom:18,left:36,height:5,width:progress*1848,borderRadius:4,background:'#e3b766'}}/>
  <div style={{position:'absolute',left:miniX-34,bottom:25+Math.abs(Math.sin(t*6.8))*3,width:68,height:68,transform:`rotate(${Math.sin(t*6.8)*5}deg)`,filter:'drop-shadow(0 2px 2px #0009)'}}><Toast pose={Math.floor(t*1.8)%2?'wink':'toast'} size={68}/></div>
 </AbsoluteFill>
};
const defaults:Props={label:'吐司学长（赶due版）',durationInFrames:30,scenes:[],subtitles:[]};
registerRoot(()=> <Composition id='ToastVideo' component={Video} defaultProps={defaults} durationInFrames={30} fps={FPS} width={1920} height={1080} calculateMetadata={({props})=>({durationInFrames:props.durationInFrames})}/>);
