'use strict';
const {contextBridge,ipcRenderer}=require('electron');
contextBridge.exposeInMainWorld('desktop',{savePDF:()=>ipcRenderer.invoke('save-pdf'),mailState:()=>ipcRenderer.invoke('mail-state'),mailDownload:model=>ipcRenderer.invoke('mail-download',model),mailStart:options=>ipcRenderer.invoke('mail-start',options),mailCancel:()=>ipcRenderer.invoke('mail-cancel'),onMail:callback=>{const listener=(_e,data)=>callback(data);ipcRenderer.on('mail-event',listener);return ()=>ipcRenderer.removeListener('mail-event',listener);}});
