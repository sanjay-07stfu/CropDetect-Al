// ============================================
// AI Crop Disease Detection System
// Camera Module - Real-time Detection
// ============================================

class CameraManager {
    constructor() {
        this.video = document.getElementById('video');
        this.captureBtn = document.getElementById('captureBtn');
        this.resultDiv = document.getElementById('result');
        this.stream = null;
        this.isInitialized = false;
    }

    /**
     * Initialize camera access and set up event listeners
     */
    async init() {
        if (this.isInitialized) return;

        try {
            // Feature detect getUserMedia
            if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
                throw new Error('getUserMedia is not supported in this browser');
            }

            // Request permission and get camera stream
            const constraints = {
                video: {
                    width: { ideal: 1280 },
                    height: { ideal: 720 },
                    facingMode: 'environment' // Back camera on mobile
                }
            };

            this.stream = await navigator.mediaDevices.getUserMedia(constraints);
            this.video.srcObject = this.stream;

            // Set up event listeners first (safe to bind handlers early)
            this.setupEventListeners();

            // Wait for video to become ready
            await new Promise((resolve, reject) => {
                const onReady = () => {
                    try {
                        // Some browsers require play() to start the stream
                        const playPromise = this.video.play();
                        if (playPromise && playPromise.catch) {
                            playPromise.catch(() => {});
                        }
                    } catch (e) {}

                    // If video has valid size, consider it ready
                    if (this.video.videoWidth > 0 && this.video.videoHeight > 0) {
                        resolve();
                    } else {
                        // give it a short moment then resolve
                        setTimeout(resolve, 250);
                    }
                };

                this.video.addEventListener('loadedmetadata', onReady, { once: true });
                // Fallback if loadedmetadata doesn't fire
                setTimeout(onReady, 1200);
            });

            this.enableCapture();
            try { new ToastNotification('Camera initialized successfully', 'success', 2000); } catch(e) {}
            this.isInitialized = true;

        } catch (error) {
            this.handleCameraError(error);
        }
    }

    /**
     * Handle camera errors
     */
    handleCameraError(error) {
        console.error('Camera Error:', error);

        let errorMessage = 'Unable to access camera.';
        if (error.name === 'NotAllowedError') {
            errorMessage = 'Camera permission denied. Please enable camera access in your browser settings.';
        } else if (error.name === 'NotFoundError') {
            errorMessage = 'No camera device found on this device.';
        } else if (error.name === 'NotReadableError') {
            errorMessage = 'Camera is already in use by another application.';
        }

        this.resultDiv.innerHTML = `
            <div class="alert alert-danger alert-dismissible fade show" role="alert">
                <i class="bi bi-exclamation-triangle"></i>
                <strong>Camera Error:</strong> ${errorMessage}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
            <div class="alert alert-info">
                <strong>Alternative:</strong> Try using the 
                <a href="/detect" class="alert-link">image upload method</a> instead.
            </div>
        `;

        this.disableCapture();
        new ToastNotification(errorMessage, 'error');
    }

    /**
     * Set up event listeners for capture button
     */
    setupEventListeners() {
        if (this.captureBtn) {
            this.captureBtn.addEventListener('click', () => this.captureAndAnalyze());
        }

        // Optional: Space bar to capture
        document.addEventListener('keydown', (e) => {
            if (e.code === 'Space' && this.isInitialized && !this.captureBtn.disabled) {
                e.preventDefault();
                this.captureAndAnalyze();
            }
        });
    }

    /**
     * Capture image from video and send for analysis
     */
    async captureAndAnalyze() {
        try {
            if (!this.video.videoWidth || !this.video.videoHeight) {
                this.resultDiv.innerHTML = `
                    <div class="alert alert-warning">
                        <i class="bi bi-exclamation-triangle"></i>
                        Camera is still initializing. Please wait 1-2 seconds and try again.
                    </div>
                `;
                this.enableCapture();
                return;
            }

            // Create canvas and draw current video frame
            const canvas = document.createElement('canvas');
            canvas.width = this.video.videoWidth;
            canvas.height = this.video.videoHeight;

            const ctx = canvas.getContext('2d');
            
            // Mirror the image (like a selfie camera)
            ctx.translate(canvas.width, 0);
            ctx.scale(-1, 1);
            ctx.drawImage(this.video, 0, 0);
            
            const imageData = canvas.toDataURL('image/jpeg', 0.9);

            // Show loading state
            this.showLoading();
            this.disableCapture();

            // Send image to server
            await this.sendForAnalysis(imageData);

        } catch (error) {
            console.error('Capture Error:', error);
            this.resultDiv.innerHTML = `
                <div class="alert alert-danger">
                    <i class="bi bi-exclamation-circle"></i>
                    Error capturing image. Please try again.
                </div>
            `;
            new ToastNotification('Failed to capture image', 'error');
            this.enableCapture();
        }
    }

    /**
     * Send captured image to backend for analysis
     */
    async sendForAnalysis(imageData) {
        try {
            const response = await fetch('/analyze', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded'
                },
                body: 'image_data=' + encodeURIComponent(imageData)
            });

            if (!response.ok) {
                let errorMessage = `Server error: ${response.status}`;
                try {
                    const errorData = await response.json();
                    if (errorData && errorData.error) {
                        errorMessage = errorData.error;
                    }
                } catch (e) {}
                throw new Error(errorMessage);
            }

            const data = await response.json();
            this.displayResults(data);
            new ToastNotification('Analysis complete!', 'success', 2000);

        } catch (error) {
            console.error('Analysis Error:', error);
            this.resultDiv.innerHTML = `
                <div class="alert alert-danger">
                    <i class="bi bi-exclamation-circle"></i>
                    <strong>Analysis Failed:</strong> ${error.message}
                </div>
            `;
            new ToastNotification('Analysis failed. Please try again.', 'error');
        } finally {
            this.enableCapture();
        }
    }

    /**
     * Display analysis results
     */
    displayResults(data) {
        if (data.error) {
            this.resultDiv.innerHTML = `
                <div class="alert alert-danger alert-dismissible fade show" role="alert">
                    <i class="bi bi-exclamation-circle"></i>
                    <strong>Error:</strong> ${data.error}
                    <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                </div>
            `;
            return;
        }

        const confidence = parseFloat(data.confidence) * 100;
        const confidenceClass = confidence > 80 ? 'bg-success' : confidence > 60 ? 'bg-warning' : 'bg-danger';

        let html = `
            <div class="result-card">
                <h4 class="result-title mb-3">
                    <i class="bi bi-check-circle-fill text-success"></i> Detection Result
                </h4>
                
                <div class="mb-4">
                    <h5 class="text-primary-green">${data.disease}</h5>
                </div>

                <div class="mb-4">
                    <label class="form-label fw-bold">Confidence Level</label>
                    <div class="progress" style="height: 35px; border-radius: 8px; overflow: hidden;">
                        <div 
                            class="progress-bar ${confidenceClass}" 
                            role="progressbar" 
                            style="width: ${confidence}%"
                            aria-valuenow="${confidence}" 
                            aria-valuemin="0" 
                            aria-valuemax="100"
                        >
                            <strong>${confidence.toFixed(2)}%</strong>
                        </div>
                    </div>
                </div>

                <div class="mb-4">
                    <label class="form-label fw-bold">Captured Image</label>
                    <img src="${data.image_url}" class="result-image img-fluid rounded" alt="Captured leaf">
                </div>
        `;

        // Add disease information if available
        if (data.info) {
            html += `
                <div class="disease-info-section">
                    <h5 class="mb-3"><i class="bi bi-book"></i> Disease Information</h5>
                    
                    <div class="accordion accordion-flush info-accordion" id="cameraAccordion">
                        <div class="accordion-item">
                            <h2 class="accordion-header">
                                <button class="accordion-button" type="button" data-bs-toggle="collapse" data-bs-target="#camDesc">
                                    <i class="bi bi-justify-left me-2"></i> Description
                                </button>
                            </h2>
                            <div id="camDesc" class="accordion-collapse collapse show" data-bs-parent="#cameraAccordion">
                                <div class="accordion-body small">
                                    ${data.info.description || 'No description available'}
                                </div>
                            </div>
                        </div>

                        <div class="accordion-item">
                            <h2 class="accordion-header">
                                <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#camPrev">
                                    <i class="bi bi-shield-check me-2"></i> Prevention
                                </button>
                            </h2>
                            <div id="camPrev" class="accordion-collapse collapse" data-bs-parent="#cameraAccordion">
                                <div class="accordion-body small">
                                    ${data.info.prevention || 'No prevention methods available'}
                                </div>
                            </div>
                        </div>

                        <div class="accordion-item">
                            <h2 class="accordion-header">
                                <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#camOrg">
                                    <i class="bi bi-leaf me-2"></i> Organic Treatment
                                </button>
                            </h2>
                            <div id="camOrg" class="accordion-collapse collapse" data-bs-parent="#cameraAccordion">
                                <div class="accordion-body small">
                                    ${data.info.organic || 'No organic treatments available'}
                                </div>
                            </div>
                        </div>

                        <div class="accordion-item">
                            <h2 class="accordion-header">
                                <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#camChem">
                                    <i class="bi bi-droplet me-2"></i> Chemical Treatment
                                </button>
                            </h2>
                            <div id="camChem" class="accordion-collapse collapse" data-bs-parent="#cameraAccordion">
                                <div class="accordion-body small">
                                    ${data.info.chemical || 'No chemical treatments available'}
                                </div>
                            </div>
                        </div>

                        ${data.info.products ? `
                        <div class="accordion-item">
                            <h2 class="accordion-header">
                                <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#camProd">
                                    <i class="bi bi-shop me-2"></i> Recommended Products
                                </button>
                            </h2>
                            <div id="camProd" class="accordion-collapse collapse" data-bs-parent="#cameraAccordion">
                                <div class="accordion-body small">
                                    ${data.info.products.supplements ? `
                                    <div class="mb-3">
                                        <h6 class="text-success mb-2"><i class="bi bi-capsule"></i> Supplements</h6>
                                        <div class="list-group list-group-sm">
                                            ${data.info.products.supplements.map(p => `
                                                <a href="${p.url}" target="_blank" rel="noopener noreferrer" class="list-group-item list-group-item-action">
                                                    ${p.name}
                                                    <i class="bi bi-box-arrow-up-right float-end"></i>
                                                </a>
                                            `).join('')}
                                        </div>
                                    </div>
                                    ` : ''}
                                    ${data.info.products.fungicides ? `
                                    <div class="mb-3">
                                        <h6 class="text-warning mb-2"><i class="bi bi-droplet"></i> Fungicides</h6>
                                        <div class="list-group list-group-sm">
                                            ${data.info.products.fungicides.map(p => `
                                                <a href="${p.url}" target="_blank" rel="noopener noreferrer" class="list-group-item list-group-item-action">
                                                    ${p.name}
                                                    <i class="bi bi-box-arrow-up-right float-end"></i>
                                                </a>
                                            `).join('')}
                                        </div>
                                    </div>
                                    ` : ''}
                                    <div class="alert alert-info small mt-2 mb-0">
                                        <i class="bi bi-info-circle me-2"></i>
                                        All links redirect to Amazon. Check availability in your region.
                                    </div>
                                </div>
                            </div>
                        </div>
                        ` : ''}
                    </div>
                </div>
            `;
        }

        html += `
            <div class="mt-4 d-flex gap-2 flex-wrap">
                <button type="button" class="btn btn-success flex-grow-1" onclick="location.reload()">
                    <i class="bi bi-arrow-clockwise"></i> Analyze Another
                </button>
                <a href="/resources" class="btn btn-primary flex-grow-1">
                    <i class="bi bi-shop"></i> View All Products
                </a>
                <a href="/history" class="btn btn-info flex-grow-1">
                    <i class="bi bi-clock-history"></i> View History
                </a>
            </div>
            </div>
        `;

        this.resultDiv.innerHTML = html;
        this.resultDiv.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }

    /**
     * Show loading animation
     */
    showLoading() {
        this.resultDiv.innerHTML = `
            <div class="text-center py-5">
                <div class="spinner-border text-success mb-3" role="status" style="width: 3rem; height: 3rem;">
                    <span class="visually-hidden">Analyzing...</span>
                </div>
                <p class="text-muted">Analyzing image... Please wait</p>
            </div>
        `;
    }

    /**
     * Enable capture button
     */
    enableCapture() {
        if (this.captureBtn) {
            this.captureBtn.disabled = false;
            this.captureBtn.innerHTML = '<i class="bi bi-camera-fill"></i> Capture & Analyze';
        }
    }

    /**
     * Disable capture button
     */
    disableCapture() {
        if (this.captureBtn) {
            this.captureBtn.disabled = true;
            this.captureBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>Processing...';
        }
    }

    /**
     * Stop camera stream and cleanup
     */
    stop() {
        if (this.stream) {
            this.stream.getTracks().forEach(track => track.stop());
            this.isInitialized = false;
        }
    }
}

// ============================================
// Initialize Camera on Load
// ============================================
let cameraManager = null;

window.addEventListener('load', () => {
    if (document.getElementById('video')) {
        cameraManager = new CameraManager();
        cameraManager.init();
    }
});

// Stop camera when leaving page
window.addEventListener('beforeunload', () => {
    if (cameraManager) {
        cameraManager.stop();
    }
});

// Stop camera when page becomes hidden (minimize, switch tabs)
document.addEventListener('visibilitychange', () => {
    if (document.hidden && cameraManager) {
        cameraManager.stop();
    } else if (!document.hidden && cameraManager && !cameraManager.isInitialized) {
        cameraManager.init();
    }
});
