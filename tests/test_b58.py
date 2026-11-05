# b58 (owner, Nov 5). Pretend phone (Chromium), never a real phone.
# Run: python3 tests/test_b58.py   (port SA_PORT58, default 8964)
#
# Endless growth (the size-10 cap is gone) and prey stages by HUD size.
# Each line is tagged [tested] (the browser ran the game) or [read] (a live value).
import subprocess,sys,os,time,json
from playwright.sync_api import sync_playwright
ROOT=os.environ.get('SA_ROOT') or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PORT=int(os.environ.get('SA_PORT58','8964'));URL=f'http://127.0.0.1:{PORT}/'
srv=subprocess.Popen([sys.executable,'-m','http.server',str(PORT),'--bind','127.0.0.1'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(.8)
ok=bad=0
def check(c,m):
  global ok,bad
  print(('PASS ' if c else 'FAIL ')+m);ok+=bool(c);bad+=not c
rd=lambda n:open(os.path.join(ROOT,n)).read()
src=rd('game.js');html=rd('index.html');sw=rd('sw.js')
check(json.loads(rd('version.json'))['build']=='59' and 'content="59"' in html and 'game.js?v=59' in html and 'game.js?v=59' in sw and 'PREFIX="sharkattack-v"' in sw,'[read] build 59 in version.json, index.html, sw.js (cache sharkattack-v59)')
check('MAX SIZE' not in src and 'MAX_LEVEL' not in src,'[read] game.js has no MAX SIZE label and no MAX_LEVEL cap')
check('doubleclick' not in html.lower() and 'googlesyndication' not in html.lower() and 'adsbygoogle' not in html.lower(),'[read] no ad tags in index.html')
try:
 with sync_playwright() as p:
  b=p.chromium.launch()
  cx=b.new_context(viewport={'width':844,'height':390},is_mobile=True,has_touch=True,bypass_csp=True,service_workers='block');pg=cx.new_page();errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
  pg.goto(URL);pg.wait_for_function('!!window.__sa',timeout=30000);pg.wait_for_timeout(300);pg.touchscreen.tap(422,195);pg.wait_for_timeout(250)
  J=lambda s,a=None:pg.evaluate(s,a)
  J('__sa.startAs("white","endless");__sa.god=true')
  # --- growth past the old cap: bar, label, finite math, speed stays put ---
  g=J('''()=>{const out={};const step=(lvl)=>{__sa.setLevel(lvl);const n=__sa.need(lvl);__sa.feed(n*0.35);const mid=__sa.barFrac(),l0=__sa.shark.lvl;__sa.feed(n);return {l0,l1:__sa.shark.lvl,mid,lab:__sa.sizeLabel(),bar:__sa.barFrac(),need:__sa.need(__sa.shark.lvl),wk:__sa.worldK,tg:__sa.trueGrow(lvl),finite:Number.isFinite(__sa.shark.meter)&&Number.isFinite(__sa.worldK)&&Number.isFinite(__sa.shark.L)&&Number.isFinite(__sa.need(lvl))}};
    out.h13=step(12);out.h20=step(19);out.h40=step(39);
    const sp=[0,9,19,39,200].map(l=>__sa.sharkMax(l));
    out.sp=sp;out.cap=__sa.SPEED_LVL_CAP;out.tgClamp=__sa.trueGrow(5000)===__sa.trueGrow(2000)&&Number.isFinite(__sa.trueGrow(2000));
    out.chase=__sa.chaseCap();__sa.setLevel(39);out.chase40=__sa.chaseCap();out.maxBig=__sa.CREATURES.MAX_BIG;
    return out}''')
  check(g['h13']['l0']==12 and g['h13']['mid']>0.2 and g['h13']['mid']<0.6 and g['h13']['l1']==13 and g['h13']['lab']=='SIZE 14' and g['h13']['finite'],f'[tested] HUD 13 fills part of the bar, then levels to 14, and stays finite {g["h13"]}')
  check(g['h20']['l0']==19 and 0.2<g['h20']['mid']<0.6 and g['h20']['l1']==20 and g['h20']['lab']=='SIZE 21' and g['h20']['finite'],f'[tested] HUD 20 still grows and the bar still fills {g["h20"]}')
  check(g['h40']['l0']==39 and 0.2<g['h40']['mid']<0.6 and g['h40']['l1']==40 and g['h40']['lab']=='SIZE 41' and g['h40']['finite'] and g['h40']['wk']<g['h20']['wk']<g['h13']['wk'],f'[tested] HUD 40 still grows, the world is still shrinking, numbers stay finite {g["h40"]}')
  check(g['sp'][1]>g['sp'][0] and g['sp'][2]==g['sp'][1]==g['sp'][3]==g['sp'][4] and abs(g['sp'][1]/g['sp'][0]-1.36)<0.02 and g['cap']==9,f'[read] top speed rises to HUD 10 and then stays there (1.36x), including HUD 40 and far past it {g["sp"]}')
  check(g['tgClamp'] and g['chase40']==1 and g['chase']==1 and g['maxBig']==2,f'[read] trueGrow stays finite at the exponent clamp; chase cap stays 1 and MAX_BIG stays 2 at HUD 40')
  labs={}
  for hud in (13,20,40):
    J('hud=>__sa.setLevel(hud-1)',hud)
    seen=J('''()=>new Promise(res=>{const c=document.getElementById("c").getContext("2d"),f=c.fillText,seen=[];c.fillText=function(s,...a){seen.push(String(s));return f.call(this,s,...a)};requestAnimationFrame(()=>requestAnimationFrame(()=>{c.fillText=f;res(seen)}))})''')
    labs[hud]=seen
    check(any(s=='SIZE '+str(hud) for s in seen) and not any('MAX' in s for s in seen),f'[tested] HUD draws SIZE {hud} and never MAX { [s for s in seen if "SIZE" in s or "MAX" in s] }')
  # --- edibility by HUD size, same answer shallow and in the black zone ---
  # kind: 0 surfer, 2 sail, 3 cargo, 4 tanker. Expect food / not, and that depth does not flip it.
  matrix=J('''()=>{const eat=(k,hud,mark)=>{__sa.startAs("white","endless");__sa.god=true;__sa.setLevel(hud-1);__sa.depthMark=mark;const s=__sa.shark,air=k<2;s.ang=0;s.spd=0;s.vx=0;s.vy=0;s.g=0;s.air=air;s.y=__sa.SURF+(air?-16:s.L*.1);__sa.surf.forEach(q=>{q.zip=999;q.bump=0});
      const can=__sa.canEatSurf({k}),ret=__sa.surfRetired({k}),sc0=__sa.score;for(let i=0;i<3;i++){__sa.sim(1/60,()=>{s.air=air;s.vx=0;s.vy=0;s.g=0;s.spd=0;s.ang=0;s.y=__sa.SURF+(air?-16:s.L*.1);const q=__sa.surf[0];q.zip=0;q.k=k;q.vx=0;q.x=__sa.mouth()[0]},1/60)}
      return {sc:__sa.score-sc0,can,ret,bump:__sa.surf[0].bump||0,lvl:s.lvl}};
    const marks={shallow:0,black:__sa.ZONE.CARGO+1},kinds=[0,2,3,4],huds=[6,7,8,9,10,11,12,13],out={};
    for(const h of huds){out[h]={};for(const name in marks){out[h][name]={};for(const k of kinds)out[h][name][k]=eat(k,h,marks[name])}}
    return out}''')
  want={6:{0:True,2:False,3:False,4:False},7:{0:True,2:True,3:False,4:False},8:{0:True,2:True,3:False,4:False},9:{0:False,2:True,3:True,4:False},10:{0:False,2:False,3:True,4:True},11:{0:False,2:False,3:True,4:True},12:{0:False,2:False,3:True,4:True},13:{0:False,2:False,3:False,4:False}}
  names={0:'surfer',2:'sail',3:'cargo',4:'tanker'}
  bad_cells=[]
  for h,row in want.items():
    for k,food in row.items():
      for depth in ('shallow','black'):
        cell=matrix[str(h)][depth][str(k)]
        ate=cell['sc']>0
        if ate!=food or cell['can']!=food or (cell['sc']>0)!=food:bad_cells.append((h,names[k],depth,cell))
  check(not bad_cells,f'[tested] edibility at HUD 6/7, 8/9, 9/10, 11/12, 12/13 matches size, shallow and in the black zone {bad_cells[:4]}')
  # same answer at both depths for every cell
  flipped=[(h,names[k],depth) for h in want for k in want[h] for depth in ('black',) if matrix[str(h)]['shallow'][str(k)]['can']!=matrix[str(h)]['black'][str(k)]['can'] or (matrix[str(h)]['shallow'][str(k)]['sc']>0)!=(matrix[str(h)]['black'][str(k)]['sc']>0)]
  check(not flipped,f'[tested] dive depth does not flip edibility {flipped[:4]}')
  # too-small sails/cargo/tankers are harmless (no bump); not-yet-unlocked boats still bump
  harm=J('''()=>{const touch=(k,hud)=>{__sa.startAs("white","endless");__sa.god=true;__sa.setLevel(hud-1);__sa.depthMark=0;const s=__sa.shark;s.air=false;s.ang=0;s.spd=0;s.vx=0;s.vy=0;s.g=0;s.y=__sa.SURF+s.L*.1;__sa.surf.forEach(q=>{q.zip=999;q.bump=0});
      __sa.sim(1/30,()=>{s.air=false;s.vx=0;s.vy=0;s.g=0;s.spd=0;s.ang=0;s.y=__sa.SURF+s.L*.1;const q=__sa.surf[0];q.zip=0;q.k=k;q.vx=0;q.x=__sa.mouth()[0]});
      return {sc:__sa.score,bump:__sa.surf[0].bump||0,ret:__sa.surfRetired({k}),st:__sa.state}};
    return {sailEarly:touch(2,6),sailTiny:touch(2,10),cargoTiny:touch(3,13),tankTiny:touch(4,13)}}''')
  check(harm['sailEarly']['sc']==0 and harm['sailEarly']['bump']>0 and harm['sailEarly']['ret'] is False,f'[tested] HUD 6 sail boat is not food yet and still bumps {harm["sailEarly"]}')
  check(harm['sailTiny']['sc']==0 and harm['sailTiny']['bump']==0 and harm['sailTiny']['ret'] is True and harm['sailTiny']['st']=='play',f'[tested] HUD 10 sail boat is too small: not food, no bump {harm["sailTiny"]}')
  check(harm['cargoTiny']['sc']==0 and harm['cargoTiny']['bump']==0 and harm['tankTiny']['bump']==0 and harm['cargoTiny']['st']=='play',f'[tested] HUD 13 cargo and tanker are too small and harmless {harm["cargoTiny"]} {harm["tankTiny"]}')
  # --- black-zone food turns on at HUD 12, and is still there at 20 and 40 ---
  def census(hud):
    return J('''hud=>{__sa.startAs("white","endless");__sa.god=true;__sa.setLevel(hud-1);const s=__sa.shark;s.air=false;s.ang=0;s.spd=0;const y=__sa.SURF+(__sa.BED-__sa.SURF)*(__sa.ZONE.CARGO+1.2);s.y=y;s.x=innerWidth/2;__sa.camX=s.x-innerWidth/2;__sa.camY=Math.max(0,s.y-innerHeight/2);__sa.updTiles(true,true);
      const ty=Math.floor(s.y/innerHeight),T={tx:Math.floor(s.x/innerWidth),ty};let n=0,deep=0,bad=0,edible=0,minQ=99,maxQ=0;const depths=[];
      for(let r=0;r<8;r++)for(const f of __sa.fish){__sa.spawnFish(f,false,T);n++;const q=f.s/__sa.bite();if(depths.length<3)depths.push(+__sa.depthRaw(f.y).toFixed(2));
        if(!f.off&&!f.tiny&&f.kind!=="plankton"&&f.kind!=="star"&&q<0.87&&q>0.2)edible++;
        if(f.deepFood){deep++;if(q<minQ)minQ=q;if(q>maxQ)maxQ=q;if(!(q>=0.4-1e-6&&q<=0.84+1e-6)||f.tiny||f.kind!=="glow")bad++}}
      return {n,deep,bad,edible,minQ,maxQ,depths,lvl:s.lvl+1,on:s.lvl>=__sa.SURFACE.DEEP_LVL}}''',hud)
  c11,c12=census(11),census(12)
  check(c11['on'] is False and c11['deep']==0,f'[tested] HUD 11: black-zone food rule is off (no deepFood spawns) {c11}')
  check(c12['on'] is True and c12['deep']>=c12['n']*0.65 and c12['bad']==0 and c12['minQ']>=0.4-1e-6 and c12['maxQ']<=0.84+1e-6,f'[tested] HUD 12: most black-zone spawns are edible deep-dark fish at 0.4-0.84 of bite {c12}')
  # world shrink: an old fish gets smaller, a new one is sized to the shark
  shrink=J('''()=>{__sa.startAs("white","endless");__sa.god=true;__sa.setLevel(9);const f=__sa.fish[0];__sa.setCreature(f,__sa.bite()*0.7,"fish");f.off=false;const s0=f.s,k0=__sa.worldK,b0=__sa.bite();__sa.setLevel(39);const s1=f.s,k1=__sa.worldK,b1=__sa.bite();
    const s=__sa.shark,y=__sa.SURF+(__sa.BED-__sa.SURF)*(__sa.ZONE.CARGO+1.2);s.y=y;s.x=innerWidth/2;const T={tx:0,ty:Math.floor(y/innerHeight)};let neu=0,nq=0;for(let i=0;i<80&&!neu;i++){const g=__sa.fish[1];__sa.spawnFish(g,false,T);if(g.deepFood){neu=g.s;nq=g.s/__sa.bite()}}
    const fin=[s0,s1,k0,k1,b0,b1,neu].every(Number.isFinite);return {s0,s1,k0,k1,b0,b1,neu,nq,fin}}''')
  check(shrink['fin'] and shrink['k1']<shrink['k0']*0.2 and shrink['s1']<shrink['s0']*0.2 and shrink['neu']>shrink['s1']*5 and 0.4-1e-6<=shrink['nq']<=0.84+1e-6 and abs(shrink['b1']/shrink['b0']-1)<0.05,f'[tested] growing from HUD 10 to 40 shrinks the old fish with the world; a new black-zone fish is larger and sized to the bite {shrink}')
  # depth metre keeps climbing at a huge size; the coloured fraction still matches b57 inside the black edge
  dep=J('''()=>{const at=(hud,d)=>{__sa.setLevel(hud-1);const s=__sa.shark;s.y=__sa.SURF+(__sa.BED-__sa.SURF)*d;s.air=false;return {m:__sa.depthMetres(),fr:__sa.depthFrac(d),raw:__sa.depthRaw(s.y)}};
    return {a:at(1,1),b:at(1,3.2),c:at(40,1),d:at(40,3.2),e:at(40,__sa.ZONE.CARGO+6),full:__sa.depthFrac(__sa.ZONE.CARGO)}}''')
  check(dep['b']['m']>dep['a']['m'] and dep['d']['m']>dep['c']['m'] and dep['e']['m']>dep['d']['m'] and abs(dep['a']['fr']-dep['c']['fr'])<1e-9 and dep['full']==1 and dep['e']['m']>dep['d']['m'],f'[tested] the depth metre keeps climbing at HUD 40, including past the black edge, and the track is unchanged inside it {dep}')
  # high size: food is there, a bite fills the bar, a few seconds of swimming stays finite, fps holds
  def live(hud):
    cen=census(hud)
    bite=J('''hud=>{__sa.setLevel(hud-1);const s=__sa.shark;s.meter=0;s.air=false;s.ang=0;s.spd=0;s.vx=0;s.vy=0;const y=__sa.SURF+(__sa.BED-__sa.SURF)*(__sa.ZONE.CARGO+1.2);s.y=y;const f=__sa.fish[0];__sa.setCreature(f,__sa.bite()*0.6,"glow");f.tiny=false;f.off=false;f.vx=0;f.vy=0;const m0=s.meter,l0=s.lvl,sc=__sa.score;
      for(let i=0;i<12;i++)__sa.sim(1/60,()=>{s.air=false;s.ang=0;s.spd=0;s.vx=0;s.vy=0;s.y=y;const [mx,my]=__sa.mouth();f.x=mx;f.y=my;f.off=false;f.tiny=false;f.vx=0});
      const fin=[s.x,s.y,s.spd,s.L,s.meter,__sa.worldK,__sa.need(s.lvl)].every(Number.isFinite)&&__sa.fish.every(q=>Number.isFinite(q.s)&&Number.isFinite(q.x)&&Number.isFinite(q.y));
      __sa.sim(2.5,()=>{s.ang=0.4;s.air=false;Object.assign(__sa.touch,{on:true,dir:0.4,drive:1,lastMove:performance.now()+9e9})});
      const fin2=[s.x,s.y,s.spd,s.L,s.meter,__sa.worldK].every(Number.isFinite);return {grew:s.meter>m0+0.2||s.lvl>l0,sc:__sa.score>sc,st:__sa.state,fin:fin&&fin2,lvl:s.lvl}}''',hud)
    J('__sa.perf.reset()');pg.wait_for_timeout(1200)
    fps=J('({frames:__sa.perf.frames,dt:__sa.perf.dtSum,js:__sa.perf.js})')
    rate=(fps['frames']/fps['dt']) if fps and fps['dt'] else 0
    return cen,bite,fps,rate
  for hud in (20,40):
    cen,bite,fps,rate=live(hud)
    check(cen['deep']>=cen['n']*0.6 and cen['bad']==0 and cen['edible']>=8,f'[tested] HUD {hud}: black zone still spawns edible fish ({cen["deep"]}/{cen["n"]} sized, edible count {cen["edible"]})')
    check(bite['grew'] and bite['sc'] and bite['st']=='play' and bite['fin'],f'[tested] HUD {hud}: a bite fills the bar, 2.5s of swimming stays in play, numbers stay finite {bite}')
    check(rate>=12 and fps['frames']>=15,f'[tested] HUD {hud}: frame rate holds ({rate:.1f} fps over {fps["frames"]} frames)')
  check(not errs,f'[tested] no page errors {errs[:3]}')
  b.close()
finally: srv.terminate()
print(f'{ok} passed, {bad} failed');sys.exit(1 if bad else 0)
