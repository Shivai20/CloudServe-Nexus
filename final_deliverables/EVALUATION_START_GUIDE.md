# CloudServe Final Evaluation Start Guide

Welcome to the final evaluation of the CloudServe FDE Capstone! This guide will walk you through spinning up the entire end-to-end support pipeline, visualizing the data, and testing the system.

## 1. Python Environment Setup
We noticed you have multiple Python versions installed (`Python 3.10` and `Python 3.12`). To ensure no `ModuleNotFoundError` issues occur, please explicitly install the dependencies into the exact environment you are using to run Uvicorn.

Run the following command in your terminal:
```bash
python -m pip install -r requirements.txt
python -m pip install prometheus_client sentence-transformers requests
```

## 2. Start the FastAPI Support Pipeline
Start the central nervous system of the project. This will initialize the deterministic routing engine and the `all-MiniLM-L6-v2` embeddings.

```bash
uvicorn src.api:app --reload
```
*Wait for the terminal to display `Application startup complete.`*

## 3. Start the Monitoring Stack (Prometheus & Grafana)
We have fully implemented Requirement #08. Spin up the monitoring suite using Docker Compose:

1. Ensure Docker Desktop is running.
2. Open a new terminal in the `final_deliverables` folder.
3. Run:
```bash
docker-compose up -d
```
* **Prometheus** is now scraping metrics at `http://localhost:9090`
* **Grafana** is now available at `http://localhost:3000` (Default login: `admin` / `admin`)

## 4. Open the Live Trace Visualizer
We built a custom live dashboard so you can visualize exactly what the pipeline is doing under the hood!
1. Go to your file explorer and open the `final_deliverables` folder.
2. Double-click **`trace_dashboard.html`** to open it in your browser.
3. Keep this window open side-by-side with your API!

## 5. Test the Pipeline
Now, let's fire some tickets into the system!

1. Open the Swagger UI: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
2. Expand the `POST /tickets` endpoint and click **Try it out**.
3. Paste the following `TEST-200` payload and click **Execute**:

```json
{
  "ticket_id": "TEST-200",
  "channel": "email",
  "subject": "Forgot password",
  "body": "How do I reset my account password? I am completely locked out of my account.",
  "customer_tier": "Standard"
}
```

### What to watch for:
* **The Trace Dashboard:** You will instantly see the ticket appear. You can see the classification intent (`authentication_failure`), the exact documentation chunks retrieved, the guardrail passes, and the final routing decision!
* **Groq API Console:** You will see the API counter tick up as the `openai/gpt-oss-20b` model generates the response.
* **Grafana/Prometheus:** You will see the `cloudserve_tickets_processed_total` and `cloudserve_tickets_autoresponded_total` metrics increment!

## 6. Fault Tolerance Test (Graceful Degradation)
To test Requirement A11 (Resilient Fault Tolerance):
1. Open your `.env` file and temporarily change your `GROQ_API_KEY` to an invalid string like `"broken_key"`.
2. Fire `TEST-200` again.
3. Watch the Trace Dashboard: The system will effortlessly catch the API failure and **escalate** the ticket to a human, leaving a precise audit log instead of crashing!
