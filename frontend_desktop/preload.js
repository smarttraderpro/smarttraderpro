// preload.js (Optional, for secure IPC with Electron Main Process)
const { contextBridge, ipcRenderer } = require('electron');

// Expose protected methods that allow the renderer process to use
// the ipcRenderer without exposing the entire object.
// This is a more secure way to handle inter-process communication.
contextBridge.exposeInMainWorld(
  'myAPI', // This will be window.myAPI in the renderer process
  {
    // Example: send a message to main process
    // send: (channel, data) => {
    //   // Whitelist channels
    //   let validChannels = ['toMain'];
    //   if (validChannels.includes(channel)) {
    //     ipcRenderer.send(channel, data);
    //   }
    // },
    // Example: receive a message from main process
    // receive: (channel, func) => {
    //   let validChannels = ['fromMain'];
    //   if (validChannels.includes(channel)) {
    //     // Deliberately strip event as it includes `sender`
    //     ipcRenderer.on(channel, (event, ...args) => func(...args));
    //   }
    // }
    // Example: simple function call to main process
    // doSomething: () => ipcRenderer.invoke('do-something')
  }
);

console.log('Preload script executed.');
