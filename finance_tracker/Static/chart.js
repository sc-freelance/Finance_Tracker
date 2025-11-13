const form = document.getElementById("uploadForm"); // Form element
const modelSelect = document.getElementById("modelSelect"); // Model selection dropdown
const degreeContainer = document.getElementById("degreeContainer"); // Container for degree selection
const degreeSelect = document.getElementById("degreeSelect"); // Degree selection dropdown
const statusDiv = document.getElementById("status"); // Status message div
const chartCanvas = document.getElementById("forecastChart"); // Chart canvas element
let chartInstance = null; // Chart.js instance (initialized later)

// Showcasing the status of upload
function showStatus(message, type = "loading") {
  statusDiv.className = "status-box";
  if (type === "success") statusDiv.classList.add("status-success");
  else if (type === "error") statusDiv.classList.add("status-error");
  else statusDiv.classList.add("status-loading");
  statusDiv.textContent = message;
  statusDiv.style.display = "block";
}

// Show/hide degree selection based on model choice
modelSelect.addEventListener("change", () => {
  degreeContainer.style.display = modelSelect.value === "linear" ? "none" : "block";
});

// Handle form submission
form.addEventListener("submit", async (e) => {
  e.preventDefault();

  try {
    const formData = new FormData(form);
    const modelType = modelSelect.value;
    const degree = degreeSelect.value;

    // Show "loading" message
    showStatus("Uploading and analyzing data...", "loading");

    // --- Upload CSV ---
    const uploadRes = await fetch("/upload", { method: "POST", body: formData });
    const uploadData = await uploadRes.json(); // ✅ Define uploadData properly
    if (!uploadRes.ok) throw new Error(uploadData.error || "Upload failed");

    showStatus("✅ " + (uploadData.message || "File uploaded successfully!"), "success");

    // --- Request Forecast ---
    const forecastRes = await fetch(`/api/forecast?model=${modelType}&degree=${degree}`);
    const forecastData = await forecastRes.json();
    if (!forecastRes.ok) throw new Error(forecastData.error || "Forecast failed");

    // --- Chart rendering ---
    const ctx = chartCanvas.getContext("2d");
    if (chartInstance) chartInstance.destroy();

    const combinedLabels = [
      ...forecastData.past.labels,
      ...forecastData.forecast.labels,
    ];
    const pastLength = forecastData.past.labels.length;

    const combinedValues = [
      ...forecastData.past.values,
      ...Array(30).fill(null),
    ];

    chartInstance = new Chart(ctx, {
      type: "line",
      data: {
        labels: combinedLabels,
        datasets: [
          {
            label: "Past Spending (Actual)",
            data: combinedValues,
            borderColor: "steelblue",
            borderWidth: 2,
            fill: false,
            tension: 0.2,
          },
          {
            label: `${forecastData.model_used} Prediction`,
            data: [
              ...Array(pastLength).fill(null),
              ...forecastData.forecast.values,
            ],
            borderColor:
              modelType === "linear"
                ? "orange"
                : degree === "2"
                ? "brown"
                : degree === "3"
                ? "green"
                : "purple",
            borderWidth: 2,
            borderDash: [6, 4],
            fill: false,
            tension: 0.3,
          },
        ],
      },
      options: {
        responsive: true,
        plugins: {
          title: {
            display: true,
            text: `Past Spending vs 30-Day Forecast (${forecastData.model_used})`,
            font: { size: 18, weight: "bold" },
          },
          legend: { labels: { color: "#333" } },
        },
        scales: {
          x: { title: { display: true, text: "Date" } },
          y: { title: { display: true, text: "Amount ($)" } },
        },
      },
    });

    showStatus(`✅ Forecast generated using ${forecastData.model_used}`, "success");

  } catch (err) {
    showStatus("❌ Error: " + err.message, "error");
  }
});