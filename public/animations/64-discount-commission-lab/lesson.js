window.JEENIUS_LESSON = {
  "num": 64,
  "slug": "discount-commission-lab",
  "title": "Discount and Commission Lab",
  "short": "Discount and Commission",
  "grade": "CLASS 8",
  "subject": "MATHEMATICS",
  "chapter": "Discount and Commission",
  "intro": "Run a shop sale. Change the marked price and discount to see the selling price. Commission is shown as a separate percentage of selling price for this example.",
  "kind": "discount",
  "controls": [
    {
      "key": "price",
      "label": "Marked price",
      "min": 500,
      "max": 5000,
      "step": 100,
      "value": 2000,
      "unit": " ₹",
      "decimals": 0
    },
    {
      "key": "discount",
      "label": "Discount",
      "min": 0,
      "max": 50,
      "step": 5,
      "value": 10,
      "unit": "%"
    },
    {
      "key": "commission",
      "label": "Commission rate",
      "min": 0,
      "max": 15,
      "step": 1,
      "value": 5,
      "unit": "%"
    }
  ],
};
window.JEENIUS_LESSON.draw = function(c,s,t,h,m){
const {N,B,G,W,INK,GREEN,RED,GOLD,H,L,R,C,E,A,TXT,clamp}=h;
const headline=(title,subtitle)=>{H(c,title,28,30,16,'left','Goldman');H(c,subtitle,28,51,11,'left','Saira','#52667d');L(c,28,67,772,67,1,N)};
switch(window.JEENIUS_LESSON.kind){
case 'discount':{headline('A SHOPPING DISCOUNT','Marked price − discount = selling price');R(c,60,118,210,230,B,N,2);R(c,86,148,158,151,W,N,2);H(c,'SALE',165,181,23,'center','Goldman');H(c,'ITEM',165,218,13,'center','Goldman');C(c,165,280,36,W,N,2);H(c,'₹',165,291,26,'center','Goldman');A(c,280,225,335,225,2,N);R(c,350,96,410,290,W,N,1.5);H(c,'RECEIPT',374,126,14,'left','Goldman');L(c,374,140,736,140,1,N);H(c,'Marked price',374,170,13);H(c,'₹'+s.price.toFixed(0),730,170,13,'right','Goldman');H(c,'Discount ('+s.discount+'%)',374,201,13);H(c,'− ₹'+(s.price*s.discount/100).toFixed(2),730,201,13,'right','Goldman');L(c,374,216,736,216,1,N,[3,3]);H(c,'SELLING PRICE',374,246,13,'left','Goldman');H(c,'₹'+(s.price*(1-s.discount/100)).toFixed(2),730,246,21,'right','Goldman');H(c,'Commission example ('+s.commission+'%)',374,290,12);H(c,'₹'+(s.price*(1-s.discount/100)*s.commission/100).toFixed(2),730,290,13,'right','Goldman');TXT(c,['Commission is calculated on the','selling price in this worked example.'],374,323,340,12,18);H(c,'Change the sliders to update the receipt.',60,389,11);break;}
default: headline(window.JEENIUS_LESSON.title,'Interactive example');
}
};
