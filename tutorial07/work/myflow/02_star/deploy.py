from prefect import flow

if __name__ == "__main__":
    flow.from_source(
        source="https://github.com/wasit7/prefect_demo.git",
        entrypoint="02_star/flow.py:show_stars",
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