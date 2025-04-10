from prefect import flow
from pathlib import Path

source=str(Path.cwd())
entrypoint = f"flow.py:show_stars" #python file: function
print(f'entrypoint:{entrypoint}, source:{source}')

if __name__ == "__main__":
    flow.from_source(
        source=source,
        entrypoint=entrypoint,
    ).deploy(
        name="show_stars_deployment",
        parameters={
            "github_repos": [
                "wasit7/papapipeline",
                "wasit7/DjangoCrafter",
                "PrefectHQ/prefect",
                "huggingface/transformers"
            ]
        },
        work_pool_name="default-agent-pool",
        cron="*/5 * * * *",  # Run every 5 munites
    )