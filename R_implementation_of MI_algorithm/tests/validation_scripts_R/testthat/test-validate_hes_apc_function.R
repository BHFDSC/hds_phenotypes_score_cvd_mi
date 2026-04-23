# SCORE-CVD: Myocardial infarction algorithm 
# Validate that the expected output matches the actual processed output for HES APC
# test-validate_hes_apc_function.R
# BHF Data Science Centre, 2025
#
# Authors:
# - Laura Sherlock, BHF Data Science Centre
# 
# Date Created: 2025-05-12
# Last updated: 2025-05-12
# Version:      v0.1
#
# This script checks that the events which qualify as an MI and their associated terminal nodes
# match between the expected outputs (i.e. the raw simulation data) and the processed outputs 
# i.e. the columns produced  by running the processing functions/ /HES APC MI algorithm 
# it is called in the 'run_tests.R' script as part of the validation fo the simulation data
# It runs the ons_deaths_mi_function.R script as part of the process

# --- test HES APC outputs ---
test_that("Validate hes apc outputs", {
  # Source the function
  source(here::here("R", "functions", "hes_apc_mi_function.R"))
  
  options(scipen = 999)
  
  # input and output paths
  mi_hes_apc_input_path <- here::here ("data", "interim_data", "hes_apc_prepared_cips.rds")
  output_mi_hes_apc_path <-  here::here ("outputs")
  generated_hes_data_path <- here::here("outputs" , "hes_apc_mi_processed.rds")
  expected_hes_data_path <- here::here ("data", "interim_data", "expected_hes_apc_outputs.rds")
  
  # call function
  process_hes_apc_mi(  mi_hes_apc_input_path = mi_hes_apc_input_path,
                       output_mi_hes_apc_path =  output_mi_hes_apc_path)
  
  
  # Read in the generate data
  generated_data <- read_rds(generated_hes_data_path)
  
 # Select person_id and cips_id
  generated_hes_mi <- generated_data %>%
    select(person_id_var, epikey, cips_id, qualify, mi_date, mi_count, terminal_node) %>%
    mutate(mi_count = ifelse(is.na(mi_count), 0, mi_count),
           epikey= as.character(epikey)) %>%
    arrange(person_id, epikey)
  
  # Read in the expected data 
  expected_data <- read_rds(expected_hes_data_path)
  
  expected_hes_mi <- expected_data %>%
    select(person_id = PERSON_ID, epikey= EPIKEY, cips_id = EXPECTED_CIPS_ID, qualify =  EXPECTED_QUALIFY, mi_date=EXPECTED_MI_DATE, mi_count=EXPECTED_MI_COUNT, terminal_node= EXPECTED_TERMINAL_NODE) %>%
    mutate(mi_date = as.Date(mi_date, format= "%d/%m/%Y"),
           epikey = as.character(epikey)) %>%
    distinct() %>%
    arrange(person_id, epikey)
  
  # Compare expected and actual
  expect_equal(generated_hes_mi, expected_hes_mi)
})
  
  