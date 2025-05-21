from flask import Flask, request, jsonify, send_from_directory, render_template_string
import base64
import uuid
import os
from io import BytesIO
from PIL import Image
import matplotlib.pyplot as plt
import numpy as np

# --- Define Flask app and output dir ---
app = Flask(__name__)
OUTPUT_DIR = "static/results"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# --- Import your extraction function here or define inline (simplified stub below) ---
def extract_data_from_plot(image_path, left, top, bottom, right, max_colors):
    # Dummy plot generation for demonstration
    x = np.linspace(0, 10, 100)
    data_points = {}
    for i in range(max_colors):
        y = np.sin(x + i)
        color = (255 - i * 20, 100 + i * 10, 100)
        data_points[color] = (x.tolist(), y.tolist())
    return data_points

# --- Plotting and shifting logic ---
def generate_plot(data_points, gain_shift, pout_shift, color_list):
    output_file = os.path.join(OUTPUT_DIR, f"plot_{uuid.uuid4().hex}.png")
    plt.figure()
    for i, color in enumerate(color_list):
        rgb = tuple(data_points.keys())[i]
        x_vals, y_vals = data_points[rgb]
        shifted_x = [x + pout_shift[i] for x in x_vals]
        shifted_y = [y + gain_shift[i] for y in y_vals]
        plt.plot(shifted_x, shifted_y, color=np.array(rgb) / 255, label=f"{color}GHz")
    plt.xlabel("Pout (dBm)")
    plt.ylabel("Gain (dB)")
    plt.title("Gain vs. Pout")
    plt.legend()
    plt.grid(True)
    plt.savefig(output_file)
    plt.close()
    return output_file

# --- Main processing endpoint ---
@app.route("/process", methods=["POST"])
def process():
    data = request.json
    image_data = data["image_data"].split(",")[1]  # Strip data:image/png;base64,...
    image_bytes = base64.b64decode(image_data)
    image = Image.open(BytesIO(image_bytes)).convert("RGB")

    # Save temp image
    image_path = os.path.join(OUTPUT_DIR, f"input_{uuid.uuid4().hex}.png")
    image.save(image_path)

    data_points = extract_data_from_plot(
        image_path,
        data["left"],
        data["top"],
        data["bottom"],
        data["right"],
        data["max_freq"]
    )

    # Handle optional gain_shift and pout_shift
    num_colors = len(data["color_list"])
    gain_shift = data.get("gain_shift") or [0.0] * num_colors
    pout_shift = data.get("pout_shift") or [0.0] * num_colors

    output_file = generate_plot(
        data_points,
        gain_shift,
        pout_shift,
        data["color_list"]
    )

    return jsonify({"image_url": f"/{output_file}"})

# --- Serve static files ---
@app.route("/static/results/<filename>")
def result_image(filename):
    return send_from_directory(OUTPUT_DIR, filename)

if __name__ == "__main__":
    app.run(debug=True)