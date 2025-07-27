/**
 * Penny Chat WebSocket Client
 * Handles real-time communication with the AI assistant
 */

class ChatClient {
    constructor() {
        this.ws = null;
        this.isConnecting = false;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 1000;
        
        // DOM elements
        this.messagesContainer = document.getElementById('messagesContainer');
        this.messageInput = document.getElementById('messageInput');
        this.sendButton = document.getElementById('sendButton');
        this.connectionStatus = document.getElementById('connectionStatus');
        this.typingIndicator = document.getElementById('typingIndicator');
        this.characterCount = document.querySelector('.character-count');
        this.errorModal = document.getElementById('errorModal');
        this.errorMessage = document.getElementById('errorMessage');
        
        this.initializeEventListeners();
        this.connect();
    }

    initializeEventListeners() {
        // Send button click
        this.sendButton.addEventListener('click', () => this.sendMessage());
        
        // Enter key to send message
        this.messageInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });
        
        // Auto-resize textarea and update character count
        this.messageInput.addEventListener('input', () => {
            this.autoResizeTextarea();
            this.updateCharacterCount();
            this.updateSendButton();
        });
        
        // Modal event listeners
        document.getElementById('closeErrorModal').addEventListener('click', () => {
            this.hideErrorModal();
        });
        
        document.getElementById('retryConnection').addEventListener('click', () => {
            this.hideErrorModal();
            this.connect();
        });
        
        document.getElementById('dismissError').addEventListener('click', () => {
            this.hideErrorModal();
        });
        
        // Click outside modal to close
        this.errorModal.addEventListener('click', (e) => {
            if (e.target === this.errorModal) {
                this.hideErrorModal();
            }
        });
    }

    connect() {
        if (this.isConnecting || (this.ws && this.ws.readyState === WebSocket.OPEN)) {
            return;
        }

        this.isConnecting = true;
        this.updateConnectionStatus('connecting');

        try {
            // Determine WebSocket URL based on current protocol
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//${window.location.host}/ws/chat`;
            
            this.ws = new WebSocket(wsUrl);
            
            this.ws.onopen = () => {
                console.log('WebSocket connected');
                this.isConnecting = false;
                this.reconnectAttempts = 0;
                this.updateConnectionStatus('online');
            };
            
            this.ws.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    this.handleMessage(data);
                } catch (error) {
                    console.error('Error parsing WebSocket message:', error);
                }
            };
            
            this.ws.onclose = (event) => {
                console.log('WebSocket closed:', event.code, event.reason);
                this.isConnecting = false;
                this.updateConnectionStatus('offline');
                this.hideTypingIndicator();
                
                // Attempt to reconnect if not a normal closure
                if (event.code !== 1000 && this.reconnectAttempts < this.maxReconnectAttempts) {
                    setTimeout(() => {
                        this.reconnectAttempts++;
                        this.connect();
                    }, this.reconnectDelay * Math.pow(2, this.reconnectAttempts));
                } else if (this.reconnectAttempts >= this.maxReconnectAttempts) {
                    this.showErrorModal('Connection lost. Maximum reconnection attempts reached.');
                }
            };
            
            this.ws.onerror = (error) => {
                console.error('WebSocket error:', error);
                this.isConnecting = false;
                this.updateConnectionStatus('offline');
                this.showErrorModal('Failed to connect to chat service. Please check your connection.');
            };
            
        } catch (error) {
            console.error('Error creating WebSocket connection:', error);
            this.isConnecting = false;
            this.updateConnectionStatus('offline');
            this.showErrorModal('Unable to establish connection to chat service.');
        }
    }

    disconnect() {
        if (this.ws) {
            this.ws.close(1000, 'User disconnected');
            this.ws = null;
        }
    }

    sendMessage() {
        const message = this.messageInput.value.trim();
        
        if (!message || !this.ws || this.ws.readyState !== WebSocket.OPEN) {
            return;
        }

        // Add user message to chat
        this.addMessage({
            type: 'user',
            content: message,
            timestamp: new Date().toISOString()
        });

        // Send message via WebSocket
        try {
            this.ws.send(JSON.stringify({
                message: message,
                timestamp: new Date().toISOString()
            }));
            
            // Clear input and show typing indicator
            this.messageInput.value = '';
            this.updateCharacterCount();
            this.updateSendButton();
            this.autoResizeTextarea();
            this.showTypingIndicator();
            
        } catch (error) {
            console.error('Error sending message:', error);
            this.showErrorModal('Failed to send message. Please try again.');
        }
    }

    handleMessage(data) {
        this.hideTypingIndicator();
        
        // Handle different message types
        if (data.type === 'error') {
            this.showErrorModal(data.error || data.message || 'An error occurred while processing your request.');
            return;
        }
        
        if (data.type === 'system') {
            // Handle system messages (like welcome message)
            console.log('System message:', data.content);
            return;
        }
        
        if (data.type === 'typing') {
            // Typing indicator is handled separately
            return;
        }
        
        // Add AI response to chat
        this.addMessage({
            type: 'ai',
            content: data.answer || data.content || 'I received your message but couldn\'t generate a response.',
            sources: data.sources || [],
            financial_summary: data.financial_summary || null,
            timestamp: data.timestamp || new Date().toISOString()
        });
    }

    addMessage(messageData) {
        const messageElement = document.createElement('div');
        messageElement.className = `message ${messageData.type}`;
        
        const timestamp = new Date(messageData.timestamp).toLocaleTimeString([], {
            hour: '2-digit',
            minute: '2-digit'
        });

        if (messageData.type === 'user') {
            messageElement.innerHTML = `
                <div class="message-avatar user-avatar">👤</div>
                <div class="message-content">
                    <div class="message-bubble">${this.escapeHtml(messageData.content)}</div>
                    <div class="message-timestamp">${timestamp}</div>
                </div>
            `;
        } else {
            const sourcesHtml = this.renderSources(messageData.sources);
            const summaryHtml = this.renderFinancialSummary(messageData.financial_summary);
            
            messageElement.innerHTML = `
                <div class="ai-avatar">🤖</div>
                <div class="message-content">
                    <div class="message-bubble">${this.formatAiResponse(messageData.content)}</div>
                    <div class="message-timestamp">${timestamp}</div>
                    ${sourcesHtml}
                    ${summaryHtml}
                </div>
            `;
        }

        this.messagesContainer.appendChild(messageElement);
        this.scrollToBottom();
    }

    renderSources(sources) {
        if (!sources || sources.length === 0) {
            return '';
        }

        const sourceItems = sources.map(source => `
            <div class="source-item">
                <div class="source-filename">📄 ${this.escapeHtml(source.filename || 'Unknown Document')}</div>
                ${source.snippet ? `<div class="source-snippet">${this.escapeHtml(source.snippet)}</div>` : ''}
            </div>
        `).join('');

        return `
            <div class="sources-section">
                <div class="sources-header">
                    📚 Sources
                </div>
                <div class="sources-list">
                    ${sourceItems}
                </div>
            </div>
        `;
    }

    renderFinancialSummary(summary) {
        if (!summary) {
            return '';
        }

        const summaryItems = [];
        
        if (summary.total_amount !== undefined) {
            summaryItems.push(`
                <div class="summary-item">
                    <div class="summary-value">$${this.formatCurrency(summary.total_amount)}</div>
                    <div class="summary-label">Total Amount</div>
                </div>
            `);
        }
        
        if (summary.count !== undefined) {
            summaryItems.push(`
                <div class="summary-item">
                    <div class="summary-value">${summary.count}</div>
                    <div class="summary-label">Documents</div>
                </div>
            `);
        }
        
        if (summary.average_amount !== undefined) {
            summaryItems.push(`
                <div class="summary-item">
                    <div class="summary-value">$${this.formatCurrency(summary.average_amount)}</div>
                    <div class="summary-label">Average</div>
                </div>
            `);
        }

        if (summaryItems.length === 0) {
            return '';
        }

        return `
            <div class="financial-summary">
                <div class="summary-header">
                    💰 Financial Summary
                </div>
                <div class="summary-grid">
                    ${summaryItems.join('')}
                </div>
            </div>
        `;
    }

    formatAiResponse(content) {
        // Convert newlines to <br> tags and preserve formatting
        return this.escapeHtml(content).replace(/\n/g, '<br>');
    }

    formatCurrency(amount) {
        return new Intl.NumberFormat('en-US', {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        }).format(amount);
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    showTypingIndicator() {
        this.typingIndicator.style.display = 'flex';
        this.scrollToBottom();
    }

    hideTypingIndicator() {
        this.typingIndicator.style.display = 'none';
    }

    updateConnectionStatus(status) {
        const statusMap = {
            'online': { text: 'Connected', class: 'online' },
            'offline': { text: 'Disconnected', class: 'offline' },
            'connecting': { text: 'Connecting...', class: 'connecting' }
        };

        const statusInfo = statusMap[status] || statusMap['offline'];
        this.connectionStatus.textContent = statusInfo.text;
        this.connectionStatus.className = `status-indicator ${statusInfo.class}`;
        
        // Update send button state
        this.updateSendButton();
    }

    updateSendButton() {
        const hasMessage = this.messageInput.value.trim().length > 0;
        const isConnected = this.ws && this.ws.readyState === WebSocket.OPEN;
        this.sendButton.disabled = !hasMessage || !isConnected;
    }

    updateCharacterCount() {
        const length = this.messageInput.value.length;
        const maxLength = this.messageInput.maxLength;
        this.characterCount.textContent = `${length}/${maxLength}`;
        
        // Change color if approaching limit
        if (length > maxLength * 0.9) {
            this.characterCount.style.color = '#ef4444';
        } else if (length > maxLength * 0.8) {
            this.characterCount.style.color = '#f59e0b';
        } else {
            this.characterCount.style.color = '#9ca3af';
        }
    }

    autoResizeTextarea() {
        const textarea = this.messageInput;
        textarea.style.height = 'auto';
        textarea.style.height = Math.min(textarea.scrollHeight, 120) + 'px';
    }

    scrollToBottom() {
        setTimeout(() => {
            this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight;
        }, 100);
    }

    showErrorModal(message) {
        this.errorMessage.textContent = message;
        this.errorModal.style.display = 'flex';
    }

    hideErrorModal() {
        this.errorModal.style.display = 'none';
    }

    // Public method to gracefully shutdown
    destroy() {
        this.disconnect();
    }
}

// Initialize chat client when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.chatClient = new ChatClient();
});

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
    if (window.chatClient) {
        window.chatClient.destroy();
    }
});