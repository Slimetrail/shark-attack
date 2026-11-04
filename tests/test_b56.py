# b56 (Jeremy t1637u via Eve): 1 only the MOUTH of a bigger fish/shark eats you; bumping its top or body is harmless (a shove)
#  2 your own mouth still eats prey the same way  3 thresholds unchanged (surfers HUD 5, sail HUD 7, cargo HUD 9)
#  4 fewer larger sharks: chaser cap 1 from HUD 9 (incl. max size 10), fewer deep sharks (SHARK_P_DEEP, MAX_BIG)
# Run: /workspace/.pwvenv/bin/python tests/test_b56.py (port SA_PORT56, default 8961). Pretend phone (Chromium touch emulation), never a real phone.
import subprocess,sys,os,time,json
from playwright.sync_api import sync_playwright
ROOT=os.environ.get('SA_ROOT') or os.path.dirname(os.path.dirname(os.path.abspath(__file__)));PORT=int(os.environ.get('SA_PORT56','8961'));URL=f'http://127.0.0.1:{PORT}/'
srv=subprocess.Popen([sys.executable,'-m','http.server',str(PORT),'--bind','127.0.0.1'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(.8)
ok=bad=0
def check(c,m):
  global ok,bad
  print(('PASS ' if c else 'FAIL ')+m);ok+=bool(c);bad+=not c
rd=lambda n:open(os.path.join(ROOT,n)).read()
check(json.loads(rd('version.json'))['build']=="56" and 'content="56"' in rd('index.html') and 'game.js?v=56' in rd('index.html') and 'game.js?v=56' in rd('sw.js'),'build 56 in version.json, index.html and sw.js')
# one contact scene: eater (2x your bite, a shark) held in place for 1 s next to a still HUD 3 shark; real update loop, god mode OFF
SCENE='''([pos,lvl])=>{const S=__sa;S.startAs("white","endless");S.god=false;S.setLevel(lvl);S.sim(2.2);/* past EAT.GRACE */S.clearFood();const s=S.shark,D=S.BED-S.SURF;s.y=S.SURF+D*1.2;s.x=S.camX+innerWidth/2;s.ang=0;s.spd=0;S.touch.on=false;S.touch.drive=0;for(let k=0;k<90;k++){s.spd=0;S.sim(1/60)}/* camera settles on you */S.clearFood();s.x=S.camX+innerWidth/2;
  const L=s.L,B=S.bite(),f=S.fish[0];S.setCreature(f,B*2,"shark");f.off=false;f.tiny=false;f.fade=0;f.rest=0;
  const fs=f.s;let X,Y,VX;
  if(pos==="mouth"){VX=-60;f.x=0;f.y=0;f.vx=-60;const mp=S.mouthPt(f);X=s.x-mp[0];Y=s.y-mp[1]}          /* its mouth right on you */
  else if(pos==="top"){VX=60;X=s.x;Y=s.y-(L*.32+fs*.9)*.85}          /* you touch the top of its body */
  else if(pos==="tail"){VX=60;X=s.x+(L*.32+fs*.9)*.8;Y=s.y}          /* you bump its tail end (it faces away) */
  else if(pos==="side"){VX=-60;X=s.x;Y=s.y+(L*.32+fs*.9)*.85}        /* under you, facing left: belly contact */
  const x0=s.x,y0=s.y;let bumps=0,frames=0,minD=1e9;
  let shove=0;for(let k=0;k<60&&S.state==="play";k++){s.x=x0;s.y=y0;s.spd=0;s.ang=0;f.x=X;f.y=Y;f.vx=VX;f.vy=0;f.rest=0;f.bump=0;S.sim(1/60);frames++;if(f.s!==fs||f.off)break;/* slot reused: stop */if(f.bump>0)bumps++;shove=Math.max(shove,Math.hypot(s.x-x0,s.y-y0))}
  return {state:S.state,end:S.endReason,bumps,frames,moved:+shove.toFixed(1),eater:f.danger,L:+L.toFixed(1),fs:+fs.toFixed(1)}}'''
try:
 with sync_playwright() as p:
  b=p.chromium.launch()
  cx=b.new_context(viewport={'width':844,'height':390},is_mobile=True,has_touch=True,bypass_csp=True,service_workers='block');pg=cx.new_page();errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
  pg.goto(URL);pg.wait_for_function('!!window.__sa',timeout=30000);pg.wait_for_timeout(400);pg.touchscreen.tap(422,195);pg.wait_for_timeout(300)
  J=lambda s,a=None:pg.evaluate(s,a)
  for lvl in [2,6]:
   r=J(SCENE,['mouth',lvl]);check(r['end']=='eaten' and r['state']!='play',f'HUD {lvl+1}: a bigger shark whose MOUTH touches you eats you {r}')
   for pos in ['top','tail','side']:
    r=J(SCENE,[pos,lvl]);check(r['state']=='play' and r['end']!='eaten' and r['frames']==60 and r['eater'],f'HUD {lvl+1}: touching its {pos} for 1 s does NOT kill you {r}')
    check(r['bumps']>=50 and r['moved']>0,f'HUD {lvl+1}: {pos} contact is a bump: you get shoved (max shove per frame {r["moved"]} px, bump frames {r["bumps"]})')
  # it still chases and eats you when it swims mouth-first at you (real AI, no holding)
  r=J('''(()=>{const S=__sa;S.startAs("white","endless");S.god=false;S.setLevel(2);S.sim(2.2);S.clearFood();const s=S.shark,D=S.BED-S.SURF;s.y=S.SURF+D*.5;s.x=S.camX+innerWidth/2;s.ang=0;s.spd=0;S.touch.on=false;
    const f=S.fish[0];S.setCreature(f,S.bite()*2,"shark");f.off=false;f.tiny=false;f.fade=0;f.rest=0;f.x=s.x+s.L*2.2;f.y=s.y;f.vx=-60;f.vy=0;let t=0;for(;t<8&&S.state==="play";t+=1/60){s.spd=0;S.sim(1/60)}return {end:S.endReason,t:+t.toFixed(2)}})()''')
  check(r['end']=='eaten',f'a chasing bigger shark that reaches you mouth-first still eats you {r}')
  # your own mouth eats prey the same
  r=J('''(()=>{const S=__sa;S.startAs("white","endless");S.god=true;S.setLevel(2);S.sim(.5);S.clearFood();const s=S.shark,D=S.BED-S.SURF;s.y=S.SURF+D*.5;s.ang=0;s.spd=0;
    const out=[];for(const [nm,dx,dy] of [["mouth",.48,0],["body",-.2,0]]){const f=S.fish[1];S.setCreature(f,S.bite()*.5,"fish");f.off=false;f.tiny=false;f.fade=0;const sc=S.score;f.x=s.x+s.L*dx;f.y=s.y+dy;f.vx=0;S.sim(1/60);out.push([nm,S.score>sc])}return out})()''')
  check(all(x[1] for x in r),f'prey touching your mouth or body is still eaten {r}')
  # 3 thresholds unchanged
  G=J('({sl:__sa.GROW.SURF_LVL,sa:__sa.SURFACE.SAIL_LVL,ca:__sa.SURFACE.CARGO_LVL})')
  check((G['sl']+1,G['sa']+1,G['ca']+1)==(5,7,9),f'thresholds unchanged: surfers HUD 5, sail boats HUD 7, cargo ships HUD 9 (got {G["sl"]+1},{G["sa"]+1},{G["ca"]+1})')
  # 4 fewer chasers
  C=J('({C:__sa.CHASE,cr:{p:__sa.CREATURES.SHARK_P_DEEP,m:__sa.CREATURES.MAX_BIG},caps:[4,5,6,7,8,9].map(l=>{__sa.setLevel(l);return __sa.chaseCap()})})')
  check(C['caps']==[2,2,2,2,1,1],f'chaser cap by HUD 5..10: {C["caps"]} (b55: 2 everywhere; b56: 1 from HUD 9, max size included)')
  check(C['cr']['p']<.45 and C['cr']['m']<3,f'fewer deep sharks than b55 (SHARK_P_DEEP {C["cr"]["p"]} < .45, MAX_BIG {C["cr"]["m"]} < 3)')
  for lvl in [8,9]:
   r=J('''(lvl)=>{__sa.startAs("white","endless");__sa.god=true;__sa.setLevel(lvl);const s=__sa.shark,S=__sa.SURF,D=__sa.BED-S,C=__sa.CHASE,B=()=>__sa.bite();s.y=S+D*1.2;let mx=0;
    for(let k=0;k<400;k++){const f=__sa.fish[k%__sa.fish.length];__sa.spawnFish(f,false);f.x=s.x+(Math.random()-.5)*innerWidth*C.NEAR;f.y=s.y+(Math.random()-.5)*innerHeight*C.NEAR;
      const n=__sa.fish.filter(q=>!q.off&&!q.tiny&&q.kind!=="plankton"&&q.kind!=="star"&&q.s/B()>=__sa.EAT.RATIO&&Math.abs(q.x-s.x)<innerWidth*C.NEAR&&Math.abs(q.y-s.y)<innerHeight*C.NEAR).length;mx=Math.max(mx,n)}
    return {mx,cap:__sa.chaseCap()}}''',lvl)
   check(r['cap']==1 and r['mx']<=2,f'HUD {lvl+1}: 400 spawns around you: at most cap+1 = 2 eaters near (max {r["mx"]})')
  check(not errs,f'no page errors {errs[:2]}')
  b.close()
finally: srv.terminate()
print(f'{ok} passed, {bad} failed');sys.exit(1 if bad else 0)
