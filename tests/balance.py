# Headless balance check: scripted bot plays N full rounds per shark type using the real game update (fixed 1/60 s steps, no rendering).
# Run: python3 tests/balance.py [rounds]   -> prints a table; exits 1 if a fairness rule is broken.
import subprocess,sys,os,time,json
from playwright.sync_api import sync_playwright
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)));PORT=int(os.environ.get('SA_PORT3','8875'));N=int(sys.argv[1]) if len(sys.argv)>1 else 25
srv=subprocess.Popen([sys.executable,'-m','http.server',str(PORT),'--bind','127.0.0.1'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(1)
BOT=r'''(wig)=>{const S=__sa,s=S.shark,W=innerWidth,H=innerHeight;let mode="hunt",wt=0,t=0;const st={get mode(){return mode},amb:0,ambEaten:0,ambWarn:[],netT:[]};let ambSeen=false,ambT0=0;
 return {st,fn(dt){t+=dt;const T=S.touch;T.on=true;T.lastMove=performance.now()+9e9;
  if(S.amb.on&&S.amb.phase==="come"&&!ambSeen){ambSeen=true;st.amb++;ambT0=t}if(!S.amb.on)ambSeen=false;
  if(s.stun>0){wt+=dt;if(wig&&wt>1/wig){wt=0;S.struggle(W*S.DIV.STRUGGLE_PX)}return}
  let ax=0,ay=0;const L=s.L;
  for(const f of S.fish)if(S.rel(f)>0){const dx=s.x-f.x,dy=s.y-f.y,d=Math.hypot(dx,dy);if(d<L*2.2+f.s){ax+=dx/d*(1/Math.max(.3,d/L));ay+=dy/d*(1/Math.max(.3,d/L))}}
  for(const d of S.divers)if(d.grace<=0){const dx=s.x-d.x,dy=s.y-d.y,q=Math.hypot(dx,dy);if(q<H*.3){ax+=dx/q*1.5;ay+=dy/q*1.5}}
  if(Math.hypot(ax,ay)>.4){T.dir=Math.atan2(ay,ax);T.drive=1;return}
  const sf=S.surf.filter(q=>q.zip<=0&&q.x>40&&q.x<W-40);
  if(sf.length&&!s.air){if(mode==="hunt"&&s.y<S.SURF+H*.8&&Math.random()<dt*.6)mode="dive";
   if(mode==="dive"){T.dir=Math.PI/2+(s.x<W/2?-.6:.6);T.drive=1;if(s.y>S.SURF+H*1.05)mode="rise"}
   if(mode==="rise"){const q=sf.reduce((a,b)=>Math.abs(b.x-s.x)<Math.abs(a.x-s.x)?b:a);T.dir=Math.atan2(S.SURF-40-s.y,(q.x+q.vx*.5-s.x)*.35);T.drive=1;if(s.y<S.SURF+L)mode="hunt";return}
   if(mode==="dive")return}
  let best=null,bd=1e9;for(const f of S.fish)if(S.rel(f)<0&&f.x>0&&f.x<W){const d=Math.hypot(f.x-s.x,f.y-s.y);if(d<bd){bd=d;best=f}}
  if(best){T.dir=Math.atan2(best.y-s.y,best.x-s.x);T.drive=.8}else{T.dir=Math.atan2(S.SURF+H*.45-s.y,W/2-s.x);T.drive=.5}}}}'''
res={}
try:
 with sync_playwright() as p:
  b=p.chromium.launch();cx=b.new_context(viewport={'width':915,'height':412},bypass_csp=True,service_workers='block');pg=cx.new_page()
  pg.goto(f'http://127.0.0.1:{PORT}/');pg.wait_for_timeout(300)
  for wig,label,pre in [(4,'wiggles',0),(0,'no-wiggle',0),(4,'1diver',3),(4,'3divers',9)]:
   for t in ['white','hammer','tiger']:
    rows=pg.evaluate('''([N,t,wig,BOT,pre])=>{const mk=eval(BOT),out=[];for(let i=0;i<N;i++){__sa.startAs(t);localStorage.setItem("sharkAttack_diverTip","1");const B=mk(wig);for(let k=0;k<pre;k++)__sa.surferCaught();const el=__sa.sim(80,B.fn);
      out.push({score:__sa.score,lvl:__sa.shark.lvl,end:__sa.endReason,surf:__sa.surfersCaught,div:__sa.divers.length,hits:__sa.netHits,amb:B.st.amb,t:el,eatenByAmb:!!(__sa.amb&&__sa.amb.ate)})}return out}''',[N,t,wig,BOT,pre])
    res[(label,t)]=rows
  b.close()
finally: srv.terminate()
def avg(a): return sum(a)/len(a) if a else 0
bad=[]
print(f"{'bot':10}{'type':8}{'score':>7}{'max':>5}{'lvl':>5}{'surf':>6}{'divers':>7}{'hits':>6}{'amb':>5}  ends(time/eaten/caught)  ambush-eaten  early(<15s)")
for (label,t),r in res.items():
  ends={k:sum(1 for x in r if x['end']==k) for k in ['time','eaten','caught']};early=sum(1 for x in r if x['end']!='time' and x['t']<15)
  print(f"{label:10}{t:8}{avg([x['score'] for x in r]):7.1f}{max(x['score'] for x in r):5}{avg([x['lvl'] for x in r]):5.1f}{avg([x['surf'] for x in r]):6.1f}{avg([x['div'] for x in r]):7.1f}{avg([x['hits'] for x in r]):6.2f}{avg([x['amb'] for x in r]):5.2f}  {ends['time']:>3}/{ends['eaten']:>2}/{ends['caught']:>2}               {sum(x['eatenByAmb'] for x in r):>3}        {early}")
  if label=='wiggles':
    if ends['time']<len(r)*.4: bad.append(f'{t}: fewer than 40% of rounds survive to time-up')
    if early>len(r)*.15: bad.append(f'{t}: too many early losses')
    if sum(x['eatenByAmb'] for x in r)>0: bad.append(f'{t}: a wiggling player was eaten by an ambush')
sc={t:avg([x['score'] for x in res[('wiggles',t)]]) for t in ['white','hammer','tiger']}
if max(sc.values())>1.6*min(sc.values()): bad.append(f'shark types unbalanced {sc}')
print('ISSUES' if bad else 'BALANCE OK',bad);json.dump({f'{k[0]}/{k[1]}':v for k,v in res.items()},open('/tmp/balance.json','w'))
sys.exit(1 if bad else 0)
