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
# LOAD ONLY ENCODERS (LIGHTWEIGHT)
# =========================
def load_encoders():
    return joblib.load(os.path.join(BASE_DIR, "../model/label_encoders.pkl"))


# =========================
# LOAD FULL MODEL (HEAVY)
# =========================
def load_model_bundle():
    model = joblib.load(os.path.join(BASE_DIR, "../model/rf_price_model1.pkl"))
    feature_schema = joblib.load(os.path.join(BASE_DIR, "../model/feature_schema.pkl"))
    alpha = joblib.load(os.path.join(BASE_DIR, "../model/alpha.pkl"))
    beta = joblib.load(os.path.join(BASE_DIR, "../model/beta.pkl"))
    return model, feature_schema, alpha, beta


# =========================
# ROUTES
# =========================

@app.route("/")
def home():
    return "Backend running ✅"


@app.route("/ui")
def ui():
    return app.send_static_file("index.html")


# =========================
# DROPDOWN APIs (FAST)
# =========================

@app.route("/states")
def states():
    try:
        label_encoders = load_encoders()
        return jsonify(label_encoders["STATE"].classes_.tolist())
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/districts")
def districts():
    try:
        label_encoders = load_encoders()
        return jsonify(label_encoders["District Name"].classes_.tolist())
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/markets")
def markets():
    try:
        label_encoders = load_encoders()
        return jsonify(label_encoders["Market Name"].classes_.tolist())
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/commodities")
def commodities():
    try:
        label_encoders = load_encoders()
        return jsonify(label_encoders["Commodity"].classes_.tolist())
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# =========================
# PREDICTION API
# =========================
@app.route("/predict", methods=["POST"])
def predict():
    try:
        # Load heavy models only when needed
        model, feature_schema, alpha, beta = load_model_bundle()
        label_encoders = load_encoders()

        data = request.json

        # Date processing
        d = datetime.strptime(data["Price Date"], "%Y-%m-%d")
        data["day"], data["month"], data["year"] = d.day, d.month, d.year
        del data["Price Date"]

        # Encode categorical values
        for col, enc in label_encoders.items():
            data[col] = int(enc.transform([data[col]])[0])

        # Prepare input
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