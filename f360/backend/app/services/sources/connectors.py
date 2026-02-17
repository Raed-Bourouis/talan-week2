"""
F360 – Source Connectors
Pluggable connectors for S3, Kafka, API endpoints, and SharePoint.
Each connector implements a common interface: connect(), fetch(), stream().
"""
from __future__ import annotations

import asyncio
import io
import json
import logging
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, AsyncIterator
from pathlib import Path

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════
# BASE CONNECTOR INTERFACE
# ═══════════════════════════════════════════════════════════════

class BaseConnector(ABC):
    """Abstract connector for multimodal data sources."""

    def __init__(self, name: str, config: dict[str, Any] | None = None):
        self.name = name
        self.config = config or {}
        self._connected = False

    @abstractmethod
    async def connect(self) -> None:
        """Establish connection to the source."""
        ...

    @abstractmethod
    async def fetch(self, query: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        """Fetch data from the source (batch mode)."""
        ...

    @abstractmethod
    async def stream(self, topic: str | None = None) -> AsyncIterator[dict[str, Any]]:
        """Stream data from the source in real-time."""
        ...

    async def disconnect(self) -> None:
        """Clean up connection resources."""
        self._connected = False

    @property
    def is_connected(self) -> bool:
        return self._connected


# ═══════════════════════════════════════════════════════════════
# S3 CONNECTOR
# ═══════════════════════════════════════════════════════════════

class S3Connector(BaseConnector):
    """
    AWS S3 / MinIO connector for document ingestion.
    Supports: list, download, upload, watch for new objects.
    """

    def __init__(self, config: dict[str, Any] | None = None):
        super().__init__("S3", config)
        self.bucket = self.config.get("bucket", "f360-documents")
        self.prefix = self.config.get("prefix", "")
        self.endpoint_url = self.config.get("endpoint_url")  # For MinIO
        self._client = None

    async def connect(self) -> None:
        try:
            import aiobotocore.session
            session = aiobotocore.session.get_session()
            kwargs = {
                "region_name": self.config.get("region", "eu-west-1"),
            }
            if self.endpoint_url:
                kwargs["endpoint_url"] = self.endpoint_url
            self._client = await session.create_client("s3", **kwargs).__aenter__()
            self._connected = True
            logger.info(f"S3 connected: bucket={self.bucket}")
        except ImportError:
            logger.warning("aiobotocore not installed – S3 connector in mock mode")
            self._connected = True  # Mock mode

    async def fetch(self, query: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        """List and download objects from S3 bucket."""
        prefix = (query or {}).get("prefix", self.prefix)
        max_keys = (query or {}).get("max_keys", 100)

        if self._client is None:
            return self._mock_fetch(prefix, max_keys)

        response = await self._client.list_objects_v2(
            Bucket=self.bucket, Prefix=prefix, MaxKeys=max_keys,
        )
        objects = []
        for obj in response.get("Contents", []):
            objects.append({
                "key": obj["Key"],
                "size": obj["Size"],
                "last_modified": obj["LastModified"].isoformat(),
                "source": "s3",
                "bucket": self.bucket,
            })
        return objects

    async def download(self, key: str) -> bytes:
        """Download an object from S3."""
        if self._client is None:
            return b""
        response = await self._client.get_object(Bucket=self.bucket, Key=key)
        return await response["Body"].read()

    async def stream(self, topic: str | None = None) -> AsyncIterator[dict[str, Any]]:
        """Poll S3 for new objects (simulated streaming)."""
        seen_keys: set[str] = set()
        while True:
            objects = await self.fetch({"prefix": topic or self.prefix})
            for obj in objects:
                if obj["key"] not in seen_keys:
                    seen_keys.add(obj["key"])
                    yield obj
            await asyncio.sleep(30)  # Poll interval

    def _mock_fetch(self, prefix: str, max_keys: int) -> list[dict[str, Any]]:
        return [
            {"key": f"{prefix}sample_invoice.pdf", "size": 245000, "source": "s3-mock"},
            {"key": f"{prefix}budget_2026.xlsx", "size": 128000, "source": "s3-mock"},
        ]


# ═══════════════════════════════════════════════════════════════
# KAFKA CONNECTOR
# ═══════════════════════════════════════════════════════════════

class KafkaConnector(BaseConnector):
    """
    Apache Kafka connector for real-time event ingestion.
    Consumes financial events: invoices, payments, accounting entries.
    """

    def __init__(self, config: dict[str, Any] | None = None):
        super().__init__("Kafka", config)
        self.brokers = self.config.get("brokers", "localhost:9092")
        self.group_id = self.config.get("group_id", "f360-consumer")
        self.topics = self.config.get("topics", ["f360.invoices", "f360.payments", "f360.entries"])
        self._consumer = None

    async def connect(self) -> None:
        try:
            from aiokafka import AIOKafkaConsumer
            self._consumer = AIOKafkaConsumer(
                *self.topics,
                bootstrap_servers=self.brokers,
                group_id=self.group_id,
                auto_offset_reset="latest",
                value_deserializer=lambda v: json.loads(v.decode("utf-8")),
            )
            await self._consumer.start()
            self._connected = True
            logger.info(f"Kafka connected: brokers={self.brokers}, topics={self.topics}")
        except ImportError:
            logger.warning("aiokafka not installed – Kafka connector in mock mode")
            self._connected = True

    async def fetch(self, query: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        """Consume a batch of messages."""
        timeout = (query or {}).get("timeout_ms", 5000)
        max_records = (query or {}).get("max_records", 100)

        if self._consumer is None:
            return self._mock_fetch()

        data = await self._consumer.getmany(timeout_ms=timeout, max_records=max_records)
        records = []
        for tp, messages in data.items():
            for msg in messages:
                records.append({
                    "topic": tp.topic,
                    "partition": tp.partition,
                    "offset": msg.offset,
                    "timestamp": msg.timestamp,
                    "value": msg.value,
                    "source": "kafka",
                })
        return records

    async def stream(self, topic: str | None = None) -> AsyncIterator[dict[str, Any]]:
        """Stream messages from Kafka in real-time."""
        if self._consumer is None:
            # Mock stream
            for record in self._mock_fetch():
                yield record
                await asyncio.sleep(1)
            return

        async for msg in self._consumer:
            yield {
                "topic": msg.topic,
                "partition": msg.partition,
                "offset": msg.offset,
                "value": msg.value,
                "source": "kafka",
            }

    async def disconnect(self) -> None:
        if self._consumer:
            await self._consumer.stop()
        await super().disconnect()

    def _mock_fetch(self) -> list[dict[str, Any]]:
        return [
            {
                "topic": "f360.invoices",
                "value": {"invoice_number": "FAC-2026-001", "amount": 15000.00},
                "source": "kafka-mock",
            }
        ]


# ═══════════════════════════════════════════════════════════════
# API CONNECTOR (REST / GraphQL)
# ═══════════════════════════════════════════════════════════════

class APIConnector(BaseConnector):
    """
    Generic REST/GraphQL connector for ERP/CRM/SIRH systems.
    Supports: SAP, Oracle, Sage, Salesforce, custom APIs.
    """

    def __init__(self, config: dict[str, Any] | None = None):
        super().__init__("API", config)
        self.base_url = self.config.get("base_url", "")
        self.auth_type = self.config.get("auth_type", "bearer")  # bearer, basic, api_key
        self.auth_token = self.config.get("auth_token", "")
        self.headers = self.config.get("headers", {})

    async def connect(self) -> None:
        try:
            import httpx
            self._http = httpx.AsyncClient(
                base_url=self.base_url,
                headers={
                    **self.headers,
                    "Authorization": f"Bearer {self.auth_token}" if self.auth_type == "bearer" else "",
                },
                timeout=30.0,
            )
            self._connected = True
            logger.info(f"API connected: {self.base_url}")
        except ImportError:
            logger.warning("httpx not installed – API connector in mock mode")
            self._connected = True

    async def fetch(self, query: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        """Fetch data from API endpoint."""
        endpoint = (query or {}).get("endpoint", "/")
        params = (query or {}).get("params", {})

        if not hasattr(self, "_http") or self._http is None:
            return self._mock_fetch(endpoint)

        response = await self._http.get(endpoint, params=params)
        response.raise_for_status()
        data = response.json()
        return data if isinstance(data, list) else [data]

    async def stream(self, topic: str | None = None) -> AsyncIterator[dict[str, Any]]:
        """Poll API endpoint for new data."""
        while True:
            records = await self.fetch({"endpoint": topic or "/"})
            for record in records:
                yield record
            await asyncio.sleep(60)

    def _mock_fetch(self, endpoint: str) -> list[dict[str, Any]]:
        return [
            {
                "endpoint": endpoint,
                "data": {"synced_records": 42, "status": "success"},
                "source": "api-mock",
            }
        ]


# ═══════════════════════════════════════════════════════════════
# SHAREPOINT CONNECTOR
# ═══════════════════════════════════════════════════════════════

class SharePointConnector(BaseConnector):
    """
    Microsoft SharePoint / OneDrive connector.
    Accesses document libraries via Microsoft Graph API.
    """

    def __init__(self, config: dict[str, Any] | None = None):
        super().__init__("SharePoint", config)
        self.tenant_id = self.config.get("tenant_id", "")
        self.client_id = self.config.get("client_id", "")
        self.client_secret = self.config.get("client_secret", "")
        self.site_url = self.config.get("site_url", "")
        self.drive_id = self.config.get("drive_id", "")
        self._graph_client = None

    async def connect(self) -> None:
        """Authenticate via OAuth2 client credentials flow."""
        logger.info(f"SharePoint connector initialized for site: {self.site_url}")
        self._connected = True  # Production: implement MS Graph auth

    async def fetch(self, query: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        """List files in a SharePoint document library."""
        folder = (query or {}).get("folder", "/")

        # Mock implementation – production uses MS Graph API
        return [
            {
                "name": "Contrat_Fournisseur_A.pdf",
                "size": 320000,
                "path": f"{folder}/Contrat_Fournisseur_A.pdf",
                "modified": datetime.now(timezone.utc).isoformat(),
                "source": "sharepoint",
            },
            {
                "name": "Budget_Q1_2026.xlsx",
                "size": 95000,
                "path": f"{folder}/Budget_Q1_2026.xlsx",
                "modified": datetime.now(timezone.utc).isoformat(),
                "source": "sharepoint",
            },
        ]

    async def stream(self, topic: str | None = None) -> AsyncIterator[dict[str, Any]]:
        """Watch SharePoint folder for changes via delta query."""
        while True:
            files = await self.fetch({"folder": topic or "/"})
            for f in files:
                yield f
            await asyncio.sleep(120)


# ═══════════════════════════════════════════════════════════════
# CONNECTOR REGISTRY
# ═══════════════════════════════════════════════════════════════

CONNECTOR_REGISTRY: dict[str, type[BaseConnector]] = {
    "s3": S3Connector,
    "kafka": KafkaConnector,
    "api": APIConnector,
    "sharepoint": SharePointConnector,
}


def get_connector(source_type: str, config: dict[str, Any] | None = None) -> BaseConnector:
    """Factory: instantiate a connector by type."""
    cls = CONNECTOR_REGISTRY.get(source_type.lower())
    if cls is None:
        raise ValueError(
            f"Unknown source type: {source_type}. "
            f"Available: {list(CONNECTOR_REGISTRY.keys())}"
        )
    return cls(config)
