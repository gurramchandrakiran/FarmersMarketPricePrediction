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
        # Load models
        model, feature_schema, alpha, beta = load_model_bundle()
        label_encoders = load_encoders()

        data = request.json
        print("Received JSON:", data)

        # =========================
        # DATE HANDLING (ROBUST)
        # =========================
        date_str = data.get("Price Date")

        if not date_str:
            return jsonify({"error": "Price Date is required"}), 400

        parsed = None
        for fmt in ("%Y-%m-%d", "%d-%m-%Y"):
            try:
                parsed = datetime.strptime(date_str, fmt)
                break
            except:
                continue

        if parsed is None:
            return jsonify({"error": "Invalid date format. Use YYYY-MM-DD or DD-MM-YYYY"}), 400

        data["day"], data["month"], data["year"] = parsed.day, parsed.month, parsed.year
        del data["Price Date"]

        # =========================
        # SAFE ENCODING
        # =========================
        for col, enc in label_encoders.items():
            value = str(data.get(col, "")).strip()

            if value in enc.classes_:
                data[col] = int(enc.transform([value])[0])
            else:
                return jsonify({
                    "error": f"Invalid value '{value}' for column '{col}'"
                }), 400

        print("Encoded data:", data)

        # =========================
        # FEATURE ALIGNMENT
        # =========================
        X = pd.DataFrame([data])

        # Ensure correct column order
        X = X.reindex(columns=feature_schema, fill_value=0)

        # =========================
        # PREDICTION
        # =========================
        modal = float(model.predict(X)[0])

        result = {
            "Predicted_Modal_Price": round(modal, 2),
            "Estimated_Min_Price": round(modal * alpha, 2),
            "Estimated_Max_Price": round(modal * beta, 2)
        }

        print("Prediction result:", result)

        return jsonify(result)

    except Exception as e:
        print("ERROR in /predict:", str(e))
        return jsonify({"error": str(e)}), 500


# =========================
# RUN SERVER (RENDER FIX)
# =========================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)