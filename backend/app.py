from flask import Flask, jsonify, request, send_from_directory
import joblib
from datetime import datetime
import pandas as pd

app = Flask(__name__, static_folder="static",static_url_path="/static")

model = joblib.load("../model/rf_price_model1.pkl")
feature_schema = joblib.load("../model/feature_schema.pkl")
label_encoders = joblib.load("../model/label_encoders.pkl")
alpha = joblib.load("../model/alpha.pkl")
beta = joblib.load("../model/beta.pkl")

@app.route("/")
def home():
    return "Backend running"

@app.route("/ui")
def ui():
    return app.send_static_file("index.html")

@app.route("/states")
def states():
    return jsonify(label_encoders["STATE"].classes_.tolist())

@app.route("/districts")
def districts():
    return jsonify(label_encoders["District Name"].classes_.tolist())

@app.route("/markets")
def markets():
    return jsonify(label_encoders["Market Name"].classes_.tolist())

@app.route("/commodities")
def commodities():
    return jsonify(label_encoders["Commodity"].classes_.tolist())

@app.route("/predict", methods=["POST"])
def predict():
    data = request.json
    d = datetime.strptime(data["Price Date"], "%Y-%m-%d")
    data["day"], data["month"], data["year"] = d.day, d.month, d.year
    del data["Price Date"]

    for col, enc in label_encoders.items():
        data[col] = int(enc.transform([data[col]])[0])

    X = pd.DataFrame([data])[feature_schema]
    modal = float(model.predict(X)[0])

    return jsonify({
        "Predicted_Modal_Price": round(modal, 2),
        "Estimated_Min_Price": round(modal * alpha, 2),
        "Estimated_Max_Price": round(modal * beta, 2)
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

