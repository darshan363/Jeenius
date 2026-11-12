window.JEENIUS_LESSON = {
  "num": 61,
  "slug": "work-and-energy-lab",
  "title": "Work and Energy Lab",
  "short": "Work and Energy",
  "grade": "CLASS 9",
  "subject": "SCIENCE",
  "chapter": "Work and Energy",
  "intro": "See how a push and a movement combine to do work. Change force or distance and watch the work calculation update.",
  "kind": "work-energy",
  "controls": [
    {
      "key": "force",
      "label": "Force",
      "min": 0,
      "max": 20,
      "step": 1,
      "value": 10,
      "unit": " N"
    },
    {
      "key": "distance",
      "label": "Distance moved",
      "min": 0,
      "max": 10,
      "step": 1,
      "value": 4,
      "unit": " m"
    }
  ],
};
window.JEENIUS_LESSON.draw = function(c,s,t,h,m){
const {N,B,G,W,INK,GREEN,RED,GOLD,H,L,R,C,E,A,TXT,clamp}=h;
const headline=(title,subtitle)=>{H(c,title,28,30,16,'left','Goldman');H(c,subtitle,28,51,11,'left','Saira','#52667d');L(c,28,67,772,67,1,N)};
switch(window.JEENIUS_LESSON.kind){
case 'work-energy':{headline('WORK = FORCE × DISTANCE','The force must act along the direction of movement.');const x=120+s.distance*28,forceLen=clamp(s.force*5,0,120);L(c,54,342,514,342,2,N);for(let i=0;i<=10;i++){L(c,70+i*42,342,70+i*42,350,1,N);H(c,String(i),70+i*42,366,10,'center')}H(c,'DISTANCE (m)',70,390,11,'left','Goldman');R(c,clamp(x,80,470),267,62,66,B,N,2);R(c,clamp(x,80,470)+12,278,38,20,W,N,1.5);H(c,'BOX',clamp(x,80,470)+31,306,11,'center','Goldman');A(c,clamp(x,80,470)+58,294,clamp(x,80,470)+58+forceLen,294,3,GREEN);H(c,s.force+' N',clamp(x,80,470)+58+forceLen/2,277,12,'center','Goldman');H(c,'A force pushes the box',72,235,12);R(c,560,118,208,238,W,N,1.5);H(c,'WORK DONE',580,146,13,'left','Goldman');const w=s.force*s.distance;H(c,w.toFixed(1)+' J',580,194,30,'left','Goldman');H(c,'Force × distance',580,216,12);R(c,580,246,166,18,G,N,1);R(c,580,246,166*clamp(w/200,0,1),18,B,N,1);H(c,'0 J',580,282,10);H(c,'200 J',746,282,10,'right');TXT(c,['Watch the box move as you','change the force or distance.'],580,318,172,12,17);H(c,'Simple model: force along motion',28,412,11);break;}
default: headline(window.JEENIUS_LESSON.title,'Interactive example');
}
};
