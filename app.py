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
        <link href="https://fonts.googleapis.com/css2?family=Red+Hat+Display:wght@400;500;600;700;800&display=swap" rel="stylesheet">
        <link rel="stylesheet" href="{{ url_for('static', filename='css/style.css') }}">
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    </head>
    <body>
        <header class="header">
            <h1>Payment Processor Load Test</h1>
        </header>
        
        <main class="main-content">
            <div class="page-header">
                <h1>payment-processor</h1>
            </div>
            
            <div class="dashboard-grid" id="dashboardGrid">
                <div class="card">
                    <div class="card-header">
                        <h2>Load Test Control</h2>
                    </div>
                    <div class="card-body centered">
                        <div class="control-panel">
                            <button class="test-button" onclick="runTest()" id="testButton">
                                <span>Start Load Test</span>
                            </button>
                            
                            <div class="loading-spinner" id="loadingSpinner">
                                <div class="spinner"></div>
                                <p>Making 100 calls to payment processor...</p>
                            </div>
                            
                            <div class="status-message" id="statusMessage"></div>
                        </div>
                    </div>
                </div>
                
                <div class="card" id="resultsSection" style="display: none;">
                    <div class="card-header">
                        <h2>Traffic Distribution</h2>
                    </div>
                    <div class="card-body">
                        <div class="chart-container">
                            <canvas id="resultsChart"></canvas>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="stats-grid" id="statsGrid"></div>
        </main>
        
                <script src="{{ url_for('static', filename='js/app.js') }}"></script>
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