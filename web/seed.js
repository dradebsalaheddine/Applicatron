// A clean installation starts empty. These examples are fictional and opt-in.
const SEED = [];
function makeDemo(){
 const date=offset=>{const d=new Date();d.setDate(d.getDate()+offset);return [d.getFullYear(),String(d.getMonth()+1).padStart(2,'0'),String(d.getDate()).padStart(2,'0')].join('-')};
 return [
  ['Moon Cheese Labs','Junior Quality Astronaut',-5,'Applied',14],
  ['Bureau of Mild Inconveniences','Process Improvement Intern',-20,'Applied',10],
  ['Definitely Not Three Raccoons','Security Analyst',-12,'Interview',14],
  ['Cloud Castle Collective','Infrastructure Intern',-3,'In progress',''],
  ['Intergalactic Stapler Co.','Office Technology Intern',-25,'Rejected','']
 ].map(([company,role,offset,status,windowDays],i)=>({id:'demo-'+i,company,role,applied:date(offset),status,windowDays:String(windowDays),windowEnd:'',followUp:i===1?date(0):'',location:'Fictional example',url:'',notes:'Demo data only. No real application or employer is represented.'}));
}
