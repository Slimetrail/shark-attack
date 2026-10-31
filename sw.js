// Offline cache + quiet updates. The build id lives in version.json, which is NEVER cached (always fetched with no-store).
// Each build gets its own cache PREFIX+build. A new build is downloaded in the background, written only when EVERY file
// fetched OK, and marked "pending". The switch happens on the next launch (navigation), never mid-play; old caches are then deleted.
const PREFIX="sharkattack-v",META=PREFIX+"meta";
const SHELL=["./","index.html","game.js?v=46","manifest.webmanifest","icons/icon-192.png","icons/icon-512.png","icons/maskable-512.png","art/title-art.webp","audio/intro-scary.ogg","audio/play-swim-piano.ogg"];
const VERSION_URL="version.json";
async function getMeta(){try{const c=await caches.open(META),r=await c.match("meta");return r?await r.json():{}}catch(e){return {}}}
async function setMeta(m){const c=await caches.open(META);await c.put("meta",new Response(JSON.stringify(m),{headers:{"content-type":"application/json"}}))}
async function remoteBuild(){const ac=new AbortController(),t=setTimeout(()=>ac.abort(),8000);let r;try{r=await fetch(VERSION_URL,{cache:"no-store",signal:ac.signal})}finally{clearTimeout(t)}if(!r.ok)throw new Error("version "+r.status);const j=await r.json();if(!j||!j.build)throw new Error("no build");return String(j.build)}
async function complete(build){if(!build)return false;if(!(await caches.has(PREFIX+build)))return false;const c=await caches.open(PREFIX+build);for(const u of SHELL)if(!(await c.match(u,{ignoreSearch:true})))return false;return true}
// all-or-nothing download: nothing is written unless every file came back 200
async function download(build){const res=await Promise.all(SHELL.map(u=>fetch(new Request(u,{cache:"reload"})).then(r=>{if(!r.ok||r.status!==200)throw new Error(u+" "+r.status);return r})));
 await caches.delete(PREFIX+build);const c=await caches.open(PREFIX+build);for(let i=0;i<SHELL.length;i++)await c.put(SHELL[i],res[i]);
 if(!(await complete(build))){await caches.delete(PREFIX+build);throw new Error("incomplete")}}
async function cleanup(m){const keep=new Set([META,PREFIX+m.current,PREFIX+m.pending]);for(const k of await caches.keys())if(k.startsWith(PREFIX)&&!keep.has(k))await caches.delete(k)}
let checking=null;
function checkUpdate(){if(checking)return checking;checking=(async()=>{try{const b=await remoteBuild(),m=await getMeta();
  if(b===m.current||b===m.pending)return;await download(b);const m2=await getMeta();m2.pending=b;await setMeta(m2);tell({type:"pending",build:b})}catch(e){/* silent: offline or broken update keeps the working build */try{const m=await getMeta();m.lastErr=String(e).slice(0,120);await setMeta(m)}catch(_){}}finally{checking=null}})();return checking}
async function switchIfPending(){const m=await getMeta();if(m.pending&&m.pending!==m.current&&await complete(m.pending)){m.current=m.pending;delete m.pending;await setMeta(m);await cleanup(m)}else if(m.pending&&!(await complete(m.pending))){delete m.pending;await setMeta(m)}return m}
self.addEventListener("install",e=>{e.waitUntil((async()=>{const m=await getMeta();if(!(await complete(m.current))){const b=await remoteBuild();await download(b);m.current=b;delete m.pending;await setMeta(m)}await self.skipWaiting()})())});
self.addEventListener("activate",e=>{e.waitUntil((async()=>{const m=await getMeta();if(m.current)await cleanup(m);await self.clients.claim()})())});
// v10 b42 update button: the page asks "status" (is a downloaded build waiting?), "check" (look now) and "apply" (switch now, only from the title screen).
async function tell(msg){for(const c of await self.clients.matchAll({includeUncontrolled:true}))c.postMessage(msg)}
async function status(){const m=await getMeta();const ok=!!(m.pending&&m.pending!==m.current&&await complete(m.pending));return {type:"status",current:m.current||null,pending:ok?m.pending:null}}
self.addEventListener("message",e=>{const d=e.data,src=e.source,reply=async()=>{const st=await status();if(src)src.postMessage(st);else await tell(st)};
 if(d==="check")e.waitUntil(checkUpdate().then(reply));
 else if(d==="status")e.waitUntil(reply());
 else if(d==="apply")e.waitUntil(switchIfPending().then(m=>{const r={type:"applied",current:m.current||null};if(src)src.postMessage(r);else return tell(r)}))});
self.addEventListener("fetch",e=>{const r=e.request,u=new URL(r.url);if(r.method!=="GET"||u.origin!==location.origin)return;
 if(u.pathname.endsWith("/"+VERSION_URL)){e.respondWith(fetch(r,{cache:"no-store"}).catch(()=>new Response("{}",{status:503})));return}
 e.respondWith((async()=>{const m=r.mode==="navigate"?await switchIfPending():await getMeta();
  if(m.current){const c=await caches.open(PREFIX+m.current);let hit=await c.match(r,{ignoreSearch:true});if(!hit&&r.mode==="navigate")hit=await c.match("index.html");if(hit)return hit}
  return fetch(r)})());
 if(r.mode==="navigate")e.waitUntil(checkUpdate())});
