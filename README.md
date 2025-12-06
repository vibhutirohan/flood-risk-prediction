 🌊 Flood Risk Prediction Dashboard

### *AI-powered Flood Vulnerability Intelligence with Interactive Analytics, Weather Insights & Predictive Modeling*

<p align="center">
  <img src="https://img.shields.io/badge/Streamlit-Deployed-brightgreen?style=for-the-badge&logo=streamlit" />
  <img src="https://img.shields.io/badge/Python-3.10+-blue?style=for-the-badge&logo=python" />
  <img src="https://img.shields.io/badge/ML-XGBoost-orange?style=for-the-badge" />
  <img src="https://img.shields.io/badge/Data-Flood%20Risk%20Dataset-yellow?style=for-the-badge" />
</p>

---

## 🌐 **Live Demo**

👉 **[https://flood-risk-prediction.streamlit.app/](https://flood-risk-prediction.streamlit.app/)**

---

## 📖 Overview

This project delivers a powerful **Flood Risk Prediction Dashboard** built using machine learning and interactive visual analytics.
Users can input environmental parameters, run predictions, explore breakdowns, generate PDF reports, and view weather-based insights — all in one clean interface.

Built using:

* Streamlit
* XGBoost
* Plotly
* Pandas / NumPy
* FPDF
* Weather + hydrology data

---

## ⭐ Key Features

* 🌧 **AI-based flood probability prediction**
* ⚙️ **What-if scenario analysis**
* 📊 **Interactive charts & risk dashboards**
* 📍 **Location-aware predictions using latitude/longitude**
* 🌤 **Weather snapshot integration**
* 📄 **Downloadable PDF reports**
* 🗂 **Multiple scenario history**

---

# 🗂 Folder Structure

```
flood-risk-prediction/
├── api/
├── app/
├── streamlit_app/
│   └── app.py
├── src/
├── models/
├── data/
│   └── raw/
├── notebooks/
├── reports/
├── tests/
├── config.py
├── README.md
└── requirements.txt
```

---

# 🧠 Model Details

* **Model:** XGBoost
* **Inputs:** Rainfall, hydrology, soil saturation, elevation, drainage, land cover
* **Output:** Flood probability score (0–1), risk category

---

# 📊 Datasets Used

| File                                    | Size    | Description                  |
| --------------------------------------- | ------- | ---------------------------- |
| `flood_data.xlsx`                       | ~356 KB | Historical flood indicators  |
| `urban_pluvial_flood_risk_dataset.xlsx` | ~430 KB | Rainfall + hydrology dataset |

---

# 🚀 Run the Project Locally

Follow these steps to set up the Flood Risk Prediction Dashboard on your local machine.

---

### **1️⃣ Clone the repository**

```bash
git clone https://github.com/vibhutirohan/flood-risk-prediction.git
cd flood-risk-prediction
```

---

### **2️⃣ Create a virtual environment**

```bash
python -m venv venv
```

#### **Activate the environment**

**Windows**

```bash
venv\Scripts\activate
```

**macOS / Linux**

```bash
source venv/bin/activate
```

---

### **3️⃣ Install dependencies**

```bash
pip install -r requirements.txt
```

---

### **4️⃣ Launch the Streamlit app**

```bash
streamlit run streamlit_app/app.py
```

---

# 🤖 Tech Stack

* Python
* Streamlit
* XGBoost
* Plotly
* Pandas / NumPy
* FPDF
* Matplotlib / Seaborn

---

# 🔮 Future Enhancements

* Geospatial flood mapping
* LSTM rainfall forecasting
* Real-time hydrology API
* Full FastAPI backend deployment
* Risk mapping with satellite imagery


