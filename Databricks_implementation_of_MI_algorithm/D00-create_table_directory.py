# Databricks notebook source
# MAGIC %run "./project_config"

# COMMAND ----------

import json
from functions import write_json_file

# Database names
db = ''
dbc = f'{db}_collab'
dsa = ''
dss = 'dss_corporate'

# Table directory
archive_date = '2024-04-25'
archive_date_underscore = archive_date.replace("-", "_")

table_directory = {
    # --------------------------------------------------------------------------
    # Provisioned datasets
    # --------------------------------------------------------------------------
    'gdppr': {
        'database': dbc,
        'table_name': 'gdppr__archive',
        'archive_date': archive_date
    },
    'gdppr_all_versions': {
        'database': dbc,
        'table_name': 'gdppr__archive',
    },
    'hes_apc': {
        'database': dbc,
        'table_name': 'hes_apc_all_years_archive',
        'archive_date': archive_date
    },
    'hes_op': {
        'database': dbc,
        'table_name': 'hes_op_all_years_archive',
        'archive_date': archive_date
    },
    'hes_ae': {
        'database': dbc,
        'table_name': 'hes_ae_all_years_archive',
        'archive_date': archive_date
    },
    'minap': {
        'database': dbc,
        'table_name': 'nicor_minap__archive',
        'archive_date': '2025-04-24'
    },
    'ssnap': {
        'database': dbc,
        'table_name': 'ssnap__archive',
        'archive_date': archive_date
    },
    'vaccine_status':{
        'database': dbc,
        'table_name': 'vaccine_status__archive',
        'archive_date': archive_date
    },
    'deaths': {
        'database': dbc,
        'table_name': 'deaths__archive',
        'archive_date': archive_date
    },
    # --------------------------------------------------------------------------
    # HDS Common Tables - Demographics
    # --------------------------------------------------------------------------
    'gdppr_demographics_all_versions': {
        'database': dsa,
        'table_name': 'hds_curated_assets__gdppr_demographics',
    },
    'gdppr_demographics': {
        'database': dsa,
        'table_name': 'hds_curated_assets__gdppr_demographics',
        'max_archive_date': archive_date
    },
    'date_of_birth_multisource': {
        'database': dsa,
        'table_name': f'hds_curated_assets__date_of_birth_multisource_{archive_date_underscore}',
    },
    'date_of_birth_individual': {
        'database': dsa,
        'table_name': f'hds_curated_assets__date_of_birth_individual_{archive_date_underscore}',
    },
    'sex_multisource': {
        'database': dsa,
        'table_name': f'hds_curated_assets__sex_multisource_{archive_date_underscore}',
    },
    'sex_individual': {
        'database': dsa,
        'table_name': f'hds_curated_assets__sex_individual_{archive_date_underscore}',
    },
    'ethnicity_multisource': {
        'database': dsa,
        'table_name': f'hds_curated_assets__ethnicity_multisource_{archive_date_underscore}',
    },
    'ethnicity_individual': {
        'database': dsa,
        'table_name': f'hds_curated_assets__ethnicity_individual_{archive_date_underscore}',
    },
    'lsoa_multisource': {
        'database': dsa,
        'table_name': f'hds_curated_assets__lsoa_multisource_{archive_date_underscore}',
    },
    'lsoa_individual': {
        'database': dsa,
        'table_name': f'hds_curated_assets__lsoa_individual_{archive_date_underscore}',
    },
    'demographics': {
        'database': dsa,
        'table_name': f'hds_curated_assets__demographics_{archive_date_underscore}',
    },
    # --------------------------------------------------------------------------
    # HDS Common Tables - HES-APC 
    # --------------------------------------------------------------------------
    #
    #'hes_apc_cips_episodes': {
    #    'database': dsa,
    #    'table_name': f'hds_curated_assets__hes_apc_cips_episodes_{archive_date_underscore}',
    #},
    #'hes_apc_provider_spells': {
    #    'database': dsa,
    #    'table_name': f'hds_curated_assets__hes_apc_provider_spells_{archive_date_underscore}',
    #},
    #'hes_apc_cip_spells': {
    #    'database': dsa,
    #    'table_name': f'hds_curated_assets__hes_apc_cip_spells_{archive_date_underscore}',
    #},
    'hes_apc_diagnosis': {
        'database': dsa,
        'table_name': f'hds_curated_assets__hes_apc_diagnosis_{archive_date_underscore}',
    },
    #'hes_apc_procedure': {
    #    'database': dsa,
    #    'table_name': f'hds_curated_assets__hes_apc_procedure_{archive_date_underscore}',
    #},

    # --------------------------------------------------------------------------
    # HDS Common Tables - ONS Deaths
    # --------------------------------------------------------------------------
    'deaths_single': {
        'database': dsa,
        'table_name': f'hds_curated_assets__deaths_single_{archive_date_underscore}',
    },
    'deaths_cause_of_death': {
        'database': dsa,
        'table_name': f'hds_curated_assets__deaths_cause_of_death_{archive_date_underscore}',
    },

    # --------------------------------------------------------------------------
    # Project tables
    # --------------------------------------------------------------------------

    # D00a-hes_apc_cleaned

    'hes_apc_cleaned': {
        'database': dsa,
        'table_name': f'{project_name}__hes_apc_cleaned',
    },

    # D00b-hes_apc_cips 

    'hes_apc_cips_episodes': {
        'database': dsa,
        'table_name': f'{project_name}__hes_apc_cips_episodes',
    },
    'hes_apc_cips_provider_spells': {
        'database': dsa,
        'table_name': f'{project_name}__hes_apc_cips_provider_spells',
    },
    'hes_apc_cips_cips': {
        'database': dsa,
        'table_name': f'{project_name}__hes_apc_cips_cips',
    },
    'hes_apc_mi': {
        'database': dsa,
        'table_name': f'{project_name}__hes_apc_mi',
    },

    # D00c-minap_cleaned

    'minap_cleaned': {
        'database': dsa,
        'table_name': f'{project_name}__minap_cleaned',
    },


    # D01-create_cohort

    'cohort': {
        'database': dsa,
        'table_name': f'{project_name}__cohort',
    },

    # D02-mi_algorithm_hes_apc

    'hes_apc_algo_prep': {
        'database': dsa,
        'table_name': f'{project_name}__hes_apc_algo_prep',
    },
    'hes_apc_algo_non_mi_patients': {
        'database': dsa,
        'table_name': f'{project_name}__hes_apc_algo_non_mi_patients',
    },
    'hes_apc_algo_mi_patients': {
        'database': dsa,
        'table_name': f'{project_name}__hes_apc_algo_mi_patients',
    },

    # D03-mi_algorithm_ons

    'deaths_mi': {
        'database': dsa,
        'table_name': f'{project_name}__deaths_mi',
    },

    # D04-mi_algorithm_events

    'mi_events': {
        'database': dsa,
        'table_name': f'{project_name}__mi_events',
    },

    # D00-minap_exclusion_flowchart

    'minap_flowchart': {
        'database': dsa,
        'table_name': f'{project_name}__minap_flowchart',
    },
     # D06-minap_validation
    'hes_apc_admissions_minap': {
        'database': dsa,
        'table_name': f'{project_name}_hes_apc_admissions_minap',
    },
    'hes_minap_full': {
        'database': dsa,
        'table_name': f'{project_name}__hes_minap_full',
    },
    'minap_hes_labeled' : {
        'database': dsa,
        'table_name': f'{project_name}_minap_hes_labeled',
    },
    'reduced_hes_minap': {
        'database': dsa,
        'table_name': f'{project_name}__reduced_hes_minap',
    },
    'all_hes_counts': {
        'database': dsa,
        'table_name': f'{project_name}__all_hes_counts',
    },
    'all_hes_metrics': {
        'database': dsa,
        'table_name': f'{project_name}__all_hes_metrics',
    }, 
    'hes_I21_I22_counts': {
        'database': dsa,
        'table_name': f'{project_name}__hes_I21_I22_counts',
    },
    'hes_I21_I22_metrics': {
        'database': dsa,
        'table_name': f'{project_name}__hes_I21_I22_metrics',
    },
    'all_minap80_counts': {
        'database': dsa,
        'table_name': f'{project_name}__all_minap80_counts',
    },
    'all_minap80_metrics': {
        'database': dsa,
        'table_name': f'{project_name}__all_minap80_metrics',
    },
    'combined_counts': {
        'database': dsa,
        'table_name': f'{project_name}__combined_counts'
    },
    'combined_metrics': {
        'database': dsa,
        'table_name': f'{project_name}__combined_metrics'
    },
     'combined_counts_export': {
        'database': dsa,
        'table_name': f'{project_name}__combined_counts_export'
    },
    'combined_metrics_export': {
        'database': dsa,
        'table_name': f'{project_name}__combined_metrics_export'
    }
}

# Write table_directory
write_json_file(table_directory, path = './config/table_directory.json')