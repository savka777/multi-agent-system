# Production Deployment Guide

## Architecture Overview

```
┌──────────┐      ┌──────────────┐      ┌───────────┐      ┌────────────┐
│  Client  │─────▶│  FastAPI API │─────▶│   Redis   │◀────▶│ RQ Workers │
│          │      │  (main_redis)│      │   Queue   │      │ (1-N nodes)│
└──────────┘      └──────────────┘      └───────────┘      └────────────┘
    │                    │                                         │
    │                    │                                         │
    └─── Poll status ────┘                                         │
                                                                   │
                                    ┌─────────────────────────────┘
                                    │
                                    ▼
                            ┌──────────────────┐
                            │ Claude Agent SDK │
                            │  Multi-Agent     │
                            │  Due Diligence   │
                            └──────────────────┘
```

## Why This Pattern Is Production-Ready

### ✅ Advantages

1. **Handles Long-Running Tasks**
   - Due diligence can take 2-10 minutes
   - No HTTP timeout issues
   - Client gets immediate response with job_id

2. **Scalability**
   - Add more workers to handle more concurrent jobs
   - Workers can be on different machines
   - Redis handles job distribution

3. **Reliability**
   - Jobs survive worker crashes (retry)
   - Results persist in Redis (24h default)
   - Failed jobs stored for debugging

4. **User Experience**
   - Non-blocking API calls
   - Client can poll for updates
   - Show progress to users

### ⚠️ Considerations

1. **Polling vs Webhooks**
   - Current: Client polls `/analyze/status/{job_id}`
   - Better: Add webhooks to notify on completion
   
2. **Job Persistence**
   - Current: Results expire after 24h
   - Consider: Store final reports in database

3. **Rate Limiting**
   - Add rate limiting per user/API key
   - Prevent queue flooding

## Production Improvements Made

### 1. Request Validation
```python
class AnalysisRequest(BaseModel):
    startup_name: str = Field(..., min_length=1, max_length=200)
    startup_description: str = Field(..., min_length=10, max_length=5000)
    funding_stage: Optional[str] = None
```

### 2. Error Handling
- Redis connection errors → 503 Service Unavailable
- Job not found → 404 Not Found
- Invalid requests → 422 Unprocessable Entity

### 3. Configuration from Environment
```bash
export REDIS_HOST=localhost
export REDIS_PORT=6379
export REDIS_PASSWORD=secret
export JOB_TIMEOUT=600
export ALLOWED_ORIGINS=https://yourdomain.com
```

### 4. Health Checks
```bash
curl http://localhost:8000/health
# {"status": "healthy", "redis": "connected", "queue_size": 5}
```

### 5. Job Management
- Cancel jobs: `DELETE /analyze/{job_id}`
- List recent jobs: `GET /analyze/jobs/recent`
- Job timeouts (10 min default)
- Result TTL (24h default)

### 6. Logging
- Structured logging
- Request tracing
- Error tracking

## Deployment Options

### Option 1: Docker Compose (Recommended)

See `docker-compose.yml` for full setup.

```bash
docker-compose up -d
```

### Option 2: Separate Services

**Terminal 1: Redis**
```bash
redis-server
```

**Terminal 2: API Server**
```bash
export REDIS_HOST=localhost
uvicorn src.main_redis:app --host 0.0.0.0 --port 8000
```

**Terminal 3: Worker(s)**
```bash
export OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES  # macOS only
export REDIS_HOST=localhost
rq worker agents
```

**Terminal 4: More Workers (Optional)**
```bash
rq worker agents  # Add more as needed
```

### Option 3: Kubernetes

See `k8s/` directory for manifests (to be created).

## Scaling Strategy

### Vertical Scaling (Single Machine)
```bash
# Run multiple workers
for i in {1..4}; do
  rq worker agents &
done
```

### Horizontal Scaling (Multiple Machines)
```
Machine 1: FastAPI (API server)
Machine 2: Redis (queue + cache)
Machine 3-5: RQ Workers (3 machines × 4 workers = 12 concurrent jobs)
```

## Monitoring

### Key Metrics to Track

1. **Queue Length**: `len(agent_tasks)`
2. **Job Completion Rate**: successful/failed jobs
3. **Average Job Duration**: time from enqueue to complete
4. **Worker Utilization**: active workers / total workers
5. **Error Rate**: failed jobs / total jobs

### Tools

- **Redis Monitoring**: Redis Commander, RedisInsight
- **RQ Monitoring**: RQ Dashboard (`pip install rq-dashboard`)
- **Application Monitoring**: DataDog, Sentry, New Relic
- **Logging**: ELK Stack, Splunk, CloudWatch

### RQ Dashboard (Built-in)

```bash
pip install rq-dashboard
rq-dashboard
# Open http://localhost:9181
```

## Production Checklist

- [ ] Environment variables configured
- [ ] Redis password set (not using default)
- [ ] CORS origins restricted (not using `*`)
- [ ] Rate limiting implemented
- [ ] Monitoring/alerting set up
- [ ] Logs aggregated (ELK/CloudWatch)
- [ ] Database for long-term result storage
- [ ] Webhook notifications (optional)
- [ ] Authentication/API keys
- [ ] CI/CD pipeline
- [ ] Load testing completed

## Alternative: Direct API Approach

If you want to avoid the fork issue entirely, you can use direct Anthropic API calls:

**Pros:**
- No subprocess, no fork issues
- More control over API calls
- Simpler deployment

**Cons:**
- More code to write (tool handling)
- Lose Agent SDK features
- Need to implement tool execution manually

**When to switch:**
- If fork issues persist on your deployment platform
- If you need fine-grained control over API calls
- If SDK adds too much overhead

## Alternative: Celery

Celery is more feature-rich than RQ:

**Pros:**
- Better for complex workflows
- Built-in retry logic
- Periodic tasks (cron-like)
- Multiple queue backends

**Cons:**
- More complex setup
- Heavier dependency

**When to use:**
- Need advanced scheduling
- Multiple queue types
- Larger production systems

## Linux vs macOS

### Development (macOS)
```bash
export OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES
./start_worker.sh
```

### Production (Linux - Recommended)
```bash
# No special env var needed!
rq worker agents
```

**Linux doesn't have the Objective-C fork issue**, so your production deployment will be simpler.

## Cost Optimization

### API Costs (Claude)
- Average job: ~50K input + ~10K output tokens
- Cost per job: ~$0.50-$2.00 (depending on model)
- 1000 analyses/month: ~$500-$2000

### Infrastructure Costs
- Redis: $10-50/month (managed)
- API server: $20-100/month (2-4 CPU)
- Workers: $50-200/month (scale as needed)

### Total: ~$80-$350/month for moderate usage

## Security Considerations

1. **API Authentication**: Add API keys or OAuth
2. **Rate Limiting**: Prevent abuse
3. **Input Validation**: Already implemented ✅
4. **Redis Password**: Set in production
5. **Network Security**: Use VPC, private networks
6. **Secrets Management**: Use AWS Secrets Manager, Vault

## Conclusion

Your architecture is **solid for production**! The key improvements:

1. ✅ Async job processing (core pattern)
2. ✅ Error handling
3. ✅ Configuration management
4. ✅ Health checks
5. ✅ Job management
6. ✅ Logging

**Next Steps:**
1. Add authentication
2. Set up monitoring
3. Add webhooks (optional)
4. Deploy to Linux (avoids macOS issues)
5. Load test with realistic workload

You've chosen the right pattern for your use case! 🚀
