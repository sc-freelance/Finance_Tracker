const form = document.getElementById("uploadForm"); // Form element
const modelSelect = document.getElementById("modelSelect"); // Model selection dropdown
const degreeContainer = document.getElementById("degreeContainer"); // Container for degree selection
const degreeSelect = document.getElementById("degreeSelect"); // Degree selection dropdown
const statusDiv = document.getElementById("status"); // Status message div
const chartCanvas = document.getElementById("forecastChart"); // Chart canvas element
let chartInstance = null; // Chart.js instance (initialized later)

// Show/hide degree selection based on model choice
modelSelect.addEventListener("change", () => {
  degreeContainer.style.display = 
    modelSelect.value === "linear" ? "none" : "block";
});

// Handle form submission
form.addEventListener("submit", async(e) => {
  e.preventDefault();
  
  const formData = new FormData(form); // Collect form data
  const modelType = modelSelect.value; // Selected model type 
  const degree = degreeSelect.value; // Selected polynomial degree
  statusDiv.textContent = "Uploading and analysing data..."; // Initial status message

  // Upload file to server and request forecast
  try {
    const uploadRes = await fetch("/upload", { method: "POST", body: formData }); // Upload endpoint
    const uploadData = await uploadRes.json();// Parse JSON Response
    if (uploadData.error) throw new Error(uploadData.error); // Handle upload errors
    statusDiv.textContent = "✅ " + uploadData.message; // Update status on success

    const forecastRes = await fetch(`/api/forecast?model=${modelType}&degree=${degree}`); // Forecast endpoint
    const forecastData = await forecastRes.json(); // Parse JSON Response
    if (forecastData.error) {
      statusDiv.textContent = "❌ " + forecastData.error; // Handle forecast errors
      return; // Exit on error
    }

    const ctx = chartCanvas.getContext("2d"); // Get canvas context
    if (chartInstance) chartInstance.destroy(); // Destroy previous chart if exists
    
    // Combine past and forecast data for charting
    const combinedLabels = [
      ...forecastData.past.labels,
      ...forecastData.forecast.labels,
    ];

    const pastLength = forecastData.past.labels.length; // Length of past data
    
    // Combine past values with nulls for future spacing
    const combinedValues = [
      ...forecastData.past.values,
      ...Array(30).fill(null), // pad future for spacing
    ];

    // Create new Chart.js instance
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

      // Chart configuration options
      options: {
        responsive: true,
        plugins: {
          title: {
            display: true,
            text: `Past Spending vs 30-Day Forecast (${forecastData.model_used})`,
            font: { size: 18, weight: "bold" },
          },
          legend: {
            labels: { color: "#333" },
          },
        },
        scales: {
          x: { title: { display: true, text: "Date" } },
          y: { title: { display: true, text: "Amount ($)" } },
        },
      },
    });

    // Update status on successful forecast
    statusDiv.textContent = `✅ Forecast generated using ${forecastData.model_used}`;
  } catch (err) {
    statusDiv.textContent = "❌ Error: " + err.message;
  }
});