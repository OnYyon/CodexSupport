/* Pure learning/battle state machine; no DOM or animation timers. */
(function(global){
'use strict';
const shuffle=(items,rng)=>{const a=items.slice();for(let i=a.length-1;i>0;i--){const j=Math.floor(rng()*(i+1));[a[i],a[j]]=[a[j],a[i]]}return a};
class JourneyEngine {
 constructor(stages,saved={},rng=Math.random){
  this.stages=stages;this.rng=rng;this.completed=Number.isInteger(saved.completed)?Math.max(0,Math.min(stages.length,saved.completed)):0;
  this.stage=Number.isInteger(saved.stage)?Math.max(0,Math.min(this.completed,stages.length-1,saved.stage)):Math.min(this.completed,stages.length-1);
  this.phase='intro';this.enemyHp=5;this.mistakes=0;this.queue=[];this.cursor=0;this.last=null;this.missed=[];this.report=[];
  if(Array.isArray(saved.report))this.report=saved.report.filter(id=>this.data.questions.some(q=>q.id===id));
 }
 get data(){return this.stages[this.stage]}
 get question(){return this.queue[this.cursor]||null}
 get lives(){return Math.max(0,2-this.mistakes)}
 get hits(){return 5-this.enemyHp}
 start(){if(this.phase!=='intro')return false;this.phase=this.completed===this.stages.length?'complete':'read';return true}
 openStage(stage){if(!Number.isInteger(stage)||stage<0||stage>=this.stages.length||stage>this.completed||['animation','approach','journey'].includes(this.phase))return false;this.stage=stage;this.phase='read';this.report=[];return true}
 begin(){
  if(this.phase!=='read')return false;
  const ordered=shuffle(this.data.questions,this.rng);ordered.sort((a,b)=>Number(this.report.includes(b.id))-Number(this.report.includes(a.id)));
  this.queue=ordered.map(q=>({...q,displayOptions:shuffle(q.options.map((label,id)=>({id,label})),this.rng)}));
  this.enemyHp=5;this.mistakes=0;this.cursor=0;this.last=null;this.missed=[];this.report=[];this.phase='approach';return true;
 }
 arrive(){if(this.phase!=='approach')return false;this.phase='battle';return true}
 answer(option){
  const q=this.question;if(this.phase!=='battle'||!q||!Number.isInteger(option)||option<0||option>=q.options.length)return null;
  const correct=option===q.answer;
  if(correct)this.enemyHp--;else{this.mistakes++;if(!this.missed.includes(q.id))this.missed.push(q.id)}
  this.last={correct,chosen:option,question:q,lethal:this.enemyHp===0,retreat:this.mistakes>=2};this.phase='animation';return this.last;
 }
 finishAnimation(){
  if(this.phase!=='animation')return null;
  if(this.mistakes>=2){this.phase='read';this.report=this.missed.slice();return 'review'}
  if(this.enemyHp===0){this.completed=Math.max(this.completed,this.stage+1);this.phase='victory';return 'victory'}
  this.phase='feedback';return 'feedback';
 }
 acknowledge(){if(this.phase!=='feedback')return false;this.cursor++;if(!this.question)throw new Error('Question bank exhausted');this.phase='battle';return true}
 next(){if(this.phase!=='victory')return false;if(this.stage===this.stages.length-1){this.phase='complete';return true}this.stage++;this.report=[];this.phase='journey';return true}
 arrivedNext(){if(this.phase!=='journey')return false;this.phase='read';return true}
 serialize(){return {version:1,completed:this.completed,stage:this.stage,report:this.report.slice()}}
}
global.JourneyEngine=JourneyEngine;
if(typeof module!=='undefined'&&module.exports)module.exports=JourneyEngine;
})(typeof globalThis!=='undefined'?globalThis:this);
