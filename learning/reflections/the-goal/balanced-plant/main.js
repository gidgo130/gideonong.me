// main.js — The Balanced Plant Theorem (Reflections · The Goal). Ported from the approved
// explainer: the DATA arrays are exact Markov-chain solutions and the seeded random numbers are
// unchanged. Charts use the reflection series tokens --s1..--s4 (reflections.css), never
// --fit / --fix, and every line in a shared chart has its own dash pattern or marker. Math on the
// page is rendered by the self-hosted KaTeX (index.html); this file only draws and redraws.
(function(){
"use strict";
const $=id=>document.getElementById(id);
/* Line forms for lines that share a chart (at most three, told apart by shape alone):
   solid, "dashed" (10 px dashes, 6 px gaps) and "dotted" (round 3.25 px dots every 6 px). A fourth
   series gets a second cue instead: hollow square markers plus a direct label at the line's end.
   The legend classes .dash / .dotted / .sq in reflections.css use the same geometry. */
const DASH={2:undefined,3:"dashed",4:"dotted",5:undefined};const BOWL_DASH={0:undefined,1:"dashed",3:"dotted"};
const DATA={"bufsweep":{"2":[0.66667,0.75,0.8,0.83333,0.85714,0.875,0.88889,0.9,0.90909],"3":[0.5641,0.67047,0.73402,0.77671,0.80749,0.83076,0.84899,0.86367,0.87573],"4":[0.51478,0.63115,0.70071,0.74771,0.78178,0.80766,0.82803,0.84447,0.85804],"5":[0.4858,0.60758,0.68049,0.72995,0.76593,0.79337,0.815]},
"bowl":{"0":[0.56709,0.56718,0.56713,0.56695,0.56664,0.5662,0.56563,0.56493,0.5641,0.56315,0.56208,0.56089,0.55959,0.55817,0.55664,0.555,0.55326],"1":[0.6722,0.67301,0.67352,0.67375,0.67368,0.67331,0.67266,0.67171,0.67047,0.66894,0.66714,0.66506,0.66271,0.66011,0.65726,0.65417,0.65085],"3":[0.77105,0.77379,0.77601,0.77767,0.77874,0.77919,0.77901,0.77819,0.77671,0.77459,0.77182,0.76843,0.76443,0.75986,0.75474,0.74911,0.74301]},
"bowlx":[0.8,0.825,0.85,0.875,0.9,0.925,0.95,0.975,1,1.025,1.05,1.075,1.1,1.125,1.15,1.175,1.2]};

/* ---------- tiny SVG plotter ---------- */
function nice(lo,hi,n){const span=hi-lo||1;const raw=span/n;const p=Math.pow(10,Math.floor(Math.log10(raw)));const f=raw/p;const st=(f<1.5?1:f<3?2:f<7?5:10)*p;const out=[];for(let v=Math.ceil(lo/st-1e-9)*st;v<=hi+1e-9;v+=st)out.push(+v.toFixed(10));return out;}
function fmt(v){const a=Math.abs(v);if(a>=1000)return Math.round(v).toLocaleString("en-US");if(a>=10||v===0)return String(Math.round(v*10)/10);return String(+v.toFixed(2));}
/* Chart size. At desktop a chart keeps the viewBox it was authored with (640 wide). On narrow
   screens (viewport under 820 px, where the page is one column) the viewBox follows the
   container's width instead, at least 300 user units, so 13-unit text renders at about 13 px
   rather than 6; the height keeps the authored aspect ratio, never under 220. The authored
   viewBox is remembered in data-vb so a resize can go either way. */
function chartSize(svg){
  if(!svg.dataset.vb)svg.dataset.vb=svg.getAttribute("viewBox");
  const [,,w0,h0]=svg.dataset.vb.split(/\s+/).map(Number);
  const cw=svg.getBoundingClientRect().width||svg.parentNode.clientWidth;
  if(!cw)return{w:w0,h:h0};
  /* One user unit = one CSS pixel at every width, so 13-unit text is 13 px on screen whether the
     chart is a 309 px phone column or a 896 px desktop figure. Height keeps the authored ratio,
     between 220 and 1.25× the authored height. */
  const w=Math.max(Math.round(cw),300);
  return{w,h:Math.min(Math.max(Math.round(h0*w/w0),220),Math.round(h0*1.25))};
}
function plot(svg,o){
  svg._plot=o;   /* kept so a resize can redraw the same data at the new size */
  const VB=chartSize(svg),W=VB.w,H=VB.h,m={l:58,r:18,t:14,b:46};
  svg.setAttribute("viewBox",`0 0 ${W} ${H}`);
  /* k converts screen pixels to user units, so strokes, dashes and markers keep their size on
     screen whatever the viewBox scale (the SVG is width:100%, so its rendered width is known). */
  const k=W/(svg.getBoundingClientRect().width||W),px=v=>+(v*k).toFixed(2);
  /* Axis titles: 13 px, or 12 px when that does not fit, and two lines at 12 px when even that
     is too long (never below 12 px on screen). The bottom or left margin grows for a two-line title. */
  const title=(txt,room)=>{txt=txt||"";const u=Math.max(1,k),est=f=>0.62*f*u*txt.length;
    if(est(13)<=room)return{fs:13*u,lines:[txt]};if(est(12)<=room)return{fs:12*u,lines:[txt]};
    const w=txt.split(" "),mid=Math.ceil(w.length/2);return{fs:12*u,lines:[w.slice(0,mid).join(" "),w.slice(mid).join(" ")]};};
  const lineH=f=>Math.round(f*1.15);
  const xT=title(o.xl,W-m.l-m.r),yT=title(o.yl,H-m.t-m.b);
  if(xT.lines.length>1)m.b+=lineH(xT.fs);
  if(yT.lines.length>1)m.l+=lineH(yT.fs);
  /* Direct labels (series with `label`) go in a right margin reserved for them, at each line's
     final y. If that margin would leave less than 200 px of plot, the labels are dropped and the
     legend carries the names; dash forms and markers stay. */
  const fsL=13*Math.max(1,k),labeled=(o.series||[]).filter(se=>se.label&&!se.dots);
  let useLabels=labeled.length>0;
  if(useLabels){const mr=18+Math.ceil(Math.max(...labeled.map(se=>0.62*fsL*se.label.length)))+8;if(W-m.l-mr<200)useLabels=false;else m.r=mr;}
  const sx=x=>m.l+(x-o.x[0])/(o.x[1]-o.x[0])*(W-m.l-m.r);
  const sy=y=>H-m.b-(y-o.y[0])/(o.y[1]-o.y[0])*(H-m.t-m.b);
  let s=`<rect class="plot-bg" x="${m.l}" y="${m.t}" width="${W-m.l-m.r}" height="${H-m.t-m.b}"/>`;
  const xt=o.xticks||nice(o.x[0],o.x[1],6), yt=o.yticks||nice(o.y[0],o.y[1],5);
  yt.forEach(v=>{const y=sy(v);s+=`<line class="gridl" x1="${m.l}" x2="${W-m.r}" y1="${y}" y2="${y}"/><text x="${m.l-8}" y="${y+4}" text-anchor="end">${(o.yf||fmt)(v)}</text>`;});
  xt.forEach(v=>{const x=sx(v);s+=`<text x="${x}" y="${H-m.b+18}" text-anchor="middle">${(o.xf||fmt)(v)}</text>`;});
  s+=`<line class="axis" x1="${m.l}" x2="${W-m.r}" y1="${H-m.b}" y2="${H-m.b}"/><line class="axis" x1="${m.l}" x2="${m.l}" y1="${m.t}" y2="${H-m.b}"/>`;
  s+=`<text x="${(m.l+W-m.r)/2}" y="${H-8-(xT.lines.length-1)*lineH(xT.fs)}" text-anchor="middle" style="font-size:${xT.fs.toFixed(1)}px">`+xT.lines.map((l,i)=>`<tspan x="${(m.l+W-m.r)/2}" dy="${i?lineH(xT.fs):0}">${l}</tspan>`).join("")+`</text>`;
  s+=`<text transform="translate(14 ${(m.t+H-m.b)/2}) rotate(-90)" text-anchor="middle" style="font-size:${yT.fs.toFixed(1)}px">`+yT.lines.map((l,i)=>`<tspan x="0" dy="${i?lineH(yT.fs):0}">${l}</tspan>`).join("")+`</text>`;
  s+=`<clipPath id="${svg.id}cp"><rect x="${m.l}" y="${m.t-2}" width="${W-m.l-m.r}" height="${H-m.t-m.b+4}"/></clipPath><g clip-path="url(#${svg.id}cp)">`;
  (o.areas||[]).forEach(a=>{s+=`<path d="M${a.pts.map(p=>sx(p[0])+","+sy(p[1])).join(" L")} Z" style="fill:${a.c};opacity:${a.op||.25}"/>`;});
  const labels=[];
  (o.series||[]).forEach(se=>{
    if(se.dots){const r=px(se.r||4);se.pts.forEach(p=>{if(!isFinite(p[1]))return;const cx=sx(p[0]),cy=sy(p[1]);
      if(se.marker==="square")s+=`<rect x="${(cx-r).toFixed(1)}" y="${(cy-r).toFixed(1)}" width="${(2*r).toFixed(1)}" height="${(2*r).toFixed(1)}" style="fill:var(--paper);stroke:${se.c};stroke-width:${px(2)}"/>`;
      else s+=`<circle cx="${cx}" cy="${cy}" r="${r}" style="${se.ring?`fill:var(--paper);stroke:${se.c};stroke-width:${px(2.5)}`:`fill:${se.c};stroke:var(--paper);stroke-width:${px(1.5)}`}"/>`;});return;}
    let d="",pen=false,last=null;se.pts.forEach(p=>{if(!isFinite(p[1])){pen=false;return;}d+=(pen?" L":" M")+sx(p[0]).toFixed(1)+","+sy(p[1]).toFixed(1);pen=true;last=p;});
    const dotted=se.dash==="dotted",w=px(dotted?3.25:(se.w||2.2));
    const dash=dotted?`stroke-dasharray:0 ${px(6)};`:se.dash?`stroke-dasharray:${px(10)} ${px(6)};`:"";
    s+=`<path d="${d}" style="fill:none;stroke:${se.c};stroke-width:${w};${dash}stroke-linejoin:round;stroke-linecap:round"/>`;
    if(useLabels&&se.label&&last)labels.push({y:sy(last[1]),c:se.c,text:se.label});
  });
  /* Direct labels at line ends, nudged apart so neighbours never overlap. */
  (o.vlines||[]).forEach(v=>{const x=sx(v.x);s+=`<line x1="${x}" x2="${x}" y1="${m.t}" y2="${H-m.b}" style="stroke:${v.c};stroke-width:${px(1.5)};stroke-dasharray:${px(10)} ${px(6)}"/>${v.label?`<text x="${x+5}" y="${m.t+12}">${v.label}</text>`:""}`;});
  s+="</g>";
  /* The direct labels, outside the clip: in the margin at the line's final y, nudged apart to
     1.2× the label height and kept inside the plot's vertical span, so none touches a line, a
     point or another label. */
  /* A label's rendered box is about 1.31× its font size tall, so 1.2× the box is ~1.6× the size. */
  if(labels.length){const gap=fsL*1.6,top=m.t+fsL*0.7,bot=H-m.b-fsL*0.7;labels.sort((p,q)=>p.y-q.y);
    for(let i=0;i<labels.length;i++)labels[i].y=Math.max(labels[i].y,i?labels[i-1].y+gap:top);
    for(let i=labels.length-1;i>=0;i--)labels[i].y=Math.min(labels[i].y,i<labels.length-1?labels[i+1].y-gap:bot);
    labels.forEach(l=>{s+=`<text x="${(W-m.r+8).toFixed(1)}" y="${(l.y+fsL*0.35).toFixed(1)}" style="fill:${l.c};font-size:${fsL}px;font-weight:600">${l.text}</text>`;});}
  svg.innerHTML=s;
}

/* ---------- random numbers ---------- */
let seed=12345;function rnd(){seed=(seed*1664525+1013904223)>>>0;return (seed+0.5)/4294967296;}
function randn(){return Math.sqrt(-2*Math.log(rnd()))*Math.cos(2*Math.PI*rnd());}
function gamma(k){if(k<1){return gamma(k+1)*Math.pow(rnd(),1/k);}const d=k-1/3,c=1/Math.sqrt(9*d);for(;;){let x,v;do{x=randn();v=1+c*x;}while(v<=0);v=v*v*v;const u=rnd();if(u<1-0.0331*x*x*x*x)return d*v;if(Math.log(u)<0.5*x*x+d*(1-v+Math.log(v)))return d*v;}}
function sampler(mean,scv){if(scv<=1e-9)return()=>mean;const k=1/scv;return()=>gamma(k)*mean/k;}

/* ---------- §2 dice game ---------- */
function roll(mode){return mode==="d6"?1+Math.floor(rnd()*6):mode==="narrow"?3+Math.floor(rnd()*2):3.5;}
function game(N,R,mode){const inv=new Array(N).fill(0);let out=0;const cum=[0],wip=[0];
  for(let r=1;r<=R;r++){for(let i=0;i<N;i++){const x=roll(mode);const mv=i===0?x:Math.min(x,inv[i]);if(i>0)inv[i]-=mv;if(i<N-1)inv[i+1]+=mv;else out+=mv;}
    cum.push(out);wip.push(inv.reduce((a,b)=>a+b,0));}
  return{cum,wip};}
function drawDice(res,avg,N,R){
  const t=res.cum.map((_,i)=>i);
  plot($("dc1"),{x:[0,R],y:[0,3.5*R*1.02],xl:"round",yl:"matches out (cumulative)",series:[{pts:t.map(i=>[i,3.5*i]),c:"var(--muted)",dash:true,w:2},{pts:t.map(i=>[i,res.cum[i]]),c:"var(--s1)"}]});
  const series=[{pts:t.map(i=>[i,res.wip[i]]),c:"var(--s2)"}];let cfit=null;
  if(avg){let num=0,den=0;t.forEach(i=>{num+=res.wip[i]*Math.sqrt(i);den+=i;});cfit=num/den;series.push({pts:t.map(i=>[i,cfit*Math.sqrt(i)]),c:"var(--s3)",dash:true,w:2});}
  const ymax=Math.max(4,...res.wip)*1.1;
  plot($("dc2"),{x:[0,R],y:[0,ymax],xl:"round",yl:"matches in bowls (WIP)",series});
  const short=3.5*R-res.cum[R];
  $("dRead").innerHTML=`<span>${avg?"Average over 2,000 games":"One game"}, ${N} stations, ${R} rounds</span>`+
   `<span>Output per round: <b>${(res.cum[R]/R).toFixed(2)}</b> (plan 3.50)</span>`+
   `<span>Shortfall: <b>${short.toFixed(1)}</b> matches</span><span>WIP at end: <b>${res.wip[R].toFixed(1)}</b></span>`+
   (cfit?`<span>Fit: WIP ≈ <b>${cfit.toFixed(2)}</b>·√round</span>`:"");
}
function playOne(){const N=+$("dN").value,R=+$("dR").value,mode=$("dV").value;drawDice(game(N,R,mode),false,N,R);}
function playAvg(){const N=+$("dN").value,R=+$("dR").value,mode=$("dV").value,M=2000;
  const cum=new Array(R+1).fill(0),wip=new Array(R+1).fill(0);
  for(let g=0;g<M;g++){const r=game(N,R,mode);for(let i=0;i<=R;i++){cum[i]+=r.cum[i]/M;wip[i]+=r.wip[i]/M;}}
  drawDice({cum,wip},true,N,R);}
["dN","dR"].forEach(id=>$(id).addEventListener("input",()=>{$(id+"o").textContent=$(id).value;}));
$("dPlay").addEventListener("click",playOne);$("dAvg").addEventListener("click",playAvg);
$("dV").addEventListener("change",playAvg);$("dN").addEventListener("change",playAvg);$("dR").addEventListener("change",playAvg);

/* ---------- §4 M/M/1 ---------- */
function drawMM1(){const r=+$("mR").value;$("mRo").textContent=r.toFixed(2);
  const xs=[];for(let x=0;x<=0.981;x+=0.005)xs.push(x);
  const ymax=50;
  plot($("mc"),{x:[0,1],y:[0,ymax],xl:"utilization ρ",yl:"jobs in system",xticks:[0,.2,.4,.6,.8,1],
   areas:[{pts:xs.map(x=>[x,x/(1-x)+Math.sqrt(x)/(1-x)]).concat(xs.slice().reverse().map(x=>[x,Math.max(0,x/(1-x)-Math.sqrt(x)/(1-x))])),c:"var(--s2)",op:.15}],
   series:[{pts:xs.map(x=>[x,x/(1-x)]),c:"var(--s1)"},{pts:[[r,r/(1-r)]],dots:true,c:"var(--s3)",r:5}],
   vlines:[{x:r,c:"var(--s3)"}]});
  const L=r/(1-r);
  $("mRead").innerHTML=`<span>L = <b>${L.toFixed(2)}</b> jobs</span><span>sd(N) = <b>${(Math.sqrt(r)/(1-r)).toFixed(2)}</b></span><span>W = <b>${(1/(1-r)).toFixed(2)}</b> service times</span><span>P(no wait) = <b>${(1-r).toFixed(2)}</b></span>`;}
$("mR").addEventListener("input",drawMM1);

/* ---------- §5 Little's Law picture ---------- */
function drawLittle(){const a=[0.5,1.2,1.6,3.0,3.4,4.6],d=[1.4,2.3,3.1,4.0,4.4,5.6],T=6;
  const step=(ev)=>{const p=[[0,0]];ev.forEach((t,i)=>{p.push([t,i]);p.push([t,i+1]);});p.push([T,ev.length]);return p;};
  const A=step(a),D=step(d);
  const poly=A.concat(D.slice().reverse());
  plot($("lc"),{x:[0,T],y:[0,6.5],xl:"time",yl:"cumulative count",yticks:[0,1,2,3,4,5,6],xticks:[0,1,2,3,4,5,6],
    areas:[{pts:poly,c:"var(--s3)",op:.28}],series:[{pts:A,c:"var(--s2)"},{pts:D,c:"var(--s1)"}]});}

/* ---------- §6 Kingman ---------- */
function lindley(u,ca2,cs2,n){const A=sampler(1/u,ca2),S=sampler(1,cs2);let w=0,sum=0;const burn=Math.floor(n*0.05);
  for(let k=0;k<n+burn;k++){w=Math.max(0,w+S()-A());if(k>=burn)sum+=w;}return sum/n;}
let kPts=null;
function drawKing(){const ca=+$("kA").value,cs=+$("kS").value;$("kAo").textContent=ca.toFixed(2);$("kSo").textContent=cs.toFixed(2);
  const xs=[];for(let x=0.02;x<=0.975;x+=0.005)xs.push(x);
  const V=(ca+cs)/2,ymax=Math.max(4,Math.min(40,Math.max(V,1)*0.95/0.05*1.05));
  const ser=[{pts:xs.map(u=>[u,u/(1-u)]),c:"var(--muted)",dash:true,w:2},{pts:xs.map(u=>[u,V*u/(1-u)]),c:"var(--s1)"}];
  if(kPts&&kPts.ca===ca&&kPts.cs===cs)ser.push({pts:kPts.pts,dots:true,c:"var(--s3)"});
  plot($("kc"),{x:[0,1],y:[0,ymax],xl:"utilization u",yl:"mean wait in queue (× mean process time)",xticks:[0,.2,.4,.6,.8,1],series:ser});
  let txt=`<span>V = (c²ₐ + c²ₛ)/2 = <b>${V.toFixed(2)}</b></span><span>At u = 0.9: Wq ≈ <b>${(V*9).toFixed(1)}</b> × tₑ</span>`;
  if(Math.abs(ca-1)<1e-9)txt+=`<span>c²ₐ = 1, so this curve is exact (Pollaczek–Khinchine)</span>`;
  if(ca===0&&cs===0)txt+=`<span>No variability: no waiting at any u &lt; 1</span>`;
  if(kPts&&kPts.ca===ca&&kPts.cs===cs)txt+=`<span>Simulated at u = 0.9: <b>${kPts.at9.toFixed(1)}</b></span>`;
  $("kRead").innerHTML=txt;}
function simKing(){const ca=+$("kA").value,cs=+$("kS").value;const us=[0.3,0.5,0.6,0.7,0.8,0.85,0.9,0.95];
  const btn=$("kSim");btn.textContent="Simulating…";btn.disabled=true;
  setTimeout(()=>{const pts=us.map(u=>[u,lindley(u,ca,cs,200000)]);kPts={ca,cs,pts,at9:pts[6][1]};btn.textContent="Simulate points";btn.disabled=false;drawKing();},30);}
["kA","kS"].forEach(id=>$(id).addEventListener("input",drawKing));$("kSim").addEventListener("click",simKing);

/* ---------- §7 random walk at rho = 1 ---------- */
function runWalk(){const T=1000,G=200,P=300,grid=[];for(let i=0;i<=G;i++)grid.push(i*T/G);
  const mean=new Array(G+1).fill(0),samples=[];
  for(let p=0;p<P;p++){let t=0,n=0,gi=0;const path=new Array(G+1);
    while(gi<=G){const dt=-Math.log(rnd())/2;while(gi<=G&&grid[gi]<t+dt){path[gi]=n;gi++;}t+=dt;if(rnd()<0.5)n++;else if(n>0)n--;}
    for(let i=0;i<=G;i++)mean[i]+=path[i]/P;if(p<4)samples.push(path);}
  const ser=samples.map(s=>({pts:grid.map((g,i)=>[g,s[i]]),c:"var(--grid)",w:1.5}));
  ser.push({pts:grid.map((g,i)=>[g,mean[i]]),c:"var(--s1)",w:2.6});
  ser.push({pts:grid.map(g=>[g,2*Math.sqrt(g/Math.PI)]),c:"var(--s3)",dash:true,w:2.2});
  const ymax=Math.max(...samples.flat(),40)*1.05;
  plot($("rc"),{x:[0,T],y:[0,ymax],xl:"time (mean service times)",yl:"jobs in system",series:ser});}
$("rRun").addEventListener("click",runWalk);

/* ---------- §8 buffers ---------- */
function drawBuf(){const cols={2:"var(--s1)",3:"var(--s2)",4:"var(--s3)",5:"var(--s4)"};const ser=[];
  Object.keys(DATA.bufsweep).forEach(n=>{const pts=DATA.bufsweep[n].map((v,b)=>[b,v]);ser.push({pts,c:cols[n],dash:DASH[n],label:n+" stations"});ser.push({pts,dots:true,c:cols[n],r:3.5,marker:n==="5"?"square":undefined});});
  plot($("bc"),{x:[0,8],y:[0.4,1],xl:"buffer slots b between each pair of stations",yl:"throughput ÷ demand",xticks:[0,1,2,3,4,5,6,7,8],yticks:[.4,.5,.6,.7,.8,.9,1],
    series:ser.concat([{pts:[[0,1],[8,1]],c:"var(--muted)",dash:true,w:1.5}])});}

/* ---------- §9 bowl ---------- */
function drawBowl(){const cols={0:"var(--s1)",1:"var(--s2)",3:"var(--s3)"};const ser=[],opt=[];const xs=DATA.bowlx;
  Object.keys(DATA.bowl).forEach(b=>{const ys=DATA.bowl[b];const base=ys[8];const pts=xs.map((x,i)=>[x,100*(ys[i]/base-1)]);ser.push({pts,c:cols[b],dash:BOWL_DASH[b]});
    let k=0;ys.forEach((v,i)=>{if(v>ys[k])k=i;});opt.push([xs[k],100*(ys[k]/base-1)]);});
  ser.push({pts:opt,dots:true,c:"var(--s4)",r:5});
  plot($("wc"),{x:[0.8,1.2],y:[-4.5,1],xl:"middle station's mean time (1.0 = balanced)",yl:"throughput change vs balanced (%)",xticks:[.8,.9,1,1.1,1.2],yticks:[-4,-3,-2,-1,0,1],yf:v=>(v>0?"+":"")+v,
    series:ser,vlines:[{x:1,c:"var(--muted)",label:"balanced"}]});}

/* ---------- §10 cost ---------- */
function drawCost(){const lam=+$("cL").value,hc=+$("cH").value;const cm=$("cM");cm.min=lam+0.5;cm.max=lam*4+10;
  let mu=+cm.value;if(mu<=lam){mu=lam+0.5;cm.value=mu;}
  $("cLo").textContent=lam;$("cHo").textContent=hc.toFixed(2);$("cMo").textContent=(+cm.value).toFixed(1);
  const ms=Math.sqrt(hc*lam),mus=lam+ms,C=m=>m+hc*lam/(m-lam);
  const hi=+cm.max,xs=[];for(let x=lam+0.02;x<=hi;x+=(hi-lam)/300)xs.push(x);
  const ymax=C(mus)*2.2;
  plot($("cc"),{x:[lam,hi],y:[0,ymax],xl:"capacity μ (units per hour)",yl:"cost per hour ÷ c",
    series:[{pts:xs.map(x=>[x,x]),c:"var(--s2)",dash:"dashed",w:2},{pts:xs.map(x=>[x,hc*lam/(x-lam)]),c:"var(--s3)",dash:"dotted"},{pts:xs.map(x=>[x,C(x)]),c:"var(--s1)"},
      {pts:[[mus,C(mus)]],dots:true,ring:true,c:"var(--s4)",r:6},{pts:[[mu,C(mu)]],dots:true,c:"var(--ink)",r:5}],
    vlines:[{x:lam,c:"var(--muted)",label:"μ = λ"}]});
  const trim=lam+0.1*ms;
  $("cRead").innerHTML=`<span>μ* = λ + √(hλ/c) = <b>${mus.toFixed(1)}</b></span><span>Utilization at μ*: <b>${(100*lam/mus).toFixed(0)}%</b></span>`+
   `<span>Current cost: <b>${C(mu).toFixed(1)}</b> vs optimum <b>${C(mus).toFixed(1)}</b></span>`+
   `<span>${mu>mus?"Trimming toward μ* <b>saves</b> money here":"Trimming further <b>raises</b> cost here"}</span>`+
   `<span>Trim almost to demand (μ = ${trim.toFixed(1)}): cost <b>${C(trim).toFixed(1)}</b></span>`;}
["cL","cH","cM"].forEach(id=>$(id).addEventListener("input",drawCost));

/* ---------- initial state ---------- */
playAvg();drawMM1();drawLittle();drawKing();runWalk();drawBuf();drawBowl();drawCost();
/* Redraw every chart at its new size when the window is resized (same data, no re-simulation). */
let rsz;window.addEventListener("resize",()=>{clearTimeout(rsz);rsz=setTimeout(()=>{document.querySelectorAll("svg[id]").forEach(s=>{if(s._plot)plot(s,s._plot);});},150);});
})();
