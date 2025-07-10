from flask import Flask, jsonify, render_template_string
import asyncio
import aiohttp

app = Flask(__name__)

# Config
TOTAL_REQUESTS = 100
CONCURRENCY = 10
PAYMENT_PROCESSOR_URL = "http://payment-processor.aws.svc.cluster.local:8080/api/pay"

results = {"payment-processed-at-azure": 0, "processed-at-datacentre": 0}

@app.route('/')
def index():
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Payment Processor Load Test</title>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #EE0000 0%, #A30000 100%);
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
                padding: 20px;
            }
            
            .container {
                background: white;
                border-radius: 20px;
                box-shadow: 0 20px 40px rgba(238, 0, 0, 0.15);
                padding: 40px;
                max-width: 800px;
                width: 100%;
                text-align: center;
            }
            
            h1 {
                color: #333;
                font-size: 2.5em;
                margin-bottom: 10px;
                font-weight: 300;
            }
            
            .subtitle {
                color: #666;
                font-size: 1.1em;
                margin-bottom: 40px;
                font-weight: 400;
            }
            
            .test-controls {
                margin-bottom: 40px;
            }
            
            .test-button {
                background: linear-gradient(45deg, #000000, #A30000);
                color: white;
                border: none;
                padding: 15px 40px;
                font-size: 1.1em;
                border-radius: 50px;
                cursor: pointer;
                transition: all 0.3s ease;
                font-weight: 600;
                letter-spacing: 1px;
                text-transform: uppercase;
                box-shadow: 0 5px 15px rgba(0, 0, 0, 0.3);
            }
            
            .test-button:hover {
                transform: translateY(-2px);
                box-shadow: 0 8px 25px rgba(238, 0, 0, 0.4);
            }
            
            .test-button:active {
                transform: translateY(0);
            }
            
            .test-button:disabled {
                opacity: 0.6;
                cursor: not-allowed;
                transform: none;
            }
            
            .loading-spinner {
                display: none;
                margin: 20px 0;
            }
            
            .spinner {
                width: 40px;
                height: 40px;
                border: 4px solid #f3f3f3;
                border-top: 4px solid #EE0000;
                border-radius: 50%;
                animation: spin 1s linear infinite;
                margin: 0 auto;
            }
            
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
            
            .status-message {
                margin: 20px 0;
                padding: 15px;
                border-radius: 10px;
                font-weight: 500;
                display: none;
            }
            
            .status-success {
                background: #d4edda;
                color: #155724;
                border: 1px solid #c3e6cb;
            }
            
            .status-error {
                background: #f8d7da;
                color: #721c24;
                border: 1px solid #f5c6cb;
            }
            
            .results-section {
                margin-top: 40px;
                padding: 30px;
                background: #f8f9fa;
                border-radius: 15px;
                display: none;
            }
            
            .results-title {
                color: #333;
                font-size: 1.5em;
                margin-bottom: 20px;
                font-weight: 600;
            }
            
            .chart-container {
                position: relative;
                height: 400px;
                margin: 20px 0;
            }
            
            .stats-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 20px;
                margin-top: 20px;
            }
            
            .stat-card {
                background: white;
                padding: 20px;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }
            
            .stat-value {
                font-size: 2em;
                font-weight: bold;
                color: #EE0000;
            }
            
            .stat-label {
                color: #666;
                font-size: 0.9em;
                margin-top: 5px;
            }
            
            @media (max-width: 768px) {
                .container {
                    padding: 20px;
                }
                
                h1 {
                    font-size: 2em;
                }
                
                .test-button {
                    padding: 12px 30px;
                    font-size: 1em;
                }
                
                .chart-container {
                    height: 300px;
                }
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Payment Processor</h1>
            <p class="subtitle">Load Test Dashboard</p>
            
            <div class="test-controls">
                <button class="test-button" onclick="runTest()" id="testButton">
                    Start Load Test
                </button>
            </div>
            
            <div class="loading-spinner" id="loadingSpinner">
                <div class="spinner"></div>
                <p>Running load test...</p>
            </div>
            
            <div class="status-message" id="statusMessage"></div>
            
            <div class="results-section" id="resultsSection">
                <h2 class="results-title">Test Results</h2>
                <div class="chart-container">
                    <canvas id="resultsChart"></canvas>
                </div>
                <div class="stats-grid" id="statsGrid"></div>
            </div>
        </div>
        
        <script>
            let chart = null;
            
            async function runTest() {
                const button = document.getElementById('testButton');
                const spinner = document.getElementById('loadingSpinner');
                const statusMessage = document.getElementById('statusMessage');
                const resultsSection = document.getElementById('resultsSection');
                
                // Reset UI
                button.disabled = true;
                button.textContent = 'Running Test...';
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
                    button.textContent = 'Start Load Test';
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
                            '#EE0000',
                            '#000000'
                        ],
                        borderColor: [
                            '#A30000',
                            '#333333'
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
        </script>
    </body>
    </html>
    ''')

@app.route('/run')
async def run_test():
    global results
    results = {"payment-processed-at-azure": 0, "processed-at-datacentre": 0}

    semaphore = asyncio.Semaphore(CONCURRENCY)

    async def call_service():
        async with semaphore:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(PAYMENT_PROCESSOR_URL) as resp:
                        text = await resp.text()
                        if text in results:
                            results[text] += 1
            except Exception as e:
                print(f"Error: {e}")

    await asyncio.gather(*(call_service() for _ in range(TOTAL_REQUESTS)))
    return jsonify({"status": "completed"})

@app.route('/results')
def get_results():
    return jsonify(results)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)