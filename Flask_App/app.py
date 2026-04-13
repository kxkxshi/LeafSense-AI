import os
import gdown
from flask import Flask, redirect, render_template, request, url_for
from PIL import Image
import torchvision.transforms.functional as TF
import CNN
import numpy as np
import torch
import pandas as pd

# =========================
# LOAD DATA
# =========================
disease_info = pd.read_csv('disease_info.csv', encoding='cp1252')
supplement_info = pd.read_csv('supplement_info.csv', encoding='cp1252')

# =========================
# DOWNLOAD MODEL (IMPORTANT FOR RENDER)
# =========================
MODEL_PATH = "plant_disease_model_1_latest.pt"

if not os.path.exists(MODEL_PATH):
    url = "https://drive.google.com/uc?id=1PAV9LYD08sKeQ01ndJMNdQSuHPREP8ss"
    gdown.download(url, MODEL_PATH, quiet=False)

# =========================
# LOAD MODEL
# =========================
model = CNN.CNN(39)
model.load_state_dict(torch.load(MODEL_PATH, map_location=torch.device('cpu')))
model.eval()

# =========================
# IMAGE FIX FUNCTION
# =========================
def fix_image(name, url):
    if pd.isna(url) or str(url).strip() == "":
        query = str(name).split()[0] if not pd.isna(name) else "fertilizer"
        return f"https://source.unsplash.com/400x300/?{query},plant"
    return url

# =========================
# PREDICTION FUNCTION
# =========================
def prediction(image_path):
    image = Image.open(image_path)
    image = image.convert('RGB')
    image = image.resize((224, 224))

    input_data = TF.to_tensor(image)
    input_data = input_data.view((-1, 3, 224, 224))

    output = model(input_data)
    output = output.detach().numpy()
    index = np.argmax(output)

    return index

# =========================
# FLASK APP
# =========================
app = Flask(__name__)

UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# =========================
# ROUTES
# =========================

@app.route('/')
def home_page():
    return render_template('home.html')

@app.route('/contact')
def contact():
    return render_template('contact-us.html')

@app.route('/index')
def ai_engine_page():
    return render_template('index.html')

@app.route('/mobile-device')
def mobile_device_detected_page():
    return render_template('mobile-device.html')

# =========================
# SUBMIT (AI RESULT)
# =========================
@app.route('/submit', methods=['POST'])
def submit():
    image = request.files.get('image')

    if image is None or image.filename == "":
        return redirect(url_for('ai_engine_page'))

    filename = image.filename
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    image.save(file_path)

    pred = prediction(file_path)

    # DATA
    title = disease_info['disease_name'][pred]
    description = disease_info['description'][pred]
    prevent = disease_info['Possible Steps'][pred]

    # SHOW USER UPLOADED IMAGE
    image_url = url_for('static', filename=f'uploads/{filename}')

    supplement_name = supplement_info['supplement name'][pred]
    supplement_image_url = fix_image(
        supplement_name,
        supplement_info['supplement image'][pred]
    )
    supplement_buy_link = supplement_info['buy link'][pred]

    return render_template(
        'submit.html',
        title=title,
        desc=description,
        prevent=prevent,
        image_url=image_url,
        pred=pred,
        sname=supplement_name,
        simage=supplement_image_url,
        buy_link=supplement_buy_link
    )

# =========================
# MARKET (SUPPLEMENTS PAGE)
# =========================
@app.route('/market')
def market():

    supplement_names = list(supplement_info['supplement name'])
    raw_images = list(supplement_info['supplement image'])

    fixed_images = [
        fix_image(name, img)
        for name, img in zip(supplement_names, raw_images)
    ]

    return render_template(
        'market.html',
        supplement_image=fixed_images,
        supplement_name=supplement_names,
        disease=list(disease_info['disease_name']),
        buy=list(supplement_info['buy link'])
    )

# =========================
# RUN APP
# =========================
if __name__ == '__main__':
    app.run(debug=True)

