window.JEENIUS_LESSON = {
  "num": 69,
  "slug": "ratio-proportion-lab",
  "title": "Ratio and Proportion Lab",
  "short": "Ratio and Proportion",
  "grade": "CLASS 9",
  "subject": "MATHEMATICS",
  "chapter": "Ratio and Proportion",
  "intro": "Scale a ladoo recipe without changing its taste. Multiply every part by the same number to keep the ratio equivalent.",
  "kind": "ratio",
  "controls": [
    {
      "key": "ghee",
      "label": "Ghee bowls",
      "min": 1,
      "max": 5,
      "step": 1,
      "value": 2,
      "unit": " bowl(s)"
    }
  ],
};
window.JEENIUS_LESSON.draw = function(c,s,t,h,m){
const {N,B,G,W,INK,GREEN,RED,GOLD,H,L,R,C,E,A,TXT,clamp}=h;
const headline=(title,subtitle)=>{H(c,title,28,30,16,'left','Goldman');H(c,subtitle,28,51,11,'left','Saira','#52667d');L(c,28,67,772,67,1,N)};
switch(window.JEENIUS_LESSON.kind){
case 'ratio':{headline('SCALE A RECIPE','Keep the same ratio to keep the same proportions.');const qs=[['GHEE',s.ghee,'#d8a447'],['RAWA',3*s.ghee,B],['SUGAR',2*s.ghee,W]],xs=[150,350,550];qs.forEach((q,i)=>{const x=xs[i],n=q[1],bh=clamp(n/15*190,22,190);R(c,x-55,145,110,202,W,N,2);R(c,x-45,347-bh,90,bh,q[2],N,1.5);L(c,x-45,347-bh,x+45,347-bh,1,N);H(c,String(n)+' bowl(s)',x,123,15,'center','Goldman');H(c,q[0],x,380,13,'center','Goldman');H(c,'× '+(i===0?1:i===1?3:2),x,405,11,'center')});A(c,210,235,281,235,1.5,N);A(c,410,235,481,235,1.5,N);R(c,600,87,160,32,B,N,1.5);H(c,'RATIO  1 : 3 : 2',680,108,13,'center','Goldman');TXT(c,['Every ingredient is','multiplied by the same','scale factor.'],600,150,150,12,18);H(c,'BOWLS OF GHEE = '+s.ghee,60,429,10,'left','Goldman');break;}
default: headline(window.JEENIUS_LESSON.title,'Interactive example');
}
};
