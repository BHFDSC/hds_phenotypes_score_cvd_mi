# Documentation for PySpark MI Algorithm Implementation

## Overview

This project falls under the BHF Data Science Centre's [SCORE-CVD](https://zenodo.org/records/8171481) (Standardising Clinical Outcome measures in Routinely collected Electronic healthcare systems data) project. It provides a pipeline for identifying myocardial infarction (MI) events, including recurrent MIs, in HES APC and ONS deaths datasets. Priority is given to MI events identified in HES APC records, i.e. if an MI event is counted in HES records, the event is not counted as an MI event in the deaths records. A flowchart detailing the logic of the algorithm can be found in the docs folder `docs > flowchart`.

A 'Task and Finish' group comprising clinical cardiologists, experienced trialists, and data analysts reviewed existing phenotyping algorithms, including those from the HDR UK Phenotype Library and prior clinical trials. A consensus was reached to base the MI classification algorithm on the RIPCORD 2 trial (flow diagram available on pages 3-4: [RIPCORD 2 Supplement](https://www.ahajournals.org/action/downloadSupplement?doi=10.1161%2FCIRCULATIONAHA.121.057793&file=circ_circulationaha-2021-057793_supp1.pdf)).

The ICD-10 codes I21 and I22 were used to flag MI events in the health records. I23 was excluded after sensitivity analysis revealed that it often co-occurred with an I21 code.

Continuous inpatient spells were generated based on documentation from the [Health & Social Care Information Centre (2014)](https://webarchive.nationalarchives.gov.uk/ukgwa/20180307232845tf_/http:/content.digital.nhs.uk/media/11859/Provider-Spells-Methodology/pdf/Spells_Methodology.pdf).

This document provides documentation for the PySpark implementation of the SCORE-CVD Myocardial Infarction (MI) detection algorithm in Databricks. An R version is also available [here](https://github.com/BHFDSC/SCORE-CVD/tree/main/MI_algorithm/R_implementation_of%20MI_algorithm). 
The algorithm processes HES APC and ONS deaths records to identify and classify MI events using a decision tree approach.

## 1. Files Generated During Pipeline Execution

The files listed below are created during the execution of the PySpark MI algorithm pipeline.

### Files saved in Databricks tables

| Table | Description | Script |
|-------|-------------|---------|
| `hes_apc_cleaned` | Cleaned HES APC data with column selection, date cleaning, and episode filtering | D00a-hes_apc_cleaned.py |
| `hes_apc_cips_episodes` | HES APC episodes with Continuous Inpatient Spell (CIPS) identifiers | D00b-hes_apc_cips.py |
| `hes_apc_cips_provider_spells` | Provider spell level data with CIPS linkage | D00b-hes_apc_cips.py |
| `hes_apc_cips_cips` | CIPS level summary data | D00b-hes_apc_cips.py |
| `cohort` | Study cohort with inclusion criteria applied and covariates flagged| D01-create_cohort.py and D005-covariates|
| `hes_apc_algo_prep` | Prepared HES APC data for MI algorithm processing | D02-mi_algorithm_hes_apc.py |
| `hes_apc_algo_non_mi_patients` | Episodes from patients with no qualifying MI event | D02-mi_algorithm_hes_apc.py |
| `hes_apc_algo_mi_patients` | Episodes from patients with a qualifying MI event, with algorithm results | D02-mi_algorithm_hes_apc.py |
| `deaths_mi` | ONS deaths data with MI cause of death, with algorithm results | D03-mi_algorithm_ons.py |
| `mi_events` | Combined MI events from HES APC and ONS deaths | D04a-mi_algorithm_events.py |
|

### Files saved as CSV outputs

| File | Description | Script |
|------|-------------|---------|
| `outputs/flowchart_1.csv` | HES APC inclusion/exclusion flowchart | D00a-hes_apc_cleaned.py |
| `outputs/flowchart_cohort.csv` | Cohort creation flowchart | D01-create_cohort.py |
| `outputs/flowchart_mi_hes_apc.csv` | HES APC MI algorithm decision tree flowchart | D02-mi_algorithm_hes_apc.py |
| `outputs/flowchart_mi_deaths.csv` | ONS deaths MI algorithm decision tree flowchart | D03-mi_algorithm_ons.py |
| `outputs/flowchart_hes_apc.csv` | Flowchart of HES APC data input to algorithm | D04b-mi_algorithm-hes_ons_flowcharts.py |
| `outputs/flowchart_ons_deaths.csv` | Flowchart of ONS deaths data input to algorithm | D04b-mi_algorithm-hes_ons_flowcharts.py |
| `outputs/flowchart_minap.csv` | MINAP inclusion/exclusion flowchart  | D06a-minap_cleaned.py |
| `outputs/minap_counts.csv` | MINAP validation confusion matrix counts | D06b-minap_validation.py |
| `outputs/minap_metrics.csv` | MINAP validation performance metrics | D06b-minap_validation.py |

## 2. Script Documentation

### D00a-hes_apc_cleaned.py

This script performs initial cleaning and filtering of HES APC data.

#### Key Processing Steps:
1. **Column Selection**: Selects essential columns including person_id, episode dates, diagnosis codes
2. **Date Cleaning**: Nullifies invalid dates (1800-01-01, 1801-01-01)
3. **Episode Date Correction**: Swaps epistart/epiend if epistart > epiend
4. **ADMIDATE Imputation**: Uses epistart as admidate when missing under specific conditions
5. **Inclusion Criteria**: Applies filtering based on data quality requirements
6. **Flowchart Generation**: Creates inclusion/exclusion flowchart

#### Derived Variables:

##### epistart_gt_epiend
**Label:** Episode start greater than episode end flag  
**Description:** Flag indicating whether episode start date is after episode end date  
**Source data:** HES APC  
**Data type:** Integer (1 or null)  
**Values:** 1 if epistart > epiend, null otherwise  
**Missing values:** Null when dates are in correct order  
**Derivation function:** Date cleaning section  
**Derivation rules:** `f.when(f.col('epistart') > f.col('epiend'), f.lit(1))`  
**Dependencies:** epistart, epiend  
**Usage:** Used to identify and correct date inconsistencies

##### valid_epikey, valid_person_id, valid_procode, etc.
**Label:** Data quality flags  
**Description:** Boolean flags indicating presence of required data elements  
**Source data:** HES APC  
**Data type:** Boolean  
**Values:** True/False  
**Missing values:** False when data element is missing  
**Derivation function:** Inclusion criteria section  
**Derivation rules:** Various SQL expressions checking for NOT NULL values  
**Dependencies:** Respective source columns  
**Usage:** Used for data quality filtering and flowchart generation

##### include
**Label:** Final inclusion flag  
**Description:** Boolean flag indicating whether episode meets all inclusion criteria  
**Source data:** HES APC  
**Data type:** Boolean  
**Values:** True/False  
**Missing values:** None  
**Derivation function:** Inclusion criteria section  
**Derivation rules:** Cumulative AND of all inclusion criteria  
**Dependencies:** All inclusion criteria flags  
**Usage:** Used to filter dataset to valid episodes for analysis

### D00b-hes_apc_cips.py

This script creates Continuous Inpatient Spells (CIPS) from HES APC episodes.

#### Key Processing Steps:
1. **Transit Flag Creation**: Identifies inter-provider transfers
2. **Provider Spell Generation**: Groups episodes within same provider
3. **CIPS Generation**: Links provider spells into continuous care periods
4. **Spell Summarization**: Creates spell-level and CIPS-level summary tables

#### Derived Variables:

##### transit
**Label:** Transfer type flag  
**Description:** Categorizes episodes by transfer status  
**Source data:** HES APC  
**Data type:** Integer  
**Values:** 0 (no transfer), 1 (transfer out), 2 (transfer through), 3 (transfer in)  
**Missing values:** None  
**Derivation function:** Transit flag creation  
**Derivation rules:** Complex nested WHEN statements based on admission source/method and discharge destination/method  
**Dependencies:** admisorc, admimeth, disdest, dismeth  
**Usage:** Used for episode ordering within provider spells

##### p_spell_id
**Label:** Provider spell identifier  
**Description:** Unique identifier for each provider spell  
**Source data:** Derived  
**Data type:** String  
**Values:** Format: {person_id}-{procode5}-{p_spell_order}  
**Missing values:** None  
**Derivation function:** Provider spell grouping  
**Derivation rules:** Concatenation of person_id, provider code, and spell order  
**Dependencies:** person_id, procode5, p_spell_order  
**Usage:** Groups episodes within same provider continuous stay

##### cips_id
**Label:** Continuous Inpatient Spell identifier  
**Description:** Unique identifier for each CIPS  
**Source data:** Derived  
**Data type:** String  
**Values:** Format: {person_id}-{cips_order}  
**Missing values:** None  
**Derivation function:** CIPS grouping  
**Derivation rules:** Concatenation of person_id and CIPS order  
**Dependencies:** person_id, cips_order  
**Usage:** Links related provider spells into continuous care episodes

##### new_p_spell
**Label:** New provider spell flag  
**Description:** Flag indicating start of new provider spell  
**Source data:** Derived  
**Data type:** Integer  
**Values:** 0 (continuation), 1 (new spell)  
**Missing values:** None  
**Derivation function:** Provider spell logic  
**Derivation rules:** Based on admission date, episode start, and discharge method comparisons  
**Dependencies:** admidate, epistart, previous episode dates, dismeth  
**Usage:** Used to segment episodes into provider spells

##### new_cips
**Label:** New CIPS flag  
**Description:** Flag indicating start of new CIPS  
**Source data:** Derived  
**Data type:** Integer  
**Values:** 0 (continuation), 1 (new CIPS)  
**Missing values:** None  
**Derivation function:** CIPS logic  
**Derivation rules:** Based on time gap and transfer indicators between provider spells  
**Derivation rules detail:** CIPS continues if episode start ≤3 days from previous end AND (previous discharge to hospital OR current admission from hospital OR current admission is transfer)  
**Dependencies:** p_spell_epistart, prev_p_spell_epiend, discharge/admission codes  
**Usage:** Used to segment provider spells into CIPS

### D01-create_cohort.py

This script creates the study cohort on which this algorithm was developed, with inclusion criteria and baseline covariates 

#### Key Processing Steps:
1. **Demographics Loading**: Loads demographic data and assigns study dates
2. **GDPPR Linkage**: Adds primary care registration dates
3. **Prior MI Check**: Identifies patients with MI history before study period
4. **Age Calculation**: Calculates age at study start
5. **Inclusion Criteria**: Applies cohort inclusion criteria with flowchart
6. **Regional Mapping**: Adds geographical region information

#### Derived Variables:

##### age_study_start
**Label:** Age at study start  
**Description:** Patient age in years at study start date  
**Source data:** Demographics  
**Data type:** Decimal  
**Values:** Age in years (typically 18-120)  
**Missing values:** None after inclusion criteria applied  
**Derivation function:** Age calculation  
**Derivation rules:** `f.round(f.datediff('study_start_date', 'date_of_birth')/365.25, 2)`  
**Dependencies:** study_start_date, date_of_birth  
**Usage:** Used for inclusion criteria (age 18-120)

##### prior_mi_flag
**Label:** Prior MI flag  
**Description:** Flag indicating MI diagnosis before study period  
**Source data:** HES APC diagnosis  
**Data type:** Integer  
**Values:** 1 if prior MI, null otherwise  
**Missing values:** Null for patients without prior MI  
**Derivation function:** Prior MI check  
**Derivation rules:** Presence of I21 or I22 codes before study start date  
**Dependencies:** HES APC diagnosis codes, epistart dates  
**Usage:** Used for inclusion criteria (excludes patients with prior MI)

##### include
**Label:** Final cohort inclusion flag  
**Description:** Boolean flag indicating cohort membership  
**Source data:** Derived  
**Data type:** Boolean  
**Values:** True/False  
**Missing values:** None  
**Derivation function:** Inclusion criteria application  
**Derivation rules:** Cumulative AND of all cohort inclusion criteria  
**Dependencies:** All inclusion criteria flags  
**Usage:** Defines final study cohort

### D02-mi_algorithm_hes_apc.py

This script implements the MI detection algorithm for HES APC data using a decision tree approach.

#### Key Processing Steps:
1. **Data Preparation**: Filters to study period and cohort, creates diagnosis arrays
2. **Initial Classification**: Separates patients with/without any MI codes
3. **Algorithm Application**: Applies decision tree logic using pandas UDF
4. **Results Processing**: Generates terminal node classifications and flowchart

#### Derived Variables:

##### diag_i21
**Label:** I21 diagnosis flag  
**Description:** Flag indicating presence of I21 (STEMI) diagnosis in episode  
**Source data:** HES APC diagnosis codes  
**Data type:** Boolean  
**Values:** True/False  
**Missing values:** None  
**Derivation function:** Diagnosis flag creation  
**Derivation rules:** `f.array_contains('diag_3_array', 'I21')`  
**Dependencies:** diag_3_array  
**Usage:** Used in MI algorithm decision tree

##### diag_i22
**Label:** I22 diagnosis flag  
**Description:** Flag indicating presence of I22 (subsequent MI) diagnosis in episode  
**Source data:** HES APC diagnosis codes  
**Data type:** Boolean  
**Values:** True/False  
**Missing values:** None  
**Derivation function:** Diagnosis flag creation  
**Derivation rules:** `f.array_contains('diag_3_array', 'I22')`  
**Dependencies:** diag_3_array  
**Usage:** Used in MI algorithm decision tree

##### diag_i21_or_i22
**Label:** Any MI diagnosis flag  
**Description:** Flag indicating presence of either I21 or I22 diagnosis  
**Source data:** Derived  
**Data type:** Boolean  
**Values:** True/False  
**Missing values:** None  
**Derivation function:** Diagnosis flag creation  
**Derivation rules:** `diag_i21 OR diag_i22`  
**Dependencies:** diag_i21, diag_i22  
**Usage:** Primary filter for MI algorithm eligibility

##### diag_i21_and_i22
**Label:** Both MI diagnosis flags  
**Description:** Flag indicating presence of both I21 and I22 diagnoses in same episode  
**Source data:** Derived  
**Data type:** Boolean  
**Values:** True/False  
**Missing values:** None  
**Derivation function:** Diagnosis flag creation  
**Derivation rules:** `diag_i21 AND diag_i22`  
**Dependencies:** diag_i21, diag_i22  
**Usage:** Used to identify episodes with multiple MI types

##### first_mi_diagnosis
**Label:** First MI diagnosis flag  
**Description:** Flag indicating this is the first episode with MI diagnosis for the patient  
**Source data:** Derived  
**Data type:** Boolean  
**Values:** True/False  
**Missing values:** None  
**Derivation function:** Pandas UDF algorithm  
**Derivation rules:** Index of first MI episode equals current episode index  
**Dependencies:** Episode ordering, diag_i21_or_i22  
**Usage:** Decision tree node D2 - determines if first MI occurrence

##### qualify
**Label:** MI event qualification flag  
**Description:** Flag indicating whether episode qualifies as an MI event  
**Source data:** Derived  
**Data type:** Boolean  
**Values:** True/False  
**Missing values:** None  
**Derivation function:** Pandas UDF algorithm  
**Derivation rules:** Complex decision tree logic based on multiple factors  
**Dependencies:** Multiple algorithm variables  
**Usage:** Primary outcome indicating MI event detection

##### mi_date
**Label:** MI event date  
**Description:** Date assigned to MI event (typically episode start date)  
**Source data:** Derived  
**Data type:** Date  
**Values:** Episode start dates  
**Missing values:** Null for non-qualifying episodes  
**Derivation function:** Pandas UDF algorithm  
**Derivation rules:** Set to epistart for qualifying episodes  
**Dependencies:** qualify, epistart  
**Usage:** Temporal reference for MI event

##### mi_count
**Label:** MI event count  
**Description:** Number of MI events detected in the episode  
**Source data:** Derived  
**Data type:** Integer  
**Values:** 1 or 2  
**Missing values:** Null for non-qualifying episodes  
**Derivation function:** Pandas UDF algorithm  
**Derivation rules:** 1 for single MI type, 2 for both I21 and I22  
**Dependencies:** diag_i21_and_i22, qualify  
**Usage:** Used to expand events when both MI types present

##### terminal_node
**Label:** Decision tree terminal node  
**Description:** Final node reached in decision tree algorithm  
**Source data:** Derived  
**Data type:** Integer  
**Values:** 0-11  
**Missing values:** None  
**Derivation function:** Pandas UDF algorithm  
**Derivation rules:** Set based on decision tree path  
**Dependencies:** All decision variables  
**Usage:** Audit trail and algorithm validation

##### episode_lt_28d_from_mi
**Label:** Episode within 28 days flag  
**Description:** Flag indicating episode started <28 days from previous MI  
**Source data:** Derived  
**Data type:** Boolean  
**Values:** True/False  
**Missing values:** Null for first MI episodes  
**Derivation function:** Pandas UDF algorithm  
**Derivation rules:** Date difference calculation from last qualifying MI  
**Dependencies:** epistart, last_qualifying_mi_date  
**Usage:** Decision tree node D4 - temporal exclusion rule

##### prev_mi_had_i22
**Label:** Previous MI had I22 flag  
**Description:** Flag indicating whether previous MI event included I22 diagnosis  
**Source data:** Derived  
**Data type:** Boolean  
**Values:** True/False  
**Missing values:** Null when not applicable  
**Derivation function:** Pandas UDF algorithm  
**Derivation rules:** Lookup to previous qualifying episode's I22 status  
**Dependencies:** Previous episode data, diag_i22  
**Usage:** Decision tree node D6 - I22 sequence logic

##### same_cips_as_last_mi
**Label:** Same CIPS flag  
**Description:** Flag indicating episode is in same CIPS as previous MI  
**Source data:** Derived  
**Data type:** Boolean  
**Values:** True/False  
**Missing values:** Null when not applicable  
**Derivation function:** Pandas UDF algorithm  
**Derivation rules:** CIPS ID comparison with previous MI episode  
**Dependencies:** cips_id, previous episode data  
**Usage:** Decision tree node D7 - inpatient continuity logic

##### any_gap_in_mi_diagnosis
**Label:** Gap in MI diagnosis flag  
**Description:** Flag indicating gap in MI diagnoses between episodes  
**Source data:** Derived  
**Data type:** Boolean  
**Values:** True/False  
**Missing values:** Null when not applicable  
**Derivation function:** Pandas UDF algorithm  
**Derivation rules:** Checks for episodes without MI codes between current and last MI  
**Dependencies:** Episode sequence, diag_i21_or_i22  
**Usage:** Decision tree node D9 - diagnostic continuity logic

### D03-mi_algorithm_ons.py

This script implements the MI detection algorithm for ONS deaths data.

#### Key Processing Steps:
1. **Death Record Filtering**: Identifies deaths with MI as cause of death
2. **Hospital Death Detection**: Links with HES APC to identify in-hospital deaths
3. **Recent MI Event Check**: Identifies deaths within 7 days of HES MI event
4. **Algorithm Application**: Applies ONS-specific decision tree logic

#### Derived Variables:

##### mi_cod
**Label:** MI cause of death flag  
**Description:** Flag indicating MI mentioned as cause of death  
**Source data:** ONS deaths  
**Data type:** Boolean  
**Values:** True/False  
**Missing values:** None  
**Derivation function:** Cause of death filtering  
**Derivation rules:** I21 or I22 in underlying or mentioned causes of death  
**Dependencies:** underlying_cod, cod_mentioned_1, cod_mentioned_2  
**Usage:** Initial filter for potentially relevant deaths

##### in_hospital_death
**Label:** In-hospital death flag  
**Description:** Flag indicating death occurred in hospital setting  
**Source data:** Derived from HES APC linkage  
**Data type:** Boolean  
**Values:** True/False  
**Missing values:** False when no hospital record found  
**Derivation function:** Hospital death detection  
**Derivation rules:** Death within 1 day of discharge AND discharge method/destination indicating death  
**Dependencies:** date_of_death, disdate, dismeth, disdest  
**Usage:** Decision tree node D1 - excludes hospital deaths captured in HES

##### mi_event_less_than_7_days_prior
**Label:** Recent MI event flag  
**Description:** Flag indicating MI event in HES within 7 days before death  
**Source data:** Derived from HES algorithm results  
**Data type:** Boolean  
**Values:** True/False  
**Missing values:** False when no recent MI event  
**Derivation function:** Recent MI detection  
**Derivation rules:** Qualifying HES MI event within 7 days of death  
**Dependencies:** date_of_death, mi_date from HES algorithm  
**Usage:** Decision tree node D2 - excludes deaths related to recent HES MI

##### qualify
**Label:** Death MI event qualification flag  
**Description:** Flag indicating whether death qualifies as an MI event  
**Source data:** Derived  
**Data type:** Boolean  
**Values:** True/False  
**Missing values:** None  
**Derivation function:** ONS algorithm logic  
**Derivation rules:** NOT in_hospital_death AND NOT mi_event_less_than_7_days_prior  
**Dependencies:** in_hospital_death, mi_event_less_than_7_days_prior  
**Usage:** Primary outcome for ONS MI event detection

### D04a-mi_algorithm_events.py

This script combines MI events from HES APC and ONS deaths into a unified events table.

#### Key Processing Steps:
1. **Event Extraction**: Extracts qualifying events from both sources
2. **Event Expansion**: Handles multiple MI events per episode
3. **Event Combination**: Unions HES and ONS events
4. **Event Indexing**: Assigns sequential numbers to MI events per patient
5. **Fatality Classification**: Classifies events as fatal/non-fatal based on death timing

#### Derived Variables:

##### data_source
**Label:** Data source identifier  
**Description:** Identifies whether MI event comes from HES APC or ONS deaths  
**Source data:** Derived  
**Data type:** String  
**Values:** 'HES-APC', 'ONS Mortality'  
**Missing values:** None  
**Derivation function:** Event extraction  
**Derivation rules:** Literal value assigned during event creation  
**Dependencies:** Source dataset  
**Usage:** Tracks provenance of MI events

##### mi_index
**Label:** MI event index  
**Description:** Sequential number of MI event for each patient  
**Source data:** Derived  
**Data type:** Integer  
**Values:** 1, 2, 3, ... (sequential)  
**Missing values:** None  
**Derivation function:** Event indexing  
**Derivation rules:** Row number within patient ordered by MI date and data source  
**Dependencies:** person_id, mi_date, data_source  
**Usage:** Identifies first, second, etc. MI events

##### mi_total_count
**Label:** Total MI count  
**Description:** Total number of MI events for the patient  
**Source data:** Derived  
**Data type:** Integer  
**Values:** Positive integers  
**Missing values:** None  
**Derivation function:** Event counting  
**Derivation rules:** Maximum mi_index for each patient  
**Dependencies:** mi_index  
**Usage:** Used to identify final MI event for fatality assessment

##### death_within_28_days
**Label:** Death within 28 days flag  
**Description:** Flag indicating death occurred within 28 days of MI event  
**Source data:** Derived  
**Data type:** Boolean  
**Values:** True/False  
**Missing values:** None  
**Derivation function:** Fatality assessment  
**Derivation rules:** Date difference between MI event and death ≤28 days  
**Dependencies:** mi_date, date_of_death  
**Usage:** Used for fatal MI classification

##### mi_fatal_type
**Label:** MI fatality type  
**Description:** Classification of MI event as fatal or non-fatal  
**Source data:** Derived  
**Data type:** String  
**Values:** 'Fatal', 'Non-fatal'  
**Missing values:** None  
**Derivation function:** Fatality classification  
**Derivation rules:** 'Fatal' if last MI event and death within 28 days, otherwise 'Non-fatal'  
**Dependencies:** mi_index, mi_total_count, death_within_28_days  
**Usage:** Epidemiological classification for analysis

## 3. Algorithm Decision Tree Logic

### HES APC Algorithm Flow

The HES APC MI detection algorithm follows this decision tree structure:

1. **D1**: Does episode have I21 or I22 diagnosis?
   - No → **T1**: Not an MI event
   - Yes → Continue to D2

2. **D2**: Is this the first I21 or I22 diagnosis for patient?
   - Yes → Continue to D3
   - No → Continue to D4

3. **D3**: Does episode contain both I21 and I22?
   - No → **T2**: Single MI event on episode start date
   - Yes → **T3**: Two separate MI events on episode start date

4. **D4**: Is episode <28 days from previous recorded MI event?
   - Yes → Continue to D5
   - No → Continue to D7

5. **D5**: Does episode contain I22?
   - No → **T4**: Not an MI event
   - Yes → Continue to D6

6. **D6**: Did previous MI event contain I22?
   - No → **T5**: Single MI event on episode start date
   - Yes → **T6**: Not an MI event

7. **D7**: Is episode part of same CIPS as previous MI event?
   - No → Continue to D8
   - Yes → Continue to D9

8. **D8**: Does episode contain both I21 and I22?
   - No → **T7**: Single MI event on episode start date
   - Yes → **T8**: Two separate MI events on episode start date

9. **D9**: Gap in MI diagnosis between episodes?
   - No → **T9**: Not an MI event
   - Yes → Continue to D10

10. **D10**: Does episode contain both I21 and I22?
    - No → **T10**: Single MI event on episode start date
    - Yes → **T11**: Two separate MI events on episode start date

### ONS Deaths Algorithm Flow

The ONS deaths MI detection algorithm follows this simpler structure:

1. **D1**: Is there corresponding in-hospital death record in HES APC?
   - Yes → **T1**: Excluded (captured in HES APC)
   - No → Continue to D2

2. **D2**: Is there MI event in HES within 7 days before death?
   - Yes → **T2**: Excluded (relates to previous HES MI)
   - No → **T3**: Single MI event with date of death as event date

## 4. Data Quality and Validation

### Inclusion Criteria Applied

#### HES APC Data:
- Valid epikey, person_id, provider code
- Valid episode and admission dates  
- Finished episodes only (epistat = 3)

#### Study Cohort:
- Age 18-120 years at study start
- Male or female sex
- Alive on study start date
- Valid death records if applicable
- GDPPR registration before study start
- English LSOA
- No prior MI history


## 5. Output Specifications

### Event-Level Outputs

The primary algorithm outputs include:
- **person_id**: Patient identifier
- **mi_date**: Date of MI event
- **data_source**: Source of event detection (HES-APC/ONS Mortality)
- **mi_index**: Sequential MI event number
- **mi_fatal_type**: Fatal/non-fatal classification
- **terminal_node**: Decision tree endpoint reached
- **qualify**: Final qualification decision
- **Intermediate variables**: All decision variables preserved 

### Summary Outputs

- **Flowcharts**: Decision tree traversal counts with statistical disclosure control
- **Episode counts**: Detailed breakdown by terminal node and patient characteristics

## 6. Limitations of the Algorithm
The algorithm has been developed using HES APC data - as with all electronic health records there will be a delay between the patient event and the data being coded and available. This algorithm may not be suitable for all use cases. 
NHS administratively organises the data by Hospital Spells and Episodes which are recorded separately as single record (row of data) per patient. An episode is defined by NHS as a continuous period of admitted patient care administered under one consultant within healthcare providers. An MI occurring after an admission will be coded to the start date of the episode and as such, we recognise this may not be accurate to the day of the event. 
This algorithm may not be suitable for surgical or intervention trials with less than 6 months follow up or where there is a need for increased specificity to identify multiple events within a very short period (<24 hrs). In these cases, there may be an option to adopt a hybrid approach where such events are identified or adjudicated with traditional data collection.


## 7. Contributors

- *James Farrell, BHF Data Science Centre*
- *Laura Sherlock, BHF Data Science Centre*

## 8. Contact details 
Should you have any suggestions for improvements of the algorithm and/or the related documentation, or should you have any questions, please email the BHF Health Data Science team at  
<br>
<br>
<br>