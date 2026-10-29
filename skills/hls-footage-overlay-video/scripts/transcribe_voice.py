"""Local ASR timestamps and an independent script comparison (not forced alignment)."""
import argparse
import difflib
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import unicodedata
import wave

def normalized(text):
    return ''.join(c.lower() for c in unicodedata.normalize('NFKC', text) if c.isalnum())

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--runtime',type=Path,default=Path.home()/'.local/share/hls-footage-overlay-video/runtime.json')
    ap.add_argument('--audio',type=Path,required=True)
    ap.add_argument('--text-file',type=Path,required=True)
    ap.add_argument('--output',type=Path,required=True,help='New JSON report; sibling .srt is also written')
    ap.add_argument('--worker',action='store_true',help=argparse.SUPPRESS)
    a=ap.parse_args()
    r=json.loads(a.runtime.read_text(encoding='utf-8-sig'))
    for key in ('asr_python','asr_model_path'):
        if not r.get(key):ap.error('Runtime requires '+key)
        r[key]=str((a.runtime.resolve().parent/Path(r[key]).expanduser()).resolve())
    if not a.worker:
        raise SystemExit(subprocess.call([r['asr_python'],str(Path(__file__).resolve()),*sys.argv[1:],'--worker'],env={**os.environ,'PYTHONUTF8':'1','HF_HUB_OFFLINE':'1'}))
    if a.output.exists() or a.output.with_suffix('.srt').exists():ap.error('Choose a new report version')
    from faster_whisper import WhisperModel
    with wave.open(str(a.audio),'rb') as wav:duration=wav.getnframes()/wav.getframerate()
    model=WhisperModel(r['asr_model_path'],device='cpu',compute_type='int8',cpu_threads=4,local_files_only=True)
    segments,_=model.transcribe(str(a.audio),language='zh',beam_size=5,word_timestamps=True,vad_filter=True,condition_on_previous_text=False)
    rows=[];captions=[]
    for seg in segments:
        words=[{'start':w.start,'end':w.end,'text':w.word} for w in seg.words or []]
        rows.append({'start':seg.start,'end':seg.end,'text':seg.text,'words':words})
        # Break at measured word boundaries, never divide duration by character count.
        group=[]
        for w in words:
            if group and len(''.join(x['text'] for x in group))+len(w['text'])>18:
                captions.append([group[0]['start'],group[-1]['end'],''.join(x['text'] for x in group).strip()]);group=[]
            group.append(w)
        if group:captions.append([group[0]['start'],group[-1]['end'],''.join(x['text'] for x in group).strip()])
    expected=a.text_file.read_text(encoding='utf-8-sig').strip()
    heard=''.join(s['text'] for s in rows).strip()
    x,y=normalized(expected),normalized(heard)
    ratio=difflib.SequenceMatcher(None,x,y).ratio()
    result={'method':'faster-whisper ASR word timestamps; not forced alignment','audio_duration':duration,'audio_sha256':hashlib.sha256(a.audio.read_bytes()).hexdigest(),'model':r['asr_model_path'],'expected_text':expected,'recognized_text':heard,'normalized_exact_match':x==y,'similarity':ratio,'status':'TEXT_MATCH' if x==y else 'REVIEW_TEXT','listening_status':'not_reviewed','segments':rows,'captions':captions}
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    def stamp(t):
        ms=round(t*1000);h,ms=divmod(ms,3600000);m,ms=divmod(ms,60000);s,ms=divmod(ms,1000)
        return f'{h:02}:{m:02}:{s:02},{ms:03}'
    a.output.with_suffix('.srt').write_text('\n\n'.join(f'{i}\n{stamp(s)} --> {stamp(e)}\n{t}' for i,(s,e,t) in enumerate(captions,1))+'\n',encoding='utf-8')
    print(json.dumps({k:result[k] for k in ('status','recognized_text','similarity','audio_duration')},ensure_ascii=False))
    if not x==y:raise SystemExit(2)

if __name__=='__main__':main()
