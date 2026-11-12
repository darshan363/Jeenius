window.JEENIUS_LESSON = {
  "num": 65,
  "slug": "division-of-polynomials-lab",
  "title": "Division of Polynomials Lab",
  "short": "Division of Polynomials",
  "grade": "CLASS 8",
  "subject": "MATHEMATICS",
  "chapter": "Division of Polynomials",
  "intro": "Follow the two division steps. The example divides a quadratic polynomial by a linear polynomial and shows the remainder.",
  "kind": "polynomial-division",
  "controls": [
    {
      "key": "k",
      "label": "Divisor constant k",
      "min": 1,
      "max": 5,
      "step": 1,
      "value": 2,
      "unit": ""
    },
    {
      "key": "remainder",
      "label": "Remainder r",
      "min": 0,
      "max": 4,
      "step": 1,
      "value": 0,
      "unit": ""
    }
  ],
};
window.JEENIUS_LESSON.draw = function(c,s,t,h,m){
const {N,B,G,W,INK,GREEN,RED,GOLD,H,L,R,C,E,A,TXT,clamp}=h;
const headline=(title,subtitle)=>{H(c,title,28,30,16,'left','Goldman');H(c,subtitle,28,51,11,'left','Saira','#52667d');L(c,28,67,772,67,1,N)};
switch(window.JEENIUS_LESSON.kind){
case 'polynomial-division':{headline('POLYNOMIAL LONG DIVISION','Divide the leading term, multiply, subtract, then repeat.');const k=s.k,r=s.remainder;R(c,52,98,448,287,W,N,1.5);H(c,'x + '+k+'  )  x² + '+(k+3)+'x + '+(3*k+r),75,136,16,'left','Goldman');L(c,75,149,465,149,2,N);H(c,'− (x² + '+k+'x)',124,181,14,'left','Saira');L(c,124,192,440,192,1,N,[3,3]);H(c,'3x + '+(3*k+r),124,222,15,'left','Goldman');H(c,'− (3x + '+(3*k)+')',124,254,14);L(c,124,265,440,265,1,N,[3,3]);H(c,'Remainder = '+r,124,296,17,'left','Goldman');H(c,'QUOTIENT',124,344,11,'left','Goldman');H(c,'x + 3',220,344,19,'left','Goldman');R(c,535,108,232,254,B,N,1.5);H(c,'STEP BY STEP',555,139,13,'left','Goldman');C(c,562,170,12,N,N);H(c,'1',562,174,12,'center','Goldman',W);TXT(c,['x² ÷ x = x','Subtract x(x + k).'],584,167,165,12,18);C(c,562,220,12,N,N);H(c,'2',562,224,12,'center','Goldman',W);TXT(c,['3x ÷ x = 3','Subtract 3(x + k).'],584,217,165,12,18);C(c,562,270,12,N,N);H(c,'3',562,274,12,'center','Goldman',W);TXT(c,[r===0?'Nothing is left.':'The constant left is r = '+r+'.',r===0?'Division is exact.':'This is the remainder.'],584,267,165,12,18);H(c,'Identity: dividend = divisor × quotient + remainder',54,414,11);break;}
default: headline(window.JEENIUS_LESSON.title,'Interactive example');
}
};
