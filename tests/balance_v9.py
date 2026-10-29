# v9 balance: an early-diving bot vs a shallow bot (both judge size from data: f.s / bite(), no indicator exists).
# Timed rounds (80 s cap) and endless games (CAP s): first-surfer time, Timed winnability, deaths by depth.
# Run: python3 tests/balance_v9.py [rounds] [endless_cap_s]
import subprocess,sys,os,time,re,statistics as st
from playwright.sync_api import sync_playwright
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)));PORT=int(os.environ.get('SA_PORT9','8879'))
N=int(sys.argv[1]) if len(sys.argv)>1 else 12;CAP=int(sys.argv[2]) if len(sys.argv)>2 else 240
BOT=re.search(r"BOT=r'''(.*?)'''",open(os.path.join(ROOT,'tests','balance.py')).read(),re.S).group(1)
WRAP=r'''(BOT,band)=>{const mk=eval(BOT);return wig=>{const B=mk(wig),S=__sa,s=S.shark,H=innerHeight;let dmin=1,dmax=0;
 return {st:B.st,get dmax(){return dmax},fn(dt){B.fn(dt);const T=S.touch,d=(s.y-S.SURF)/(S.BED-S.SURF),L=s.L;dmax=Math.max(dmax,d);if(s.stun>0||s.air)return;
  let near=false;for(const f of S.fish)if(!f.off&&f.kind!=="plankton"&&f.kind!=="star"&&f.s/S.bite()>=S.EAT.RATIO*.92&&Math.hypot(f.x-s.x,f.y-s.y)<L*2.2+f.s)near=true;
  if(near)return;/* fleeing a bigger creature wins */
  if(band==="deep"&&d<.7&&B.st.mode!=="rise"){T.dir=Math.PI/2+Math.sin(performance.now()/900)*.5;T.drive=1}
  if(band==="shallow"&&d>.22){T.dir=-Math.PI/2;T.drive=1}}}}}'''
srv=subprocess.Popen([sys.executable,'-m','http.server',str(PORT),'--bind','127.0.0.1'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(1)
res={}
try:
 with sync_playwright() as p:
  b=p.chromium.launch();cx=b.new_context(viewport={'width':915,'height':412},bypass_csp=True,service_workers='block');pg=cx.new_page()
  pg.goto(f'http://127.0.0.1:{PORT}/');pg.wait_for_timeout(300)
  for mode,secs in [('timed',80),('endless',CAP)]:
   for band in ['deep','shallow']:
    for t in ['white','hammer','tiger']:
     res[(mode,band,t)]=pg.evaluate('''([N,t,BOT,WRAP,band,mode,secs])=>{const mk=eval(WRAP)(BOT,band),out=[];for(let i=0;i<N;i++){__sa.startAs(t,mode);localStorage.setItem("sharkAttack_diverTip","1");const B=mk(4);
       let ft=-1,lt=-1,tt=0;const el=__sa.sim(secs,dt=>{tt+=dt;if(ft<0&&__sa.surfersCaught>0)ft=tt;if(lt<0&&__sa.shark.lvl>=6)lt=tt;B.fn(dt)});const s=__sa.shark;
       out.push({end:__sa.endReason||"alive",t:el,ft,lt,lvl:s.lvl,score:__sa.score,dd:(s.y-__sa.SURF)/(__sa.BED-__sa.SURF),dmax:B.dmax})}__sa.setMode("timed");return out}''',[N,t,BOT,WRAP,band,mode,secs])
  b.close()
finally: srv.terminate()
med=lambda a:st.median(a) if a else -1
print(f"{'mode':8}{'bot':8}{'type':7}{'eaten':>6}{'time/alive':>11}{'caught':>7}{'lvl':>5}{'score':>7}{'1st surfer':>12}{'surfer size':>12}  eaten at depth (<.3/.3-.6/>.6)  median death t")
for (mode,band,t),r in res.items():
  e=[x for x in r if x['end']=='eaten'];ok=sum(1 for x in r if x['end'] in ('time','alive'));c=sum(1 for x in r if x['end']=='caught')
  bins=[sum(1 for x in e if x['dd']<.3),sum(1 for x in e if .3<=x['dd']<.6),sum(1 for x in e if x['dd']>=.6)]
  ft=[x['ft'] for x in r if x['ft']>=0];lt=[x['lt'] for x in r if x['lt']>=0]
  print(f"{mode:8}{band:8}{t:7}{len(e):>6}{ok:>11}{c:>7}{st.mean(x['lvl'] for x in r):5.1f}{st.mean(x['score'] for x in r):7.0f}{f'{len(ft)}/{len(r)} {med(ft):.0f}s':>12}{f'{len(lt)}/{len(r)} {med(lt):.0f}s':>12}  {str(bins):30}  {med([x['t'] for x in e]):.1f}")
