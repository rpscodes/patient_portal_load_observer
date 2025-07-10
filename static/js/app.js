let chart = null;

async function runTest() {
    const button = document.getElementById('testButton');
    const spinner = document.getElementById('loadingSpinner');
    const statusMessage = document.getElementById('statusMessage');
    const resultsSection = document.getElementById('resultsSection');
    
    // Reset UI
    button.disabled = true;
    button.querySelector('span').textContent = 'Running Test...';
    spinner.style.display = 'block';
    statusMessage.style.display = 'none';
    resultsSection.style.display = 'none';
    
    try {
        // Start the test
        await fetch('/run');
        
        // Get results
        const res = await fetch('/results');
        const data = await res.json();
        
        // Show success message
        showStatusMessage('Test completed successfully!', 'success');
        
        // Update chart
        updateChart(data);
        
        // Update stats
        updateStats(data);
        
        // Show results
        resultsSection.style.display = 'block';
        
    } catch (error) {
        showStatusMessage('Error running test: ' + error.message, 'error');
    } finally {
        // Reset button
        button.disabled = false;
        button.querySelector('span').textContent = 'Start Load Test';
        spinner.style.display = 'none';
    }
}

function showStatusMessage(message, type) {
    const statusMessage = document.getElementById('statusMessage');
    statusMessage.textContent = message;
    statusMessage.className = `status-message status-${type}`;
    statusMessage.style.display = 'block';
    
    // Auto-hide after 5 seconds
    setTimeout(() => {
        statusMessage.style.display = 'none';
    }, 5000);
}

function updateChart(data) {
    const ctx = document.getElementById('resultsChart').getContext('2d');
    
    // Destroy existing chart if it exists
    if (chart) {
        chart.destroy();
    }
    
    chart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['Azure Responses', 'Datacentre Responses'],
            datasets: [{
                data: [data["payment-processed-at-azure"], data["processed-at-datacentre"]],
                backgroundColor: [
                    '#3b82f6',
                    '#ef4444'
                ],
                borderColor: [
                    '#2563eb',
                    '#dc2626'
                ],
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        font: {
                            size: 14
                        },
                        padding: 20
                    }
                }
            },
            animation: {
                duration: 1000,
                easing: 'easeOutBounce'
            }
        }
    });
}

function updateStats(data) {
    const statsGrid = document.getElementById('statsGrid');
    const total = data["payment-processed-at-azure"] + data["processed-at-datacentre"];
    
    statsGrid.innerHTML = `
        <div class="stat-card">
            <div class="stat-value">${data["payment-processed-at-azure"]}</div>
            <div class="stat-label">Azure Responses</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">${data["processed-at-datacentre"]}</div>
            <div class="stat-label">Datacentre Responses</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">${total}</div>
            <div class="stat-label">Total Requests</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">${total > 0 ? ((data["payment-processed-at-azure"] / total * 100).toFixed(1) + '%') : '0%'}</div>
            <div class="stat-label">Azure Percentage</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">${total > 0 ? ((data["processed-at-datacentre"] / total * 100).toFixed(1) + '%') : '0%'}</div>
            <div class="stat-label">Datacentre Percentage</div>
        </div>
    `;
} 