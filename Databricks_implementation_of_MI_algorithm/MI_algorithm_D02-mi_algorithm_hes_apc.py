# Databricks notebook source
# MAGIC %run "./project_config"

# COMMAND ----------

# MAGIC %run "./parameters"

# COMMAND ----------

# MAGIC %run "./functions/hds_functions"

# COMMAND ----------

from functions import load_table, save_table, read_csv_file, write_csv_file, map_column_values
import re
from pyspark.sql import functions as f
import pyspark.sql.types as t
from pyspark.sql.window import Window
import pandas as pd
from functools import reduce

# COMMAND ----------

hes_apc_cips_episodes = load_table('hes_apc_cips_episodes')
cohort = load_table('cohort')

diagnosis_3_columns = [col for col in list(hes_apc_cips_episodes.columns) if re.match(r'^diag_3_\d\d$', col)]
diagnosis_4_columns = [col for col in list(hes_apc_cips_episodes.columns) if re.match(r'^diag_4_\d\d$', col)]

hes_apc_algo_prep = (
    load_table('hes_apc_cips_episodes')
    .select(
        'epikey', 'person_id', 'epistart', 'epiend', 'epiorder',
        'admidate', 'disdate', 'admisorc', 'disdest', 'admimeth', 'dismeth',
        f.array(diagnosis_3_columns).alias('diag_3_array'),
        f.array(diagnosis_4_columns).alias('diag_4_array'),
        'cips_id', 'cips_admidate', 'cips_disdate', 'procode5'
    )
    .filter(f"(epistart >= '{study_start_date}') AND (epistart <= '{study_end_date}') AND (person_id IS NOT NULL)")
    .join(
        cohort
        .select('person_id'),
        on = 'person_id', how = 'inner'
    )
)

save_table(df = hes_apc_algo_prep, table = 'hes_apc_algo_prep')


# COMMAND ----------

hes_apc_algo_prep = load_table('hes_apc_algo_prep')

_win_id = Window.partitionBy('person_id')

hes_apc_prep = (
    hes_apc_algo_prep
    .withColumn(
        'diag_i21',
        f.when(
            f.array_contains('diag_3_array', 'I21'),
            f.lit(True)
        ).otherwise(f.lit(False))
    )
    .withColumn(
        'diag_i22',
        f.when(
            f.array_contains('diag_3_array', 'I22'),
            f.lit(True)
        ).otherwise(f.lit(False))
    )
    .withColumn('diag_i21_or_i22', f.expr('diag_i21 OR diag_i22'))
    .withColumn('diag_i21_and_i22', f.expr('diag_i21 AND diag_i22'))
    .withColumn(
        'individual_with_mi',
        f.max('diag_i21_or_i22').over(_win_id)
    )
)


hes_apc_algo_non_mi_patients = (
    hes_apc_prep
    .filter("individual_with_mi = False")
    .withColumn('qualify', f.lit(False))
    .withColumn('terminal_node', f.lit(0))
    .withColumn('terminal_node_description', f.lit('T0: individual with no I.21 or I.22 ever'))
)

save_table(df = hes_apc_algo_non_mi_patients, table = 'hes_apc_algo_non_mi_patients')

hes_apc_algo_mi_patients = (
    hes_apc_prep
    .filter("individual_with_mi = True")
)

save_table(df = hes_apc_algo_mi_patients, table = 'hes_apc_algo_mi_patients')


# COMMAND ----------

def hes_apc_mi_pandas(pdf):

    # Sort dataframe by admidate, epistart, epiend and epiorder
    pdf = pdf.sort_values(by = ['admidate', 'epistart', 'epiend', 'epiorder'])

    # Row index
    pdf = pdf.reset_index(drop=True)
    pdf['index_num'] = pdf.index

    # Compute logical flag for the first I.21 or I.22 diagnosis for this individual
    pdf['first_mi_diagnosis'] = pdf[pdf['diag_i21_or_i22'] == True].first_valid_index() == pdf['index_num']

    # Initiate new columns
    pdf['qualify'] = pd.NA
    pdf['mi_date'] = pd.NA
    pdf['mi_count'] = pd.NA
    pdf['terminal_node'] = pd.NA
    pdf['terminal_node_description'] = pd.NA
    pdf['last_qualifying_mi_date'] = pd.NA
    pdf['episode_lt_28d_from_mi'] = pd.NA
    pdf['prev_mi_had_i22'] = pd.NA
    pdf['same_cips_as_last_mi'] = pd.NA
    pdf['any_gap_in_mi_diagnosis'] = pd.NA
    

    # Loop over rows
    for index, row in pdf.iterrows():

        # Index of last valid MI event
        index_last_valid_mi = pdf[pdf['qualify'] == True].last_valid_index()

        # D1: Does this episode have an I.21 or I.22 diagnosis?
        if not row['diag_i21_or_i22']:

            # No - this episode does not contain an I.21 or I.22 diagnosis code.

            # T1: Not an MI event
            row['qualify'] = False
            row['terminal_node'] = 1
            row['terminal_node_description'] = 'T1: Not an MI event'

        else:

            # Yes - this episode contains an I.21 or I.22 diagnosis code.

            # D2: Is this the first I.21 or I.22 diagnosis?
            if row['first_mi_diagnosis']:

                # Yes - this is the first occurance of an I.21 or I.22 code for this individual

                # D3: Does this episode contain both I.21 and I.22 diagnoses?
                if not row['diag_i21_and_i22']:

                    # No - this episode only contains one of I.21 or I.22 diagnoses

                    # T2: Single MI event on episode start date
                    row['qualify'] = True
                    row['mi_count'] = 1
                    row['mi_date'] = row['epistart']
                    row['terminal_node'] = 2
                    row['terminal_node_description'] = 'T2: Single MI event on episode start date'

                else:

                    # Yes - this episode contains both I.21 and I.22 diagnoses

                    # T3: Two seperate MI events on episode start date
                    row['qualify'] = True
                    row['mi_count'] = 2
                    row['mi_date'] = row['epistart']
                    row['terminal_node'] = 3
                    row['terminal_node_description'] = 'T3: Two seperate MI events on episode start date'

            else:
               
                # No - this is not the first occurance of an I.21 or I.22 code for this individual
                
                # Compute whether the episode start occured less than 28 days from a recorded MI event
                row['last_qualifying_mi_date'] = pdf.at[index_last_valid_mi, 'mi_date']
                row['episode_lt_28d_from_mi'] =  ((row['epistart'] - row['last_qualifying_mi_date']).days < 28)

                # D4: Is this episode less than 28 days from an already recorded MI event?
                if row['episode_lt_28d_from_mi']:

                    # Yes - episode started less than 28 days from an already recorded MI event

                    # D5: Does this episode contain I.22?
                    if not row['diag_i22']:

                        # No - episode diagnosis does not contain I.22

                        # T4: Not an MI event
                        row['qualify'] = False
                        row['terminal_node'] = 4
                        row['terminal_node_description'] = 'T4: Not an MI event'

                    else:

                        # Yes - episode diagnosis contains I.22

                        # Compute whether the last recorded MI event contained an I.22 code
                        row['prev_mi_had_i22'] = pdf.at[index_last_valid_mi, 'diag_i22']

                        # D6: Did the last recorded MI event contain an I.22 code?
                        if not row['prev_mi_had_i22']:

                            # No - the previous MI event did not contain an I.22 code

                            # T5: Single MI event on episode start date
                            row['qualify'] = True
                            row['mi_count'] = 1
                            row['mi_date'] = row['epistart']
                            row['terminal_node'] = 5
                            row['terminal_node_description'] = 'T5: Single MI event on episode start date'

                        else:

                            # Yes - the previous MI event did contain an I.22 code

                            # T6: Not an MI event
                            row['qualify'] = False
                            row['terminal_node'] = 6
                            row['terminal_node_description'] = 'T6: Not an MI event'

                else:
                    
                    # No - episode started 28 days or more from an already recorded MI event

                    # Compute whether this episode is part of the same CIPS as the last recorded MI event
                    row['same_cips_as_last_mi'] = row['cips_id'] ==  pdf.at[index_last_valid_mi, 'cips_id']

                    # D7: Is this row part of the same continuous inpatient spell (CIPS) as the previous recorded MI event?
                    if not row['same_cips_as_last_mi']:

                        # No - This episode is not part of the same CIPS as the previous recorded MI event

                        # D8: Does this episode contain both I.21 and I.22 diagnoses?
                        if not row['diag_i21_and_i22']:

                            # No - this episode only contains one of I.21 or I.22 diagnoses

                            # T7: Single MI event on episode start date
                            row['qualify'] = True
                            row['mi_count'] = 1
                            row['mi_date'] = row['epistart']
                            row['terminal_node'] = 7
                            row['terminal_node_description'] = 'T7: Single MI event on episode start date'

                        else:

                            # Yes - this episode contains both I.21 and I.22 diagnoses

                            # T8: Two seperate MI events on episode start date
                            row['qualify'] = True
                            row['mi_count'] = 2
                            row['mi_date'] = row['epistart']
                            row['terminal_node'] = 8
                            row['terminal_node_description'] = 'T8: Two seperate MI events on episode start date'

                    else:

                        # Yes - This episode is part of the same CIPS as the previous recorded MI event

                        # Compute whether there are any episodes without I.21 or I.22 between this episode and the
                        # last recorded MI episode
                        row['any_gap_in_mi_diagnosis'] = (
                            pdf.loc[
                                (pdf['index_num'] > index_last_valid_mi) 
                                & (pdf['index_num'] < index)
                                & (pdf['diag_i21_or_i22'] == False)
                            ].shape[0] > 0
                        )

                        # D9: Is there at least one episode between the previous MI event and this 
                        #     episode which does not contain I.21 or I.22?

                        if not row['any_gap_in_mi_diagnosis']:

                            # No - There are no episodes between the previous recorded MI event and this
                            # episode that do not contain I.21 or I.22 diagnosis

                            # T9: Not an MI event
                            row['qualify'] = False
                            row['terminal_node'] = 9
                            row['terminal_node_description'] = 'T9: Not an MI event'

                        else:

                            # Yes - There is at least one episode between the previous MI event and this
                            # episode which does not contain I.21 or I.22

                            # D10: Does this episode contain both I.21 and I.22 diagnoses?
                            if not row['diag_i21_and_i22']:

                                # No - this episode only contains one of I.21 or I.22 diagnoses

                                # T10: Single MI event on episode start date
                                row['qualify'] = True
                                row['mi_count'] = 1
                                row['mi_date'] = row['epistart']
                                row['terminal_node'] = 10
                                row['terminal_node_description'] = 'T10: Single MI event on episode start date'

                            else:

                                # Yes - this episode contains both I.21 and I.22 diagnoses

                                # T11: Two seperate MI events on episode start date
                                row['qualify'] = True
                                row['mi_count'] = 2
                                row['mi_date'] = row['epistart']
                                row['terminal_node'] = 11
                                row['terminal_node_description'] = 'T11: Two seperate MI events on episode start date'
        
        # Update table with row values
        pdf.loc[index, 'qualify'] = row['qualify']
        pdf.loc[index, 'mi_count'] = row['mi_count']
        pdf.loc[index, 'mi_date'] = row['mi_date']
        pdf.loc[index, 'terminal_node'] = row['terminal_node']
        pdf.loc[index, 'terminal_node_description'] = row['terminal_node_description']
        pdf.loc[index, 'last_qualifying_mi_date'] = row['last_qualifying_mi_date']
        pdf.loc[index, 'episode_lt_28d_from_mi'] = row['episode_lt_28d_from_mi']
        pdf.loc[index, 'prev_mi_had_i22'] = row['prev_mi_had_i22']
        pdf.loc[index, 'same_cips_as_last_mi'] = row['same_cips_as_last_mi']
        pdf.loc[index, 'any_gap_in_mi_diagnosis'] = row['any_gap_in_mi_diagnosis']

    return pdf

# COMMAND ----------


hes_apc_algo_mi_patients = load_table('hes_apc_algo_mi_patients')

# Extract the schema of the input DataFrame
input_schema = hes_apc_algo_mi_patients.schema

# Create a new schema by adding new columns dynamically
new_columns = [
    t.StructField('qualify', t.BooleanType(), True),
    t.StructField('mi_date', t.DateType(), True),
    t.StructField('mi_count', t.IntegerType(), True),
    t.StructField('terminal_node', t.IntegerType(), True),
    t.StructField('terminal_node_description', t.StringType(), True),
    t.StructField('last_qualifying_mi_date', t.DateType(), True),
    t.StructField('first_mi_diagnosis', t.BooleanType(), True),
    t.StructField('index_num', t.IntegerType(), True),
    t.StructField('episode_lt_28d_from_mi', t.BooleanType(), True),
    t.StructField('prev_mi_had_i22', t.BooleanType(), True),
    t.StructField('same_cips_as_last_mi', t.BooleanType(), True),
    t.StructField('any_gap_in_mi_diagnosis', t.BooleanType(), True)

]

output_schema = t.StructType(input_schema.fields + new_columns)

hes_apc_algo_mi_patients = (
    hes_apc_algo_mi_patients
    .groupBy('person_id')
    .applyInPandas(
        hes_apc_mi_pandas,
        schema = output_schema
    )
)

save_table(df = hes_apc_algo_mi_patients, table = 'hes_apc_algo_mi_patients')

# COMMAND ----------

hes_apc_algo_mi_patients = load_table('hes_apc_algo_mi_patients')

display(
    hes_apc_algo_mi_patients
    .groupBy('terminal_node', 'terminal_node_description')
    .agg(
        f.count('*').alias('n'),
        f.countDistinct('person_id').alias('n_id')
    )
)

# COMMAND ----------




flowchart_schema = {
    'node_d01': {
        'parent_node': None,
        'expression': 'TRUE',
        'description': 'D1: Does this episode have an I.21 or I.22 diagnosis?'
    },
    'node_t01': {
        'parent_node': 'node_d01',
        'expression': '(diag_i21_or_i22 = FALSE)',
        'description': 'T1: Not an MI event'
    },
    'node_d02': {
        'parent_node': 'node_d01',
        'expression': '(diag_i21_or_i22 = TRUE)',
        'description': 'D2: Is this the first I.21 or I.22 diagnosis?'
    },
    'node_d03': {
        'parent_node': 'node_d02',
        'expression': '(first_mi_diagnosis = TRUE)',
        'description': 'D3: Does this episode contain both I.21 and I.22?'
    },
    'node_t02': {
        'parent_node': 'node_d03',
        'expression': '(diag_i21_and_i22 = FALSE)',
        'description': 'T2: Single MI event on episode start date'
    },
    'node_t03': {
        'parent_node': 'node_d03',
        'expression': '(diag_i21_and_i22 = TRUE)',
        'description': 'T3: Two seperate MI events on episode start date'
    },
    'node_d04': {
        'parent_node': 'node_d02',
        'expression': '(first_mi_diagnosis = FALSE)',
        'description': 'D4: Is this episode less than 28 days from an already recorded MI event?'
    },
    'node_d05': {
        'parent_node': 'node_d04',
        'expression': '(episode_lt_28d_from_mi = TRUE)',
        'description': 'D5: Does this episode contain I.22?'
    },
    'node_t04': {
        'parent_node': 'node_d05',
        'expression': '(diag_i22 = FALSE)',
        'description': 'T4: Not an MI event'
    },
    'node_d06': {
        'parent_node': 'node_d05',
        'expression': '(diag_i22 = TRUE)',
        'description': 'D6: Did the last recorded MI event contain an I.22 code?'
    },
    'node_t05': {
        'parent_node': 'node_d06',
        'expression': '(prev_mi_had_i22 = FALSE)',
        'description': 'T5: Single MI event on episode start date'
    },
    'node_t06': {
        'parent_node': 'node_d06',
        'expression': '(prev_mi_had_i22 = TRUE)',
        'description': 'T6: Not an MI event'
    },
    'node_d07': {
        'parent_node': 'node_d04',
        'expression': '(episode_lt_28d_from_mi = FALSE)',
        'description': 'D7: Is this episode part of the same continuous inpatient spell (CIPS) as the previous recorded MI event?'
    },
    'node_d08': {
        'parent_node': 'node_d07',
        'expression': '(same_cips_as_last_mi = FALSE)',
        'description': 'D8: Does this episode contain both I.21 and I.22?'
    },
    'node_t07': {
        'parent_node': 'node_d08',
        'expression': '(diag_i21_and_i22 = FALSE)',
        'description': 'T7: Single MI event on episode start date'
    },
    'node_t08': {
        'parent_node': 'node_d08',
        'expression': '(diag_i21_and_i22 = TRUE)',
        'description': 'T8: Two seperate MI events on episode start date'
    },
    'node_d09': {
        'parent_node': 'node_d07',
        'expression': '(same_cips_as_last_mi = TRUE)',
        'description': 'D9: Is there at least one episode between the previous MI event and this episode which does not contain I.21 or I.22?'
    },
    'node_t09': {
        'parent_node': 'node_d09',
        'expression': '(any_gap_in_mi_diagnosis = FALSE)',
        'description': 'T9: Not an MI event'
    },
    'node_d10': {
        'parent_node': 'node_d09',
        'expression': '(any_gap_in_mi_diagnosis = TRUE)',
        'description': 'D10: Does this row contain both I.21 and I.22?'
    },
    'node_t10': {
        'parent_node': 'node_d10',
        'expression': '(diag_i21_and_i22 = FALSE)',
        'description': 'T10: Single MI event on episode start date'
    },
    'node_t11': {
        'parent_node': 'node_d10',
        'expression': '(diag_i21_and_i22 = TRUE)',
        'description': 'T11: Two seperate MI events on episode start date'
    }
}

node_names = keys_list = list(flowchart_schema.keys())


hes_apc_algo_mi_patients = load_table('hes_apc_algo_mi_patients')

for node_name, node_features in flowchart_schema.items():

    if node_features['parent_node'] is None:
        hes_apc_algo_mi_patients = (
            hes_apc_algo_mi_patients
            .withColumn(node_name, f.expr(node_features['expression']))
        )
    
    else:
        hes_apc_algo_mi_patients = (
            hes_apc_algo_mi_patients
            .withColumn(node_name, f.col(node_features['parent_node']) & f.expr(node_features['expression']))
        )

flowchart_long = (
    hes_apc_algo_mi_patients 
    .withColumn('row_id', f.row_number().over(Window.orderBy(f.lit(1))))
    .select(['row_id', 'person_id', 'epikey', *node_names])
    .unpivot(
        ids = ['row_id', 'person_id', 'epikey'],
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

write_csv_file(df = flowchart_summary, path = './outputs/flowchart_mi_hes_apc.csv')

flowchart_summary_sdc = (
    flowchart_summary
    .withColumn('n', f.round(f.col('n')/10, 0)*10)
    .withColumn('n_id', f.round(f.col('n_id')/10, 0)*10)
)

write_csv_file(df = flowchart_summary_sdc, path = './outputs/flowchart_mi_hes_apc_sdc.csv')
