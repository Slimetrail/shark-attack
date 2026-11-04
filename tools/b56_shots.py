# b56 screenshots (desktop Chromium touch emulation, not a real phone): 1 your shark bumping the top of a bigger shark's body (safe);
# 2 a bigger shark's mouth on you (Gulp). Usage: /workspace/.pwvenv/bin/python tools/b56_shots.py [OUT dir]
import os,sys,subprocess,time
from playwright.sync_api import sync_playwright
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)));OUT=sys.argv[1] if len(sys.argv)>1 else '/workspace/shark-b56-runs/shots';os.makedirs(OUT,exist_ok=True)
PORT=8964;U=f'http://127.0.0.1:{PORT}/'
srv=subprocess.Popen([sys.executable,'-m','http.server',str(PORT),'--bind','127.0.0.1'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(.8)
SET='''([pos])=>{const S=__sa;S.startAs("white","endless");S.god=false;S.setLevel(2);S.sim(2.2);S.clearFood();const s=S.shark,D=S.BED-S.SURF;s.y=S.SURF+D*1.0;s.x=S.camX+innerWidth/2;s.ang=0;s.spd=0;S.touch.on=false;
 for(let k=0;k<90;k++){s.spd=0;S.sim(1/60)}S.clearFood();s.x=S.camX+innerWidth/2;const f=S.fish[0];S.setCreature(f,S.bite()*2,"shark");f.off=false;f.tiny=false;f.fade=0;
 const L=s.L,fs=f.s,_m=(f.x=0,f.y=0,f.vx=-60,S.mouthPt(f)),X=pos==="mouth"?s.x-_m[0]:s.x+L*.1,Y=pos==="mouth"?s.y-_m[1]:s.y+(L*.32+fs*.9)*.8,VX=pos==="mouth"?-60:-60,x0=s.x,y0=s.y;
 window.__hold=setInterval(()=>{if(S.state!=="play")return;f.x=X;f.y=Y;f.vx=VX;f.vy=0;f.rest=0;if(pos!=="mouth"){s.x=x0;s.y=y0;s.spd=0;s.ang=0}},4);return {fs,L}}'''
try:
 with sync_playwright() as p:
  b=p.chromium.launch()
  for w,h in [(844,390),(915,412)]:
   for name,wait in [('bump-safe',900),('mouth-hit',250)]:
    cx=b.new_context(viewport={'width':w,'height':h},device_scale_factor=2,has_touch=True,is_mobile=True,bypass_csp=True,service_workers='block');pg=cx.new_page()
    pg.goto(U);pg.wait_for_function('!!window.__sa',timeout=30000);pg.wait_for_timeout(300);pg.touchscreen.tap(w//2,h//2);pg.wait_for_timeout(300)
    pg.evaluate(SET,['mouth' if name=='mouth-hit' else 'top']);pg.wait_for_timeout(wait)
    info=pg.evaluate('({state:__sa.state,end:__sa.endReason})');fn=f'{OUT}/b56-{name}-{w}x{h}.png';pg.screenshot(path=fn);print(fn,info);cx.close()
  b.close()
finally: srv.terminate()
