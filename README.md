# Azure Data Engineering Portfolio

A hands-on portfolio documenting my transition into **Azure Data Engineering**, with an emphasis on production-style data platforms, distributed processing, reliability, performance, and modern cloud architecture.

The repository combines:

- Enterprise Data Engineering projects
- Azure architecture and implementation patterns
- SQL and PySpark problem solving
- Databricks and Spark internals
- Incremental loading and CDC
- Streaming data pipelines
- Metadata-driven frameworks
- Data quality and validation
- Failure recovery and idempotency
- Spark performance engineering
- Selected GenAI learning and experiments

---

# Career Transition Focus

The primary objective of this portfolio is to demonstrate practical Data Engineering capability through realistic enterprise scenarios rather than isolated tutorials.

The engineering approach used throughout the projects is:

```text
Business Problem
      ↓
Data / System Constraint
      ↓
Architecture Decision
      ↓
Implementation
      ↓
Failure / Edge Case
      ↓
Recovery Strategy
      ↓
Validation & Performance
```

The goal is to demonstrate not only **how** a technology works, but also **why** a particular design is appropriate and what happens when the system fails.

---

# Projects

## Project 01 — Enterprise Retail Data Platform

A production-style retail data platform designed around a simulated enterprise OLTP source.

Key areas:

- SQL Server source system
- Large-scale synthetic data generation
- Incremental loading
- Composite watermarks
- CDC
- Idempotent processing
- Delta-oriented data architecture
- Data quality validation
- Audit and control tables
- Failure simulation and restartability
- Spark performance engineering

Project location:

```text
projects/project-01-enterprise-retail-data-platform/
```

---

## Project 02 — Real-Time E-Commerce Analytics Platform

Planned streaming project covering:

- Event-driven architecture
- Azure Event Hubs
- Databricks Structured Streaming
- Late-arriving events
- Streaming checkpoints
- Deduplication
- Window aggregations
- Bronze / Silver / Gold processing
- Streaming failure recovery

Project location:

```text
projects/project-02-real-time-ecommerce-platform/
```

---

## Project 03 — Enterprise Metadata-Driven Data Platform

Planned reusable ingestion framework covering:

- Metadata-driven ingestion
- Parameterized pipelines
- Dynamic source and target configuration
- Full and incremental loading
- Watermark management
- Data quality rules
- Audit logging
- Retry and error handling
- Idempotent replay

Project location:

```text
projects/project-03-metadata-driven-data-platform/
```

---

# Technology Areas

| Area | Technologies / Concepts |
|---|---|
| SQL | SQL Server, joins, aggregations, analytical SQL |
| Programming | Python, PySpark |
| Orchestration | Azure Data Factory |
| Storage | ADLS Gen2, Parquet, Delta Lake |
| Processing | Apache Spark, Databricks |
| Data Movement | Incremental loading, CDC, watermarks |
| Reliability | Idempotency, checkpoints, retries, recovery |
| Streaming | Event Hubs, Structured Streaming |
| Governance | Metadata, audit, data quality |
| Performance | Partitioning, shuffle, skew, broadcast, Spark UI |
| Analytics | Gold-layer modeling, Power BI |
| GenAI | RAG, embeddings, tool calling, agents |

---

# Repository Structure

```text
azure-data-engineering-portfolio/
│
├── README.md
│
├── projects/
│   ├── project-01-enterprise-retail-data-platform/
│   ├── project-02-real-time-ecommerce-platform/
│   └── project-03-metadata-driven-data-platform/
│
├── Day-01/ ...
├── Day-02/ ...
├── ...
│
└── resources/
    ├── architecture/
    ├── diagrams/
    └── references/
```

The existing learning notes and GenAI material remain part of the broader learning journey, while the `projects/` directory is the primary portfolio section for Data Engineering work.

---

# Engineering Philosophy

I focus on understanding systems through failure modes and trade-offs:

```text
What problem are we solving?
        ↓
Why does the problem exist?
        ↓
What happens at scale?
        ↓
Where can the pipeline fail?
        ↓
How do we make processing idempotent?
        ↓
How do we recover safely?
        ↓
How do we prove the result is correct?
```

This repository is therefore intended to show **engineering reasoning, implementation, testing, and operational thinking** rather than only completed code.
