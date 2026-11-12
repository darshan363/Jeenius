window.JEENIUS_LESSON = {
  "num": 66,
  "slug": "compound-interest-lab",
  "title": "Compound Interest Lab",
  "short": "Compound Interest",
  "grade": "CLASS 8",
  "subject": "MATHEMATICS",
  "chapter": "Compound Interest",
  "intro": "Watch a balance grow year by year. Interest is added to the balance before the next year’s interest is calculated.",
  "kind": "compound-interest",
  "controls": [
    {
      "key": "principal",
      "label": "Principal",
      "min": 1000,
      "max": 20000,
      "step": 1000,
      "value": 5000,
      "unit": " ₹",
      "decimals": 0
    },
    {
      "key": "rate",
      "label": "Annual interest rate",
      "min": 1,
      "max": 20,
      "step": 1,
      "value": 10,
      "unit": "%"
    },
    {
      "key": "years",
      "label": "Time",
      "min": 1,
      "max": 6,
      "step": 1,
      "value": 3,
      "unit": " years"
    }
  ],
};
window.JEENIUS_LESSON.draw = function(c,s,t,h,m){
const {N,B,G,W,INK,GREEN,RED,GOLD,H,L,R,C,E,A,TXT,clamp}=h;
const headline=(title,subtitle)=>{H(c,title,28,30,16,'left','Goldman');H(c,subtitle,28,51,11,'left','Saira','#52667d');L(c,28,67,772,67,1,N)};
switch(window.JEENIUS_LESSON.kind){
case 'compound-interest':{headline('BALANCE GROWS YEAR BY YEAR','Illustration: annual compounding, with no deposits or withdrawals.');const p=s.principal,rate=s.rate/100,n=s.years;let vals=[p];for(let i=1;i<=n;i++)vals.push(vals[i-1]*(1+rate));const max=vals[vals.length-1];L(c,75,343,500,343,1.5,N);for(let i=0;i<=n;i++){const x=95+i*390/Math.max(1,n),hh=220*vals[i]/max;R(c,x-20,343-hh,40,hh,i===n?B:G,N,1.5);H(c,'Y'+i,x,364,11,'center','Goldman');H(c,(vals[i]/1000).toFixed(1)+'k',x,343-hh-10,10,'center');if(i>0)A(c,95+(i-1)*390/Math.max(1,n),120,95+i*390/Math.max(1,n),120,1.2,GREEN)}R(c,535,108,232,278,W,N,1.5);H(c,'YEAR '+n+' BALANCE',555,140,13,'left','Goldman');H(c,'₹'+vals[n].toFixed(2),555,183,22,'left','Goldman');H(c,'Interest earned',555,222,12);H(c,'₹'+(vals[n]-p).toFixed(2),555,247,18,'left','Goldman');L(c,555,266,744,266,1,N);TXT(c,['Year 0 is the starting','principal. Each next bar','includes interest from','earlier years.'],555,293,176,12,18);H(c,'Annual rate: '+s.rate+'%',70,401,12,'left','Goldman');break;}
default: headline(window.JEENIUS_LESSON.title,'Interactive example');
}
};
