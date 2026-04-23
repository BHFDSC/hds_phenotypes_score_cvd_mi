# SCORE-CVD: Myocardial infarction algorithm 
# Prepare ONS death
# 01b_ons_deaths_prepare_function.R
# BHF Data Science Centre, 2025
#
# Authors:
# - Laura Sherlock using code from Jamie Farrell's script '01_hes_apc_prepare.R, BHF Data Science Centre
# 
# Date Created: 2025-03-28
# Last updated: 2025-03-28
# Version:      v0.1
#
# This script encapsulates the original '01b_ons_deaths_prepare.R' script in a function.
# It loads the ONS deaths data set and performs the following:
# - Removing duplicates
# - Assigning numeric, date and integer columns
# - Removing null dates
# - Rename columns for consistency
# - Removing bad episodes (with flowchart)
# - Saves cleaned dataset

library(tidyverse)
library(lubridate)
library(here)

# Function to prepare ONS deaths data
prepare_ons_deaths <- function(input_ons_deaths_path, 
                               person_id_var, 
                               output_ons_deaths_path) {
  

  ## Columns with non-character data types
  date_cols =  c("date_of_death")
  
  # read in ONS deaths data
  ons_deaths <- read_csv(input_ons_deaths_path, col_types = cols(.default = col_character()))
  # convert column names to lower case if necessary
  names(ons_deaths) <- tolower(names(ons_deaths))
  
  # Set column types
  set_column_types = function(.ons_deaths, .date_cols){
    
    .col_names = colnames(.ons_deaths)
    .date_cols = intersect(.col_names, date_cols)
    
    
    if(length(.date_cols) > 0){
      .ons_deaths = .ons_deaths %>% 
        mutate(across(all_of(.date_cols),  ~ dmy(.)))
    }
    
    
    return(.ons_deaths)
  }
  
  ons_deaths <- ons_deaths %>% 
    set_column_types(
      .date_cols = date_cols
    )
  
  # Remove null dates
  remove_null_dates = function(.date, null_dates){
    .date = if_else(.date %in% ymd(null_dates), NA_Date_, .date)
    return(.date)
  }
  
  ons_deaths<- ons_deaths %>% 
    mutate(
      across(all_of(date_cols), function(.x) {
        remove_null_dates(.x, null_dates = c("1800-01-01", "1801-01-01"))
      }
      )
    )
  
  # Clean column names and assign person_id column
  ons_deaths<- ons_deaths %>% 
    rename(person_id = person_id_var,
           underlying_cod = s_underlying_cod_icd10,
           cod_mentioned_1 = s_cod_code_1,
           cod_mentioned_2 =s_cod_code_2) %>% 
    janitor::clean_names()
  
  # create column to flag those who have an MI event in one of the conditions at death
  ons_deaths<- ons_deaths%>% 
    mutate(mi_code_present = ifelse(str_detect(underlying_cod, pattern = "I21") |str_detect(underlying_cod, pattern = "I22") | str_detect(cod_mentioned_1 , pattern = "I21") |str_detect(cod_mentioned_1 , pattern = "I22") | str_detect(cod_mentioned_2 , pattern = "I21") |str_detect(cod_mentioned_2 , pattern = "I22"), TRUE, FALSE)) %>%
    mutate(mi_code_present = ifelse(is.na(mi_code_present),FALSE, mi_code_present))

  # Flag duplicates
  ons_deaths<- ons_deaths %>%
    arrange(person_id, date_of_death) %>%
    group_by(person_id)%>%
    mutate(
      non_duplicated_record = case_when(
        n() == 1 ~ 1,  
        n() > 1 & date_of_death == min(date_of_death) & mi_code_present == TRUE  ~ 1,
        n() > 1 & date_of_death == min(date_of_death) & mi_code_present == FALSE  ~ 0,
        date_of_death == min(date_of_death) ~ 1,
        TRUE ~ 0
      )
    ) %>%
    ungroup()
  
  # Create quality indicators
  ons_deaths<- ons_deaths %>%  
    mutate(
      known_person_id = if_else(!is.na(person_id), TRUE, FALSE),
      known_death_date = if_else(!is.na(date_of_death), TRUE, FALSE),
      non_duplicated_record = ifelse(non_duplicated_record==1, TRUE, FALSE)
    )
  
  # Create inclusion flags
  ons_deaths<- ons_deaths %>%  
    mutate(
      c0 = TRUE,
      c1 = c0 & known_person_id,
      c2 = c1 & known_death_date,
      c3 = c2 & non_duplicated_record,
      include = c3
    )
  
  # Compute flowchart
  flowchart_ons_deaths<- ons_deaths %>%   
    select(person_id, c0, c1, c2, c3) %>% 
    mutate(row_id = row_number()) %>% 
    pivot_longer(cols = starts_with("c"), names_to = "criteria", values_to = "inclusion") %>%
    filter(inclusion) %>% 
    group_by(criteria) %>%
    summarise(
      n_episodes = n(),
      n_ids = n_distinct(person_id),
    ) %>%
    ungroup() %>% 
    mutate(
      description = case_when(
        criteria == "c0" ~ "Original ONS deaths dataset",
        criteria == "c1" ~ " non-null person_id",
        criteria == "c2" ~ " non-null date_of_death",
        criteria == "c3" ~ " non_duplicated_record"
      ),
      episodes_removed = n_episodes - lag(n_episodes),
      ids_removed = n_ids - lag(n_ids),
      pct_episodes_removed = round(episodes_removed / lag(n_episodes) * 100, 2),
      pct_ids_removed = round(ids_removed / lag(n_ids) * 100, 2),
    ) %>% 
    select(criteria, description, n_episodes, episodes_removed, pct_episodes_removed,
           n_ids, ids_removed, pct_ids_removed)
  
  # Save flowchart
  write_csv(
    x = flowchart_ons_deaths,
    file = here::here(output_ons_deaths_path, "flowchart_ons_deaths.csv")
  )
  
  # Save excluded rows for reference
  ons_deaths_excluded_rows <- ons_deaths %>% 
    filter(!include)
  
  write_csv(
    x = ons_deaths_excluded_rows,
    file = here::here(output_ons_deaths_path, "ons_deaths_excluded_rows.csv")
  )
  
  # Filter out bad rows and save to file
  ons_deaths_prepared <- ons_deaths %>% 
    filter(include)
  
  # Remove mi_code_present from ons_deaths_prepared
  ons_deaths_prepared <- ons_deaths_prepared %>%
    select(-"mi_code_present")
  
  # Save ons_deaths_prepared to .csv for portability
  write_csv(
    x = ons_deaths_prepared,
    file = here::here(output_ons_deaths_path, "ons_deaths_prepared.csv")
  )
  
  # Save ons_deaths_prepared to .rds for reading into ons_detahs_mi_function
  write_rds(
    x = ons_deaths_prepared,
    file = here::here(output_ons_deaths_path, "ons_deaths_prepared.rds")
  )
}
