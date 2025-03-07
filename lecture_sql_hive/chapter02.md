# **Chapter 2: Introduction to SQL-Based ETL & the Overwrite Date Concept**

In the previous chapter, we discussed why synthetic data is essential and how to store it in a relational database for testing. Now it’s time to explore one of the most popular data processing patterns: **SQL-based ETL** (Extract, Transform, Load). SQL-based ETL pipelines are common in analytics and data engineering because they leverage **set-based operations**, which can be more efficient and simpler to manage for many transformations. Here, we’ll focus on how SQL queries, combined with an **overwrite date** (or `etl_date`), enable **incremental** or **daily** loading of data into your target system—often a **data lake**.

---

## **2.1 The Basics of SQL-Based ETL**

### **2.1.1 Extract**
- **Definition**: The “Extract” phase pulls data from source systems—in our scenario, the relational DB that holds your synthetic dataset.  
- **SQL Query**: Typically includes `SELECT` statements with any necessary joins or filters to isolate the data you want.  
- **Connection**: Uses a database engine driver (e.g., `psycopg2` for PostgreSQL, ODBC for MSSQL) to run the SQL and retrieve results in Python.

### **2.1.2 Transform**
- **Within SQL**: Joins between tables (like `user`, `bike`, and `rent`) can quickly transform data—merging them into a single view or dataset.  
- **Supplementary Logic**: You may also do certain validations or conversions in Python after reading the results (e.g., cleaning up “error” values).  
- **Column Selection**: You can rename or cast columns directly in the `SELECT` statement (e.g., `TO_CHAR(r.rent_start, 'YYYY-MM-DD')`).

### **2.1.3 Load**
- **Destination**: For many modern pipelines, the load target is a data lake, typically written in **Parquet** format.  
- **PyArrow & Parquet**: Once you’ve transformed your data into a pandas DataFrame or a PyArrow Table, you can easily write it to partitioned Parquet files.  
- **Incremental Approach**: Often, you only load new data (e.g., for a single day) into the data lake to keep your pipeline runs efficient.

---

## **2.2 Why Use an Overwrite Date (`etl_date`)?**

### **2.2.1 Incremental & Partitioned Loads**
- **Daily or Periodic Slices**: By specifying a single date (e.g., `"2025-02-14"`) in the `WHERE` clause, the SQL query extracts only the records for that day.  
- **Partition Pruning**: Downstream tools can quickly read or skip entire partitions if they only need certain dates.  
- **Efficiency**: Instead of reading the entire dataset each time, you focus on a small slice that changed or was newly generated.

### **2.2.2 Overwriting vs. Appending**
- **Overwrite**: If the pipeline detects that a partition for `"2025-02-14"` already exists, it can **clear** that folder to avoid duplication before writing fresh data. This ensures no overlapping or conflicting rows.  
- **Append**: If you wish to accumulate data without wiping old files, you can simply add new Parquet files under the same partition.  
- **Choose the Right Mode**: The “overwrite date” concept is powerful for daily snapshots or data corrections. Appending is more common for streaming or event-based systems.

### **2.2.3 Error Correction & Re-Processing**
- **Fixing Mistakes**: If you discover a data error for `"2025-02-14"`, you can rerun the pipeline with that date. The pipeline will overwrite that day’s partition, ensuring the data lake is consistent.  
- **ETL Debugging**: By focusing on one day, you can debug data anomalies faster (e.g., “cost” has an “error” string instead of a number).

---

## **2.3 Using `dtype_backend="pyarrow"` to Preserve Types**

### **2.3.1 Mixed Data Types in Columns**
- **Common Issue**: Real-world data can have columns that are mostly numeric but occasionally contain invalid strings (like `"error"`). Pandas often defaults to an `object` column, leading to confusion and potential performance issues.  
- **PyArrow Backend**: When you call  
  ```python
  pd.read_sql_query(query, engine, dtype_backend="pyarrow")
  ```  
  you encourage pandas to store columns as **Arrow data types** instead of standard NumPy dtypes. This often yields better precision and consistent typing.

### **2.3.2 Advantages of Arrow Dtypes**
- **Efficient Memory Usage**: Arrow’s columnar format can be more memory-friendly.  
- **Consistency**: Data that might typically end up as “object” type may remain in a well-defined Arrow type, even if it includes null or edge values.  
- **Downstream Compatibility**: If you convert to a PyArrow Table, you don’t lose type information when you later write to Parquet.

### **2.3.3 Caveats**
- **Truly Invalid Data**: If “error” is neither convertible to numeric nor intended to be a string, you still need cleaning logic.  
- **Conversion**: You might do:  
  ```python
  df["rent_cost"] = pd.to_numeric(df["rent_cost"], errors="coerce")
  ```  
  to transform invalid entries to `NaN`.

---

## **2.4 Example: A Single-Day ETL Job**

1. **Construct the SQL Query**  
   ```sql
   SELECT r.rent_id, r.user_id, r.bike_id,
          r.rent_start, r.rent_end, r.rent_cost,
          u.name AS user_name, u.age, u.email,
          b.model AS bike_model, b.price AS bike_price, b.type AS bike_type,
          TO_CHAR(r.rent_start, 'YYYY-MM-DD') AS rent_date
   FROM rent r
   JOIN "user" u ON r.user_id = u.user_id
   JOIN bike b ON r.bike_id = b.bike_id
   WHERE TO_CHAR(r.rent_start, 'YYYY-MM-DD') = '2025-02-14';
   ```
   - The `WHERE` clause filters by the chosen date.  
   - The `TO_CHAR` function ensures consistent string formatting.

2. **Read into Pandas**  
   ```python
   df_join = pd.read_sql_query(query, engine, dtype_backend="pyarrow")
   ```
   - This gives you a DataFrame (`df_join`) with Arrow-based columns.  
   - You can verify the schema via `df_join.info()`.

3. **Add Partition Columns**  
   ```python
   df_join["year"] = pd.to_datetime(df_join["rent_start"]).dt.strftime("%Y")
   df_join["month"] = pd.to_datetime(df_join["rent_start"]).dt.strftime("%m")
   df_join["day"] = pd.to_datetime(df_join["rent_start"]).dt.strftime("%d")
   ```
   - These columns will guide the folder structure (e.g., `year=2025/month=02/day=14`).

4. **Write to Partitioned Parquet (Overwrite)**  
   ```python
   table = pa.Table.from_pandas(df_join, preserve_index=False)
   pq.write_to_dataset(
       table,
       root_path="path/to/datalake",
       partition_cols=["year", "month", "day"]
   )
   ```
   - If you detect that `year=2025/month=02/day=14` already exists, clear it first to avoid duplicates.

---

## **2.5 Practical Considerations & Next Steps**

### **2.5.1 Handling Larger Data**
- If your data volumes grow, consider **chunked reading** from the DB and writing multiple Parquet files for each partition to avoid excessive memory usage.

### **2.5.2 Testing & Debugging**
- Always run a row-count check or sample check (e.g., `df_join.head()`) after you read from the DB. If the row count doesn’t match expectations, debug the query or the date filter.

### **2.5.3 Broader Scheduling & Automation**
- Tools like Airflow, Luigi, or Cron can orchestrate these daily ETL runs.  
- Each run can target a new “overwrite date,” or you can pass the current date dynamically.

### **2.5.4 Potential for Data Validation**
- If you find columns that can have invalid data (“error”), build a **validation step** that logs or corrects these anomalies. Arrow-backed DataFrames make it easier to spot them.

---

## **2.6 Key Takeaways**

1. **SQL-Based ETL**: A powerful approach for combining data from multiple tables and applying initial transformations in a single query.  
2. **Incremental Loading with Overwrite Date**: Filtering by a specific date (e.g., `WHERE to_char(r.rent_start, 'YYYY-MM-DD') = '{overwrite_date}'`) enables smaller, more manageable loads.  
3. **`dtype_backend="pyarrow"`**: Preserves column types better than classic NumPy dtypes, reducing “object” columns and improving integration with Parquet.  
4. **Overwrite vs. Append**: Overwrite erases old partition data, while append adds new files. Choose the mode that fits your pipeline’s logic.  
5. **Next Steps**: In the following chapters, we’ll delve into **Hive partitioning, Parquet writing modes,** and **testing** these pipelines (both the ETL process and reading Parquet files with DuckDB, PyArrow, and pandas).