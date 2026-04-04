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
        
        // Animation d'entrée
        mainApp.style.animation = 'fadeIn 0.5s ease';
    }, 500);
});
// Éléments DOM
const uploadSection = document.getElementById('uploadSection');
const resultSection = document.getElementById('resultSection');
const originalImage = document.getElementById('originalImage');
const resultCanvas = document.getElementById('resultCanvas');
const ctx = resultCanvas.getContext('2d');
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
document.getElementById('uploadBtn').addEventListener('click', () => {
    document.getElementById('imageInput').click();
});

document.getElementById('imageInput').addEventListener('change', (e) => {
    if (e.target.files[0]) processImage(e.target.files[0]);
});

document.getElementById('newImageBtn').addEventListener('click', reset);
document.getElementById('downloadBtn').addEventListener('click', downloadResult);

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
    const file = e.dataTransfer.files[0];
    if (file && file.type.startsWith('image/')) processImage(file);
});

async function processImage(file) {
    if (file.size > 50 * 1024 * 1024) {
        alert('L\'image est trop volumineuse (max 50MB)');
        return;
    }

    currentImageFile = file;

    // Afficher l'image originale
    const reader = new FileReader();
    reader.onload = (e) => {
        originalImage.src = e.target.result;
    };
    reader.readAsDataURL(file);

    // Cacher upload, afficher résultats
    uploadSection.style.display = 'none';
    resultSection.style.display = 'block';
    loadingOverlay.style.display = 'block';
    detectionResults.style.display = 'none';

    // Envoyer au serveur
    const formData = new FormData();
    formData.append('image', file);

    try {
        console.log('📤 Envoi de l\'image...');
        const response = await fetch('/api/detect', { method: 'POST', body: formData });
        const data = await response.json();
        console.log('📥 Réponse:', data);

        if (data.success) {
            displayResults(data, file);
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

function displayResults(data, file) {
    currentDetections = data.detections;

    // Mettre à jour le badge
    detectionBadge.textContent = `${data.count} détection(s)`;
    appleCountMain.textContent = data.count;

    // Dessiner sur le canvas
    const img = new Image();
    img.onload = () => {
        resultCanvas.width = img.width;
        resultCanvas.height = img.height;
        ctx.drawImage(img, 0, 0);

        let totalConfidence = 0;

        data.detections.forEach((detection, index) => {
            const [x1, y1, x2, y2] = detection.bbox;
            const confidence = detection.confidence;
            totalConfidence += confidence;

            // Rectangle rouge
            ctx.strokeStyle = '#ff6b6b';
            ctx.lineWidth = 3;
            ctx.strokeRect(x1, y1, x2 - x1, y2 - y1);

            // Label
            const label = `${detection.label} ${Math.round(confidence * 100)}%`;
            ctx.font = 'bold 14px Inter';
            const textWidth = ctx.measureText(label).width;
            ctx.fillStyle = 'rgba(255, 107, 107, 0.9)';
            ctx.fillRect(x1, y1 - 22, textWidth + 8, 20);
            ctx.fillStyle = 'white';
            ctx.fillText(label, x1 + 4, y1 - 8);
        });

        const avgConfidence = totalConfidence / (data.detections.length || 1);
        confidenceAvg.textContent = `${Math.round(avgConfidence * 100)}%`;
        confidenceFill.style.width = `${avgConfidence * 100}%`;

        // Afficher les détails
        if (data.detections.length > 0) {
            detectionsList.innerHTML = data.detections.map((det, index) => `
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

    img.src = URL.createObjectURL(file);
}

function reset() {
    uploadSection.style.display = 'flex';
    resultSection.style.display = 'none';
    document.getElementById('imageInput').value = '';
    if (currentImageFile) URL.revokeObjectURL(currentImageFile);
    ctx.clearRect(0, 0, resultCanvas.width, resultCanvas.height);
    originalImage.src = '';
}

function downloadResult() {
    if (!resultCanvas) return;
    const link = document.createElement('a');
    link.download = 'tomato_detection_result.png';
    link.href = resultCanvas.toDataURL();
    link.click();
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

// Vérifier le thème sauvegardé
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
        // Réinitialiser la session
        sessionStorage.removeItem('iaActivated');
        
        // Cacher l'application
        mainApp.style.display = 'none';
        themeToggleBtn.style.display = 'none';
        
        // Réinitialiser les valeurs
        reset();
        
        // Réinitialiser les champs
        document.getElementById('imageInput').value = '';
        if (currentImageFile) URL.revokeObjectURL(currentImageFile);
        if (originalImage) originalImage.src = '';
        if (resultCanvas) {
            const ctx = resultCanvas.getContext('2d');
            ctx.clearRect(0, 0, resultCanvas.width, resultCanvas.height);
        }
        
        // Afficher la page d'accueil
        landingPage.style.display = 'flex';
        landingPage.classList.remove('fade-out');
        
        // Animation de réapparition
        landingPage.style.animation = 'fadeInUp 0.5s ease';
        
        console.log('🔌 IA désactivée, retour à l\'accueil');
    });
}
checkServer();
