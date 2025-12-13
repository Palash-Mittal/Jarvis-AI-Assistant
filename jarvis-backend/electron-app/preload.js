const { contextBridge, ipcRenderer } = require("electron");

console.log("PRELOAD LOADED");

contextBridge.exposeInMainWorld("jarvis", {
  send: (msg) => {
    console.log("PRELOAD → MAIN:", msg);
    ipcRenderer.send("send-to-jarvis", msg);
  },

  onResponse: (callback) => {
    ipcRenderer.on("jarvis-response", (event, data) => {
      console.log("MAIN → PRELOAD:", data);
      callback(data);
    });
  }
});
