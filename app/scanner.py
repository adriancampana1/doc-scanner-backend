import re
import os

from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive

from google.cloud import vision

def process_image(file_path):
    client = vision.ImageAnnotatorClient()

    with open(file_path, 'rb') as image_file:
        content = image_file.read()

    image = vision.Image(content=content)
    response = client.text_detection(image=image)
    texts = response.text_annotations

    if response.error.message:
        raise Exception(f'{response.error.message}\nPara mais detalhes: {response.error.details}')
    
    if texts:
        return texts[0].description
    else:
        return  ''

def preprocessing_text(text):
    text = re.sub(r'(?<=\w)-\n', '', text)
    return text

def extract_name(text):
    text = preprocessing_text(text)
    
    pattern = r"Nome do Candidato:?\s*([^\n]+)"

    # Busca por todas as ocorrências que possam corresponder ao padrão
    results = re.findall(pattern, text, re.MULTILINE)

    if results:
        # Assume que o nome do candidato é o texto imediatamente após o padrão,
        # que pode estar na linha seguinte.
        name = results[0].strip().replace('\n', ' ')
        return name
    else:
        return "Nome do candidato não encontrado"

    
def get_specific_folder_id(drive, parent_folder_name, target_folder_name, initial=None):
    # Busca a pasta pai
    parent_folder_list = drive.ListFile({'q': f"title='{parent_folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"}).GetList()
    if parent_folder_list:
        parent_folder_id = parent_folder_list[0]['id']
    else:
        # Cria a pasta pai se não existir
        parent_folder = drive.CreateFile({'title': parent_folder_name, 'mimeType': 'application/vnd.google-apps.folder'})
        parent_folder.Upload()
        parent_folder_id = parent_folder['id']
        print(f"Pasta '{parent_folder_name}' criada com sucesso.")

    # Busca a pasta alvo dentro da pasta pai
    target_folder_list = drive.ListFile({'q': f"'{parent_folder_id}' in parents and title='{target_folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"}).GetList()
    if target_folder_list:
        target_folder_id = target_folder_list[0]['id']
    else:
        # Cria a pasta alvo se não existir
        target_folder = drive.CreateFile({'title': target_folder_name, 'mimeType': 'application/vnd.google-apps.folder', 'parents': [{'id': parent_folder_id}]})
        target_folder.Upload()
        target_folder_id = target_folder['id']
        print(f"Pasta '{target_folder_name}' criada dentro de '{parent_folder_name}'.")

    # Se uma inicial for passada, ele busca ou cria uma pasta com a inicial dentro da pasta target
    if initial:
        final_folder_list = drive.ListFile({'q': f"'{target_folder_id}' in parents and title='{initial}' and mimeType='application/vnd.google-apps.folder' and trashed=false"}).GetList()
        if final_folder_list:
            final_folder_id = final_folder_list[0]['id']
        else:
            # Cria a pasta com a inicial se não existir
            final_folder = drive.CreateFile({'title': initial, 'mimeType': 'application/vnd.google-apps.folder', 'parents': [{'id': target_folder_id}]})
            final_folder.Upload()
            final_folder_id = final_folder['id']
            print(f"Pasta '{initial}' criada dentro de '{target_folder_name}'.")
        return final_folder_id
    else:
        return target_folder_id

def save_document_to_drive(name_candidate, document_path):
    gauth = GoogleAuth()
    gauth.LoadCredentialsFile('mycreds.json')
    
    if (gauth.credentials is None):
        gauth.LocalWebserverAuth()
    elif gauth.access_token_expired:
        gauth.Refresh()
    else:
        gauth.Authorize()
    
    gauth.SaveCredentialsFile("mycreds.json")
    drive = GoogleDrive(gauth)
    
    initial = name_candidate[0].upper()
    folder_id = get_specific_folder_id(drive, "ARQUIVOS MUSICAIS CASONI", "FICHAS DE OFICIALIZAÇÃO", initial)
    name_candidate = name_candidate.replace(" ", "")

    file_name, file_extension = os.path.splitext(document_path)
    new_filename = f"{name_candidate}{file_extension}"

    file_drive = drive.CreateFile({'title': new_filename, 'parents': [{'id': folder_id}]})
    file_drive.SetContentFile(document_path)
    file_drive.Upload()

    return file_drive['alternateLink']