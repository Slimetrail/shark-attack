# v10: measure fish catchability with a sim chase bot (sizes 1/3/6, shallow/deep). Run: python3 tests/measure_flee.py
import os,sys,subprocess,time,json
from playwright.sync_api import sync_playwright
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)));PORT=int(os.environ.get('SA_PORTM','8894'))
JS='''(a)=>{const [lvl,frac,mode,LAG,DRV,DG]=a;__sa.startAs("tiger","endless");Object.assign(__sa.DODGE,{ON:true},DG||{});__sa.god=true;__sa.setLevel(lvl);const s=__sa.shark,W=innerWidth,H=innerHeight;
 const put=()=>{s.x=__sa.camX+W/2;s.y=__sa.SURF+(__sa.BED-__sa.SURF)*frac;s.air=false;__sa.camY=s.y-H/2};
 let rt2=0,d2=0;const bot=dt=>{rt2+=dt;if(s.y<__sa.SURF+(__sa.BED-__sa.SURF)*Math.max(.05,frac-.15)||s.y>__sa.SURF+(__sa.BED-__sa.SURF)*Math.min(.98,frac+.15)){Object.assign(__sa.touch,{on:true,dir:Math.atan2(__sa.SURF+(__sa.BED-__sa.SURF)*frac-s.y,0.001),drive:1,lastMove:performance.now()+9e9});return}
   let best=null,bd=1e9;for(const f of __sa.fish){if(f.off||__sa.rel(f)>=0||f.kind==="star")continue;const d=Math.hypot(f.x-s.x,f.y-s.y);if(d<bd){bd=d;best=f}}
   if(rt2>=LAG){rt2=0;d2=best?Math.atan2(best.y-s.y,best.x-s.x):s.ang}Object.assign(__sa.touch,{on:true,dir:d2,drive:DRV,lastMove:performance.now()+9e9})};
 if(mode==="free"){put();__sa.respawnAll();const lv=s.lvl;let n=0,sc=__sa.score,t=0;__sa.sim(60,dt=>{t+=dt;__sa.timeLeft=999;if(s.lvl!==lv)__sa.setLevel(lv);s.meter=0;if(__sa.score>sc){n++;sc=__sa.score}bot(dt)});__sa.touch.on=false;__sa.DODGE.ON=true;return {per:n?60/n:99,n}}
 let c=0,N=40,mx=0,top=__sa.sharkMax(lvl),gap=Math.max(H*__sa.CREATURES.SENSE,s.L*__sa.CREATURES.SENSE_L)*.8;for(let k=0;k<N;k++){put();s.spd=top*.5;__sa.clearFood();const i=__sa.placeFishAt(0,s.x+gap*(k%2?1:-1)*Math.cos((k%5-2)*.3),s.y+gap*Math.sin((k%5-2)*.3),0),f=__sa.fish[i];__sa.setCreature(f,__sa.bite()*.5,"fish");f.tile=null;f.band=[__sa.SURF+20,Infinity];f.vx=0;f.vy=0;
   const sc=__sa.score;let got=false,rt=0,dir=Math.atan2(f.y-s.y,f.x-s.x);__sa.sim(3,dt=>{__sa.timeLeft=999;s.meter=0;if(s.lvl!==lvl)__sa.setLevel(lvl);if(got)return;if(__sa.score>sc){got=true;return}if(f.st==="flee"&&Math.hypot(f.vx,f.vy)/top>mx){mx=Math.hypot(f.vx,f.vy)/top;window.__mxi=[f.vx/top,f.vy/top,f.y-__sa.SURF,f.s,__sa.fleeK(f),f.chase]}rt+=dt;if(rt>=LAG){rt=0;dir=Math.atan2(f.y-s.y,f.x-s.x)}Object.assign(__sa.touch,{on:true,dir,drive:DRV,lastMove:performance.now()+9e9})});if(got||__sa.score>sc)c++}
 __sa.touch.on=false;__sa.DODGE.ON=true;return {rate:c/N,maxFlee:mx,i:window.__mxi}}'''
def run(dg=None,bots=None,sizes=(1,3,6)):
  srv=subprocess.Popen([sys.executable,'-m','http.server',str(PORT),'--bind','127.0.0.1'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(.8);out={}
  try:
   with sync_playwright() as p:
    b=p.chromium.launch();cx=b.new_context(viewport={'width':915,'height':412},device_scale_factor=1,bypass_csp=True,service_workers='block');pg=cx.new_page();pg.goto(f'http://127.0.0.1:{PORT}/');pg.wait_for_timeout(400)
    for size in sizes:
      for name,frac in (('shallow',.15),('deep',.8)):
        for bn,lag,drv in (bots or (('perfect',.15,1),('human',.3,.8))):
          out[f'size{size}-{name}-{bn}']={**pg.evaluate(JS,[size-1,frac,'free',lag,drv,dg]),**pg.evaluate(JS,[size-1,frac,'chase',lag,drv,dg])}
  finally: srv.kill()
  return out
if __name__=='__main__':
  # usage: measure_flee.py [JSON DODGE overrides, e.g. '{"ON":false}' or '{"CD_SHALLOW":1.0}']
  r=run(json.loads(sys.argv[1]) if len(sys.argv)>1 else None)
  for k,v in r.items(): print(k,json.dumps({a:round(b,2) for a,b in v.items() if a!='i'}))
