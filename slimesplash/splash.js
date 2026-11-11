/* SlimeTrail shared logo splash v1 (t2569u), generalised from Secret Adventures splash.js (t2386u).
   First screen on every launch: waits for a tap; the tap plays the Neon Glow sound (the first gesture that unlocks phone
   audio), the logo stays HOLD ms, fades, and then the game's own start runs. Local files only, no network hosts, no ads.

   Use (no inline script needed, so it works under strict CSP):
     <link rel="stylesheet" href="slimesplash/splash.css?v=1">
     <script src="slimesplash/splash.js?v=1" data-sound="1" data-keep-above="#updateBanner,#upd"></script>   (first thing in <body>)
   Script-tag options:  data-base="slimesplash/" (folder of the logo + sound; set it when the page may load scripts from blob URLs);
     data-sound="0" = silent logo (apps / Bible Quest); data-hold="2000"; data-fade="450";
     data-z="2147483000"; data-keep-above="CSS selectors" = update banners/prompts that must stay above and tappable.
   Game hook: SlimeSplash.whenDone(fn)  runs fn once when the logo starts to fade (at once if it already has).
              window event "slimesplash:done" fires at the same moment.  SlimeSplash.open() is true until fully gone.
   Update banners: every element matching keep-above (plus the built-in list below) is lifted above the splash
   while it is open (inline z-index, restored after), and taps/keys inside them pass straight through. */
(function(){"use strict";
if(window.SlimeSplash)return;
var me=document.currentScript||document.querySelector('script[src*="splash.js"]');
var ds=(me&&me.dataset)||{};
var base=ds.base||((me&&me.getAttribute("src")||"slimesplash/splash.js").replace(/splash\.js(\?.*)?$/,""));
if(/^(blob|data):/.test(base))base="slimesplash/";
var SOUND=ds.sound!=="0"&&ds.sound!=="false";
var HOLD_MS=+ds.hold||2000,FADE_MS=+ds.fade||450,Z=+ds.z||2147483000;
var KEEP=["[data-update-banner]",".update-banner","#updateBanner","#update-banner"].concat((ds.keepAbove||"").split(",").map(function(s){return s.trim()}).filter(Boolean)).join(",");
var st="wait",tapAt=0,fadeAt=0,waiters=[],lifted=[],sp,snd=null,mo=null,iv=0;
function build(){
 sp=document.createElement("div");sp.id="slsplash";sp.setAttribute("role","button");sp.tabIndex=0;
 sp.setAttribute("aria-label","SlimeTrail Production. Tap to start");sp.style.zIndex=String(Z);
 var img=document.createElement("img");img.src=base+"logo3-neon-chosen-v1.jpg";img.alt="SlimeTrail Production";img.draggable=false;sp.appendChild(img);
 var t=document.createElement("div");t.className="slsplash-tap";t.textContent="Tap to start";sp.appendChild(t);
 if(SOUND){snd=document.createElement("audio");snd.preload="auto";snd.src=base+"logo-sound-3-neon-glow.mp3";sp.appendChild(snd);}
 (document.body||document.documentElement).appendChild(sp);
 document.documentElement.classList.add("slsplash-open");
 lift();mo=new MutationObserver(lift);mo.observe(document.documentElement,{childList:true,subtree:true,attributes:true,attributeFilter:["class","hidden","style"]});
 iv=setInterval(lift,250);
}
function lift(){if(st==="done")return;var els;try{els=document.querySelectorAll(KEEP);}catch(e){return;}
 for(var i=0;i<els.length;i++){var el=els[i];if(el===sp||sp.contains(el))continue;
  if(el.style.getPropertyValue("z-index")!==String(Z+1)||el.style.getPropertyPriority("z-index")!=="important"){
   if(!lifted.some(function(o){return o.el===el;}))lifted.push({el:el,z:el.style.getPropertyValue("z-index"),p:el.style.getPropertyPriority("z-index"),pos:el.style.position});
   if(getComputedStyle(el).position==="static")el.style.position="relative";
   el.style.setProperty("z-index",String(Z+1),"important");}}}
function unlift(){for(var i=0;i<lifted.length;i++){var o=lifted[i];if(!o.el||!o.el.style)continue;
 if(o.z)o.el.style.setProperty("z-index",o.z,o.p);else o.el.style.removeProperty("z-index");o.el.style.position=o.pos||"";}lifted=[];}
function inKeep(t){try{return !!(t&&t.closest&&t.closest(KEEP));}catch(e){return false;}}
function go(){if(st!=="wait")return;st="show";tapAt=performance.now();sp.classList.add("shown");
 if(snd){try{snd.currentTime=0;var p=snd.play();if(p&&p.catch)p.catch(function(){});}catch(e){}}
 setTimeout(fade,HOLD_MS);}
function fade(){if(st!=="show")return;st="fade";fadeAt=performance.now();sp.classList.add("out");
 var w=waiters;waiters=[];for(var i=0;i<w.length;i++){try{w[i]();}catch(e){setTimeout(function(){throw e;});}}
 try{dispatchEvent(new Event("slimesplash:done"));}catch(e){}
 setTimeout(end,FADE_MS);}
function end(){st="done";sp.hidden=true;document.documentElement.classList.remove("slsplash-open");clearInterval(iv);if(mo)mo.disconnect();unlift();}
// Window capture runs before any game listener (even document-capture ones), so a splash tap never also starts the game.
function guard(e){if(st==="done"||st==="fade")return;if(inKeep(e.target))return;
 e.stopImmediatePropagation();if(e.cancelable&&e.type!=="pointerdown")e.preventDefault();
 if((e.type==="pointerup"||e.type==="click"||e.type==="touchend")&&st==="wait")go();}
["pointerdown","pointerup","pointermove","pointercancel","mousedown","mouseup","click","dblclick","touchstart","touchend","touchmove","contextmenu"].forEach(function(n){addEventListener(n,guard,{capture:true,passive:false});});
addEventListener("keydown",function(e){if(st==="done"||st==="fade"||inKeep(e.target))return;e.preventDefault();e.stopImmediatePropagation();if(e.key==="Enter"||e.key===" ")go();},true);
addEventListener("keyup",function(e){if(st==="done"||st==="fade"||inKeep(e.target))return;e.stopImmediatePropagation();},true);
window.SlimeSplash={open:function(){return st!=="done";},state:function(){return st;},tappedAt:function(){return tapAt;},fadedAt:function(){return fadeAt;},
 audio:function(){return snd;},sound:SOUND,HOLD_MS:HOLD_MS,FADE_MS:FADE_MS,
 whenDone:function(fn){if(st==="fade"||st==="done")fn();else waiters.push(fn);}};
if(document.body)build();else document.addEventListener("DOMContentLoaded",build);
})();
