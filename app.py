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
  <title>DeepFace — Análisis Facial</title>
</head>
<body>
  <header>
    <h1>DeepFace — Análisis Facial</h1>
    <p>Género · Etnia estimada</p>
  </header>
  <div class="container">
    <!-- Zona de carga de imagen -->
    <input type="file" id="file-input" accept="image/*">
    <button id="analyze-btn" disabled>Analizar</button>
    <!-- Resultados -->
    <div id="results"></div>
  </div>
  <script>
    const fileInput  = document.getElementById('file-input');
    const analyzeBtn = document.getElementById('analyze-btn');
    const resultsDiv = document.getElementById('results');
    let selectedFile = null;

    fileInput.addEventListener('change', e => {
      selectedFile = e.target.files[0];
      if (selectedFile) analyzeBtn.disabled = false;
    });

    analyzeBtn.addEventListener('click', async () => {
      const fd = new FormData();
      fd.append('image', selectedFile);
      const resp = await fetch('/analyze', { method: 'POST', body: fd });
      const data = await resp.json();
      renderResults(data);
    });

    function renderResults(data) {
      const { faces, annotated_image } = data;
      resultsDiv.innerHTML = '';
      if (annotated_image) {
        const img = document.createElement('img');
        img.src = 'data:image/jpeg;base64,' + annotated_image;
        resultsDiv.appendChild(img);
      }
      faces.forEach((face, i) => {
        resultsDiv.innerHTML += `
          <h3>Rostro ${i+1}</h3>
          <p>Género: ${face.genero} (${face.genero_confianza}%)</p>
          <p>Etnia:  ${face.raza_dominante}</p>
          <!-- TAREA: agrega edad y emoción aquí -->
        `;
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