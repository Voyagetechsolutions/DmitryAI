// main.js - Electron main process
const { app, BrowserWindow, ipcMain, Menu } = require('electron');
const path = require('path');
const http = require('http');

// Agent API URL
const AGENT_API_URL = 'http://127.0.0.1:8765';

let mainWindow;

function createWindow() {
    mainWindow = new BrowserWindow({
        width: 1200,
        height: 800,
        minWidth: 900,
        minHeight: 600,
        frame: true,
        titleBarStyle: 'hidden',
        titleBarOverlay: {
            color: '#0a0a0a',
            symbolColor: '#8ffcff',
            height: 40
        },
        backgroundColor: '#0a0a0a',
        webPreferences: {
            nodeIntegration: false,
            contextIsolation: true,
            preload: path.join(__dirname, 'preload.js'),
        },
        icon: path.join(__dirname, 'public', 'icon.png'),
    });

    // In development, load from React dev server
    const isDev = process.env.NODE_ENV === 'development' || !app.isPackaged;

    if (isDev) {
        mainWindow.loadURL('http://localhost:3000');
        mainWindow.webContents.openDevTools();
    } else {
        mainWindow.loadFile(path.join(__dirname, 'build', 'index.html'));
    }

    // Remove menu in production
    if (!isDev) {
        Menu.setApplicationMenu(null);
    }

    mainWindow.on('closed', () => {
        mainWindow = null;
    });
}

// IPC handlers for agent communication
ipcMain.handle('agent:send-message', async (event, message) => {
    try {
        const response = await fetch(`${AGENT_API_URL}/message`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message }),
        });
        return await response.json();
    } catch (error) {
        return { error: error.message };
    }
});

ipcMain.handle('agent:switch-mode', async (event, mode) => {
    try {
        const response = await fetch(`${AGENT_API_URL}/mode`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ mode }),
        });
        return await response.json();
    } catch (error) {
        return { error: error.message };
    }
});

ipcMain.handle('agent:confirm-action', async (event, actionId, confirmed) => {
    try {
        const response = await fetch(`${AGENT_API_URL}/confirm`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ actionId, confirmed }),
        });
        return await response.json();
    } catch (error) {
        return { error: error.message };
    }
});

ipcMain.handle('agent:get-logs', async (event, limit = 50) => {
    try {
        const response = await fetch(`${AGENT_API_URL}/logs?limit=${limit}`);
        return await response.json();
    } catch (error) {
        return { error: error.message };
    }
});

ipcMain.handle('agent:get-status', async () => {
    try {
        const response = await fetch(`${AGENT_API_URL}/status`);
        return await response.json();
    } catch (error) {
        return { error: error.message, connected: false };
    }
});

app.whenReady().then(createWindow);

app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') {
        app.quit();
    }
});

app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
        createWindow();
    }
});
