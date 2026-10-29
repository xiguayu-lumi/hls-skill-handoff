"""Decode final video, check duration/dimensions and measure voice correlation lag."""
import argparse, json, subprocess
from pathlib import Path
import numpy as np
from scipy.signal import correlate, correlation_lags
from project import probe, media, save

def mono(path, start, seconds):
 raw=subprocess.check_output(['ffmpeg','-v','error','-ss',str(start),'-i',str(path),'-t',str(seconds),'-ar','8000','-ac','1','-f','f32le','-'])
 return np.frombuffer(raw,np.float32)

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('project',type=Path);p.add_argument('video',type=Path)
 a=p.parse_args();c=json.loads((a.project/'video.json').read_text('utf8'))
 info=probe(a.video);v=next(s for s in info['streams'] if s['codec_type']=='video')
 assert (v['width'],v['height'])==(1920,1080)
 assert v['avg_frame_rate']=='30/1'
 assert any(s['codec_type']=='audio' for s in info['streams'])
 expected=c['durationInFrames']/30
 assert abs(float(info['format']['duration'])-expected)<.08
 subprocess.run(['ffmpeg','-v','error','-xerror','-i',str(a.video),'-f','null','-'],check=True)
 alignment=[]
 for start in np.linspace(0,max(0,expected-4),min(7,max(1,int(expected/4)))):
  x=mono(media(a.project,c['voice']),float(start),4)
  y=mono(a.video,float(start),4)
  n=min(len(x),len(y));x=x[:n];y=y[:n]
  if n<100 or np.std(x)<.001: continue
  corr=correlate(y-y.mean(),x-x.mean(),mode='full',method='fft')
  lags=correlation_lags(n,n,mode='full');mask=np.abs(lags)<=400
  lag=int(lags[mask][np.argmax(corr[mask])])
  rho=float(np.corrcoef(x,y)[0,1])
  alignment.append({'start':round(float(start),3),'lag_ms':lag/8,'correlation':round(rho,4)})
  assert abs(lag)<=16, 'Voice offset exceeds 2 ms'
  assert rho>.95, 'Voice differs from source; inspect mix'
 assert alignment, 'No speech window for audio alignment'
 out={'decode':'pass','resolution':[1920,1080],'fps':30,'duration':expected,'alignment':alignment,'visual_review':'required separately'}
 save(a.project/'verification.json',out);print(json.dumps(out))
