from app import app
from flask import request, jsonify
from .scanner import process_image, extract_name, save_document_to_drive
from werkzeug.utils import secure_filename
import os

@app.route('/upload', methods=['POST'])
def upload_file():
    if ('file' not in request.files):
        return 'Nenhum arquivo enviado'
    
    file = request.files['file']
    if file.filename == "":
        return 'Nenhum arquivo selecionado'
    
    if file:
        filename = secure_filename(file.filename)

        save_path = os.path.join('TMPFiles', filename)
        file.save(save_path)
        extracted_text = process_image(save_path)
        candidate_name = extract_name(extracted_text)

        return jsonify({'candidateName': candidate_name, 'filePath': save_path})

    return 'Arquivo recebido e processado com sucesso!'


@app.route('/save_document', methods=['POST'])
def save_document_route():
    data = request.json
    name_candidate = data['name']
    document_path = data['filePath']
    new_path = save_document_to_drive(name_candidate, document_path)
    
    try:
        os.remove(document_path)
    except OSError as err:
        print(f"Erro ao excluir o arquivo {document_path}: {err.strerror}")
    
    return jsonify({'message': 'Documento salvo com sucesso!', 'newPath': new_path})

@app.route('/')
def home():
    return 'Inicio'