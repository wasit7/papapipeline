# **Chapter 3: Improving the Tested ETL Code**

In previous chapters, we established the need for **SQL-based ETL** (Extract, Transform, Load) and how using an **overwrite date** (or `etl_date`) enables incremental data loads. We also discussed how `dtype_backend="pyarrow"` helps preserve data types during the **Extract** phase. In this chapter, we’ll **refine** the ETL code to make it **simpler**, easier to maintain, and more flexible.

---

## **3.1 Review of Existing ETL Code**

The existing function `run_etl_join()` does the following:

1. Builds a SQL query joining three tables (`rent`, `user`, `bike`).  
2. Optionally filters results by `overwrite_date`.  
3. Reads data from the database into a pandas DataFrame (Arrow-backed).  
4. Adds partition columns (`year`, `month`, `day`) based on `rent_start`.  
5. Clears any existing partition directory if `overwrite_date` was specified.  
6. Writes the final dataset to a Hive-partitioned Parquet layout.

While effective, the function can be **condensed**. We’ll eliminate repetitive query code and reduce some of the branching.

---

## **3.2 Simplified `run_etl_join()` Function**

Below is a **streamlined** version of the function. The main changes are:

- **Base Query Construction**: We define a single query template and apply the optional filter if `overwrite_date` is provided.  
- **Shared Logic**: Only one code path for partition directories, rather than duplicating queries.  
- **Parameterization**: Introduced a `date_col` parameter (default: `"rent_start"`) to show how you might generalize for a different column if needed.

```python
import os
import shutil
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

def run_etl_join(
    engine,
    root_path,
    partition_col="rent_date",
    date_col="rent_start",
    overwrite_date=None
):
    """
    Run ETL by:
      1. Executing a join query across rent, user, and bike tables.
      2. Optionally filtering on a specific day if overwrite_date is provided.
      3. Adding partition columns (year, month, day) based on date_col.
      4. Clearing the partition directory if overwrite_date is provided.
      5. Writing the joined result to a Hive-partitioned Parquet dataset.
    """

    # Build the base SQL query
    base_query = f"""
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
        TO_CHAR(r.{date_col}, 'YYYY-MM-DD') AS {partition_col}
    FROM rent r
    JOIN "user" u ON r.user_id = u.user_id
    JOIN bike b ON r.bike_id = b.bike_id
    """

    # If overwrite_date is provided, add a WHERE clause to filter on that date
    if overwrite_date:
        query = base_query + f"\nWHERE TO_CHAR(r.{date_col}, 'YYYY-MM-DD') = '{overwrite_date}'"
    else:
        query = base_query  # no filter, loads everything

    # Extract step: read data from DB into a pandas DataFrame (Arrow-backed)
    df_join = pd.read_sql_query(query, engine, dtype_backend="pyarrow")

    # Transform step: add partition columns
    df_join["year"] = pd.to_datetime(df_join[date_col]).dt.strftime("%Y")
    df_join["month"] = pd.to_datetime(df_join[date_col]).dt.strftime("%m")
    df_join["day"] = pd.to_datetime(df_join[date_col]).dt.strftime("%d")

    # If overwriting, clear the existing partition folder
    if overwrite_date:
        y, m, d = overwrite_date.split("-")
        partition_dir = os.path.join(root_path, f"year={y}", f"month={m}", f"day={d}")
        if os.path.exists(partition_dir):
            print(f"Clearing existing data in: {partition_dir}")
            for entry in os.scandir(partition_dir):
                if entry.is_file() or entry.is_symlink():
                    os.remove(entry.path)
                elif entry.is_dir():
                    shutil.rmtree(entry.path)
            print(f"Partition cleared: {partition_dir}")
        else:
            print(f"Partition directory does not exist yet: {partition_dir}")

    # Convert DataFrame to a PyArrow Table for Parquet writing
    table = pa.Table.from_pandas(df_join, preserve_index=False)

    # Load step: write the partitioned Parquet dataset
    pq.write_to_dataset(
        table=table,
        root_path=root_path,
        partition_cols=["year", "month", "day"]
    )
    print("ETL join complete. Data partitioned at:", root_path)
```

### **3.2.1 Key Points in the Simplified Function**

1. **Single SQL Query Template**  
   - The function defines `base_query` only once, avoiding duplication.  
   - The optional `WHERE` clause is appended if `overwrite_date` is set.

2. **Date Flexibility**  
   - We introduced `date_col="rent_start"` so you can change which column to base partitions on if your requirements shift.

3. **Condensed Partition Logic**  
   - The partition-clearing logic is only triggered if `overwrite_date` is set.  
   - A simple `if ...:` check, rather than building two separate queries or code paths.

4. **Arrow Dtypes & Partition Columns**  
   - Still uses `dtype_backend="pyarrow"` so numeric or string anomalies are more gracefully handled.  
   - The partition columns (`year`, `month`, `day`) are appended to the DataFrame from the same column (`date_col`).

5. **Logging**  
   - Some brief print statements inform you when partition clearing starts and finishes.

---

## **3.3 Additional Improvements**

While the simplified function covers the essentials, consider these optional enhancements:

1. **Data Validation**  
   - You could automatically detect if columns like `rent_cost` contain invalid strings (e.g., `"error"`) and convert them to a numeric type or log them.  
   - Example:
     ```python
     df_join["rent_cost"] = pd.to_numeric(df_join["rent_cost"], errors="coerce")
     ```

2. **Logging & Error Handling**  
   - Swap out `print(...)` for Python’s built-in `logging` module to manage log levels (INFO, WARNING, ERROR).  
   - Wrap the entire process in a `try/except` to handle DB or filesystem errors gracefully.

3. **Configuration Files**  
   - Instead of hardcoding `root_path` or `date_col`, store these in a config file (YAML, JSON) so you can switch them quickly without editing code.

4. **Chunked Reads for Large Tables**  
   - If data volumes become huge, use a chunk-based approach for reading or writing. For instance:
     ```python
     for chunk in pd.read_sql_query(query, engine, chunksize=100000):
         # process and write chunk
     ```
   - Then gather and combine them in Arrow or keep separate files under the same partition.

---

## **3.4 Summary and Next Steps**

By simplifying `run_etl_join()`, we have:

- A **clear, concise** pipeline that handles the **Extract** (via SQL), **Transform** (adding partition columns, optional cleaning), and **Load** (writing Hive-partitioned Parquet).  
- Reduced code duplication, making it easier to **maintain** and **extend**.  
- Retained essential behavior (e.g., clearing the partition directory if it exists and using `dtype_backend="pyarrow"`).

In the **next chapters**, we’ll delve deeper into **Hive partitioning** specifics and show **how to test** each step by reading the resulting Parquet data with **DuckDB**, **PyArrow**, and **pandas**. This ensures your entire pipeline—**from DB to data lake**—is both **correct** and **reproducible**.