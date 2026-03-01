// ============================================
// AI Crop Disease Detection System
// Main JavaScript Utilities & Interactions
// ============================================

// ============================================
// Toast Notification System
// ============================================
class ToastNotification {
    constructor(message, type = 'info', duration = 4000) {
        this.message = message;
        this.type = type; // success, error, warning, info
        this.duration = duration;
        this.show();
    }

    show() {
        const container = this.getContainer();
        const toast = document.createElement('div');
        toast.className = `toast ${this.type}`;
        
        const icons = {
            'success': 'bi-check-circle-fill',
            'error': 'bi-exclamation-circle-fill',
            'warning': 'bi-exclamation-triangle-fill',
            'info': 'bi-info-circle-fill'
        };

        toast.innerHTML = `
            <div style="display: flex; align-items: center;">
                <i class="bi ${icons[this.type]} me-2"></i>
                <span>${this.message}</span>
                <button type="button" class="btn-close ms-auto" onclick="this.parentElement.parentElement.remove()"></button>
            </div>
        `;

        container.appendChild(toast);

        // Auto-remove after duration
        setTimeout(() => {
            toast.style.animation = 'slideOutRight 0.3s ease';
            setTimeout(() => toast.remove(), 300);
        }, this.duration);
    }

    getContainer() {
        let container = document.querySelector('.toast-container');
        if (!container) {
            container = document.createElement('div');
            container.className = 'toast-container';
            document.body.appendChild(container);
        }
        return container;
    }
}

// ============================================
// Upload Form Handler with Spinner
// ============================================
document.addEventListener('DOMContentLoaded', function() {
    const uploadForm = document.getElementById('uploadForm');
    
    if (uploadForm) {
        uploadForm.addEventListener('submit', function(e) {
            const submitBtn = uploadForm.querySelector('button[type=submit]');
            
            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.innerHTML = `
                    <span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
                    Analyzing Image...
                `;
                
                // Optional: Add some visual feedback
                uploadForm.style.opacity = '0.7';
            }
        });

        // Show preview and file info when image is selected
        const imageInput = document.getElementById('imageInput');
        if (imageInput) {
            imageInput.addEventListener('change', function() {
                if (this.files && this.files[0]) {
                    const file = this.files[0];
                    const fileSize = (file.size / 1024).toFixed(2);
                    
                    // Show file size info
                    const fileInfo = document.getElementById('fileInfo');
                    const fileName = document.getElementById('fileName');
                    if (fileInfo && fileName) {
                        fileName.textContent = `${file.name} (${fileSize} KB)`;
                        fileInfo.style.display = 'block';
                        
                        new ToastNotification(
                            `File selected: ${file.name}`,
                            'success',
                            2000
                        );
                    }
                }
            });
        }
    }
});

// ============================================
// Navigation Active State
// ============================================
document.addEventListener('DOMContentLoaded', function() {
    const navLinks = document.querySelectorAll('.navbar-nav .nav-link');
    const currentPath = window.location.pathname;

    navLinks.forEach(link => {
        // Get the href and remove trailing slashes
        const href = link.getAttribute('href').replace(/\/$/, '') || '/';
        const path = currentPath.replace(/\/$/, '') || '/';
        
        if (href === path) {
            link.classList.add('active');
            link.setAttribute('aria-current', 'page');
        } else {
            link.classList.remove('active');
        }
    });
});

// ============================================
// Smooth Scroll Behavior
// ============================================
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        const href = this.getAttribute('href');
        if (href !== '#' && document.querySelector(href)) {
            e.preventDefault();
            const target = document.querySelector(href);
            target.scrollIntoView({
                behavior: 'smooth',
                block: 'start'
            });
        }
    });
});

// ============================================
// Loading Spinner Management
// ============================================
function showLoadingSpinner(message = 'Processing...') {
    const spinner = document.createElement('div');
    spinner.className = 'spinner-container';
    spinner.id = 'loadingSpinner';
    spinner.innerHTML = `
        <div class="text-center">
            <div class="spinner-border text-primary" role="status" style="width: 3rem; height: 3rem;">
                <span class="visually-hidden">Loading...</span>
            </div>
            <p class="loading-text mt-3">${message}</p>
        </div>
    `;
    document.body.appendChild(spinner);
    return spinner;
}

function hideLoadingSpinner() {
    const spinner = document.getElementById('loadingSpinner');
    if (spinner) {
        spinner.style.animation = 'fadeOut 0.3s ease';
        setTimeout(() => spinner.remove(), 300);
    }
}

// ============================================
// Image Preview Modal Enhancement
// ============================================
document.addEventListener('DOMContentLoaded', function() {
    const imageModal = document.getElementById('imageModal');
    if (imageModal) {
        imageModal.addEventListener('show.bs.modal', function(event) {
            const button = event.relatedTarget;
            if (button) {
                const modalTitle = this.querySelector('.modal-title');
                const modalImage = this.querySelector('#modalImage');
                
                if (modalTitle && modalImage) {
                    // Blur background
                    document.body.style.filter = 'blur(0.5px)';
                }
            }
        });

        imageModal.addEventListener('hide.bs.modal', function() {
            document.body.style.filter = 'blur(0)';
        });
    }
});

// ============================================
// Responsive Table Handler
// ============================================
document.addEventListener('DOMContentLoaded', function() {
    const tables = document.querySelectorAll('.table-responsive table');
    tables.forEach(table => {
        table.addEventListener('scroll', function() {
            // Add shadow effect on scroll
            if (this.scrollLeft > 0) {
                table.style.boxShadow = 'inset 10px 0 10px -8px rgba(0, 0, 0, 0.1)';
            } else {
                table.style.boxShadow = 'none';
            }
        });
    });
});

// ============================================
// Form Validation Helper
// ============================================
function validateForm(formId) {
    const form = document.getElementById(formId);
    if (!form) return false;

    const requiredFields = form.querySelectorAll('[required]');
    let isValid = true;

    requiredFields.forEach(field => {
        if (!field.value.trim()) {
            field.classList.add('is-invalid');
            isValid = false;
        } else {
            field.classList.remove('is-invalid');
        }
    });

    return isValid;
}

// ============================================
// AJAX Request Handler
// ============================================
async function sendAjaxRequest(url, options = {}) {
    try {
        const defaultOptions = {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        };

        const config = { ...defaultOptions, ...options };
        const response = await fetch(url, config);

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        return await response.json();
    } catch (error) {
        console.error('AJAX Error:', error);
        new ToastNotification(
            'Error: Could not complete request',
            'error'
        );
        throw error;
    }
}

// ============================================
// Export Data Functionality
// ============================================
function exportTableAsCSV(tableId, filename = 'export.csv') {
    const table = document.getElementById(tableId);
    if (!table) return;

    let csv = [];
    const rows = table.querySelectorAll('tr');

    rows.forEach(row => {
        const cells = row.querySelectorAll('td, th');
        const rowData = Array.from(cells).map(cell => {
            let text = cell.textContent.trim();
            // Escape quotes and wrap in quotes if contains comma
            text = text.replace(/"/g, '""');
            return text.includes(',') ? `"${text}"` : text;
        });
        csv.push(rowData.join(','));
    });

    const csvContent = csv.join('\n');
    downloadFile(csvContent, filename, 'text/csv');

    new ToastNotification(
        `Table exported as ${filename}`,
        'success'
    );
}

function downloadFile(content, filename, type) {
    const blob = new Blob([content], { type });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
}

// ============================================
// Keyboard Shortcuts
// ============================================
document.addEventListener('keydown', function(event) {
    // Alt + U = Go to Upload
    if (event.altKey && event.key === 'u') {
        window.location.href = '/detect';
    }
    
    // Alt + C = Go to Camera
    if (event.altKey && event.key === 'c') {
        window.location.href = '/camera';
    }
    
    // Alt + H = Go to History
    if (event.altKey && event.key === 'h') {
        window.location.href = '/history';
    }
});

// ============================================
// Browser Storage Manager
// ============================================
const StorageManager = {
    set: function(key, value) {
        try {
            localStorage.setItem(key, JSON.stringify(value));
            return true;
        } catch (error) {
            console.error('Storage error:', error);
            return false;
        }
    },

    get: function(key) {
        try {
            const item = localStorage.getItem(key);
            return item ? JSON.parse(item) : null;
        } catch (error) {
            console.error('Storage error:', error);
            return null;
        }
    },

    remove: function(key) {
        try {
            localStorage.removeItem(key);
            return true;
        } catch (error) {
            console.error('Storage error:', error);
            return false;
        }
    },

    clear: function() {
        try {
            localStorage.clear();
            return true;
        } catch (error) {
            console.error('Storage error:', error);
            return false;
        }
    }
};

// ============================================
// Initialize tooltips and popovers (Bootstrap)
// ============================================
document.addEventListener('DOMContentLoaded', function() {
    // Initialize all tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Initialize all popovers
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
});

// ============================================
// Analytics and Logging (Development Only)
// ============================================
function logEvent(eventName, eventData = {}) {
    if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
        console.log(`[EVENT] ${eventName}:`, eventData);
    }
}

// Log page view
logEvent('page_view', { path: window.location.pathname });

// ============================================
// Error Handling
// ============================================
window.addEventListener('error', function(event) {
    console.error('Global error:', event.error);
    new ToastNotification(
        'An unexpected error occurred',
        'error'
    );
});
