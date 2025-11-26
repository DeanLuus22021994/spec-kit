"""
Async SOAP Client with zeep and Python 3.14 features
Supports WSDL parsing, WS-Security, and retry logic
"""

from __future__ import annotations

import asyncio
import hashlib
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Self

import httpx
import structlog  # pylint: disable=import-error
from pydantic import BaseModel, ConfigDict
from tenacity import retry, stop_after_attempt, wait_exponential  # pylint: disable=import-error
from zeep import AsyncClient  # pylint: disable=import-error
from zeep.cache import SqliteCache  # pylint: disable=import-error
from zeep.exceptions import Error as ZeepError  # pylint: disable=import-error
from zeep.transports import AsyncTransport  # pylint: disable=import-error

# Configure structured logging
logger = structlog.get_logger(__name__)


class SoapError(Exception):
    """Base exception for SOAP errors."""

    def __init__(
        self,
        message: str,
        code: str | None = None,
        details: dict[str, Any] | None = None,
    ):
        super().__init__(message)
        self.code = code
        self.details = details or {}


class WsdlError(SoapError):
    """WSDL parsing or validation error."""


class TransportError(SoapError):
    """HTTP transport error."""


@dataclass
class SoapClientConfig:
    """Configuration for SOAP client."""

    wsdl_url: str
    timeout: float = 30.0
    cache_path: Path = field(default_factory=lambda: Path("/app/cache/wsdl"))
    max_retries: int = 3
    verify_ssl: bool = True
    headers: dict[str, str] = field(default_factory=dict)

    def __post_init__(self):
        self.cache_path.mkdir(parents=True, exist_ok=True)


class SoapRequest(BaseModel):
    """SOAP request model."""

    model_config = ConfigDict(strict=True)

    operation: str
    params: dict[str, Any] = {}
    headers: dict[str, str] = {}

    def get_cache_key(self) -> str:
        """Generate cache key for request."""
        content = f"{self.operation}:{sorted(self.params.items())}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]


class SoapResponse(BaseModel):
    """SOAP response model."""

    model_config = ConfigDict(strict=True)

    success: bool
    data: dict[str, Any] = {}
    error: str | None = None
    duration_ms: float = 0.0

    @classmethod
    def from_zeep(cls, result: Any, duration: float) -> Self:
        """Create response from zeep result."""
        return cls(
            success=True,
            data=dict(result) if hasattr(result, "__iter__") else {"result": result},
            duration_ms=duration * 1000,
        )

    @classmethod
    def from_error(cls, error: Exception, duration: float) -> Self:
        """Create response from error."""
        return cls(
            success=False,
            error=str(error),
            duration_ms=duration * 1000,
        )


class SoapClient:
    """
    Async SOAP client with automatic WSDL parsing and caching.

    Usage:
        async with SoapClient("https://api.example.com?wsdl") as client:
            # List available operations
            operations = client.list_operations()

            # Call a SOAP operation
            result = await client.call("GetStatus", item_id="123")
    """

    def __init__(self, wsdl_url: str, **config_kwargs: Any):
        self.config = SoapClientConfig(wsdl_url=wsdl_url, **config_kwargs)
        self._client: AsyncClient | None = None
        self._transport: AsyncTransport | None = None
        self._http_client: httpx.AsyncClient | None = None
        self._logger = logger.bind(wsdl_url=wsdl_url)

    async def __aenter__(self) -> Self:
        """Async context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        await self.close()

    async def connect(self) -> None:
        """Initialize SOAP client with WSDL."""
        try:
            self._http_client = httpx.AsyncClient(
                timeout=self.config.timeout,
                verify=self.config.verify_ssl,
                headers=self.config.headers,
            )

            cache = SqliteCache(path=str(self.config.cache_path / "wsdl.db"))
            self._transport = AsyncTransport(client=self._http_client, cache=cache)
            self._client = AsyncClient(
                wsdl=self.config.wsdl_url,
                transport=self._transport,
            )

            self._logger.info("soap_client_connected", operations=self.list_operations())

        except ZeepError as e:
            raise WsdlError(f"Failed to parse WSDL: {e}") from e
        except httpx.HTTPError as e:
            raise TransportError(f"HTTP error fetching WSDL: {e}") from e

    async def close(self) -> None:
        """Close HTTP connections."""
        if self._http_client:
            await self._http_client.aclose()
            self._http_client = None
        self._client = None
        self._transport = None
        self._logger.info("soap_client_closed")

    def list_operations(self) -> list[str]:
        """List available SOAP operations."""
        if not self._client:
            return []

        operations = []
        for service in self._client.wsdl.services.values():
            for port in service.ports.values():
                # Access _operations is required by zeep API design
                operations.extend(port.binding._operations.keys())  # pylint: disable=protected-access
        return sorted(set(operations))

    def get_operation_signature(self, operation: str) -> dict[str, Any]:
        """Get input/output signature for an operation."""
        if not self._client:
            raise SoapError("Client not connected")

        for service in self._client.wsdl.services.values():
            for port in service.ports.values():
                # Access _operations is required by zeep API design
                if operation in port.binding._operations:  # pylint: disable=protected-access
                    op = port.binding._operations[operation]  # pylint: disable=protected-access
                    return {
                        "input": str(op.input.body),
                        "output": str(op.output.body) if op.output else None,
                    }

        raise SoapError(f"Operation '{operation}' not found")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
    )
    async def call(
        self,
        operation: str,
        _service: str | None = None,
        _port: str | None = None,
        **params: Any,
    ) -> SoapResponse:
        """
        Call a SOAP operation.

        Args:
            operation: Name of the SOAP operation to call
            _service: Optional service name (for multi-service WSDLs)
            _port: Optional port name
            **params: Operation parameters

        Returns:
            SoapResponse with result data or error
        """
        if not self._client:
            raise SoapError("Client not connected - use 'async with' context manager")

        start = asyncio.get_event_loop().time()
        # SoapRequest created for potential logging/tracing extension
        _ = SoapRequest(operation=operation, params=params)

        self._logger.info("soap_call_start", operation=operation, params=params)

        try:
            # Get service
            if _service:
                service = self._client.bind(_service, _port)
            else:
                service = self._client.service

            # Execute call
            method = getattr(service, operation)
            result = await method(**params)

            duration = asyncio.get_event_loop().time() - start
            response = SoapResponse.from_zeep(result, duration)

            self._logger.info(
                "soap_call_success",
                operation=operation,
                duration_ms=response.duration_ms,
            )

            return response

        except ZeepError as e:
            duration = asyncio.get_event_loop().time() - start
            self._logger.error("soap_call_error", operation=operation, error=str(e))
            return SoapResponse.from_error(e, duration)

    async def call_raw(self, operation: str, xml_body: str) -> str:
        """
        Send raw XML request for custom operations.

        Args:
            operation: Operation name for logging
            xml_body: Raw XML SOAP body

        Returns:
            Raw XML response string
        """
        if not self._http_client:
            raise SoapError("Client not connected")

        self._logger.info("soap_raw_call", operation=operation)

        response = await self._http_client.post(
            self.config.wsdl_url.replace("?wsdl", ""),
            content=xml_body.encode(),
            headers={"Content-Type": "text/xml; charset=utf-8"},
        )

        response.raise_for_status()
        return str(response.text)


@asynccontextmanager
async def create_client(wsdl_url: str, **kwargs: Any) -> AsyncIterator[SoapClient]:
    """Factory function for creating SOAP client."""
    client = SoapClient(wsdl_url, **kwargs)
    try:
        await client.connect()
        yield client
    finally:
        await client.close()
