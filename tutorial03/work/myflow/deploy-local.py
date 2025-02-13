from prefect import flow
from pathlib import Path

source=str(Path.cwd())
entrypoint = f"flow.py:hello_flow"
print(f'entrypoint:{entrypoint}, source:{source}')

if __name__ == "__main__":
    flow.from_source(
        source=source,
        entrypoint=entrypoint,
    ).deploy(
        name="local_deployment",
        parameters={
            'name': 'DSI: Big Data Infrastructure'
        },
        work_pool_name="default-agent-pool",
        cron="* * * * *",  # Run every munite
    )