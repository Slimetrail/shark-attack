# b56 (copy of tools/pace_b55.py, waits for the game to load) pace + death report (pretend phone 844x390, simulated time). N endless rounds (white shark, tests/balance_endless.py bot from THIS repo).
# Per HUD size 5..10: rounds reaching it + mean time; deaths by cause (eaten: killer kind + HUD size + depth band), mean chasers (eaters) on screen per HUD size.
# Usage: /workspace/.pwvenv/bin/python tools/pace_b55.py [GAME_ROOT] [PORT] [N] [SECONDS]
import subprocess,sys,os,time,json,re,statistics as st,collections
from playwright.sync_api import sync_playwright
HERE=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT=sys.argv[1] if len(sys.argv)>1 else HERE;PORT=int(sys.argv[2]) if len(sys.argv)>2 else 8981;N=int(sys.argv[3]) if len(sys.argv)>3 else 12;SEC=int(sys.argv[4]) if len(sys.argv)>4 else 600
BOT=re.search(r"BOT=r'''(.*?)'''",open(os.path.join(HERE,'tests','balance_endless.py')).read(),re.S).group(1)
srv=subprocess.Popen([sys.executable,'-m','http.server',str(PORT),'--bind','127.0.0.1'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(1)
try:
 with sync_playwright() as p:
  b=p.chromium.launch();cx=b.new_context(viewport={'width':844,'height':390},is_mobile=True,has_touch=True,bypass_csp=True,service_workers='block');pg=cx.new_page();pg.goto(f'http://127.0.0.1:{PORT}/');pg.wait_for_function('!!window.__sa',timeout=30000);pg.wait_for_timeout(500)
  out=[]
  for i in range(N):
   out.append(pg.evaluate("""([BOT,SEC])=>{const S=__sa,mk=eval(BOT);S.startAs("white","endless");localStorage.setItem("sharkAttack_diverTip","1");const B=mk(4);let t=0,r={},ch={},nf={};
   const fn=dt=>{t+=dt;const l=S.shark.lvl;for(let L=3;L<=9;L++)if(r[L]===undefined&&l>=L)r[L]=+t.toFixed(1);
     let n=0,m=0;for(const f of S.fish)if(!f.off&&Math.abs(f.x-S.shark.x)<innerWidth/2&&Math.abs(f.y-S.shark.y)<innerHeight/2){if(f.danger)n++;else if(S.rel(f)<0&&!f.tiny)m++}(ch[l]=ch[l]||[]).push(n);(nf[l]=nf[l]||[]).push(m);B.fn(dt)};
   const el=S.sim(SEC,fn,1/30);let k=null;if(S.endReason==="eaten"){let bd=1e9;for(const f of S.fish)if(!f.off&&f.s/S.bite()>=S.EAT.RATIO){const d=Math.hypot(f.x-S.shark.x,f.y-S.shark.y);if(d<bd){bd=d;k=f.kind}}}
   const av=o=>Object.fromEntries(Object.entries(o).map(([a,v])=>[a,+(v.reduce((x,y)=>x+y,0)/v.length).toFixed(2)]));
   return {r,el:+el.toFixed(1),end:S.endReason||"alive",lvl:S.shark.lvl,killer:k,depth:+S.depthOf(S.shark.y).toFixed(2),ch:av(ch),food:av(nf)}}""",[BOT,SEC]))
  b.close()
finally: srv.terminate()
print(json.dumps(out))
for L in range(3,10):
  ts=[o['r'][str(L)] for o in out if str(L) in o['r']]
  print(f"HUD {L+1}: reached {len(ts)}/{len(out)}"+(f"  time mean {st.mean(ts):.1f}s median {st.median(ts):.1f}s range {min(ts)}-{max(ts)}" if ts else ""))
print('ends:',dict(collections.Counter(o['end'] for o in out)))
print('deaths (killer, HUD size at death, depth):',[(o['killer'],o['lvl']+1,o['depth']) for o in out if o['end']=='eaten'])
for L in range(0,10):
  a=[o['ch'][str(L)] for o in out if str(L) in o['ch']];b2=[o['food'][str(L)] for o in out if str(L) in o['food']]
  if a: print(f"HUD {L+1}: chasers on screen mean {st.mean(a):.2f}  edible food on screen mean {st.mean(b2):.2f}")
