/**
 * Electron preload — context bridge.
 * Runs in the renderer process with Node.js access disabled.
 * Only exposes the minimal API surface the UI needs.
 */
const { contextBridge, ipcRenderer } = require("electron");

contextBridge.exposeInMainWorld("athena", {
  quit:        ()         => ipcRenderer.send("app-quit"),
  minimize:    ()         => ipcRenderer.send("app-minimize"),
  onStatus:    (callback) => ipcRenderer.on("status", (_e, msg) => callback(msg)),
  removeStatus:(callback) => ipcRenderer.removeListener("status", callback),
});
