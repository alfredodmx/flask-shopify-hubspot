from flask import Flask, request, jsonify
import requests
import json
import os

app = Flask(__name__)

# 🔑 Obtener API Key de HubSpot y Shopify desde variables de entorno
HUBSPOT_ACCESS_TOKEN = os.getenv("HUBSPOT_ACCESS_TOKEN")
SHOPIFY_ACCESS_TOKEN = os.getenv("SHOPIFY_ACCESS_TOKEN")  # Agrega la API Key de Shopify
SHOPIFY_STORE = "uaua8v-s7.myshopify.com"  # Reemplaza con el dominio de tu tienda Shopify

if not HUBSPOT_ACCESS_TOKEN or not SHOPIFY_ACCESS_TOKEN:
    print("❌ ERROR: Las API Keys no están configuradas. Asegúrate de definir 'HUBSPOT_ACCESS_TOKEN' y 'SHOPIFY_ACCESS_TOKEN'.")
    exit(1)  # Detiene la aplicación si faltan credenciales

HUBSPOT_API_URL = "https://api.hubapi.com/crm/v3/objects/contacts"

# 📌 Función para obtener los metacampos de un cliente en Shopify
def get_customer_metafields(customer_id):
    shopify_url = f"https://{SHOPIFY_STORE}/admin/api/2023-10/customers/{customer_id}/metafields.json"
    
    headers = {
        "X-Shopify-Access-Token": SHOPIFY_ACCESS_TOKEN,
        "Content-Type": "application/json"
    }

    response = requests.get(shopify_url, headers=headers)
    
    if response.status_code == 200:
        metafields = response.json().get("metafields", [])
        modelo = next((m["value"] for m in metafields if m["key"] == "modelo"), "Sin modelo")
        precio = next((m["value"] for m in metafields if m["key"] == "precio"), "Sin precio")
        return modelo, precio
    else:
        print("❌ Error obteniendo metacampos de Shopify:", response.text)
        return "Error", "Error"

# 📩 Ruta del webhook que Shopify enviará a esta API
@app.route('/webhook/shopify', methods=['POST'])
def receive_webhook():
    data = request.get_json()  # Lee el JSON enviado por Shopify
    print("📩 Webhook recibido de Shopify:", json.dumps(data, indent=4))

    # Extraer información básica del cliente
    customer_id = data.get("id")  # Necesario para buscar metacampos
    email = data.get("email")
    first_name = data.get("first_name", "")
    last_name = data.get("last_name", "")
    phone = data.get("phone", "")

    if not email or not customer_id:
        print("❌ ERROR: No se recibió un email o ID de cliente válido.")
        return jsonify({"error": "Falta email o ID de cliente"}), 400

    # 🔍 Obtener los metacampos desde Shopify
    modelo, precio = get_customer_metafields(customer_id)

    # 📌 Crear el contacto con los metacampos incluidos
    contact_data = {
        "properties": {
            "email": email,
            "firstname": first_name,
            "lastname": last_name,
            "phone": phone,
            "custom_modelo": modelo,
            "custom_precio": precio
        }
    }

    headers = {
        "Authorization": f"Bearer {HUBSPOT_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

    # 🚀 Enviar los datos a HubSpot
    response = requests.post(HUBSPOT_API_URL, json=contact_data, headers=headers)
    print("🔍 Respuesta de HubSpot:", response.text)

    if response.status_code == 201:
        return jsonify({"message": "Contacto creado en HubSpot con metacampos"}), 200
    else:
        return jsonify({"error": "No se pudo crear el contacto en HubSpot", "details": response.text}), 400

# 🔥 Iniciar el servidor en Render
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
