// Independent offline illustrations. Prices are synthetic, not exchange observations.
export const backtestBars = [
  {open:100,close:100},{open:101,close:102},{open:103,close:101},{open:102,close:104},
  {open:105,close:103},{open:102,close:100},{open:99,close:98},{open:101,close:101},
];
export function runCostExample(bps=10){
  if(!Number.isFinite(bps)||bps<0||bps>1000)throw new RangeError('Invalid cost');
  const c=bps/10000;
  let cash=10000,shares=0,grossCash=10000,grossShares=0;
  const rows=backtestBars.map((bar,i)=>{
    if(i===3){shares=cash/(bar.open*(1+c));cash=0;grossShares=grossCash/bar.open;grossCash=0;}
    if(i===6){cash=shares*bar.open*(1-c);shares=0;grossCash=grossShares*bar.open;grossShares=0;}
    return {bar:i+1,net:cash+shares*bar.open,gross:grossCash+grossShares*bar.open,cash,shares};
  });
  return {rows,final:rows.at(-1).net,gross:rows.at(-1).gross,benchmark:10000/(102*(1+c))*101*(1-c)};
}
export function drawdownExample(lossPercent=25,recoveryPercent=20){
  if(lossPercent<0||lossPercent>=100||recoveryPercent<0)throw new RangeError('Invalid scenario');
  const bottom=120*(1-lossPercent/100);
  const wealth=[100,120,bottom,bottom*(1+recoveryPercent/100)];
  let peak=wealth[0];const drawdowns=wealth.map(value=>{peak=Math.max(peak,value);return value/peak-1;});
  return {wealth,drawdowns,maxDrawdown:Math.min(...drawdowns),requiredRecovery:lossPercent/(100-lossPercent)*100};
}
export function orderExample(events){
  const seen=new Map();let cash=2000,quantity=0,totalFee=0;
  const audit=[];
  for(const event of events){
    if(seen.has(event.id)){if(seen.get(event.id)!==JSON.stringify(event))throw new Error('Conflicting fill ID');audit.push({...event,status:'duplicate',cash,quantity});continue;}
    if(!(event.quantity>0)||!(event.price>0)||event.fee<0||quantity+event.quantity>10)throw new Error('Invalid fill');
    const cost=event.quantity*event.price+event.fee;
    if(cost>cash)throw new Error('Insufficient cash');
    cash-=cost;quantity+=event.quantity;totalFee+=event.fee;seen.set(event.id,JSON.stringify(event));
    audit.push({...event,fillQuantity:event.quantity,status:'applied',cash,quantity});
  }
  return {cash,quantity,totalFee,audit,state:quantity===10?'FILLED':quantity?'PARTIAL':'ACCEPTED'};
}
