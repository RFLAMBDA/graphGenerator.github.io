from flask import Flask, request, jsonify, send_from_directory, render_template_string, render_template
import base64
import uuid
import os
import random
from io import BytesIO
from PIL import Image
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image
from collections import defaultdict
from scipy.spatial import KDTree
from scipy.stats import zscore
import sys

# --- Define Flask app and output dir ---
app = Flask(__name__)

APP_VERSION = "1.2.2"

@app.route("/")
def index():
    return render_template("index.html", version=APP_VERSION)

OUTPUT_DIR = "static/results"
os.makedirs(OUTPUT_DIR, exist_ok=True)
data_points = []

# --- Import your extraction function here or define inline (simplified stub below) ---
def extract_data_from_plot(image_path, left, top, bottom, right, max_colors, distance_threshold=10, points_n=20):
    try:
        # Open and convert the image to RGB mode
        img = Image.open(image_path).convert('RGB')
        img_array = np.array(img)
        
        # Dictionary to count occurrences of each color
        color_counts = defaultdict(int)
        height, width, _ = img_array.shape

        # Detect and count unique colors
        for y in range(height):  # Sampling to speed up
            for x in range(width):
                color = tuple(img_array[y, x, :3])
                if not(color[0] == color[1] == color[2]):  # Ignore grayscale
                    color_counts[color] += 1

        
        # Select the top N colors based on frequency
        top_colors = sorted(color_counts, key=color_counts.get, reverse=True)[:max_colors]

        # Dictionary to store x, y points for each color
        data_points = {color: ([], []) for color in top_colors}

        # Extract points for selected colors
        for y in range(height):
            for x in range(width):
                color = tuple(img_array[y, x, :3])
                if color in top_colors:
                    data_points[color][0].append(x)
                    data_points[color][1].append(height - y)  # Flip y-axis


        # Function to remove isolated points
        def filter_noise(x_values, y_values, threshold, diff = 50):
            prev_y = -1
            if len(x_values) < 3:  # Avoid processing very small datasets
                return x_values, y_values

            points = np.array(list(zip(x_values, y_values)))
            points = sorted(points, key=lambda point: point[0], reverse=True)

            filtered_x, filtered_y = [], []
            for i, (x, y) in enumerate(points):
                if prev_y == -1 or np.abs(prev_y - y) < diff:
                  prev_y = y
                  filtered_x.append(x)
                  filtered_y.append(y)

            return filtered_x, filtered_y

        # Apply noise filtering
        for color in data_points:
            x_vals, y_vals = data_points[color]
            data_points[color] = filter_noise(x_vals, y_vals, distance_threshold)

        


        def pixel_real(data_points):
          color_b_max = -1
          color_b_min = sys.maxsize
          color_r_max = -1
          color_r_min = sys.maxsize

          for color in data_points:
              x_vals, y_vals = data_points[color]
              if color_b_max < y_vals[0]:
                  color_b_max = y_vals[0]
              if color_b_min > y_vals[-1]:
                  color_b_min = y_vals[-1]

              if color_r_max < x_vals[0]:
                  color_r_max = x_vals[0]
              if color_r_min > x_vals[-1]:
                  color_r_min = x_vals[-1]

          for color in data_points:
              x_vals, y_vals = data_points[color]

              y_v = float(top*color_b_min-bottom*color_b_max)/float(top - bottom)
              x_v = top/(color_b_max-y_v)

              y_h = float(right*color_r_min - left*color_r_max)/float(right - left)
              x_h = right/(color_r_max-y_h)

              for i in range(len(y_vals)):
                y_vals[i] = (y_vals[i]-y_v)*x_v
                x_vals[i] = (x_vals[i]-y_h)*x_h

              data_points[color] = (x_vals, y_vals)

          return data_points

        # Calculate scaling
        data_points = pixel_real(data_points)

        # Convert to Pout vs Pin
        new_data_points = {}
        for color in data_points:
            x_vals, y_vals = data_points[color]
            new_x_vals = y_vals
            new_y_vals = [a - b for a, b in zip(y_vals, x_vals)]
            new_data_points[color] = (new_x_vals, new_y_vals)

        # Get a few points

        for color in new_data_points:
            x_vals, y_vals = new_data_points[color]
            new_x_vals = []
            new_y_vals = []
            if len(x_vals) > points_n:
              for i in range(0, len(x_vals), int(len(x_vals)/points_n)):
                new_x_vals.append(x_vals[i])
                new_y_vals.append(y_vals[i])
              new_data_points[color] = (new_x_vals, new_y_vals)

        return new_data_points

    except FileNotFoundError:
        print(f"Error: Image file '{image_path}' not found.")
        sys.stdout.flush()
        
        return {}
    except Exception as e:
        print(f"An error occurred: {e}")
        sys.stdout.flush()
        return {}

def get_random_rgb(exclude_list):
    # Convert list of tuples/lists to set of tuples for fast lookup
    exclude_set = set(tuple(rgb) for rgb in exclude_list)
    while True:
        rgb = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
        if rgb not in exclude_set:
            return rgb

# --- Plotting and shifting logic ---
def generate_plot(data_points, gain_shift, pout_shift, color_list, x_ticks=8, y_ticks=6):
    output_file = os.path.join(OUTPUT_DIR, f"plot_{uuid.uuid4().hex}.png")
    plt.figure(figsize=(8, 6))
    rgb_keys = list(data_points.keys())
    max_freq = len(rgb_keys)
    max_x = -1
    min_x = sys.maxsize
    max_y = -1
    min_y = sys.maxsize
    vals = []
    legends = []

    # Sort the zipped list by the first element (list1)
    sorted_zip = sorted(zip(color_list, list(range(0, len(color_list)))), key=lambda x: x[0])

    # Unzip (split back into separate lists)
    _, order = zip(*sorted_zip)
    
    # Convert to lists (since zip returns tuples)
    sorted_zip = sorted(zip(list(order), pout_shift, gain_shift), key=lambda x: x[0])

    # Unzip (split back into separate lists)
    _, pout_shift, gain_shift = zip(*sorted_zip)

    pout_shift = list(pout_shift)
    gain_shift = list(gain_shift)
        

    for i, rgb in enumerate(rgb_keys):
        x_vals, y_vals = data_points[rgb]
        shifted_x = [x + pout_shift[i] for x in x_vals]
        shifted_y = [y + gain_shift[i] for y in y_vals]
        max_x = max(max_x, max(shifted_x))
        min_x = min(min_x, min(shifted_x))
        max_y = max(max_y, max(shifted_y))
        min_y = min(min_y, min(shifted_y))
        label = color_list[i] if color_list[i] != 0 else f"Color {i+1}"
        legends.append(label)
        line, = plt.plot(shifted_x, shifted_y, color=np.array(rgb) / 255, label=label)
        vals.append(line)

    if type(legends[0]) != str:
        # Sort the zipped list by the first element (list1)
        sorted_zip = sorted(zip(vals, legends, rgb_keys), key=lambda x: x[1])

        # Unzip (split back into separate lists)
        vals, legends, rgb_keys = zip(*sorted_zip)
        
        # Convert to lists (since zip returns tuples)
        vals = list(vals)
        legends = list(legends)
        
        for i in range(0, max_freq):
            legends[i] = str(legends[i]) + "GHz"

    plt.xlabel("Pout (dBm)")
    plt.ylabel("Gain (dB)")
    plt.title("Gain vs. Pout")
    plt.grid(True)
    plt.xticks(np.arange(np.ceil(min_x), np.ceil(max_x)+1, np.ceil((max_x - min_x)/5)))
    plt.yticks(np.arange(np.ceil(min_y), np.ceil(max_y)+1, np.ceil((max_y - min_y)/5)))
    # plt.gca().set_aspect('equal', adjustable='box')
    # Enforce proportional scaling
    plt.gca().set_aspect(y_ticks/x_ticks, adjustable='box')
    handles, labels = plt.gca().get_legend_handles_labels()
    plt.tight_layout()
    if handles:
        plt.legend(vals, legends,loc='center left', bbox_to_anchor=(1, 0.5))
    plt.savefig(output_file, bbox_inches='tight')
    plt.close()
    return output_file


# --- Step 1: initial image processing ---
@app.route("/process-initial", methods=["POST"])
def process_initial():
    data = request.json
    image_data = data["image_data"].split(",")[1]
    image_bytes = base64.b64decode(image_data)
    image = Image.open(BytesIO(image_bytes)).convert("RGB")
    image_path = os.path.join(OUTPUT_DIR, f"input_{uuid.uuid4().hex}.png")
    image.save(image_path)
    global data_points
    data_points = extract_data_from_plot(
        image_path,
        data["left"],
        data["top"],
        data["bottom"],
        data["right"],
        data["max_freq"]
    )
    request_id = uuid.uuid4().hex
    session_file = os.path.join(OUTPUT_DIR, f"session_{request_id}.npz")
    np.savez(session_file, **{str(k): v for k, v in data_points.items()})
    gain_shift = [0.0] * len(data_points)
    pout_shift = [0.0] * len(data_points)
    color_list = [0.0] * len(data_points)
    output_file = generate_plot(data_points, gain_shift, pout_shift, color_list)
    return jsonify({"image_path": f"/{output_file}", "session_id": request_id})

# --- Step 2: add more color ---
@app.route("/process-add", methods=["POST"])
def process_add():
    data = request.json
    if data["image_data"]:
        image_data = data["image_data"].split(",")[1]
        image_bytes = base64.b64decode(image_data)
        image = Image.open(BytesIO(image_bytes)).convert("RGB")
        image_path = os.path.join(OUTPUT_DIR, f"input_{uuid.uuid4().hex}.png")
        image.save(image_path)
        data_points_add = extract_data_from_plot(
            image_path,
            data["left"],
            data["top"],
            data["bottom"],
            data["right"],
            1 #only get one
        )
        _, rgb_value = next(iter(data_points_add.items()))
    else:
        image_data = None
        rgb_value = None
    request_id = uuid.uuid4().hex
    session_file = os.path.join(OUTPUT_DIR, f"session_{request_id}.npz")
    global data_points #make it sync globally
    rgb_keys = list(data_points.keys())
    if data["color_num"]-1 < len(data_points):
        if rgb_value:
            data_points[rgb_keys[data["color_num"]-1]] = rgb_value
        else:
            del data_points[rgb_keys[data["color_num"]-1]]
    else:
        if rgb_value:
            data_points[get_random_rgb(rgb_keys)] = rgb_value

    np.savez(session_file, **{str(k): v for k, v in data_points.items()})
    gain_shift = [0.0] * len(data_points)
    pout_shift = [0.0] * len(data_points)
    color_list = [0.0] * len(data_points)
    output_file = generate_plot(data_points, gain_shift, pout_shift, color_list)
    return jsonify({"image_path": f"/{output_file}", "session_id": request_id})

# --- Step 2: apply relabel ---
@app.route("/process-relabel", methods=["POST"])
def process_relabel():
    data = request.json
    session_file = os.path.join(OUTPUT_DIR, f"session_{data['session_id']}.npz")
    npz_data = np.load(session_file, allow_pickle=True)
    data_points = {eval(k): tuple(v) for k, v in npz_data.items()}
    x_ticks, y_ticks = data.get("scale") or [0.0] * 2
    gain_shift = data.get("gain_shift") or [0.0] * len(data_points)
    pout_shift = data.get("pout_shift") or [0.0] * len(data_points)
    color_list = data.get("color_list") or [0.0] * len(data_points)
    output_file = generate_plot(data_points, gain_shift, pout_shift, color_list, x_ticks, y_ticks)
    return jsonify({"image_url": f"/{output_file}"})

# --- Step 3: apply shifts ---
@app.route("/process-shift", methods=["POST"])
def process_shift():
    data = request.json
    session_file = os.path.join(OUTPUT_DIR, f"session_{data['session_id']}.npz")
    npz_data = np.load(session_file, allow_pickle=True)
    data_points = {eval(k): tuple(v) for k, v in npz_data.items()}
    x_ticks, y_ticks = data.get("scale") or [0.0] * 2
    gain_shift = data.get("gain_shift") or [0.0] * len(data_points)
    pout_shift = data.get("pout_shift") or [0.0] * len(data_points)
    color_list = data.get("color_list") or [0.0] * len(data_points)
    output_file = generate_plot(data_points, gain_shift, pout_shift, color_list, x_ticks, y_ticks)
    return jsonify({"image_url": f"/{output_file}"})

# --- Serve static files ---
@app.route("/static/results/<filename>")
def result_image(filename):
    return send_from_directory(OUTPUT_DIR, filename)

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)