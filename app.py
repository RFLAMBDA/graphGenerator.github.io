from flask import Flask, request, jsonify, send_from_directory, render_template_string, render_template
import base64
import uuid
import os
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

@app.route("/")
def index():
    return render_template("index.html")

OUTPUT_DIR = "static/results"
os.makedirs(OUTPUT_DIR, exist_ok=True)

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

# --- Plotting and shifting logic ---
def generate_plot(data_points, gain_shift, pout_shift, color_list):
    output_file = os.path.join(OUTPUT_DIR, f"plot_{uuid.uuid4().hex}.png")
    plt.figure()
    i = 1
    vals = []
    legends = []
    for color, (x, y) in data_points.items():
        if x and y:  # Check if extracted points exist
            line, = plt.plot(x, y, color=np.array(color) / 255, label=f"Color {i}", linewidth=2)
            vals.append(line)
        i+=1
        
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

    print("data len",len(data_points))
    sys.stdout.flush()
    # Handle optional gain_shift and pout_shift
    num_colors = len(data_points.keys())
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
    app.run(debug=True, host='0.0.0.0', port=5000)