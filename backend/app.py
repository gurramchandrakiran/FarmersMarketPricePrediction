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
# LOAD MODELS
# =========================
def load_encoders():
    return joblib.load(os.path.join(BASE_DIR, "../model/label_encoders.pkl"))

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
# DROPDOWN APIs
# =========================

@app.route("/states")
def states():
    label_encoders = load_encoders()
    return jsonify(label_encoders["STATE"].classes_.tolist())


@app.route("/districts")
def districts():
    label_encoders = load_encoders()
    return jsonify(label_encoders["District Name"].classes_.tolist())


@app.route("/markets")
def markets():
    label_encoders = load_encoders()
    return jsonify(label_encoders["Market Name"].classes_.tolist())


@app.route("/commodities")
def commodities():
    label_encoders = load_encoders()
    return jsonify(label_encoders["Commodity"].classes_.tolist())


# =========================
# PREDICT API (FINAL STABLE)
# =========================
@app.route("/predict", methods=["POST"])
def predict():
    try:
        model, feature_schema, alpha, beta = load_model_bundle()
        label_encoders = load_encoders()

        data = request.json
        print("Incoming:", data)

        # =========================
        # DATE
        # =========================
        d = datetime.strptime(data["Price Date"], "%Y-%m-%d")
        data["day"], data["month"], data["year"] = d.day, d.month, d.year
        del data["Price Date"]

        # =========================
        # ADD DEFAULTS (IMPORTANT)
        # =========================
        data["Variety"] = "Other"
        data["Grade"] = "FAQ"

        # =========================
        # ENCODING
        # =========================
        for col, enc in label_encoders.items():
            value = str(data.get(col, "")).strip()

            if value not in enc.classes_:
                return jsonify({"error": f"{value} not valid for {col}"})

            data[col] = int(enc.transform([value])[0])

        # =========================
        # DATAFRAME ALIGNMENT
        # =========================
        X = pd.DataFrame([data])

        # Fill missing columns
        for col in feature_schema:
            if col not in X.columns:
                X[col] = 0

        # Correct order
        X = X[feature_schema]

        # =========================
        # PREDICT
        # =========================
        modal = float(model.predict(X)[0])

        result = {
            "Predicted_Modal_Price": round(modal, 2),
            "Estimated_Min_Price": round(modal * alpha, 2),
            "Estimated_Max_Price": round(modal * beta, 2)
        }

        print("Result:", result)

        return jsonify(result)

    except Exception as e:
        print("ERROR:", e)
        return jsonify({"error": str(e)})


# =========================
# RUN SERVER
# =========================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)