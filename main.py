from config import SUPABASE_URL, SUPABASE_API_KEY
from flask import Flask, request, jsonify
from supabase import create_client, Client
from PIL import Image
import face_recognition
import io
import os

app = Flask(__name__)

supabase: Client = create_client(SUPABASE_URL, SUPABASE_API_KEY)

@app.route('/compare', methods=['POST'])
def compare_images():
    file = request.files.get('file')
    if not file:
        return jsonify({"error": "No file uploaded"}), 400

    try:
        uploaded_image = face_recognition.load_image_file(file)
        uploaded_encodings = face_recognition.face_encodings(uploaded_image)
        if not uploaded_encodings:
            return jsonify({"error": "No face found in uploaded image"}), 400
        uploaded_encoding = uploaded_encodings[0]
    except Exception as e:
        return jsonify({"error": f"Failed to process uploaded image: {str(e)}"}), 400

    storage_path = 'avatar/'
    try:
        response = supabase.storage.from_('avatar').list()
        if isinstance(response, dict) and 'error' in response:
            raise Exception(f"Error retrieving files: {response['error']}")
    except Exception as e:
        return jsonify({"error": f"Failed to list images from storage: {str(e)}"}), 500

    if not response or len(response) == 0:
        return jsonify({"error": "No images found in storage"}), 404

    for item in response:
        image_name = item['name']

        try:
            image_data = supabase.storage.from_('avatar').download(image_name)
            known_image = face_recognition.load_image_file(io.BytesIO(image_data))
            known_encodings = face_recognition.face_encodings(known_image)

            if not known_encodings:
                continue 
            
            for known_encoding in known_encodings:
                match = face_recognition.compare_faces([known_encoding], uploaded_encoding,  tolerance=0.5)
                if any(match):
                    return jsonify({"match": image_name, "message": "Face matched!"}), 200
        except Exception as e:
            continue

    return jsonify({"message": "No matches found"}), 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host="0.0.0.0", port=port)