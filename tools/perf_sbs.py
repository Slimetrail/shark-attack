# Side-by-side frame rate of several builds, same script and settings (desktop-Chromium PROXY for a phone with CPU throttling, NOT a phone measurement).
# Each round plays every build once per scene, builds interleaved, so a load change on the box hits all builds alike. Check `uptime` first (quiet box).
# Scenes: size 1 and size 10 (internal level 0 / 9) at the surface, waterline on screen, tiger, god mode, game defaults for render scale and effects, adapt off.
# Usage: /workspace/.pwvenv/bin/python tools/perf_sbs.py ROUNDS CPU NAME=ROOT [NAME=ROOT ...]   e.g. 5 4 b52=/tmp/pb52 b53=/tmp/pb53 b54=.
#   SA_Q="&rs=1.5" adds URL settings (same for every build), e.g. to get under the 60 fps vsync ceiling.
import sys,json,subprocess,time,statistics as st
from playwright.sync_api import sync_playwright
R=int(sys.argv[1]);CPU=float(sys.argv[2]);B=[a.split('=',1) for a in sys.argv[3:]]
SCN={'size1-surface':(0,'__sa.SURF+innerHeight*.3'),'size10-surface':(9,'__sa.SURF+innerHeight*.3')}
MEAS='''()=>new Promise(res=>{const d=[];let last=performance.now();const t0=last;const f=n=>{d.push(n-last);last=n;if(n-t0<5000)requestAnimationFrame(f);else res(d)};requestAnimationFrame(f)})'''
srv=[subprocess.Popen([sys.executable,'-m','http.server',str(8981+i),'--bind','127.0.0.1'],cwd=r,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL) for i,(n,r) in enumerate(B)];time.sleep(1)
res={(n,s):[] for n,_ in B for s in SCN}
try:
 with sync_playwright() as p:
  b=p.chromium.launch()
  for rd in range(R):
   for scn,(lvl,yy) in SCN.items():
    for i,(n,_) in enumerate(B):
     cx=b.new_context(viewport={'width':915,'height':412},device_scale_factor=2.625,has_touch=True,is_mobile=True,bypass_csp=True,service_workers='block');pg=cx.new_page();ev=pg.evaluate;cdp=cx.new_cdp_session(pg)
     pg.goto(f'http://127.0.0.1:{8981+i}/?adapt=0'+__import__('os').environ.get('SA_Q',''));pg.wait_for_timeout(300);pg.click('#tap');pg.wait_for_timeout(700);pg.click('#start');pg.wait_for_timeout(150);pg.click('.pick[data-type=tiger]');pg.wait_for_timeout(250)
     ev('__sa.god=true;__sa.timeLeft=999')
     ev(f'()=>{{__sa.setLevel({lvl});const s=__sa.shark;s.y={yy};s.x=__sa.camX+innerWidth/2;__sa.camX=s.x-innerWidth/2;__sa.camY=s.y-innerHeight/2;__sa.respawnAll()}}')
     cdp.send('Emulation.setCPUThrottlingRate',{'rate':CPU});pg.wait_for_timeout(600)
     d=ev(MEAS)[1:];fps=round(len(d)/(sum(d)/1000),1);res[(n,scn)].append(fps);print(json.dumps(dict(round=rd+1,build=n,scene=scn,cpu=CPU,avg_fps=fps,state=ev('__sa.state'))),flush=True);cx.close()
  b.close()
finally:
  for s in srv: s.terminate()
for scn in SCN:
  print(scn+':  '+'   '.join(f"{n} median {st.median(res[(n,scn)]):.1f} fps (min {min(res[(n,scn)]):.1f}, max {max(res[(n,scn)]):.1f}, n={len(res[(n,scn)])})" for n,_ in B))
