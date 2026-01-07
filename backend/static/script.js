// ===============================
// Farmers Market Price Prediction
// Frontend Script (FINAL VERSION)
// ===============================

// Load dropdowns when page loads
window.onload = () => {
  loadDropdown("/states", "state", "Select State");
  loadDropdown("/districts", "district", "Select District");
  loadDropdown("/markets", "market", "Select Market");
  loadDropdown("/commodities", "commodity", "Select Commodity");
};

// Generic dropdown loader
function loadDropdown(url, elementId, placeholder) {
  fetch(url)
    .then(response => response.json())
    .then(data => {
      const select = document.getElementById(elementId);
      select.innerHTML = `<option value="">${placeholder}</option>`;

      data.forEach(item => {
        const option = document.createElement("option");
        option.value = item;
        option.textContent = item;
        select.appendChild(option);
      });
    })
    .catch(error => {
      console.error(`Error loading ${elementId}:`, error);
    });
}

// ===============================
// Predict Price Function
// ===============================
function predictPrice() {
  const state = document.getElementById("state").value;
  const district = document.getElementById("district").value;
  const market = document.getElementById("market").value;
  const commodity = document.getElementById("commodity").value;
  const date = document.getElementById("priceDate").value;

  // Basic validation
  if (!state || !district || !market || !commodity || !date) {
    alert("Please fill all fields before prediction.");
    return;
  }

  const payload = {
    "STATE": state,
    "District Name": district,
    "Market Name": market,
    "Commodity": commodity,
    "Variety": "Other",
    "Grade": "FAQ",
    "Price Date": date
  };

  fetch("/predict", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  })
    .then(response => response.json())
    .then(data => {
      displayResult(data);
    })
    .catch(error => {
      console.error("Prediction error:", error);
      alert("Error occurred while predicting price.");
    });
}

// ===============================
// Display Result + Profit/Loss
// ===============================
function displayResult(data) {
  const resultDiv = document.getElementById("result");
  resultDiv.style.display = "block";

  const modal = data.Predicted_Modal_Price;
  const minPrice = data.Estimated_Min_Price;
  const maxPrice = data.Estimated_Max_Price;

  // Profit / Loss logic
  const range = maxPrice - minPrice;
  const position = modal - minPrice;
  const score = position / range;

  let statusText = "";
  let statusColor = "";

  if (score >= 0.66) {
    statusText = "🟢 PROFIT ZONE – Good time to sell";
    statusColor = "#2e7d32";
  } else if (score <= 0.33) {
    statusText = "🔴 LOSS RISK – Better to wait";
    statusColor = "#c62828";
  } else {
    statusText = "🟡 NEUTRAL – Hold and monitor market";
    statusColor = "#f9a825";
  }

  // Render result
  resultDiv.innerHTML = `
    <h3>📊 Price Prediction Result</h3>

    <div class="result-item">
      <b>Step 1:</b> Predicted Modal Price<br>
      ₹ ${modal}
    </div>

    <div class="result-item">
      <b>Step 2:</b> Estimated Minimum Price<br>
      ₹ ${minPrice}
    </div>

    <div class="result-item">
      <b>Step 3:</b> Estimated Maximum Price<br>
      ₹ ${maxPrice}
    </div>

    <hr>

    <div class="result-item" style="font-weight:bold; color:${statusColor}">
      Farmer Insight: ${statusText}
    </div>
  `;
}
