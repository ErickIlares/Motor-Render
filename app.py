import os, yt_dlp, cv2, base64, tempfile, uuid
from flask import Flask, request, jsonify

app = Flask(__name__)

def obtener_frame(url):
    with tempfile.TemporaryDirectory() as tmp_dir:
        # Creamos un nombre de archivo temporal
        output_path = os.path.join(tmp_dir, f"{uuid.uuid4()}.mp4")
        
        ydl_opts = {
            'format': 'best',
            'outtmpl': output_path,
            'quiet': True,
            'no_warnings': True,
            # Forzamos el uso de ffmpeg del sistema (Render lo tiene en el PATH)
            'external_downloader': 'ffmpeg',
            'external_downloader_args': ['-t', '3'], # Bajamos solo 3 segundos para ir rápido
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36',
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            
            # Procesamos con OpenCV
            cap = cv2.VideoCapture(output_path)
            success, frame = cap.read()
            cap.release()
            
            if success:
                # Redimensionamos un poco para que el Base64 no sea gigante
                frame = cv2.resize(frame, (640, 360)) 
                return frame
            return None
        except Exception as e:
            print(f"Error detectado: {e}")
            return None

@app.route('/capturar', methods=['POST'])
def handle_request():
    data = request.json
    video_url = data.get('url_video')
    
    if not video_url:
        return jsonify({"status": "error", "message": "Falta URL"}), 400

    resultado_frame = obtener_frame(video_url)
    
    if resultado_frame is None:
        return jsonify({"status": "failed"}), 200

    _, buffer = cv2.imencode('.jpg', resultado_frame)
    img_str = base64.b64encode(buffer).decode('utf-8')
    
    return jsonify({
        "status": "success",
        "imagen_base64": img_str
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)