/**
 * Latitude MedTech — Athena Electron Main Process
 * =================================================
 * Single-instance desktop app. Starts FastAPI + Vite as hidden processes.
 * No visible CMD windows. Lives in system tray. Handles graceful shutdown.
 */

const { app, BrowserWindow, Tray, Menu, nativeImage, ipcMain, shell, dialog, screen } = require("electron");
const { spawn, execSync } = require("child_process");
const path = require("path");
const http = require("http");
const fs   = require("fs");

// ── Suppress Windows Script Error dialogs from legacy system components ───────
process.on("uncaughtException",   err => console.error("[main] uncaughtException:", err));
process.on("unhandledRejection",  err => console.error("[main] unhandledRejection:", err));

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
  const { width: sw, height: sh } = screen.getPrimaryDisplay().workAreaSize;
  const pw = Math.max(640, Math.round(sw * 0.70));
  const ph = Math.max(360, Math.round(sh * 0.70));

  const w = new BrowserWindow({
    width: pw, height: ph, frame: false,
    resizable: false, center: true, transparent: false,
    alwaysOnTop: true,
    webPreferences: { nodeIntegration: false, contextIsolation: true },
  });

  const bgPath = path.join(ROOT, "ui", "splash_bg.jpg");
  let bgSrc = "";
  try { bgSrc = "data:image/jpeg;base64," + fs.readFileSync(bgPath).toString("base64"); } catch {}

  const html = `<!DOCTYPE html>
<html><head><meta charset="UTF-8">
<style>
  *{margin:0;padding:0;box-sizing:border-box}
  @keyframes shimmer{0%{background-position:-300% center}100%{background-position:300% center}}
  @keyframes dotFlash{0%,80%,100%{opacity:.15}40%{opacity:1}}
  html,body{width:100%;height:100%;overflow:hidden}
  body{font-family:'Segoe UI','Helvetica Neue',Arial,sans-serif;background:#0d2a44;position:relative}
  #bg{position:absolute;width:100%;height:100%;object-fit:cover;object-position:28% center;z-index:0}
  #overlay{
    position:absolute;inset:0;z-index:1;
    background:linear-gradient(180deg,
      rgba(8,28,50,0) 0%,rgba(8,28,50,0) 18%,rgba(8,28,50,.60) 44%,
      rgba(8,28,50,.88) 58%,rgba(8,28,50,.97) 70%,
      rgba(8,28,50,1) 80%,rgba(8,28,50,1) 100%)
  }
  #content{position:absolute;bottom:0;left:0;right:0;padding:0 72px 56px;z-index:2}
  .eyebrow{font-size:15px;letter-spacing:.28em;color:#C4922A;text-transform:uppercase;font-weight:700;margin-bottom:12px;text-shadow:0 1px 8px rgba(0,0,0,.7)}
  .name{font-size:clamp(60px,7vw,100px);font-weight:200;letter-spacing:.04em;color:#EDE6D8;line-height:1;margin-bottom:12px;text-shadow:0 2px 24px rgba(0,0,0,.85),0 0 48px rgba(0,0,0,.4)}
  .tagline{font-size:20px;letter-spacing:.18em;color:rgba(220,210,195,.75);text-transform:uppercase;margin-bottom:36px;text-shadow:0 1px 8px rgba(0,0,0,.6)}
  .status-text{font-size:17px;color:rgba(220,210,195,.65);letter-spacing:.04em}
  .dot{display:inline-block;font-size:17px;color:rgba(196,146,42,.85);animation:dotFlash 1.4s ease-in-out infinite both}
  .dot1{animation-delay:0s}.dot2{animation-delay:.2s}.dot3{animation-delay:.4s}
  #bar-wrap{position:absolute;bottom:0;left:0;width:100%;height:5px;background:#1a3a58;overflow:hidden;z-index:3}
  #bar{height:100%;width:0%;
    background:linear-gradient(90deg,rgba(196,146,42,.4),rgba(232,184,75,1),rgba(196,146,42,.4));
    background-size:300% auto;
    animation:shimmer 2.4s linear infinite;
    transition:width .5s ease}
</style>
</head><body>
${bgSrc ? `<img id="bg" src="${bgSrc}" alt="">` : ""}
<div id="overlay"></div>
<div id="content">
  <div class="eyebrow">Latitude MedTech</div>
  <div class="name">Athena</div>
  <div class="tagline">Advancing Human Intelligence</div>
  <span class="status-text" id="status">Starting up</span><span id="dots"><span class="dot dot1">.</span><span class="dot dot2">.</span><span class="dot dot3">.</span></span>
</div>
<div id="bar-wrap"><div id="bar"></div></div>
</body></html>`;

  w.loadURL("data:text/html;charset=utf-8," + encodeURIComponent(html));
  return w;
}

function setSplashStatus(splash, text, pct) {
  if (!splash || splash.isDestroyed()) return;
  splash.webContents.executeJavaScript(
    `(function(){` +
    `var s=document.getElementById('status');if(s)s.textContent=${JSON.stringify(text)};` +
    `var b=document.getElementById('bar');if(b)b.style.width='${pct}%';` +
    `})()`
  ).catch(() => {});
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

  // Route renderer errors to console instead of native Windows dialogs
  mainWindow.webContents.on("render-process-gone", (_e, details) => {
    log(`[renderer] gone: ${details.reason}`);
  });
  mainWindow.webContents.on("unresponsive", () => log("[renderer] unresponsive"));

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
  // Prefer the ICO (multi-res) at the project root; fall back to the 32px PNG
  const icoPath = path.join(ROOT, "athena.ico");
  const pngPath = path.join(ROOT, "ui", "frontend", "public", "icon-32.png");
  const iconPath = fs.existsSync(icoPath) ? icoPath : pngPath;
  const icon = nativeImage.createFromPath(iconPath);
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
  // Bring existing window to front — no dialog, session continues uninterrupted
  if (mainWindow) {
    mainWindow.show();
    mainWindow.focus();
  }
});

app.whenReady().then(async () => {
  // Kill any orphaned processes from a previous crashed run
  killOrphans();

  const splash = createSplash();
  createMainWindow();
  createTray();

  try {
    log("Starting Athena backend…");
    setSplashStatus(splash, "Warming up the backend", 15);
    backendProc = spawnHidden(VENV_PY, [SERVER_PY], path.join(ROOT, "ui", "backend"), "backend");
    await waitForHttp(BACKEND_URL + "/");
    log("Backend ready.");
    setSplashStatus(splash, "Backend ready — launching interface", 70);

    log("Starting frontend…");
    // Use vite.cmd directly — avoids spawning a CMD host window
    const viteBin = fs.existsSync(VITE_BIN) ? VITE_BIN
      : path.join(FRONTEND_DIR, "node_modules", ".bin", "vite");
    frontendProc = spawnHidden(viteBin, [], FRONTEND_DIR, "frontend");
    setSplashStatus(splash, "Loading the interface", 80);
    await waitForHttp(FRONTEND_URL, 20000);
    log("Frontend ready.");
    setSplashStatus(splash, "Welcome back. Athena is ready.", 100);
    await new Promise(r => setTimeout(r, 600));

    splash.close();
    mainWindow.show();
    mainWindow.maximize();
    mainWindow.focus();
  } catch (err) {
    log(`Startup error: ${err.message}`);
    splash.close();
    mainWindow.show();
    mainWindow.maximize();
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
