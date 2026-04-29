import os
from flask import Flask, request, jsonify
import google.generativeai as genai
import json
import base64
import re

# ✅ Use ENV variable ONLY (never hardcode API keys)
API_KEY = os.getenv("GOOGLE_API_KEY")

if not API_KEY:
    raise ValueError("❌ GOOGLE_API_KEY not set")

genai.configure(api_key=API_KEY)

# ✅ Stable model name
model = genai.GenerativeModel("gemini-2.5-flash-lite")

app = Flask(__name__)


@app.route("/", methods=["GET"])
def home():
    return "🌱 Ecosort AI Waste Classifier is Running!"


@app.route("/classify", methods=["POST"])
def classify():
    try:
        data = request.get_json()

        if not data or "image" not in data:
            return jsonify({"error": "No image provided"}), 400

        # ✅ Safe base64 decode
        try:
            image_bytes = base64.b64decode(data["image"])
        except Exception:
            return jsonify({"error": "Invalid base64 image"}), 400

        prompt = """
You are a waste classification AI.

Classify the image into ONE of:
- biodegradable
- non-biodegradable
- hazardous

Rules:
- Humans → "stop"
- Phones/electronics → "hazardous"
- If unclear or multiple objects → "Fail"

Return ONLY valid JSON:
{
  "class": "biodegradable",
  "confidence": 0.95
}
"""

        # ✅ Correct Gemini image format
        response = model.generate_content([
            {
                "inline_data": {
                    "mime_type": "image/jpeg",
                    "data": base64.b64encode(image_bytes).decode("utf-8")
                }
            },
            {"text": prompt}
        ])

        raw_text = response.text.strip() if response.text else ""

        if not raw_text:
            return jsonify({
                "class": None,
                "confidence": None,
                "error": "No output from model"
            })

        # ✅ Clean Gemini output (handles ```json etc.)
        cleaned = raw_text.replace("```json", "").replace("```", "").strip()

        # ✅ Extract JSON safely
        match = re.search(r"\{[\s\S]*\}", cleaned)
        if not match:
            return jsonify({
                "class": "Fail",
                "confidence": 0,
                "raw": cleaned
            })

        result = json.loads(match.group())

        return jsonify(result)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)