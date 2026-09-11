// Adapted from React Bits Stepper-JS-CSS. Semantic quiz progress and static fallback.
import React,{useState,Children,useRef,useEffect} from 'react';
import {motion,AnimatePresence,useReducedMotion} from 'motion/react';
import './Stepper.css';
export default function Stepper({children,initialStep=1,onStepChange=()=>{},onFinalStepCompleted=()=>{},backButtonProps={},nextButtonProps={},backButtonText='Back',nextButtonText='Continue',completeButtonText='Complete'}) {
  const [currentStep,setCurrentStep]=useState(initialStep),[direction,setDirection]=useState(1);
  const steps=Children.toArray(children),totalSteps=steps.length,reduced=useReducedMotion();
  const contentRef=useRef(null),first=useRef(true);
  useEffect(()=>{if(first.current){first.current=false;return;}contentRef.current?.focus({preventScroll:true});},[currentStep]);
  const updateStep=n=>{if(n>totalSteps){onFinalStepCompleted();return;}setDirection(n>currentStep?1:-1);setCurrentStep(n);onStepChange(n);};
  return <div className="outer-container"><div className="step-circle-container">
    <ol className="step-indicator-row" aria-label="ความคืบหน้าแบบทบทวน">{steps.map((_,index)=><li key={index} aria-current={index+1===currentStep?'step':undefined}><span className={'step-indicator-inner '+(index+1<=currentStep?'active':'')}>{index+1}</span><span className="sr-only">{'ข้อ '+(index+1)}</span>{index<totalSteps-1&&<span className="step-connector"><motion.span className="step-connector-inner" initial={false} animate={{width:currentStep>index+1?'100%':'0%'}} transition={{duration:reduced?0:.2}}/></span>}</li>)}</ol>
    <div className="step-content-default" ref={contentRef} tabIndex={-1}><AnimatePresence initial={false} mode="wait"><motion.div key={currentStep} initial={reduced?false:{opacity:0,x:direction*10}} animate={{opacity:1,x:0}} exit={reduced?{opacity:1}:{opacity:0,x:-direction*10}} transition={{duration:reduced?0:.12}}>{steps[currentStep-1]}</motion.div></AnimatePresence></div>
    <div className="footer-nav"><button type="button" className="back-button" onClick={()=>updateStep(currentStep-1)} disabled={currentStep===1} {...backButtonProps}>{backButtonText}</button><button type="button" className="next-button" onClick={()=>updateStep(currentStep+1)} {...nextButtonProps}>{currentStep===totalSteps?completeButtonText:nextButtonText}</button></div>
  </div></div>;
}
export function Step({children}){return <div className="step-default">{children}</div>;}
