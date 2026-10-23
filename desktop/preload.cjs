'use strict';
const {contextBridge,ipcRenderer}=require('electron');
contextBridge.exposeInMainWorld('desktop',{savePDF:()=>ipcRenderer.invoke('save-pdf')});
