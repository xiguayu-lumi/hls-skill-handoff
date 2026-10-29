"""Render a config-driven footage overlay film with original audio at t=0."""
import argparse
import base64
import functools
import http.server
import json
import math
import subprocess
import tempfile
import threading
from pathlib import Path

def probe(path):
    return json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(path)]))

def load_config(path):
    c=json.loads(path.read_text(encoding='utf-8-sig'))
    for key in ('width','height','fps','duration'):
        if not isinstance(c.get(key),(int,float)) or not math.isfinite(c[key]) or c[key]<=0: raise ValueError(f'Invalid {key}')
    if any(int(c[k])!=c[k] for k in ('width','height','fps')): raise ValueError('Size and fps must be integers')
    if c['width']%2 or c['height']%2: raise ValueError('Video dimensions must be even')
    if abs(c['width']/c['height']-9/16)>.001: raise ValueError('Starter layout supports 9:16; adapt engine.js for other ratios')
    if abs(c['duration']*c['fps']-round(c['duration']*c['fps']))>1e-5: raise ValueError('Duration must contain a whole number of frames')
    end=0;ids=set()
    for s in c['scenes']:
        if s['id'] in ids or abs(s['start']-end)>.00001 or s['end']<=s['start']: raise ValueError('Duplicate ID, gap, overlap or invalid scene')
        ids.add(s['id']);end=s['end']
        if s['asset'] not in c['media']: raise ValueError('Missing asset '+s['asset'])
        if s.get('offset',0)<0: raise ValueError('Negative media offset')
        p=s.get('panel')
        if p:
            if p['x']<0 or p['y']<0 or p['w']<=72 or p['h']<=0 or p['x']+p['w']>1080 or p['y']+p['h']>1920: raise ValueError('Panel outside design canvas')
            if not 0<=p.get('opacity',.62)<=1: raise ValueError('Invalid opacity')
            at=-1
            for r in p['rows']:
                if not 0<=r['at']<s['end']-s['start'] or r['at']<at: raise ValueError('Row timing must be ordered within scene')
                if not r['text'] or r.get('size',76)<=0: raise ValueError('Invalid row')
                if r.get('mark') not in (None,'underline','strike'): raise ValueError('Unknown mark')
                at=r['at']
    if abs(end-c['duration'])>1e-5: raise ValueError('Scenes must cover entire duration')
    end=0
    for a,b,text in c['captions']:
        if a<end or not a<b<=c['duration'] or not text: raise ValueError('Invalid caption time or text')
        end=b
    mapping={}
    for key,m in c['media'].items():
        f=(path.parent/m['file']).resolve()
        if not f.is_file(): raise ValueError(f'Missing media {f}')
        info=probe(f);stream=next((s for s in info['streams'] if s['codec_type']=='video'),None)
        if stream is None: raise ValueError(f'Not a video {f}')
        duration=float(info['format']['duration'])
        for s in c['scenes']:
            if s['asset']==key and not s.get('loop',False) and s.get('offset',0)+s['end']-s['start']>duration+.001: raise ValueError(f'Clip too short for {s["id"]}; trim/select footage or explicitly enable loop')
        for field in ('focus_x','focus_y'):
            if not 0<=m.get(field,.5)<=1: raise ValueError('Focus must be 0..1')
        mapping[f'/media/{len(mapping)}']=f;m['file']=list(mapping)[-1]
    audio=(path.parent/c['audio']).resolve()
    info=probe(audio)
    if not any(s['codec_type']=='audio' for s in info['streams']): raise ValueError('Missing audio stream')
    if float(info['format']['duration'])>c['duration']+.05: raise ValueError('Duration would truncate audio')
    if c.get('font_file'):
        f=(path.parent/c['font_file']).resolve()
        if not f.is_file(): raise ValueError('Missing font file')
        mapping['/font.woff']=f;c['font_url']='/font.woff'
    return c,mapping,audio

def srt_time(t):
    ms=round(t*1000);h,ms=divmod(ms,3600000);m,ms=divmod(ms,60000);s,ms=divmod(ms,1000)
    return f'{h:02}:{m:02}:{s:02},{ms:03}'

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--config',type=Path,required=True)
    ap.add_argument('--output',type=Path,help='Versioned output prefix, not a directory')
    ap.add_argument('--check',action='store_true')
    ap.add_argument('--stills',action='store_true')
    ap.add_argument('--full',action='store_true')
    ap.add_argument('--channel',choices=['chrome','msedge'],help='Use an installed browser instead of bundled Chromium')
    a=ap.parse_args();config=a.config.resolve();c,mapping,audio=load_config(config)
    if not a.check and not a.stills and not a.full: ap.error('Choose --check, --stills or --full')
    if a.check: print('Config and input media valid')
    if not(a.stills or a.full): return
    if not a.output: ap.error('--output required when rendering')
    out=a.output.resolve();out.parent.mkdir(parents=True,exist_ok=True)
    targets=[Path(str(out)+suffix) for suffix in ('_captioned.mp4','_clean.mp4','.srt','_stills','_render.json')]
    if any(p.exists() for p in targets): ap.error('Output prefix already exists; choose a new version')
    from playwright.sync_api import sync_playwright
    starter=Path(__file__).resolve().parents[1]/'assets/starter'
    for name in ('index.html','engine.js'):
        local=config.parent/name;mapping['/'+name]=local if local.exists() else starter/name
    errors=[]
    with tempfile.TemporaryDirectory(prefix='footage-render-') as td:
        temp=Path(td);(temp/'config.json').write_text(json.dumps(c,ensure_ascii=False),encoding='utf-8');mapping['/config.json']=temp/'config.json'
        class Handler(http.server.SimpleHTTPRequestHandler):
            def log_message(self,*args): pass
            def translate_path(self,path): return str(mapping.get(path.split('?')[0],temp/'absent'))
        server=http.server.ThreadingHTTPServer(('127.0.0.1',0),Handler)
        threading.Thread(target=server.serve_forever,daemon=True).start()
        try:
            with sync_playwright() as pw:
                browser=pw.chromium.launch(channel=a.channel);page=browser.new_page(viewport={'width':c['width'],'height':c['height']})
                page.on('pageerror',lambda e:errors.append(str(e)))
                page.goto(f'http://127.0.0.1:{server.server_port}/index.html')
                page.wait_for_function('window.__ready || window.__bootFailed',timeout=120000)
                if page.evaluate('window.__bootFailed || null'): raise RuntimeError(page.evaluate('window.__bootFailed'))
                def grab(t,caption): return base64.b64decode(page.evaluate('async q=>{await prepare(q.t);return renderFrame(q.t,q.caption)}',{'t':t,'caption':caption}))
                if a.stills:
                    targets[3].mkdir()
                    for s in c['scenes']:
                        times=sorted(set([s['start']+.1*(s['end']-s['start']),s['end']-1/c['fps']]+[s['start']+r['at']+.24 for r in s.get('panel',{}).get('rows',[]) if s['start']+r['at']+.24<s['end']]))
                        for t in times: (targets[3]/f'{t:08.3f}.jpg').write_bytes(grab(t,True))
                if a.full:
                    count=round(c['duration']*c['fps'])
                    for idx,caption in enumerate((True,False)):
                        silent=temp/'silent.mp4'
                        cmd=['ffmpeg','-y','-v','error','-f','image2pipe','-framerate',str(c['fps']),'-c:v','mjpeg','-i','-','-c:v','libx264','-preset','fast','-crf','18','-pix_fmt','yuv420p',str(silent)]
                        proc=subprocess.Popen(cmd,stdin=subprocess.PIPE)
                        try:
                            for i in range(count):
                                proc.stdin.write(grab(i/c['fps'],caption))
                                if i%(c['fps']*3)==0: print(f'version {idx+1}: {i}/{count}',flush=True)
                            proc.stdin.close()
                            if proc.wait(): raise RuntimeError('Encoder failed')
                        finally:
                            if proc.poll() is None: proc.kill();proc.wait()
                        subprocess.run(['ffmpeg','-y','-v','error','-i',str(silent),'-i',str(audio),'-map','0:v:0','-map','1:a:0','-af','apad','-t',str(c['duration']),'-c:v','copy','-c:a','aac','-b:a','256k','-movflags','+faststart',str(targets[idx])],check=True)
                    targets[2].write_text('\n\n'.join(f'{i+1}\n{srt_time(r[0])} --> {srt_time(r[1])}\n{r[2]}' for i,r in enumerate(c['captions']))+'\n',encoding='utf-8')
                browser.close()
        except Exception as exc:
            errors.append(str(exc))
            raise
        finally:
            server.shutdown();server.server_close()
            targets[4].write_text(json.dumps({'errors':errors,'config':str(config)},ensure_ascii=False,indent=2),encoding='utf-8')
    if errors: raise RuntimeError(errors)

if __name__=='__main__': main()
