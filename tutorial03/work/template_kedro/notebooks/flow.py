from pathlib import Path
from typing import Dict, List, Union, Callable

from kedro.framework.hooks.manager import _create_hook_manager
from kedro.framework.project import pipelines
from kedro.framework.session import KedroSession
from kedro.framework.startup import bootstrap_project
from kedro.io import DataCatalog, MemoryDataset
from kedro.pipeline.node import Node
from kedro.runner import run_node

from prefect import flow, task, get_run_logger

@flow(name="my_flow", log_prints=True)
def my_flow(pipeline_name: str, env: str):
    logger = get_run_logger()
    # Determine the project root: if pyproject.toml is in the current directory, use it;
    # otherwise, use its parent directory.
    project_path = Path.cwd() if (Path.cwd() / "pyproject.toml").exists() else Path.cwd().parent
    logger.info("Project path: %s", project_path)

    metadata = bootstrap_project(project_path)
    logger.info("Project name: %s", metadata.project_name)

    logger.info("Initializing Kedro...")
    execution_config = kedro_init(
        pipeline_name=pipeline_name, project_path=project_path, env=env
    )

    logger.info("Building execution layers...")
    execution_layers = init_kedro_tasks_by_execution_layer(pipeline_name, execution_config)

    for layer in execution_layers:
        logger.info("Running layer...")
        for node_task in layer:
            logger.info("Running node...")
            node_task()

@task()
def kedro_init(pipeline_name: str, project_path: Path, env: str) -> Dict[str, Union[DataCatalog, str]]:
    logger = get_run_logger()
    logger.info("Bootstrapping project")
    bootstrap_project(project_path)
    session = KedroSession.create(project_path=project_path, env=env)
    logger.info("Session created with ID %s", session.session_id)
    pipeline = pipelines.get(pipeline_name)
    logger.info("Loading context...")
    context = session.load_context()
    catalog = context.catalog
    logger.info("Registering datasets...")
    unregistered_ds = pipeline.datasets() - set(catalog.list())
    for ds_name in unregistered_ds:
        catalog.add(ds_name, MemoryDataset())
    return {"catalog": catalog, "sess_id": session.session_id}

def init_kedro_tasks_by_execution_layer(
    pipeline_name: str,
    execution_config: Union[None, Dict[str, Union[DataCatalog, str]]] = None,
) -> List[List[Callable]]:
    pipeline = pipelines.get(pipeline_name)
    execution_layers = []
    for layer in pipeline.grouped_nodes:
        execution_layer = []
        for node in layer:
            t = instantiate_task(node, execution_config)
            execution_layer.append(t)
        execution_layers.append(execution_layer)
    return execution_layers

def kedro_task(node: Node, task_dict: Union[None, Dict[str, Union[DataCatalog, str]]] = None):
    run_node(
        node,
        task_dict["catalog"],
        _create_hook_manager(),
        task_dict["sess_id"],
    )

def instantiate_task(node: Node, execution_config: Union[None, Dict[str, Union[DataCatalog, str]]] = None) -> Callable:
    return task(lambda: kedro_task(node, execution_config)).with_options(name=node.name)

if __name__ == "__main__":
    my_flow(pipeline_name="__default__", env="base")
