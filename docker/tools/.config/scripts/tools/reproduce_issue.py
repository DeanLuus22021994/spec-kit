"""
Reproduction and verification script for SubagentTask type conversion.

This script verifies that the SubagentTask class correctly handles
string inputs for task_type by converting them to TaskType enum members.
It serves as a regression test for the CLI-to-Orchestrator interface.
"""

import json
import sys

from orchestrator.config import SubagentTask, TaskType
from orchestrator.orchestrator import SubagentOrchestrator

# JSON payload simulating CLI input
TASK_JSON = '{"task_id": "test", "task_type": "DOCKER_RUN", "payload": {}}'


def verify_task_creation() -> SubagentTask:
    """
    Verify that SubagentTask can be created from JSON string data.

    Returns:
        The created SubagentTask instance.
    """
    print("Testing SubagentTask creation from JSON...")
    task_data = json.loads(TASK_JSON)

    try:
        task = SubagentTask(**task_data)
        print(f"Task created successfully: {task}")
        print(f"Task type type: {type(task.task_type)}")

        # Verify the fix: task_type should be an Enum, not a string
        if not isinstance(task.task_type, TaskType):
            print("FAILURE: task_type is not an Enum member")
            sys.exit(1)

        if task.task_type != TaskType.DOCKER_RUN:
            print(
                f"FAILURE: task_type mismatch. Expected DOCKER_RUN, got {task.task_type}"
            )
            sys.exit(1)

        print("SUCCESS: SubagentTask correctly converted string to Enum")
        return task

    except (ValueError, TypeError) as e:
        print(f"Error creating task: {e}")
        sys.exit(1)


def verify_orchestrator_integration(task: SubagentTask) -> None:
    """
    Verify that the orchestrator can handle the created task.

    Args:
        task: The SubagentTask to verify against the orchestrator.
    """
    print("\nTesting Orchestrator integration...")

    try:
        orch = SubagentOrchestrator()
        print(f"Orchestrator initialized: {orch}")

        # Verify that we can check for executors without error
        # This mimics the check in orchestrator.submit()
        if task.task_type not in orch.executors:
            print(
                f"Note: No executor registered for {task.task_type} (Expected in this test)"
            )

    except (ValueError, RuntimeError) as e:
        print(f"Error in orchestrator: {e}")
        sys.exit(1)


def main() -> None:
    """Main execution function."""
    try:
        task = verify_task_creation()
        verify_orchestrator_integration(task)
    except Exception as e:  # pylint: disable=broad-exception-caught
        print(f"Unexpected error during verification: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
