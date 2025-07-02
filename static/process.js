    let imageBase64 = "";
    let sessionId = "";

    const dropZone = document.getElementById("drop-zone");
    const fileInput = document.getElementById("fileInput");
    const preview = document.getElementById("preview");

    dropZone.addEventListener("click", () => fileInput.click());
    dropZone.addEventListener("dragover", e => {
      e.preventDefault(); dropZone.classList.add("dragover");
    });
    dropZone.addEventListener("dragleave", () => dropZone.classList.remove("dragover"));
    dropZone.addEventListener("drop", e => {
      e.preventDefault(); dropZone.classList.remove("dragover");
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

    //Step 1
    document.getElementById("submit-initial").addEventListener("click", async () => {
      if (!imageBase64) return alert("Please upload a PNG image.");
      document.getElementById("loadingInit").style.display = "block";

      const payload = {
        image_data: imageBase64,
        max_freq: parseInt(document.getElementById("max_freq").value),
        top: parseFloat(document.getElementById("top").value),
        bottom: parseFloat(document.getElementById("bottom").value),
        left: parseFloat(document.getElementById("left").value),
        right: parseFloat(document.getElementById("right").value)
      };

      const response = await fetch("/process-initial", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });

      const result = await response.json();
      document.getElementById("initialPlot").src = result.image_path;
      sessionId = result.session_id;

      // Show second form
      document.getElementById("step2").style.display = "block";
      document.getElementById("loadingInit").style.display = "none";
      const count = parseInt(document.getElementById("max_freq").value);
      const zeros = Array(count).fill(0).join(",");
      document.getElementById("gain_shift").value = zeros;
      document.getElementById("pout_shift").value = zeros;
    });

    //Step 2
    document.getElementById("submit-relabel").addEventListener("click", async () => {
      if (!sessionId) return alert("No session found.");
      document.getElementById("loadingRelabel").style.display = "block";

      const payload = {
        session_id: sessionId,
        color_list: document.getElementById("color_list").value.split(',').map(Number),
        gain_shift: null,
        pout_shift: null
      };

      const response = await fetch("/process-relabel", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });

      const result = await response.json();
      document.getElementById("relabelPlot").src = result.image_url;
      document.getElementById("loadingRelabel").style.display = "none";

      // Show third form
      document.getElementById("step3").style.display = "block";
    });

    //Step 3
    document.getElementById("submit-shift").addEventListener("click", async () => {
      if (!sessionId) return alert("No session found.");
      document.getElementById("loadingFinal").style.display = "block";

      const payload = {
        session_id: sessionId,
        color_list: document.getElementById("color_list").value.split(',').map(Number),
        gain_shift: document.getElementById("gain_shift").value.trim()
          ? document.getElementById("gain_shift").value.split(',').map(Number)
          : null,
        pout_shift: document.getElementById("pout_shift").value.trim()
          ? document.getElementById("pout_shift").value.split(',').map(Number)
          : null
      };

      const response = await fetch("/process-shift", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });

      const result = await response.json();
      document.getElementById("finalPlot").src = result.image_url;
      document.getElementById("loadingFinal").style.display = "none";
    });