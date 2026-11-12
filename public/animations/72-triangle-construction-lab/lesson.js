window.JEENIUS_LESSON = {
  "num": 72,
  "slug": "triangle-construction-lab",
  "title": "Triangle Construction Lab",
  "short": "Constructions of Triangles",
  "grade": "CLASS 9",
  "subject": "MATHEMATICS",
  "chapter": "Constructions of Triangles",
  "intro": "Construct a triangle from three side lengths (SSS). The circles show compass arcs from the two endpoints of the base.",
  "kind": "triangle-construction",
  "controls": [
    {
      "key": "a",
      "label": "Side BC",
      "min": 3,
      "max": 8,
      "step": 1,
      "value": 6,
      "unit": " cm"
    },
    {
      "key": "b",
      "label": "Side AC",
      "min": 3,
      "max": 8,
      "step": 1,
      "value": 5,
      "unit": " cm"
    },
    {
      "key": "c",
      "label": "Base AB",
      "min": 3,
      "max": 8,
      "step": 1,
      "value": 7,
      "unit": " cm"
    }
  ],
};
window.JEENIUS_LESSON.draw = function(c,s,t,h,m){
const {N,B,G,W,INK,GREEN,RED,GOLD,H,L,R,C,E,A,TXT,clamp}=h;
const headline=(title,subtitle)=>{H(c,title,28,30,16,'left','Goldman');H(c,subtitle,28,51,11,'left','Saira','#52667d');L(c,28,67,772,67,1,N)};
switch(window.JEENIUS_LESSON.kind){
case 'triangle-construction':{headline('CONSTRUCT A TRIANGLE BY SSS','AB is the base. Use one arc from A and one arc from B.');const a=s.a,b=s.b,base=s.c,valid=a+b>base&&a+base>b&&b+base>a,scale=24,Ax=230,Ay=342,Bx=Ax+base*scale,By=Ay;L(c,Ax,Ay,Bx,By,2,N);const proj=(b*b+base*base-a*a)/(2*base),high=Math.sqrt(Math.max(0,b*b-proj*proj)),Cx=Ax+proj*scale,Cy=Ay-high*scale;c.save();c.setLineDash([5,5]);c.strokeStyle=GREEN;c.lineWidth=1.5;c.beginPath();c.arc(Ax,Ay,b*scale,Math.PI,Math.PI*2);c.stroke();c.beginPath();c.arc(Bx,By,a*scale,Math.PI,Math.PI*2);c.stroke();c.restore();if(valid){c.save();c.beginPath();c.moveTo(Ax,Ay);c.lineTo(Bx,By);c.lineTo(Cx,Cy);c.closePath();c.fillStyle=B;c.fill();c.strokeStyle=N;c.lineWidth=2;c.stroke();c.restore();L(c,Ax,Ay,Cx,Cy,2,N);L(c,Bx,By,Cx,Cy,2,N);C(c,Cx,Cy,4,N,N);H(c,'C',Cx,Cy-12,14,'center','Goldman');H(c,b+' cm',Ax+(Cx-Ax)/2-12,Ay+(Cy-Ay)/2-8,12,'center','Goldman');H(c,a+' cm',Bx+(Cx-Bx)/2+12,By+(Cy-By)/2-8,12,'center','Goldman');H(c,base+' cm',(Ax+Bx)/2,Ay+24,12,'center','Goldman')}C(c,Ax,Ay,4,N,N);C(c,Bx,By,4,N,N);H(c,'A',Ax,Ay+18,13,'center','Goldman');H(c,'B',Bx,By+18,13,'center','Goldman');R(c,514,104,250,277,W,N,1.5);H(c,'CONSTRUCTION CHECK',534,134,13,'left','Goldman');TXT(c,['1. Draw AB = '+base+' cm.','2. Draw an arc centred at A','   with radius '+b+' cm.','3. Draw an arc centred at B','   with radius '+a+' cm.','4. Join the intersection to','   A and B.'],534,166,210,12,20);H(c,valid?'ARCS MEET: TRIANGLE POSSIBLE':'ARCS DO NOT FORM A TRIANGLE',534,333,valid?11:10,'left','Goldman',valid?GREEN:RED);H(c,valid?'Valid SSS construction':'Change the side lengths',534,355,12,'left','Goldman');break;}
default: headline(window.JEENIUS_LESSON.title,'Interactive example');
}
};
