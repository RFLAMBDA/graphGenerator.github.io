let imageBase64 = "";

    const dropZone = document.getElementById("drop-zone");
    const fileInput = document.getElementById("fileInput");
    const preview = document.getElementById("preview");
    const output = document.getElementById("output");
    const resultImage = document.getElementById("resultImage");

    dropZone.addEventListener("click", () => fileInput.click());
    dropZone.addEventListener("dragover", e => { e.preventDefault(); dropZone.classList.add("dragover"); });
    dropZone.addEventListener("dragleave", () => dropZone.classList.remove("dragover"));
    dropZone.addEventListener("drop", e => {
      e.preventDefault();
      dropZone.classList.remove("dragover");
      handleFile(e.dataTransfer.files[0]);
    });
    fileInput.addEventListener("change", e => handleFile(e.target.files[0]));

    function handleFile(file) {
      if (!file || file.type !== "image/png") return alert("Only PNG files allowed.");
      const reader = new FileReader();
      reader.onload = e => {
        imageBase64 = e.target.result;
        preview.src = imageBase64;
        preview.style.display = "block";
      };
      reader.readAsDataURL(file);
    }

    document.getElementById("extractForm").addEventListener("submit", async function (event) {
      event.preventDefault();
      if (!imageBase64) return alert("Please upload a PNG image.");

      const payload = {
        image_data: imageBase64,
        max_freq: parseInt(document.getElementById("max_freq").value),
        top: parseFloat(document.getElementById("top").value),
        bottom: parseFloat(document.getElementById("bottom").value),
        left: parseFloat(document.getElementById("left").value),
        right: parseFloat(document.getElementById("right").value),
        color_list: document.getElementById("color_list").value.split(',').map(Number),
        gain_shift: document.getElementById("gain_shift").value.trim() ? document.getElementById("gain_shift").value.split(',').map(Number) : null,
        pout_shift: document.getElementById("pout_shift").value.trim() ? document.getElementById("pout_shift").value.split(',').map(Number) : null
      };

      const response = await fetch("/process", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });

      
      output.style.display = "none"; // hide until image is ready

      console.log(response);
      const result = await response.json();
      document.getElementById("resultImage").src = result.image_url;
      output.style.display = "block";
    });