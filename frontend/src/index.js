import axios from 'axios';
import L from 'leaflet';
import noUiSlider from 'nouislider';
import flatpickr from "flatpickr";
import Plotly from 'plotly.js-dist';

import 'bootstrap';
import 'nouislider/dist/nouislider.css';
import 'leaflet/dist/leaflet.css';
import 'flatpickr/dist/flatpickr.min.css';
import './assets/styles.scss';

let marker;
let map;
const baseURL = "/api"

async function fetchDataAndPlot(url) {
    try {
        displayLoader(true);
        let response = await axios.get(url);
        let data = response.data;

        // Handle no data scenario
        if (!data || !data.scatter_chart || !data.bar_chart) {
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
    const { scatter_chart, bar_chart, statistics } = data;

    displayRainfallChart(JSON.parse(scatter_chart));
    displayValueCountsBarChart(JSON.parse(bar_chart));
    displayStatistics(statistics);
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

function displayRainfallChart(figure) {
	try {
		Plotly.newPlot('rainfallChart', figure.data, figure.layout);
	} catch (error) {
		console.error("Error displaying rainfall chart:", error);
	}
}

function displayValueCountsBarChart(figure) {
	try {
		Plotly.newPlot('valueCountsChart', figure.data, figure.layout);
	} catch (error) {
		console.error("Error displaying value counts chart:", error);
	}
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

    // Check if slider is already initialized, if so, update its range
    if (slider.noUiSlider) {
        slider.noUiSlider.updateOptions({
            range: {
                'min': min,
                'max': max
            }
        });
    } else {
        noUiSlider.create(slider, {
            start: [min, max],
            connect: true,
            range: {
                'min': min,
                'max': max
            }
        });
    }

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
    const minRainfall = parseFloat(rainfallRange[0]);
    const maxRainfall = parseFloat(rainfallRange[1]);

    let queryParams = [];
    if (startDate) queryParams.push(`startDate=${startDate}`);
    if (endDate) queryParams.push(`endDate=${endDate}`);
    if (minRainfall !== undefined) queryParams.push(`minRainfall=${minRainfall}`);
    if (maxRainfall !== undefined) queryParams.push(`maxRainfall=${maxRainfall}`);
    if (minRainfall !== undefined && maxRainfall !== undefined && minRainfall === maxRainfall) {
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

	// Reset the slider to its initial state
    const slider = document.getElementById('rainfall-slider');
    if (slider.noUiSlider) {
        slider.noUiSlider.reset();
    }
    
    // Hide the no data alert if it's showing
    document.getElementById("noDataAlert").style.display = "none";
    
    await fetchDataAndPlot(`${baseURL}/data`);
});
