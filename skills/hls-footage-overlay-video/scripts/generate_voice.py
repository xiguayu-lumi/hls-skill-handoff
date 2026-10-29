"""Design a narration voice with a local VoxCPM2 model; no reference audio needed."""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import re
import subprocess
import sys
import time

DEFAULT_RUNTIME = Path.home()/'.local/share/hls-footage-overlay-video/runtime.json'
PROFILES = Path(__file__).resolve().parents[1]/'assets/voice_profiles.json'

def choose_voice(text, style='auto', description=None):
    profiles=json.loads(PROFILES.read_text(encoding='utf-8'))
    if description:
        return 'custom',description,'Explicit voice description supplied by the caller'
    if style!='auto':
        return style,profiles[style]['description'],'Explicit profile selected for this script'
    scores={k:sum(word.lower() in text.lower() for word in v['keywords']) for k,v in profiles.items()}
    selected=max(scores,key=scores.get) if any(scores.values()) else 'academic'
    return selected,profiles[selected]['description'],f'Keyword fallback selection: {scores}; academic is the general explainer default'

def read_runtime(path):
    if not path.is_file():
        raise ValueError(f'Local runtime config missing: {path}; configure python and model_path first')
    runtime=json.loads(path.read_text(encoding='utf-8-sig'))
    for key in ('python','model_path'):
        if not runtime.get(key):raise ValueError(f'Runtime requires {key}')
        runtime[key]=str((path.parent/Path(runtime[key]).expanduser()).resolve())
    if not Path(runtime['python']).is_file():raise ValueError('Configured Python does not exist')
    model=Path(runtime['model_path'])
    config=json.loads((model/'config.json').read_text(encoding='utf-8'))
    if config.get('architecture','').lower()!='voxcpm2':raise ValueError('Model must be VoxCPM2')
    for name in ('model.safetensors','audiovae.pth','tokenizer.json'):
        if not (model/name).is_file():raise ValueError('Missing local model file '+name)
    return runtime

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--runtime',type=Path,default=DEFAULT_RUNTIME)
    ap.add_argument('--text-file',type=Path,required=True,help='Plain UTF-8 speech body, without delivery instructions')
    ap.add_argument('--output',type=Path,required=True,help='Versioned .wav path')
    ap.add_argument('--style',choices=['auto','academic','friendly','reassuring','story'],default='auto')
    ap.add_argument('--voice-description',help='Content-aware voice description; overrides style')
    ap.add_argument('--seed',type=int,default=2026)
    ap.add_argument('--timesteps',type=int,default=10)
    ap.add_argument('--cfg',type=float,default=2.0)
    ap.add_argument('--max-len',type=int,default=4096)
    ap.add_argument('--device',choices=['cuda','cpu'],help='Defaults to local runtime device, then cuda')
    ap.add_argument('--check',action='store_true',help='Validate configuration and report selected voice, without inference')
    ap.add_argument('--worker',action='store_true',help=argparse.SUPPRESS)
    a=ap.parse_args();runtime=read_runtime(a.runtime.resolve())
    if not 1<=a.timesteps<=100 or not math.isfinite(a.cfg) or not 0<a.cfg<=10 or not 10<=a.max_len<=16000:ap.error('Invalid inference parameters')
    body=re.sub(r'\s+',' ',a.text_file.read_text(encoding='utf-8-sig')).strip()
    if not body:ap.error('Speech body is empty')
    if a.output.suffix.lower()!='.wav':ap.error('Output must end in .wav')
    if a.output.resolve()==a.text_file.resolve():ap.error('Output cannot replace input')
    style,description,reason=choose_voice(body,a.style,a.voice_description)
    description=description.strip()
    if not description or any(c in description for c in '()（）'):ap.error('Voice description must be nonempty and contain no parentheses')
    plan={'engine':'VoxCPM2','mode':'voice_design','style':style,'description':description,'selection_reason':reason,'text':body,'model_path':runtime['model_path'],'device':a.device or runtime.get('device','cuda'),'seed':a.seed,'timesteps':a.timesteps,'cfg':a.cfg,'max_len':a.max_len}
    if a.check:
        print(json.dumps(plan,ensure_ascii=False,indent=2));return
    if not a.worker:
        args=[runtime['python'],str(Path(__file__).resolve()),*sys.argv[1:],'--worker']
        env={**os.environ,'PYTHONUTF8':'1','HF_HUB_OFFLINE':'1','TRANSFORMERS_OFFLINE':'1','TORCH_COMPILE_DISABLE':'1'}
        raise SystemExit(subprocess.call(args,env=env))
    os.environ.update(HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',TORCH_COMPILE_DISABLE='1')
    import importlib.metadata
    import numpy as np
    import soundfile as sf
    import torch
    from voxcpm import VoxCPM
    model=Path(runtime['model_path'])
    plan['voxcpm_version']=importlib.metadata.version('voxcpm')
    plan['model_config_sha256']=hashlib.sha256((model/'config.json').read_bytes()).hexdigest()
    plan['weights_identity']={f.name:{'bytes':f.stat().st_size,'mtime_ns':f.stat().st_mtime_ns} for f in [model/'model.safetensors',model/'audiovae.pth']}
    signature=hashlib.sha256(json.dumps(plan,sort_keys=True,ensure_ascii=False).encode('utf-8')).hexdigest()
    output=a.output.resolve();record=output.with_suffix('.voice.json')
    if output.exists() or record.exists():
        if output.is_file() and record.is_file():
            previous=json.loads(record.read_text(encoding='utf-8'))
            if previous.get('signature')==signature and previous.get('audio_sha256')==hashlib.sha256(output.read_bytes()).hexdigest():
                print(f'CACHE_OK {output}');return
        raise ValueError('Output exists with different or untracked content; choose a new version')
    if plan['device']=='cuda' and not torch.cuda.is_available():raise RuntimeError('CUDA unavailable; configure cpu explicitly or repair runtime')
    torch.manual_seed(a.seed)
    started=time.monotonic()
    print(f'Generating one continuous narration: profile={style}, device={plan["device"]}',flush=True)
    engine=VoxCPM.from_pretrained(runtime['model_path'],device=plan['device'],load_denoiser=False,optimize=False,local_files_only=True)
    # Installed 2.0.3 accepts seed via torch, and max_len (not max_tokens).
    samples=np.asarray(engine.generate(text=f'({description}){body}',cfg_value=a.cfg,inference_timesteps=a.timesteps,max_len=a.max_len,normalize=False,denoise=False,retry_badcase=True,retry_badcase_max_times=2),dtype=np.float32).reshape(-1)
    rate=engine.tts_model.sample_rate
    if len(samples)==0 or not np.isfinite(samples).all():raise RuntimeError('Empty or non-finite generated audio')
    peak=float(np.max(np.abs(samples)));rms=float(np.sqrt(np.mean(samples**2)))
    if rms<.0001:raise RuntimeError('Generated audio is effectively silent')
    gain=min(1.,.98/max(peak,1e-8));samples*=gain
    output.parent.mkdir(parents=True,exist_ok=True)
    temporary=output.with_suffix('.tmp.wav')
    sf.write(str(temporary),samples,rate,subtype='PCM_16');temporary.replace(output)
    result={**plan,'signature':signature,'audio_sha256':hashlib.sha256(output.read_bytes()).hexdigest(),'sample_rate':rate,'samples':len(samples),'duration':len(samples)/rate,'peak_before_gain':peak,'gain':gain,'rms_before_gain':rms,'generation_seconds':round(time.monotonic()-started,3),'method':'single_call_complete_script','text_verified':False,'listening_status':'not_reviewed','alignment_status':'pending'}
    record.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(f'WAV={output} DURATION={result["duration"]:.3f}s SR={rate}',flush=True)

if __name__=='__main__':main()
