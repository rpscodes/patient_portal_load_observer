from flask import Flask, jsonify, render_template_string
import asyncio
import aiohttp

app = Flask(__name__)

# Config
TOTAL_REQUESTS = 100
CONCURRENCY = 10
PAYMENT_PROCESSOR_URL = "http://payment-processor.aws.svc.cluster.local:8080/api/pay"

results = {"processed-at-azure": 0, "processed-at-datacentre": 0}

@app.route('/')
def index():
    return render_template_string('''
    <html>
    <head>
        <title>Payment Processor Load Test</title>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    </head>
    <body>
        <h2>Load Test Results</h2>
        <button onclick="runTest()">Start Test</button>
        <canvas id="resultsChart" width="400" height="200"></canvas>
        <script>
        async function runTest() {
            await fetch('/run');
            const res = await fetch('/results');
            const data = await res.json();
            const ctx = document.getElementById('resultsChart').getContext('2d');
            new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: ['Azure', 'Datacentre'],
                    datasets: [{
                        label: '# of Responses',
                        data: [data["processed-at-azure"], data["processed-at-datacentre"]],
                    }]
                }
            });
        }
        </script>
    </body>
    </html>
    ''')

@app.route('/run')
async def run_test():
    global results
    results = {"processed-at-azure": 0, "processed-at-datacentre": 0}

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