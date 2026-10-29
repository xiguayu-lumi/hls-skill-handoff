"""Get timestamp evidence; output is a draft for script-aware proofreading, not final subtitles."""
import argparse, json
from pathlib import Path
from faster_whisper import WhisperModel

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('audio',type=Path);p.add_argument('output',type=Path)
 p.add_argument('--model',default='small');p.add_argument('--language',default='zh')
 a=p.parse_args()
 if a.output.exists(): p.error('Choose a new output file; refusing to overwrite')
 model=WhisperModel(a.model,device='cpu',compute_type='int8',cpu_threads=4,local_files_only=True)
 segments,info=model.transcribe(str(a.audio),language=a.language,beam_size=5,word_timestamps=True,vad_filter=False,condition_on_previous_text=False)
 rows=[]
 for s in segments:
  rows.append({'start':s.start,'end':s.end,'text':s.text,'words':[{'start':w.start,'end':w.end,'text':w.word} for w in s.words or []]})
 a.output.write_text(json.dumps({'audio_duration':info.duration,'segments':rows},ensure_ascii=False,indent=2),encoding='utf8')
 if not rows: raise RuntimeError('No speech recognized')
 print(f'{len(rows)} draft segments; first={rows[0]["start"]:.2f}, last={rows[-1]["end"]:.2f}, audio={info.duration:.2f}')
