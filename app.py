import os
import hmac
import hashlib
import json
import requests
import qrcode
import tempfile
import base64  
import cloudinary
from dotenv import load_dotenv
from cloudinary.utils import cloudinary_url

# Set cloudinary credentials
load_dotenv()
cloudinary.config( 
 cloud_name = os.environ.get('CLOUDINARY_NAME'),
  api_key =  os.environ.get('CLOUDINARY_API_KEY'),
  api_secret = os.environ.get('CLOUDINARY_API_SECRET'),
  secure = True
)

import cloudinary.uploader
import cloudinary.api

from io import BytesIO
from flask import Flask, jsonify, request, make_response, Response

app = Flask(__name__)


@app.route("/")
def hello():
    return jsonify(message='Hello from path!')


SLACK_WEBHOOK_URL= os.environ.get('SLACK_WEBHOOK_URL')

@app.route('/webhook', methods=['POST'])
# Handle incoming webhook requests from Expo
def webhook():
    try:
        body = request.data.decode('utf-8')
        expo_signature = request.headers.get('expo-signature')
        secret_key = os.environ.get('EXPO_WEBHOOK_SECRET_KEY')


        if not expo_signature:
            return Response("Missing 'expo-signature' header", status=400)

        if secret_key is None:
            return Response('Secret key not configured', status=500)

        hmac_obj = hmac.new(secret_key.encode('utf-8'), request.data, hashlib.sha1)
        calculated_hash = 'sha1=' + hmac_obj.hexdigest()

        if expo_signature != calculated_hash:
            return Response(f"Signatures didn't match! calculated_hash: {calculated_hash}, expo_signature: {expo_signature}", status=500)


        # Gets the data from the request body
        data = json.loads(body)
        id = data.get('id')
        accountName = data.get('accountName')
        status = data.get('status')
        artifacts = data.get('artifacts')
        metadata = data.get('metadata')
        platform = data.get('platform')
        error = data.get('error')
        app_name = metadata.get('appName') if metadata else None
        appVersion = metadata.get('appVersion') if metadata else None
        buildArtifact = artifacts.get('buildUrl')
        buildProfile = metadata.get('buildProfile') if metadata else None
        channel = metadata.get('channel') if metadata else None
        username = metadata.get('username') if metadata else None
        buildMode = metadata.get('buildMode') if metadata else None


        build_url = f'https://expo.io/accounts/{accountName if metadata and metadata.get("trackingContext") else os.environ.get("EXPO_DEFAULT_TEAM_NAME")}/projects/{metadata["appName"] if metadata else "unknown"}/builds/{id}'
        type_build_message = 'Nova Build' if buildMode == 'build' else 'Nova Submissão de App'
        
        qr_code_temp_image = generate_qr_code_temp_image(buildArtifact)
       
        # Upload the file to Cloudinary and get the URL
        uploaded_image_url = upload(qr_code_temp_image)

        if status == 'finished':
            # Send a message to Slack
            message = f':sunny: {type_build_message} concluída com sucesso!\nApp: {app_name}\n Versão: {appVersion}\nPlataforma: {platform}\nUsuário: {username}\n Perfil: {buildProfile} - Channel: {channel}\n<{build_url}|Ver mais detalhes> '
            send_slack_message(message, uploaded_image_url)
        elif status == 'errored':
            # Send an error message to Slack
            error_code = error.get('errorCode') if error else None
            error_message = error.get('message') if error else None
            error_message = f'*Error Code*\n{error_code}\n*Mensagem*\n{error_message}\n*Detalhes*\n{build_url}'
            send_slack_message(error_message)

        # Delete the temporary file
        os.remove(qr_code_temp_image)

        return 'OK', 200

    except Exception as e:
        return str(e), 500

def send_slack_message(message, qr_code_image_bytes = None):
    # Prepare the payload with the message and QR code file
    if qr_code_image_bytes is None:
        payload = {
            "text": message
        }
    else:
        payload = {
            "blocks": [
              
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": message
                    }
                },
                  {
                    "title": {
                        "type": "plain_text",
                        "text": "QR Code"
                    },

                    "type": 'image',
                    "image_url": qr_code_image_bytes,
                    "alt_text": 'QR Code'
                },
            ]
        }

    # Send the payload to Slack
    try:
        response = requests.post(SLACK_WEBHOOK_URL, json=payload)
        if response.status_code != 200:
            print(f'Failed to send message to Slack: {response.text}')
            return (f'Failed to send message to Slack: {response.text}')
    except Exception as e:
        return (f'Failed to send message to Slack: {e}')

def upload(file):
    # Upload file to Cloudinary
    response = cloudinary.uploader.upload(file)
    url, options = cloudinary_url(
        response['public_id'],
        format=response['format'],
        width=250,
        height=250,
        crop="fill"
    )
    return url

def generate_qr_code_temp_image(build_url):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )

    # Add the URL data to the QR code
    qr.add_data(build_url)
    qr.make(fit=True)

    # Create an image from the QR code
    img = qr.make_image(fill_color="black", back_color="white")

    # Convert the image to bytes
    img_bytes_io = BytesIO()
    img.save(img_bytes_io, format="PNG")
    img_bytes = img_bytes_io.getvalue()

    # Encode the image as a Base64 string
    img_base64 = base64.b64encode(img_bytes).decode()

    # Construct a data URL
    data_url = f"{img_base64}"

    base64_string = data_url
    # Decode the Base64 string
    image_data = base64.b64decode(base64_string)
    # Create a temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".png", dir='./') as temp_file:
        temp_file.write(image_data)
    # Get the temporary file path
    temp_file_path = temp_file.name


    return temp_file_path

@app.errorhandler(404)
def resource_not_found(e):
    return make_response(jsonify(error='Not found!'), 404)
