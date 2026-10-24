'use strict';
// One atomic document: changing profiles never overwrites a different profile's list.
(function(root){
 const KEY='applicatron-profiles-v1',LEGACY='applicatron-3000-v1';
 function create(storage,validate,uuid){
  function name(value){const n=String(value||'').trim();if(!n||n.length>80)throw Error('Use a profile name of 1–80 characters.');return n;}
  function read(){
   const raw=storage.getItem(KEY);
   if(raw){const d=JSON.parse(raw);if(d.version!==1||!Array.isArray(d.profiles)||!d.profiles.length)throw Error('Invalid profiles backup.');const ids=new Set();for(const p of d.profiles){if(typeof p.id!=='string'||!p.id||ids.has(p.id))throw Error('Invalid profile ID.');ids.add(p.id);p.name=name(p.name);p.applications=validate(p.applications);p.settings=p.settings&&typeof p.settings==='object'?p.settings:{};}if(!ids.has(d.active))throw Error('Active profile is missing.');return d;}
   const old=storage.getItem(LEGACY);const d={version:1,active:'default',profiles:[{id:'default',name:'Default',applications:old?validate(JSON.parse(old)):[],settings:{}}]};
   storage.setItem(KEY,JSON.stringify(d));return d; // Retain the original key as a migration fallback.
  }
  let data=read();
  const active=()=>data.profiles.find(p=>p.id===data.active);
  function change(fn){if(storage.getItem(KEY)!==JSON.stringify(data))throw Error('Profiles changed in another window. Reload before saving.');const next=structuredClone(data);fn(next);storage.setItem(KEY,JSON.stringify(next));data=next;return active();}
  function unique(d,n,except){if(d.profiles.some(p=>p.id!==except&&p.name.toLowerCase()===n.toLowerCase()))throw Error('A profile with that name already exists.');}
  return {key:KEY,get data(){return structuredClone(data);},get current(){return structuredClone(active());},reload(){data=read();return this.current;},
   save(items){const clean=validate(items);return change(d=>{d.profiles.find(p=>p.id===d.active).applications=clean;});},
   settings(value){return change(d=>{d.profiles.find(p=>p.id===d.active).settings=structuredClone(value);});},
   switch(id){return change(d=>{if(!d.profiles.some(p=>p.id===id))throw Error('Profile no longer exists.');d.active=id;});},
   add(value,copy=false){const n=name(value);return change(d=>{unique(d,n);const source=d.profiles.find(p=>p.id===d.active);const id=uuid();d.profiles.push({id,name:n,applications:copy?structuredClone(source.applications):[],settings:copy?structuredClone(source.settings):{}});d.active=id;});},
   rename(value){const n=name(value);return change(d=>{unique(d,n,d.active);d.profiles.find(p=>p.id===d.active).name=n;});},
   remove(){return change(d=>{if(d.profiles.length===1)throw Error('Keep at least one profile.');d.profiles=d.profiles.filter(p=>p.id!==d.active);d.active=d.profiles[0].id;});}
  };
 }
 const api={create,KEY};if(typeof module==='object')module.exports=api;else root.ProfileStore=api;
})(globalThis);
