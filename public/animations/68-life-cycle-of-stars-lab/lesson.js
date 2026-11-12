window.JEENIUS_LESSON = {
  "num": 68,
  "slug": "life-cycle-of-stars-lab",
  "title": "Life Cycle of Stars Lab",
  "short": "Life Cycle of Stars",
  "grade": "CLASS 8",
  "subject": "SCIENCE",
  "chapter": "Life Cycle of Stars",
  "intro": "Follow a simplified star life cycle from a cloud of gas and dust to a final stage. Choose a mass group to compare possible outcomes.",
  "kind": "star-life",
  "controls": [
    {
      "key": "mass",
      "label": "Star mass group",
      "type": "select",
      "options": [
        "Low mass",
        "Medium / high mass",
        "Very high mass"
      ],
      "value": 2
    },
    {
      "key": "stage",
      "label": "Life-cycle stage",
      "type": "select",
      "options": [
        "Nebula",
        "Protostar",
        "Main sequence",
        "Giant / supergiant",
        "Final stage"
      ],
      "value": 0
    }
  ],
};
window.JEENIUS_LESSON.draw = function(c,s,t,h,m){
const {N,B,G,W,INK,GREEN,RED,GOLD,H,L,R,C,E,A,TXT,clamp}=h;
const headline=(title,subtitle)=>{H(c,title,28,30,16,'left','Goldman');H(c,subtitle,28,51,11,'left','Saira','#52667d');L(c,28,67,772,67,1,N)};
switch(window.JEENIUS_LESSON.kind){
case 'star-life':{headline('A STAR’S LIFE CYCLE','Simplified pathway · exact evolution depends on stellar mass.');const names=['Nebula','Protostar','Main\nsequence','Giant /\nsupergiant','Final stage'];const xs=[92,245,398,551,704];for(let i=0;i<4;i++)A(c,xs[i]+28,160,xs[i+1]-32,160,1.5,N);xs.forEach((x,i)=>{const active=i===s.stage;C(c,x,160,active?38:29,active?B:W,N,active?3:1);if(i===0){for(let j=0;j<9;j++)C(c,x+Math.cos(j*2.4)*18,160+Math.sin(j*2.4)*14,5,j%2?G:B,N,.5)}else if(i===1){C(c,x,160,13,GOLD,N,1.5);C(c,x-5,156,5,RED,N,1)}else if(i===2){C(c,x,160,19,GOLD,N,1.5);for(let j=0;j<8;j++){const a=j*Math.PI/4;L(c,x+Math.cos(a)*20,160+Math.sin(a)*20,x+Math.cos(a)*28,160+Math.sin(a)*28,2,GOLD)}}else if(i===3){C(c,x,160,24,RED,N,1.5);C(c,x,160,12,GOLD,N,1)}else{C(c,x,160,18,s.mass===0?B:N,N,2);if(s.mass===2){C(c,x,160,7,N,N,1);for(let j=0;j<8;j++){const a=j*Math.PI/4;L(c,x+Math.cos(a)*22,160+Math.sin(a)*22,x+Math.cos(a)*29,160+Math.sin(a)*29,1.5,N)}}}TXT(c,names[i].split('\n'),x,211,90,11,14,active?N:'#52667d',active?'Goldman':'Saira')});R(c,76,266,648,104,W,N,1.5);H(c,'WHAT HAPPENS AT THE SELECTED STAGE?',96,292,12,'left','Goldman');TXT(c,[['Gas and dust collect in a nebula.','Gravity gathers the material.'],['A contracting protostar grows hot.','The core continues to heat.'],['Fusion in the core releases energy.','Gravity and pressure are in balance.'],['The star expands as core fuel changes.','The outer layers become larger.'],[s.mass===0?'Outer layers drift away; a white dwarf remains.':s.mass===1?'A massive star may leave a neutron star after a supernova.':'A very massive star may collapse into a black hole.','The exact path depends on mass.']][s.stage],96,318,595,12,17);H(c,'MASS GROUP: '+['LOW MASS','MEDIUM / HIGH MASS','VERY HIGH MASS'][s.mass],76,400,12,'left','Goldman');break;}
default: headline(window.JEENIUS_LESSON.title,'Interactive example');
}
};
