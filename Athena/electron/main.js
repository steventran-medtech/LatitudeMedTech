/**
 * Latitude MedTech — Athena Electron Main Process
 * =================================================
 * Single-instance desktop app. Starts FastAPI + Vite as hidden processes.
 * No visible CMD windows. Lives in system tray. Handles graceful shutdown.
 */

const { app, BrowserWindow, Tray, Menu, nativeImage, ipcMain, shell, dialog } = require("electron");
const { spawn, execSync } = require("child_process");
const path = require("path");
const http = require("http");
const fs   = require("fs");

// ── Single-instance lock — must run BEFORE app.whenReady ────────────────────
const gotLock = app.requestSingleInstanceLock();
if (!gotLock) {
  // Another instance is running — bring it to front and exit this one
  app.quit();
  process.exit(0);
}

// ── Paths ─────────────────────────────────────────────────────────────────────
const ROOT         = path.join(__dirname, "..");
const VENV_PY      = path.join(ROOT, "voice", "venv", "Scripts", "python.exe");
const SERVER_PY    = path.join(ROOT, "ui", "backend", "server.py");
const FRONTEND_DIR = path.join(ROOT, "ui", "frontend");
const NODE_EXE     = process.execPath.replace("electron.exe", "node.exe");
const VITE_BIN     = path.join(FRONTEND_DIR, "node_modules", ".bin", "vite.cmd");
const BACKEND_URL  = "http://127.0.0.1:8000";
const FRONTEND_URL = "http://localhost:3000";

// ── State ─────────────────────────────────────────────────────────────────────
let mainWindow   = null;
let tray         = null;
let backendProc  = null;
let frontendProc = null;
let isQuitting   = false;

// ── Helpers ───────────────────────────────────────────────────────────────────

function log(msg) {
  const ts = new Date().toISOString().slice(11, 19);
  console.log(`[${ts}] ${msg}`);
}

function killOrphans() {
  // Kill any leftover python/node processes from previous runs
  try { execSync("taskkill /F /IM python.exe /T >nul 2>&1", { windowsHide: true }); } catch {}
  try { execSync("taskkill /F /IM node.exe /T >nul 2>&1",   { windowsHide: true }); } catch {}
}

function waitForHttp(url, maxMs = 35000) {
  return new Promise((resolve, reject) => {
    const start    = Date.now();
    const interval = setInterval(() => {
      http.get(url, () => {
        clearInterval(interval);
        resolve();
      }).on("error", () => {
        if (Date.now() - start > maxMs) {
          clearInterval(interval);
          reject(new Error(`Timeout waiting for ${url}`));
        }
      });
    }, 700);
  });
}

function spawnHidden(exe, args, cwd, label) {
  const proc = spawn(exe, args, {
    cwd,
    windowsHide: true,   // critical — prevents CMD window
    detached:    false,
    shell:       false,  // never use shell — avoids CMD host window
    stdio:       ["ignore", "pipe", "pipe"],
    env:         { ...process.env, PYTHONUNBUFFERED: "1", BROWSER: "none" },
  });
  proc.stdout?.on("data", d => log(`[${label}] ${d.toString().trim().slice(0, 200)}`));
  proc.stderr?.on("data", d => log(`[${label}] ${d.toString().trim().slice(0, 200)}`));
  proc.on("exit", code => {
    log(`[${label}] exited (${code})`);
    // If backend exits and we're not quitting intentionally → quit the app
    if (!isQuitting && label === "backend") {
      isQuitting = true;
      app.quit();
    }
  });
  return proc;
}

// ── Splash window ─────────────────────────────────────────────────────────────

function createSplash() {
  const w = new BrowserWindow({
    width: 420, height: 280, frame: false,
    resizable: false, center: true, transparent: false,
    alwaysOnTop: true,
    webPreferences: { nodeIntegration: false, contextIsolation: true },
  });
  const html = `<!DOCTYPE html><html><head><meta charset="UTF-8"/>
  <style>
    *{margin:0;padding:0;box-sizing:border-box}
    body{background:#0A2540;color:#fff;font-family:-apple-system,sans-serif;
         height:280px;display:flex;flex-direction:column;align-items:center;
         justify-content:center;gap:14px;user-select:none}
    .brand{font-size:10px;letter-spacing:.22em;color:rgba(255,255,255,.35);text-transform:uppercase}
    .name{font-size:34px;color:#fff;font-weight:300;letter-spacing:.04em}
    .sub{font-size:10px;color:rgba(255,255,255,.35);letter-spacing:.08em}
    .bar{width:180px;height:2px;background:rgba(255,255,255,.1);border-radius:1px;overflow:hidden}
    .fill{height:100%;background:#C4922A;border-radius:1px;animation:ld 2s ease-in-out infinite}
    @keyframes ld{0%{width:0}60%{width:80%}100%{width:100%}}
  </style></head>
  <body>
    <div class="brand">Latitude MedTech</div>
    <div class="name">Athena</div>
    <div class="sub">AI OPERATING SYSTEM · SAN DIEGO</div>
    <div class="bar"><div class="fill"></div></div>
  </body></html>`;
  w.loadURL("data:text/html;charset=utf-8," + encodeURIComponent(html));
  return w;
}

// ── Main window ───────────────────────────────────────────────────────────────

function createMainWindow() {
  mainWindow = new BrowserWindow({
    width: 1440, height: 900, minWidth: 1024, minHeight: 680,
    title: "Athena — Latitude MedTech",
    frame: true, show: false,
    webPreferences: {
      preload: path.join(__dirname, "preload.js"),
      contextIsolation: true, nodeIntegration: false,
      sandbox: true, webSecurity: true,
    },
  });

  mainWindow.loadURL(FRONTEND_URL);

  mainWindow.on("close", e => {
    if (!isQuitting) {
      e.preventDefault();
      mainWindow.hide(); // minimise to tray
    }
  });

  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    shell.openExternal(url);
    return { action: "deny" };
  });
}

// ── Tray ──────────────────────────────────────────────────────────────────────

function createTray() {
  const icon = nativeImage.createFromDataURL(
    "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAAHklEQVQ4jWNgYGD4z8BAAoxqGAVDGwAA//8DAAQIAgEBNjQ4AAAAAElFTkSuQmCC"
  );
  tray = new Tray(icon);
  tray.setToolTip("Athena — Latitude MedTech");
  tray.setContextMenu(Menu.buildFromTemplate([
    { label: "Open Athena", click: () => { mainWindow?.show(); mainWindow?.focus(); } },
    { type: "separator" },
    { label: "Quit Athena", click: () => confirmQuit() },
  ]));
  tray.on("click", () => { mainWindow?.show(); mainWindow?.focus(); });
}

// ── Quit helpers ──────────────────────────────────────────────────────────────

function doQuit() {
  isQuitting = true;
  // Kill child processes before quitting
  try { backendProc?.kill("SIGTERM"); }  catch {}
  try { frontendProc?.kill("SIGTERM"); } catch {}
  setTimeout(() => {
    try { backendProc?.kill("SIGKILL"); }  catch {}
    try { frontendProc?.kill("SIGKILL"); } catch {}
    app.quit();
  }, 1500);
}

function confirmQuit() {
  mainWindow?.show();
  mainWindow?.focus();
  dialog.showMessageBox(mainWindow, {
    type: "question",
    title: "Exit Athena",
    message: "Are you sure you want to exit Athena?",
    detail: "All voice and agent sessions will be closed.",
    buttons: ["Exit", "Cancel"],
    defaultId: 1,
    cancelId: 1,
    noLink: true,
  }).then(({ response }) => {
    if (response === 0) doQuit();
  });
}

// ── App lifecycle ─────────────────────────────────────────────────────────────

app.on("second-instance", () => {
  // Focus existing window if user tries to open a second instance
  mainWindow?.show();
  mainWindow?.focus();
});

app.whenReady().then(async () => {
  // Kill any orphaned processes from a previous crashed run
  killOrphans();

  const splash = createSplash();
  createMainWindow();
  createTray();

  try {
    log("Starting Athena backend…");
    backendProc = spawnHidden(VENV_PY, [SERVER_PY], path.join(ROOT, "ui", "backend"), "backend");
    await waitForHttp(BACKEND_URL + "/");
    log("Backend ready.");

    log("Starting frontend…");
    // Use vite.cmd directly — avoids spawning a CMD host window
    const viteBin = fs.existsSync(VITE_BIN) ? VITE_BIN
      : path.join(FRONTEND_DIR, "node_modules", ".bin", "vite");
    frontendProc = spawnHidden(viteBin, [], FRONTEND_DIR, "frontend");
    await waitForHttp(FRONTEND_URL, 20000);
    log("Frontend ready.");

    splash.close();
    mainWindow.show();
    mainWindow.focus();
  } catch (err) {
    log(`Startup error: ${err.message}`);
    splash.close();
    mainWindow.show();
  }
});

app.on("window-all-closed", e => e.preventDefault()); // live in tray

app.on("before-quit", () => {
  isQuitting = true;
  try { backendProc?.kill(); }  catch {}
  try { frontendProc?.kill(); } catch {}
});

// ── IPC ───────────────────────────────────────────────────────────────────────
ipcMain.on("app-quit",    () => confirmQuit());
ipcMain.on("app-minimize",() => mainWindow?.minimize());
ipcMain.on("app-force-quit", () => doQuit());   // called after goodbye plays
