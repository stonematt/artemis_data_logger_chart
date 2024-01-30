document.addEventListener('DOMContentLoaded', function () {
  const socket = io.connect(
    location.protocol + '//' + document.domain + ':' + location.port
  );
  const ctx = document.getElementById('dataChart').getContext('2d');
  const columnSelect = document.getElementById('columnSelect');
  const submitButton = document.getElementById('submitColumns');

  // Initialize Chart.js
  const myChart = new Chart(ctx, {
    type: 'line',
    data: {
      labels: [], // Time labels
      datasets: [
        {
          label: 'Data',
          data: [], // Data values
          borderColor: 'rgb(75, 192, 192)',
          tension: 0.1,
        },
      ],
    },
    options: {
      scales: {
        y: {
          beginAtZero: true,
        },
      },
    },
  });

  // Listen for 'header_data' event from Flask-SocketIO
  socket.on('header_data', function (header) {
    // console.log('Received header data:', header);
    // Clear existing options in the dropdown
    columnSelect.innerHTML = '';

    // Dynamically add new options based on received header data
    header.forEach((col) => {
      let option = document.createElement('option');
      option.value = col;
      option.text = col;
      columnSelect.appendChild(option);
    });
  });

  // Handle button click to submit selected columns
  submitButton.addEventListener('click', function () {
    let selectedOptions = columnSelect.selectedOptions;
    let selectedColumns = Array.from(selectedOptions).map(
      (option) => option.value
    );

    // Emit the selected columns to the server
    socket.emit('update_selected_columns', selectedColumns);
  });

  // Handle incoming data for the selected column(s)
  socket.on('serial_data', function (data) {
    // Assuming you want to update the chart for the first selected column only
    const selectedColumn = columnSelect.value;
    if (data.hasOwnProperty(selectedColumn)) {
      // Update chart with new data
      myChart.data.labels.push(new Date().toLocaleTimeString());
      myChart.data.datasets.forEach((dataset) => {
        dataset.data.push(data[selectedColumn]);
      });
      myChart.update();
    }
  });

  // Handle column selection change (Optional, depending on your needs)
  columnSelect.addEventListener('change', function () {
    // Clear existing chart data when a new column is selected
    myChart.data.labels = [];
    myChart.data.datasets.forEach((dataset) => {
      dataset.data = [];
    });
    myChart.update();
  });
});
