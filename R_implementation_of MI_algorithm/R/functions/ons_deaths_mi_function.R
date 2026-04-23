# SCORE-CVD: Myocardial infarction alogrithm 
# MI algorithm for ONS deaths data
# 04_ons_deaths_mi_function.R
# BHF Data Science Centre, 2025
#
# Authors:
# - James Farrell, BHF Data Science Centre, wrote the original script in PySpark
# - Laura Sherlock, BHF Data Science Centre, converted to R
# 
# Date Created: 2025-04-01
# Last updated: 2025-04-01
# Version:      v0.1
#
# This script encapsulates the original '04_ons_deaths_mi_function.R' script in a function.
# It identifies MI events in ONS Deaths data based on the algorithm from
# the RIPCORD-2 trial (https://www.ahajournals.org/doi/10.1161/CIRCULATIONAHA.121.057793)


process_ons_deaths_mi <- function(mi_ons_deaths_input_path, 
                                  output_mi_ons_deaths_path, 
                                  mi_hes_apc_input_path,
                                  mi_hes_apc_processed_path) {
  # Load data
  ons_deaths_mi <- read_rds(mi_ons_deaths_input_path)
  hes_apc_cleaned <- read_rds(mi_hes_apc_input_path)
  hes_apc_algo_mi_patients <- read_rds(mi_hes_apc_processed_path) 
  
  # Select columns
  ons_deaths_mi <- ons_deaths_mi %>% 
    select(person_id, date_of_death, underlying_cod, cod_mentioned_1, cod_mentioned_2) %>%
    mutate(mi_cod = ifelse(str_detect(underlying_cod, pattern = "I21") |str_detect(underlying_cod, pattern = "I22") | str_detect(cod_mentioned_1 , pattern = "I21") |str_detect(cod_mentioned_1 , pattern = "I22") | str_detect(cod_mentioned_2 , pattern = "I21") |str_detect(cod_mentioned_2 , pattern = "I22"), TRUE, FALSE)) %>% 
    mutate(mi_cod = ifelse(is.na(mi_cod),FALSE, mi_cod))
  
  # In-hospital death
  in_hospital_death <- ons_deaths_mi %>%
    select(person_id, date_of_death) %>%
    inner_join(hes_apc_cleaned %>%
                 select(person_id, epikey, epiend, disdate, dismeth, disdest), by = "person_id") %>%
    mutate(
      death_within_1_day_of_discharge = ifelse(date_of_death - disdate <= 1, 1, 0),
      discharge_to_death = ifelse(dismeth == 4 | disdest == 79, 1, 0),
      death_before_hosp_death = ifelse(
        (discharge_to_death == 1) & (date_of_death < pmax(epiend, disdate, na.rm = TRUE)),
        1, 0
      ),
      in_hospital_death = ifelse(
        (death_within_1_day_of_discharge == 1 | death_before_hosp_death == 1) & discharge_to_death == 1,
        1, 0
      )
    ) %>%
    group_by(person_id) %>%
    summarise(in_hospital_death = if (all(is.na(in_hospital_death))) NA else max(in_hospital_death, na.rm = TRUE), .groups = "drop")
  
  # MI event < 7 days before death
  mi_event_7_days_before_death <- ons_deaths_mi %>%
    select(person_id, date_of_death) %>%
    inner_join(hes_apc_algo_mi_patients %>%
                 select(person_id, epikey, mi_date, qualify) %>%
                 filter(qualify == TRUE), by = "person_id") %>%
    mutate(mi_event_less_than_7_days_prior = ifelse(date_of_death - mi_date < 7, 1, 0)) %>%
    group_by(person_id) %>%
    summarise(mi_event_less_than_7_days_prior = if (all(is.na(mi_event_less_than_7_days_prior))) NA else max(mi_event_less_than_7_days_prior, na.rm = TRUE), .groups = "drop")
  
  # Combine and classify
  ons_deaths_mi_processed <- ons_deaths_mi %>%
    left_join(in_hospital_death, by = "person_id") %>%
    left_join(mi_event_7_days_before_death, by = "person_id") %>%
    replace_na(list(in_hospital_death = 0, mi_event_less_than_7_days_prior = 0)) %>%
    mutate(
      qualify = ifelse((in_hospital_death == 0) & (mi_event_less_than_7_days_prior == 0) & (mi_cod==TRUE), TRUE, FALSE),
      terminal_node = ifelse(
        mi_cod == FALSE, 0, 
        ifelse(in_hospital_death == 1, 1,
               ifelse(mi_event_less_than_7_days_prior == 1, 2,
                      ifelse((in_hospital_death == 0) & (mi_event_less_than_7_days_prior == 0), 3, NA)))
      ),
      mi_date = as.Date(ifelse (qualify == TRUE, as.Date(date_of_death), NA
      ))
    )
  
  # Write to .csv for viewing file
  write_csv(
    x = ons_deaths_mi_processed,
    file = here::here(output_mi_ons_deaths_path, "ons_deaths_mi_processed.csv")
  )
  
  # write to .rds file for importing to validate_hes_apc_mi.R
  write_rds(
    x = ons_deaths_mi_processed,
    file = here::here(output_mi_ons_deaths_path, "ons_deaths_mi_processed.rds")
    
    )
  

}