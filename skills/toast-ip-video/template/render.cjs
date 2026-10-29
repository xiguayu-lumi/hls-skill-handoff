// Use local npm dependencies, or point REMOTION_DEPS to an existing node_modules parent.
const path=require('path'), fs=require('fs');
const {createRequire}=require('module');
const {spawnSync}=require('child_process');
const env=process.env.REMOTION_DEPS||__dirname;
const dep=createRequire(path.resolve(env,'package.json'));
const {bundle}=dep('@remotion/bundler');
const {selectComposition,renderStill,renderMedia}=dep('@remotion/renderer');
const props=JSON.parse(fs.readFileSync(path.join(__dirname,'video.json'),'utf8'));
const opts={chromiumOptions:{gl:'swiftshader'},...(process.env.REMOTION_BROWSER?{browserExecutable:process.env.REMOTION_BROWSER}:{})};
async function main(){
 if(!props.durationInFrames||!props.scenes.length)throw Error('Run project.py prepare before rendering');
 const serveUrl=await bundle({entryPoint:path.join(__dirname,'index.tsx'),publicDir:path.join(__dirname,'public'),webpackOverride:c=>({...c,resolve:{...c.resolve,modules:[path.join(env,'node_modules'),'node_modules']}})});
 const composition=await selectComposition({serveUrl,id:'ToastVideo',inputProps:props,...opts});
 const args=process.argv.slice(2);
 if(args[0]==='--stills'){
  const out=path.join(__dirname,'review');fs.mkdirSync(out,{recursive:true});
  const times=args[1]?args[1].split(',').map(Number):props.scenes.map(s=>Math.min(s.start+.8,s.end-1/30));
  for(const sec of times){
   const frame=Math.min(props.durationInFrames-1,Math.max(0,Math.round(sec*30)));
   await renderStill({serveUrl,composition,inputProps:props,...opts,frame,output:path.join(out,`frame-${frame}.png`)});
   console.log(`STILL ${frame}`);
  }
  return;
 }
 const output=path.resolve(args[0]||path.join(__dirname,'../05_最终交付/toast-v1.mp4'));
 if(fs.existsSync(output))throw Error(`Choose a new version; output exists: ${output}`);
 const mix=path.join(__dirname,'mix.wav');
 if(!fs.existsSync(mix))throw Error('Run scripts/audio.py with this project before final render');
 fs.mkdirSync(path.dirname(output),{recursive:true});
 const silent=path.join(__dirname,'silent.mp4');
 let last=-10;
 await renderMedia({serveUrl,composition,inputProps:props,...opts,codec:'h264',crf:18,pixelFormat:'yuv420p',muted:true,concurrency:4,outputLocation:silent,onProgress:p=>{const n=Math.floor(p.progress*100);if(n>=last+10){console.log(`RENDER ${n}%`);last=n;}}});
 const r=spawnSync('ffmpeg',['-v','error','-n','-i',silent,'-i',mix,'-map','0:v:0','-map','1:a:0','-c:v','copy','-c:a','aac','-b:a','192k','-t',String(props.durationInFrames/30),'-movflags','+faststart',output],{stdio:'inherit'});
 if(r.status!==0)throw Error('Final audio mux failed; silent render retained');
 fs.unlinkSync(silent);
 console.log(`COMPLETE ${output}`);
}
main().catch(e=>{console.error(e);process.exit(1)});
