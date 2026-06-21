from flask import Flask, request, jsonify, render_template_string
from analyzer import analyze_from_bytes
import traceback
import json

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16 MB máx

HTML = """<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>DeepFace — Análisis Facial en Tiempo Real</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
      background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
      min-height: 100vh;
      color: #e4e4e4;
      padding: 2rem 1rem;
    }
    header {
      text-align: center;
      margin-bottom: 1.5rem;
      animation: fadeInDown 0.8s ease;
    }
    header h1 {
      font-size: 2.2rem;
      color: #00d4ff;
      margin-bottom: 0.3rem;
      text-shadow: 0 0 20px rgba(0, 212, 255, 0.3);
    }
    .mode-toggle {
      display: flex;
      justify-content: center;
      gap: 1rem;
      margin-bottom: 1rem;
    }
    .mode-btn {
      padding: 0.6rem 1.2rem;
      background: rgba(255,255,255,0.1);
      border: 1px solid #00d4ff;
      border-radius: 20px;
      color: #e4e4e4;
      cursor: pointer;
      transition: all 0.3s ease;
    }
    .mode-btn.active {
      background: #00d4ff;
      color: #1a1a2e;
      font-weight: 600;
    }
    .container {
      max-width: 800px;
      margin: 0 auto;
      background: rgba(255, 255, 255, 0.05);
      border-radius: 20px;
      padding: 1.5rem;
      backdrop-filter: blur(10px);
      border: 1px solid rgba(255, 255, 255, 0.1);
      animation: fadeIn 1s ease;
    }
    #file-input { display: none; }
    .upload-label {
      display: block;
      padding: 1.5rem;
      border: 2px dashed #00d4ff;
      border-radius: 15px;
      text-align: center;
      cursor: pointer;
      transition: all 0.3s ease;
      background: rgba(0, 212, 255, 0.05);
      margin-bottom: 1rem;
    }
    .upload-label:hover {
      background: rgba(0, 212, 255, 0.1);
    }
    #camera-container {
      display: none;
      margin-bottom: 1rem;
    }
    #video {
      width: 100%;
      border-radius: 15px;
      background: #000;
    }
    .camera-controls {
      display: flex;
      gap: 0.5rem;
      margin-top: 0.5rem;
    }
    .camera-btn {
      flex: 1;
      padding: 0.8rem;
      background: linear-gradient(135deg, #00d4ff 0%, #0099cc 100%);
      border: none;
      border-radius: 10px;
      color: #fff;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.3s ease;
    }
    .camera-btn:disabled {
      background: #444;
      cursor: not-allowed;
    }
    #analyze-btn {
      display: block;
      width: 100%;
      padding: 1rem;
      font-size: 1.1rem;
      font-weight: 600;
      color: #fff;
      background: linear-gradient(135deg, #00d4ff 0%, #0099cc 100%);
      border: none;
      border-radius: 10px;
      cursor: pointer;
      transition: all 0.3s ease;
      margin-bottom: 1rem;
    }
    #analyze-btn:disabled {
      background: #444;
      cursor: not-allowed;
    }
    #results { text-align: center; }
    #results img {
      max-width: 100%;
      border-radius: 15px;
      box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
      margin-bottom: 1rem;
      animation: scaleIn 0.5s ease;
    }
    .face-card {
      background: rgba(255, 255, 255, 0.08);
      padding: 1rem;
      border-radius: 10px;
      margin: 0.5rem 0;
      text-align: left;
    }
    .face-card h3 { color: #00d4ff; margin-bottom: 0.5rem; }
    .face-card p { margin: 0.2rem 0; }
    .error {
      color: #ff6b6b;
      background: rgba(255, 107, 107, 0.1);
      padding: 1rem;
      border-radius: 10px;
      margin-top: 1rem;
    }
    @keyframes fadeIn { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }
    @keyframes fadeInDown { from { opacity: 0; transform: translateY(-20px); } to { opacity: 1; transform: translateY(0); } }
    @keyframes scaleIn { from { opacity: 0; transform: scale(0.95); } to { opacity: 1; transform: scale(1); } }
    @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }
    @media (max-width: 600px) {
      header h1 { font-size: 1.8rem; }
      .container { padding: 1rem; }
    }
  </style>
</head>
<body>
  <header>
    <h1>DeepFace — Análisis Facial</h1>
    <p>Género · Etnia · Edad · Emoción</p>
  </header>
  <div class="mode-toggle">
    <button class="mode-btn active" data-mode="upload">Subir Imagen</button>
    <button class="mode-btn" data-mode="camera">Cámara en Vivo</button>
  </div>
  <div class="container">
    <div id="upload-container">
      <label for="file-input" class="upload-label" id="drop-area">📸 Haz clic o arrastra una imagen</label>
      <input type="file" id="file-input" accept="image/*">
    </div>
    <div id="camera-container">
      <video id="video" autoplay playsinline></video>
      <canvas id="canvas" style="display:none;"></canvas>
      <div class="camera-controls">
        <button id="start-camera" class="camera-btn">Iniciar Cámara</button>
        <button id="capture-frame" class="camera-btn" disabled>Capturar y Analizar</button>
        <button id="stop-camera" class="camera-btn" disabled>Detener Cámara</button>
      </div>
    </div>
    <button id="analyze-btn" disabled>Analizar Imagen</button>
    <div id="results"></div>
  </div>
  <script>
    const fileInput = document.getElementById('file-input');
    const analyzeBtn = document.getElementById('analyze-btn');
    const resultsDiv = document.getElementById('results');
    const dropArea = document.getElementById('drop-area');
    const video = document.getElementById('video');
    const canvas = document.getElementById('canvas');
    const startCameraBtn = document.getElementById('start-camera');
    const captureFrameBtn = document.getElementById('capture-frame');
    const stopCameraBtn = document.getElementById('stop-camera');
    const uploadContainer = document.getElementById('upload-container');
    const cameraContainer = document.getElementById('camera-container');
    const modeBtns = document.querySelectorAll('.mode-btn');
    let selectedFile = null;
    let stream = null;

    modeBtns.forEach(btn => {
      btn.addEventListener('click', () => {
        modeBtns.forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        const mode = btn.dataset.mode;
        uploadContainer.style.display = mode === 'upload' ? 'block' : 'none';
        cameraContainer.style.display = mode === 'camera' ? 'block' : 'none';
        if (mode === 'upload') {
          stopCamera();
          analyzeBtn.textContent = 'Analizar Imagen';
        } else {
          analyzeBtn.textContent = 'Analizar Frame';
        }
      });
    });

    fileInput.addEventListener('change', e => {
      selectedFile = e.target.files[0];
      if (selectedFile) {
        analyzeBtn.disabled = false;
        dropArea.textContent = selectedFile.name;
      }
    });

    dropArea.addEventListener('dragover', e => { e.preventDefault(); dropArea.style.background = 'rgba(0, 212, 255, 0.15)'; });
    dropArea.addEventListener('dragleave', e => { e.preventDefault(); dropArea.style.background = ''; });
    dropArea.addEventListener('drop', e => {
      e.preventDefault();
      dropArea.style.background = '';
      selectedFile = e.dataTransfer.files[0];
      if (selectedFile) {
        fileInput.files = e.dataTransfer.files;
        analyzeBtn.disabled = false;
        dropArea.textContent = selectedFile.name;
      }
    });

    startCameraBtn.addEventListener('click', async () => {
      try {
        stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'user' } });
        video.srcObject = stream;
        startCameraBtn.disabled = true;
        captureFrameBtn.disabled = false;
        stopCameraBtn.disabled = false;
      } catch (err) {
        resultsDiv.innerHTML = '<p class="error">No se pudo acceder a la cámara: ' + err.message + '</p>';
      }
    });

    stopCameraBtn.addEventListener('click', () => stopCamera());

    function stopCamera() {
      if (stream) {
        stream.getTracks().forEach(t => t.stop());
        stream = null;
      }
      video.srcObject = null;
      startCameraBtn.disabled = false;
      captureFrameBtn.disabled = true;
      stopCameraBtn.disabled = true;
    }

    captureFrameBtn.addEventListener('click', async () => {
      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;
      canvas.getContext('2d').drawImage(video, 0, 0);
      canvas.toBlob(blob => {
        selectedFile = new File([blob], 'frame.jpg', { type: 'image/jpeg' });
        analyzeBtn.disabled = false;
        analyzeCurrent();
      }, 'image/jpeg', 0.8);
    });

    analyzeBtn.addEventListener('click', analyzeCurrent);

    async function analyzeCurrent() {
      analyzeBtn.disabled = true;
      analyzeBtn.textContent = 'Analizando...';
      const fd = new FormData();
      fd.append('image', selectedFile);
      try {
        const resp = await fetch('/analyze', { method: 'POST', body: fd });
        const data = await resp.json();
        renderResults(data);
      } catch (err) {
        resultsDiv.innerHTML = '<p class="error">Error de conexión: ' + err.message + '</p>';
      }
      analyzeBtn.disabled = false;
      const activeMode = document.querySelector('.mode-btn.active').dataset.mode;
      analyzeBtn.textContent = activeMode === 'upload' ? 'Analizar Imagen' : 'Analizar Frame';
    }

    function renderResults(data) {
      const { faces, annotated_image, error } = data;
      resultsDiv.innerHTML = '';
      if (error) {
        resultsDiv.innerHTML = '<p class="error">' + error + '</p>';
        return;
      }
      if (annotated_image) {
        const img = document.createElement('img');
        img.src = 'data:image/jpeg;base64,' + annotated_image;
        resultsDiv.appendChild(img);
      }
      if (!faces || !Array.isArray(faces)) {
        resultsDiv.innerHTML += '<p class="error">No se detectaron rostros en la imagen.</p>';
        return;
      }
      faces.forEach((face, i) => {
        const card = document.createElement('div');
        card.className = 'face-card';
        card.innerHTML = `
          <h3>Rostro ${i+1}</h3>
          <p>Género: ${face.genero} (${face.genero_confianza}%)</p>
          <p>Etnia: ${face.raza_dominante}</p>
          <p>Edad estimada: ${face.edad_estimada} años</p>
          <p>Emoción: ${face.emocion}</p>
        `;
        resultsDiv.appendChild(card);
      });
    }
  </script>
</body>
</html>"""


@app.route("/")
def index():
    return render_template_string(HTML)


@app.route("/analyze", methods=["POST"])
def analyze():
    if "image" not in request.files:
        return jsonify({"error": "No se recibió ninguna imagen."}), 400
    file = request.files["image"]
    try:
        faces, img_b64 = analyze_from_bytes(file.read())
        return jsonify({"faces": faces, "annotated_image": img_b64})
    except Exception as e:
        return jsonify({"error": str(e)}), 400


if __name__ == "__main__":
    print("App corriendo en http://localhost:5000")
    app.run(debug=True, host="0.0.0.0", port=5000)