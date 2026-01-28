import os, yt_dlp, cv2, base64, tempfile, uuid, stat
from flask import Flask, request, jsonify

app = Flask(__name__)

# Definimos la ruta al binario de FFmpeg que está en tu carpeta /bin
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FFMPEG_PATH = os.path.join(BASE_DIR, 'bin', 'ffmpeg')

def obtener_frame(url):
    # Paso 1: Dar permisos de ejecución al binario FFmpeg (Vital en Render)
    if os.path.exists(FFMPEG_PATH):
        st = os.stat(FFMPEG_PATH)
        os.chmod(FFMPEG_PATH, st.st_mode | stat.S_IEXEC)
    
    with tempfile.TemporaryDirectory() as tmp_dir:
        output_path = os.path.join(tmp_dir, f"{uuid.uuid4()}.mp4")
        
        # Paso 2: Configuración de yt-dlp
        ydl_opts = {
            'format': 'best',
            'outtmpl': output_path,
            'quiet': True,
            'ffmpeg_location': FFMPEG_PATH,
            'external_downloader': 'ffmpeg',
            'external_downloader_args': ['-t', '5'], # Solo descarga 5 seg para no saturar RAM
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36',
            'nocheckcertificate': True
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            
            # Paso 3: Extraer el frame con OpenCV
            cap = cv2.VideoCapture(output_path)
            success, frame = cap.read()
            cap.release()
            return frame if success else None
        except Exception as e:
            print(f"Error en procesamiento: {e}")
            return None

@app.route('/capturar', methods=['POST'])
def handle_request():
    data = request.json
    video_url = data.get('url_video')
    
    if not video_url:
        return jsonify({"status": "error", "message": "URL no proporcionada"}), 400

    resultado_frame = obtener_frame(video_url)
    
    if resultado_frame is None:
        return jsonify({"status": "failed", "message": "No se pudo extraer el video"}), 200

    # Paso 4: Codificar a Base64
    _, buffer = cv2.imencode('.jpg', resultado_frame)
    img_str = base64.b64encode(buffer).decode('utf-8')
    
    return jsonify({
        "status": "success",
        "imagen_base64": img_str
    })

if __name__ == '__main__':
    # Render asigna un puerto dinámico mediante la variable de entorno PORT
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
