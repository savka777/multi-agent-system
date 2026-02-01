# Quick Start Guide

Get the async due diligence API running in under 5 minutes!

## Prerequisites

- Python 3.11+
- Redis (or use Docker)
- Anthropic API key

## Option 1: Docker (Easiest - Recommended)

### 1. Set up environment

```bash
# Copy and edit environment file
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY
```

### 2. Start everything

```bash
docker-compose up -d
```

That's it! Services running:
- API: http://localhost:8000
- Redis: localhost:6379
- Workers: 2 instances
- Dashboard: http://localhost:9181

### 3. Test it

```bash
# Check health
curl http://localhost:8000/health

# Submit a job
python example_client.py
```

### 4. Monitor

- API docs: http://localhost:8000/docs
- Job dashboard: http://localhost:9181

---

## Option 2: Local Development (macOS)

### 1. Install dependencies

```bash
# Install uv (if not installed)
pip install uv

# Install dependencies
uv sync
```

### 2. Start Redis

```bash
# Terminal 1
redis-server
```

### 3. Start API server

```bash
# Terminal 2
export ANTHROPIC_API_KEY=sk-ant-...
uv run uvicorn src.main_redis:app --reload
```

### 4. Start worker

```bash
# Terminal 3
export ANTHROPIC_API_KEY=sk-ant-...
export OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES  # macOS only!
./start_worker.sh
```

### 5. Test it

```bash
# Terminal 4
python example_client.py
```

---

## Option 3: Linux Production

Same as Option 2, but **skip the `OBJC_DISABLE_INITIALIZE_FORK_SAFETY` env var** - you don't need it on Linux!

```bash
# Start workers (no special env var needed)
rq worker agents
```

---

## API Usage

### Submit Analysis

```bash
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "startup_name": "Stripe",
    "startup_description": "Payments infrastructure company",
    "funding_stage": "series-a"
  }'

# Response: {"success": true, "job_id": "abc123", ...}
```

### Check Status

```bash
curl http://localhost:8000/analyze/status/abc123

# Response when complete:
# {
#   "job_id": "abc123",
#   "status": "finished",
#   "result": { ... full due diligence report ... }
# }
```

### Cancel Job

```bash
curl -X DELETE http://localhost:8000/analyze/abc123
```

---

## Architecture

```
Client
  │
  └─▶ POST /analyze
       │
       ├─▶ Returns job_id immediately
       │
       └─▶ Job queued in Redis
            │
            └─▶ Worker picks up job
                 │
                 ├─▶ Runs 5-10 agents
                 ├─▶ Takes 2-10 minutes
                 └─▶ Saves result to Redis
                      │
                      └─▶ Client polls /analyze/status/{job_id}
```

---

## Scaling

### Add More Workers

**Docker:**
```yaml
# In docker-compose.yml, change:
deploy:
  replicas: 4  # Run 4 workers
```

**Local:**
```bash
# Start multiple workers
rq worker agents &  # Worker 1
rq worker agents &  # Worker 2
rq worker agents &  # Worker 3
```

---

## Monitoring

### RQ Dashboard (included)

```bash
# Already running at http://localhost:9181 with Docker
# Or start manually:
rq-dashboard --redis-url redis://localhost:6379
```

### Check Queue Status

```bash
curl http://localhost:8000/analyze/jobs/recent
```

---

## Troubleshooting

### "No module named 'src'"

Make sure you're in the project root:
```bash
cd /Users/sav/Desktop/multi-agent-system
```

### "Connection refused" to Redis

Start Redis:
```bash
redis-server
```

### macOS fork error (objc[...]: +[NSMutableString initialize])

Set environment variable:
```bash
export OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES
```

Or use the startup script:
```bash
./start_worker.sh
```

### Job stuck in "queued"

No workers running! Start at least one worker:
```bash
./start_worker.sh
```

### Job takes too long

Default timeout is 10 minutes. Increase it:
```bash
export JOB_TIMEOUT=1200  # 20 minutes
```

---

## Next Steps

1. **Add Authentication**: Secure your API with API keys
2. **Add Webhooks**: Notify clients when jobs complete
3. **Store Results**: Save reports to database for long-term storage
4. **Add Monitoring**: Integrate with DataDog, Sentry, etc.
5. **Deploy to Production**: Use Linux to avoid macOS fork issues

See [PRODUCTION.md](./PRODUCTION.md) for detailed production deployment guide.

---

## Questions?

- **How long do results stay in Redis?** 24 hours by default
- **Can I run multiple jobs at once?** Yes! Add more workers
- **What happens if a worker crashes?** Job will be retried
- **Can I cancel a running job?** Yes, use `DELETE /analyze/{job_id}`

Happy analyzing! 🚀
