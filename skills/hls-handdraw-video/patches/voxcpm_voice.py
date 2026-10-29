#!/usr/bin/env python3
"""HLS full-script synthesis with a pinned local VoxCPM2; upstream reference checks remain active.

HLS deliberately overrides upstream semantic-chunk synthesis. After generation, use upstream
align.py and production audio gates before building; no fabricated alignment is emitted.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
from voice_studio import voice_reference, load_voice_catalog
from narration_master import generation_target


def resolved_options(options, root):
    catalog = load_voice_catalog(root)
    identifier = options.get('voice', catalog['default'])
    profile = next((voice for voice in catalog['voices'] if voice['id'] == identifier), {})
    approved = profile.get('verified_generation_parameters', {})
    fields = ('mode', 'cfg_value', 'timesteps', 'seed', 'max_tokens', 'model_path', 'enhancement_model_path', 'backend', 'device', 'optimize', 'style')
    defaults = {key: approved[key] for key in fields if key in approved}
    return {**defaults, 'voice': identifier, **options}


def enhancement_fingerprint(path):
    if not path:
        return None
    directory = Path(path).expanduser().resolve()
    weights = directory/'model.safetensors'
    if not directory.is_dir() or not weights.is_file():
        raise ValueError('Speech cleanup requires an explicitly configured, installed local model')
    return {'model_path':str(directory), 'weights_sha256':hashlib.sha256(weights.read_bytes()).hexdigest()}


def generation_kwargs(params, text, reference=None, transcript=None):
    """Official defaults: cfg 2.0, 10 steps; max length = 6 patches per text token + 10 (retry_badcase)."""
    kwargs = {'text': text, 'inference_timesteps': params['timesteps'], 'cfg_value': params['cfg_value'], 'max_tokens': len(text) * 6 + 10}
    if params['mode'] == 'combined':
        return {**kwargs, 'ref_audio': str(reference), 'prompt_audio': str(reference), 'prompt_text': transcript}
    if params['mode'] == 'reference':
        return {**kwargs, 'ref_audio': str(reference), **({'instruct': params['style']} if params.get('style') else {})}
    return {**kwargs, 'instruct': params['design']}


def generate(job):
    root = Path(job).resolve()
    from material_gate import check_job
    check_job(root)
    import numpy as np
    import soundfile as sf
    manifest = json.loads((root/'job.json').read_text(encoding='utf-8'))
    options = resolved_options(manifest.get('voxcpm', {}), root)
    backend = options.get('backend', 'pytorch' if os.name == 'nt' else 'mlx')
    if backend not in ('mlx', 'pytorch'):
        raise ValueError('voxcpm.backend must be mlx or pytorch')
    model_path = Path(options.get('model_path', '')).expanduser()
    if not options.get('model_path') or not (model_path/'config.json').is_file():
        raise ValueError('Set voxcpm.model_path to an already installed local VoxCPM2 model')
    if options.get('model_config_sha256') and hashlib.sha256((model_path/'config.json').read_bytes()).hexdigest() != options['model_config_sha256']:
        raise ValueError('Pinned voice model configuration changed; review before generating')
    reference, transcript = voice_reference(options, root)
    if backend == 'pytorch':
        from voxcpm import VoxCPM
        if options.get('enhancement_model_path'):
            raise ValueError('enhancement_model_path is only supported by the MLX backend')
        model = VoxCPM.from_pretrained(str(model_path.resolve()),
            device=options.get('device', 'cuda'), optimize=bool(options.get('optimize', False)),
            load_denoiser=False, local_files_only=True)
    else:
        import mlx.core as mx
        from mlx_audio.tts.utils import load
        model = load(str(model_path.resolve()))
    target, complete_text = generation_target(root, manifest)
    for beat in [{'id': 'narration-master', 'text': complete_text, 'audio': str(target)}]:
        target = (root/beat['audio']).resolve()
        if not target.is_relative_to(root):
            raise ValueError('Narration output must stay in the job')
        params = {'text':beat['text'],'backend':backend,'seed':int(options.get('seed',2026)),
                  'timesteps':int(options.get('timesteps',10)),'cfg_value':float(options.get('cfg_value',2.)),
                  'mode':options.get('mode','combined'),'max_tokens':int(options.get('max_tokens',6500))}
        if backend == 'pytorch':
            params['device'] = options.get('device', 'cuda')
            params['optimize'] = bool(options.get('optimize', False))
        params['enhancement'] = enhancement_fingerprint(options.get('enhancement_model_path'))
        if params['mode'] not in ('combined','reference'):
            raise ValueError('VoxCPM2 mode must be combined or reference')
        signature = hashlib.sha256(json.dumps(params,sort_keys=True).encode()+reference.read_bytes()+transcript.encode()+str(model_path.resolve()).encode()).hexdigest()
        record_path = target.with_suffix('.voice.json')
        if target.is_file() and record_path.is_file() and json.loads(record_path.read_text(encoding='utf-8')).get('signature') == signature:
            continue
        if target.exists() and not record_path.exists():
            raise ValueError('Existing untracked narration will not be overwritten: '+str(target))
        if backend == 'pytorch':
            import torch
            torch.manual_seed(params['seed'])
            conditioning = {'reference_wav_path':str(reference)}
            if params['mode'] == 'combined':
                conditioning.update(prompt_wav_path=str(reference), prompt_text=transcript)
            samples = np.asarray(model.generate(text=beat['text'], **conditioning,
                inference_timesteps=params['timesteps'], cfg_value=params['cfg_value'],
                max_len=params['max_tokens']), dtype=np.float32)
            sample_rate = model.tts_model.sample_rate
        else:
            mx.random.seed(params['seed'])
            conditioning = {'prompt_audio':str(reference),'prompt_text':transcript} if params['mode']=='combined' else {}
            result = list(model.generate(text=beat['text'], ref_audio=str(reference), **conditioning,
                          inference_timesteps=params['timesteps'], cfg_value=params['cfg_value'], max_tokens=params['max_tokens']))
            samples = np.concatenate([np.asarray(chunk.audio) for chunk in result])
            sample_rate = result[0].sample_rate
        if not len(samples) or not np.isfinite(samples).all():
            raise ValueError('Generated narration is empty or non-finite')
        if params['enhancement']:
            from mlx_audio.sts.models.deepfilternet import DeepFilterNetModel
            if sample_rate != 48000:
                raise ValueError('Configured speech cleanup requires a 48 kHz narration waveform')
            cleaner = DeepFilterNetModel.from_pretrained(params['enhancement']['model_path'], subfolder=None)
            enhanced = np.asarray(cleaner.enhance_array(samples), dtype=np.float32)
            if len(enhanced) != len(samples) or not np.isfinite(enhanced).all():
                raise ValueError('Speech cleanup changed narration duration or produced invalid samples')
            samples = enhanced
        target.parent.mkdir(parents=True,exist_ok=True)
        temporary = target.with_name(target.stem+'.generating.wav')
        sf.write(temporary,samples,sample_rate,subtype='PCM_24')
        temporary.replace(target)
        record_path.write_text(json.dumps({'signature':signature,'text':beat['text'],'model_path':str(model_path),
            'duration':len(samples)/sample_rate,'voice':options.get('voice'),'method':'single_call_complete_script','conditioning':params['mode'],
            'reference_audio':str(reference),'reference_sha256':hashlib.sha256(reference.read_bytes()).hexdigest(),
            'reference_text':transcript,'parameters':params,'subjective_listening':'not_performed'},ensure_ascii=False,indent=2),encoding='utf-8')
        print('READY',beat.get('id',target.stem),flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('job',type=Path)
    generate(parser.parse_args().job)
