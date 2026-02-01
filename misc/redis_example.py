from fastapi import FastAPI
from pydantic import BaseModel
from redis import Redis
from rq import Queue
from rq.job import Job

app = FastAPI()

redis_conn = Redis(host='localhost', port=6379)

# name of worker: task queue
# uv run rq worker "task"
task_queue = Queue('task', connection=redis_conn)

# Example of a job:
def do_job(lowest : int, highest: int):
    print("doing job..... ")
    for i in range(lowest, highest):
        print(i)
    
    return highest # will return in Job.results = highest
    
@app.get('/status')
def status():
    return{
        "success": True,
        "message": "OK"
    }

class Task(BaseModel):
    lowest:int
    highest: int

@app.post('/task/async')
async def create_task(task: Task):
    # pass the job in here
    job_instance = task_queue.enqueue(do_job,task.lowest, task.highest)

    return {
        'success': True, 
        'message': "Job queued, callback at specified URL: /status/{job id}",
        'job_id': job_instance.id
    }

@app.get("/status/{job_id}")
def get_job_status(job_id : str):
    job = Job.fetch(job_id, connection=redis_conn)
    return{
        'job_id': job_id,
        'status': job.get_status(),
        'result': job.result
    }