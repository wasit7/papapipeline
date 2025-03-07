# **Chapter 5: Testing the ETL & Reading Data**

In the previous chapters, you learned how to **extract** data from a relational database using SQL, **transform** it into a partitioned format with PyArrow, and **load** that data as Hive-partitioned Parquet files. Now, it’s time to verify that each step of the pipeline works as intended. This chapter focuses on **testing** the ETL process—both in terms of **data correctness** (row counts, column types) and **readability** (using DuckDB SQL, PyArrow, and pandas to query the resulting Parquet files).

---

## **5.1 Why Testing Matters in ETL**

1. **Data Accuracy**: Ensuring the final Parquet files match the expected row counts and column values from the source DB.  
2. **Schema Consistency**: Verifying that the data types (numeric, string, etc.) remain correct, especially if you’re using `dtype_backend="pyarrow"`.  
3. **Partition Validation**: Checking that the partition directories (`year=YYYY/month=MM/day=DD`) contain the correct data and have no duplicates if you’ve overwritten any day.  
4. **Regression Prevention**: Catching issues early before they propagate into production or upstream analytics.

---

## **5.2 Testing the ETL Step-by-Step**

### **5.2.1 Row Count & Sample Check**

A quick test involves **comparing**:

- **Source**: A simple SQL count against the relational DB.
  ```sql
  SELECT COUNT(*) FROM rent 
  WHERE TO_CHAR(rent_start, 'YYYY-MM-DD') = '2025-02-14';
  ```
- **Target**: After running `run_etl_join(overwrite_date="2025-02-14")`, read the corresponding Parquet partition (e.g., `year=2025/month=02/day=14/`) and check the row count. If they match, it’s a good sign your ETL logic is consistent.

Additionally, you might select a small sample of rows from the DB (`SELECT * LIMIT 5`) and compare them to the top 5 rows read from the Parquet file.

### **5.2.2 Column Types & “Error” Values**

- **Spot-Check “rent_cost”**: If “rent_cost” had occasional string values like `"error"`, confirm how they appear in the final Parquet. Are they coerced to `NaN`, or are they left as strings?  
- **Validate Age**: If “age” is mostly numeric but sometimes “N/A,” ensure your approach (Arrow-based or a cleaning function) is consistent.

---

## **5.3 Reading the Parquet Files**

### **5.3.1 Using DuckDB SQL**

DuckDB is a fast, embedded SQL engine that can query Parquet directly. For example:

```python
import duckdb

# If your data is in 'datalake/' root folder
con = duckdb.connect()

# Query across all partitions under the root
df_duck = con.execute("""
    SELECT COUNT(*) AS row_count
    FROM 'datalake/**/*.parquet';
""").df()

print("DuckDB row count:", df_duck.loc[0, 'row_count'])
```

1. **Glob Pattern**: `'datalake/**/*.parquet'` matches all files in subdirectories, effectively reading from all partitions (year=..., month=..., day=...).  
2. **SQL**: You can run a standard SELECT, filter by partition columns (`WHERE year='2025'`), or do aggregates.

**Partition Column Usage**  
If you included partition columns (`year`, `month`, `day`) in the Parquet schema, you can filter:

```sql
SELECT *
FROM 'datalake/**/*.parquet'
WHERE year = '2025' AND month = '02';
```

### **5.3.2 Using PyArrow**

You can also read Parquet files in **Python** with PyArrow directly:

```python
import pyarrow.parquet as pq

# Read the entire dataset
dataset = pq.ParquetDataset("datalake/", use_legacy_dataset=False)
table = dataset.read()

print("PyArrow Table schema:")
print(table.schema)

# Convert to pandas for quick exploration
df_arrow = table.to_pandas()
print(df_arrow.info())
print(df_arrow.head())
```

- **`ParquetDataset`**: Gathers metadata across all partitions automatically, letting you read them as a single cohesive dataset.  
- **Schema Checking**: You can see if the partition columns (year, month, day) are indeed recognized.

### **5.3.3 Using pandas**

Finally, you can do a **direct pandas read** of a Parquet file or directory:

```python
import pandas as pd

df_pandas = pd.read_parquet("datalake/")
print(df_pandas.info())
print(df_pandas.head(10))
```

- **Directory Support**: `pd.read_parquet("datalake/")` will typically read all Parquet files in subdirectories, but depending on pandas/PyArrow version, you might need to ensure it supports partition discovery.  
- **Useful for Quick Validation**: `df_pandas.shape`, `df_pandas.describe()`, etc.

---

## **5.4 Recommended Validation Steps**

1. **Row Count Comparison**  
   - DB vs. Parquet, for a single date or a date range.  
   - Verify no duplicates if you overwrite partitions.

2. **Schema & Dtype Checks**  
   - `df_pandas.info()` or `df_arrow.schema` to ensure expected column types.  
   - If you see columns labeled “object” or unexpected conversions, investigate.

3. **Sample Data Consistency**  
   - Check that columns like `user_name`, `rent_cost`, and `bike_model` are populated as expected.  
   - Look for anomalies (e.g., “error” strings in numeric columns) and confirm your handling logic.

4. **Partition Directory Verification**  
   - Inspect your `datalake/year=2025/month=02/day=14` folder. Is it empty or does it contain `.parquet` files? If you overwrote it, confirm old files are gone.

5. **Cross-Date Queries**  
   - If you loaded multiple days (`2025-02-14`, `2025-02-15`, `2025-02-17`), run queries that span these days:
     ```sql
     SELECT year, month, day, COUNT(*) as rows
     FROM 'datalake/**/*.parquet'
     GROUP BY year, month, day
     ORDER BY year, month, day;
     ```
   - Validate each partition has the expected row counts.

---

## **5.5 Example Testing Scenario**

Below is an illustration of a **mini test script**:

```python
def test_etl_for_day(engine, root_path, test_date):
    # 1) Count rows in the DB
    sql_count = f"""
        SELECT COUNT(*) AS db_count
        FROM rent
        WHERE TO_CHAR(rent_start, 'YYYY-MM-DD') = '{test_date}';
    """
    db_count_df = pd.read_sql(sql_count, engine)
    db_count = db_count_df['db_count'][0]
    print(f"Rows in DB for {test_date}: {db_count}")

    # 2) Run ETL
    run_etl_join(engine, root_path, overwrite_date=test_date)

    # 3) Read Parquet with DuckDB
    con = duckdb.connect()
    parquet_count = con.execute(f"""
        SELECT COUNT(*) as parquet_count
        FROM '{root_path}/year={test_date[:4]}/month={test_date[5:7]}/day={test_date[8:]}/**.parquet'
    """).fetchone()[0]
    print(f"Rows in Parquet for {test_date}: {parquet_count}")

    # 4) Compare
    if db_count == parquet_count:
        print("Test PASSED: row counts match.")
    else:
        print("Test FAILED: row counts differ.")
```

**Explanation**:
1. **Query DB** for row count.  
2. **ETL** writes the partition for `test_date`.  
3. **DuckDB** then queries the specific partition path.  
4. **Comparison** checks consistency.

---

## **5.6 Chapter Summary**

- **Thorough testing** is essential for robust data pipelines. By comparing row counts, verifying data types, and sampling columns, you ensure your **SQL-based ETL** correctly reflects the source data.  
- **DuckDB** provides a simple SQL interface to Parquet, ideal for quick validation. **PyArrow** and **pandas** let you do in-Python checks (count, schema inspection, etc.).  
- **Partition Validation** helps confirm that your daily overwrite logic is working (no duplicate files remain).  

With these steps, you can confirm your ETL pipeline correctly transforms relational data into a **Hive-partitioned Parquet** layout. In a **production** environment, you might automate these validations, feed the results into a logging system, and even set up **alerts** if row counts diverge from expected baselines.