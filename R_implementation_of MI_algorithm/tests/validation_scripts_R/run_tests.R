# SCORE-CVD: Myocardial infarction algorithm 
# Saves simulation data, runs preparation scripts and MI algorithm, checks
# that the outputs of the algorithm match what we expect from the simulation data
# run_tests.R
# BHF Data Science Centre, 2025
#
# Authors:
# - Laura Sherlock, BHF Data Science Centre
# 
# Date Created: 2025-05-12
# Last updated: 2025-05-12
# Version:      v0.1
#
# This script runs each of the function scripts needed to  validate that the outputs
# produced by the MI algorithm are what we expect given the simulation data. 
# It runs the following scripts:
# "hes_apc_prepare_function.R" - prepares HES APC data
# "ons_deaths_prepare_function.R" - prepares ONS deaths data
# "hes_apc_generate_cips_function.R - generates the continuous inpatient stay (CIPS) ID
# It uses testthat to check for matches between the expected and actual outputs. 
# testthat is run on all scripts in the file "tests", "validation_scripts_R", "testthat" 
# i.e. test-validate_hes_apc_function (which runs the 03_hes_apc_mi_function.R script 
# and compares the output with the expected simulation data)
# and test-validate_ons_deaths_function (which runs the 04_ons_deaths_mi_function.R script 
# and compares the output with the expected simulation data)

# The script returns whether the test-validate_ons_deaths_function.R and test-validate_hes_apc_function.R
# pass checks of whether the simulation outputs and generated outputs match


# Load libraries
library(testthat)
library(tidyverse)
library(lubridate)
library(here)  

# --- Define ID name ---
# NB to be changed by algorithm user depending on ID name in the data set
person_id_var <- "person_id"

# turns off scientific notation
options(scipen = 999)

# --- Save the raw simulation data in correct format in file 'data' ----

message("Saving raw simulation data...")

# save the simulation data in correct format
# source the script to save the simulaiton data in the correct format
source(here::here("tests", "validation_scripts_R", "function", "save_sample_data_function.R" ))  

# set the input and output paths for save_sample_data_function script
input_sample_hes_apc_path <- here::here ("tests", "sample_data", "sample_hes_apc.csv")
expected_columns_hes_path <- here::here ("data", "interim_data")
output_sample_data_hes_path <- here::here ("data", "hes_apc_data")

input_sample_ons_deaths_path  <- here::here ("tests", "sample_data", "sample_ons_deaths.csv")
expected_columns_deaths_path <- here::here ("data", "interim_data")
output_sample_data_deaths_path <- here::here ("data", "ons_deaths_Data")

# run the function
save_sample_data(
  input_sample_hes_apc_path = input_sample_hes_apc_path,
  expected_columns_hes_path = expected_columns_hes_path,
  output_sample_data_hes_path = output_sample_data_hes_path,
  input_sample_ons_deaths_path = input_sample_ons_deaths_path ,
  expected_columns_deaths_path = expected_columns_deaths_path,
  output_sample_data_deaths_path = output_sample_data_deaths_path
)


# --- Run the data preparation and cips generation functions ----
message("Running data preparation functions...")

# Source preparation and cips generation scripts 
source(here::here("R", "functions", "hes_apc_prepare_function.R"))
source(here::here("R", "functions", "ons_deaths_prepare_function.R"))
source(here::here("R", "functions", "hes_apc_generate_cips_function.R")) 

# set the input and output paths for preparation scripts
input_hes_apc_path <- here::here ("data", "hes_apc_data")
output_hes_apc_path <- here::here ("data", "interim_data")

input_ons_deaths_path <- here::here ("data", "ons_deaths_data", "ons_deaths_data.csv")
output_ons_deaths_path <- here::here ("data", "interim_data")

cips_input_path <- here::here ("data", "interim_data", "hes_apc_prepared.rds")
output_cips_path <-  here::here ("data", "interim_data")


# Run the preparation functions for HES APC and ONS deaths and cips generation
prepare_hes_apc(input_hes_apc_path = input_hes_apc_path, 
                person_id_var = person_id_var,
                output_hes_apc_path =  output_hes_apc_path)


prepare_ons_deaths(input_ons_deaths_path =input_ons_deaths_path, 
                   person_id_var = person_id_var,
                   output_ons_deaths_path = output_ons_deaths_path)

generate_cips(cips_input_path = cips_input_path, 
              output_cips_path = output_cips_path)

# --- Run the validation scripts ---
# Run tests 
testthat::with_reporter(
  SummaryReporter$new(),
  testthat::test_dir(here::here("tests", "validation_scripts_R", "testthat"))
)

# End of testing
message("Testing complete.")
