class FileManager {
    constructor() {
        this.dropZone = document.getElementById('dropZone');
        this.fileInput = document.getElementById('fileInput');
        this.browseBtn = document.getElementById('browseBtn');
        this.filesList = document.getElementById('filesList');
        this.refreshBtn = document.getElementById('refreshBtn');
        this.uploadProgress = document.getElementById('uploadProgress');
        this.progressFill = document.getElementById('progressFill');
        this.progressText = document.getElementById('progressText');
        this.confirmModal = document.getElementById('confirmModal');
        this.confirmDelete = document.getElementById('confirmDelete');
        this.cancelDelete = document.getElementById('cancelDelete');
        
        this.currentDeleteFile = null;
        this.acceptedTypes = ['application/pdf', 'image/jpeg', 'image/jpg', 'image/png'];
        
        this.initEventListeners();
        this.loadFiles();
    }

    initEventListeners() {
        // Drag and drop events
        this.dropZone.addEventListener('dragover', this.handleDragOver.bind(this));
        this.dropZone.addEventListener('dragleave', this.handleDragLeave.bind(this));
        this.dropZone.addEventListener('drop', this.handleDrop.bind(this));
        this.dropZone.addEventListener('click', () => this.fileInput.click());
        
        // File input change
        this.fileInput.addEventListener('change', this.handleFileSelect.bind(this));
        
        // Browse button
        this.browseBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            this.fileInput.click();
        });
        
        // Refresh button
        this.refreshBtn.addEventListener('click', this.loadFiles.bind(this));
        
        // Modal events
        this.confirmDelete.addEventListener('click', this.handleConfirmDelete.bind(this));
        this.cancelDelete.addEventListener('click', this.hideDeleteModal.bind(this));
        this.confirmModal.addEventListener('click', (e) => {
            if (e.target === this.confirmModal) {
                this.hideDeleteModal();
            }
        });
    }

    handleDragOver(e) {
        e.preventDefault();
        this.dropZone.classList.add('drag-over');
    }

    handleDragLeave(e) {
        e.preventDefault();
        if (!this.dropZone.contains(e.relatedTarget)) {
            this.dropZone.classList.remove('drag-over');
        }
    }

    handleDrop(e) {
        e.preventDefault();
        this.dropZone.classList.remove('drag-over');
        
        const files = Array.from(e.dataTransfer.files);
        this.processFiles(files);
    }

    handleFileSelect(e) {
        const files = Array.from(e.target.files);
        this.processFiles(files);
        e.target.value = ''; // Reset input
    }

    processFiles(files) {
        const validFiles = files.filter(file => {
            if (file.size > 10 * 1024 * 1024) { // 10MB limit
                this.showError(`File "${file.name}" is too large. Maximum size is 10MB.`);
                return false;
            }
            
            if (!this.acceptedTypes.includes(file.type)) {
                this.showError(`File "${file.name}" is not a supported format.`);
                return false;
            }
            
            return true;
        });

        if (validFiles.length > 0) {
            this.uploadFiles(validFiles);
        }
    }

    async uploadFiles(files) {
        this.showUploadProgress();
        
        for (let i = 0; i < files.length; i++) {
            const file = files[i];
            const progress = ((i + 1) / files.length) * 100;
            
            try {
                await this.uploadSingleFile(file);
                this.updateProgress(progress, `Uploaded ${i + 1}/${files.length} files`);
            } catch (error) {
                this.showError(`Failed to upload "${file.name}": ${error.message}`);
            }
        }
        
        this.hideUploadProgress();
        this.loadFiles();
    }

    async uploadSingleFile(file) {
        const formData = new FormData();
        formData.append('file', file);
        
        const response = await fetch('/api/files/upload', {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Upload failed');
        }
        
        return response.json();
    }

    async loadFiles() {
        try {
            const response = await fetch('/api/files');
            if (!response.ok) throw new Error('Failed to load files');
            
            const files = await response.json();
            this.renderFiles(files);
        } catch (error) {
            this.showError('Failed to load files: ' + error.message);
        }
    }

    renderFiles(files) {
        if (files.length === 0) {
            this.filesList.innerHTML = `
                <div class="empty-state">
                    <p>No files uploaded yet</p>
                </div>
            `;
            return;
        }

        this.filesList.innerHTML = files.map(file => `
            <div class="file-item" data-file-id="${file.id}">
                <div class="file-info">
                    <div class="file-icon">${this.getFileIcon(file.type)}</div>
                    <div class="file-details">
                        <h4>${file.name}</h4>
                        <div class="file-meta">
                            ${this.formatFileSize(file.size)} • ${this.formatDate(file.upload_date)}
                        </div>
                    </div>
                </div>
                <div class="file-actions">
                    <button class="btn-danger" onclick="fileManager.showDeleteModal('${file.id}', '${file.name}')">
                        Delete
                    </button>
                </div>
            </div>
        `).join('');
    }

    getFileIcon(fileType) {
        if (fileType === 'application/pdf') return '📄';
        if (fileType.startsWith('image/')) return '🖼️';
        return '📎';
    }

    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    formatDate(dateString) {
        const date = new Date(dateString);
        return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
    }

    showDeleteModal(fileId, fileName) {
        this.currentDeleteFile = { id: fileId, name: fileName };
        this.confirmModal.querySelector('p').textContent = `Are you sure you want to delete "${fileName}"?`;
        this.confirmModal.style.display = 'flex';
    }

    hideDeleteModal() {
        this.currentDeleteFile = null;
        this.confirmModal.style.display = 'none';
    }

    async handleConfirmDelete() {
        if (!this.currentDeleteFile) return;
        
        try {
            const response = await fetch(`/api/files/${this.currentDeleteFile.id}`, {
                method: 'DELETE'
            });
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Delete failed');
            }
            
            this.hideDeleteModal();
            this.loadFiles();
        } catch (error) {
            this.showError('Failed to delete file: ' + error.message);
        }
    }

    showUploadProgress() {
        this.uploadProgress.style.display = 'block';
        this.dropZone.classList.add('uploading');
        this.updateProgress(0, 'Preparing upload...');
    }

    hideUploadProgress() {
        this.uploadProgress.style.display = 'none';
        this.dropZone.classList.remove('uploading');
    }

    updateProgress(percent, text) {
        this.progressFill.style.width = percent + '%';
        this.progressText.textContent = text;
    }

    showError(message) {
        // Create and show error notification
        const errorDiv = document.createElement('div');
        errorDiv.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: #e53e3e;
            color: white;
            padding: 15px 20px;
            border-radius: 6px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.2);
            z-index: 1001;
            max-width: 400px;
            word-wrap: break-word;
        `;
        errorDiv.textContent = message;
        
        document.body.appendChild(errorDiv);
        
        // Auto remove after 5 seconds
        setTimeout(() => {
            if (errorDiv.parentNode) {
                errorDiv.parentNode.removeChild(errorDiv);
            }
        }, 5000);
        
        console.error(message);
    }
}

// Initialize file manager when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.fileManager = new FileManager();
});