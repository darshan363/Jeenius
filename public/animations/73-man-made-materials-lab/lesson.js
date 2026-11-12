window.JEENIUS_LESSON = {
  "num": 73,
  "slug": "man-made-materials-lab",
  "title": "Man-made Materials Lab",
  "short": "Man-made Materials",
  "grade": "CLASS 8",
  "subject": "SCIENCE",
  "chapter": "Man-made Materials",
  "intro": "Trace a material from its starting materials through a manufacturing process to an everyday product. Then consider reuse and disposal.",
  "kind": "manmade-materials",
  "controls": [
    {
      "key": "material",
      "label": "Choose material",
      "type": "select",
      "options": [
        "Plastic",
        "Nylon",
        "Glass"
      ],
      "value": 0
    }
  ],
};
window.JEENIUS_LESSON.draw = function(c,s,t,h,m){
const {N,B,G,W,INK,GREEN,RED,GOLD,H,L,R,C,E,A,TXT,clamp}=h;
const headline=(title,subtitle)=>{H(c,title,28,30,16,'left','Goldman');H(c,subtitle,28,51,11,'left','Saira','#52667d');L(c,28,67,772,67,1,N)};
switch(window.JEENIUS_LESSON.kind){
case 'manmade-materials':{headline('FROM RAW MATERIAL TO PRODUCT','Manufacturing changes materials into useful objects.');const rows=[['PLASTIC','Feedstock','Polymer process','Container'],['NYLON','Chemical feedstock','Fibre spinning','Rope / fabric'],['GLASS','Silica-rich mix','Melt and shape','Bottle / window']][s.material];const xs=[120,310,500,690];for(let i=0;i<3;i++)A(c,xs[i]+48,214,xs[i+1]-50,214,1.5,N);xs.forEach((x,i)=>{R(c,x-66,138,132,148,i===s.material?B:W,N,i===s.material?2:1);H(c,['RAW MATERIAL','PROCESS','SHAPING','PRODUCT'][i],x,164,11,'center','Goldman');if(i===0){if(s.material===2){for(let j=0;j<5;j++)C(c,x-30+j*15,204+(j%2)*7,6,G,N,1)}else if(s.material===1){for(let j=0;j<5;j++)L(c,x-32+j*15,194,x-24+j*15,220,3,GOLD)}else{C(c,x-10,205,18,GOLD,N,1);C(c,x+16,214,13,G,N,1)}}if(i===1){R(c,x-36,185,72,48,G,N,1.5);for(let j=0;j<4;j++)C(c,x-22+j*15,209,4,N,N)}if(i===2){R(c,x-29,184,58,55,s.material===2?G:s.material===1?B:GOLD,N,1.5);L(c,x-29,184,x+29,184,1,N)}if(i===3){if(s.material===1){L(c,x-30,192,x+28,221,4,N);L(c,x-30,200,x+28,229,4,GREEN);L(c,x-30,208,x+28,237,4,N)}else if(s.material===2){R(c,x-24,182,48,64,B,N,2);E(c,x,182,24,7,B,N,1)}else{R(c,x-26,184,52,54,B,N,2);R(c,x-19,174,38,10,GOLD,N,1)}}H(c,rows[i],x,260,10,'center','Saira')});R(c,105,321,590,63,W,N,1.5);H(c,'AFTER USE',125,347,12,'left','Goldman');A(c,230,347,296,347,1.5,N);H(c,'Reuse',315,352,12,'center');A(c,355,347,421,347,1.5,N);H(c,'Check local recycling',438,352,12,'center');A(c,534,347,592,347,1.5,N);H(c,'Dispose responsibly',603,352,11,'center');H(c,['Plastic','Nylon','Glass'][s.material]+' is useful, but handling and end-of-life choices matter.',105,414,12);break;}
default: headline(window.JEENIUS_LESSON.title,'Interactive example');
}
};
