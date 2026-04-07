from flask import Flask, jsonify, request
import joblib
from datetime import datetime
import pandas as pd
import os

app = Flask(__name__, static_folder="static", static_url_path="/static")

# =========================
# BASE DIRECTORY
# =========================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))


# =========================
# LAZY LOAD FUNCTION (KEY FIX)
# =========================
def load_models():
    model = joblib.load(os.path.join(BASE_DIR, "../model/rf_price_model1.pkl"))
    feature_schema = joblib.load(os.path.join(BASE_DIR, "../model/feature_schema.pkl"))
    label_encoders = joblib.load(os.path.join(BASE_DIR, "../model/label_encoders.pkl"))
    alpha = joblib.load(os.path.join(BASE_DIR, "../model/alpha.pkl"))
    beta = joblib.load(os.path.join(BASE_DIR, "../model/beta.pkl"))

    return model, feature_schema, label_encoders, alpha, beta


# =========================
# ROUTES
# =========================

@app.route("/")
def home():
    return "Backend running ✅"


@app.route("/ui")
def ui():
    return app.send_static_file("index.html")


@app.route("/states")
def states():
    _, _, label_encoders, _, _ = load_models()
    return jsonify(label_encoders["STATE"].classes_.tolist())


@app.route("/districts")
def districts():
    _, _, label_encoders, _, _ = load_models()
    return jsonify(label_encoders["District Name"].classes_.tolist())


@app.route("/markets")
def markets():
    _, _, label_encoders, _, _ = load_models()
    return jsonify(label_encoders["Market Name"].classes_.tolist())


@app.route("/commodities")
def commodities():
    _, _, label_encoders, _, _ = load_models()
    return jsonify(label_encoders["Commodity"].classes_.tolist())


# =========================
# PREDICTION API
# =========================
@app.route("/predict", methods=["POST"])
def predict():
    try:
        # Load models only when needed
        model, feature_schema, label_encoders, alpha, beta = load_models()

        data = request.json

        # Date processing
        d = datetime.strptime(data["Price Date"], "%Y-%m-%d")
        data["day"], data["month"], data["year"] = d.day, d.month, d.year
        del data["Price Date"]

        # Encoding
        for col, enc in label_encoders.items():
            data[col] = int(enc.transform([data[col]])[0])

        # DataFrame creation
        X = pd.DataFrame([data])[feature_schema]

        # Prediction
        modal = float(model.predict(X)[0])

        return jsonify({
            "Predicted_Modal_Price": round(modal, 2),
            "Estimated_Min_Price": round(modal * alpha, 2),
            "Estimated_Max_Price": round(modal * beta, 2)
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# =========================
# RUN SERVER (RENDER FIX)
# =========================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)