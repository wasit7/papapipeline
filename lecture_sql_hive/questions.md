Below is a **30-question multiple-choice exam** covering the requested topics. Each question has four options (a–d), with the **correct answer always being “a.”** The questions address:

1. **Dataset generation and storing in a relational database**  
2. **Reasons for performing ETL with an `etl_date` and `dtype_backend="pyarrow"`**  
3. **Hive partitioning and Parquet writing modes (append vs. overwrite)**  
4. **Testing ETL by performing ETL on specific dates from a relational DB to a data lake**  
5. **Testing Parquet reads** using DuckDB SQL, PyArrow, and pandas.

---

## Exam Questions

### Dataset Generation & Storing in a Relational DB

1. Which of the following is a key reason for **generating synthetic datasets** before production testing?  
   a) It allows you to test data pipelines without using sensitive real data.  
   b) It ensures production data will never change.  
   c) It automatically fixes schema drift problems.  
   d) It eliminates the need for real databases.

2. When storing test data in a **relational database** for development, which practice is most beneficial?  
   a) Inserting data in tables that mirror the intended production schema.  
   b) Using random table names each time to avoid collisions.  
   c) Storing data in a single, flattened text column.  
   d) Avoiding indexes to speed up inserts.

3. For a **bike rental** test scenario, which set of **relational tables** typically captures the data model effectively?  
   a) `rent`, `user`, and `bike` tables with primary and foreign keys.  
   b) A single `rentbike` table containing all data.  
   c) A generic table named `test_table_1`.  
   d) A separate table per day to mimic partitioning at the database layer.

4. What is a practical reason for **generating mock user data** (names, emails, etc.) before storing it in a DB for testing?  
   a) It helps create realistic yet safe test scenarios.  
   b) It eliminates the need for referencing data quality checks.  
   c) It avoids the use of random sample queries.  
   d) It automatically partitions the data by user attributes.

5. In a typical **development workflow**, why store the generated dataset in a **PostgreSQL or MSSQL** instance?  
   a) Because it closely resembles how production data is accessed.  
   b) Because these databases prevent local development altogether.  
   c) Because CSV or JSON files are completely incompatible with data science tools.  
   d) Because NoSQL databases cannot handle testing data.

6. After generating the dataset for testing, which is the **best method** to keep it persistent in a local environment?  
   a) Using named volumes in Docker or local DB data folders.  
   b) Creating ephemeral in-memory tables that vanish on restart.  
   c) Relying on random test data for each query.  
   d) Copying the raw data to the clipboard for each test run.

---

### Reasons Behind Performing ETL with `etl_date` & `dtype_backend="pyarrow"`

7. Why do we commonly include an **ETL date** (e.g., `overwrite_date`) when running a SQL-based ETL?  
   a) To filter data for a specific day or partition in incremental loads.  
   b) To ignore all data that doesn’t match the current system date.  
   c) To force the SQL engine to use in-memory transformations only.  
   d) To rename the database schema automatically.

8. What is a **major advantage** of specifying `dtype_backend="pyarrow"` in `pandas.read_sql_query()`?  
   a) It preserves source data types more consistently than the default.  
   b) It automatically removes string columns from the DataFrame.  
   c) It forcibly converts all columns to integer.  
   d) It discards rows with mixed data types.

9. When using `etl_date` as a filter condition in a **SQL `WHERE` clause**, what is the main goal?  
   a) To limit the dataset to only the day (or period) being processed.  
   b) To ensure the database always returns all historical records.  
   c) To alter the underlying table schema each day.  
   d) To store all results in a single unpartitioned file.

10. How does `dtype_backend="pyarrow"` **help** if certain columns have mixed data like numeric values and the string `"error"`?  
    a) It can store them in an Arrow-type column without defaulting everything to “object.”  
    b) It automatically corrects `"error"` to a valid integer.  
    c) It forcibly drops any row containing a string.  
    d) It renames the column based on data type changes.

11. Using an **ETL date** approach supports incremental loads. Which statement best describes this?  
    a) Only data for the targeted date range is pulled, making the load more efficient.  
    b) The entire table is truncated, and full data is reloaded every time.  
    c) Metadata columns are never included in the dataset.  
    d) It automatically merges partitions after each load.

12. If you ignore `dtype_backend="pyarrow"`, which **problem** may arise in columns that sometimes store strings and other times numbers?  
    a) Pandas might fallback to `object` dtype, causing inconsistencies.  
    b) Pandas automatically reindexes the entire DataFrame.  
    c) Pandas discards all string rows silently.  
    d) The database returns an error preventing any reading.

---

### Hive Partitioning & Parquet Writing Modes

13. **Hive partitioning** in a data lake primarily refers to:  
    a) Organizing data into directory structures based on partition columns (e.g., `year=YYYY/month=MM/day=DD`).  
    b) Compressing files using hive-compatible libraries.  
    c) Manually rewriting parquet metadata for each partition.  
    d) Storing data in single large files labeled by date.

14. What is the purpose of **writing to a Hive-partitioned Parquet dataset** with `partition_cols=["year", "month", "day"]`?  
    a) To create a directory hierarchy that big-data tools can quickly prune.  
    b) To force each row to be stored in a separate Parquet file.  
    c) To rename the internal table structure in the database.  
    d) To use CSV output for maximum flexibility.

15. In PyArrow’s `pq.write_to_dataset()`, what does **“overwrite mode”** generally imply in an ETL context?  
    a) Removing or clearing the existing data for a particular partition before writing new data.  
    b) Appending new data files to existing data in the same directory.  
    c) Storing data in memory only.  
    d) Converting Parquet files to JSON automatically.

16. Conversely, **“append mode”** for writing Hive-partitioned Parquet is best described as:  
    a) Adding new files without removing older ones under the same partition.  
    b) Deleting all existing files and writing brand new ones.  
    c) Generating empty partitions in each folder.  
    d) Renaming each existing Parquet file to “backup.parquet” first.

17. Which statement accurately describes **why** Hive partition columns are often derived from a timestamp (e.g., `rent_start`)?  
    a) It allows queries to skip irrelevant partitions, improving performance.  
    b) It forces a single partition for all data, which is more efficient.  
    c) It ensures each row is updated only once per day.  
    d) It is required to store data in CSV format.

18. When you **overwrite** a partition directory, which step is typically **necessary**?  
    a) Deleting or clearing existing files under that partition folder.  
    b) Using the `drop table` command in the relational database.  
    c) Renaming the column `partition_col` to “deleted_col.”  
    d) Restricting the query to only numeric columns.

---

### Testing the ETL Process

19. What is the main reason to **test an ETL run on specific dates** (e.g., `overwrite_date="2025-02-17"`) in a local environment?  
    a) To verify that only that day’s data is extracted and partitioned correctly.  
    b) To skip all partition columns during the data load.  
    c) To convert all columns into string objects.  
    d) To rename the table to “2025-02-17” for easy reference.

20. If your test data for **2025-02-17** already exists in the data lake partition, which step helps **avoid duplication** when you re-run?  
    a) Clearing the existing `year=2025/month=02/day=17` folder.  
    b) Automatically skipping the partition in your query.  
    c) Renaming the old data folder to “old_date.”  
    d) Appending a numeric suffix to the folder name.

21. Which of the following is **true** about incremental testing with an ETL date?  
    a) It’s a straightforward way to ensure each day’s data can be processed independently.  
    b) It means the ETL must load all historical data every time.  
    c) It forces the pipeline to discard the partition columns.  
    d) It merges all days into a single partition to simplify queries.

22. When verifying your ETL results, you notice that the column types differ from the source DB. A likely reason is:  
    a) Pandas type inference was used instead of `dtype_backend="pyarrow"`.  
    b) The database automatically typed all columns as integers.  
    c) The pipeline created multiple date partitions in a single folder.  
    d) The partitioning process forced everything to become numeric.

23. How can you **confirm** that the correct number of rows loaded for a given date in the data lake partition?  
    a) Run a quick count query (e.g., `SELECT COUNT(*)`) against the Parquet files or the DB.  
    b) Assume all data arrived if no error was thrown.  
    c) Inspect the partition folder name only.  
    d) Compare the size of the folder to random thresholds.

24. Which is **most helpful** in ensuring your ETL tests are reproducible?  
    a) Using consistent environment variables and a stable code base.  
    b) Randomizing all table structures daily.  
    c) Mixing CSV and Parquet outputs together.  
    d) Deleting your entire data directory after every run.

---

### Testing Reading Parquet Files (DuckDB, PyArrow, pandas)

25. Why might you use **DuckDB** to read Parquet files for testing?  
    a) Because it supports efficient SQL queries directly on Parquet without a big cluster.  
    b) Because it only works on CSV data.  
    c) Because it requires a complex external server setup.  
    d) Because it converts all data to a single text column.

26. When reading Parquet files with **PyArrow**, what advantage do you get for testing?  
    a) Direct manipulation of Arrow Tables in memory.  
    b) Automatic conversion of all columns to booleans.  
    c) Forced reading of only one row at a time.  
    d) Deletion of partition columns on load.

27. How can you **verify** partition columns (like `year`, `month`, `day`) after reading a partitioned dataset with PyArrow?  
    a) Inspect the metadata or columns in the resulting PyArrow Table.  
    b) Confirm that the file extension is `.parquet`.  
    c) Convert each partition to CSV for final checks.  
    d) Evaluate the schema only in the SQL database.

28. In **pandas**, which method is typically used to read a local Parquet file or directory?  
    a) `pd.read_parquet(...)`  
    b) `pd.read_csv(...)`  
    c) `pd.to_parquet(...)`  
    d) `pd.merge_parquet(...)`

29. When using **DuckDB** to query a partitioned Parquet dataset, you can filter by `year` or `day` to:  
    a) Prune partitions and reduce the amount of data scanned.  
    b) Append new data to existing Parquet files automatically.  
    c) Convert the dataset to Arrow before continuing.  
    d) Rename columns inside the partition directories.

30. Reading a **Hive-partitioned dataset** via **pandas** often requires specifying:  
    a) The top-level directory path, so that pandas or PyArrow can discover sub-partitions.  
    b) A single `.parquet` file name for the entire dataset.  
    c) A JSON manifest of all available partitions.  
    d) The original SQL table name from the relational database.