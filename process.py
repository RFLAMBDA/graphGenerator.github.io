from flask import Flask, request, jsonify, send_from_directory
from your_script import extract_data_from_plot  # reuse your logic
import matplotlib.pyplot as plt
import os
import uuid

import base64
from io import BytesIO
from PIL import Image

app = Flask(__name__)
OUTPUT_DIR = "static/results"
os.makedirs(OUTPUT_DIR, exist_ok=True)

@app.route("/process", methods=["POST"])
def process():
    data = request.json
    image_data = data["image_data"].split(",")[1]  # Strip off data:image/png;base64,
    image_bytes = base64.b64decode(image_data)
    image = Image.open(BytesIO(image_bytes)).convert("RGB")

    # Save image temporarily
    image_path = f"static/tmp_{uuid.uuid4().hex}.png"
    image.save(image_path)

    # Use in your existing logic
    data_points = extract_data_from_plot(
        image_path,
        data["left"],
        data["top"],
        data["bottom"],
        data["right"],
        data["max_freq"]
    )

    # plotting logic...
    output_name = f"{uuid.uuid4().hex}.png"
    output_path = os.path.join(OUTPUT_DIR, output_name)

    # Plot your result
    for color, (x, y) in data_points.items():
        plt.plot(x, y, color=np.array(color) / 255)
    plt.savefig(output_path)
    plt.close()

    return jsonify({"image_url": f"/{output_path}"})

@app.route('/static/results/<filename>')
def send_image(filename):
    return send_from_directory(OUTPUT_DIR, filename)

if __name__ == "__main__":
    app.run(debug=True)
