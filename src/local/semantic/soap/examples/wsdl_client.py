#!/usr/bin/env python3
"""
Example SOAP client usage with Python 3.14 async features.

Usage:
    python wsdl_client.py https://api.example.com/service?wsdl list
    python wsdl_client.py https://api.example.com/service?wsdl call GetStatus item_id=123
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from typing import TYPE_CHECKING

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

if TYPE_CHECKING:
    pass

# Import after path modification - pylint: disable=wrong-import-position
from semantic.soap import SoapClient  # noqa: E402


async def main() -> int:
    """Entry point for WSDL client CLI."""
    if len(sys.argv) < 3:
        print(__doc__)
        return 1

    wsdl_url = sys.argv[1]
    command = sys.argv[2]

    async with SoapClient(wsdl_url) as client:
        return await _handle_command(client, command)


async def _handle_command(client: SoapClient, command: str) -> int:
    """Dispatch command to appropriate handler."""
    handlers = {
        "list": _cmd_list,
        "call": _cmd_call,
        "signature": _cmd_signature,
    }
    handler = handlers.get(command)
    if handler is None:
        print(f"Unknown command: {command}")
        print("Commands: list, call, signature")
        return 1
    return await handler(client)


async def _cmd_list(client: SoapClient) -> int:
    """List available WSDL operations."""
    operations = client.list_operations()
    print(f"Available operations ({len(operations)}):")
    for op in operations:
        print(f"  - {op}")
    return 0


async def _cmd_call(client: SoapClient) -> int:
    """Call a SOAP operation."""
    if len(sys.argv) < 4:
        print("Usage: call <operation> [key=value ...]")
        return 1

    operation = sys.argv[3]
    params = {arg.split("=", 1)[0]: arg.split("=", 1)[1] for arg in sys.argv[4:] if "=" in arg}

    result = await client.call(operation, **params)
    if not result.success:
        print(f"Error: {result.error}")
        return 1

    print(f"Success ({result.duration_ms:.2f}ms):")
    for k, v in result.data.items():
        print(f"  {k}: {v}")
    return 0


async def _cmd_signature(client: SoapClient) -> int:
    """Show operation signature."""
    if len(sys.argv) < 4:
        print("Usage: signature <operation>")
        return 1

    sig = client.get_operation_signature(sys.argv[3])
    print(f"Input: {sig['input']}")
    print(f"Output: {sig['output']}")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
