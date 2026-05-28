# Databricks notebook source
# MAGIC %run "./project_config"

# COMMAND ----------

# %run "./functions/hds_functions"

# COMMAND ----------

from functions import load_table, save_table
from pyspark.sql import functions as f
from pyspark.sql.window import Window

# COMMAND ----------

deaths_mi = (
    load_table('deaths_mi')
    .filter("qualify")
    .select(
        'person_id',
        f.col('date_of_death').alias('mi_date'),
        f.lit('ONS Mortality').alias('data_source')
    )
    
)


# COMMAND ----------

hes_apc_mi = (
    load_table('hes_apc_algo_mi_patients')
    .filter("qualify")
    .select('person_id', 'mi_date', 'mi_count')
    .withColumn('mi_date_array', f.expr("array_repeat(mi_date, mi_count)"))
    .withColumn('mi_date', f.explode('mi_date_array'))
    .select('person_id', 'mi_date', f.lit('HES-APC').alias('data_source'))
)


# COMMAND ----------

deaths_single = load_table('deaths_single')

_win_id = Window.partitionBy('person_id')
_win_id_ordered = Window.partitionBy('person_id').orderBy('mi_date', 'data_source')


mi_events = (
    hes_apc_mi
    .unionByName(deaths_mi)
    .join(
        deaths_single
        .select('person_id', 'date_of_death'),
        on = 'person_id', how = 'left'
    )
    .withColumn(
        'mi_index',
        f.row_number().over(_win_id_ordered)
    )
    .withColumn(
        'mi_total_count',
        f.max('mi_index').over(_win_id)
    )
    .withColumn(
        'death_within_28_days',
        f.when(
            f.datediff('date_of_death', 'mi_date') <= 28,
            f.lit(True)
        )
        .otherwise(False)
    )
    .withColumn(
        'mi_fatal_type',
        f.when(
            f.expr("(mi_index = mi_total_count) AND (death_within_28_days)"),
            f.lit('Fatal')
        )
        .otherwise('Non-fatal')
    )
    .select('person_id', 'mi_date', 'data_source', 'mi_index', 'mi_total_count', 'mi_fatal_type')
)

save_table(df = mi_events, table = 'mi_events')

# COMMAND ----------

mi_events = load_table('mi_events')

mi_summary = (mi_events
    .groupBy('mi_index', 'data_source')
    .agg(
        f.count('*').alias('n')
    )
    .orderBy('mi_index', 'data_source')
)


# COMMAND ----------

mi_summary.select(f.sum("n")).show()