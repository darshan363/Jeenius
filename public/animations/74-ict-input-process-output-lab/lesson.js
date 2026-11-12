window.JEENIUS_LESSON = {
  "num": 74,
  "slug": "ict-input-process-output-lab",
  "title": "ICT Input–Process–Output Lab",
  "short": "Information Communication Technology",
  "grade": "CLASS 9",
  "subject": "SCIENCE",
  "chapter": "Information Communication Technology (ICT)",
  "intro": "See how a digital task moves from input to processing to output. Choose a task and follow the information through the system.",
  "kind": "ict",
  "controls": [
    {
      "key": "task",
      "label": "Choose a task",
      "type": "select",
      "options": [
        "Research a question",
        "Use a spreadsheet",
        "Create a presentation"
      ],
      "value": 0
    }
  ],
};
window.JEENIUS_LESSON.draw = function(c,s,t,h,m){
const {N,B,G,W,INK,GREEN,RED,GOLD,H,L,R,C,E,A,TXT,clamp}=h;
const headline=(title,subtitle)=>{H(c,title,28,30,16,'left','Goldman');H(c,subtitle,28,51,11,'left','Saira','#52667d');L(c,28,67,772,67,1,N)};
switch(window.JEENIUS_LESSON.kind){
case 'ict':{headline('INPUT → PROCESS → OUTPUT','Choose a digital task and see its workflow.');const arr=[['RESEARCH','Question','Search + verify','Sourced answer'],['SPREADSHEET','Numbers: 12, 8, 5','SUM(12, 8, 5)','Total = 25'],['PRESENTATION','Lesson idea','Organise + illustrate','3 clear slides']][s.task],xs=[145,400,655];for(let i=0;i<2;i++)A(c,xs[i]+82,230,xs[i+1]-83,230,2,N);xs.forEach((x,i)=>{R(c,x-94,140,188,178,i===1?B:W,N,i===1?2:1.5);H(c,['INPUT','PROCESS','OUTPUT'][i],x,170,13,'center','Goldman');if(i===0){R(c,x-48,191,96,44,G,N,1.5);H(c,s.task===0?'Question':s.task===1?'12, 8, 5':'Lesson idea',x,218,12,'center','Goldman');H(c,'Keyboard / files',x,261,11,'center')}if(i===1){R(c,x-51,194,102,54,W,N,1.5);for(let j=0;j<3;j++)R(c,x-42+j*29,203,25,14,j===1?B:G,N,.8);H(c,arr[2],x,267,11,'center');}if(i===2){R(c,x-55,191,110,70,B,N,1.5);L(c,x-38,205,x+38,205,1.5,N);L(c,x-38,217,x+24,217,1,N);L(c,x-38,229,x+34,229,1,N);H(c,arr[3],x,286,11,'center','Goldman')}});R(c,112,350,576,42,W,N,1.5);H(c,'SAFETY CHECK',132,376,12,'left','Goldman');H(c,'Verify sources · keep personal details private · check output before sharing',258,376,11);H(c,'Task: '+arr[0],112,420,12,'left','Goldman');break;}
default: headline(window.JEENIUS_LESSON.title,'Interactive example');
}
};
