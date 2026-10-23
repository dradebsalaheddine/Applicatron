'use strict';
const {app,BrowserWindow,Menu,protocol,net,session,shell,dialog,ipcMain}=require('electron');
const path=require('node:path');const fs=require('node:fs/promises');const {pathToFileURL}=require('node:url');
const {safeExternal,assetName}=require('./policy.cjs');
app.setName('Applicatron 3000');
protocol.registerSchemesAsPrivileged([{scheme:'applicatron',privileges:{standard:true,secure:true,supportFetchAPI:true}}]);
let win;
const trusted=event=>event.sender===win?.webContents&&event.senderFrame?.url==='applicatron://app/index.html';
async function openExternal(url){if(!safeExternal(url))return;const result=await dialog.showMessageBox(win,{type:'question',title:'Open application link?',message:'Open this link in your default browser?',detail:url,buttons:['Cancel','Open link'],defaultId:0,cancelId:0});if(result.response===1)await shell.openExternal(url);}
if(!app.requestSingleInstanceLock()){app.quit();}else{
 app.on('second-instance',()=>{if(win){if(win.isMinimized())win.restore();win.focus();}});
 app.whenReady().then(()=>{
  protocol.handle('applicatron',request=>{const name=assetName(request.url);if(!name)return new Response('Not found',{status:404});return net.fetch(pathToFileURL(path.join(__dirname,'../web',name)).toString());});
  session.defaultSession.setPermissionRequestHandler((_wc,_permission,callback)=>callback(false));
  session.defaultSession.setPermissionCheckHandler(()=>false);
  Menu.setApplicationMenu(null);
  win=new BrowserWindow({width:1420,height:960,minWidth:800,minHeight:600,show:false,backgroundColor:'#f5f5f0',title:'Applicatron 3000',webPreferences:{preload:path.join(__dirname,'preload.cjs'),nodeIntegration:false,contextIsolation:true,sandbox:true,webSecurity:true}});
  win.webContents.on('will-navigate',(event,url)=>{if(url!=='applicatron://app/index.html'){event.preventDefault();openExternal(url).catch(()=>{});}});
  win.webContents.setWindowOpenHandler(({url})=>{openExternal(url).catch(()=>{});return {action:'deny'};});
  ipcMain.handle('save-pdf',async event=>{if(!trusted(event))throw Error('Untrusted sender');const picked=await dialog.showSaveDialog(win,{title:'Save application overview',defaultPath:'applications.pdf',filters:[{name:'PDF',extensions:['pdf']}]});if(picked.canceled)return false;const bytes=await win.webContents.printToPDF({printBackground:true,pageSize:'A4',landscape:true});await fs.writeFile(picked.filePath,bytes);return true;});
  win.once('ready-to-show',()=>win.show());win.loadURL('applicatron://app/index.html');
 });
 app.on('window-all-closed',()=>app.quit());
}
