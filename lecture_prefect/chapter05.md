# **Chapter 5: Building Pipelines with Prefect**

## **5.1 Introduction to Prefect Flows**

### 5.1.1 What is a Flow?
A **flow** is the primary abstraction in Prefect. It represents the **orchestrated steps** of your data pipeline. Each flow can have:
- One or more **tasks** (sub-steps) that perform discrete operations (e.g., data extraction, transformation, loading).  
- A definition of **dependencies** (i.e., which tasks must run before others).  
- Optional **parameters** for dynamic configuration.

In **Prefect 2/3**, flows are defined using the `@flow` **decorator** in Python:
```python
from prefect import flow

@flow
def my_flow():
    print("Running my first Prefect flow!")
```

### 5.1.2 Why Prefect?
- **Orchestration**: Built-in scheduling, retries, and logging.  
- **Observability**: Flow runs can be monitored via the Prefect UI.  
- **Scalability**: Multiple **workers** can handle parallel runs.  
- **Integration**: Flows can be deployed from local files, GitHub repos, object storage, etc.

---

## **5.2 Defining and Parameterizing Flows**

### 5.2.1 Simple Flow Example
```python
from prefect import flow

@flow
def hello_flow(name: str = "Prefect User"):
    print(f"Hello, {name}!")
```
This flow has a **parameter** `name`. If no argument is passed, it defaults to `"Prefect User"`.

### 5.2.2 Running a Flow Locally
You can run it directly like a Python function:
```bash
python hello_flow.py
# Output: "Hello, Prefect User!"
```
However, this **local run** does not utilize the Prefect server or worker. For full orchestration, you’ll **deploy** the flow so that it’s discoverable by the Prefect Worker.

### 5.2.3 Tasks and Subflows
While smaller flows can be a single function, bigger pipelines often break down into **tasks**:
```python
from prefect import flow, task

@task
def add(a, b):
    return a + b

@flow
def math_flow(x, y):
    result = add(x, y)
    print(f"Sum is {result}")
```
This approach allows:
- **Task-level parallelism**  
- **Retry policies** for specific tasks  
- **Caching** of task outputs  

---

## **5.3 Deploying Flows**

### 5.3.1 Modern Deployment Syntax
Prefect 2.x+ introduced a more explicit deployment approach. You can:
1. Use the **CLI** (`prefect deployment build/apply`)  
2. Or programmatically call `.deploy()` on the flow.

**Programmatic Example**:
```python
from prefect import flow

if __name__ == "__main__":
    flow.from_source(
        source="git@github.com:username/my_repo.git",
        entrypoint="path/to/hello_flow.py:hello_flow",
    ).deploy(
        name="hello-deployment",
        work_pool_name="default-agent-pool",
        parameters={"name": "Data Eng 101"},
        # Optionally add a schedule, e.g. cron="*/10 * * * *" for every 10 minutes
    )
```
Running:
```bash
python deploy.py
```
**registers** the deployment with the Prefect server. You can then see and trigger this deployment in the Prefect UI.

### 5.3.2 Work Pool Assignment
You specify `work_pool_name` so the Prefect server knows **which pool** to schedule runs against. Workers listening to that pool will pick up the flow runs.

### 5.3.3 Storing Code and Dependencies
- **Local**: Worker reads code from the local volume (shared if in Docker Compose).  
- **Git**: Worker clones from a Git repository—ideal for version-controlled flows.  
- **Custom Docker Images**: If your flow needs special libraries, build a custom image containing them (see Chapter 2’s Dockerfile tips).

---

## **5.4 Scheduling and Triggers**

### 5.4.1 Cron Schedules
Prefect supports **cron** syntax:
```python
# Every 5 minutes
cron="*/5 * * * *"
```
For every midnight:
```python
cron="0 0 * * *"
```

### 5.4.2 Interval Scheduling
Alternatively, you can schedule an **interval** (e.g., every hour) if you prefer:
```python
# Pseudocode for an hourly interval
interval_schedule = IntervalSchedule(interval=timedelta(hours=1))
```

### 5.4.3 Manual Triggers
You can also **trigger** a run on-demand via the UI or CLI:
```bash
prefect deployment run hello-deployment
```

---

## **5.5 Executing and Monitoring Flows**

### 5.5.1 Worker Execution
- Once the flow is scheduled or manually triggered, the **Prefect Worker** assigned to the relevant **Work Pool** fetches the run.  
- The worker sets up the code environment, executes tasks, and sends logs/states back to the server.

### 5.5.2 Viewing Runs in the UI
Check **http://localhost:4200** (or your configured server address) to see:
- **Flow Runs**: Active, scheduled, or completed.  
- **Logs**: Each task’s print statements and logs.  
- **Schedules**: Next planned execution times (if cron or interval is used).

### 5.5.3 CLI Monitoring
- **`prefect logs`**: Quick access to recent logs.  
- **`prefect deployment ls`**: Lists all registered deployments.  
- **`prefect flow-run ls`** (in some versions) or **`prefect blocks ls`** for advanced usage with blocks and other metadata.

---

## **5.6 Logging and Error Handling**

### 5.6.1 Built-In Logging
Simply use `print()` in a flow or task with the flow decorator argument:
```python
@flow(log_prints=True)
def my_flow():
    print("Hello logs!")
```
These prints appear in the **Prefect UI** logs. Or you can use the standard Python `logging` module.

### 5.6.2 Error Handling with Retries
You can **configure retries** for tasks:
```python
@task(retries=3, retry_delay_seconds=10)
def flaky_task():
    # Potentially failing code
    pass
```
If the code fails, Prefect automatically retries up to 3 times with a 10-second delay.

---

## **5.7 Best Practices**

1. **Modularize**: Keep flows small and focused. Combine multiple flows for complex pipelines.  
2. **Use Git**: Store flow definitions in a Git repo; version control ensures reproducibility.  
3. **Parameterize**: Pass dynamic variables (dates, file paths, etc.) to flows, avoiding hardcoded values.  
4. **Separate Dev/Prod**: Use different **Work Pools** or different schedules for development vs. production flows.  
5. **Monitor and Alert**: Check logs in the Prefect UI or integrate notifications (e.g., Slack, email) for failures.  
6. **Dockerize**: Build custom worker images with your required libraries for consistent environments across dev/stage/prod.

---

## **5.8 Summary**

In this chapter, you learned how to create, deploy, schedule, and monitor **Prefect flows**, culminating the knowledge from previous chapters:

1. **Linux & Git** (Chapter 1): Use Git to store and manage your flow definitions.  
2. **Docker & Docker Compose** (Chapter 2): Containerize your environment to run a Prefect server and workers in separate, orchestrated services.  
3. **Prefect Server** (Chapter 3): The central orchestrator that registers flows, stores metadata, and provides a UI.  
4. **Prefect Worker** (Chapter 4): Executes scheduled or triggered flows from a Work Pool, reporting logs and states back to the server.

By combining these concepts:
- You can define and test flows **locally**.  
- Deploy them to a **self-hosted** Prefect environment for scheduling, resource management, and monitoring.  
- Scale your workloads by **increasing worker replicas** or distributing tasks across multiple Docker containers.

**Congratulations!** You now have a solid foundation for building reliable, containerized, and orchestrated data pipelines using Prefect. Whether you’re running **ETL** processes, **machine learning** workflows, or complex event-driven tasks, Prefect provides the tools you need to manage them effectively and transparently.