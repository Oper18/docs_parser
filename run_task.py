import asyncio
import argparse

from core.settings import settings
from lib.typesense.client import AsyncClient

from tasks import task_runners


def parse_arguments():
    parser = argparse.ArgumentParser(description="Typesense client application")
    parser.add_argument("--task", help="Task type for running", required=True)
    return parser.parse_args()


async def main(args):
    client = AsyncClient(
        {
            "api_key": settings.typesense_api_key,
            "nodes": [
                {
                    "host": settings.typesense_host,
                    "port": settings.typesense_port,
                    "protocol": settings.typesense_protocol,
                }
            ],
            "connection_timeout_seconds": 10,
        }
    )
    task_runner = next(
        (runner for runner in task_runners if runner._task_type == args.task), None
    )
    task_runner_instance = task_runner(client)
    await task_runner_instance.run()


if __name__ == "__main__":
    args = parse_arguments()
    asyncio.run(main(args))
