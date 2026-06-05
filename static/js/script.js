// Global variables
let stream = null;
let faceImages = [];

// Camera functions
async function startCamera(videoElement) {
    try {
        stream = await navigator.mediaDevices.getUserMedia({ 
            video: { 
                width: 640, 
                height: 480,
                facingMode: 'user'
            } 
        });
        videoElement.srcObject = stream;
        return true;
    } catch (err) {
        console.error('Error accessing camera:', err);
        alert('Cannot access camera. Please ensure you have given camera permissions.');
        return false;
    }
}

function stopCamera() {
    if (stream) {
        stream.getTracks().forEach(track => track.stop());
        stream = null;
    }
}

function capturePhoto(videoElement, canvasElement) {
    const context = canvasElement.getContext('2d');
    canvasElement.width = videoElement.videoWidth;
    canvasElement.height = videoElement.videoHeight;
    context.drawImage(videoElement, 0, 0);
    
    return canvasElement.toDataURL('image/jpeg', 0.8);
}

// API functions
async function apiCall(endpoint, data) {
    try {
        const response = await fetch(endpoint, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data)
        });
        
        return await response.json();
    } catch (error) {
        console.error('API call error:', error);
        return { status: 'error', message: 'Network error: ' + error.message };
    }
}

// Utility functions
function showAlert(message, type = 'info') {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.querySelector('.container').insertBefore(alertDiv, document.querySelector('.container').firstChild);
    
    // Auto remove after 5 seconds
    setTimeout(() => {
        if (alertDiv.parentElement) {
            alertDiv.remove();
        }
    }, 5000);
}

function showLoading(element) {
    element.disabled = true;
    element.innerHTML = '<span class="spinner-border spinner-border-sm" role="status"></span> Processing...';
}

function hideLoading(element, originalText) {
    element.disabled = false;
    element.innerHTML = originalText;
}

// Face registration management
function addFaceImage(imageData) {
    if (faceImages.length >= 5) {
        showAlert('Maximum 5 face images allowed', 'warning');
        return;
    }
    
    faceImages.push(imageData);
    updateFacePreviews();
}

function removeFaceImage(index) {
    faceImages.splice(index, 1);
    updateFacePreviews();
}

function updateFacePreviews() {
    const container = document.getElementById('facePreviews');
    if (!container) return;
    
    container.innerHTML = '';
    
    faceImages.forEach((imageData, index) => {
        const div = document.createElement('div');
        div.className = 'd-inline-block position-relative me-2 mb-2';
        div.innerHTML = `
            <img src="${imageData}" class="photo-preview" alt="Face ${index + 1}">
            <button type="button" class="btn btn-danger btn-sm position-absolute top-0 end-0" 
                    onclick="removeFaceImage(${index})">
                <i class="fas fa-times"></i>
            </button>
        `;
        container.appendChild(div);
    });
    
    // Update counter
    const counter = document.getElementById('photoCounter');
    if (counter) {
        counter.textContent = `${faceImages.length} photos captured`;
        counter.className = faceImages.length >= 2 ? 'text-success fw-bold' : 'text-warning';
    }
}

// Navigation function
function navigateTo(url) {
    window.location.href = url;
}

// System health check
async function checkSystemHealth() {
    try {
        const response = await fetch('/api/health');
        const data = await response.json();
        
        if (data.status === 'healthy') {
            return {
                operational: true,
                employees: data.employees_count,
                checkins: data.today_checkins,
                time: data.time_display
            };
        }
    } catch (error) {
        console.error('Health check failed:', error);
    }
    
    return { operational: false };
}

// Attendance functions
async function loadAttendanceRecords(date = null) {
    try {
        if (!date) {
            const today = new Date().toISOString().split('T')[0];
            date = today;
        }
        
        const response = await fetch(`/api/attendance?date=${date}`);
        const data = await response.json();
        
        if (data.status === 'success') {
            return data.records;
        }
    } catch (error) {
        console.error('Error loading attendance:', error);
    }
    
    return [];
}

async function loadEmployeeList() {
    try {
        const response = await fetch('/api/employees');
        const data = await response.json();
        
        if (data.status === 'success') {
            return data.employees;
        }
    } catch (error) {
        console.error('Error loading employees:', error);
    }
    
    return [];
}

async function loadSystemStats() {
    try {
        const response = await fetch('/api/stats');
        const data = await response.json();
        
        if (data.status === 'success') {
            return data.stats;
        }
    } catch (error) {
        console.error('Error loading stats:', error);
    }
    
    return null;
}

// Registration form validation
function validateRegistrationForm(employeeId, name, department) {
    if (!employeeId.trim()) {
        showAlert('Employee ID is required', 'warning');
        return false;
    }
    
    if (!name.trim()) {
        showAlert('Employee name is required', 'warning');
        return false;
    }
    
    if (!department.trim()) {
        showAlert('Department is required', 'warning');
        return false;
    }
    
    if (faceImages.length < 2) {
        showAlert('At least 2 face photos are required for registration', 'warning');
        return false;
    }
    
    return true;
}

// Check-in functions
async function processCheckin(faceImage) {
    try {
        const response = await fetch('/api/checkin', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                face_image: faceImage,
                checkin_type: 'IN'
            })
        });
        
        return await response.json();
    } catch (error) {
        console.error('Check-in error:', error);
        return { status: 'error', message: 'Network error during check-in' };
    }
}

// Date formatting utilities
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-IN', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    });
}

function formatTime(dateString) {
    const date = new Date(dateString);
    return date.toLocaleTimeString('en-IN', {
        hour: '2-digit',
        minute: '2-digit',
        hour12: false
    });
}

// Confidence score formatting
function formatConfidence(score) {
    if (score >= 80) return `<span class="badge bg-success">${score.toFixed(2)}</span>`;
    if (score >= 60) return `<span class="badge bg-warning">${score.toFixed(2)}</span>`;
    return `<span class="badge bg-danger">${score.toFixed(2)}</span>`;
}

// Data export functions (for future use)
function exportAttendanceCSV(records) {
    if (records.length === 0) {
        showAlert('No records to export', 'warning');
        return;
    }
    
    let csvContent = "Employee ID,Name,Department,Time,Confidence,Type\n";
    
    records.forEach(record => {
        csvContent += `"${record.employee_id}","${record.name}","${record.department}","${record.time_display}",${record.confidence},"${record.checkin_type}"\n`;
    });
    
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `attendance_${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
    window.URL.revokeObjectURL(url);
}

// Search and filter functions
function filterEmployees(employees, searchTerm) {
    if (!searchTerm) return employees;
    
    const term = searchTerm.toLowerCase();
    return employees.filter(emp => 
        emp.employee_id.toLowerCase().includes(term) ||
        emp.name.toLowerCase().includes(term) ||
        emp.department.toLowerCase().includes(term)
    );
}

function filterAttendance(records, searchTerm) {
    if (!searchTerm) return records;
    
    const term = searchTerm.toLowerCase();
    return records.filter(record => 
        record.employee_id.toLowerCase().includes(term) ||
        record.name.toLowerCase().includes(term) ||
        record.department.toLowerCase().includes(term)
    );
}

// Initialize camera on pages that need it
document.addEventListener('DOMContentLoaded', function() {
    const video = document.getElementById('video');
    const startCameraBtn = document.getElementById('startCamera');
    
    if (video && startCameraBtn) {
        startCameraBtn.addEventListener('click', async function() {
            const success = await startCamera(video);
            if (success) {
                this.style.display = 'none';
                const cameraControls = document.getElementById('cameraControls');
                if (cameraControls) {
                    cameraControls.style.display = 'block';
                }
            }
        });
    }
    
    // Clear face images when leaving registration page
    const registerPage = document.getElementById('registrationPage');
    if (registerPage) {
        window.addEventListener('beforeunload', function() {
            faceImages = [];
        });
    }
    
    // Update system info on home page
    const systemInfo = document.getElementById('systemInfo');
    if (systemInfo) {
        checkSystemHealth().then(health => {
            if (health.operational) {
                systemInfo.innerHTML = `
                    <p><strong>Status:</strong> <span class="text-success">Operational</span></p>
                    <p><strong>Employees Registered:</strong> ${health.employees}</p>
                    <p><strong>Today's Check-ins:</strong> ${health.checkins}</p>
                    <p><strong>Current Time (IST):</strong> ${health.time}</p>
                `;
            } else {
                systemInfo.innerHTML = `
                    <p class="text-danger"><i class="fas fa-exclamation-triangle"></i> Unable to connect to server</p>
                `;
            }
        });
    }
    
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    const tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Auto-refresh for attendance and stats pages
    const attendancePage = document.querySelector('[data-page="attendance"]');
    const statsPage = document.querySelector('[data-page="stats"]');
    
    if (attendancePage || statsPage) {
        // Refresh every 30 seconds
        setInterval(() => {
            if (attendancePage) {
                const refreshBtn = document.getElementById('refreshBtn');
                if (refreshBtn) refreshBtn.click();
            }
            if (statsPage) {
                const refreshStats = document.getElementById('refreshStats');
                if (refreshStats) refreshStats.click();
            }
        }, 30000);
    }
});

// Error handling
window.addEventListener('error', function(e) {
    console.error('Global error:', e.error);
});

// Network status monitoring
window.addEventListener('online', function() {
    showAlert('Connection restored', 'success');
});

window.addEventListener('offline', function() {
    showAlert('Connection lost. Some features may not work.', 'warning');
});

// Service Worker registration (for future PWA capabilities)
if ('serviceWorker' in navigator) {
    window.addEventListener('load', function() {
        navigator.serviceWorker.register('/sw.js')
            .then(function(registration) {
                console.log('ServiceWorker registration successful');
            })
            .catch(function(error) {
                console.log('ServiceWorker registration failed: ', error);
            });
    });
}

// Performance monitoring
const perfObserver = new PerformanceObserver((list) => {
    list.getEntries().forEach((entry) => {
        console.log(`${entry.name}: ${entry.duration}ms`);
    });
});

perfObserver.observe({ entryTypes: ['measure', 'navigation'] });

// Export functions to global scope for HTML onclick attributes
window.navigateTo = navigateTo;
window.addFaceImage = addFaceImage;
window.removeFaceImage = removeFaceImage;
window.exportAttendanceCSV = exportAttendanceCSV;
window.formatConfidence = formatConfidence;
window.formatDate = formatDate;
window.formatTime = formatTime;