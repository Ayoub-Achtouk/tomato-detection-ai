// Gestion de la page d'accueil et activation IA
const landingPage = document.getElementById('landingPage');
const mainApp = document.getElementById('mainApp');
const themeToggleBtn = document.getElementById('themeToggleBtn');
const activateBtn = document.getElementById('activateAI');

// Vérifier si l'IA a déjà été activée (session)
if (sessionStorage.getItem('iaActivated') === 'true') {
    landingPage.style.display = 'none';
    mainApp.style.display = 'block';
    themeToggleBtn.style.display = 'block';
}

// Bouton d'activation
activateBtn.addEventListener('click', () => {
    landingPage.classList.add('fade-out');
    setTimeout(() => {
        landingPage.style.display = 'none';
        mainApp.style.display = 'block';
        themeToggleBtn.style.display = 'block';
        sessionStorage.setItem('iaActivated', 'true');
        mainApp.style.animation = 'fadeIn 0.5s ease';
    }, 500);
});

// Éléments DOM
const uploadSection = document.getElementById('uploadSection');
const resultSection = document.getElementById('resultSection');

const originalImage = document.getElementById('originalImage');
const originalVideo = document.getElementById('originalVideo');

const resultCanvas = document.getElementById('resultCanvas');
const ctx = resultCanvas.getContext('2d');
//const resultVideo = document.getElementById('resultVideo');

const originalTitle = document.getElementById('originalTitle');
const resultTitle = document.getElementById('resultTitle');

const loadingOverlay = document.getElementById('loadingOverlay');
const detectionResults = document.getElementById('detectionResults');
const detectionBadge = document.getElementById('detectionBadge');
const appleCountMain = document.getElementById('appleCountMain');
const confidenceAvg = document.getElementById('confidenceAvg');
const confidenceFill = document.getElementById('confidenceFill');
const detectionsList = document.getElementById('detectionsList');

const uploadBtn = document.getElementById('uploadBtn');
const uploadVideoBtn = document.getElementById('uploadVideoBtn');
const imageInput = document.getElementById('imageInput');
const videoInput = document.getElementById('videoInput');
const newImageBtn = document.getElementById('newImageBtn');
const downloadBtn = document.getElementById('downloadBtn');

let currentImageFile = null;
let currentVideoFile = null;
let currentDetections = [];
let currentMode = null; // 'image' ou 'video'
let currentImageObjectUrl = null;
let currentVideoObjectUrl = null;

// Boutons
uploadBtn.addEventListener('click', () => {
    imageInput.click();
});

uploadVideoBtn.addEventListener('click', () => {
    videoInput.click();
});

imageInput.addEventListener('change', (e) => {
    if (e.target.files[0]) {
        processImage(e.target.files[0]);
    }
});

videoInput.addEventListener('change', (e) => {
    if (e.target.files[0]) {
        processVideo(e.target.files[0]);
    }
});

newImageBtn.addEventListener('click', reset);
downloadBtn.addEventListener('click', downloadResult);

// Drag & Drop
const uploadCard = document.querySelector('.upload-card');

uploadCard.addEventListener('dragover', (e) => {
    e.preventDefault();
    uploadCard.style.borderColor = '#ff6b6b';
});

uploadCard.addEventListener('dragleave', () => {
    uploadCard.style.borderColor = 'rgba(255, 255, 255, 0.2)';
});

uploadCard.addEventListener('drop', (e) => {
    e.preventDefault();
    uploadCard.style.borderColor = 'rgba(255, 255, 255, 0.2)';

    const file = e.dataTransfer.files[0];
    if (!file) return;

    if (file.type.startsWith('image/')) {
        processImage(file);
    } else if (file.type.startsWith('video/')) {
        processVideo(file);
    } else {
        alert('Format non supporté. Choisissez une image ou une vidéo.');
    }
});

function showImageMode() {
    originalImage.style.display = 'block';
    resultCanvas.style.display = 'block';

    originalVideo.style.display = 'none';
    originalVideo.pause();
    originalVideo.removeAttribute('src');
    originalVideo.load();

    resultVideo.style.display = 'none';
    resultVideo.pause();
    resultVideo.removeAttribute('src');
    resultVideo.load();

    originalTitle.textContent = '📸 Image originale';
    resultTitle.textContent = '🎯 Résultat d’analyse';
}
//function showVideoMode() {
  //  originalVideo.style.display = 'block';
    //resultVideo.style.display = 'block';

    //originalImage.style.display = 'none';
    //originalImage.removeAttribute('src');

    //resultCanvas.style.display = 'none';
    //ctx.clearRect(0, 0, resultCanvas.width, resultCanvas.height);

    //originalTitle.textContent = '🎥 Vidéo originale';
    //resultTitle.textContent = '🎬 Vidéo analysée';
//}
async function processImage(file) {
    if (file.size > 50 * 1024 * 1024) {
        alert("L'image est trop volumineuse (max 50MB)");
        return;
    }

    resetMediaOnly();
    currentMode = 'image';
    currentImageFile = file;

    showImageMode();

    if (currentImageObjectUrl) {
        URL.revokeObjectURL(currentImageObjectUrl);
    }
    currentImageObjectUrl = URL.createObjectURL(file);
    originalImage.src = currentImageObjectUrl;

    uploadSection.style.display = 'none';
    resultSection.style.display = 'block';
    loadingOverlay.style.display = 'block';
    detectionResults.style.display = 'none';

    const formData = new FormData();
    formData.append('image', file);

    try {
        console.log("📤 Envoi de l'image...");
        const response = await fetch('/api/detect', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();
        console.log('📥 Réponse:', data);

        if (data.success) {
            displayImageResults(data);
        } else {
            alert('Erreur: ' + data.error);
            reset();
        }
    } catch (error) {
        console.error('❌ Erreur:', error);
        alert('Erreur de connexion au serveur');
        reset();
    } finally {
        loadingOverlay.style.display = 'none';
    }
}

function displayImageResults(data) {
    currentDetections = data.detections || [];

    detectionBadge.textContent = `${data.count} détection(s)`;
    appleCountMain.textContent = data.count;

    const img = new Image();
    img.onload = () => {
        resultCanvas.width = img.width;
        resultCanvas.height = img.height;
        ctx.clearRect(0, 0, resultCanvas.width, resultCanvas.height);
        ctx.drawImage(img, 0, 0);

        let totalConfidence = 0;

        currentDetections.forEach((detection) => {
            const [x1, y1, x2, y2] = detection.bbox;
            const confidence = detection.confidence;
            totalConfidence += confidence;

            ctx.strokeStyle = '#ff6b6b';
            ctx.lineWidth = 3;
            ctx.strokeRect(x1, y1, x2 - x1, y2 - y1);

            const label = `${detection.label} ${Math.round(confidence * 100)}%`;
            ctx.font = 'bold 14px Inter';
            const textWidth = ctx.measureText(label).width;
            ctx.fillStyle = 'rgba(255, 107, 107, 0.9)';
            ctx.fillRect(x1, Math.max(0, y1 - 22), textWidth + 8, 20);
            ctx.fillStyle = 'white';
            ctx.fillText(label, x1 + 4, Math.max(12, y1 - 8));
        });

        const avgConfidence = totalConfidence / (currentDetections.length || 1);
        confidenceAvg.textContent = `${Math.round(avgConfidence * 100)}%`;
        confidenceFill.style.width = `${avgConfidence * 100}%`;

        if (currentDetections.length > 0) {
            detectionsList.innerHTML = currentDetections.map((det, index) => `
                <div class="detection-item">
                    <div class="detection-number">TOMATE #${index + 1}</div>
                    <div class="detection-info">
                        <strong>🍅 ${det.label}</strong><br>
                        Confiance: ${Math.round(det.confidence * 100)}%<br>
                        Position: (${Math.round(det.bbox[0])}, ${Math.round(det.bbox[1])})
                    </div>
                </div>
            `).join('');
        } else {
            detectionsList.innerHTML = `
                <div class="detection-item">
                    <div class="detection-info">
                        😢 Aucune tomate détectée dans cette image
                    </div>
                </div>
            `;
        }

        detectionResults.style.display = 'block';
    };

    // Si ton backend renvoie une image annotée déjà prête
    if (data.image_url) {
        img.src = data.image_url;
    } else if (currentImageObjectUrl) {
        img.src = currentImageObjectUrl;
    }
}

async function processVideo(file) {
    if (file.size > 200 * 1024 * 1024) {
        alert('La vidéo est trop volumineuse (max 200MB)');
        return;
    }

    resetMediaOnly();
    currentMode = 'video';
    currentVideoFile = file;

    //showVideoMode();

    if (currentVideoObjectUrl) {
        URL.revokeObjectURL(currentVideoObjectUrl);
    }
    currentVideoObjectUrl = URL.createObjectURL(file);
    originalVideo.src = currentVideoObjectUrl;

    uploadSection.style.display = 'none';
    resultSection.style.display = 'block';
    loadingOverlay.style.display = 'block';
    detectionResults.style.display = 'none';

    const formData = new FormData();
    formData.append('video', file);

    try {
        console.log('📤 Envoi de la vidéo...');
        const response = await fetch('/api/detect-video', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();
        console.log('📥 Réponse vidéo:', data);

        if (data.success) {
            displayVideoResults(data);
        } else {
            alert('Erreur: ' + data.error);
            reset();
        }
    } catch (error) {
        console.error('❌ Erreur vidéo:', error);
        alert('Erreur de connexion au serveur');
        reset();
    } finally {
        loadingOverlay.style.display = 'none';
    }
}
//function displayVideoResults(data) {

function resetMediaOnly() {
    currentDetections = [];

    if (currentImageObjectUrl) {
        URL.revokeObjectURL(currentImageObjectUrl);
        currentImageObjectUrl = null;
    }

    if (currentVideoObjectUrl) {
        URL.revokeObjectURL(currentVideoObjectUrl);
        currentVideoObjectUrl = null;
    }

    originalImage.removeAttribute('src');
    originalVideo.pause();
    originalVideo.removeAttribute('src');
    originalVideo.load();

    resultVideo.pause();
    resultVideo.removeAttribute('src');
    resultVideo.load();

    ctx.clearRect(0, 0, resultCanvas.width, resultCanvas.height);
}

function reset() {
    resetMediaOnly();

    uploadSection.style.display = 'flex';
    resultSection.style.display = 'none';
    detectionResults.style.display = 'none';
    loadingOverlay.style.display = 'none';

    imageInput.value = '';
    videoInput.value = '';

    currentImageFile = null;
    currentVideoFile = null;
    currentMode = null;

    detectionBadge.textContent = '0 détection(s)';
    appleCountMain.textContent = '0';
    confidenceAvg.textContent = '0%';
    confidenceFill.style.width = '0%';
    detectionsList.innerHTML = '';

    showImageMode();
}

function downloadResult() {
    if (currentMode === 'image') {
        const link = document.createElement('a');
        link.download = 'tomato_detection_result.png';
        link.href = resultCanvas.toDataURL('image/png');
        link.click();
        return;
    }

    if (currentMode === 'video' && resultVideo.src) {
        const link = document.createElement('a');
        link.download = 'tomato_detection_result.mp4';
        link.href = resultVideo.src;
        link.click();
        return;
    }

    alert('Aucun résultat à télécharger.');
}

// Vérifier le serveur
async function checkServer() {
    try {
        const response = await fetch('/api/health');
        const data = await response.json();
        if (data.status === 'ok') {
            console.log('✅ Serveur connecté');
        }
    } catch (error) {
        console.warn('⚠️ Serveur non accessible');
    }
}

// Dark Mode Toggle
const themeToggle = document.getElementById('themeToggle');
const themeIcon = document.getElementById('themeIcon');
const themeText = document.getElementById('themeText');

const savedTheme = localStorage.getItem('theme');
if (savedTheme === 'dark') {
    document.body.classList.add('dark-mode');
    themeIcon.textContent = '🌙';
    themeText.textContent = 'Mode sombre';
}

themeToggle.addEventListener('click', () => {
    document.body.classList.toggle('dark-mode');

    if (document.body.classList.contains('dark-mode')) {
        localStorage.setItem('theme', 'dark');
        themeIcon.textContent = '🌙';
        themeText.textContent = 'Mode sombre';
    } else {
        localStorage.setItem('theme', 'light');
        themeIcon.textContent = '🌞';
        themeText.textContent = 'Mode clair';
    }
});

// Bouton de désactivation de l'IA
const deactivateBtn = document.getElementById('deactivateAI');

if (deactivateBtn) {
    deactivateBtn.addEventListener('click', () => {
        sessionStorage.removeItem('iaActivated');

        mainApp.style.display = 'none';
        themeToggleBtn.style.display = 'none';

        reset();

        landingPage.style.display = 'flex';
        landingPage.classList.remove('fade-out');
        landingPage.style.animation = 'fadeInUp 0.5s ease';

        console.log("🔌 IA désactivée, retour à l'accueil");
    });
}

checkServer();
