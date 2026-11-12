window.JEENIUS_LESSON = {
  "num": 62,
  "slug": "inside-the-atom-lab",
  "title": "Inside the Atom Lab",
  "short": "Inside the Atom",
  "grade": "CLASS 8",
  "subject": "SCIENCE",
  "chapter": "Inside the Atom",
  "intro": "Explore a simple atom model. Protons and neutrons are in the nucleus; electrons are shown around it. The drawing is not to scale.",
  "kind": "atom",
  "controls": [
    {
      "key": "protons",
      "label": "Protons",
      "min": 1,
      "max": 10,
      "step": 1,
      "value": 3,
      "unit": ""
    },
    {
      "key": "neutrons",
      "label": "Neutrons",
      "min": 0,
      "max": 12,
      "step": 1,
      "value": 4,
      "unit": ""
    }
  ],
};
window.JEENIUS_LESSON.draw = function(c,s,t,h,m){
const {N,B,G,W,INK,GREEN,RED,GOLD,H,L,R,C,E,A,TXT,clamp}=h;
const headline=(title,subtitle)=>{H(c,title,28,30,16,'left','Goldman');H(c,subtitle,28,51,11,'left','Saira','#52667d');L(c,28,67,772,67,1,N)};
switch(window.JEENIUS_LESSON.kind){
case 'atom':{headline('A SIMPLE MODEL OF THE ATOM','Nucleus in the middle · electrons around it · drawing not to scale');const cx=395,cy=235;[70,116,158].forEach((rx,i)=>{c.save();c.beginPath();c.ellipse(cx,cy,rx,rx*.62,i*.42,0,Math.PI*2);c.strokeStyle=N;c.lineWidth=1.3;c.setLineDash([5,5]);c.stroke();c.restore()});let p=s.protons,n=s.neutrons;const dots=[];for(let i=0;i<p+n;i++){const ang=i*2.399,rad=12+Math.sqrt(i)*7;dots.push([cx+Math.cos(ang)*rad,cy+Math.sin(ang)*rad])}dots.forEach((d,i)=>C(c,d[0],d[1],10,i<p?B:G,N,1.5));H(c,'p⁺',cx-1,cy-3,10,'center','Goldman');H(c,'n⁰',cx+13,cy+14,10,'center','Goldman');for(let i=0;i<p;i++){const shell=i<2?0:1,j=i<2?i:i-2,count=i<2?2:Math.max(1,p-2),rad=shell===0?70:116,ang=j/count*Math.PI*2+t*(shell===0?.6:-.38);const ex=cx+Math.cos(ang)*rad,ey=cy+Math.sin(ang)*rad*.62;C(c,ex,ey,7,N,W,1.5)}R(c,570,105,194,276,W,N,1.5);H(c,'PARTS OF AN ATOM',586,132,12,'left','Goldman');C(c,592,164,7,B,N,1);H(c,'Proton (positive)',608,169,12);C(c,592,193,7,G,N,1);H(c,'Neutron (no charge)',608,198,12);C(c,592,222,6,N,W,1);H(c,'Electron (negative)',608,227,12);TXT(c,['The nucleus contains protons','and neutrons. Electrons occupy','regions around the nucleus.'],586,270,158,12,18);H(c,'Atomic number = proton count',586,342,11,'left','Goldman');H(c,'Mass number = p + n',586,362,11,'left','Goldman');H(c,'NOT TO SCALE',395,413,10,'center','Goldman');break;}
default: headline(window.JEENIUS_LESSON.title,'Interactive example');
}
};
