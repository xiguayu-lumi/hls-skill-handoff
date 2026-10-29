"""Offline tests using simulated user records; no real approvals or video generation."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from PIL import Image, PngImagePlugin
from material_gate import snapshot, check_job, digest
from prepare_runtime import prepare

class MaterialGateTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name).resolve()
        (self.root/'inputs').mkdir();(self.root/'design').mkdir()
        im=Image.new('RGB',(16,8),'red');im.paste('blue',(8,0,16,8));im.save(self.root/'inputs/atlas.png')
        self.assets=[{'asset_id':'red','source':'inputs/atlas.png','crop':[0,0,8,8]},
                     {'asset_id':'blue','source':'inputs/atlas.png','crop':[8,0,16,8]}]
        self.write('design/materials.json',{'assets':self.assets})
        self.manifest={'version':1,'cover':{'source':'inputs/cover.png','material_asset_ids':[]},'pages':[
            {'beats':[{'actions':[{'type':'illustration',**a}]}]} for a in self.assets]}
        self.write('job.json',self.manifest)
        snapshot(self.root)
    def tearDown(self):self.temp.cleanup()
    def write(self,name,data):
        p=self.root/name;p.parent.mkdir(parents=True,exist_ok=True)
        p.write_text(json.dumps(data,ensure_ascii=False),encoding='utf8')
    def approve_fixture(self):
        self.write('design/materials-approval.json',{'status':'approved','paused':False,
            'materials_sha256':digest(self.root/'design/materials.json'),
            'user_quote':'TEST FIXTURE ONLY: all materials approved','evidence':'simulated test record; not a real user decision'})
    def test_pending_blocks(self):
        with self.assertRaisesRegex(ValueError,'explicit user review'):check_job(self.root)
    def test_unique_atlas_units_pass(self):
        self.approve_fixture();self.assertEqual(len(check_job(self.root)['used_materials']),2)
    def test_repeat_across_pages_blocks(self):
        self.approve_fixture();self.manifest['pages'].append(self.manifest['pages'][0]);self.write('job.json',self.manifest)
        with self.assertRaisesRegex(ValueError,'Repeated material'):check_job(self.root)
    def test_repeat_between_beat_and_visual_group_blocks(self):
        self.approve_fixture();self.manifest['pages'][0]['visual_groups']=[{'actions':[{'type':'illustration',**self.assets[0]}]}];self.write('job.json',self.manifest)
        with self.assertRaisesRegex(ValueError,'Repeated material'):check_job(self.root)
    def test_cover_and_body_repeat_blocks(self):
        self.approve_fixture();self.manifest['cover']['material_asset_ids']=['red'];self.write('job.json',self.manifest)
        with self.assertRaisesRegex(ValueError,'Repeated material'):check_job(self.root)
    def test_paused_or_fake_empty_quote_blocks(self):
        self.approve_fixture();p=self.root/'design/materials-approval.json';a=json.loads(p.read_text())
        for changes in ({'paused':True},{'user_quote':''},{'evidence':''}):
            self.write('design/materials-approval.json',{**a,**changes})
            with self.assertRaisesRegex(ValueError,'explicit user review'):check_job(self.root)
    def test_changed_file_blocks_and_snapshot_resets(self):
        self.approve_fixture();Image.new('RGB',(16,8),'green').save(self.root/'inputs/atlas.png')
        with self.assertRaisesRegex(ValueError,'Material changed'):check_job(self.root)
        # Keep this fixture's two regions distinct when refreshing.
        im=Image.new('RGB',(16,8),'green');im.paste('yellow',(8,0,16,8));im.save(self.root/'inputs/atlas.png')
        snapshot(self.root);a=json.loads((self.root/'design/materials-approval.json').read_text())
        self.assertEqual((a['status'],a['user_quote']),('pending',''))
        with self.assertRaisesRegex(ValueError,'explicit user review'):check_job(self.root)
    def test_renamed_reencoded_identical_pixels_blocks(self):
        with Image.open(self.root/'inputs/atlas.png') as im:tile=im.crop((0,0,8,8))
        meta=PngImagePlugin.PngInfo();meta.add_text('test','different encoding metadata')
        tile.save(self.root/'inputs/alias.png',pnginfo=meta)
        self.assets.append({'asset_id':'alias','source':'inputs/alias.png','crop':None});self.write('design/materials.json',{'assets':self.assets})
        with self.assertRaisesRegex(ValueError,'Duplicate material pixels'):snapshot(self.root)
    def test_overlapping_detail_crops_block(self):
        self.assets=[{'asset_id':'whole','source':'inputs/atlas.png','crop':None},self.assets[0]]
        self.write('design/materials.json',{'assets':self.assets});snapshot(self.root);self.approve_fixture()
        self.manifest['pages']=[{'beats':[{'actions':[{'type':'illustration',**a}]}]} for a in self.assets];self.write('job.json',self.manifest)
        with self.assertRaisesRegex(ValueError,'overlapping'):check_job(self.root)
    def test_usage_crop_change_blocks(self):
        self.approve_fixture();self.manifest['pages'][0]['beats'][0]['actions'][0]['crop']=[0,0,7,8];self.write('job.json',self.manifest)
        with self.assertRaisesRegex(ValueError,'differs'):check_job(self.root)
    def test_stale_approval_blocks(self):
        self.approve_fixture();p=self.root/'design/materials.json';a=json.loads(p.read_text());a['review_batch']='new';self.write('design/materials.json',a)
        with self.assertRaisesRegex(ValueError,'explicit user review'):check_job(self.root)
    def test_guarded_runtime_blocks_all_production_commands(self):
        self.write('confirmation.json',{'status':'confirmed','scope':'production','paused':False,
            'topic':'test fixture','style_id':'FA-012','user_quote':'TEST ONLY','evidence':'simulated fixture'})
        runtime=prepare(Path(__file__).resolve().parents[2]/'sweety-handdraw-video',self.root,self.root/'confirmation.json')
        for command in ('build','render','verify','finalize'):
            p=subprocess.run([sys.executable,'-X','utf8',str(runtime/'scripts/handdraw_video.py'),command,str(self.root)],capture_output=True,text=True)
            self.assertNotEqual(p.returncode,0);self.assertIn('explicit user review',p.stderr)

if __name__=='__main__':unittest.main()
