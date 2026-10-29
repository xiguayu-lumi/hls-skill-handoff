"""Offline regression checks of actual captions and the pinned voice; no TTS."""
from pathlib import Path
import importlib.util, json, hashlib, tempfile, wave, sys
import numpy as np
from PIL import Image
from prepare_defaults import apply_defaults, SKILL

def load_module(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def check(project):
    project=Path(project).resolve()
    caption=load_module('baseline_caption',SKILL/'patches/caption_assets.py')
    profile=json.loads((SKILL/'assets/voices/hls-essay-male-20261014/profile.json').read_text(encoding='utf-8-sig'))
    with wave.open(str(project/'02_脚本与配音/旁白_v2.wav'),'rb') as stream:
        rate=stream.getframerate()
        stream.setpos(round(profile['source_interval'][0]*rate))
        expected=stream.readframes(round((profile['source_interval'][1]-profile['source_interval'][0])*rate))
    with wave.open(str(SKILL/'assets/voices/hls-essay-male-20261014/reference.wav'),'rb') as stream:
        assert stream.readframes(stream.getnframes())==expected
        assert stream.getframerate()==48000
    cases=0
    widths=[]
    with tempfile.TemporaryDirectory(prefix='hls-baseline-') as directory:
        job=Path(directory)/'job'
        job.mkdir()
        (job/'job.json').write_text('{}',encoding='utf-8')
        apply_defaults(job)
        manifest=json.loads((job/'job.json').read_text(encoding='utf-8'))
        assert manifest['voxcpm']['voice']==profile['id'] and manifest['voxcpm']['mode']=='combined'
        assert manifest['voxcpm']['seed']==2027 and manifest['voxcpm']['max_tokens']==10000
        model=Path(manifest['voxcpm']['model_path'])
        assert hashlib.sha256((model/'config.json').read_bytes()).hexdigest()==profile['model_config_sha256']
        scripts=SKILL.parent/'sweety-handdraw-video/scripts'
        sys.path.insert(0,str(scripts))
        from voice_studio import voice_reference
        reference, transcript=voice_reference(manifest['voxcpm'],job)
        assert hashlib.sha256(reference.read_bytes()).hexdigest()==profile['reference_sha256']
        assert transcript==(SKILL/'assets/voices/hls-essay-male-20261014/reference.txt').read_text(encoding='utf-8').strip()
        sys.path.insert(0,str(SKILL/'scripts'))
        adapter=load_module('pinned_voxcpm',SKILL/'patches/voxcpm_voice.py')
        try:
            adapter.generate(job)
        except (ValueError,FileNotFoundError) as error:
            assert 'material' in str(error).lower()
        else:
            raise AssertionError('Voice generation must refuse unreviewed materials')
        alignment=json.loads((project/'03_制作工程/手绘成片_v1/inputs/narration/alignment.json').read_text(encoding='utf-8'))
        assets=job/'review'
        assets.mkdir()
        for beat in alignment['beats']:
            for cue in beat['caption_cues']:
                name=f'caption-{cases}'
                meta=caption.build_caption(assets,name,cue['text'],manifest['captions'],1080,1920)
                assert len(meta['lines'])<=2 and meta['width']<=1080*.85
                assert ''.join(meta['lines']).replace(' ','')==cue['text'].replace(' ','')
                assert all(not line.startswith(tuple('，。？！、；：,.!?;:')) for line in meta['lines'][1:])
                image=np.array(Image.open(assets/f'{name}.png').convert('RGBA'))
                assert np.all(image[:,:,:3]==0) and meta['stroke_width']==0 and meta['shadow'] is None
                assert np.any(image[:,:,3])
                assert not np.any(image[0,:,3]) and not np.any(image[-1,:,3])
                widths.append(meta['width'])
                cases+=1
        meta=caption.build_caption(assets,'english','这是你的 thesis statement，一句话说清立场。',manifest['captions'],1080,1920)
        assert any('thesis' in line for line in meta['lines']) and any('statement' in line for line in meta['lines'])
        old=manifest['captions'].copy()
        old['embolden_px']=0
        caption.build_caption(assets,'plain','观点与结构',old,1080,1920)
        caption.build_caption(assets,'bold','观点与结构',manifest['captions'],1080,1920)
        count=lambda name:np.count_nonzero(np.array(Image.open(assets/f'{name}.png'))[:,:,3])
        assert count('bold')>count('plain')
        explicit={'font':{'path':'chosen.ttf'},'captions':{'font_size':80,'color':'#123456'},'voxcpm':{'voice':'explicit-other'}}
        (job/'job.json').write_text(json.dumps(explicit),encoding='utf-8')
        apply_defaults(job)
        result=json.loads((job/'job.json').read_text(encoding='utf-8'))
        assert result['font']==explicit['font'] and result['captions']['font_size']==80 and result['captions']['color']=='#123456'
        assert result['voxcpm']==explicit['voxcpm']
        existing={'narration':{'source':'already.wav'}}
        (job/'job.json').write_text(json.dumps(existing),encoding='utf-8')
        apply_defaults(job)
        assert 'voxcpm' not in json.loads((job/'job.json').read_text(encoding='utf-8'))
    return {'voice_excerpt_pcm_equal':True,'voice_adapter_reference_resolves':True,'model_config_matches':True,
            'caption_cues':cases,'max_caption_width':max(widths),'black_no_outline_no_shadow':True,
            'english_words_preserved':True,'bold_area_increased':True,'explicit_settings_preserved':True,
            'existing_narration_preserved':True,'voice_generation_blocked_without_material_approval':True,
            'new_tts_generated':False,'new_video_rendered':False}

if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser()
    parser.add_argument('--project',required=True)
    print(json.dumps(check(parser.parse_args().project),ensure_ascii=False))
