from flask import Flask, request, jsonify
import requests
import json
import os

app = Flask(__name__)

# 🔑 Obtener API Key de HubSpot y Shopify desde variables de entorno
HUBSPOT_ACCESS_TOKEN = os.getenv("HUBSPOT_ACCESS_TOKEN")
SHOPIFY_ACCESS_TOKEN = os.getenv("SHOPIFY_ACCESS_TOKEN")  # Agregamos la API Key de Shopify
SHOPIFY_STORE = "uaua8v-s7.myshopify.com"  # Reemplaza con tu dominio real de Shopify

if not HUBSPOT_ACCESS_TOKEN or not SHOPIFY_ACCESS_TOKEN:
    print("❌ ERROR: Las API Keys no están configuradas. Asegúrate de definir 'HUBSPOT_ACCESS_TOKEN' y 'SHOPIFY_ACCESS_TOKEN'.")
    exit(1)

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
        describe = next((m["value"] for m in metafields if m["key"] == "describe"), "Sin descripcion")  # Corregido
        plano = next((m["value"] for m in metafields if m["key"] == "plano"), "Sin plano")  # Corregido
        direccion = next((m["value"] for m in metafields if m["key"] == "direccion"), "Sin direccion")  # Corregido
        presupuesto = next((m["value"] for m in metafields if m["key"] == "presupuesto"), "Sin presupuesto")  # Corregido
        persona = next((m["value"] for m in metafields if m["key"] == "persona"), "Sin persona")  # Corregido
        
        return modelo, precio, describe, plano, direccion, presupuesto, persona
    else:
        print("❌ Error obteniendo metacampos de Shopify:", response.text)
        return "Error", "Error", "Error", "Error", "Error", "Error", "Error"

# 📩 Ruta del webhook que Shopify enviará a esta API
@app.route('/webhook/shopify', methods=['POST'])
def receive_webhook():
    try:
        raw_data = request.data.decode('utf-8')  # Capturar datos crudos del webhook
        print("📩 Webhook recibido (RAW):", raw_data)

        # Intentar parsear JSON
        data = request.get_json(silent=True)

        if not data:
            print("❌ ERROR: No se pudo interpretar el JSON correctamente.")
            return jsonify({"error": "Webhook sin JSON válido"}), 400

        print("📩 Webhook recibido de Shopify (JSON):", json.dumps(data, indent=4))

        # Extraer información básica
        customer_id = data.get("id")  # Obtener el ID del cliente para buscar metacampos
        email = data.get("email")
        first_name = data.get("first_name", "")
        last_name = data.get("last_name", "")
        phone = data.get("phone", "")

        if not email or not customer_id:
            print("❌ ERROR: No se recibió un email o ID de cliente válido.")
            return jsonify({"error": "Falta email o ID de cliente"}), 400

        # 🔍 Obtener los metacampos desde Shopify
        modelo, precio, describe, plano, direccion, presupuesto, persona = get_customer_metafields(customer_id)

        # 📌 Crear el contacto con los metacampos incluidos
        contact_data = {
            "properties": {
                "email": email,
                "firstname": first_name,
                "lastname": last_name,
                "phone": phone,
                "custom_modelo": modelo,
                "custom_precio": precio,
                "custom_descripcion": describe,
                "custom_plano": plano,
                "custom_direccion": direccion,
                "custom_presupuesto": presupuesto,
                "custom_persona": persona
            }
        }

        headers = {
            "Authorization": f"Bearer {HUBSPOT_ACCESS_TOKEN}",
            "Content-Type": "application/json"
        }

        # 🚀 Imprimir qué datos se están enviando a HubSpot
        print("📤 Enviando datos a HubSpot:", json.dumps(contact_data, indent=4))

        # 🚀 Enviar los datos a HubSpot
        response = requests.post(HUBSPOT_API_URL, json=contact_data, headers=headers)

        # 🔍 Imprimir la respuesta de HubSpot
        print("🔍 Respuesta de HubSpot:", response.status_code, response.text)

        if response.status_code == 201:
            return jsonify({"message": "Contacto creado en HubSpot con metacampos"}), 200
        else:
            return jsonify({"error": "No se pudo crear el contacto en HubSpot", "details": response.text}), 400

    except Exception as e:
        print("❌ ERROR procesando el webhook:", str(e))
        return jsonify({"error": "Error interno"}), 500

# 🔥 Iniciar el servidor en Render
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
