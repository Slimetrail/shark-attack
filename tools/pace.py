# Pace report (pretend phone, Chromium; simulated time, so box load does not change the numbers): N endless rounds as the white shark,
# driven by the tests/balance_endless.py bot (diving when nothing edible is in view). Prints, per HUD size 4/5/7/10: how many rounds got there,
# mean/range time to reach it and fish eaten to reach it, then the STRETCH times (HUD 1->4, 4->7, 7->10 from the means) and points per 20 s at the cap.
# Usage: /workspace/.pwvenv/bin/python tools/pace.py [GAME_ROOT (default: this repo)] [PORT (8971)] [N rounds (8)]
#   e.g. compare builds: git worktree add /tmp/sa51 e5e9b4f && /workspace/.pwvenv/bin/python tools/pace.py /tmp/sa51 8972 8
#   (the bot always comes from THIS repo's tests/balance_endless.py, so every build is played by the same bot)
import subprocess,sys,os,time,json,re,statistics as st
from playwright.sync_api import sync_playwright
HERE=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT=sys.argv[1] if len(sys.argv)>1 else HERE;PORT=int(sys.argv[2]) if len(sys.argv)>2 else 8971;N=int(sys.argv[3]) if len(sys.argv)>3 else 8
src=open(os.path.join(HERE,'tests','balance_endless.py')).read();BOT=re.search(r"BOT=r'''(.*?)'''",src,re.S).group(1);assert 'else{T.dir=Math.atan2(H*.35,W*.3);T.drive=.7}' in BOT,'bot must dive when nothing edible is in view (same bot as the b53 pace runs)'
srv=subprocess.Popen([sys.executable,'-m','http.server',str(PORT),'--bind','127.0.0.1'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(1)
try:
 with sync_playwright() as p:
  b=p.chromium.launch();cx=b.new_context(viewport={'width':844,'height':390},is_mobile=True,has_touch=True,bypass_csp=True,service_workers='block');pg=cx.new_page();pg.goto(f'http://127.0.0.1:{PORT}/');pg.wait_for_timeout(500)
  out=pg.evaluate("""([N,BOT])=>{const mk=eval(BOT),out=[];for(let i=0;i<N;i++){__sa.startAs("white","endless");localStorage.setItem("sharkAttack_diverTip","1");const B=mk(4);let t=0,n=0,sc=__sa.score,r={},capT=-1,capS=0,p20=-1;
   const fn=dt=>{t+=dt;if(__sa.score>sc){n++;sc=__sa.score}for(const L of [3,4,6,9])if(r[L]===undefined&&__sa.shark.lvl>=L)r[L]={t:+t.toFixed(1),n};if(__sa.shark.lvl>=9&&capT<0){capT=t;capS=__sa.score}if(capT>=0&&p20<0&&t-capT>=20)p20=__sa.score-capS;B.fn(dt)};
   const el=__sa.sim(900,fn,1/30);out.push({r,p20,el,end:__sa.endReason||"alive"})}return out}""",[N,BOT])
  b.close()
finally: srv.terminate()
print(json.dumps(out))
for L in [3,4,6,9]:
  ts=[o['r'][str(L)]['t'] for o in out if str(L) in o['r']];ns=[o['r'][str(L)]['n'] for o in out if str(L) in o['r']]
  if ts: print(f"HUD {L+1}: reached {len(ts)}/{len(out)}  time mean {st.mean(ts):.1f}s range {min(ts)}-{max(ts)}  eats mean {st.mean(ns):.1f} range {min(ns)}-{max(ns)}")
  else: print(f"HUD {L+1}: not reached")
pp=[o['p20'] for o in out if o['p20']>=0];print('points per 20s after reaching HUD10:',pp, 'mean',st.mean(pp) if pp else None)
M={}
for L in [3,6,9]:
  ts=[o['r'][str(L)]['t'] for o in out if str(L) in o['r']];M[L]=st.mean(ts) if ts else None
if all(M.values()): print(f"STRETCH HUD 1->4 {M[3]:.1f}s, HUD 4->7 {M[6]-M[3]:.1f}s, HUD 7->10 {M[9]-M[6]:.1f}s (from the means of rounds that got there)")
