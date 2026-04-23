# SCORE-CVD: Myocardial infarction alogrithm 
# Validate that the expected output matches the actual processed output for ONS deaths
# test-validate_ons_deaths_function.R
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
# i.e. the columns produced  by running the processing functions/ONS deaths MI algorithm 
# it is called in the 'run_tests.R' script as part of the validation fo the simulation data
# It runs the ons_deaths_mi_function.R script as part of the process

# --- test ONS deaths outputs ---
test_that("Validate ONS deaths outputs", {
  # Source the function
  source(here::here("R", "functions", "ons_deaths_mi_function.R")) 
  
  # input and output paths
  mi_ons_deaths_input_path <-  here::here ("data", "interim_data", "ons_deaths_prepared.rds")
  output_mi_ons_deaths_path <-  here::here ("outputs")
  mi_hes_apc_input_path <- here::here ("data", "interim_data", "hes_apc_prepared_cips.rds")
  mi_hes_apc_processed_path <- here::here ("outputs", "hes_apc_mi_processed.rds")
  generated_ons_data_path <- here::here("outputs" , "ons_deaths_mi_processed.rds")
  expected_ons_data_path <- here::here ( "data", "interim_data", "expected_ons_deaths_outputs.rds")
  
  # call function
  process_ons_deaths_mi(mi_ons_deaths_input_path = mi_ons_deaths_input_path, 
                        output_mi_ons_deaths_path = output_mi_ons_deaths_path, 
                        mi_hes_apc_input_path = mi_hes_apc_input_path, 
                        mi_hes_apc_processed_path = mi_hes_apc_processed_path)
  
  # Read in the generate data
  generated_data <- read_rds(generated_ons_data_path)
  
  # Select columns
  generated_death_mi <- generated_data %>%
    select(person_id_var, qualify, mi_date, terminal_node) %>%
    arrange(person_id_var)
  
  # Read in the expected data 
  expected_data <- read_rds(expected_ons_data_path)
  names(expected_data) <- tolower(names(expected_data))
  
  

  expected_death_mi <- expected_data %>%
    select(person_id_var,  qualify = expected_qualify, mi_date= expected_mi_date, terminal_node=expected_terminal_node) %>%
    distinct() %>%
    arrange(person_id_var) %>%
    mutate(mi_date = as.Date(mi_date, format= "%d/%m/%Y"))
  
  # Compare expected and actual
  expect_equal(generated_death_mi, expected_death_mi)
})

