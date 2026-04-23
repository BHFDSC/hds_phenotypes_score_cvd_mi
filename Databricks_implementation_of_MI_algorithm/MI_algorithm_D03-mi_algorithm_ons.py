# Databricks notebook source
# MAGIC %run ./project_config

# COMMAND ----------

# MAGIC %run "/Shared/SHDS/common/functions"

# COMMAND ----------

from hds_functions import load_table, save_table, read_csv_file, write_csv_file, map_column_values
import re
from pyspark.sql import functions as f
import pyspark.sql.types as t
from pyspark.sql.window import Window
import pandas as pd
from functools import reduce

# COMMAND ----------

# MAGIC %run ./parameters

# COMMAND ----------

deaths_single = load_table('deaths_single')
cohort = load_table('cohort')

deaths_mi = (
    deaths_single
    .select(
        'person_id',
        'date_of_death',
        f.col('s_underlying_cod_icd10').alias('underlying_cod'),
        f.col('s_cod_code_1').alias('cod_metioned_1'),
        f.col('s_cod_code_2').alias('cod_metioned_2')
    )
    .join(
        cohort
        .select('person_id'),
        on = 'person_id', how = 'inner'
    )
    .withColumn(
        'mi_cod',
        f.when(
            (
                f.col('underlying_cod').startswith('I21')
                | f.col('cod_metioned_1').startswith('I21')
                | f.col('cod_metioned_2').startswith('I21')
                | f.col('underlying_cod').startswith('I22')
                | f.col('cod_metioned_1').startswith('I22')
                | f.col('cod_metioned_2').startswith('I22')
            ),
            f.lit(True)
        )
    )
    .filter(f"(mi_cod) AND (date_of_death >= '{study_start_date}') AND (date_of_death <= '{study_end_date}')")
)


# COMMAND ----------

count_var(deaths_mi, 'person_id')

# COMMAND ----------

hes_apc_cleaned = load_table('hes_apc_cleaned')

in_hospital_death = (
    deaths_mi
    .select('person_id', 'date_of_death')
    .join(
        hes_apc_cleaned
        .select('epikey', 'person_id', 'disdate', 'dismeth', 'disdest'),
        how = 'inner',
        on = ['person_id']
    )
    .withColumn(
        'death_within_1_day_of_discharge',
        f.when(
            f.abs(f.datediff('date_of_death', 'disdate')) <= f.lit(1),
            f.lit(True)
        )
        .otherwise(False)
    )
    .withColumn(
        'discharge_to_death',
        f.when(
            f.expr("(dismeth = '4') OR (disdest = '79')"),
            f.lit(True)
        )
        .otherwise(False)
    )
    .withColumn(
        'in_hospital_death',
        f.expr("death_within_1_day_of_discharge AND discharge_to_death")
    )
    .groupBy('person_id')
    .agg(
        f.max('in_hospital_death').alias('in_hospital_death')
    )
)


# COMMAND ----------

hes_apc_algo_mi_patients = load_table('hes_apc_algo_mi_patients')

mi_event_7_days_before_death = (
    deaths_mi
    .select('person_id', 'date_of_death')
    .join(
        hes_apc_algo_mi_patients
        .select('epikey', 'person_id', 'mi_date', 'qualify')
        .filter("qualify"),
        how = 'inner',
        on = ['person_id']
    )
    .withColumn(
        'mi_event_less_than_7_days_prior',
        f.when(
            f.datediff('date_of_death', 'mi_date') < f.lit(7),
            f.lit(True)
        )
        .otherwise(False)
    )
    .groupBy('person_id')
    .agg(
        f.max('mi_event_less_than_7_days_prior').alias('mi_event_less_than_7_days_prior')
    )
)


# COMMAND ----------


deaths_mi = (
    deaths_mi
    .join(
        in_hospital_death,
        on = 'person_id', how = 'left'
    )
    .join(
        mi_event_7_days_before_death,
        on = 'person_id', how = 'left'
    )
    .fillna(False, subset = ['in_hospital_death', 'mi_event_less_than_7_days_prior'])
    .withColumn(
        'qualify',
        f.when(
            f.expr("(in_hospital_death = False) AND (mi_event_less_than_7_days_prior = False)"),
            f.lit(True)
        )
        .otherwise(False)
    )
)

save_table(df = deaths_mi, table = 'deaths_mi')


# COMMAND ----------

flowchart_schema = {
    'node_d01': {
        'parent_node': None,
        'expression': 'TRUE',
        'description': "D1: Is there a corresponding record in HES-APC documenting an in-hospital death with:- Dicharge date within 1 day of the date of death; and - Dicharge method of '4' (Patient died), or discharge destination of '79' (Not applicable - Patient died or still birth)"
    },
    'node_t01': {
        'parent_node': 'node_d01',
        'expression': '(in_hospital_death = TRUE)',
        'description': 'T1: Excluded as event will have been captured in HES-APC'
    },
    'node_d02': {
        'parent_node': 'node_d01',
        'expression': '(in_hospital_death = FALSE)',
        'description': 'D2: Is this the first I.21 or I.22 diagnosis?'
    },
    'node_t02': {
        'parent_node': 'node_d02',
        'expression': '(mi_event_less_than_7_days_prior = TRUE)',
        'description': 'T2: Excluded as death assumed to relate to previously recorded MI.'
    },
    'node_t03': {
        'parent_node': 'node_d02',
        'expression': '(mi_event_less_than_7_days_prior = FALSE)',
        'description': 'T3: Single MI event with date of death as the event date'
    }
}

node_names = keys_list = list(flowchart_schema.keys())


deaths_mi = load_table('deaths_mi')

for node_name, node_features in flowchart_schema.items():

    if node_features['parent_node'] is None:
        deaths_mi = (
            deaths_mi
            .withColumn(node_name, f.expr(node_features['expression']))
        )
    
    else:
        deaths_mi = (
            deaths_mi
            .withColumn(node_name, f.col(node_features['parent_node']) & f.expr(node_features['expression']))
        )

flowchart_long = (
    deaths_mi 
    .withColumn('row_id', f.row_number().over(Window.orderBy(f.lit(1))))
    .select(['row_id', 'person_id', *node_names])
    .unpivot(
        ids = ['row_id', 'person_id'],
        values = node_names,
        variableColumnName = 'node_id',
        valueColumnName = 'membership'
    )
)

# Create two separate dictionaries
dict_parent_node = {key: value['parent_node'] for key, value in flowchart_schema.items()}
dict_description = {key: value['description'] for key, value in flowchart_schema.items()}

flowchart_summary = (
    flowchart_long
    .groupBy('node_id') \
    .agg(
        f.count(f.when(f.expr("membership = TRUE"), f.lit(1))).alias('n'),
        f.countDistinct(f.when(f.expr("membership = TRUE"), f.col('person_id'))).alias('n_id')
    )
    .transform(
        map_column_values,
        map_dict = dict_parent_node,
        column = 'node_id',
        new_column = 'parent_node'
    )
    .transform(
        map_column_values,
        map_dict = dict_description,
        column = 'node_id',
        new_column = 'description'
    )
)

write_csv_file(df = flowchart_summary, path = './outputs/flowchart_mi_deaths.csv')

flowchart_summary_sdc = (
    flowchart_summary
    .withColumn('n', f.round(f.col('n')/10, 0)*10)
    .withColumn('n_id', f.round(f.col('n_id')/10, 0)*10)
)

write_csv_file(df = flowchart_summary_sdc, path = './outputs/flowchart_mi_deaths_sdc.csv')