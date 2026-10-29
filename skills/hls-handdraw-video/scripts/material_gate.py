"""Bind user material review to images and reject reuse inside a video."""
import argparse
import hashlib
import json
from pathlib import Path
from PIL import Image

def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))

def region(root, item):
    path=(root/item['source']).resolve()
    if not path.is_relative_to(root):
        raise ValueError('Material source must stay inside the job')
    with Image.open(path) as source:
        image=source.convert('RGBA')
        crop=item.get('crop')
        if crop is not None:
            if (not isinstance(crop,list) or len(crop)!=4 or
                any(type(n) is not int for n in crop) or
                not 0<=crop[0]<crop[2]<=image.width or
                not 0<=crop[1]<crop[3]<=image.height):
                raise ValueError('Invalid material crop')
            image=image.crop(tuple(crop))
        pixel=hashlib.sha256(str(image.size).encode()+image.tobytes()).hexdigest()
    return {'source_sha256':digest(path),'pixel_sha256':pixel}

def inventory(root):
    path=root/'design/materials.json'
    data=read(path)
    assets=data.get('assets')
    if not isinstance(assets,list) or not assets:
        raise ValueError('A full material inventory is required')
    ids=[a.get('asset_id') for a in assets]
    if any(not isinstance(i,str) or not i.strip() for i in ids) or len(set(ids))!=len(ids):
        raise ValueError('Each material needs a unique stable asset_id')
    pixels={}
    for a in assets:
        actual=region(root,a)
        if any(a.get(k)!=v for k,v in actual.items()):
            raise ValueError('Material changed; snapshot and obtain user review again: '+a['asset_id'])
        if actual['pixel_sha256'] in pixels:
            raise ValueError('Duplicate material pixels: '+pixels[actual['pixel_sha256']]+' / '+a['asset_id'])
        pixels[actual['pixel_sha256']]=a['asset_id']
    return path,{a['asset_id']:a for a in assets}

def snapshot(job):
    root=Path(job).resolve();path=root/'design/materials.json';data=read(path)
    if not isinstance(data.get('assets'),list) or not data['assets']:
        raise ValueError('Populate materials.json before snapshot')
    for a in data['assets']:
        a.update(region(root,a))
    path.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
    inventory(root)
    approval={'status':'pending','materials_sha256':digest(path),'user_quote':'','evidence':'','paused':False}
    (root/'design/materials-approval.json').write_text(json.dumps(approval,ensure_ascii=False,indent=2),encoding='utf-8')
    return {'status':'awaiting_user_material_review','materials_sha256':digest(path)}

def illustration_actions(manifest):
    for p,page in enumerate(manifest['pages']):
        for group in [*page['beats'],*page.get('visual_groups',[])]:
            for action in group.get('actions',[]):
                if action.get('type')=='illustration':
                    yield f'page-{p+1}',action

def overlapping(a,b):
    if a['source_sha256']!=b['source_sha256']:
        return False
    x,y=a.get('crop'),b.get('crop')
    if x is None or y is None:
        return True
    intersection=max(0,min(x[2],y[2])-max(x[0],y[0]))*max(0,min(x[3],y[3])-max(x[1],y[1]))
    smaller=min((x[2]-x[0])*(x[3]-x[1]),(y[2]-y[0])*(y[3]-y[1]))
    return intersection/smaller>=.5

def check_job(job):
    root=Path(job).resolve();path,assets=inventory(root)
    approval=read(root/'design/materials-approval.json')
    if (approval.get('status')!='approved' or approval.get('paused') is not False or
        approval.get('materials_sha256')!=digest(path) or
        any(not isinstance(approval.get(k),str) or not approval[k].strip() for k in ('user_quote','evidence'))):
        raise ValueError('Stop: all current materials need explicit user review before production')
    manifest=read(root/'job.json');cover=manifest.get('cover',{})
    if not isinstance(cover.get('material_asset_ids'),list):
        raise ValueError('Declare material_asset_ids for the video cover; [] only for a text-only cover')
    uses=[('video-cover',i,None) for i in cover['material_asset_ids']]
    uses.extend((where,a.get('asset_id'),a) for where,a in illustration_actions(manifest))
    used={};pixel_uses={};seen=[]
    for where,identity,action in uses:
        if identity not in assets:
            raise ValueError('Usage needs an approved asset_id: '+where)
        asset=assets[identity]
        if action is not None:
            actual=region(root,action)
            if action.get('crop')!=asset.get('crop') or any(actual[k]!=asset[k] for k in actual):
                raise ValueError('Usage differs from the approved material: '+identity)
        if identity in used:
            raise ValueError('Repeated material '+identity+': '+used[identity]+' / '+where)
        if asset['pixel_sha256'] in pixel_uses:
            raise ValueError('Repeated material pixels at '+where)
        for old_id,old_asset in seen:
            if overlapping(old_asset,asset):
                raise ValueError('Repeated overlapping material crops: '+old_id+' / '+identity)
        used[identity]=where;pixel_uses[asset['pixel_sha256']]=where;seen.append((identity,asset))
    return {'status':'user_material_review_and_unique_usage_passed','materials_sha256':digest(path),'used_materials':used}

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command',choices=['snapshot','check']);parser.add_argument('job',type=Path)
    args=parser.parse_args()
    try:
        result=snapshot(args.job) if args.command=='snapshot' else check_job(args.job)
        print(json.dumps(result,ensure_ascii=False,indent=2))
    except (ValueError,FileNotFoundError,KeyError) as error:
        parser.exit(1,f'ERROR: {error}\n')
