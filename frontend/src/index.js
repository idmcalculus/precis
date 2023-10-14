import 'bootstrap';
import Chart from 'chart.js/auto';
import 'chartjs-adapter-date-fns';
import { formatISO } from 'date-fns';
import axios from 'axios';
import './assets/styles.scss';

async function fetchDataAndPlot() {
    // Fetch the data from our Flask backend
    let response = await axios.get('http://127.0.0.1:5000/data');
    let data = response.data;

	console.log(data.slice(0, 5));

    // Extract times and rainfall amounts for plotting
	const times = data.map(entry => {
		const dateString = entry.time.replace(/^[a-z]+, /i, ''); // Remove the day name from the date string
		let [day, month, year, hour, minute, second] = dateString.split(/[\s:]/); // Split the date string into its components
		let monthNumber = new Date(`${month} 1, 1970`).getMonth() + 1; // Get the month number from the month name
		let date = new Date(year, monthNumber - 1, day, hour, minute, second); // Create a Date object
		return formatISO(date); // Format the date to ISO string
	});

    let rainfallAmounts = data.map(entry => entry.RG_A);

    // Define the chart data and configuration
    var chartData = {
        labels: times,
        datasets: [{
            label: 'Rainfall (RG_A)',
            data: rainfallAmounts,
            borderColor: 'rgba(75, 192, 192, 1)',
            borderWidth: 1,
            fill: false
        }]
    };

    var chartOptions = {
		scales: {
			x: {
				type: 'time',
				time: {
					unit: 'day',  // Use day as the smallest unit
					stepSize: 14,  // Display every 14th day, i.e., fortnightly
					displayFormats: {
						day: 'MMM d, yyyy'  // Format to show month, day, and year
					}
				},
				title: {
					text: 'Time',
					display: true
				}
			},
			y: {
				ticks: {
					stepSize: 0.5  // Set step size to 0.5 for y-axis
				},
				title: {
					text: 'Rainfall (RG_A)',
					display: true
				}
			}
		},
		maintainAspectRatio: false,
	};	

    // Create the chart
    var ctx = document.getElementById('rainfallChart').getContext('2d');
    var rainfallChart = new Chart(ctx, {
        type: 'line',
        data: chartData,
        options: chartOptions
    });
}

// Call the function on page load
document.addEventListener('DOMContentLoaded', (event) => {
    fetchDataAndPlot();
});
