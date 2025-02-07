import requests
import time

host = 'https://fetchfox.ai'
api_key = 'ff_be6upmlf8ylv390dy6rowccjxssaywo7t6542cks'

workflow = {
  "steps": [
    {
      "name": "const",
      "args": {
        "items": [
          {
            "url": "https://earthquake.usgs.gov/earthquakes/map/?extent=-89.71968,-79.80469&extent=89.71968,479.88281"
          }
        ],
        "maxPages": 1
      }
    },
    {
      "name": "extract",
      "args": {
        "questions": {
          "magnitude": "What is the magnitude of this earthquake?",
          "location": "What is the location of this earthquake?",
          "time": "What is the time of this earthquake?"
        },
        "single": True,
        "maxPages": 1
      }
    }
  ],
  "options": {
    "limit": 5
  }
}

# Create the workflow
print("Creating workflow...")
headers = {
    'Content-Type': 'application/json',
    'Authorization': f'Bearer: {api_key}'
}

workflow_resp = requests.post(f"{host}/api/v2/workflows", headers=headers, json=workflow)
workflow_data = workflow_resp.json()
workflow_id = workflow_data['id']

print(f"Running workflow: {workflow_id}")

# Run the workflow
run_resp = requests.post(f"{host}/api/v2/workflows/{workflow_id}/run", headers=headers, json={})
run_data = run_resp.json()
job_id = run_data['jobId']

print(f"Started job: {job_id}")

# Poll for job status
results = None
while True:
    time.sleep(5)
    print(f"Polling job: {job_id}")
    job_resp = requests.get(f"{host}/api/v2/jobs/{job_id}", headers=headers)
    job_data = job_resp.json()
    results = job_data.get('results')
    if job_data.get('done'):
        break
    print(f"Got {len(results.get('items', []))} results so far...")

print("Final results:")
print(results['items'])
