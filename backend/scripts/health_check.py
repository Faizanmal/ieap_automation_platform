#!/usr/bin/env python3
"""
IEAP - Health Check Script

This script performs health checks on the application components.
Used for Kubernetes liveness and readiness probes.
"""

import asyncio
import os
import sys
from typing import Any

import aiohttp

# Configuration
API_HOST = os.getenv("API_HOST", "localhost")
API_PORT = int(os.getenv("API_PORT", "8000"))
TIMEOUT = int(os.getenv("HEALTH_CHECK_TIMEOUT", "10"))


async def check_health(check_type: str = "liveness") -> dict[str, Any]:
    """Perform health check against the API."""
    url = f"http://{API_HOST}:{API_PORT}/api/v1/health/{check_type}"

    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, timeout=TIMEOUT) as response:
                if response.status == 200:
                    return await response.json()
                return {"status": "unhealthy", "code": response.status}
        except aiohttp.ClientError as e:
            return {"status": "unhealthy", "error": str(e)}
        except TimeoutError:
            return {"status": "unhealthy", "error": "timeout"}


def main() -> int:
    """Main entry point for health check."""
    check_type = sys.argv[1] if len(sys.argv) > 1 else "liveness"

    if check_type not in ("liveness", "readiness"):
        print(f"Invalid check type: {check_type}")
        print("Usage: health_check.py [liveness|readiness]")
        return 1

    result = asyncio.run(check_health(check_type))

    if result.get("status") == "healthy":
        print(f"✓ {check_type.capitalize()} check passed")
        return 0
    print(f"✗ {check_type.capitalize()} check failed: {result}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
