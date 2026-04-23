"""
Real-Time Data Pipeline - Intelligent Enterprise Automation Platform

This module provides a high-performance, event-driven data pipeline for
real-time processing of enterprise data streams. It handles multiple data
sources, applies transformations, and routes data to appropriate consumers
with automatic scaling and fault tolerance.

Key Features:
- Multi-source data ingestion (APIs, databases, files, IoT sensors)
- Real-time stream processing with low latency
- Event-driven architecture with message queuing
- Automatic scaling based on data volume
- Data quality validation and enrichment
- Multiple output formats and destinations
- Built-in monitoring and alerting
"""

import asyncio
import concurrent.futures
import json
import logging
import queue
import threading
import time
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class DataSourceType(Enum):
    """Types of data sources"""
    API = "api"
    DATABASE = "database"
    FILE = "file"
    STREAM = "stream"
    IOT_SENSOR = "iot_sensor"
    MESSAGE_QUEUE = "message_queue"


class ProcessingStatus(Enum):
    """Data processing status"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"


class DataQuality(Enum):
    """Data quality levels"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INVALID = "invalid"


@dataclass
class DataRecord:
    """Represents a single data record in the pipeline"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    source_id: str = ""
    source_type: DataSourceType = DataSourceType.API
    timestamp: datetime = field(default_factory=datetime.now)
    data: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    quality_score: float = 1.0
    quality_level: DataQuality = DataQuality.HIGH
    processing_status: ProcessingStatus = ProcessingStatus.PENDING
    error_message: str = ""
    retry_count: int = 0
    max_retries: int = 3


@dataclass
class PipelineMetrics:
    """Pipeline performance metrics"""
    records_processed: int = 0
    records_failed: int = 0
    total_throughput: float = 0.0
    average_latency: float = 0.0
    current_load: float = 0.0
    pipeline_health: float = 1.0
    last_updated: datetime = field(default_factory=datetime.now)


class DataSource(ABC):
    """Abstract base class for data sources"""

    def __init__(self, source_id: str, config: dict[str, Any]):
        self.source_id = source_id
        self.config = config
        self.is_active = False
        self.metrics = {"records_read": 0, "errors": 0}

    @abstractmethod
    async def read_data(self) -> list[DataRecord]:
        """Read data from the source"""

    @abstractmethod
    def start(self):
        """Start the data source"""

    @abstractmethod
    def stop(self):
        """Stop the data source"""


class APIDataSource(DataSource):
    """Data source for REST APIs"""

    def __init__(self, source_id: str, config: dict[str, Any]):
        super().__init__(source_id, config)
        self.endpoint = config.get("endpoint", "")
        self.headers = config.get("headers", {})
        self.poll_interval = config.get("poll_interval", 60)  # seconds
        self._running = False
        self._thread = None

    async def read_data(self) -> list[DataRecord]:
        """Read data from API endpoint"""
        records = []

        try:
            # Mock API call - in real implementation, use aiohttp or requests
            # response = await aiohttp.get(self.endpoint, headers=self.headers)
            # data = await response.json()

            # Generate mock API data
            mock_data = [
                {
                    "customer_id": f"cust_{i}",
                    "transaction_amount": 100 + i * 10,
                    "timestamp": datetime.now().isoformat(),
                    "merchant": f"merchant_{i % 5}",
                    "status": "completed"
                }
                for i in range(5)
            ]

            for item in mock_data:
                record = DataRecord(
                    source_id=self.source_id,
                    source_type=DataSourceType.API,
                    data=item,
                    metadata={"endpoint": self.endpoint}
                )
                records.append(record)

            self.metrics["records_read"] += len(records)

        except Exception as e:
            logger.error(f"Error reading from API {self.endpoint}: {e!s}")
            self.metrics["errors"] += 1

        return records

    def start(self):
        """Start polling the API"""
        self.is_active = True
        self._running = True
        self._thread = threading.Thread(target=self._poll_loop)
        self._thread.start()
        logger.info(f"Started API data source: {self.source_id}")

    def stop(self):
        """Stop polling the API"""
        self.is_active = False
        self._running = False
        if self._thread:
            self._thread.join()
        logger.info(f"Stopped API data source: {self.source_id}")

    def _poll_loop(self):
        """Polling loop for the API"""
        while self._running:
            try:
                # This would be handled by the pipeline manager
                time.sleep(self.poll_interval)
            except Exception as e:
                logger.error(f"Error in polling loop: {e!s}")


class DatabaseDataSource(DataSource):
    """Data source for databases"""

    def __init__(self, source_id: str, config: dict[str, Any]):
        super().__init__(source_id, config)
        self.connection_string = config.get("connection_string", "")
        self.query = config.get("query", "")
        self.poll_interval = config.get("poll_interval", 300)  # 5 minutes

    async def read_data(self) -> list[DataRecord]:
        """Read data from database"""
        records = []

        try:
            # Mock database query - in real implementation, use asyncpg, aiomysql, etc.
            # conn = await asyncpg.connect(self.connection_string)
            # rows = await conn.fetch(self.query)
            # await conn.close()

            # Generate mock database data
            mock_rows = [
                {
                    "id": i,
                    "product_id": f"prod_{i}",
                    "inventory_count": 100 - i,
                    "warehouse": f"warehouse_{i % 3}",
                    "last_updated": datetime.now().isoformat()
                }
                for i in range(10)
            ]

            for row in mock_rows:
                record = DataRecord(
                    source_id=self.source_id,
                    source_type=DataSourceType.DATABASE,
                    data=row,
                    metadata={"table": "inventory", "query": self.query}
                )
                records.append(record)

            self.metrics["records_read"] += len(records)

        except Exception as e:
            logger.error(f"Error reading from database: {e!s}")
            self.metrics["errors"] += 1

        return records

    def start(self):
        """Start database monitoring"""
        self.is_active = True
        logger.info(f"Started database data source: {self.source_id}")

    def stop(self):
        """Stop database monitoring"""
        self.is_active = False
        logger.info(f"Stopped database data source: {self.source_id}")


class DataProcessor(ABC):
    """Abstract base class for data processors"""

    @abstractmethod
    def process(self, record: DataRecord) -> DataRecord:
        """Process a data record"""


class DataValidationProcessor(DataProcessor):
    """Validates data quality and completeness"""

    def __init__(self, validation_rules: dict[str, Any]):
        self.validation_rules = validation_rules

    def process(self, record: DataRecord) -> DataRecord:
        """Validate data record"""
        try:
            quality_score = 1.0

            # Check required fields
            required_fields = self.validation_rules.get("required_fields", [])
            for field in required_fields:
                if field not in record.data or record.data[field] is None:
                    quality_score -= 0.2

            # Check data types
            type_rules = self.validation_rules.get("type_rules", {})
            for field, expected_type in type_rules.items():
                if field in record.data:
                    if not isinstance(record.data[field], expected_type):
                        quality_score -= 0.1

            # Check value ranges
            range_rules = self.validation_rules.get("range_rules", {})
            for field, (min_val, max_val) in range_rules.items():
                if field in record.data:
                    value = record.data[field]
                    if isinstance(value, (int, float)):
                        if value < min_val or value > max_val:
                            quality_score -= 0.15

            # Update record quality
            record.quality_score = max(0.0, quality_score)

            if record.quality_score >= 0.8:
                record.quality_level = DataQuality.HIGH
            elif record.quality_score >= 0.6:
                record.quality_level = DataQuality.MEDIUM
            elif record.quality_score >= 0.4:
                record.quality_level = DataQuality.LOW
            else:
                record.quality_level = DataQuality.INVALID

        except Exception as e:
            record.quality_level = DataQuality.INVALID
            record.error_message = f"Validation error: {e!s}"

        return record


class DataEnrichmentProcessor(DataProcessor):
    """Enriches data with additional information"""

    def __init__(self, enrichment_config: dict[str, Any]):
        self.enrichment_config = enrichment_config

    def process(self, record: DataRecord) -> DataRecord:
        """Enrich data record"""
        try:
            # Add timestamp if not present
            if "processed_timestamp" not in record.data:
                record.data["processed_timestamp"] = datetime.now().isoformat()

            # Add computed fields
            if "transaction_amount" in record.data:
                amount = record.data["transaction_amount"]
                record.data["amount_category"] = self._categorize_amount(amount)
                record.data["amount_tier"] = self._get_amount_tier(amount)

            # Add geolocation info (mock)
            if "customer_id" in record.data:
                record.data["customer_region"] = self._get_customer_region(record.data["customer_id"])

            # Add business context
            record.metadata["enriched_at"] = datetime.now().isoformat()
            record.metadata["enrichment_version"] = "1.0"

        except Exception as e:
            record.error_message = f"Enrichment error: {e!s}"

        return record

    def _categorize_amount(self, amount: float) -> str:
        """Categorize transaction amount"""
        if amount < 50:
            return "small"
        if amount < 500:
            return "medium"
        if amount < 5000:
            return "large"
        return "very_large"

    def _get_amount_tier(self, amount: float) -> int:
        """Get amount tier (1-5)"""
        if amount < 100:
            return 1
        if amount < 500:
            return 2
        if amount < 1000:
            return 3
        if amount < 5000:
            return 4
        return 5

    def _get_customer_region(self, customer_id: str) -> str:
        """Get customer region (mock implementation)"""
        regions = ["North", "South", "East", "West", "Central"]
        return regions[hash(customer_id) % len(regions)]


class DataSink(ABC):
    """Abstract base class for data sinks"""

    @abstractmethod
    async def write_data(self, records: list[DataRecord]):
        """Write data to the sink"""


class DatabaseSink(DataSink):
    """Writes data to a database"""

    def __init__(self, connection_string: str, table_name: str):
        self.connection_string = connection_string
        self.table_name = table_name
        self.metrics = {"records_written": 0, "errors": 0}

    async def write_data(self, records: list[DataRecord]):
        """Write records to database"""
        try:
            # Mock database write - in real implementation, use batch inserts
            for record in records:
                # await conn.execute(insert_query, record.data)
                pass

            self.metrics["records_written"] += len(records)
            logger.info(f"Wrote {len(records)} records to database table {self.table_name}")

        except Exception as e:
            self.metrics["errors"] += 1
            logger.error(f"Error writing to database: {e!s}")


class FileSystemSink(DataSink):
    """Writes data to files"""

    def __init__(self, output_directory: str, file_format: str = "json"):
        self.output_directory = output_directory
        self.file_format = file_format
        self.metrics = {"files_written": 0, "records_written": 0}

    async def write_data(self, records: list[DataRecord]):
        """Write records to files"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"data_batch_{timestamp}.{self.file_format}"
            filepath = f"{self.output_directory}/{filename}"

            # Convert records to serializable format
            data_to_write = [
                {
                    "id": record.id,
                    "source_id": record.source_id,
                    "timestamp": record.timestamp.isoformat(),
                    "data": record.data,
                    "quality_score": record.quality_score
                }
                for record in records
            ]

            # Mock file write - in real implementation, write to actual file
            # with open(filepath, 'w') as f:
            #     if self.file_format == 'json':
            #         json.dump(data_to_write, f, indent=2)

            self.metrics["files_written"] += 1
            self.metrics["records_written"] += len(records)
            logger.info(f"Wrote {len(records)} records to file {filename}")

        except Exception as e:
            logger.error(f"Error writing to file: {e!s}")


class RealTimeDataPipeline:
    """
    Main real-time data pipeline orchestrator
    """

    def __init__(self, config: dict[str, Any] = None):
        self.config = config or {}
        self.data_sources: dict[str, DataSource] = {}
        self.processors: list[DataProcessor] = []
        self.data_sinks: list[DataSink] = []
        self.processing_queue = queue.Queue()
        self.metrics = PipelineMetrics()
        self.is_running = False
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=10)
        self._processing_threads = []

        # Configuration
        self.batch_size = config.get("batch_size", 100)
        self.processing_interval = config.get("processing_interval", 1.0)  # seconds
        self.max_queue_size = config.get("max_queue_size", 10000)

        # Initialize components
        self._initialize_processors()
        self._initialize_sinks()

        logger.info("Real-time data pipeline initialized")

    def _initialize_processors(self):
        """Initialize data processors"""

        # Data validation processor
        validation_rules = {
            "required_fields": ["timestamp"],
            "type_rules": {
                "transaction_amount": float,
                "customer_id": str
            },
            "range_rules": {
                "transaction_amount": (0, 100000)
            }
        }
        self.processors.append(DataValidationProcessor(validation_rules))

        # Data enrichment processor
        enrichment_config = {
            "add_regions": True,
            "compute_categories": True
        }
        self.processors.append(DataEnrichmentProcessor(enrichment_config))

    def _initialize_sinks(self):
        """Initialize data sinks"""

        # Database sink
        db_sink = DatabaseSink("mock_connection_string", "processed_data")
        self.data_sinks.append(db_sink)

        # File system sink
        fs_sink = FileSystemSink("./output", "json")
        self.data_sinks.append(fs_sink)

    def add_data_source(self, source: DataSource):
        """Add a data source to the pipeline"""
        self.data_sources[source.source_id] = source
        logger.info(f"Added data source: {source.source_id}")

    def add_processor(self, processor: DataProcessor):
        """Add a data processor to the pipeline"""
        self.processors.append(processor)

    def add_sink(self, sink: DataSink):
        """Add a data sink to the pipeline"""
        self.data_sinks.append(sink)

    def start(self):
        """Start the data pipeline"""
        if self.is_running:
            logger.warning("Pipeline is already running")
            return

        self.is_running = True

        # Start all data sources
        for source in self.data_sources.values():
            source.start()

        # Start processing threads
        for i in range(self.config.get("processing_threads", 3)):
            thread = threading.Thread(target=self._processing_loop, args=(i,))
            thread.start()
            self._processing_threads.append(thread)

        # Start data ingestion loop
        ingestion_thread = threading.Thread(target=self._ingestion_loop)
        ingestion_thread.start()
        self._processing_threads.append(ingestion_thread)

        # Start metrics update loop
        metrics_thread = threading.Thread(target=self._metrics_loop)
        metrics_thread.start()
        self._processing_threads.append(metrics_thread)

        logger.info("Data pipeline started")

    def stop(self):
        """Stop the data pipeline"""
        if not self.is_running:
            return

        self.is_running = False

        # Stop all data sources
        for source in self.data_sources.values():
            source.stop()

        # Wait for processing threads to finish
        for thread in self._processing_threads:
            thread.join()

        self.executor.shutdown(wait=True)

        logger.info("Data pipeline stopped")

    def _ingestion_loop(self):
        """Main data ingestion loop"""
        while self.is_running:
            try:
                # Collect data from all sources
                for source in self.data_sources.values():
                    if source.is_active:
                        records = asyncio.run(source.read_data())

                        for record in records:
                            if self.processing_queue.qsize() < self.max_queue_size:
                                self.processing_queue.put(record)
                            else:
                                logger.warning("Processing queue is full, dropping record")

                time.sleep(self.processing_interval)

            except Exception as e:
                logger.error(f"Error in ingestion loop: {e!s}")

    def _processing_loop(self, thread_id: int):
        """Data processing loop"""
        batch = []
        last_batch_time = time.time()

        while self.is_running:
            try:
                # Try to get a record from the queue
                try:
                    record = self.processing_queue.get(timeout=1.0)
                    batch.append(record)
                except queue.Empty:
                    # Process current batch if it's been too long
                    if batch and (time.time() - last_batch_time) > 5.0:
                        self._process_batch(batch, thread_id)
                        batch = []
                        last_batch_time = time.time()
                    continue

                # Process batch when it reaches the desired size
                if len(batch) >= self.batch_size:
                    self._process_batch(batch, thread_id)
                    batch = []
                    last_batch_time = time.time()

            except Exception as e:
                logger.error(f"Error in processing loop {thread_id}: {e!s}")

        # Process remaining batch
        if batch:
            self._process_batch(batch, thread_id)

    def _process_batch(self, batch: list[DataRecord], thread_id: int):
        """Process a batch of records"""
        start_time = time.time()

        try:
            processed_records = []

            for record in batch:
                record.processing_status = ProcessingStatus.PROCESSING

                # Apply all processors
                for processor in self.processors:
                    try:
                        record = processor.process(record)
                    except Exception as e:
                        record.processing_status = ProcessingStatus.FAILED
                        record.error_message = f"Processing error: {e!s}"
                        break

                if record.processing_status != ProcessingStatus.FAILED:
                    record.processing_status = ProcessingStatus.COMPLETED
                    processed_records.append(record)

            # Write to all sinks
            for sink in self.data_sinks:
                try:
                    asyncio.run(sink.write_data(processed_records))
                except Exception as e:
                    logger.error(f"Error writing to sink: {e!s}")

            # Update metrics
            processing_time = time.time() - start_time
            self.metrics.records_processed += len(processed_records)
            self.metrics.records_failed += (len(batch) - len(processed_records))

            # Update average latency
            if self.metrics.records_processed > 0:
                self.metrics.average_latency = (
                    (self.metrics.average_latency * (self.metrics.records_processed - len(processed_records)) +
                     processing_time * len(processed_records)) / self.metrics.records_processed
                )

            logger.info(f"Thread {thread_id}: Processed batch of {len(batch)} records in {processing_time:.2f}s")

        except Exception as e:
            logger.error(f"Error processing batch in thread {thread_id}: {e!s}")

    def _metrics_loop(self):
        """Metrics collection and health monitoring loop"""
        while self.is_running:
            try:
                # Calculate throughput (records per second)
                current_time = time.time()
                time_diff = current_time - self.metrics.last_updated.timestamp()

                if time_diff > 0:
                    self.metrics.total_throughput = self.metrics.records_processed / time_diff

                # Calculate current load
                self.metrics.current_load = min(1.0, self.processing_queue.qsize() / self.max_queue_size)

                # Calculate pipeline health
                if self.metrics.records_processed > 0:
                    success_rate = 1.0 - (self.metrics.records_failed /
                                        (self.metrics.records_processed + self.metrics.records_failed))
                    self.metrics.pipeline_health = success_rate * (1.0 - self.metrics.current_load * 0.5)

                self.metrics.last_updated = datetime.now()

                # Log metrics periodically
                if int(current_time) % 30 == 0:  # Every 30 seconds
                    self._log_metrics()

                time.sleep(5)  # Update metrics every 5 seconds

            except Exception as e:
                logger.error(f"Error in metrics loop: {e!s}")

    def _log_metrics(self):
        """Log current pipeline metrics"""
        logger.info(f"Pipeline Metrics - "
                   f"Processed: {self.metrics.records_processed}, "
                   f"Failed: {self.metrics.records_failed}, "
                   f"Throughput: {self.metrics.total_throughput:.2f} records/sec, "
                   f"Latency: {self.metrics.average_latency:.3f}s, "
                   f"Load: {self.metrics.current_load:.2f}, "
                   f"Health: {self.metrics.pipeline_health:.2f}")

    def get_metrics(self) -> dict[str, Any]:
        """Get current pipeline metrics"""
        return {
            "records_processed": self.metrics.records_processed,
            "records_failed": self.metrics.records_failed,
            "total_throughput": self.metrics.total_throughput,
            "average_latency": self.metrics.average_latency,
            "current_load": self.metrics.current_load,
            "pipeline_health": self.metrics.pipeline_health,
            "queue_size": self.processing_queue.qsize(),
            "active_sources": len([s for s in self.data_sources.values() if s.is_active]),
            "last_updated": self.metrics.last_updated.isoformat()
        }

    def get_status(self) -> dict[str, Any]:
        """Get overall pipeline status"""
        return {
            "is_running": self.is_running,
            "data_sources": {
                source_id: {
                    "is_active": source.is_active,
                    "metrics": source.metrics
                }
                for source_id, source in self.data_sources.items()
            },
            "processors_count": len(self.processors),
            "sinks_count": len(self.data_sinks),
            "pipeline_metrics": self.get_metrics()
        }


# Example usage and testing
if __name__ == "__main__":

    # Initialize pipeline
    config = {
        "batch_size": 50,
        "processing_interval": 2.0,
        "processing_threads": 2,
        "max_queue_size": 1000
    }

    pipeline = RealTimeDataPipeline(config)

    # Add data sources
    api_source = APIDataSource("transactions_api", {
        "endpoint": "https://api.example.com/transactions",
        "poll_interval": 10
    })

    db_source = DatabaseDataSource("inventory_db", {
        "connection_string": "postgresql://user:pass@localhost/db",
        "query": "SELECT * FROM inventory WHERE updated_at > NOW() - INTERVAL 1 HOUR",
        "poll_interval": 30
    })

    pipeline.add_data_source(api_source)
    pipeline.add_data_source(db_source)

    # Start pipeline
    pipeline.start()

    try:
        # Let it run for a while
        time.sleep(60)

        # Check status
        status = pipeline.get_status()
        print("\nPipeline Status:")
        print(json.dumps(status, indent=2, default=str))

    finally:
        # Stop pipeline
        pipeline.stop()
        print("\nPipeline stopped")
