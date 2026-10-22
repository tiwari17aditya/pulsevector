import os
import requests
import dotenv

dotenv.load_dotenv()
token = os.getenv("GITHUB_TOKEN")
headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"} if token else {}
repo = "tiwari17aditya/pulsevector"

r = requests.get(f"https://api.github.com/repos/{repo}/actions/runs?per_page=100", headers=headers)
data = r.json()
runs = data.get("workflow_runs", [])
by_name = {}
for run in runs:
    name = run.get("name", "Unknown")
    by_name.setdefault(name, []).append(run)

for name, r_list in by_name.items():
    latest = r_list[0]
    failures = [x for x in r_list if x.get("conclusion") == "failure"]
    print(f"Workflow: {name}")
    print(f"  Latest: ID={latest.get('id')} status={latest.get('status')} conclusion={latest.get('conclusion')} date={latest.get('created_at')}")
    print(f"  Count: {len(r_list)}, Failures: {len(failures)}")
    if failures:
        for f in failures[:2]:
            print(f"    Failed ID: {f.get('id')} on {f.get('created_at')}")
            j_resp = requests.get(f.get('jobs_url'), headers=headers)
            if j_resp.status_code == 200:
                for job in j_resp.json().get('jobs', []):
                    print(f"      Job: {job.get('name')} -> {job.get('conclusion')}")
                    for step in job.get('steps', []):
                        if step.get('conclusion') == 'failure':
                            print(f"        Step FAILED: {step.get('name')}")
            else:
                print(f"      Failed to get jobs: {j_resp.status_code} {j_resp.text}")
