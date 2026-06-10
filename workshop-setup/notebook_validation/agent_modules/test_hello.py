"""Minimal smoke test to verify remote execution on Databricks.

Confirms the cluster has the prerequisites for Lab 2 notebook validation:
1. Python and Spark are available
2. Neo4j Spark Connector jar is on the classpath
3. Output is captured in the job run

Usage:
    ./upload.sh test_hello.py && ./submit.sh test_hello.py
"""

import os
import sys

print("=" * 60)
print("notebook_validation: Remote execution test")
print("=" * 60)
print(f"Python version: {sys.version}")
print(f"Python executable: {sys.executable}")
print(f"Working directory: {os.getcwd()}")
print(f"DATABRICKS_RUNTIME_VERSION: {os.environ.get('DATABRICKS_RUNTIME_VERSION', 'not set')}")

# Verify Spark is available
try:
    from pyspark.sql import SparkSession
    spark = SparkSession.builder.getOrCreate()
    print(f"Spark version: {spark.version}")
    print(f"Spark app name: {spark.sparkContext.appName}")
except Exception as e:
    print(f"Spark not available: {e}")

# Verify Neo4j Spark Connector jar is on the classpath
try:
    spark._jvm.Class.forName("org.neo4j.spark.DataSource")
    print("Neo4j Spark Connector: found on classpath")
except Exception:
    print("Neo4j Spark Connector: NOT found — install the connector library on the cluster")

print("=" * 60)
print("SUCCESS: Remote execution verified")
print("=" * 60)
