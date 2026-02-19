import React, { useState, useEffect, useRef } from 'react';
import { Send, Terminal, Shield, Code, Search, Brain, Target, Cpu } from 'lucide-react';

// Mode definitions - Utility is default startup mode
const MODES = [
    { id: 'utility', name: 'Utility', icon: '🗂️', description: 'Everyday simple tasks' },
    { id: 'general', name: 'General', icon: '🧠', description: 'Broad thinking' },
    { id: 'design', name: 'Design', icon: '🏗', description: 'System architecture' },
    { id: 'developer', name: 'Developer', icon: '💻', description: 'Coding support' },
    { id: 'research', name: 'Research', icon: '🔍', description: 'Tech evaluation' },
    { id: 'security', name: 'Security', icon: '🛡️', description: 'Risk analysis' },
    { id: 'simulation', name: 'Simulation', icon: '🎯', description: 'Impact modeling' },
];

function App() {
    const [messages, setMessages] = useState([
        { id: 1, type: 'ai', text: 'Hey. How can I help you today?' }
    ]);
    const [input, setInput] = useState('');
    const [currentMode, setCurrentMode] = useState('utility');
    const [logs, setLogs] = useState([]);
    const [isConnected, setIsConnected] = useState(false);
    const [isLoading, setIsLoading] = useState(false);
    const [confirmation, setConfirmation] = useState(null);

    const chatEndRef = useRef(null);
    const inputRef = useRef(null);

    // Check agent connection
    useEffect(() => {
        const checkConnection = async () => {
            if (window.dmitryAPI) {
                const status = await window.dmitryAPI.getStatus();
                if (status.error) {
                    console.error('Connection failed:', status.error);
                    setLogs(prev => [{
                        tool: 'System',
                        status: 'failed',
                        time: new Date().toLocaleTimeString(),
                        message: `Connection error: ${status.error}`
                    }, ...prev].slice(0, 50));
                }
                setIsConnected(!status.error);
            }
        };

        checkConnection();
        const interval = setInterval(checkConnection, 5000);
        return () => clearInterval(interval);
    }, []);

    // Scroll to bottom on new messages
    useEffect(() => {
        chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    // Listen for confirmation requests
    useEffect(() => {
        if (window.dmitryAPI) {
            window.dmitryAPI.onConfirmationRequest((data) => {
                setConfirmation(data);
            });
        }
    }, []);

    const handleSend = async () => {
        if (!input.trim() || isLoading) return;

        const userMessage = { id: Date.now(), type: 'user', text: input };
        setMessages(prev => [...prev, userMessage]);
        setInput('');
        setIsLoading(true);

        try {
            if (window.dmitryAPI) {
                const response = await window.dmitryAPI.sendMessage(input);

                if (response.error) {
                    setMessages(prev => [...prev, {
                        id: Date.now(),
                        type: 'system',
                        text: `Error: ${response.error}`
                    }]);
                } else {
                    // Add AI response
                    if (response.text) {
                        setMessages(prev => [...prev, {
                            id: Date.now(),
                            type: 'ai',
                            text: response.text
                        }]);
                    }

                    // Add tool execution message if applicable
                    if (response.tool_executed) {
                        setMessages(prev => [...prev, {
                            id: Date.now(),
                            type: 'tool',
                            text: `⚙️ ${response.tool_executed}: ${response.tool_result || 'completed'}`
                        }]);
                    }

                    // Update logs
                    if (response.log) {
                        setLogs(prev => [response.log, ...prev].slice(0, 50));
                    }
                }
            } else {
                // Demo mode without agent
                setTimeout(() => {
                    setMessages(prev => [...prev, {
                        id: Date.now(),
                        type: 'ai',
                        text: `I received your message: "${input}". The agent API is not connected.`
                    }]);
                }, 500);
            }
        } catch (err) {
            setMessages(prev => [...prev, {
                id: Date.now(),
                type: 'system',
                text: `Connection error: ${err.message}`
            }]);
        }

        setIsLoading(false);
    };

    const handleModeSwitch = async (modeId) => {
        setCurrentMode(modeId);

        if (window.dmitryAPI) {
            await window.dmitryAPI.switchMode(modeId);
        }

        const mode = MODES.find(m => m.id === modeId);
        setMessages(prev => [...prev, {
            id: Date.now(),
            type: 'system',
            text: `Switched to ${mode.icon} ${mode.name} Mode`
        }]);
    };

    const handleConfirm = async (confirmed) => {
        if (confirmation && window.dmitryAPI) {
            await window.dmitryAPI.confirmAction(confirmation.actionId, confirmed);
        }
        setConfirmation(null);
    };

    const handleKeyDown = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
    };

    return (
        <div className="app-container">
            {/* Sidebar */}
            <div className="sidebar">
                <div className="sidebar-header">
                    <div className="logo">
                        <span className="logo-text">DMITRY</span>
                        <span className="logo-version">v1.2</span>
                    </div>
                </div>

                <div className="mode-selector">
                    <div className="mode-label">Cognitive Mode</div>
                    <div className="mode-list">
                        {MODES.map(mode => (
                            <button
                                key={mode.id}
                                className={`mode-btn ${currentMode === mode.id ? 'active' : ''}`}
                                onClick={() => handleModeSwitch(mode.id)}
                            >
                                <span className="mode-icon">{mode.icon}</span>
                                <span>{mode.name}</span>
                            </button>
                        ))}
                    </div>
                </div>
            </div>

            {/* Main Content */}
            <div className="main-content">
                {/* Chat Area */}
                <div className="chat-area">
                    {messages.map(msg => (
                        <div key={msg.id} className={`message ${msg.type}`}>
                            {msg.text}
                        </div>
                    ))}
                    {isLoading && (
                        <div className="message ai" style={{ opacity: 0.6 }}>
                            Thinking...
                        </div>
                    )}
                    <div ref={chatEndRef} />
                </div>

                {/* Input Area */}
                <div className="input-area">
                    <div className="input-wrapper">
                        <textarea
                            ref={inputRef}
                            className="chat-input"
                            placeholder="Ask Dmitry anything..."
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            onKeyDown={handleKeyDown}
                            rows={1}
                        />
                        <button
                            className="send-btn"
                            onClick={handleSend}
                            disabled={!input.trim() || isLoading}
                        >
                            <Send size={20} />
                        </button>
                    </div>
                </div>
            </div>

            {/* Right Panel - Logs */}
            <div className="right-panel">
                <div className="panel-header">
                    <Terminal size={14} style={{ marginRight: 8, verticalAlign: 'middle' }} />
                    Action Log
                </div>
                <div className="log-list">
                    {logs.length === 0 ? (
                        <div style={{ padding: 16, color: 'var(--text-muted)', textAlign: 'center' }}>
                            No actions yet
                        </div>
                    ) : (
                        logs.map((log, i) => (
                            <div key={i} className="log-item">
                                <span className="log-icon">
                                    {log.status === 'success' ? '✓' : log.status === 'failed' ? '✗' : '⚙️'}
                                </span>
                                <span className="log-content">{log.tool}</span>
                                <span className="log-time">{log.time}</span>
                            </div>
                        ))
                    )}
                </div>
            </div>

            {/* Status Bar */}
            <div className="status-bar">
                <div className="status-indicator">
                    <span className={`status-dot ${isConnected ? '' : 'disconnected'}`} />
                    <span>{isConnected ? 'Connected' : 'Disconnected'}</span>
                </div>
                <span>Mode: {MODES.find(m => m.id === currentMode)?.name}</span>
            </div>

            {/* Confirmation Dialog */}
            {confirmation && (
                <div className="confirm-overlay">
                    <div className="confirm-dialog">
                        <div className="confirm-title">⚠️ Confirm Action</div>
                        <div className="confirm-message">{confirmation.message}</div>
                        <div className="confirm-actions">
                            <button className="btn btn-cancel" onClick={() => handleConfirm(false)}>
                                Cancel
                            </button>
                            <button className="btn btn-confirm" onClick={() => handleConfirm(true)}>
                                Confirm
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}

export default App;
