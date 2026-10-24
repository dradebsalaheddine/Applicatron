'use strict';
const allowed=new Set(['index.html','style.css','app.js','seed.js','core.js','mail-ui.js']);
function safeExternal(raw){try{const u=new URL(raw);return ['https:','http:'].includes(u.protocol)&&!u.username&&!u.password;}catch{return false;}}
function assetName(raw){try{const u=new URL(raw);if(u.protocol!=='applicatron:'||u.hostname!=='app'||u.search||u.hash)return null;const name=decodeURIComponent(u.pathname).replace(/^\//,'');return allowed.has(name)?name:null;}catch{return null;}}
module.exports={safeExternal,assetName};
