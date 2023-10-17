import Chart from 'chart.js/auto';
import { format } from 'date-fns';
import axios from 'axios';
import L from 'leaflet';
import noUiSlider from 'nouislider';
import flatpickr from "flatpickr";

import 'chartjs-adapter-date-fns';
import 'hammerjs';
import 'chartjs-plugin-zoom';
import 'bootstrap';
import 'nouislider/dist/nouislider.css';
import 'leaflet/dist/leaflet.css';
import 'flatpickr/dist/flatpickr.min.css';
import './assets/styles.scss';

let rainfallChart;
let valueCountsChart;
let map;
let marker;
const baseURL = "/api"

async function fetchDataAndPlot(url) {
    try {
        displayLoader(true);
        let response = await axios.get(url);
        let data = response.data;

        // Handle no data scenario
        if (!data || data?.data?.length === 0) {
			console.log("No data found")
            document.getElementById("noDataAlert").style.display = "block";
            return;
        } else {
            document.getElementById("noDataAlert").style.display = "none";
        }

        plotData(data);
    } catch (error) {
        console.error("There was an error fetching or plotting the data:", error);
    } finally {
        displayLoader(false);
    }
}

function displayLoader(show) {
    document.getElementById('loader').style.display = show ? 'block' : 'none';
}

async function plotData(data) {

	if (typeof data === "string") {
		data = JSON.parse(data);
	}

    const { data: rainfallData, statistics, value_counts } = data;

    const times = extractAndFormatDates(rainfallData); // Extract and format times for plotting

    const rainfallAmounts = rainfallData.map(entry => entry.RG_A);

	displayValueCountsBarChart(value_counts);
    displayStatistics(statistics);

    drawChart(times, rainfallAmounts);
}

function extractAndFormatDates(rainfallData) {
    rainfallData.sort((a, b) => new Date(a.time) - new Date(b.time));

    const times = rainfallData.map(entry => format(new Date(entry.time), "yyyy-MM-dd'T'HH:mm:ss"));

    const startTime = format(new Date(times[0]), "EEE, d MMMM, yyyy h:mm a");
    const endTime = format(new Date(times[times.length - 1]), "EEE, d MMMM, yyyy h:mm a");

    document.getElementById('fromDate').textContent = startTime;
    document.getElementById('toDate').textContent = endTime;

    return times;
}

function displayStatistics(statistics) {
    const {
        highest,
        lowest,
        mean,
        median,
        range,
        standard_deviation,
        total_count
    } = statistics;

    let statsHtml = `
        <li><span class="key">Mean:</span> <span class="value">${mean}</span></li>
        <li><span class="key">Median:</span> <span class="value">${median}</span></li>
        <li><span class="key">Standard Deviation:</span> <span class="value">${standard_deviation}</span></li>
        <li><span class="key">Range:</span> <span class="value">${range}</span></li>
        <li><span class="key">Lowest:</span> <span class="value">${lowest}</span></li>
        <li><span class="key">Highest:</span> <span class="value">${highest}</span></li>
    `;

	document.getElementById('totalCount').textContent = total_count;
    document.getElementById('statistics').innerHTML = statsHtml;
    setupRainfallSlider(lowest, highest);
}


function drawChart(times, rainfallAmounts) {
    const chartData = {
		labels: times,
		datasets: [{
			label: 'Rainfall (RG_A)',
			data: rainfallAmounts,
			borderColor: 'rgba(75, 192, 192, 1)',
			borderWidth: 1,
			fill: false
		}]
	};

	const chartOptions = {
		scales: {
			x: {
				type: 'time',
				time: {
					unit: 'day',
					stepSize: 14,
					displayFormats: {
						day: 'MMM d, yyyy'
					}
				},
				title: {
					text: 'Dates',
					display: true,
					font: {
						size: 16,
						weight: 'bold'
					}
				}
			},
			y: {
				ticks: {
					stepSize: 0.5
				},
				title: {
					text: 'Rainfall (RG_A)',
					display: true,
					font: {
						size: 16,
						weight: 'bold'
					}
				}
			}
		},
		maintainAspectRatio: true,
		plugins: {
			tooltip: {
				callbacks: {
					label: function(context) {
						return `Rainfall is ${context.parsed.y} on ${format(context.parsed.x, "EEEE, do MMMM, yyyy 'at' ha")}`;
					}
				}
			},
			zoom: {
				zoom: {
					wheel: {
						enabled: true,
					},
					pinch: {
						enabled: true
					},
					mode: 'xy'
				},
				pan: {
					enabled: true,
					mode: 'xy'
				}
			}
		}
	};

	// Check if a chart instance already exists. If so, destroy it.
	if (rainfallChart) {
		rainfallChart.destroy();
	}

	// Create the chart
	const ctx = document.getElementById('rainfallChart').getContext('2d');
	rainfallChart = new Chart(ctx, {
		type: 'line',
		data: chartData,
		options: chartOptions
	});
}

function displayValueCountsBarChart(valueCounts) {
    const ctx = document.getElementById('valueCountsChart').getContext('2d');
    
    const labels = Object.keys(valueCounts);
    const data = Object.values(valueCounts);

	// Generate random colors for each bar
    const backgroundColors = labels.map(() => getRandomColor());
    const borderColors = backgroundColors.map(color => color.replace('0.7', '1')); // make border colors more opaque

	const chartData = {
		labels: labels,
		datasets: [{
			label: 'Frequency of Rainfall Data',
			data: data,
			backgroundColor: backgroundColors,
			borderColor: borderColors,
			borderWidth: 1
		}]
	};

	const chartOptions = {
		scales: {
			y: {
				type: 'logarithmic',
				beginAtZero: true,
				title: {
					display: true,
					text: 'Frequency',
					font: {
						size: 16,
						weight: 'bold'
					}
				}
			},
			x: {
				title: {
					display: true,
					text: 'Rainfall (RG_A)',
					font: {
						size: 16,
						weight: 'bold'
					}
				}
			}
		},
		plugins: {
			legend: {
				display: true,
				position: 'top',
			},
		}
	};

	// Check if a chart instance already exists. If so, destroy it.
	if (valueCountsChart) {
		valueCountsChart.destroy();
	}

	// Create the chart
	valueCountsChart = new Chart(ctx, {
		type: 'bar',
		data: chartData,
		options: chartOptions
	});
}

function getRandomColor() {
    const r = Math.floor(Math.random() * 256);
    const g = Math.floor(Math.random() * 256);
    const b = Math.floor(Math.random() * 256);
    return `rgba(${r}, ${g}, ${b}, 0.7)`;
}

async function initMap() {
    map = L.map('map').setView([52.4862, -1.8904], 14);  // Coordinates for central Birmingham

    // Set up the tiles for the map
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
    }).addTo(map);

	var materialIcon = L.divIcon({
		className: 'material-icons', 
		html: 'place', 
		iconSize: [25, 25], 
		iconAnchor: [12, 25]  // Center the icon over the marker's geographical location
	});

    // Add a marker for central Birmingham
    marker = L.marker([52.4862, -1.8904], {icon: materialIcon})
		.addTo(map)
        .bindPopup("Central Birmingham")
}

function setupRainfallSlider(min, max) {
    const slider = document.getElementById('rainfall-slider');

	// Check if slider is already initialized, if so, destroy it
    if (slider.noUiSlider) {
        slider.noUiSlider.destroy();
    }

    noUiSlider.create(slider, {
        start: [min, max],
        connect: true,
        range: {
            'min': min,
            'max': max
        }
    });

    slider.noUiSlider.on('update', function (values) {
        document.getElementById('rainfall-slider-value').textContent = `Rainfall Range: ${parseFloat(values[0]).toFixed(2)} to ${parseFloat(values[1]).toFixed(2)}`;
    });
}

// Call the functions on page load
document.addEventListener('DOMContentLoaded', async (event) => {
	await initMap();
    await fetchDataAndPlot(`${baseURL}/data`);
	
	flatpickr("#startDate", {
		enableTime: true,
		dateFormat: "Y-m-d H:i",
	});
	
	flatpickr("#endDate", {
		enableTime: true,
		dateFormat: "Y-m-d H:i",
	});
});

document.getElementById("filterData").addEventListener("click", async (event) => {
	event.preventDefault(); // Prevent the form from submitting

    const startDate = document.getElementById("startDate").value;
    const endDate = document.getElementById("endDate").value;
    const rainfallRange = document.getElementById('rainfall-slider').noUiSlider.get();
	const minRainfall = rainfallRange[0];
	const maxRainfall = rainfallRange[1];

    let queryParams = [];
    if (startDate) queryParams.push(`startDate=${startDate}`);
    if (endDate) queryParams.push(`endDate=${endDate}`);
    if (minRainfall) queryParams.push(`minRainfall=${minRainfall}`);
    if (maxRainfall) queryParams.push(`maxRainfall=${maxRainfall}`);
	if (minRainfall && maxRainfall && minRainfall === maxRainfall) {
		// delete minRainfall and maxRainfall if they are the same
		queryParams = queryParams.filter(param => !param.includes('minRainfall') && !param.includes('maxRainfall'));

		// Add specificRainfall query param instead
		queryParams.push(`specificRainfall=${minRainfall}`);
	}

    const url = `${baseURL}/data?${queryParams.join("&")}`;
    await fetchDataAndPlot(url);
});

document.getElementById("clearFilters").addEventListener("click", async (event) => {
	event.preventDefault();

	flatpickr("#startDate").clear();
	flatpickr("#endDate").clear();
	document.getElementById('rainfall-slider').noUiSlider.reset();
    
    // Hide the no data alert if it's showing
    document.getElementById("noDataAlert").style.display = "none";
    
    await fetchDataAndPlot(`${baseURL}/data`);
});
