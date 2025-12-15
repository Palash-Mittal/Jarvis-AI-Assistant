const { app, BrowserWindow, ipcMain } = require("electron");
const { spawn } = require("child_process");

let jarvis;
let win;

function createWindow() {
  win = new BrowserWindow({
    width: 1000,
    height: 700,
    webPreferences: {
      preload: __dirname + "/preload.js"
    }
  });

  win.loadFile("index.html");
}

app.whenReady().then(() => {
  createWindow();

  // START PYTHON
  jarvis = spawn("python", ["../backend/main.py"]);

  jarvis.stdout.on("data", (data) => {
    const text = data.toString().trim();
    console.log("PYTHON → ELECTRON:", text);

    // Send to renderer
    win.webContents.send("jarvis-response", text);
  });

  jarvis.stderr.on("data", (data) => {
    console.log("PYTHON ERROR:", data.toString());
  });
});

// RECEIVE from renderer, SEND to Python
ipcMain.on("send-to-jarvis", (event, message) => {
  console.log("ELECTRON → PYTHON:", message);
  jarvis.stdin.write(JSON.stringify({ command: message }) + "\n");
});
