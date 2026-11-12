window.JEENIUS_LESSON = {
  "num": 67,
  "slug": "metals-and-nonmetals-lab",
  "title": "Metals and Nonmetals Lab",
  "short": "Metals and Nonmetals",
  "grade": "CLASS 8",
  "subject": "SCIENCE",
  "chapter": "Metals and Nonmetals",
  "intro": "Select a sample and a property test. The lesson compares common classroom properties; it is a safe illustration, not a real experiment.",
  "kind": "metals",
  "controls": [
    {
      "key": "material",
      "label": "Sample material",
      "type": "select",
      "options": [
        "Copper",
        "Iron",
        "Sulfur"
      ],
      "value": 0
    },
    {
      "key": "test",
      "label": "Property test",
      "type": "select",
      "options": [
        "Electrical conductivity",
        "Heat conduction",
        "Hammering / malleability"
      ],
      "value": 0
    }
  ],
};
window.JEENIUS_LESSON.draw = function(c,s,t,h,m){
const {N,B,G,W,INK,GREEN,RED,GOLD,H,L,R,C,E,A,TXT,clamp}=h;
const headline=(title,subtitle)=>{H(c,title,28,30,16,'left','Goldman');H(c,subtitle,28,51,11,'left','Saira','#52667d');L(c,28,67,772,67,1,N)};
switch(window.JEENIUS_LESSON.kind){
case 'metals':{headline('COMPARE A MATERIAL PROPERTY','Choose a sample and a test on the right.');const mats=[['COPPER','Metal',1],['IRON','Metal',1],['SULFUR','Nonmetal',0]],mat=mats[s.material],conduct=s.test===2?(s.material!==2):s.material!==2;R(c,58,104,245,278,W,N,1.5);H(c,'SELECTED SAMPLE',78,132,12,'left','Goldman');const fill=s.material===2?G:s.material===1?B:'#c68b54';if(s.test===2){R(c,130,215,95,50,fill,N,2);if(conduct){L(c,175,202,160,184,2,N);L(c,175,202,201,184,2,N);A(c,180,210,215,210,2,GREEN);H(c,'shape changes',180,289,12,'center')}else{L(c,130,215,150,232,2,RED);L(c,160,235,184,215,2,RED);H(c,'brittle / cracks',180,289,12,'center')}}else{R(c,137,190,82,94,fill,N,2);H(c,178,240,13,'center','Goldman');if(s.test===0){L(c,80,236,137,236,3,N);L(c,219,236,272,236,3,N);R(c,68,215,28,43,B,N,2);H(c,'+',82,232,11,'center','Goldman');H(c,'−',82,249,11,'center','Goldman');C(c,272,199,13,conduct?GOLD:G,N,2);L(c,272,212,272,240,2,N);if(conduct){for(let i=0;i<6;i++)C(c,263+i*3,199,2,N,N);H(c,'bulb ON',178,315,13,'center','Goldman')}else H(c,'bulb OFF',178,315,13,'center','Goldman')}else{A(c,93,171,147,188,2,GOLD);A(c,100,167,147,188,2,GOLD);for(let i=0;i<4;i++)A(c,225,206+i*13,250,206+i*13,1.5,conduct?RED:N);H(c,178,315,conduct?'HEAT PASSES':'LIMITED HEAT',12,'center','Goldman')}}R(c,420,112,345,265,B,N,1.5);H(c,'OBSERVATION',442,142,13,'left','Goldman');H(c,mat[0]+' · '+mat[1],442,178,19,'left','Goldman');TXT(c,s.test===0?(conduct?['The bulb lights in this simplified','circuit because the selected sample','is a conductor.']:['The bulb stays off: the selected','sample is a poor conductor in','this simple model.']):s.test===1?(conduct?['Heat can pass through this','sample in the classroom model.']:['This sample is shown as a poor','heat conductor in the model.']):(conduct?['The metal sample can be shaped','in this simplified demonstration.']:['The nonmetal sample is shown as','brittle rather than malleable.']),442,216,284,13,19);H(c,'EXAMPLE USE',442,315,11,'left','Goldman');H(c,['Wiring','Tools / structures','Chemical manufacture'][s.material],442,337,13);H(c,'Illustration only · do not heat or strike real materials.',58,414,11);break;}
default: headline(window.JEENIUS_LESSON.title,'Interactive example');
}
};
