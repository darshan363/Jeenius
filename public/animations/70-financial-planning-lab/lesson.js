window.JEENIUS_LESSON = {
  "num": 70,
  "slug": "financial-planning-lab",
  "title": "Financial Planning Lab",
  "short": "Financial Planning",
  "grade": "CLASS 9",
  "subject": "MATHEMATICS",
  "chapter": "Financial Planning",
  "intro": "Plan a simple monthly budget. Choose how much of the income to save, then compare monthly savings with a full year.",
  "kind": "financial-planning",
  "controls": [
    {
      "key": "income",
      "label": "Monthly income",
      "min": 10000,
      "max": 80000,
      "step": 5000,
      "value": 40000,
      "unit": " ₹",
      "decimals": 0
    },
    {
      "key": "save",
      "label": "Savings rate",
      "min": 5,
      "max": 50,
      "step": 5,
      "value": 20,
      "unit": "%"
    }
  ],
};
window.JEENIUS_LESSON.draw = function(c,s,t,h,m){
const {N,B,G,W,INK,GREEN,RED,GOLD,H,L,R,C,E,A,TXT,clamp}=h;
const headline=(title,subtitle)=>{H(c,title,28,30,16,'left','Goldman');H(c,subtitle,28,51,11,'left','Saira','#52667d');L(c,28,67,772,67,1,N)};
switch(window.JEENIUS_LESSON.kind){
case 'financial-planning':{headline('GIVE EVERY RUPEE A JOB','Illustrative budget · needs and savings vary by household.');const inc=s.income,save=inc*s.save/100,spend=inc-save,x=72,y=137,w=650;R(c,x,y,w,72,W,N,1.5);R(c,x,y,w*(1-s.save/100),72,G,N,1);R(c,x+w*(1-s.save/100),y,w*s.save/100,72,B,N,1);H(c,'SPENDING / NEEDS',x+14,y+27,13,'left','Goldman');H(c,'₹'+spend.toLocaleString('en-IN'),x+14,y+51,16,'left','Goldman');H(c,'SAVINGS',x+w*(1-s.save/100)+8,y+27,11,'left','Goldman');if(s.save>=13)H(c,'₹'+save.toLocaleString('en-IN'),x+w*(1-s.save/100)+8,y+51,14,'left','Goldman');R(c,72,247,310,112,W,N,1.5);H(c,'MONTHLY SAVINGS',92,278,12,'left','Goldman');H(c,'₹'+save.toLocaleString('en-IN'),92,318,24,'left','Goldman');R(c,410,247,312,112,W,N,1.5);H(c,'12-MONTH SAVINGS',430,278,12,'left','Goldman');H(c,'₹'+(save*12).toLocaleString('en-IN'),430,318,24,'left','Goldman');H(c,'Income: ₹'+inc.toLocaleString('en-IN')+'  ·  savings rate: '+s.save+'%',72,395,13,'left','Goldman');TXT(c,['Set aside planned savings, then budget the rest','for necessities and other expenses.'],72,420,620,12,16);break;}
default: headline(window.JEENIUS_LESSON.title,'Interactive example');
}
};
