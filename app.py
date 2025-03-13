from flask import Flask, request, jsonify
import requests
import json
import os

app = Flask(__name__)

# 🔑 Token de Acceso de HubSpot (REEMPLÁZALO con tu token real)
HUBSPOT_ACCESS_TOKEN = "tu_token_hubspot"
HUBSPOT_API_URL = "https://api.hubapi.com/crm/v3/objects/contacts"

# 📩 Ruta del webhook que Shopify enviará a esta API
@app.route('/webhook/shopify', methods=['POST'])
def receive_webhook():
    data = request.get_json()  # Lee el JSON enviado por Shopify
    print("📩 Datos recibidos de Shopify:", json.dumps(data, indent=4))

    # Extraer información importante
    email = data.get("email")
    first_name = data.get("first_name", "")
    last_name = data.get("last_name", "")
    phone = data.get("phone", "")

    if not email:
        return jsonify({"error": "No se recibió un email válido"}), 400

    # 📌 Crear un contacto en HubSpot
    contact_data = {
        "properties": {
            "email": email,
            "firstname": first_name,
            "lastname": last_name,
            "phone": phone
        }
    }

    headers = {
        "Authorization": f"Bearer {HUBSPOT_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

    response = requests.post(HUBSPOT_API_URL, json=contact_data, headers=headers)
    print("🔍 Respuesta de HubSpot:", response.text)

    if response.status_code == 201:
        return jsonify({"message": "Contacto creado en HubSpot"}), 200
    else:
        return jsonify({"error": "No se pudo crear el contacto en HubSpot", "details": response.text}), 400

# 🔥 Iniciar el servidor en Railway
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
