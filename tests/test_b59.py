# b59 (owner, Nov 5). Pretend phone (Chromium), never a real phone.
# Surfers are food through HUD 8 and too small from HUD 9 (when cargo starts).
# Run: python3 tests/test_b59.py   (port SA_PORT59, default 8965)
import subprocess,sys,os,time,json
from playwright.sync_api import sync_playwright
ROOT=os.environ.get('SA_ROOT') or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PORT=int(os.environ.get('SA_PORT59','8965'));URL=f'http://127.0.0.1:{PORT}/'
srv=subprocess.Popen([sys.executable,'-m','http.server',str(PORT),'--bind','127.0.0.1'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(.8)
ok=bad=0
def check(c,m):
  global ok,bad
  print(('PASS ' if c else 'FAIL ')+m);ok+=bool(c);bad+=not c
rd=lambda n:open(os.path.join(ROOT,n)).read()
check(json.loads(rd('version.json'))['build']=='59' and 'content="59"' in rd('index.html') and 'game.js?v=59' in rd('index.html') and 'game.js?v=59' in rd('sw.js') and 'PREFIX="sharkattack-v"' in rd('sw.js'),'[read] build 59 in version.json, index.html, sw.js (cache sharkattack-v59)')
try:
 with sync_playwright() as p:
  b=p.chromium.launch()
  cx=b.new_context(viewport={'width':844,'height':390},is_mobile=True,has_touch=True,bypass_csp=True,service_workers='block');pg=cx.new_page();errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
  pg.goto(URL);pg.wait_for_function('!!window.__sa',timeout=30000);pg.wait_for_timeout(300);pg.touchscreen.tap(422,195);pg.wait_for_timeout(250)
  J=lambda s,a=None:pg.evaluate(s,a)
  J('__sa.startAs("white","endless");__sa.god=true')
  # surfer: food at HUD 8, too small at HUD 9, shallow and deep, in the air and from below
  surf=J('''()=>{const bite=(hud,mark,air)=>{__sa.startAs("white","endless");__sa.god=true;__sa.setLevel(hud-1);__sa.depthMark=mark;const s=__sa.shark;s.ang=0;s.spd=0;s.vx=0;s.vy=0;s.g=0;s.air=!!air;s.y=__sa.SURF+(air?-16:s.L*.1);__sa.surf.forEach(q=>{q.zip=999;q.bump=0});
      const can=__sa.canEatSurf({k:0}),ret=__sa.surfRetired({k:0}),draw=__sa.surfDrawK({k:0})*__sa.SURFER_SPAN,sc0=__sa.score;
      for(let i=0;i<4;i++)__sa.sim(1/60,()=>{s.air=!!air;s.vx=0;s.vy=0;s.g=0;s.spd=0;s.ang=0;s.y=__sa.SURF+(air?-16:s.L*.1);const q=__sa.surf[0];q.zip=0;q.k=0;q.vx=0;q.x=__sa.mouth()[0]},1/60);
      return {sc:__sa.score-sc0,can,ret,bump:__sa.surf[0].bump||0,draw,st:__sa.state}};
    const z=__sa.ZONE;return {h8:bite(8,0,true),h8deep:bite(8,z.CARGO+1,true),h9:bite(9,0,true),h9deep:bite(9,z.SURF,true),h9below:bite(9,0,false)}}''')
  check(surf['h8']['sc']>0 and surf['h8']['can'] is True and surf['h8']['ret'] is False and surf['h8deep']['sc']>0 and surf['h8deep']['can'] is True,f'[tested] HUD 8 a surfer is food, at the surface and in the black zone {surf["h8"]} {surf["h8deep"]}')
  check(surf['h9']['sc']==0 and surf['h9']['can'] is False and surf['h9']['ret'] is True and surf['h9']['bump']==0 and surf['h9deep']['sc']==0 and surf['h9deep']['can'] is False and surf['h9below']['sc']==0 and surf['h9below']['bump']==0 and surf['h9']['st']=='play',f'[tested] HUD 9 a surfer is too small: not food, no bump, in the air or from below {surf["h9"]} {surf["h9deep"]} {surf["h9below"]}')
  check(surf['h9']['draw']<surf['h8']['draw']*0.4 and surf['h9']['draw']>0,f'[tested] HUD 9 a surfer draws tiny next to the HUD 8 surfer ({surf["h9"]["draw"]:.1f}px vs {surf["h8"]["draw"]:.1f}px)')
  # boundaries that must stay put: sail 7 on / 10 off, cargo 9 on / 13 off, tanker 10 on / 13 off, deep fish 12 on
  edge=J('''()=>{__sa.startAs("white","endless");__sa.god=true;const at=h=>{__sa.setLevel(h-1);return {sail:__sa.canEatSurf({k:2}),cargo:__sa.canEatSurf({k:3}),tank:__sa.canEatSurf({k:4}),surf:__sa.canEatSurf({k:0}),deep:__sa.shark.lvl>=__sa.SURFACE.DEEP_LVL,retS:__sa.surfRetired({k:0})}};
    const o={};for(const h of [6,7,8,9,10,11,12,13])o[h]=at(h);return o}''')
  check(edge['6']['sail'] is False and edge['7']['sail'] is True and edge['9']['sail'] is True and edge['10']['sail'] is False,f'[read] sail boats still food at HUD 7-9 and off at 10 { {k:edge[k]["sail"] for k in edge} }')
  check(edge['8']['cargo'] is False and edge['9']['cargo'] is True and edge['12']['cargo'] is True and edge['13']['cargo'] is False,f'[read] cargo still food at HUD 9-12 and off at 13')
  check(edge['9']['tank'] is False and edge['10']['tank'] is True and edge['12']['tank'] is True and edge['13']['tank'] is False,f'[read] tankers still food at HUD 10-12 and off at 13')
  check(edge['11']['deep'] is False and edge['12']['deep'] is True and edge['8']['surf'] is True and edge['9']['surf'] is False and edge['9']['retS'] is True,f'[read] deep fish still start at HUD 12; surfers flip off at HUD 9')
  # no gap: every HUD from 5 to 20 has at least one edible food, and the numbers stay finite
  gap=J('''()=>{__sa.startAs("white","endless");__sa.god=true;const rows=[];
    for(let h=5;h<=20;h++){__sa.setLevel(h-1);const s=__sa.shark,l=s.lvl,food=[];
      if(__sa.canEatSurf({k:0}))food.push("surfer");if(__sa.canEatSurf({k:2}))food.push("sail");if(__sa.canEatSurf({k:3}))food.push("cargo");if(__sa.canEatSurf({k:4}))food.push("tanker");if(l>=__sa.SURFACE.DEEP_LVL)food.push("deep");
      __sa.feed(__sa.need(l)*0.25);
      const nums=[s.x,s.y,s.L,s.meter,s.spd,__sa.worldK,__sa.need(l),__sa.trueGrow(l),__sa.sharkMax(l),__sa.bite()];
      rows.push({h,food,fin:nums.every(Number.isFinite),bar:__sa.barFrac()})}
    return rows}''')
  empty=[r for r in gap if not r['food']]
  badn=[r for r in gap if not r['fin'] or not (0<=r['bar']<=1)]
  check(not empty,f'[tested] HUD 5 through 20 each have at least one food ({[(r["h"],r["food"]) for r in gap]})')
  check(not badn and len(gap)==16,f'[tested] HUD 5 through 20 stay finite and the bar stays in range {badn[:3]}')
  check(not errs,f'[tested] no page errors {errs[:3]}')
  b.close()
finally: srv.terminate()
print(f'{ok} passed, {bad} failed');sys.exit(1 if bad else 0)
