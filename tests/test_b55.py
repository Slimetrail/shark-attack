# b55 (Jeremy t1627u via Eve): 1 fish in an outgrown depth band STAY (swimming, drawn, not faded), only too small to eat, and harmless
#  2 eating thresholds: surfers HUD 5, sail boats HUD 7, cargo ships HUD 9 (internal lvl 4/6/8), spawn mix follows
#  3 chaser cap from HUD 5: never more than CHASE.CAP would-be eaters spawned within CHASE.NEAR screens of the shark
# Run: /workspace/.pwvenv/bin/python tests/test_b55.py (port SA_PORT55, default 8959). Pretend phone (Chromium touch emulation), never a real phone.
import subprocess,sys,os,time,json
from playwright.sync_api import sync_playwright
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)));PORT=int(os.environ.get('SA_PORT55','8959'));URL=f'http://127.0.0.1:{PORT}/'
srv=subprocess.Popen([sys.executable,'-m','http.server',str(PORT),'--bind','127.0.0.1'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(.8)
ok=bad=0
def check(c,m):
  global ok,bad
  print(('PASS ' if c else 'FAIL ')+m);ok+=bool(c);bad+=not c
rd=lambda n:open(os.path.join(ROOT,n)).read()
check(json.loads(rd('version.json'))['build']=="59" and 'content="59"' in rd('index.html') and 'game.js?v=59' in rd('index.html') and 'game.js?v=59' in rd('sw.js'),'build 59 in version.json, index.html and sw.js')
try:
 with sync_playwright() as p:
  b=p.chromium.launch()
  cx=b.new_context(viewport={'width':844,'height':390},is_mobile=True,has_touch=True,bypass_csp=True,service_workers='block');pg=cx.new_page();errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
  pg.goto(URL);pg.wait_for_timeout(400);pg.touchscreen.tap(422,195);pg.wait_for_timeout(300)
  J=lambda s:pg.evaluate(s)
  # 1 fish stay in the outgrown top band
  r=J('''(()=>{__sa.startAs("white","endless");__sa.god=true;__sa.setLevel(5);const s=__sa.shark,S=__sa.SURF,D=__sa.BED-S;s.y=S+D*.2;s.spd=0;s.air=false;
    const F=__sa.fish.slice(0,6);F.forEach((f,i)=>{__sa.spawnFish(f,false);f.x=s.x+(i-3)*40;f.y=S+D*.12;__sa.setCreature(f,__sa.bite()*.6,"fish");f.off=false;f.fade=0;f.tiny=false});
    const sc0=__sa.score;let gone=0,fade=0;
    for(let k=0;k<90;k++){__sa.sim(1/30);for(const f of F)if(f.off&&Math.abs(f.y-(S+D*.12))<D*.2&&Math.abs(f.x-s.x)<innerWidth*.3)gone++;for(const f of F)if(f.fade>0)fade++}
    const alive=F.filter(f=>!f.off).length,tiny=F.filter(f=>f.tiny).length,food=F.filter(f=>!f.off&&!f.tiny&&__sa.rel(f)<0).length;
    /* touch test: put the shark's mouth on a tiny fish */const f=F.find(q=>!q.off&&q.tiny);let eaten=null;if(f){s.y=f.y;s.x=f.x-s.L*.45;s.ang=0;const sc=__sa.score;f.bump=0;let fl=0,bu=0;for(let k=0;k<12;k++){f.x=s.x+s.L*.1;f.y=s.y;f.vx=0;f.vy=0;__sa.sim(1/60);if(f.st==='flee')fl++;if(f.bump>0)bu++}eaten=__sa.score>sc||f.off;var flee=fl,bump=bu}
    return {alive,tiny,food,gone,fade,eaten,flee:typeof flee==='undefined'?-1:flee,bump:typeof bump==='undefined'?-1:bump,gA:__sa.goneAt(S+D*.12)}})()''')
  check(r['alive']==6 and r['gone']==0 and r['fade']==0,f'HUD 6 shark, 6 fish in the outgrown top band: all still swimming after 3 s (none faded or despawned on screen) {r}')
  check(r['tiny']==6 and r['food']==0,f'those fish are marked too small to eat (tiny), not food {r["tiny"]}/6')
  check(r['eaten'] is False,'mouth on a tiny fish: not eaten, no points')
  check(r['flee']==0,f'a tiny fish does not flee from the shark (it is not prey) {r["flee"]}')
  check(r['bump']==0,f'a tiny fish does not bump the shark (harmless, no contact) {r["bump"]}')
  r=J('''(()=>{__sa.setLevel(5);const s=__sa.shark,S=__sa.SURF,D=__sa.BED-S;s.y=S+D*.1;let off=0,tiny=0,n=0,dang=0;
    for(let k=0;k<200;k++){const f=__sa.fish[k%__sa.fish.length];__sa.spawnFish(f,false);if(__sa.goneAt(f.y)){n++;if(f.off)off++;if(f.tiny)tiny++;if(f.s/__sa.bite()>=__sa.EAT.RATIO)dang++}}return {n,off,tiny,dang}})()''')
  check(r['n']>0 and r['off']==0 and r['tiny']==r['n'] and r['dang']==0,f'new spawns in an outgrown band appear (not switched off), tiny and harmless {r}')
  r=J('(()=>{__sa.setLevel(3);const S=__sa.SURF,D=__sa.BED-S;return __sa.goneAt(S+D*.12)})()')
  check(r is False,'HUD 4: the top band is not outgrown yet (fish there are food)')
  # 2 thresholds
  G=J('({sl:__sa.GROW.SURF_LVL,sa:__sa.SURFACE.SAIL_LVL,ca:__sa.SURFACE.CARGO_LVL})')
  check((G['sl']+1,G['sa']+1,G['ca']+1)==(5,7,9),f'surfers HUD 5, sail boats HUD 7, cargo ships HUD 9 (got {G["sl"]+1},{G["sa"]+1},{G["ca"]+1})')
  mix=J('''(()=>{const o={};for(const l of [3,4,5,6,7,8,9]){__sa.setLevel(l);const c=[0,0,0,0];for(let i=0;i<600;i++){const s=__sa.surf[0];__sa.spawnSurf(s,false);c[s.k]++}o[l+1]=c}return o})()''')
  check(mix['6'][2]==0 and mix['6'][3]==0 and mix['5'][2]==0,f'HUD 5-6: surfers only (no boats) {mix["5"]} {mix["6"]}')
  check(mix['7'][2]>0 and mix['7'][3]==0 and mix['8'][3]==0,f'HUD 7-8: sail boats, no cargo ships {mix["7"]} {mix["8"]}')
  check(mix['9'][3]>0 and mix['10'][3]>0,f'HUD 9+: cargo ships {mix["9"]}')
  # 3 chaser cap
  r=J('''(()=>{__sa.setLevel(5);const s=__sa.shark,S=__sa.SURF,D=__sa.BED-S;s.y=S+D*1.2;__sa.clearFood();const C=__sa.CHASE,F=__sa.fish,B=__sa.bite();
    const put=(f,dx)=>{__sa.setCreature(f,B*2,"shark");f.off=false;f.tiny=false;f.x=s.x+dx;f.y=s.y};for(const f of F)f.off=true;
    const t=F[F.length-1];const res=[];for(let n=0;n<=Math.min(C.CAP,F.length-2);n++){for(let i=0;i<F.length-1;i++)F[i].off=true;for(let i=0;i<n;i++)put(F[i],(i+1)*30);res.push(__sa.chaseCapped(t,"shark",B*2))}
    __sa.setLevel(3);res.push(__sa.chaseCapped(t,"shark",B*2));__sa.setLevel(5);res.push(__sa.chaseCapped(t,"fish",B*.5));return {res,C}})()''')
  cap=r['C']['CAP'];res=r['res']
  check(cap<=3 and len(res)==cap+3 and all(x is False for x in res[:cap]) and res[cap] is True,f'HUD 6: a would-be eater is capped once {cap} eaters are near ({res[:cap+1]})')
  check(len(res)>cap+2 and res[cap+1] is False,'HUD 4 (before the top band is outgrown): no cap')
  check(len(res)>cap+2 and res[cap+2] is False,'food is never capped')
  r=J('''(()=>{__sa.setLevel(5);const s=__sa.shark,S=__sa.SURF,D=__sa.BED-S,C=__sa.CHASE,B=()=>__sa.bite();s.y=S+D*1.2;let mx=0,over=0;
    for(let k=0;k<400;k++){const f=__sa.fish[k%__sa.fish.length];__sa.spawnFish(f,false);f.x=s.x+(Math.random()-.5)*innerWidth*C.NEAR;f.y=s.y+(Math.random()-.5)*innerHeight*C.NEAR;
      const n=__sa.fish.filter(q=>!q.off&&!q.tiny&&q.kind!=="plankton"&&q.kind!=="star"&&q.s/B()>=__sa.EAT.RATIO&&Math.abs(q.x-s.x)<innerWidth*C.NEAR&&Math.abs(q.y-s.y)<innerHeight*C.NEAR).length;mx=Math.max(mx,n)}
    return {mx,cap:C.CAP}})()''')
  check(r['cap']<=3 and r['mx']<=r['cap']+1,f'400 spawns placed around a HUD 6 shark: never more than CAP+1 eaters near (max {r["mx"]}, cap {r["cap"]})')
  check(not errs,f'no page errors {errs[:2]}')
  b.close()
finally: srv.terminate()
print(f'{ok} passed, {bad} failed');sys.exit(1 if bad else 0)
