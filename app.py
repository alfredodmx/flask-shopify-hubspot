@app.route('/webhook/shopify', methods=['POST'])
def receive_webhook():
    try:
        # 🔍 Capturar datos RAW del webhook para ver qué envía Shopify
        raw_data = request.data.decode('utf-8')
        print("📩 Webhook recibido (RAW):", raw_data)

        # Intentar parsear JSON
        data = request.get_json(silent=True)

        if not data:
            print("❌ ERROR: No se pudo interpretar el JSON correctamente.")
            return jsonify({"error": "Webhook sin JSON válido"}), 400

        print("📩 Webhook recibido de Shopify (JSON):", json.dumps(data, indent=4))

        return jsonify({"message": "Webhook recibido correctamente"}), 200

    except Exception as e:
        print("❌ ERROR procesando el webhook:", str(e))
        return jsonify({"error": "Error interno"}), 500
