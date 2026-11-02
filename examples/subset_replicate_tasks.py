"""Prepare independent synthetic tasks; run/reduce functions are explicit opt-in calls.

This example submits no scheduler jobs and opens no remote connection.
"""

import argparse
import runpy
from pathlib import Path

from matintegrity.subset_replicates import (
    SubsetReplicateRequest,
    SubsetReplicateTask,
    SubsetReplicateTaskResult,
    build_subset_replicate_tasks,
    reduce_subset_replicate_tasks,
    run_subset_replicate_task,
)


def synthetic_parent_request():
    builder = runpy.run_path(str(Path(__file__).with_name("subset_simulation.py")))["build_request"]
    return SubsetReplicateRequest(
        analysis_id="authored-independent-replicates",
        template=builder(),
        seeds=(101, 202, 303, 404),
        target_relative_standard_error=0.1,
    )


def prepare(directory: Path):
    directory.mkdir(parents=True, exist_ok=False)
    request = synthetic_parent_request()
    (directory / "parent.json").write_text(request.model_dump_json(indent=2), encoding="utf-8")
    for index, task in enumerate(build_subset_replicate_tasks(request)):
        (directory / f"task-{index:04d}.json").write_text(task.model_dump_json(indent=2), encoding="utf-8")


def run_one(task_path: Path, output_path: Path):
    if output_path.exists():
        raise FileExistsError(output_path)
    task = SubsetReplicateTask.model_validate_json(task_path.read_text(encoding="utf-8"))
    # This is only the authored synthetic evaluator declared by synthetic_parent_request().
    expected = synthetic_parent_request()
    if task not in build_subset_replicate_tasks(expected):
        raise ValueError("this example worker only accepts its exact authored task manifest")
    result = run_subset_replicate_task(lambda latent: 2.0 - latent[0], task)
    with output_path.open("x", encoding="utf-8") as stream:
        stream.write(result.model_dump_json(indent=2))


def reduce(parent_path: Path, result_paths: list[Path], output_path: Path):
    parent = SubsetReplicateRequest.model_validate_json(parent_path.read_text(encoding="utf-8"))
    results = tuple(
        SubsetReplicateTaskResult.model_validate_json(path.read_text(encoding="utf-8"))
        for path in result_paths
    )
    summary = reduce_subset_replicate_tasks(parent, results)
    with output_path.open("x", encoding="utf-8") as stream:
        stream.write(summary.model_dump_json(indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    prepare_parser = commands.add_parser("prepare")
    prepare_parser.add_argument("directory", type=Path)
    run_parser = commands.add_parser("run")
    run_parser.add_argument("task", type=Path)
    run_parser.add_argument("output", type=Path)
    reduce_parser = commands.add_parser("reduce")
    reduce_parser.add_argument("parent", type=Path)
    reduce_parser.add_argument("output", type=Path)
    reduce_parser.add_argument("results", type=Path, nargs="+")
    args = parser.parse_args()
    if args.command == "prepare":
        prepare(args.directory)
    elif args.command == "run":
        run_one(args.task, args.output)
    else:
        reduce(args.parent, args.results, args.output)


if __name__ == "__main__":
    main()
