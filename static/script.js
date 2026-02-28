// API Configuration
const API_BASE_URL = '/api';

// User Management
let currentUser = null;
let analysisHistory = [];
let currentDetectionTab = 'image';
let selectedFile = null;

// Initialize ONCE
document.addEventListener('DOMContentLoaded', () => {
    // Test backend connection
    testBackend();
    
    // Login form
    document.getElementById('loginForm').addEventListener('submit', (e) => {
        e.preventDefault();
        handleLogin();
    });

    // Signup form
    document.getElementById('signupForm').addEventListener('submit', (e) => {
        e.preventDefault();
        handleSignup();
    });

    // File upload
    const uploadArea = document.getElementById('uploadArea');
    const fileInput = document.getElementById('fileInput');

    uploadArea.addEventListener('click', () => fileInput.click());
    
    uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.style.borderColor = '#667eea';
    });

    uploadArea.addEventListener('dragleave', () => {
        uploadArea.style.borderColor = '#ccc';
    });

    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadArea.style.borderColor = '#ccc';
        const file = e.dataTransfer.files[0];
        if (file) handleFileSelect(file);
    });

    fileInput.addEventListener('change', (e) => {
        if (e.target.files[0]) handleFileSelect(e.target.files[0]);
    });
});

// Test backend connection
async function testBackend() {
    try {
        const response = await fetch(`${API_BASE_URL}/health`);
        if (response.ok) {
            console.log('✅ Backend connected!');
        } else {
            console.error('❌ Backend not responding');
        }
    } catch (error) {
        console.error('❌ Cannot connect to backend');
        console.log('Please run: cd backend && python app.py');
    }
}

// Switch between login/signup tabs
function switchTab(tab) {
    const tabs = document.querySelectorAll('.tab');
    const forms = document.querySelectorAll('.auth-form');
    
    tabs.forEach(t => t.classList.remove('active'));
    forms.forEach(f => f.classList.remove('active'));
    
    if (tab === 'login') {
        tabs[0].classList.add('active');
        document.getElementById('loginForm').classList.add('active');
    } else {
        tabs[1].classList.add('active');
        document.getElementById('signupForm').classList.add('active');
    }
    hideError();
}

// Show/hide error messages
function showError(message) {
    const errorMsg = document.getElementById('errorMsg');
    errorMsg.textContent = message;
    errorMsg.classList.add('show');
}

function hideError() {
    document.getElementById('errorMsg').classList.remove('show');
}

// Login with backend
async function handleLogin() {
    const email = document.getElementById('loginEmail').value;
    const password = document.getElementById('loginPassword').value;
    
    if (!email || !password) {
        showError('Please enter email and password');
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}/login`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            credentials: 'include',
            body: JSON.stringify({ email, password })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            currentUser = data.user;
            showDashboard();
        } else {
            showError(data.error || 'Invalid credentials');
        }
    } catch (error) {
        showError('Backend not running! Start it with: python app.py');
    }
}

// Signup with backend
async function handleSignup() {
    const name = document.getElementById('signupName').value;
    const email = document.getElementById('signupEmail').value;
    const password = document.getElementById('signupPassword').value;
    
    if (!name || !email || !password) {
        showError('Please fill all fields');
        return;
    }
    
    if (password.length < 6) {
        showError('Password must be at least 6 characters');
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}/register`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            credentials: 'include',
            body: JSON.stringify({ name, email, password })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            currentUser = data.user;
            showDashboard();
        } else {
            showError(data.error || 'Registration failed');
        }
    } catch (error) {
        showError('Backend not running! Start it with: python app.py');
    }
}

// Show dashboard
function showDashboard() {
    document.getElementById('loginPage').classList.remove('active');
    document.getElementById('dashboardPage').classList.add('active');
    document.getElementById('userName').textContent = currentUser.name;
}

// Logout
function logout() {
    currentUser = null;
    analysisHistory = [];
    selectedFile = null;
    document.getElementById('dashboardPage').classList.remove('active');
    document.getElementById('loginPage').classList.add('active');
    document.getElementById('loginEmail').value = '';
    document.getElementById('loginPassword').value = '';
}

// Switch between image/video detection
function switchDetectionTab(tab) {
    currentDetectionTab = tab;
    const tabs = document.querySelectorAll('.tab-detection');
    tabs.forEach(t => t.classList.remove('active'));
    
    if (tab === 'image') {
        tabs[0].classList.add('active');
        document.getElementById('fileInput').accept = 'image/*';
        document.getElementById('fileTypeLabel').textContent = 'Image';
        document.querySelector('.upload-icon').textContent = '📷';
    } else {
        tabs[1].classList.add('active');
        document.getElementById('fileInput').accept = 'video/*';
        document.getElementById('fileTypeLabel').textContent = 'Video';
        document.querySelector('.upload-icon').textContent = '🎥';
    }
    resetUpload();
}

// Handle file selection
function handleFileSelect(file) {
    selectedFile = file;
    
    document.getElementById('uploadPlaceholder').style.display = 'none';
    document.getElementById('previewContainer').style.display = 'block';
    document.getElementById('fileName').textContent = file.name;
    
    const reader = new FileReader();
    reader.onload = (e) => {
        if (file.type.startsWith('image/')) {
            const img = document.getElementById('previewImage');
            img.src = e.target.result;
            img.style.display = 'block';
            document.getElementById('previewVideo').style.display = 'none';
        } else {
            const video = document.getElementById('previewVideo');
            video.src = e.target.result;
            video.style.display = 'block';
            document.getElementById('previewImage').style.display = 'none';
        }
    };
    reader.readAsDataURL(file);
    
    document.getElementById('analyzeBtn').disabled = false;
}

// Reset upload area
function resetUpload() {
    selectedFile = null;
    document.getElementById('uploadPlaceholder').style.display = 'block';
    document.getElementById('previewContainer').style.display = 'none';
    document.getElementById('analyzeBtn').disabled = true;
    document.getElementById('resultsCard').style.display = 'none';
    document.getElementById('fileInput').value = '';
}

// Analyze file with backend
async function analyzeFile() {
    if (!selectedFile) return;
    
    showLoading();
    
    const formData = new FormData();
    formData.append('file', selectedFile);
    
    try {
        const response = await fetch(`${API_BASE_URL}/analyze`, {
            method: 'POST',
            credentials: 'include',
            body: formData
        });
        
        const result = await response.json();
        
        if (response.ok) {
            displayResult(result);
            addToHistory(result);
        } else {
            alert('Analysis failed: ' + result.error);
        }
    } catch (error) {
        alert('Backend not running! Start it with: python app.py');
    } finally {
        hideLoading();
    }
}

// Demo file analysis
function useDemoFile(type) {
    showLoading();
    
    setTimeout(() => {
        const isAI = type === 'ai';
        const result = {
            isAI,
            confidence: isAI ? '92.3' : '88.7',
            fileName: type === 'ai' ? 'ai_generated_landscape.jpg' : 'real_photograph.jpg',
            fileSize: '342.56 KB',
            fileType: 'image/jpeg',
            timestamp: new Date().toLocaleString(),
            indicators: isAI ? [
                { name: 'Pixel Patterns', score: 94.2, suspicious: true, description: 'Unusual patterns detected' },
                { name: 'Noise Analysis', score: 89.8, suspicious: true, description: 'AI noise signature' },
                { name: 'Artifact Detection', score: 91.5, suspicious: true, description: 'Generation artifacts found' },
                { name: 'Color Distribution', score: 85.3, suspicious: true, description: 'Unnatural colors' }
            ] : [
                { name: 'Pixel Patterns', score: 42.1, suspicious: false, description: 'Natural patterns' },
                { name: 'Noise Analysis', score: 38.6, suspicious: false, description: 'Camera noise present' },
                { name: 'Artifact Detection', score: 35.9, suspicious: false, description: 'No artifacts' },
                { name: 'Color Distribution', score: 51.2, suspicious: false, description: 'Natural colors' }
            ],
            verdict: isAI ? 'AI Generated' : 'Real/Human Created',
            details: isAI ? 'Strong AI signatures detected.' : 'Natural characteristics present.'
        };
        
        displayResult(result);
        addToHistory(result);
        hideLoading();
    }, 2000);
}

// Display results
function displayResult(result) {
    const resultsCard = document.getElementById('resultsCard');
    const resultContent = document.getElementById('resultContent');
    
    const indicatorsHTML = result.indicators.map(ind => `
        <div class="indicator">
            <div class="indicator-header">
                <span>${ind.name}</span>
                <span style="font-weight: bold; color: ${ind.suspicious ? '#e74c3c' : '#27ae60'}">
                    ${ind.score.toFixed(1)}%
                </span>
            </div>
            <div class="progress-bar">
                <div class="progress-fill ${ind.suspicious ? 'suspicious' : 'normal'}" 
                     style="width: ${ind.score}%"></div>
            </div>
        </div>
    `).join('');
    
    resultContent.innerHTML = `
        <div class="result-box ${result.isAI ? 'ai' : 'real'}">
            <div class="result-header">
                <div>
                    <div class="result-verdict">${result.verdict}</div>
                    <p style="margin-top: 5px; color: #666;">${result.details}</p>
                </div>
                <div style="text-align: right;">
                    <div class="result-confidence">${result.confidence}%</div>
                    <div style="font-size: 12px; color: #666;">Confidence</div>
                </div>
            </div>
        </div>
        
        <div class="metadata-grid">
            <div class="metadata-item">
                <div class="metadata-label">File Name</div>
                <div class="metadata-value">${result.fileName}</div>
            </div>
            <div class="metadata-item">
                <div class="metadata-label">File Size</div>
                <div class="metadata-value">${result.fileSize}</div>
            </div>
            <div class="metadata-item">
                <div class="metadata-label">File Type</div>
                <div class="metadata-value">${result.fileType}</div>
            </div>
            <div class="metadata-item">
                <div class="metadata-label">Analyzed</div>
                <div class="metadata-value">${result.timestamp}</div>
            </div>
        </div>
        
        <h4 style="margin-bottom: 15px; color: #666;">Detection Indicators:</h4>
        ${indicatorsHTML}
    `;
    
    resultsCard.style.display = 'block';
}

// Add to history
function addToHistory(result) {
    analysisHistory.unshift(result);
    if (analysisHistory.length > 5) analysisHistory.pop();
    renderHistory();
}


    historyList.innerHTML = analysisHistory.map((item, index) => `
        <div class="history-item">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <div>
                    <div style="font-weight:600;">${item.fileName}</div>
                    <div style="font-size:13px; color:#666;">
                        ${item.verdict}
                        <span style="font-weight:bold; color:${item.isAI ? '#e74c3c' : '#27ae60'}">
                            ${item.confidence}%
                        </span>
                    </div>
                </div>

                <button 
                    onclick="removeHistoryItem(${index})"
                    style="
                        background:none;
                        border:none;
                        color:#ef4444;
                        font-size:16px;
                        cursor:pointer;
                        font-weight:bold;
                    "
                >
                    ✖
                </button>
            </div>
        </div>
    `).join('');

// Remove history item
function removeHistoryItem(index) {
    analysisHistory.splice(index, 1);
    renderHistory();
}

function renderHistory() {
    const historyList = document.getElementById('historyList');

    if (analysisHistory.length === 0) {
        historyList.innerHTML = '<p class="no-history">No analysis history yet</p>';
        return;
    }

    historyList.innerHTML = analysisHistory.map((item, index) => `
        <div class="history-item" style="padding:18px; min-height:70px;">
            <div style="
                display:flex;
                justify-content:space-between;
                align-items:center;
                gap:20px;
            ">
                <!-- TEXT AREA -->
                <div style="flex:1; padding-right:20px;">
                    <div style="font-weight:600; margin-bottom:6px;">
                        ${item.fileName}
                    </div>
                    <div style="font-size:13px; color:#666;">
                        ${item.verdict}
                        <span style="
                            font-weight:bold;
                            margin-left:6px;
                            color:${item.isAI ? '#e74c3c' : '#27ae60'};
                        ">
                            ${item.confidence}%
                        </span>
                    </div>
                </div>

                <!-- DELETE BUTTON -->
                <button 
                    onclick="removeHistoryItem(${index})"
                    title="Remove"
                    style="
                        background:none;
                        border:none;
                        color:#ef4444;
                        font-size:18px;
                        cursor:pointer;
                        font-weight:bold;
                        padding:6px 10px;
                        border-radius:6px;
                    "
                >
                    ✖
                </button>
            </div>
        </div>
    `).join('');
}


// Loading overlay
function showLoading() {
    document.getElementById('loadingOverlay').classList.add('show');
}

function hideLoading() {
    document.getElementById('loadingOverlay').classList.remove('show');
}

