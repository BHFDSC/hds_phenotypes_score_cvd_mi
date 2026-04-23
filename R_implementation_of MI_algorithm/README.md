# MI Event Identification Pipeline -- Project Documentation

## 1. Project Overview

This R project falls under the BHF Data Science Centre's [SCORE-CVD](https://zenodo.org/records/8171481) (Standardising Clinical Outcome measures in Routinely collected Electronic healthcare systems data) project. It provides a pipeline for identifying myocardial infarction (MI) events, including recurrent MIs, in HES APC and ONS deaths datasets. Priority is given to MI events identified in HES APC records, i.e. if an MI event is counted in HES records, the event is not counted as an MI event in the deaths records. A flowchart detailing the logic of the algorithm can be found in the docs folder `docs > flowchart`.

A 'Task and Finish' group comprising clinical cardiologists, experienced trialists, and data analysts reviewed existing phenotyping algorithms, including those from the HDR UK Phenotype Library and prior clinical trials. A consensus was reached to base the MI classification algorithm on the RIPCORD 2 trial (flow diagram available on pages 3-4: [RIPCORD 2 Supplement](https://www.ahajournals.org/action/downloadSupplement?doi=10.1161%2FCIRCULATIONAHA.121.057793&file=circ_circulationaha-2021-057793_supp1.pdf)).


The ICD-10 codes I21 and I22 were used to flag MI events in the health records. I23 was excluded after sensitivity analysis revealed that it often co-occurred with an I21 code.

Continuous inpatient spells were generated based on documentation from the [Health & Social Care Information Centre (2014)](https://webarchive.nationalarchives.gov.uk/ukgwa/20180307232845tf_/http:/content.digital.nhs.uk/media/11859/Provider-Spells-Methodology/pdf/Spells_Methodology.pdf).

The primary processing script is `pipeline_run.R`, which coordinates the full data workflow including input preparation, processing, MI detection, and output generation.

This returns outputs for both HES APC and ONS deaths data indicating whether each episode qualifies as an MI event, and the terminal node of the decision tree which it is associated with.

### Simulation Data for Validation

The project includes simulation data and scripts to test the outputs to support validation of the algorithm. Simulation HES and ONS datasets with columns indicating whether an episode qualifies as an MI event (as well as other outputs) are included and can be run through the pipeline using the `run_tests.R` script. These tests compare generated outputs with expected results to confirm correctness.

## 2. Data Source

The algorithm requires Hospitals Episode Statistics Admission Patient Care (HES APC) and Office for National Statistics (ONS) deaths data. For algorithm development we used anonymised HES APC and ONS deaths data between 1st January 2020 and 31st December 2023. The data was accessed within the NHS England Safe Data via the BHF Data Science Centre's [CVD-COVID-UK/COVID-IMPACT Consortium](https://bhfdatasciencecentre.org/areas/cvd-covid-uk-covid-impact/).

## 3. Folder Structure

Below is the structure of the folder, with example input data. The interim data files generated, and the output files generated are also included.

```
> data
  > hes_apc
    > hes_apc_fy_2019.csv
    > hes_apc_fy_2020.csv
    > hes_apc_fy_2021.csv
    > hes_apc_fy_2022.csv
    > hes_apc_fy_2023.csv
  > ons_deaths
    > ons_deaths.csv
  > interim_data
    > expected_hes_apc_outputs.rds
    > expected_ons_deaths_outputs.rds
    > flowchart_hes_apc.csv
    > flowchart_ons_deaths.csv
    > hes_apc_excluded_rows.csv
    > hes_apc_prepared.rds
    > hes_apc_prepared_cips.rds
    > ons_deaths_excluded_rows.csv
    > ons_deaths_prepared.rds

> docs
  > derived_variables.md
  > files_generated.md
  > mi_algorithm_flowchart.png
  > pipeline_run_flowchart.png
  > required_columns.csv

> outputs
  > hes_apc_mi_events.csv
  > hes_apc_mi_processed.csv
  > ons_deaths_mi_processed.csv

> R
  > functions
    > hes_apc_prepare_function.R
    > ons_deaths_prepare_function.R
    > hes_apc_generate_cips_function.R
    > hes_apc_mi_function.R
    > ons_deaths_mi_function.R
  > pipeline_run.R

> tests
  > sample_data
    > sample_hes_apc.csv
    > sample_ons_deaths.csv
  > validation_scripts_R
    > function
      > save_sample_data.R
  > testthat
    > test-validate_hes_apc_mi_function.R
    > test-validate_ons_deaths_mi_function.R
  > run_tests.R
  
> README.md
```

## 4. Key Components

### 4.1 Main Pipeline Script

**pipeline_run.R**

- **Role:** Orchestrates the entire processing workflow.
- **Key Features:**
  - Users must **define the name of their person ID column**:
    ```r
    person_id_var <- "your_column_name"
    ```
    This line must be manually edited before running the pipeline to reflect the actual column name used in the dataset (e.g., nhs_number, patient_id).
  - Checks for the presence of required columns -- note all column names get converted to lowercase, so input column names are case-insensitive.
  - Executes the cleaning/preparation of the HES APC and ONS deaths data, generates continuous inpatient spell (CIPS) ID for HES data, and flags MI events, returning whether an episode qualifies as an MI event, how many MI events occurred at that episode, and the corresponding decision tree terminal node associated with the episode.
  - See `docs/pipeline_run_flowchart.png` for the workflow of the pipeline

### 4.2 Functions

The functions in folder `R/functions/` feed into the `pipeline_run.R` script. For greater detail on the steps included in each function see the scripts.

| File | Description |
|------|-------------|
| `hes_apc_prepare_function.R` | Cleans and standardises raw HES APC data. |
| `ons_deaths_prepare_function.R` | Cleans and standardises ONS death records. |
| `hes_apc_generate_cips_function.R` | Assigns Continuous Inpatient Spell (CIPS) IDs. |
| `hes_apc_mi_function.R` | Detects MI events in HES data and labels first/subsequent MIs. |
| `ons_deaths_mi_function.R` | Detects MI-related deaths from ONS data. |

### 4.3 Optional Tests & Validation

**run_tests.R**

- **Role:** Can be run to validate the `pipeline_run` workflow using simulation HES APC and ONS deaths data.
- **Simulation data:** .csv files containing simulation HES APC and ONS deaths data are stored in the folder `tests/sample_data/`. This data contains cases which reflect each node of the decision tree. This dummy data is in the date range 01.01.2019 to 31.12.2023, and includes cases with key information missing to test data preparation scripts.
- **Steps:**
  1. Requires users to **define the name of their person ID column**:
     ```r
     person_id_var <- "your_column_name"
     ```
     This line must be manually edited before running the pipeline to reflect the actual column name used in the dataset (e.g., nhs_number, patient_id).

  2. **Runs save_sample_data_function.R** to prepare sample data and save expected outputs in folder `data/interim_data`.
     - Executes data preparation functions (`hes_apc_prepare_function.R`, `ons_deaths_prepare_function.R`, `hes_apc_generate_cips_function.R`)
     - saves in relevant folder 'data/', splitting HES APC data into separate files per financial year.
     - Strips expected outputs (e.g., MI flags, dates).
     - Saves expected outcomes in folder 'data/interim_data/'.

  3. **Runs unit tests via testthat.**
     - `test-validate_hes_apc_mi_function.R`: Runs `hes_apc_mi_function.R`. Validates MI detection in HES data by comparing processed outputs to expected outputs.
     - `test-validate_ons_deaths_mi_function.R`: Runs `ons_deaths_mi_function.R`. Validates MI detection in ONS data by comparing processed outputs to expected outputs.

## 5. How to Run the Pipeline

### 5.1 Production Run

Before running, open `pipeline_run.R` and modify this line to reflect your dataset's person ID column:

```r
person_id_var <- "your_column_name"
```

Then run:

```r
source("R/pipeline_run.R")
```

Your data files must be placed as follows:

- **HES APC data:** Place one or more .csv files in `data/hes_apc/`. Files can be split by financial year or not.
- **ONS deaths data:** Place a .csv file in `data/ons_deaths/`.

File paths use the `here::here()` package, so as long as the .Rproj file is used, relative paths should resolve correctly.

Column names in your data do not need to match case -- the pipeline standardises all to lowercase automatically.

See `docs/pipeline_run_flowchart.png` for the workflow of the pipeline

### 5.2 Validation / Testing Run

Before running, open `run_tests.R` and modify this line to reflect your dataset's person ID column:

```r
person_id_var <- "your_column_name"
```

Then run:

```r
source("tests/validation_scripts_R/run_tests.R")
```

- If successful, tests will confirm MI classification logic is correct.
- Test outputs are compared against `expected_*.rds` files.

## 6. Outputs

| File | Description |
|------|-------------|
| `hes_apc_mi_events.csv` | Provides a list of ID's, MI dates and index of MI (i.e. first, 2nd, 3rd etc.) |
| `hes_apc_processed.csv` | Cleaned and processed HES APC data with additional columns indicating whether the episode qualifies as an MI, the MI date, the terminal node associated with the episode. |
| `ons_deaths_mi_processed.csv` | Cleaned and processed ONS deaths data with additional columns indicating whether the episode qualifies as an MI, the MI date, the terminal node associated with the episode. |

## 7. Logical Decision Tree (MI Classification)

The decision tree depicted in `docs/mi_algorithm_flowchart` represents the logic used to identify and classify MI events using HES APC and ONS deaths data. Part A captures rules for first and subsequent MI events in HES data. Part B handles MI-related deaths based on ONS records. Each node checks for specific ICD-10 codes, timing of events, and continuity of patient episodes (CIPS), applying hierarchical logic to flag valid MI cases.

## 8. Requirements

### Software and R packages

The MI algorithm pipeline and validation pipeline were built under R version 4.4.3 (2025-02-28 ucrt)

The following R packages, which are available on CRAN, are required to run the pipelines:

- [tidyverse](https://cran.r-project.org/web/packages/tidyverse/index.html)
- [testthat](https://cran.r-project.org/web/packages/testthat/index.html)
- [here](https://cran.r-project.org/web/packages/here/index.html)
- [janitor](https://cran.r-project.org/web/packages/janitor/index.html)
- [fs](https://cran.r-project.org/web/packages/fs/index.html)

## 9. Limitations of the Algorithm
The algorithm has been developed using HES APC data - as with all electronic health records there will be a delay between the patient event and the data being coded and available. This algorithm may not be suitable for all use cases. 
NHS administratively organises the data by Hospital Spells and Episodes which are recorded separately as single record (row of data) per patient. An episode is defined by NHS as a continuous period of admitted patient care administered under one consultant within healthcare providers. An MI occurring after an admission will be coded to the start date of the episode and as such, we recognise this may not be accurate to the day of the event. 
This algorithm may not be suitable for surgical or intervention trials with less than 6 months follow up or where there is a need for increased specificity to identify multiple events within a very short period (<24 hrs). In these cases, there may be an option to adopt a hybrid approach where such events are identified or adjudicated with traditional data collection.


## 10. Contributors

- *James Farrell, BHF Data Science Centre*
- *Laura Sherlock, BHF Data Science Centre*

## 11. Contact details 
Should you have any suggestions for improvements of the algorithm and/or the related documentation, or should you have any questions, please email the BHF Health Data Science team at  .
<br>
<br>
<br>