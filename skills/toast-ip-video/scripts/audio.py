"""Original 108 BPM music and voice-anchored mix. Requires numpy/scipy + ffmpeg."""
from pathlib import Path
import argparse, json, math, subprocess, wave
import numpy as np
from scipy.ndimage import uniform_filter1d
SR=48000

def compose(duration):
 sr=SR;n=round(sr*duration)
 rng=np.random.default_rng(2902);music=np.zeros((n,2),np.float32);beat=60/108
 def add(sound,start,gain=1,pan=0):
  a=round(start*sr)
  if a<0 or a>=n:return
  sound=sound[:n-a]*gain
  music[a:a+len(sound),0]+=sound*np.sqrt((1-pan)/2)
  music[a:a+len(sound),1]+=sound*np.sqrt((1+pan)/2)
 def note(midi,dur,timbre):
  t=np.arange(round(dur*sr))/sr;f=440*2**((midi-69)/12)
  if timbre=='keys':
   y=(np.sin(2*np.pi*f*t+.5*np.sin(2*np.pi*f*2*t)*np.exp(-7*t))+.16*np.sin(2*np.pi*f*2.002*t))*np.exp(-3.1*t)
  elif timbre=='pluck':
   y=(np.sin(2*np.pi*f*t)*np.exp(-4*t)+.21*np.sin(2*np.pi*f*2.01*t)*np.exp(-13*t)+.05*np.sin(2*np.pi*f*3.99*t)*np.exp(-21*t))
  else:y=(np.sin(2*np.pi*f*t)+.15*np.sin(2*np.pi*f*2*t))*np.exp(-5*t)
  y*=np.minimum(t/.008,1)*np.minimum((dur-t)/.05,1)
  return y.astype(np.float32)
 chords=[([60,64,67,71],36),([57,60,64,67],33),([62,65,69,72],38),([59,62,65,69],31)]
 motifs=[[76,79,81,79],[76,72,74,76],[77,81,79,77],[74,71,72,74]]
 for bar in range(math.ceil(duration/(4*beat))):
  base=bar*4*beat;chord,root=chords[bar%4]
  for off,g in [(0,.105),(1.5,.075),(2.75,.075)]:
   for j,m in enumerate(chord):add(note(m,1.1,'keys'),base+off*beat+j*.009,g,(-.35+j*.2))
  for off,m in [(0,root),(1.75,root+7),(2.5,root+12)]:add(note(m,.65,'bass'),base+off*beat,.2,0)
  if bar%4!=3:
   for k,off in enumerate([.5,1.25,2.5,3.25]):
    if bar%8>=4 and k in [1,3]:continue
    add(note(motifs[bar%4][k],.66,'pluck'),base+off*beat,.09,-.3 if k%2 else .3)
  for j in range(8):
   t=np.arange(int(sr*.1))/sr;noise=rng.standard_normal(len(t));noise=np.concatenate([[0],np.diff(noise)])
   add((noise*np.exp(-65*t)).astype(np.float32),base+(j*.5+(.035 if j%2 else 0))*beat,.012 if j%2 else .018,.55)
  for off in [0,2]:
   t=np.arange(int(sr*.22))/sr;freq=48*t+25*(1-np.exp(-35*t))/35
   add((np.sin(2*np.pi*freq)*np.exp(-24*t)).astype(np.float32),base+off*beat,.12,0)
  for off in [1,3]:
   t=np.arange(int(sr*.13))/sr;noise=rng.standard_normal(len(t));noise=uniform_filter1d(noise,8)
   add((noise*np.exp(-35*t)).astype(np.float32),base+off*beat,.06,-.3)
 # Light room reflections, no long tails in the speech band.
 dry=music.copy()
 for sec,g in [(.115,.12),(.227,.07)]:
  d=round(sec*sr);
  if d<n: music[d:]+=dry[:-d,::-1]*g
 return music

def wav(path, arr):
 with wave.open(str(path),'wb') as w:
  w.setparams((2,2,SR,0,'NONE','not compressed'))
  w.writeframes((np.clip(arr,-1,1)*32767).astype('<i2').tobytes())

def decode(path, duration, loop=False):
 args=['ffmpeg','-v','error']+(['-stream_loop','-1'] if loop else [])
 raw=subprocess.check_output(args+['-i',str(path),'-t',str(duration),'-ar',str(SR),'-ac','2','-f','f32le','-'])
 samples=np.frombuffer(raw,np.float32).reshape(-1,2)
 out=np.zeros((round(duration*SR),2),np.float32)
 count=min(len(samples),len(out));out[:count]=samples[:count]
 return out

def mix(project):
 from project import validate, media, save
 c=validate(project,json.loads((project/'video.json').read_text('utf8')))
 duration=c['durationInFrames']/30
 voice=decode(media(project,c['voice']),duration)
 env=np.sqrt(np.maximum(0,uniform_filter1d(np.mean(voice**2,axis=1),size=round(SR*.12))))
 active=env>max(.003,float(env.max())*.08)
 if not active.any(): raise ValueError('Voice is silent; provide the actual narration')
 voice_rms=float(np.sqrt(np.mean(voice[active]**2)))
 music=np.zeros_like(voice)
 if c.get('music'):
  music=compose(duration) if c['music']=='generated' else decode(media(project,c['music']),duration,loop=True)
  duck=uniform_filter1d(np.clip(1-env/max(float(env.max()),1e-8)*.5,.55,1),size=round(SR*.1))
  music*=duck[:,None]
  target=voice_rms*10**(-c.get('musicBelowVoiceDb',20)/20)
  music*=target/(float(np.sqrt(np.mean(music[active]**2)))+1e-9)
  t=np.arange(len(music))/SR
  fade=np.clip(t/min(1.1,duration/4),0,1)*np.clip((duration-t)/min(1.5,duration/4),0,1)
  music*=fade[:,None]
 mixed=voice+music
 for event in c.get('effects',[]):
  effect=decode(media(project,event['file']),1)
  start=round(event['at']*SR);count=min(len(effect),len(mixed)-start)
  mixed[start:start+count]+=effect[:count]*event.get('gain',.2)
 peak=float(np.max(np.abs(mixed)))
 gain=min(1,.89/max(peak,1e-9))
 mixed*=gain
 wav(project/'mix.wav',mixed)
 music_rms=float(np.sqrt(np.mean(music[active]**2)))
 report={'duration':duration,'voice_start_shift_ms':0,'music_below_voice_db':round(float(20*np.log10(voice_rms/music_rms)),2) if music_rms else None,'peak_dbfs':round(float(20*np.log10(np.max(np.abs(mixed)))),2),'master_gain':gain}
 save(project/'mix-report.json',report)
 print(json.dumps(report))

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('project',type=Path,nargs='?')
 p.add_argument('--music-only',type=Path);p.add_argument('--seconds',type=float,default=72)
 a=p.parse_args()
 if a.music_only:
  if a.seconds<=0: p.error('seconds must be positive')
  music=compose(a.seconds);music*=.5/max(float(np.max(np.abs(music))),1e-9)
  t=np.arange(len(music))/SR
  music*=np.minimum(t/.1,1)[:,None]*np.minimum((a.seconds-t)/.4,1)[:,None]
  wav(a.music_only,music)
 elif a.project: mix(a.project)
 else: p.error('project or --music-only required')
