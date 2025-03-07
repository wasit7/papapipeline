# **Chapter 6: Suggested Design Patterns & Best Practices**

In the previous chapters, we covered the **technical steps** of generating synthetic data, storing it in a relational database, running SQL-based ETL (with optional daily partitions), and verifying the results in a Hive-partitioned Parquet data lake. This chapter focuses on how to **organize** that pipeline using **tried-and-true software design patterns** and **best practices** that can help your project remain **scalable**, **maintainable**, and **resilient**.

---

## **6.1 Embracing Modular Architecture**

### **6.1.1 Separate Extract, Transform, Load**

- **Extract**: Isolate database access logic in its own function or module—e.g., `extract_rent_data(overwrite_date)`.
- **Transform**: Keep data preparation (e.g., column renaming, type conversions, cleaning “error” values) in a distinct function.  
- **Load**: Write to Hive-partitioned Parquet in a dedicated routine. Overwrite or append as needed.

This separation reduces complexity: if you modify how you read from the source, you don’t break the transformation or loading steps.

### **6.1.2 Single Responsibility Principle**

- **One Purpose per Component**: Each function or module should handle a single responsibility. For instance, your `run_etl_join()` can orchestrate tasks, but the actual partition clearing or chunk-based reading can happen in smaller helper functions.
- **Easier Testing**: Smaller, focused functions mean you can test each piece (extract, transform, load) independently.

---

## **6.2 Configuration & Parameterization**

### **6.2.1 External Config**

- **Use Config Files**: Store paths, database credentials, or partition columns in a YAML or JSON file. Your code can load these on startup.  
- **Environment Variables**: For secure or sensitive settings (e.g., DB passwords), rely on environment variables rather than hardcoding them in your code.

### **6.2.2 Flexible Partition Columns**

- **Don’t Hardcode**: Instead of always using `year`, `month`, `day`, you could allow an array of partition columns defined in the config.  
- **Adapt to Evolving Needs**: If your dataset grows or changes structure, you can alter the config without overhauling the entire codebase.

---

## **6.3 Logging & Monitoring**

### **6.3.1 Structured Logging**

- **Use Logging Libraries**: Python’s `logging` module lets you configure log levels (INFO, WARN, ERROR). This is more flexible than `print(...)` statements.  
- **Contextual Logs**: Log the overwrite date, record counts, and any errors encountered (e.g., “rent_cost = 'error' detected in N rows”).

### **6.3.2 Row Count Audits**

- **Validation Table**: Optionally store row counts (or basic stats) in a small “audit” table, or push them to a monitoring system.  
- **Alerts**: If row counts deviate from historical averages, automatically flag an alert.

---

## **6.4 Data Validation & Cleansing**

### **6.4.1 Handling Mixed Data Types**

- **Explicit Conversion**: If a field like `rent_cost` can sometimes contain the string `"error"`, adopt a consistent rule, e.g., convert those to `NaN` or store them in a separate “invalid_rows” table.  
- **Strict Schemas**: For high-stakes pipelines, consider a validation library (e.g., Great Expectations) or custom checks ensuring the data meets certain thresholds (e.g., “age” must be > 0).

### **6.4.2 Incremental QA**

- **Testing Each Partition**: After writing a daily partition, do a quick check (row count, sample data). If it fails, you can fix or skip that day before proceeding.

---

## **6.5 Partition Overwrite & Concurrency Considerations**

### **6.5.1 Overwrite vs. Append**

- **Overwrite**: Clear the target directory for that date if you expect to **fully replace** data.  
- **Append**: If your data is truly incremental (e.g., streaming events), you can append new files to the existing partition.  
- **Consistency**: Overwrite is safer for daily “snapshot” data, ensuring no duplicates. Append is helpful for partial loads throughout a day.

### **6.5.2 Concurrency & Locking**

- **Avoid Overwrites During Active Loads**: If you have multiple ETL jobs that might handle the same partition, implement a locking mechanism or schedule them to avoid conflicts.  
- **Atomic Renames**: Some systems rename temporary folders to the final partition directory only after a successful write. This pattern prevents partial writes from corrupting a partition.

---

## **6.6 Chunk-Based Reading & Writing**

### **6.6.1 Handling Large Data Volumes**

- **Chunksize in SQL**: Use `pandas.read_sql_query(..., chunksize=...)` if your database table is too large for memory. Process each chunk in memory, then write partial Parquet files.  
- **Multiple Parquet Files per Partition**: Writing multiple files under the same partition is acceptable. Just ensure that each file is well-sized (tens or hundreds of MB, not thousands of tiny files).

### **6.6.2 Merging Small Files**

- **Optional Post-Processing**: If a partition ends up with too many small files (the “small-files problem”), you might run a merge job to combine them. Tools like Spark or an additional PyArrow pass can coalesce small Parquet files into larger ones.

---

## **6.7 Testing Patterns**

### **6.7.1 Unit & Integration Tests**

- **Unit Tests**: Confirm each function (extract, transform, load) works in isolation with small data sets.  
- **Integration Tests**: Run end-to-end checks with the entire pipeline, verifying partition directories, row counts, and schema consistency.  
- **Continuous Integration (CI)**: Automate tests in a CI pipeline so that new code changes are validated right away.

### **6.7.2 Data Sampling vs. Full Scan**

- **Quick Checks**: For daily testing, you may only sample a portion of rows or read just the newly written partition.  
- **Full Historical Validations**: Occasionally run more intensive checks across all partitions to ensure no legacy data issues.

---

## **6.8 Chapter Summary**

Following **best-practice design patterns**—like separating responsibilities, parameterizing configurations, systematically logging and validating data, and carefully handling partition overwrites—helps ensure your ETL pipeline remains robust as it evolves. By **modularizing** your code, you’ll make it easier to maintain, debug, and scale. With **sufficient logging and testing**, you’ll catch errors early and build **confidence** in your daily or periodic loads.

**Key Takeaways**:
- Keep **Extract, Transform, and Load** steps **logically separate**.  
- Store pipeline settings externally in config files or environment variables for flexibility.  
- Adopt **logging and monitoring** strategies to detect anomalies quickly.  
- Carefully design the partition overwrite logic to avoid duplicates or concurrency conflicts.  
- Gradually scale your pipeline by chunk-based reads/writes, merging small files, and adding more robust data validation.

With these design patterns and best practices in mind, your pipeline can handle growing data volumes, evolving schemas, and incremental daily loads with minimal friction. This closes the core sequence of chapters on building a small but powerful ETL-to-datalake pipeline.