class FileManager {
    constructor() {
        this.dropZone = document.getElementById('dropZone');
        this.fileInput = document.getElementById('fileInput');
        this.browseBtn = document.getElementById('browseBtn');
        this.filesList = document.getElementById('filesList');
        this.refreshBtn = document.getElementById('refreshBtn');
        this.refreshJobsBtn = document.getElementById('refreshJobsBtn');
        this.jobsList = document.getElementById('jobsList');
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
        this.loadRecentJobs();
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
        
        // Refresh buttons
        this.refreshBtn.addEventListener('click', this.loadFiles.bind(this));
        this.refreshJobsBtn.addEventListener('click', this.loadRecentJobs.bind(this));
        
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
            
            try {
                this.updateProgress(0, `Uploading "${file.name}"...`);
                const uploadResult = await this.uploadSingleFile(file);
                
                // Start tracking the processing job
                if (uploadResult.job_id) {
                    await this.trackProcessingJob(uploadResult.job_id, file.name);
                }
                
                const progress = ((i + 1) / files.length) * 100;
                this.updateProgress(progress, `Completed ${i + 1}/${files.length} files`);
                
            } catch (error) {
                this.showError(`Failed to process "${file.name}": ${error.message}`);
            }
        }
        
        this.hideUploadProgress();
        this.loadFiles();
        this.loadRecentJobs();
    }

    async uploadSingleFile(file) {
        const formData = new FormData();
        formData.append('file', file);
        
        // Use the documents endpoint for async processing
        const response = await fetch('/api/v1/documents/upload', {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Upload failed');
        }
        
        return response.json();
    }

    async trackProcessingJob(jobId, filename) {
        this.updateProgress(10, `Processing "${filename}" - Validating file...`);
        
        let completed = false;
        let attempts = 0;
        const maxAttempts = 120; // Max 2 minutes with 1-second intervals
        
        while (!completed && attempts < maxAttempts) {
            try {
                const response = await fetch(`/api/v1/jobs/progress/${jobId}`);
                if (!response.ok) {
                    throw new Error('Failed to get job progress');
                }
                
                const progress = await response.json();
                
                // Update progress bar
                const progressPercent = Math.max(10, progress.progress || 0);
                const stepText = progress.current_step || 'Processing...';
                this.updateProgress(progressPercent, `"${filename}" - ${stepText}`);
                
                if (progress.completed) {
                    completed = true;
                    if (progress.status === 'failed') {
                        throw new Error(progress.error_message || 'Processing failed');
                    }
                } else {
                    // Wait 1 second before next poll
                    await new Promise(resolve => setTimeout(resolve, 1000));
                }
                
                attempts++;
                
            } catch (error) {
                console.error('Error tracking job progress:', error);
                // Continue without failing the entire upload
                break;
            }
        }
        
        if (!completed && attempts >= maxAttempts) {
            console.warn(`Job ${jobId} tracking timed out after ${maxAttempts} attempts`);
        }
    }

    async loadFiles() {
        try {
            const response = await fetch('/api/v1/documents');
            if (!response.ok) throw new Error('Failed to load documents');
            
            const documents = await response.json();
            this.renderFiles(documents);
        } catch (error) {
            this.showError('Failed to load documents: ' + error.message);
        }
    }

    renderFiles(files) {
        if (files.length === 0) {
            this.filesList.innerHTML = `
                <div class="empty-state">
                    <p>No documents uploaded yet</p>
                </div>
            `;
            return;
        }

        this.filesList.innerHTML = files.map(file => `
            <div class="file-item" data-file-id="${file.id}">
                <div class="file-info">
                    <div class="file-icon">${this.getFileIcon(this.getContentTypeFromFilename(file.filename))}</div>
                    <div class="file-details">
                        <h4>${file.filename}</h4>
                        <div class="file-meta">
                            ${this.formatFileSize(file.file_size)} • ${this.formatDate(file.uploaded_at)}
                            ${file.indexed ? ' • ✅ Indexed' : ' • ⏳ Processing'}
                        </div>
                    </div>
                </div>
                <div class="file-actions">
                    <button class="btn-danger" onclick="fileManager.showDeleteModal('${file.id}', '${file.filename}')">
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

    getContentTypeFromFilename(filename) {
        const ext = filename.toLowerCase().split('.').pop();
        switch (ext) {
            case 'pdf': return 'application/pdf';
            case 'jpg':
            case 'jpeg': return 'image/jpeg';
            case 'png': return 'image/png';
            default: return 'application/octet-stream';
        }
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
            const response = await fetch(`/api/v1/documents/${this.currentDeleteFile.id}`, {
                method: 'DELETE'
            });
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Delete failed');
            }
            
            this.hideDeleteModal();
            this.loadFiles();
        } catch (error) {
            this.showError('Failed to delete document: ' + error.message);
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

    async loadRecentJobs() {
        try {
            const response = await fetch('/api/v1/jobs/recent?limit=10');
            if (!response.ok) throw new Error('Failed to load jobs');
            
            const data = await response.json();
            this.renderJobs(data.jobs || []);
        } catch (error) {
            console.error('Failed to load recent jobs:', error);
            // Don't show error to user as this is optional functionality
        }
    }

    renderJobs(jobs) {
        if (jobs.length === 0) {
            this.jobsList.innerHTML = `
                <div class="empty-state">
                    <p>No processing jobs yet</p>
                </div>
            `;
            return;
        }

        this.jobsList.innerHTML = jobs.map(job => `
            <div class="job-item ${job.status}" data-job-id="${job.id}">
                <div class="job-info">
                    <div class="job-icon">${this.getJobStatusIcon(job.status)}</div>
                    <div class="job-details">
                        <h4>${job.filename}</h4>
                        <div class="job-meta">
                            <span class="job-status status-${job.status}">${job.status.toUpperCase()}</span>
                            <span class="job-time">${this.formatDate(job.created_at)}</span>
                        </div>
                        <div class="job-progress-text">${job.current_step || 'Queued'}</div>
                        ${job.status === 'processing' ? `
                            <div class="job-progress-bar">
                                <div class="job-progress-fill" style="width: ${job.progress || 0}%"></div>
                            </div>
                        ` : ''}
                    </div>
                </div>
                ${job.error_message ? `
                    <div class="job-error">
                        <small>Error: ${job.error_message}</small>
                    </div>
                ` : ''}
            </div>
        `).join('');
    }

    getJobStatusIcon(status) {
        switch (status) {
            case 'pending': return '⏳';
            case 'processing': return '⚙️';
            case 'completed': return '✅';
            case 'failed': return '❌';
            default: return '📋';
        }
    }
}

// Initialize file manager when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.fileManager = new FileManager();
});