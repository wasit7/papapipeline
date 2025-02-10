from prefect import flow
from pathlib import Path

source='/home/jovyan/work/mykedroproject/notebooks'
entrypoint = f"flow.py:my_flow"
print(f'entrypoint:{entrypoint}, source:{source}')

if __name__ == "__main__":
    deployment = flow.from_source(
        source=source,
        entrypoint=entrypoint
    )
    # Deploy with a cron schedule. In this example, the flow is scheduled to run every day at midnight.
    deployment.deploy(
        name=f"kedro-deployment",
        work_pool_name="default-agent-pool",
        parameters={"pipeline_name": "__default__", "env": "base"},
        version="1.0",
        cron="* * * * *"
    )
    print(f"Deployment [kedro-deployment] registered with cron schedule.")