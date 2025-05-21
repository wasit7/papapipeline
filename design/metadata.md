
# Metadata Design Specification for Data Zones

## Overview
This specification defines metadata for each data zone (Landing, Staging, Integration, Data Mart) in a data architecture, complementing Kedro’s catalog and lineage features with zone-specific details like quality, history, and performance metrics. Metadata is stored in lakeFS and versioned for auditability.

---

## 1. Landing Zone Metadata
**Purpose**: Captures raw data details and initial quality from the source.  
**Fields**:  
- **Dataset ID**: `string` (e.g., `erp_raw_001`) — Unique identifier.  
- **Name**: `string` (e.g., `erp_raw`) — Human-readable name.  
- **Source**:  
  - **Type**: `string` (e.g., `SQL`) — Source type.  
  - **Name**: `string` (e.g., `ERP`) — Source name.  
- **Size**: `integer` (e.g., `5242880` bytes) — Data size.  
- **Row Count**: `integer` (e.g., `15000`) — Number of rows.  
- **Ingestion Timestamp**: `string` (e.g., `2025-04-26T10:00:00Z`) — Ingestion time.  
- **Quality Metrics**:  
  - **Duplicate Count**: `integer` (e.g., `200`) — Count of row-level duplicates.  


**Constraints**: All fields required; `Schema Compliance` must be 0-100.


### example code
```python
import pandas as pd

def calculate_duplicate_count(df):
    # Create a hash of all columns for each row
    df['row_hash'] = df.apply(lambda row: hash(tuple(row)), axis=1)
    # Group by hash and count occurrences
    duplicate_counts = df['row_hash'].value_counts()
    # Sum duplicates (exclude the first occurrence of each unique row)
    duplicate_count = duplicate_counts[duplicate_counts > 1].sum() - duplicate_counts[duplicate_counts > 1].count()
    return duplicate_count

    
```
---

## 2. Staging Zone Metadata
**Purpose**: Tracks data quality and business rules after initial processing.  
**Fields**:  
- **Dataset ID**: `string` (e.g., `erp_staged_001`) — Unique identifier.  
- **Name**: `string` (e.g., `erp_staged`) — Human-readable name.  
- **Size**: `integer` (e.g., `4718592` bytes) — Data size.  
- **Row Count**: `integer` (e.g., `14500`) — Number of rows.  
- **Last Updated**: `string` (e.g., `2025-04-26T10:05:00Z`) — Last update time.  
- **Quality Metrics**:  
  - **Completeness**: `float` (e.g., `98.5`) — Non-null percentage.  
  - **Consistency**: `float` (e.g., `99.2`) — Schema check pass rate.  
  - **Validation Failures**: `integer` (e.g., `300`) — Failed validation count.
  - **Schema Compliance**: `float` (e.g., `99.8`) — Schema match percentage.  
- **Business Rules Applied**: `array` (e.g., `["revenue_non_negative"]`) — Rules applied.  

**Constraints**: All fields required; quality metrics must be 0-100.

---

## 3. Integration Zone Metadata
**Purpose**: Records historical tracking and integration quality.  
**Fields**:  
- **Dataset ID**: `string` (e.g., `integrated_sales_001`) — Unique identifier.  
- **Name**: `string` (e.g., `integrated_sales`) — Human-readable name.  
- **Size**: `integer` (e.g., `8388608` bytes) — Data size.  
- **Row Count**: `integer` (e.g., `28000`) — Number of rows.  
- **Last Updated**: `string` (e.g., `2025-04-26T10:10:00Z`) — Last update time.  
- **History Metrics**:  
  - **SCD Type**: `string` (e.g., `Type 4`) — Slowly Changing Dimension type.  
  - **History Records**: `integer` (e.g., `50000`) — Total historical records.
  - **Records Overtime**: table with columns; datetime and number of records in the integration zone.  
  - **New Records**: `integer` (e.g., `28000`) — New records added.  
  - **Updated Records**: `integer` (e.g., `1500`) — Updated records.  
- **Quality Metrics**:  
  - **Deduplication Rate**: `float` (e.g., `99.5`) — Deduplication success rate.  
  - **Join Accuracy**: `float` (e.g., `98.8`) — Join operation accuracy.  

**Constraints**: All fields required; quality metrics must be 0-100.

---

## 4. Data Mart Zone Metadata
**Purpose**: Focuses on analytics performance and accessibility.  
**Fields**:  
- **Dataset ID**: `string` (e.g., `sales_mart_001`) — Unique identifier.  
- **Name**: `string` (e.g., `sales_mart`) — Human-readable name.  
- **Size**: `integer` (e.g., `7340032` bytes) — Data size.  
- **Row Count**: `integer` (e.g., `27500`) — Number of rows.  
- **Last Updated**: `string` (e.g., `2025-04-26T10:15:00Z`) — Last update time.  
- **Analytics Metrics**:  
  - **Partitioned By**: `array` (e.g., `["year", "region"]`) — Partition keys.  
  - **Avg Query Time**: `integer` (e.g., `150` ms) — Average query time.  
- **Quality Metrics**:  
  - **Anomaly Rate**: `float` (e.g., `0.01`) — Anomaly percentage.  
- **Accessibility**:  
  - **Consumers**: `array` (e.g., `["Grafana", "Micro-services"]`) — Downstream tools.  
  - **Last Accessed**: `string` (e.g., `2025-04-26T10:20:00Z`) — Last access time.  

**Constraints**: All fields required; `Anomaly Rate` must be 0-100.

---

## Storage and Versioning
- **Storage**: Stored in lakeFS at `/metadata/<zone>/<dataset_id>.md`.  
- **Versioning**: Managed via lakeFS commits for auditability.

---

## Notes
- Excludes Kedro-tracked fields (e.g., `path`, `format`, `schema`, lineage details).  
- Focuses on zone-specific quality, history, and performance metrics.
