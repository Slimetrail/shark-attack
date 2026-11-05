# b57 (Jeremy via Eve, Nov 5). Pretend phone (Chromium), never a real phone.
# Run: python3 tests/test_b57.py   (port SA_PORT57, default 8963)
#
# Each line is tagged:
#   [tested]  the browser ran the game (update loop, spawns, or canvas pixels)
#   [read]    a live constant or predicate was read; the pixels were not the proof
import subprocess,sys,os,time,json
from playwright.sync_api import sync_playwright
ROOT=os.environ.get('SA_ROOT') or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PORT=int(os.environ.get('SA_PORT57','8963'));URL=f'http://127.0.0.1:{PORT}/'
srv=subprocess.Popen([sys.executable,'-m','http.server',str(PORT),'--bind','127.0.0.1'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(.8)
ok=bad=0
def check(c,m):
  global ok,bad
  print(('PASS ' if c else 'FAIL ')+m);ok+=bool(c);bad+=not c
rd=lambda n:open(os.path.join(ROOT,n)).read()
check(json.loads(rd('version.json'))['build']=='57' and 'content="57"' in rd('index.html') and 'game.js?v=57' in rd('index.html') and 'game.js?v=57' in rd('sw.js') and 'PREFIX="sharkattack-v"' in rd('sw.js'),'[read] build 57 in version.json, index.html, sw.js (cache name is sharkattack-v + build)')
try:
 with sync_playwright() as p:
  b=p.chromium.launch()
  cx=b.new_context(viewport={'width':844,'height':390},is_mobile=True,has_touch=True,bypass_csp=True,service_workers='block');pg=cx.new_page();errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
  pg.goto(URL);pg.wait_for_function('!!window.__sa',timeout=30000);pg.wait_for_timeout(300);pg.touchscreen.tap(422,195);pg.wait_for_timeout(250)
  J=lambda s,a=None:pg.evaluate(s,a)
  J('__sa.startAs("white","endless");__sa.god=true')
  # --- 1. sail / cargo rewards sit on the existing curve ---
  G=J('''()=>{const S=__sa.SURFERS,n=l=>__sa.need(l),fish=__sa.growOf({kind:"fish",s:__sa.bite()*.6});
    return {pts:S.map(s=>s.pts),grow:S.map(s=>s.grow),surfer:__sa.GROW.SURFER,fish,
      sailAt:S[2].grow/n(6),cargoAt:S[3].grow/n(8),surferAt:__sa.GROW.SURFER/n(4),
      n6:n(6),n8:n(8),inf:__sa.allowedD(0)===Infinity&&__sa.allowedD(9)===Infinity,ml:__sa.MAX_LEVEL}}''')
  check(G['pts']==[15,20,25,40,55] and G['grow']==[2,2,3,4,5],f'[read] points 15/20/25/40/55 and growth 2/2/3/4/5 (sail was 40/5, cargo was 100/10) {G["pts"]} {G["grow"]}')
  check(G['sailAt']<0.35 and G['cargoAt']<0.35 and abs(G['sailAt']-G['surferAt'])<0.05,f'[read] at unlock, sail fills {G["sailAt"]:.0%} of the bar and cargo {G["cargoAt"]:.0%} (surfer-at-its-unlock is {G["surferAt"]:.0%}; old sail ~44%, old cargo ~56%)')
  check(G['grow'][2]>G['fish'] and G['grow'][2]<G['fish']*2 and G['grow'][3]>G['grow'][2],f'[read] sail growth {G["grow"][2]} is above one 0.6-bite fish ({G["fish"]:.2f}) and below two; cargo is the next step')
  check(G['inf'] and G['ml']==9,f'[read] allowedD stays Infinity and the HUD size cap stays 10 (MAX_LEVEL {G["ml"]})')
  # real bites: score matches the new numbers, and growth actually moves the meter
  r=J('''()=>{const out={};const bite=(k)=>{__sa.startAs("white","endless");__sa.god=true;__sa.setLevel(8);__sa.depthMark=0;const s=__sa.shark;s.air=false;s.ang=0;s.spd=0;s.y=__sa.SURF+s.L*.1;__sa.surf.forEach(q=>q.zip=999);
    const m0=s.meter;[...Array(8)].forEach(()=>{const [mx]=__sa.mouth();__sa.placeSurfer(0,mx,k);__sa.surf[0].vx=0;__sa.sim(1/30,()=>{s.air=false;s.ang=0;s.spd=0;s.y=__sa.SURF+s.L*.1;__sa.surf[0].x=__sa.mouth()[0];__sa.surf[0].vx=0})});
    return {sc:__sa.score,g:s.meter-m0,ate:__sa.surfEaten[k]}};out.sail=bite(2);out.cargo=bite(3);return out}''')
  check(r and r['sail']['ate']>=1 and r['sail']['sc']==r['sail']['ate']*25 and r['sail']['g']>0,f'[tested] eating sail boats scores 25 each and fills the meter by growth 3 {r and r["sail"]}')
  check(r and r['cargo']['ate']>=1 and r['cargo']['sc']==r['cargo']['ate']*40,f'[tested] eating cargo ships scores 40 each (was 100) {r and r["cargo"]}')
  # --- 2. sail shrink, surfer cutoff, tiny sails, tankers, all one depth ---
  Z=J('''()=>{__sa.setLevel(6);__sa.depthMark=0;const s=__sa.shark,span=d=>{s.y=__sa.SURF+(__sa.BED-__sa.SURF)*d;s.spd=0;return {sail:__sa.surfDrawK({k:2})*__sa.SAIL_SPAN,surfer:__sa.surfDrawK({k:0})*__sa.SURFER_SPAN,d:__sa.diveD()}};
    const a=span(0),b=span(__sa.ZONE.SURF*.5),c=span(__sa.ZONE.SURF),e=span(__sa.ZONE.SURF+1.2);
    return {a,b,c,e,zs:__sa.ZONE.SURF,zc:__sa.ZONE.CARGO,k:__sa.SAIL_SHRINK}}''')
  check(Z['a']['sail']>Z['a']['surfer']*3 and Z['a']['sail']>Z['b']['sail']>Z['c']['sail']>=Z['e']['sail']-1e-6,f'[tested] sailboats shrink as depth increases and keep shrinking past the transition {Z["a"]["sail"]:.1f} > {Z["b"]["sail"]:.1f} > {Z["c"]["sail"]:.1f} >= {Z["e"]["sail"]:.1f}')
  check(abs(Z['c']['sail']-Z['c']['surfer'])<1.5,f'[tested] at depth {Z["zs"]} a sailboat is the same length as a surfer ({Z["c"]["sail"]:.2f} vs {Z["c"]["surfer"]:.2f})')
  # rules stick when you come back to the surface (deepest depth reached)
  r=J('''()=>{const eat=(k,mark,air)=>{__sa.startAs("white","endless");__sa.god=true;__sa.setLevel(8);__sa.depthMark=mark;const s=__sa.shark;s.ang=0;s.spd=0;s.vx=0;s.vy=0;s.g=0;s.air=!!air;s.y=__sa.SURF+(air?-16:s.L*.1);__sa.surf.forEach(q=>q.zip=999);
    const sc=__sa.score;for(let i=0;i<8;i++){__sa.sim(1/60,()=>{s.air=!!air;s.vx=0;s.vy=0;s.g=0;s.spd=0;s.ang=0;s.y=__sa.SURF+(air?-16:s.L*.1);const q=__sa.surf[0];q.zip=0;q.k=k;q.vx=0;q.x=__sa.mouth()[0]},1/60)}
    return {sc:__sa.score-sc,can:__sa.canEatSurf({k:k}),mark:__sa.depthMark}};
    const z=__sa.ZONE;return {surfShallow:eat(0,0,true),surfDeep:eat(0,z.SURF,true),sailDeep:eat(2,z.SURF,false),sailBlack:eat(2,z.CARGO+1,false),cargoMid:eat(3,z.SURF,false),cargoBlack:eat(3,z.CARGO,false),tank:eat(4,z.SURF,false),tankEarly:eat(4,0,false)}}''')
  check(r['surfShallow']['sc']>0 and r['surfShallow']['can'] is True,f'[tested] before the transition a surfer is still edible {r["surfShallow"]}')
  check(r['surfDeep']['sc']==0 and r['surfDeep']['can'] is False,f'[tested] after the transition a surfer is not edible, back at the surface {r["surfDeep"]}')
  check(r['sailDeep']['sc']>0 and r['sailDeep']['can'] is True and r['sailBlack']['sc']>0,f'[tested] a sailboat stays edible at the transition and in the black zone (the surfer cutoff does not block it) {r["sailDeep"]} {r["sailBlack"]}')
  check(r['cargoMid']['sc']>0 and r['cargoBlack']['sc']==0 and r['cargoBlack']['can'] is False,f'[tested] cargo is edible in the sail zone and not edible once the black depth is reached {r["cargoMid"]} {r["cargoBlack"]}')
  check(r['tank']['sc']>0 and r['tankEarly']['sc']==0,f'[tested] an oil tanker is edible from the transition and not before it {r["tank"]} {r["tankEarly"]}')
  mix=J('''()=>{const count=mark=>{__sa.setLevel(8);__sa.depthMark=mark;__sa.shark.y=__sa.SURF+20;const c=[0,0,0,0,0];for(let i=0;i<500;i++){__sa.spawnSurf(__sa.surf[0],false);c[__sa.surf[0].k]++}return c};
    const z=__sa.ZONE;return {before:count(0),at:count(z.SURF),black:count(z.CARGO)}}''')
  check(mix['before'][4]==0 and mix['at'][4]>40 and mix['at'][2]>40,f'[tested] tankers and sailboats both spawn at the surfer cutoff, and tankers do not spawn before it {mix}')
  check(mix['black'][3]==0 and mix['black'][4]>0,f'[tested] in the black zone cargo ships stop spawning and tankers are still there {mix["black"]}')
  # zones line up with the colour stops (the numbers) and the picture actually gets darker smoothly
  L=J('''()=>{const stops=__sa.LIGHT.STOPS,fog=__sa.LIGHT.FOG,z=__sa.ZONE;
    return {surfStop:stops.some(s=>s[0]===z.SURF),cargoStop:stops[stops.length-1][0]===z.CARGO&&stops[stops.length-1][1].toLowerCase()==="#03070f",
      fogSurf:fog.some(s=>s[0]===z.SURF),fogEnd:fog[fog.length-1][0]===z.CARGO,
      meter:__sa.ZONES.map(q=>+q.d.toFixed(4)),meterAt:[0,+(z.SURF/z.CARGO).toFixed(4),+(2.8/z.CARGO).toFixed(4),+(3.8/z.CARGO).toFixed(4)],
      ordered:stops.every((s,i)=>i===0||s[0]>stops[i-1][0])&&stops[0][0]===0}}''')
  check(L['surfStop'] and L['cargoStop'] and L['fogSurf'] and L['fogEnd'] and L['ordered'] and L['meter']==L['meterAt'],f'[read] colour stops, fog and the depth meter use the edibility edges (light until {L["meter"]}, black at cargo) {L}')
  pix=J('''()=>new Promise(res=>{const c=document.getElementById("c"),g=c.getContext("2d"),k=c.width/innerWidth;
    const lum=()=>{const x=Math.round(innerWidth*.12*k),y=Math.round(innerHeight*.55*k),d=g.getImageData(x,y,1,1).data;return .2126*d[0]+.7152*d[1]+.0722*d[2]};
    __sa.startAs("white","endless");__sa.god=true;__sa.setLevel(2);__sa.clearFood();__sa.depthMark=0;__sa.lightProbe=true;for(const f of __sa.fish){f.off=true;f.retry=0}for(const s of __sa.surf)s.zip=999;
    const depths=[.25,.9,1.5,2.2,2.8,3.4,4,4.8],out=[];
    const step=i=>{if(i>=depths.length){__sa.lightProbe=false;res(out);return}const s=__sa.shark;s.y=__sa.SURF+(__sa.BED-__sa.SURF)*depths[i];s.spd=0;s.air=false;__sa.camY=Math.max(0,s.y-innerHeight*.55);for(const f of __sa.fish){f.off=true;f.retry=0}
      requestAnimationFrame(()=>requestAnimationFrame(()=>{out.push({d:depths[i],l:+lum().toFixed(1)});step(i+1)}))};
    step(0)})''')
  lums=[q['l'] for q in pix]
  drops=[round(lums[i]-lums[i+1],1) for i in range(len(lums)-1)]
  check(lums[0]>90 and lums[2]>lums[5]>lums[6] and lums[6]<35 and abs(lums[6]-lums[7])<18,f'[tested] screen luma falls from the light surfer zone through the sail zone to black at depth 4, and stays black past it (no floor cliff) {pix}')
  check(all(d<55 for d in drops) and lums[0]-lums[-1]>70,f'[tested] brightness steps stay smooth (largest drop {max(drops)} luma; samples {lums})')
  # surfer-zone sample is lighter than the sail-zone sample which is lighter than black
  check(pix[2]['l']>pix[4]['l']>pix[6]['l'],f'[tested] edibility bands read as light, then middle, then black (depth 1.5 / 2.8 / 4.0 luma {pix[2]["l"]} / {pix[4]["l"]} / {pix[6]["l"]})')
  # --- 3. sharks keep growing with depth; last sizes need the deep fish ---
  sz=J('''()=>{__sa.startAs("white","endless");__sa.god=true;__sa.setLevel(4);const avg=d=>{const y=__sa.SURF+(__sa.BED-__sa.SURF)*d;let m=0,n=0;for(let i=0;i<700;i++){const f=__sa.fish[i%__sa.fish.length];__sa.spawnFish(f,false,{tx:0,ty:Math.floor(y/innerHeight)});if(f.kind==="shark"&&!f.tiny){m+=f.s;n++}}return n?m/n:0};
    const a=avg(.9),c=avg(2.5),e=avg(5);__sa.setLevel(9);const S=__sa.SURF,D=__sa.BED-S;return {a,c,e,k:__sa.CREATURES.DEPTH_K,tinyAbove:__sa.goneAt(S+D*1.5),liveBelow:__sa.goneAt(S+D*1.7)===false}}''')
  check(sz['e']>sz['c']>sz['a']*1.15 and sz['k']>0,f'[tested] shark spawn size grows past depth 1 (depth .9 / 2.5 / 5 averages {sz["a"]:.0f} / {sz["c"]:.0f} / {sz["e"]:.0f}, DEPTH_K {sz["k"]})')
  check(sz['tinyAbove'] is True and sz['liveBelow'] is True,f'[tested] at HUD 10, fish above 1.6 are too small to eat and fish below 1.6 are not {sz}')
  # endless: swimming past the black water does not hit a floor
  r=J('''()=>{__sa.startAs("white","endless");__sa.god=true;__sa.setLevel(3);const s=__sa.shark,black=__sa.SURF+__sa.ZONE.CARGO*(__sa.BED-__sa.SURF);s.air=false;s.y=black+innerHeight;s.spd=0;s.ang=1.2;let y0=s.y;__sa.sim(1.2,()=>{s.ang=1.2;Object.assign(__sa.touch,{on:true,dir:1.4,drive:1,lastMove:performance.now()+9e9})});return {y0,y1:s.y,st:__sa.state,deeper:s.y>y0+40}}''')
  check(r['st']=='play' and r['deeper'] and r['y1']>r['y0'],f'[tested] past the black water the shark keeps swimming (no floor) {r}')
  # b56 mouth-only kill still holds
  r=J('''()=>{const scene=(mouth)=>{__sa.startAs("white","endless");__sa.god=false;__sa.setLevel(4);__sa.sim(2.2);__sa.clearFood();const s=__sa.shark;s.y=__sa.SURF+(__sa.BED-__sa.SURF)*1.2;s.x=__sa.camX+innerWidth/2;s.ang=0;s.spd=0;__sa.touch.on=false;for(let k=0;k<40;k++){s.spd=0;__sa.sim(1/60)}__sa.clearFood();s.x=__sa.camX+innerWidth/2;
    const f=__sa.fish[0];__sa.setCreature(f,__sa.bite()*2,"shark");f.off=false;f.tiny=false;f.fade=0;f.rest=0;f.vx=mouth?-80:40;const fs=f.s;let X,Y;if(mouth){f.x=0;f.y=0;const mp=__sa.mouthPt(f);X=s.x-mp[0];Y=s.y-mp[1]}else{X=s.x;Y=s.y-(s.L*.32+fs*.9)*.85}
    const x0=s.x,y0=s.y;for(let k=0;k<40&&__sa.state==="play";k++){s.x=x0;s.y=y0;s.spd=0;s.ang=0;f.x=X;f.y=Y;f.vx=mouth?-80:40;f.vy=0;f.rest=0;__sa.sim(1/60)}return __sa.endReason};
    return {mouth:scene(true),top:scene(false)}}''')
  check(r['mouth']=='eaten' and r['top']!='eaten',f'[tested] b56 still holds: the mouth kills, the top of the body does not {r}')
  check(not errs,f'[tested] no page errors {errs[:3]}')
  b.close()
finally: srv.terminate()
print(f'{ok} passed, {bad} failed');sys.exit(1 if bad else 0)
