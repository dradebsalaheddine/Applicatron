'use strict';
const {spawn}=require('node:child_process');const path=require('node:path');const fs=require('node:fs/promises');const readline=require('node:readline');
module.exports=function({app,ipcMain,dialog,win,trusted}){
 let child=null;const models=path.join(app.getPath('userData'),'mail-models');const names={MiniLM:'multilingual-minilm',Qwen3:'qwen3',SmolLM3:'smollm3'};
 const send=data=>{if(!win.isDestroyed())win.webContents.send('mail-event',data);};
 const guard=e=>{if(!trusted(e))throw Error('Untrusted sender');};
 async function state(){const result={};for(const [k,v] of Object.entries(names))result[k]=await fs.access(path.join(models,v,'.ready')).then(()=>true,()=>false);return result;}
 function launch(request){
  if(child)throw Error('An import or download is already running.');
  const exe=app.isPackaged?path.join(process.resourcesPath,'mail-runtime','Applicatron-Mail-Worker.exe'):(process.env.APPLICATRON_PYTHON||'python');
  child=spawn(exe,app.isPackaged?[]:[path.join(__dirname,'../tools/mail_worker.py')],{stdio:['pipe','pipe','pipe'],windowsHide:true,env:{...process.env,PYTHONUNBUFFERED:'1',PYTHONUTF8:'1',TOKENIZERS_PARALLELISM:'false',OMP_NUM_THREADS:'2',MKL_NUM_THREADS:'2'}});
  const running=child;let ended=false;let tail='';
  readline.createInterface({input:running.stdout}).on('line',line=>{try{const data=JSON.parse(line);if(['done','error'].includes(data.type))ended=true;send(data);}catch{}});
  running.stderr.on('data',b=>{tail=(tail+b.toString()).slice(-4000);});
  running.on('error',e=>send({type:'error',message:'Mail runtime could not start: '+e.message}));
  running.on('close',code=>{if(child===running)child=null;if(!ended)send({type:code===0?'done':'error',message:code===0?'Finished':'Worker stopped. '+tail});send({type:'idle'});});
  running.stdin.end(JSON.stringify({...request,models})+'\n');return true;
 }
 ipcMain.handle('mail-state',async e=>{guard(e);return state();});
 ipcMain.handle('mail-download',async(e,model)=>{guard(e);if(!names[model])throw Error('Unknown model');return launch({action:'download',model});});
 ipcMain.handle('mail-start',async(e,options)=>{guard(e);if(child)throw Error('Task already running');if(!options||!['Auto','CPU','CUDA'].includes(options.device)||!['','Qwen3','SmolLM3'].includes(options.large))throw Error('Invalid settings');
  const ready=await state();for(const n of [options.mini?'MiniLM':'',options.large].filter(Boolean))if(!ready[n])throw Error('Download '+n+' first using the model buttons.');
  const pick=await dialog.showOpenDialog(win,{title:'Choose extracted Takeout mailbox',properties:['openFile'],filters:[{name:'Mailbox',extensions:['mbox']}]});if(pick.canceled)return false;
  const report=await dialog.showSaveDialog(win,{title:'Save private import report',defaultPath:'Applicatron-import-'+Date.now()+'.html',filters:[{name:'HTML',extensions:['html']}]});if(report.canceled)return false;
  return launch({action:'scan',path:pick.filePaths[0],report:report.filePath,mini:!!options.mini,large:options.large,device:options.device});
 });
 function cancel(){if(!child)return false;const p=child;if(process.platform==='win32')spawn('taskkill',['/pid',String(p.pid),'/T','/F'],{windowsHide:true});else p.kill('SIGKILL');return true;}
 ipcMain.handle('mail-cancel',e=>{guard(e);return cancel();});app.on('before-quit',cancel);
};
