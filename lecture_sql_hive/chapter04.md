# **Chapter 4: Hive Partitioning & Parquet Writing Explained**

In previous chapters, we examined how to extract and transform data from a relational database—either a slice for a particular day (`overwrite_date`) or all rows—before **loading** them as **Parquet** files in a **Hive-partitioned** layout. This chapter explains **what Hive partitioning is**, why it’s beneficial, and how **PyArrow** helps us write partitioned data effectively.

---

## **4.1 What Is Hive Partitioning?**

**Hive partitioning** is an organizational strategy traditionally used in Apache Hive but now broadly adopted by various data systems (Spark, Trino, DuckDB, etc.). It structures your dataset as a **hierarchy of directories** based on **partition columns** (e.g., `year`, `month`, `day`). Each partition column becomes part of the directory name:

```
root_path/
└─ year=2025/
   └─ month=02/
      └─ day=14/
         └─ [Parquet files]
```

### **4.1.1 Key Benefits**
1. **Partition Pruning**: Downstream queries can skip entire directories if they don’t match the filter condition (e.g., skip all data outside `year=2025`).  
2. **Scalability**: Splitting data across many small directories can be more efficient than having one large file—especially for time-based queries.  
3. **Simplicity for Incremental Loads**: You can insert or overwrite a single day’s partition without touching other directories.

### **4.1.2 Typical Partition Columns**
- **Temporal**: `year`, `month`, `day` (the most common).  
- **Domain-Specific**: For example, `region`, `product_category`, or `user_group`.

---

## **4.2 Why Parquet Format?**

**Parquet** is a columnar file format often used in modern data platforms. It provides:

1. **Columnar Compression**: Storing columns together can greatly reduce storage size for highly repetitive or numeric data.  
2. **Predicate Pushdown**: Many engines can read only the needed columns or row groups, improving performance.  
3. **Schema Evolution**: Parquet can handle added or removed columns more gracefully than some other formats.

Combining **Hive partitioning** with **Parquet** is a **best-practice** approach in big data pipelines.

---

## **4.3 How Our ETL Code Writes Partitioned Parquet**

When calling:

```python
pq.write_to_dataset(
    table=table,
    root_path=root_path,
    partition_cols=["year", "month", "day"]
)
```

PyArrow automatically:
1. Looks at the columns `["year", "month", "day"]` in the `table`.  
2. Groups rows based on unique combinations of these columns.  
3. Creates subdirectories under `root_path` named `year=XXXX/month=XX/day=XX`.  
4. Places Parquet files containing only the data relevant to each subdirectory.

### **4.3.1 Overwriting a Partition**

If you want to **overwrite** an existing partition (e.g., `year=2025/month=02/day=14`), you need to **clear** it manually first. That’s why we included logic in `run_etl_join()` to remove any existing files in that directory if `overwrite_date` is provided.

### **4.3.2 Appending to a Partition**

If you **omit** the overwrite step and run the same ETL pipeline for the same date, PyArrow writes additional files to that partition. This is called “append mode.” You might do this if your data trickles in throughout the day and you want to accumulate it.

---

## **4.4 Directory Structures and File Organization**

### **4.4.1 Example Layout**

Assume you run the pipeline for three separate days: `2025-02-14`, `2025-02-15`, and `2025-02-17`. Your directory tree might look like this:

```
root_path/
└─ year=2025/
   ├─ month=02/
   │  ├─ day=14/
   │  │  ├─ part-0.parquet
   │  │  └─ part-1.parquet
   │  ├─ day=15/
   │  │  └─ part-0.parquet
   │  └─ day=17/
   │     └─ part-0.parquet
```

Each day’s data is cleanly separated. Some days might have multiple Parquet files (`part-0.parquet`, `part-1.parquet`, etc.) if you used chunked processing or multiple runs.

### **4.4.2 Handling Mixed Schema Over Time**

- **Added Columns**: If you later add a `discount_code` column in the DB and then run the ETL again, new partitions can contain this column while old ones do not. Most engines (Spark, DuckDB, etc.) can handle “schema evolution” by treating missing columns as null.  
- **Removed Columns**: Similarly, if a column is dropped, older partitions may still have it. Queries must handle these differences gracefully.

---

## **4.5 Performance & Best Practices**

1. **Fewer, Larger Partitions** vs. **Many Tiny Partitions**  
   - Too many small files can degrade performance. If your data for a single day is trivially small, consider grouping multiple days into a bigger partition (weekly or monthly).  
   - Conversely, if you have massive data for each day, daily partitioning can help speed up queries focusing on a single day.

2. **Metadata Caching / Indexes**  
   - Some engines keep a metadata cache of file locations for quick partition discovery. It’s helpful to refresh this cache if you’re frequently overwriting partitions.

3. **Consistent Schema**  
   - Avoid drastically changing column types across runs. If you do need to change them (e.g., from integer to float), ensure you handle it consistently in the ETL logic (e.g., always cast to float).  
   - Using `dtype_backend="pyarrow"` helps maintain consistency across different increments of data.

4. **Compression & Encoding**  
   - Parquet automatically compresses data columns. You can tweak settings (e.g., `snappy`, `gzip`, or `zstd` compression) to optimize performance and size.

---

## **4.6 Illustrative Example**

Here’s a **concise example** of reading data from your local DB (for a single date), then writing it to a partitioned Parquet dataset:

```python
import os
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

def simple_run_etl(engine, root_path, overwrite_date=None):
    base_query = """
    SELECT
        r.rent_id,
        r.user_id,
        r.bike_id,
        r.rent_start,
        r.rent_end,
        r.rent_cost,
        u.name AS user_name,
        u.age,
        u.email,
        b.model AS bike_model,
        b.price AS bike_price,
        b.type AS bike_type,
        TO_CHAR(r.rent_start, 'YYYY-MM-DD') AS rent_date
    FROM rent r
    JOIN "user" u ON r.user_id = u.user_id
    JOIN bike b ON r.bike_id = b.bike_id
    """

    if overwrite_date:
        query = base_query + f"\nWHERE TO_CHAR(r.rent_start, 'YYYY-MM-DD') = '{overwrite_date}'"
    else:
        query = base_query

    df_join = pd.read_sql_query(query, engine, dtype_backend="pyarrow")

    # Add partition columns
    df_join["year"] = pd.to_datetime(df_join["rent_start"]).dt.strftime("%Y")
    df_join["month"] = pd.to_datetime(df_join["rent_start"]).dt.strftime("%m")
    df_join["day"] = pd.to_datetime(df_join["rent_start"]).dt.strftime("%d")

    # Overwrite logic
    if overwrite_date:
        y, m, d = overwrite_date.split("-")
        part_dir = os.path.join(root_path, f"year={y}", f"month={m}", f"day={d}")
        if os.path.exists(part_dir):
            # Clear existing files
            for filename in os.listdir(part_dir):
                file_path = os.path.join(part_dir, filename)
                if os.path.isfile(file_path):
                    os.remove(file_path)

    # Write to Parquet
    table = pa.Table.from_pandas(df_join, preserve_index=False)
    pq.write_to_dataset(
        table=table,
        root_path=root_path,
        partition_cols=["year", "month", "day"]
    )
```

**Key aspects**:
- **Partition Directory**: `year=YYYY/month=MM/day=DD`.  
- **Optional Overwrite**: If `overwrite_date` is provided, we explicitly remove older files in that subdirectory.  
- **Parquet**: We rely on **PyArrow**’s `write_to_dataset()` to do the partitioning.

---

## **4.7 Chapter Summary**

1. **Hive Partitioning**: A folder-based strategy that speeds up queries by partition columns, commonly `year/month/day`.  
2. **Parquet Format**: Columnar storage that offers high compression, fast queries, and schema evolution.  
3. **ETL Flow**: We run a SQL-based Extract, add partition columns, optionally clear existing data if we’re overwriting, and write partitioned Parquet using PyArrow.  
4. **Performance Considerations**: Use partitioning levels that align with your data volume and query patterns. Monitor for too many small files or inconsistent schemas.  
5. **Next Steps**: In Chapter 5, we’ll **test** our pipeline by reading the Parquet files using DuckDB SQL, PyArrow, and pandas, verifying that the **ETL** process correctly captured the data and partition structure.