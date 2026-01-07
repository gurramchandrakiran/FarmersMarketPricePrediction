import requests

url = "http://127.0.0.1:5000/predict"

data = {
    "STATE": "Haryana",
    "District Name": "panipat",
    "Market Name": "Panipat",
    "Commodity": "Tomato",
    "Variety": "Other",
    "Grade": "FAQ",
    "Price Date": "2024-06-15"
}

res = requests.post(url, json=data)

print("Status Code:", res.status_code)
print("Response:", res.text)
