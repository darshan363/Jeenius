/* Jeenius mini-lab engine: picture + controls + one line of logic. */
const T=(x,y,s,z=13,f='#12305c',a='middle',w=400)=>`<text x="${x}" y="${y}" font-size="${z}" fill="${f}" text-anchor="${a}" font-weight="${w}">${s}</text>`;
const R=(x,y,w,h,f='#e6eeff',s='#013062',r=0)=>`<rect x="${x}" y="${y}" width="${w}" height="${h}" rx="${r}" fill="${f}" stroke="${s}"/>`;
const C=(x,y,r,f='#13498f',s='none')=>`<circle cx="${x}" cy="${y}" r="${r}" fill="${f}" stroke="${s}"/>`;
const L=(a,b,c,d,s='#013062',w=2)=>`<line x1="${a}" y1="${b}" x2="${c}" y2="${d}" stroke="${s}" stroke-width="${w}"/>`;
function Lab(c){
  const v={},prev={};let first=true,tm;
  document.body.innerHTML=`<link href="https://fonts.googleapis.com/css2?family=Goldman:wght@400;700&family=Saira:wght@400;600&display=swap" rel="stylesheet">
  <style>*{box-sizing:border-box}body{margin:0;padding:14px;font:14px/1.5 Saira,sans-serif;color:#013062;background:#e9e9e9 url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='24' height='24'%3E%3Cpath d='M24 0H0v24' fill='none' stroke='%23013062' stroke-opacity='.13'/%3E%3C/svg%3E")}h1,h2,.b{font-family:Goldman,sans-serif;font-weight:400}h1{font-size:20px;margin:0 0 6px;overflow-wrap:break-word}.ex{background:#e6eeff;border:2px solid #013062;padding:8px 12px;margin:6px 0;overflow-wrap:break-word;word-break:break-word}.tools{display:flex;flex-wrap:wrap;gap:8px;margin:8px 0}.b{display:inline-block;padding:7px 12px;border:2px solid #013062;background:#fff;color:#013062;cursor:pointer;box-shadow:2px 2px 0 #013062}.b.on{background:#013062;color:#fff}svg{width:100%;background:#fff;border:1px solid #013062;display:block;max-width:100%;height:auto}.c{margin:10px 0}.c label{display:block;font-weight:600;margin-bottom:3px;overflow-wrap:break-word}.c input{width:100%;accent-color:#013062}.tx{background:#fff;border-left:4px solid #013062;padding:8px 12px;overflow-wrap:anywhere;word-break:break-word}.ac{font-weight:600}.small{font-size:12px}@media(max-width:600px){body{padding:10px}h1{font-size:18px}.ex{padding:7px 10px;font-size:13px}.b{padding:6px 10px;font-size:12px}.tx{padding:7px 10px;font-size:13px}}@media(prefers-reduced-motion:reduce){*{animation-duration:.01ms!important;transition-duration:.01ms!important}}</style>
  <h1>${c.title}</h1>  <svg id=g viewBox="0 0 400 200" role="img" aria-label="${c.title} interactive visual"></svg><div id=cs></div><p class=tx id=tx></p>`;
  const g=document.getElementById('g'),tx=document.getElementById('tx'),cs=document.getElementById('cs');
  const name=(k,x)=>{const d=c.ctrl.find(q=>q.k===k);return d.opts?d.opts[x]:x+(d.unit||'')};
  function upd(k){
    g.innerHTML=c.draw(v);tx.textContent=c.say(v);
    if(first){first=false;return}
    clearTimeout(tm);tm=setTimeout(()=>{const d=c.ctrl.find(q=>q.k===k);
      parent.postMessage({type:'jeenius-event',summary:`student changed ${d.label} from ${name(k,prev[k])} to ${name(k,v[k])}. ${c.say(v)}`.slice(0,290)},'*')},700);
    if(k!==undefined)prev[k]=v[k];
  }
  c.ctrl.forEach(d=>{v[d.k]=prev[d.k]=d.val;const w=document.createElement('div');w.className='c';
    if(d.opts){w.innerHTML=`<label>${d.label}</label>`;d.opts.forEach((o,i)=>{const b=document.createElement('button');b.className='b'+(i===d.val?' on':'');b.textContent=o;
      b.onclick=()=>{v[d.k]=i;[...w.querySelectorAll('.b')].forEach((x,j)=>x.classList.toggle('on',j===i));upd(d.k)};w.append(b)})}
    else{w.innerHTML=`<label>${d.label}: <span>${d.val}${d.unit||''}</span></label><input type=range min=${d.min} max=${d.max} step=${d.step||1} value=${d.val}>`;
      const input=w.querySelector('input');input.oninput=e=>{v[d.k]=+e.target.value;w.querySelector('span').textContent=e.target.value+(d.unit||'');upd(d.k)}}
    cs.append(w)});
  upd();
}
if(typeof module!=='undefined')module.exports={T,R,C,L};
