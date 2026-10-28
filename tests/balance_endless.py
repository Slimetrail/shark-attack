# Endless-mode balance: the same bot plays N endless games per shark type (up to 15 min each) using the real game update (fixed 1/60 s steps, no rendering).
# Run: python3 tests/balance_endless.py [games]   -> prints a table; exits 1 if a fairness rule is broken.
import subprocess,sys,os,time,json
from playwright.sync_api import sync_playwright
# N=30 games per type: survival is bimodal (games end early or run to the cap), so a median of 10 games was a coin-flip.
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)));PORT=int(os.environ.get('SA_PORT5','8879'));N=int(sys.argv[1]) if len(sys.argv)>1 else 30;CAP=900
srv=subprocess.Popen([sys.executable,'-m','http.server',str(PORT),'--bind','127.0.0.1'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(1)
BOT=r'''(wig)=>{const S=__sa,s=S.shark,W=innerWidth,H=innerHeight;let mode="hunt",wt=0,t=0;const st={py:-1e9,pt:0,get mode(){return mode},amb:0,ambEaten:0,ambWarn:[],netT:[]};let ambSeen=false,ambT0=0;
 return {st,fn(dt){t+=dt;const T=S.touch;T.on=true;T.lastMove=performance.now()+9e9;
  if(S.amb.on&&S.amb.phase==="come"&&!ambSeen){ambSeen=true;st.amb++;ambT0=t}if(!S.amb.on)ambSeen=false;
  if(s.stun>0){wt+=dt;if(wig&&wt>1/wig){wt=0;S.struggle(W*S.DIV.STRUGGLE_PX)}return}
  let ax=0,ay=0;const L=s.L;
  for(const f of S.fish)if(S.rel(f)>0){const dx=s.x-f.x,dy=s.y-f.y,d=Math.hypot(dx,dy);if(d<L*2.2+f.s){ax+=dx/d*(1/Math.max(.3,d/L));ay+=dy/d*(1/Math.max(.3,d/L))}}
  for(const d of S.divers)if(d.grace<=0){const dx=s.x-d.x,dy=s.y-d.y,q=Math.hypot(dx,dy);if(q<H*.3){ax+=dx/q*1.5;ay+=dy/q*1.5}}
  if(Math.hypot(ax,ay)>.4){T.dir=Math.atan2(ay,ax);T.drive=1;return}
  const cx=S.camX,cy=S.camY,sf=S.surf.filter(q=>q.zip<=0&&q.x>cx+40&&q.x<cx+W-40);/* v8 endless world: everything is camera-relative */
  if(sf.length&&!s.air&&s.lvl>=S.GROW.SURF_LVL){/* v8: only a shark big enough for surfers goes for them */
if(mode==="hunt"&&s.y<S.SURF+H*.8&&Math.random()<dt*.6)mode="dive";
   if(mode==="dive"){T.dir=Math.PI/2+(s.x<cx+W/2?-.6:.6);T.drive=1;if(s.y>S.SURF+H*1.05||(s.y<=st.py+.2&&t-st.pt>.6))mode="rise";if(s.y>st.py+.2){st.py=s.y;st.pt=t}}else{st.py=-1e9;st.pt=t}/* stalled at a depth limit -> rise */
   if(mode==="rise"){const q=sf.reduce((a,b)=>Math.abs(b.x-s.x)<Math.abs(a.x-s.x)?b:a);T.dir=Math.atan2(S.SURF-40-s.y,(q.x+q.vx*.5-s.x)*.35);T.drive=1;if(s.y<S.SURF+L)mode="hunt";return}
   if(mode==="dive")return}
  let best=null,bd=1e9;for(const f of S.fish)if(!f.off&&S.rel(f)<0&&(s.lvl>0||f.kind==="plankton")&&f.x>cx-W*.2&&f.x<cx+W*1.2&&f.y>cy-H*.2&&f.y<cy+H*1.2){const d=Math.hypot(f.x-s.x,f.y-s.y);if(d<bd){bd=d;best=f}}
  if(best){const mx=s.x+Math.cos(s.ang)*L*.48,my=s.y+Math.sin(s.ang)*L*.48,da=Math.atan2(best.y-my,best.x-mx),df=Math.abs(Math.atan2(Math.sin(da-s.ang),Math.cos(da-s.ang)));T.dir=(Math.hypot(best.x-s.x,best.y-s.y)<L*.6&&df>1.2)?s.ang:da;T.drive=.8}/* aim with the mouth; too close & behind -> swim on and loop back (no orbiting) */else{T.dir=Math.atan2(S.SURF+H*.45-s.y,(s.x+W*.3)-s.x);T.drive=.5}}}}'''
res={}
try:
 with sync_playwright() as p:
  b=p.chromium.launch();cx=b.new_context(viewport={'width':915,'height':412},bypass_csp=True,service_workers='block');pg=cx.new_page()
  pg.goto(f'http://127.0.0.1:{PORT}/');pg.wait_for_timeout(300)
  for wig,label in [(4,'good(wig4)'),(1.5,'weak(wig1.5)')]:
   for t in ['white','hammer','tiger']:
    res[(label,t)]=pg.evaluate("""([N,t,wig,BOT,CAP])=>{const mk=eval(BOT),out=[];for(let i=0;i<N;i++){__sa.startAs(t,"endless");localStorage.setItem("sharkAttack_diverTip","1");const B=mk(wig);let _ft=-1,_lt=-1,_tt=0;const _fn=dt=>{_tt+=dt;if(_ft<0&&__sa.surfersCaught>0)_ft=_tt;if(_lt<0&&__sa.shark.lvl>=6)_lt=_tt;B.fn(dt)};const el=__sa.sim(CAP,_fn,1/30);
      out.push({ft:_ft,lt:_lt,score:__sa.score,end:__sa.endReason||"alive",surf:__sa.surfersCaught,hits:__sa.netHits,t:el,dv:__sa.diverSpeed()/__sa.maxSpeed()})}__sa.setMode("timed");return out}""",[N,t,wig,BOT,CAP])
  b.close()
finally: srv.terminate()
def med(a): a=sorted(a);return a[len(a)//2]
bad=[]
print(f"{'bot':13}{'type':8}{'median s':>9}{'min s':>7}{'score':>7}{'surf':>6}{'hits':>6}{'diver/shark':>12}  ends")
for (label,t),r in res.items():
  ends={}
  for x in r: ends[x['end']]=ends.get(x['end'],0)+1
  print(f"{label:13}{t:8}{med([x['t'] for x in r]):9.0f}{min(x['t'] for x in r):7.0f}{med([x['score'] for x in r]):7}{med([x['surf'] for x in r]):6}{med([x['hits'] for x in r]):6}{med([x['dv'] for x in r]):12.2f}  {ends}")
  if label.startswith('good'):
    if med([x['t'] for x in r])<180: bad.append(f'{t}: good bot lasts under 3 min')
    if any(x['end']=='caught' for x in r): bad.append(f'{t}: Caught! ended an endless game')
  if any(x['dv']>1.05+1e-6 for x in r): bad.append('diver speed above cap')
import statistics as _st
for (label,t),r in res.items():
  ft=[x['ft'] for x in r if x['ft']>=0];lt=[x['lt'] for x in r if x['lt']>=0]
  print(f"first surfer {label:10}{t:8} caught in {len(ft)}/{len(r)} games, median {(_st.median(ft) if ft else -1):.1f} s; reached surfer size in {len(lt)}/{len(r)}, median {(_st.median(lt) if lt else -1):.1f} s")
print('ISSUES' if bad else 'ENDLESS BALANCE OK',bad);sys.exit(1 if bad else 0)
