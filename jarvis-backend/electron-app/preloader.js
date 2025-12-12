const { contextBridge, ipcRenderer } = require("electron");

contextBridge.exposeInMainWorld("jarvis", {
  send: (msg) => ipcRenderer.send("send-to-jarvis", msg),
  onResponse: (cb) => ipcRenderer.on("jarvis-response", (event, data) => cb(data))
});
