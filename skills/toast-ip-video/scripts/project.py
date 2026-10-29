"""Portable project setup, timing/media checks and recording-frame preparation."""
import argparse, json, math, re, shutil, subprocess
from pathlib import Path

PACK = Path(__file__).resolve().parents[1]
FPS = 30
POSES = {'toast','deadpan','question','panic','idea','proud','pointer','startled','thinking','wink'}

def run(args):
    subprocess.run([str(a) for a in args], check=True)

def probe(path):
    return json.loads(subprocess.check_output(['ffprobe','-v','error','-show_format','-show_streams','-of','json',str(path)]))

def save(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf8')

def media(project, name):
    root = (project/'public').resolve()
    p = (root/name).resolve()
    if not p.is_relative_to(root) or not p.is_file():
        raise ValueError(f'Missing media or path outside public: {name}')
    return p

def read_srt(path):
    def seconds(v):
        h,m,s = v.replace(',', '.').split(':')
        return 3600*int(h)+60*int(m)+float(s)
    cues=[]
    for block in re.split(r'\n\s*\n', path.read_text('utf-8-sig').strip()):
        lines=block.splitlines()
        at=next((i for i,l in enumerate(lines) if '-->' in l), None)
        if at is None: raise ValueError('Invalid SRT block')
        a,b=lines[at].split('-->')
        cues.append(dict(start=seconds(a.strip()), end=seconds(b.strip()), text=' '.join(lines[at+1:])))
    return cues

def validate(project, c):
    audio=probe(media(project,c['voice']))
    if not any(s['codec_type']=='audio' for s in audio['streams']): raise ValueError('Voice has no audio')
    duration=float(audio['format']['duration'])
    if not math.isfinite(duration) or duration<=0: raise ValueError('Invalid voice duration')
    frames=math.ceil(duration*FPS)
    end=frames/FPS
    c.update(durationInFrames=frames, fps=FPS, width=1920, height=1080)
    if not c.get('scenes'): raise ValueError('Write scenes from the NEW narration before rendering')
    cursor=0
    for i,s in enumerate(c['scenes']):
        a,b=s['start'],s['end']
        if not (0<=a<b<=end+.001) or abs(a-cursor)>1/FPS+.001:
            raise ValueError(f'Scene {i}: gap, overlap or invalid range')
        cursor=b
        media(project,s['bg'])
        if s.get('mode','scene') not in {'scene','paper','classification','topics','versus','record'}:
            raise ValueError(f'Scene {i}: unknown mode')
        if s.get('side','left') not in {'left','right'}: raise ValueError('Invalid side')
        if s.get('toast','toast') not in POSES: raise ValueError('Unknown toast pose')
        if not s.get('title'): raise ValueError(f'Scene {i}: title required')
        if s.get('mode')=='classification' and len(s.get('rows',[]))!=2:
            raise ValueError('Classification needs exactly two columns')
        if s.get('mode')=='paper' and len(s.get('rows',[]))>3:
            raise ValueError('Split more than three paper rows into another scene')
        if s.get('mode')=='topics' and len(s.get('rows',[]))>4:
            raise ValueError('Topics layout fits at most four items')
        if s.get('mode')=='versus' and len(s.get('rows',[]))!=1:
            raise ValueError('Versus layout expects title plus one row')
        for field in ['rows','poses']:
            previous=-1
            for event in s.get(field,[]):
                if not 0<=event['at']<b-a or event['at']<previous:
                    raise ValueError(f'Scene {i}: {field}.at must be sorted seconds RELATIVE to scene')
                previous=event['at']
                if field=='poses' and event['pose'] not in POSES: raise ValueError('Unknown event pose')
        if s.get('mode')=='record':
            recording=probe(media(project,s['record']))
            start=s.get('recordStart',0)
            if not 0<=start<float(recording['format']['duration']): raise ValueError('Invalid recordStart')
        if i and s.get('mode') in {'paper','classification'} and s['bg']!=c['scenes'][i-1]['bg']:
            print(f'REVIEW: scene {i} paper changes previous background')
    if abs(cursor-end)>1/FPS+.001: raise ValueError('Last scene must cover rounded voice duration')
    previous=0
    if not c.get('subtitles'): raise ValueError('Corrected timed subtitles required')
    for cue in c['subtitles']:
        if not (previous-.001<=cue['start']<cue['end']<=end+.001) or not cue['text'].strip():
            raise ValueError('Invalid/overlapping subtitle cue')
        previous=cue['end']
        weight=sum(.52 if ch.isascii() else 1 for ch in cue['text'])
        if weight>30: raise ValueError('Subtitle too long: split by natural clause, preserving English words')
    if c['subtitles'][0]['start']>2 or end-c['subtitles'][-1]['end']>2:
        print('REVIEW: first/last subtitle more than 2 seconds from audio boundary; listen for missing ASR')
    for e in c.get('effects',[]):
        if not 0<=e['at']<end: raise ValueError('SFX out of range')
        media(project,e['file'])
    if c.get('music') and c['music']!='generated': media(project,c['music'])
    if not 10<=c.get('musicBelowVoiceDb',20)<=40: raise ValueError('musicBelowVoiceDb expected 10..40')
    return c

def init(dest, voice, srt):
    if dest.exists(): raise FileExistsError(f'Refusing to overwrite project: {dest}')
    dest.mkdir(parents=True)
    (dest/'CODEX.md').write_text('# 吐司视频项目\n\n公共素材只读；本期 video.json 可编辑。成片输出 ../05_最终交付 或渲染时指定路径。\n',encoding='utf8')
    (dest/'项目索引.md').write_text('# 项目索引\n\n状态：筹备中。来源：toast-ip-video。下一步：按新稿和真实配音生成字幕与分镜。\n',encoding='utf8')
    for p in (PACK/'template').iterdir():
        if p.is_file(): shutil.copy2(p,dest/p.name)
    for name in ['characters','scenes','textures','audio','fonts','recordings']:
        shutil.copytree(PACK/'assets'/name,dest/'public/assets'/name)
    c=json.loads((dest/'video.json').read_text('utf8'))
    if voice:
        target='voice'+voice.suffix.lower()
        shutil.copy2(voice,dest/'public'/target)
        c['voice']=target
        duration=float(probe(voice)['format']['duration'])
        c['durationInFrames']=math.ceil(duration*FPS)
    if srt: c['subtitles']=read_srt(srt)
    save(dest/'video.json',c)
    print(f'Created {dest}; write scenes then run prepare')

def prepare(project, c):
    for i,s in enumerate(c['scenes']):
        if s.get('mode')!='record': continue
        folder=project/'public/cache'/f'record-{i}'
        folder.mkdir(parents=True,exist_ok=True)
        root=(project/'public/cache').resolve()
        if not folder.resolve().is_relative_to(root): raise ValueError('Cache path escapes project')
        for old in folder.glob('*.jpg'): old.unlink()
        run(['ffmpeg','-v','error','-y','-ss',s.get('recordStart',0),'-i',media(project,s['record']),
             '-t',s['end']-s['start'],'-vf','fps=30,scale=958:830:force_original_aspect_ratio=decrease',
             '-q:v','3',folder/'%05d.jpg'])
        count=len(list(folder.glob('*.jpg')))
        if not count: raise ValueError('No recording frames decoded')
        s['recordFrames']=count
        s['recordDir']=f'cache/record-{i}'
    save(project/'video.json',c)
    def stamp(t):
        ms=round(t*1000)
        return f'{ms//3600000:02}:{ms//60000%60:02}:{ms//1000%60:02},{ms%1000:03}'
    (project/'subtitles.srt').write_text('\n\n'.join(
        f'{i+1}\n{stamp(cue["start"])} --> {stamp(cue["end"])}\n{cue["text"]}'
        for i,cue in enumerate(c['subtitles']))+'\n', encoding='utf8')
    print(f'Prepared {c["durationInFrames"]} frames at {FPS} fps')

def check_fixture():
    # Small executable check for real subtitle time parsing and multi-line text.
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        p=Path(tmp)/'fixture.srt'
        p.write_text('1\n00:00:01,250 --> 00:00:03,500\nHello\n同学\n',encoding='utf8')
        assert read_srt(p)==[{'start':1.25,'end':3.5,'text':'Hello 同学'}]
    print('SRT timing check passed')

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('action',choices=['init','check','prepare','self-check'])
    p.add_argument('project',type=Path,nargs='?')
    p.add_argument('--voice',type=Path);p.add_argument('--srt',type=Path)
    args=p.parse_args()
    if args.action=='self-check': check_fixture()
    elif args.project is None: p.error('project path required')
    elif args.action=='init': init(args.project.resolve(),args.voice,args.srt)
    else:
        c=json.loads((args.project/'video.json').read_text('utf-8-sig'))
        if args.srt: c['subtitles']=read_srt(args.srt)
        c=validate(args.project,c)
        if args.action=='prepare': prepare(args.project,c)
        else: print(f'Valid: {c["durationInFrames"]} frames; {len(c["scenes"])} scenes')
