window.JEENIUS_LESSON = {
  "num": 71,
  "slug": "geometry-proof-lab",
  "title": "Geometry and Proof Lab",
  "short": "Basic Geometry and Proof",
  "grade": "CLASS 9",
  "subject": "MATHEMATICS",
  "chapter": "Basic Concepts in Geometry",
  "intro": "Explore angles formed by two intersecting lines. The diagram changes with x, while the equality and straight-line rules remain true.",
  "kind": "geometry-proof",
  "controls": [
    {
      "key": "angle",
      "label": "Angle x",
      "min": 30,
      "max": 150,
      "step": 5,
      "value": 60,
      "unit": "°"
    }
  ],
};
window.JEENIUS_LESSON.draw = function(c,s,t,h,m){
const {N,B,G,W,INK,GREEN,RED,GOLD,H,L,R,C,E,A,TXT,clamp}=h;
const headline=(title,subtitle)=>{H(c,title,28,30,16,'left','Goldman');H(c,subtitle,28,51,11,'left','Saira','#52667d');L(c,28,67,772,67,1,N)};
switch(window.JEENIUS_LESSON.kind){
case 'geometry-proof':{headline('VERTICALLY OPPOSITE ANGLES','Two intersecting straight lines make equal opposite angles.');const x=330,y=236,theta=s.angle*Math.PI/180,dx=Math.cos(theta)*205,dy=Math.sin(theta)*170;L(c,98,y,590,y,2,N);L(c,x-dx,y+dy,x+dx,y-dy,2,N);C(c,x,y,4,N,N);H(c,'A',x+76,y-40,13,'left','Goldman');H(c,'C',x-75,y+45,13,'left','Goldman');H(c,'B',x-78,y-34,13,'left','Goldman');H(c,'D',x+80,y+44,13,'left','Goldman');H(c,s.angle+'°',x+58,y-14,16,'center','Goldman');H(c,s.angle+'°',x-58,y+25,16,'center','Goldman');H(c,(180-s.angle)+'°',x-62,y-18,13,'center','Goldman');H(c,(180-s.angle)+'°',x+62,y+30,13,'center','Goldman');R(c,570,103,190,282,B,N,1.5);H(c,'WHAT THE PROOF USES',588,132,12,'left','Goldman');H(c,'1. Opposite angles',588,170,12,'left','Goldman');TXT(c,['are equal.'],588,190,148,12,16);H(c,'2. Adjacent angles',588,230,12,'left','Goldman');TXT(c,['on a straight line','add to 180°.'],588,250,148,12,16);H(c,'CHECK',588,309,12,'left','Goldman');H(c,s.angle+'° + '+(180-s.angle)+'° = 180°',588,334,13,'left','Goldman');H(c,'Angle x = '+s.angle+'°',70,393,13,'left','Goldman');H(c,'Opposite angle = '+s.angle+'°',70,414,13,'left','Goldman');break;}
default: headline(window.JEENIUS_LESSON.title,'Interactive example');
}
};
