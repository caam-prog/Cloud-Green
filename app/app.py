import glob
import os
from io import BytesIO

import boto3
import requests
from PIL import Image
from flask import Flask, render_template, request, flash
from werkzeug.utils import secure_filename

# linea aggiuntiva
from requests.api import get


app = Flask(__name__)

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(ROOT_DIR, "static")
app.config['UPLOAD_FOLDER'] = UPLOAD_DIR

# create 'static' folder if not exists
if not os.path.exists(UPLOAD_DIR):
    os.mkdir(UPLOAD_DIR)

# configure boto3 client
s3_client = boto3.client('s3')


# utility functions
def get_s3_url(bucket_name, filename):
    return f"https://{bucket_name}.s3.amazonaws.com/{filename}"


def request_and_save(url, filename):
    req = requests.get(url)

    im = Image.open(BytesIO(req.content))
    path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    im.save(path, "PNG")

    return path


# app endpoints
@app.route('/', methods=['GET', 'POST'])
def index():

    filename = None
    if request.method == 'POST':
        f = request.files['file']
        filename = secure_filename(f.filename)
        f.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

    return render_template('upload.html', filename=filename)


@app.route('/watermark', methods=['POST'])
def apply_watermark():
    bucket_name = "apppy" # INSERT YOUR BUCKET NAME

    filename = request.form['filename']
    path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    r1 = s3_client.upload_file(path, bucket_name, filename, ExtraArgs={'ACL': 'public-read'})

# bucket_url = 'http://apppy.s3-website.us-east-2.amazonaws.com' + filename
# api key for qrakajack 


# come dovrebbe essere
# api key P23OWF071I39S6QUR2EL9MDT74B165JX48CKYZ8N0A5VHG

    image_url = get_s3_url(bucket_name=bucket_name, filename=filename)
    qr_url = get_s3_url(bucket_name = bucket_name, filename = qr_name)

    # GENERATE REQUEST FOR QRACKAJACK
    qr_req_url = f'https://qrackajack.expeditedaddons.com/?api_key=71T2JH3V6SAU450B710COPYI58WM39298FNDQ4G6RXKLEZ&bg_color=%23ffffff&content={qr_url}&fg_color=%23000000&height=256&width=256'

    qr_name = f"qr_{filename}"
    qr_path = request_and_save(qr_req_url, qr_name)

    r2 = s3_client.upload_file(qr_path, bucket_name, qr_name, ExtraArgs={'ACL': 'public-read'})

    

    # GENERATE REQUEST FOR WATERMARKER
    watermark_req_url = f'https://watermarker.expeditedaddons.com/?api_key=IS431O1AX38GYW8DH07C2U6K6045NMF9R5PE7QTLZVBJ29&height=100&image_url={image_url}&opacity=50&position=center&watermark_url={qr_url}&width=100'

    watermark_name = f"watermark_{filename}"
    request_and_save(watermark_req_url, watermark_name)

    print("watermark done")

    # clean bucket
    s3_client.delete_object(Bucket=bucket_name, Key=qr_name)

    return render_template("upload.html", filename=watermark_name)


if __name__ == '__main__':
    app.run(debug=True)
