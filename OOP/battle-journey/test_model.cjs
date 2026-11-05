'use strict';
const assert=require('node:assert/strict');const fs=require('node:fs');const path=require('node:path');
const Engine=require('./model.js');
const html=fs.readFileSync(path.join(__dirname,'../OOP_CPP20_Battle_Journey.html'),'utf8');
const data=JSON.parse(html.match(/<script id="journey-data" type="application\/json">([\s\S]*?)<\/script>/)[1]);
let seed=7;const rng=()=>{seed=(seed*1664525+1013904223)>>>0;return seed/4294967296};
const fresh=()=>new Engine(data.stages,{},rng);
function go(e){assert.equal(e.start(),true);assert.equal(e.phase,'read');assert.equal(e.begin(),true);assert.equal(e.arrive(),true)}
function hit(e,good=true){const q=e.question;const choice=good?q.answer:(q.answer+1)%q.options.length;assert.ok(e.answer(choice));assert.equal(e.answer(choice),null,'double-click must not change score');return e.finishAnimation()}
assert.equal(data.stages.length,8);for(const s of data.stages){assert.equal(s.questions.length,6);for(const q of s.questions){assert.ok(Number.isInteger(q.answer)&&q.answer>=0&&q.answer<q.options.length);assert.ok(s.sections.some(x=>x.topic===q.topic),'review target must exist')}}
{
 const e=fresh();go(e);assert.equal(e.openStage(1),false,'next chapter locked');for(let i=0;i<5;i++){const r=hit(e);if(i<4){assert.equal(r,'feedback');assert.equal(e.completed,0);e.acknowledge()}else assert.equal(r,'victory')}assert.equal(e.enemyHp,0);assert.equal(e.completed,1);assert.equal(e.phase,'victory');assert.equal(e.next(),true);assert.equal(e.phase,'journey');assert.equal(e.stage,1);assert.equal(e.arrivedNext(),true);assert.equal(e.phase,'read');
}
{
 const e=fresh();go(e);const first=e.question.id;assert.equal(hit(e,false),'feedback');assert.equal(e.lives,1);assert.equal(e.enemyHp,5);e.acknowledge();const second=e.question.id;assert.equal(hit(e,false),'review');assert.equal(e.phase,'read');assert.equal(e.completed,0);assert.deepEqual(new Set(e.report),new Set([first,second]));const restored=new Engine(data.stages,e.serialize(),rng);restored.start();assert.equal(restored.phase,'read');assert.deepEqual(restored.report,e.report);assert.equal(e.begin(),true);assert.equal(e.mistakes,0);assert.equal(e.enemyHp,5);assert.ok([first,second].includes(e.question.id),'retry prioritizes missed rules');
}
{
 const e=fresh();go(e);hit(e,false);e.acknowledge();for(let i=0;i<5;i++){const result=hit(e,true);if(i<4)e.acknowledge();else assert.equal(result,'victory')}assert.equal(e.completed,1,'one mistake still permits victory');assert.equal(e.cursor,5,'six distinct questions suffice');
}
{
 const e=fresh();e.start();for(let stage=0;stage<8;stage++){assert.equal(e.stage,stage);assert.equal(e.begin(),true);e.arrive();for(let hitIndex=0;hitIndex<5;hitIndex++){hit(e);if(hitIndex<4)e.acknowledge()}assert.equal(e.completed,stage+1);e.next();if(stage<7)e.arrivedNext()}assert.equal(e.phase,'complete');assert.equal(e.completed,8);const restored=new Engine(data.stages,e.serialize(),rng);restored.start();assert.equal(restored.phase,'complete');
}
{
 const e=new Engine(data.stages,{completed:999,stage:999,report:['does-not-exist']},rng);assert.equal(e.completed,8);assert.equal(e.stage,7);assert.deepEqual(e.report,[]);const a=fresh();assert.equal(a.begin(),false);assert.equal(a.arrive(),false);assert.equal(a.finishAnimation(),null);assert.equal(a.answer(0),null);go(a);assert.equal(a.answer(-1),null);assert.equal(a.answer(999),null);assert.equal(a.answer(NaN),null);
}
for(let i=0;i<200;i++){
 const e=fresh();go(e);let processed=0;while(e.phase==='battle'){const correct=rng()>.28;const result=hit(e,correct);processed++;if(result==='feedback')e.acknowledge();assert.ok(processed<=6,'battle must terminate without exhausting bank')}assert.ok(['read','victory'].includes(e.phase));assert.ok(e.enemyHp>=0&&e.enemyHp<=5);assert.ok(e.mistakes<=2);
}
console.log('PASS: 48 questions and review targets; win, defeat, retry, one-error win, eight chapters, persistence, invalid input, double-click guard, 200 randomized battles.');
