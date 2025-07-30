# Gain vs Pout Extractor

A Flask + JavaScript web app that converts amplifier gain vs. output power plots (PNG images) into clean numeric data and lets you adjust curves interactively.

---
## 🚀 Features Version 1.2.1
    
- Fixed the bug with adding a skip on step 2

## Past Version 1.2.0
    
- **Enhanced Step 2 Functionality**: Added drag-and-drop and click-to-select file upload for the "Add more color" section
- Improved user experience with responsive file upload interface
- Better error handling for invalid file types in Step 2

## Past Version 1.1.1
    
- Added a new "scaling" section

## Past Version 1.1.0
    
- Added a new "Relabeled" stage
- Change the shift ordering fitting with the descending order

## Past Version 1.0.0
    
- Upload a PNG plot image in your browser  
- Automatically extract curve data points  
- Adjust curves with `gain_shift` and `pout_shift`  
- Preview and download updated plots

---

## 📁 Project Structure

```
gain-vs-pout-app/
├── app.py # Flask backend
├── templates/
│ └── index.html # Frontend UI
├── static/
│ └── results/ # Generated and session images
├── requirements.txt
├── Dockerfile (optional)
└── README.md
```

---

## 🛠️ Requirements

- Python 3.10+
- Flask, Pillow, NumPy, Matplotlib, SciPy
- (Optional) Docker

---

## ⚙️ Setup & Run Locally

### With Docker

Open Docker Desktop APP
```bash
docker build -t gain-vs-pout-app .
docker run -p 5000:5000 gain-vs-pout-app
```

Now visit http://localhost:5000

### Without Docker

```bash
git clone https://github.com/RFLAMBDA/graphGenerator.github.io

cd graphGenerator.github.io
python3 -m venv venv
source venv/bin/activate       # or `venv\Scripts\activate` on Windows

pip install -r requirements.txt
python app.py
```

Then open http://localhost:5000

## 📫Deploy Server

Visit https://dashboard.render.com/web/srv-d0t593adbo4c739asbkg/deploys/dep-d1aahlripnbc739u2lgg
