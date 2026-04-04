// Gestion de la page d'accueil et activation IA
const landingPage = document.getElementById('landingPage');
const mainApp = document.getElementById('mainApp');
const themeToggleBtn = document.getElementById('themeToggleBtn');
const activateBtn = document.getElementById('activateAI');
const API_BASE_URL = "https://tomato-detection-ai-production.up.railway.app";

// Vérifier si l'IA a déjà été activée (session)
if (sessionStorage.getItem('iaActivated') === 'true') {
    landingPage.style.display = 'none';
    mainApp.style.display = 'block';
    themeToggleBtn.style.display = 'block';
}

// Bouton d'activation
if (activateBtn) {
    activateBtn.addEventListener('click', () => {
        landingPage.classList.add('fade-out');
        setTimeout(() => {
            landingPage.style.display = 'none';
            mainApp.style.display = 'block';
            themeToggleBtn.style.display = 'block';
            sessionStorage.setItem('iaActivated', 'true');
            
            // Animation d'entrée
            mainApp.style.animation = 'fadeIn 0.5s ease';
        }, 500);
    });
}

// Éléments DOM
const uploadSection = document.getElementById('uploadSection');
const resultSection = document.getElementById('resultSection');
const originalImage = document.getElementById('originalImage');
const resultCanvas = document.getElementById('resultCanvas');
const ctx = resultCanvas ? resultCanvas.getContext('2d') : null;
const loadingOverlay = document.getElementById('loadingOverlay');
const detectionResults = document.getElementById('detectionResults');
const detectionBadge = document.getElementById('detectionBadge');
const appleCountMain = document.getElementById('appleCountMain');
const confidenceAvg = document.getElementById('confidenceAvg');
const confidenceFill = document.getElementById('confidenceFill');
const detectionsList = document.getElementById('detectionsList');

let currentImageFile = null;
let currentDetections = [];

// Boutons
const uploadBtn = document.getElementById('uploadBtn');
if (uploadBtn) {
    uploadBtn.addEventListener('click', () => {
        document.getElementById('imageInput').click();
    });
}

const imageInput = document.getElementById('imageInput');
if (imageInput) {
    imageInput.addEventListener('change', (e) => {
        if (e.target.files[0]) processImage(e.target.files[0]);
    });
}

const newImageBtn = document.getElementById('newImageBtn');
if (newImageBtn) {
    newImageBtn.addEventListener('click', reset);
}

const downloadBtn = document.getElementById('downloadBtn');
if (downloadBtn) {
    downloadBtn.addEventListener('click', downloadResult);
}

// Drag & Drop
const uploadCard = document.querySelector('.upload-card');
if (uploadCard) {
    uploadCard.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadCard.style.borderColor = '#ff6b6b';
    });
    uploadCard.addEventListener('dragleave', () => {
        uploadCard.style.borderColor = 'rgba(255, 255, 255, 0.2)';
    });
    uploadCard.addEventListener('drop', (e) => {
        e.preventDefault();
        const file = e.dataTransfer.files[0];
        if (file && file.type.startsWith('image/')) processImage(file);
    });
}

async function processImage(file) {
    if (!file) return;
    
    if (file.size > 50 * 1024 * 1024) {
        alert('L\'image est trop volumineuse (max 50MB)');
        return;
    }

    currentImageFile = file;

    // Afficher l'image originale
    const reader = new FileReader();
    reader.onload = (e) => {
        if (originalImage) {
            originalImage.src = e.target.result;
        }
    };
    reader.readAsDataURL(file);

    // Cacher upload, afficher résultats
    if (uploadSection) uploadSection.style.display = 'none';
    if (resultSection) resultSection.style.display = 'block';
    if (loadingOverlay) loadingOverlay.style.display = 'block';
    if (detectionResults) detectionResults.style.display = 'none';

    // Envoyer au serveur - CORRECTION ICI
    const formData = new FormData();
    formData.append('image', file);

    try {
        console.log('📤 Envoi de l\'image vers:', `${API_BASE_URL}/api/detect`);
        
        // CORRECTION: Utiliser formData au lieu de rien envoyer
        const response = await fetch(`${API_BASE_URL}/api/detect`, {
            method: 'POST',
            body: formData  // ← C'était manquant !
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        console.log('📥 Réponse:', data);

        if (data.success) {
            displayResults(data, file);
        } else {
            alert('Erreur: ' + (data.error || 'Erreur inconnue'));
            reset();
        }
    } catch (error) {
        console.error('❌ Erreur:', error);
        alert('Erreur de connexion au serveur: ' + error.message);
        reset();
    } finally {
        if (loadingOverlay) loadingOverlay.style.display = 'none';
    }
}

function displayResults(data, file) {
    currentDetections = data.detections || [];

    // Mettre à jour le badge
    if (detectionBadge) detectionBadge.textContent = `${data.count || 0} détection(s)`;
    if (appleCountMain) appleCountMain.textContent = data.count || 0;

    // Dessiner sur le canvas
    const img = new Image();
    img.onload = () => {
        if (!resultCanvas || !ctx) return;
        
        resultCanvas.width = img.width;
        resultCanvas.height = img.height;
        ctx.drawImage(img, 0, 0);

        let totalConfidence = 0;
        const detections = data.detections || [];

        detections.forEach((detection) => {
            const [x1, y1, x2, y2] = detection.bbox;
            const confidence = detection.confidence;
            totalConfidence += confidence;

            // Rectangle rouge
            ctx.strokeStyle = '#ff6b6b';
            ctx.lineWidth = 3;
            ctx.strokeRect(x1, y1, x2 - x1, y2 - y1);

            // Label
            const label = `${detection.label || 'Tomate'} ${Math.round(confidence * 100)}%`;
            ctx.font = 'bold 14px Inter';
            const textWidth = ctx.measureText(label).width;
            ctx.fillStyle = 'rgba(255, 107, 107, 0.9)';
            ctx.fillRect(x1, y1 - 22, textWidth + 8, 20);
            ctx.fillStyle = 'white';
            ctx.fillText(label, x1 + 4, y1 - 8);
        });

        const avgConfidence = totalConfidence / (detections.length || 1);
        if (confidenceAvg) confidenceAvg.textContent = `${Math.round(avgConfidence * 100)}%`;
        if (confidenceFill) confidenceFill.style.width = `${avgConfidence * 100}%`;

        // Afficher les détails
        if (detectionsList) {
            if (detections.length > 0) {
                detectionsList.innerHTML = detections.map((det, index) => `
                    <div class="detection-item">
                        <div class="detection-number">🍅 TOMATE #${index + 1}</div>
                        <div class="detection-info">
                            <strong>${det.label || 'Tomate'}</strong><br>
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
        }

        if (detectionResults) detectionResults.style.display = 'block';
    };

    img.src = URL.createObjectURL(file);
}

function reset() {
    if (uploadSection) uploadSection.style.display = 'flex';
    if (resultSection) resultSection.style.display = 'none';
    if (imageInput) imageInput.value = '';
    if (currentImageFile) URL.revokeObjectURL(currentImageFile);
    if (ctx && resultCanvas) ctx.clearRect(0, 0, resultCanvas.width, resultCanvas.height);
    if (originalImage) originalImage.src = '';
}

function downloadResult() {
    if (!resultCanvas) return;
    const link = document.createElement('a');
    link.download = 'tomato_detection_result.png';
    link.href = resultCanvas.toDataURL();
    link.click();
}

// Vérifier le serveur - CORRECTION ICI
async function checkServer() {
    try {
        // CORRECTION: Utiliser l'URL complète au lieu du chemin relatif
        const response = await fetch(`${API_BASE_URL}/api/health`);
        const data = await response.json();
        if (data.status === 'ok') {
            console.log('✅ Serveur connecté');
            return true;
        }
    } catch (error) {
        console.warn('⚠️ Serveur non accessible:', error.message);
        return false;
    }
}

// Dark Mode Toggle
const themeToggle = document.getElementById('themeToggle');
const themeIcon = document.getElementById('themeIcon');
const themeText = document.getElementById('themeText');

if (themeToggle) {
    // Vérifier le thème sauvegardé
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme === 'dark') {
        document.body.classList.add('dark-mode');
        if (themeIcon) themeIcon.textContent = '🌙';
        if (themeText) themeText.textContent = 'Mode sombre';
    }

    themeToggle.addEventListener('click', () => {
        document.body.classList.toggle('dark-mode');
        
        if (document.body.classList.contains('dark-mode')) {
            localStorage.setItem('theme', 'dark');
            if (themeIcon) themeIcon.textContent = '🌙';
            if (themeText) themeText.textContent = 'Mode sombre';
        } else {
            localStorage.setItem('theme', 'light');
            if (themeIcon) themeIcon.textContent = '🌞';
            if (themeText) themeText.textContent = 'Mode clair';
        }
    });
}

// Bouton de désactivation de l'IA
const deactivateBtn = document.getElementById('deactivateAI');

if (deactivateBtn) {
    deactivateBtn.addEventListener('click', () => {
        // Réinitialiser la session
        sessionStorage.removeItem('iaActivated');
        
        // Cacher l'application
        if (mainApp) mainApp.style.display = 'none';
        if (themeToggleBtn) themeToggleBtn.style.display = 'none';
        
        // Réinitialiser les valeurs
        reset();
        
        // Réinitialiser les champs
        if (imageInput) imageInput.value = '';
        if (currentImageFile) URL.revokeObjectURL(currentImageFile);
        if (originalImage) originalImage.src = '';
        if (resultCanvas && ctx) ctx.clearRect(0, 0, resultCanvas.width, resultCanvas.height);
        
        // Afficher la page d'accueil
        if (landingPage) {
            landingPage.style.display = 'flex';
            landingPage.classList.remove('fade-out');
            landingPage.style.animation = 'fadeInUp 0.5s ease';
        }
        
        console.log('🔌 IA désactivée, retour à l\'accueil');
    });
}

// Lancer la vérification du serveur
checkServer();
