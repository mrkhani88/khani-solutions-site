export const defaults = {racks:10,rackKW:100,deltaT:10,headerD:125,branchD:40,headerL:40,branchL:20,rackDP:100,hxDP:45,filterDP:20,valveDP:15,margin:15,efficiency:65};
export function pipeLoss(flow,Dmm,L,K){
 const rho=992.2,mu=.000653,eps=15e-6,D=Dmm/1000;
 const v=4*flow/(Math.PI*D*D),Re=rho*v*D/mu;
 const f=Re<2300?64/Re:Math.pow(-1.8*Math.log10(Math.pow(eps/D/3.7,1.11)+6.9/Re),-2);
 return {velocity:v,Re,DarcyF:f,dp:(f*L/D+K)*rho*v*v/2000};
}
export function calculate(p){
 const ranges={racks:[1,100],rackKW:[1,1000],deltaT:[2,30],headerD:[1,1000],branchD:[1,1000],headerL:[0,500],branchL:[0,200],rackDP:[0,1500],hxDP:[0,1000],filterDP:[0,500],valveDP:[0,500],margin:[0,50],efficiency:[10,90]};
 for(const [key,[lo,hi]] of Object.entries(ranges))if(!Number.isFinite(p[key])||p[key]<lo||p[key]>hi)throw new Error(`Invalid input: ${key}`);
 if(!Number.isInteger(p.racks))throw new Error('Rack count must be a whole number.');
 const loadKW=p.racks*p.rackKW,mass=loadKW*1000/(4179*p.deltaT),q=mass/992.2;
 const header=pipeLoss(q,p.headerD,p.headerL,6),branch=pipeLoss(q/p.racks,p.branchD,p.branchL,8);
 const losses=[['Common header pipes & fittings',header.dp],['One rack branch pipes & fittings',branch.dp],['Rack internal path · assumed',p.rackDP],['CDU exchanger · assumed',p.hxDP],['Dirty filter allowance · assumed',p.filterDP],['Branch valve · assumed',p.valveDP]];
 const raw=losses.reduce((s,[,v])=>s+v,0),dp=raw*(1+p.margin/100);
 return {status:'Algebraic presizing only; not a solved network or validated equipment selection',inputs:{...p},properties:{rho_kg_m3:992.2,cp_J_kgK:4179,mu_Pas:.000653,roughness_m:15e-6},loadKW,mass,q,header,branch,losses,raw,dp,head:dp*1000/(992.2*9.80665),power:q*dp/(p.efficiency/100),individualDutyPumpM3h:q*3600/2};
}
if(typeof document!=='undefined'){
 const form=document.querySelector('#dc-inputs');
 if(form){
  const get=id=>document.getElementById(id),fmt=(x,n=1)=>x.toLocaleString('en-US',{minimumFractionDigits:n,maximumFractionDigits:n});
  let latest;
  function update(){
   try{
    if(!form.checkValidity())throw new Error('Enter values within the displayed ranges.');
    latest=calculate(Object.fromEntries(Object.keys(defaults).map(k=>[k,Number(form.elements[k].value)])));
    get('dc-input-status').textContent='';get('dc-export').disabled=false;
    get('dc-load').textContent=fmt(latest.loadKW/1000,2)+' MW';get('dc-flow').textContent=fmt(latest.q*1000,2)+' L/s';
    get('dc-rack-flow').textContent=fmt(latest.q*60000/latest.inputs.racks)+' L/min';
    get('dc-pressure').textContent=fmt(latest.dp)+' kPa';get('dc-head').textContent=fmt(latest.head,2)+' m';get('dc-power').textContent=fmt(latest.power,2)+' kW';
    get('dc-pump-share').textContent=`Three 50% pumps: each duty pump supplies ${fmt(latest.individualDutyPumpM3h)} m³/h at ${fmt(latest.head)} m head; two run and one is standby. This is a duty target, not a selected pump curve.`;
    get('dc-loss-table').replaceChildren();get('dc-loss-bars').replaceChildren();
    latest.losses.forEach(([name,value],i)=>{
     const tr=document.createElement('tr'),th=document.createElement('th'),td=document.createElement('td');th.scope='row';th.textContent=name;td.textContent=fmt(value);tr.append(th,td);get('dc-loss-table').append(tr);
     const bar=document.createElement('span');bar.className='dc-loss-segment';bar.style.width=(value/Math.max(latest.raw,.0001)*100)+'%';bar.style.background=['#087eac','#1c9cb3','#c9733c','#685aa0','#677b8c','#b24653'][i];bar.title=name+': '+fmt(value)+' kPa';get('dc-loss-bars').append(bar);
    });
    get('dc-loss-total').textContent=`Total ${fmt(latest.raw)} kPa + ${fmt(latest.inputs.margin,0)}% pressure margin = ${fmt(latest.dp)} kPa.`;
    let note=`Header velocity ${fmt(latest.header.velocity,2)} m/s; branch velocity ${fmt(latest.branch.velocity,2)} m/s.`;
    if(Math.max(latest.header.velocity,latest.branch.velocity)>3)note+=' High velocity: investigate larger bores, fittings and noise/erosion limits. This is a screening flag, not a code limit.';
    if([latest.header.Re,latest.branch.Re].some(r=>r>=2300&&r<4000))note+=' Transitional Reynolds number: friction estimate requires sensitivity.';
    get('dc-velocity').textContent=note;
   }catch(error){get('dc-input-status').textContent=error.message+' Results retain the last valid estimate.';get('dc-export').disabled=true;}
  }
  form.addEventListener('input',update);form.addEventListener('change',update);form.addEventListener('submit',e=>e.preventDefault());
  document.querySelectorAll('[data-preset]').forEach(button=>button.addEventListener('click',()=>{
   const p={...defaults};if(button.dataset.preset==='low-loss'){p.headerD=150;p.branchD=50;}if(button.dataset.preset==='delta5')p.deltaT=5;
   Object.entries(p).forEach(([k,v])=>{form.elements[k].value=v;});update();
  }));
  get('dc-export').addEventListener('click',()=>{if(!latest||get('dc-export').disabled)return;const url=URL.createObjectURL(new Blob([JSON.stringify({...latest,exportedAt:new Date().toISOString()},null,2)],{type:'application/json'}));const a=document.createElement('a');a.href=url;a.download='data-center-presizing.json';document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);});
  update();
 }
}
