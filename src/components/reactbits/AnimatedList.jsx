// Adapted from React Bits AnimatedList-JS-CSS. Local focus; no global key trap.
import {useRef,useState} from 'react';
import {motion,useInView,useReducedMotion} from 'motion/react';
import './AnimatedList.css';
function AnimatedItem({children,index}) {
  const ref=useRef(null),inView=useInView(ref,{amount:0.2,once:true}),reduced=useReducedMotion();
  return <motion.li ref={ref} data-index={index} initial={false} animate={{y:reduced||inView?0:5,opacity:1}} transition={{duration:reduced?0:.18,delay:reduced?0:Math.min(index*.02,.12)}}>{children}</motion.li>;
}
export default function AnimatedList({items=[],onItemSelect,renderItem,label='จุดเปลี่ยนสถานะเป้าหมาย',className=''}) {
  const [selected,setSelected]=useState(-1);
  return <div className={'scroll-list-container '+className}><ul className="scroll-list" aria-label={label}>{items.map((item,index)=><AnimatedItem key={index} index={index}>{renderItem?renderItem(item,index):<button type="button" aria-pressed={selected===index} className={'item '+(selected===index?'selected':'')} onClick={()=>{setSelected(index);onItemSelect?.(item,index);}}>{item}</button>}</AnimatedItem>)}</ul></div>;
}
