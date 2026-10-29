"""Apply documented defaults before production without generating media."""
import argparse, hashlib, json, shutil
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1]
def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def apply_defaults(job):
    job = Path(job).resolve()
    manifest_path = job/'job.json'
    manifest = json.loads(manifest_path.read_text(encoding='utf-8-sig'))
    defaults = json.loads((SKILL/'assets/production-defaults.json').read_text(encoding='utf-8'))
    profile_path = SKILL/defaults['voice_profile']
    profile = json.loads(profile_path.read_text(encoding='utf-8'))
    voice_source = profile_path.parent/profile['reference_audio']
    text = (profile_path.parent/profile['reference_text']).read_text(encoding='utf-8').strip()
    if digest(voice_source) != profile['reference_sha256'] or hashlib.sha256(text.encode()).hexdigest()!=profile['transcript_sha256']:
        raise ValueError('Pinned voice reference or transcript changed')
    font_source = SKILL/defaults['captions']['font_asset']
    if digest(font_source) != defaults['captions']['font_sha256']:
        raise ValueError('Pinned subtitle font changed')
    for source, relative in [(voice_source,'inputs/pinned-voice/reference.wav'),
                             (profile_path.parent/profile['reference_text'],'inputs/pinned-voice/reference.txt'),
                             (font_source,'inputs/fonts/思源宋体-Medium.ttf')]:
        target=job/relative
        target.parent.mkdir(parents=True,exist_ok=True)
        if target.exists() and digest(target)!=digest(source):
            raise ValueError('Existing job asset differs: '+relative)
        if not target.exists():
            shutil.copy2(source,target)
    manifest.setdefault('canvas',defaults['canvas'])
    manifest.setdefault('font',{'path':defaults['body_font']['path'],'index':0})
    captions=manifest.setdefault('captions',{})
    for key,value in defaults['captions'].items():
        if key not in ('font_asset','font_sha256'):
            captions.setdefault(key,value)
    captions.setdefault('font',{'path':str(job/'inputs/fonts/思源宋体-Medium.ttf'),'index':0})
    # Existing narration and explicit voice settings always take precedence.
    if not manifest.get('narration',{}).get('source'):
        voice=manifest.setdefault('voxcpm',{})
        if not voice or voice.get('voice')==profile['id']:
            settings={'voice':profile['id'],'mode':'combined','backend':'pytorch','device':'cuda','optimize':False,
                      'reference_audio':'inputs/pinned-voice/reference.wav','reference_text':text,
                      'reference_sha256':profile['reference_sha256'],'model_path':profile['model_path'],
                      'model_config_sha256':profile['model_config_sha256'],'seed':profile['seed'],
                      'timesteps':profile['timesteps'],'cfg_value':profile['cfg_value'],'max_tokens':profile['original_max_len']}
            for key,value in settings.items():
                voice.setdefault(key,value)
    manifest_path.write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    receipt={'profile_version':defaults['version'],'voice_id':profile['id'],
             'applied_voice_id':manifest.get('voxcpm',{}).get('voice') if not manifest.get('narration',{}).get('source') else 'existing_narration',
             'voice_reference_sha256':profile['reference_sha256'],'subtitle_font_sha256':defaults['captions']['font_sha256'],
             'media_generated':False,'explicit_values_preserved':True}
    (job/'production-defaults-receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf-8')
    return receipt

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--job',required=True)
    print(json.dumps(apply_defaults(parser.parse_args().job),ensure_ascii=False))
