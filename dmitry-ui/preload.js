// preload.js - Exposes safe APIs to renderer
const { contextBridge, ipcRenderer } = require('electron');

console.log('🔌 Preload script loading...');

contextBridge.exposeInMainWorld('dmitryAPI', {
    // Send message to agent
    sendMessage: (message) => ipcRenderer.invoke('agent:send-message', message),

    // Switch cognitive mode
    switchMode: (mode) => ipcRenderer.invoke('agent:switch-mode', mode),

    // Confirm/deny an action
    confirmAction: (actionId, confirmed) =>
        ipcRenderer.invoke('agent:confirm-action', actionId, confirmed),

    // Get action logs
    getLogs: (limit) => ipcRenderer.invoke('agent:get-logs', limit),

    // Get agent status
    getStatus: () => ipcRenderer.invoke('agent:get-status'),

    // Listen for agent events
    onAgentEvent: (callback) => {
        ipcRenderer.on('agent:event', (event, data) => callback(data));
    },

    // Listen for pending confirmations
    onConfirmationRequest: (callback) => {
        ipcRenderer.on('agent:confirmation-request', (event, data) => callback(data));
    },
});
