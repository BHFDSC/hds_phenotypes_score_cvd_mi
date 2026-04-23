# Documentation for Derived Variables

This document provides documentation of derived variables generated when the `pipeline_run.R` script is executed as part of the SCORE-CVD Myocardial Infarction (MI) algorithm.

The derived variables are grouped and documented by the specific function script in which they are created:

1. `prepare_hes_apc()` -- variables derived while preparing HES APC data
2. `prepare_ons_deaths()` -- variables derived while preparing ONS death data
3. `generate_cips()` -- variables derived during creation of Continuous Inpatient Spells (CIPS)
4. `process_hes_apc_mi()` -- variables derived while identifying and classifying MI events in HES APC
5. `process_ons_deaths_mi()` -- variables derived while identifying and classifying MI events in ONS deaths

Each derived variable is documented using the following format:

- **Label:** Brief description of the variable
- **Description:** Explanation of what the variable represents
- **Source data:** Originating dataset(s) used in its derivation
- **Data type:** Expected data type (e.g., integer, logical, date)
- **Values:** Possible or expected values
- **Missing values:** Conditions under which the variable may be missing
- **Derivation function:** The function in which the variable is created
- **Derivation rules:** Logic or conditions used to create the variable
- **Dependencies:** Other variables required for derivation
- **Usage:** Role of the variable within the MI classification algorithm

## 1. prepare_hes_apc()

The variables listed here are derived when the `prepare_hes_apc()` function is executed.

### admidate

**Label:** Date of admission (cleaned)  
**Description:** Imputed admission date if it is missing and where epiorder is 1 and epistart is available.  
**Source data:** HES APC  
**Data type:** Date  
**Values:** Hospital admission dates  
**Missing values:** NA possible if imputation conditions not met  
**Derivation function:** inline in `prepare_hes_apc()`  
**Derivation rules:** `if_else(is.na(admidate) & !is.na(epistart) & epiorder == 1, epistart, admidate)`  
**Dependencies:** admidate, epistart, epiorder  
**Usage:** Used for inpatient spell derivation and filtering valid episodes for downstream analysis

### known_person_id

**Label:** Known person ID  
**Description:** Flag indicating whether the person ID is present.  
**Source data:** HES APC  
**Data type:** Logical  
**Values:** TRUE = known, FALSE = missing  
**Missing values:** None  
**Derivation function:** inline in `prepare_hes_apc()`  
**Derivation rules:** `if_else(!is.na(person_id), TRUE, FALSE)`  
**Dependencies:** person_id  
**Usage:** Used in filtering valid episodes for downstream analysis

### known_epikey

**Label:** Known episode key  
**Description:** Flag indicating whether epikey is present.  
**Source data:** HES APC  
**Data type:** Logical  
**Values:** TRUE = known, FALSE = missing  
**Missing values:** None  
**Derivation function:** inline in `prepare_hes_apc()`  
**Derivation rules:** `if_else(!is.na(epikey), TRUE, FALSE)`  
**Dependencies:** epikey  
**Usage:** Used in filtering valid episodes for downstream analysis

### known_procode5

**Label:** Known provider code  
**Description:** Flag indicating whether the provider code is present.  
**Source data:** HES APC  
**Data type:** Logical  
**Values:** TRUE = known, FALSE = missing  
**Missing values:** None  
**Derivation function:** inline in `prepare_hes_apc()`  
**Derivation rules:** `if_else(!is.na(procode5), TRUE, FALSE)`  
**Dependencies:** procode5  
**Usage:** Used in filtering valid episodes for downstream analysis

### known_epistart

**Label:** Known episode start date  
**Description:** Flag indicating whether epistart is present.  
**Source data:** HES APC  
**Data type:** Logical  
**Values:** TRUE = known, FALSE = missing  
**Missing values:** None  
**Derivation function:** inline in `prepare_hes_apc()`  
**Derivation rules:** `if_else(!is.na(epistart), TRUE, FALSE)`  
**Dependencies:** epistart  
**Usage:** Used in filtering valid episodes for downstream analysis

### known_epiend

**Label:** Known episode end date  
**Description:** Flag indicating whether epiend is present.  
**Source data:** HES APC  
**Data type:** Logical  
**Values:** TRUE = known, FALSE = missing  
**Missing values:** None  
**Derivation function:** inline in `prepare_hes_apc()`  
**Derivation rules:** `if_else(!is.na(epiend), TRUE, FALSE)`  
**Dependencies:** epiend  
**Usage:** Used in filtering valid episodes for downstream analysis

### known_admidate

**Label:** Known admission date  
**Description:** Flag indicating whether cleaned admidate is present.  
**Source data:** HES APC  
**Data type:** Logical  
**Values:** TRUE = known, FALSE = missing  
**Missing values:** None  
**Derivation function:** inline in `prepare_hes_apc()`  
**Derivation rules:** `if_else(!is.na(admidate))`  
**Dependencies:** admidate (after cleaning)  
**Usage:** Used in filtering valid episodes for downstream analysis

### complete_episode

**Label:** Episode is complete  
**Description:** Indicates whether an episode has finished.  
**Source data:** HES APC  
**Data type:** Logical  
**Values:** TRUE if epistat == 3, else FALSE  
**Missing values:** None  
**Derivation function:** inline in `prepare_hes_apc()`  
**Derivation rules:** `if_else(epistat == 3, TRUE, FALSE, missing = FALSE)`  
**Dependencies:** epistat  
**Usage:** Used to exclude incomplete episodes from analysis

### c0 to c7

**Label:** Inclusion criteria flags  
**Description:** Series of logical filters applied step-by-step to derive the final inclusion flag.  
**Source data:** HES APC  
**Data type:** Logical  
**Values:** TRUE/FALSE  
**Missing values:** None  
**Derivation function:** inline in `prepare_hes_apc()`  
**Derivation rules:**

```r
c0 = TRUE,
c1 = c0 & known_person_id,
c2 = c1 & known_epikey,
c3 = c2 & known_procode5,
c4 = c3 & complete_episode,
c5 = c4 & known_epistart,
c6 = c5 & known_epiend,
c7 = c6 & known_admidate,
```

**Dependencies:** known_person_id, known_epikey, known_procode5, known_epistart, known_epiend, known_admidate, complete_episode  
**Usage:** Flowchart tracking and final cohort inclusion

### include

**Label:** Final inclusion flag  
**Description:** Final logical filter based on all previous criteria (c7)  
**Source data:** HES APC  
**Data type:** Logical  
**Values:** TRUE/FALSE  
**Missing values:** None  
**Derivation function:** inline in `prepare_hes_apc()`  
**Derivation rules:** `include = c7`  
**Dependencies:** c7  
**Usage:** Used to select final clean dataset

## 2. generate_cips()

The variables listed here are derived when the `generate_cips()` function is executed.

### transit

**Label:** Episode transfer flag  
**Description:** Categorical flag identifying transfer status of each episode based on admission source/method and discharge destination codes  
**Source data:** HES APC  
**Data type:** Integer  
**Values:**

- 0 = No transfer
- 1 = Transfer out only
- 2 = Transfer in and out
- 3 = Transfer in only

**Missing values:** None  
**Derivation function:** `generate_cips()`  
**Derivation rules:**

When:
- 0 = No transfer
- 1 = Transfer out only
- 2 = Transfer in and out
- 3 = Transfer in only

**Dependencies:** admisorc, admimeth, disdest  
**Usage:** Used in sorting and identifying potential transfer episodes for provider spell grouping

### new_p_spell

**Label:** New provider spell indicator  
**Description:** Binary flag identifying if an episode starts a new provider spell  
**Source data:** HES APC  
**Data type:** Integer  
**Values:** 1 = New spell, 0 = Continuation of previous spell  
**Missing values:** None  
**Derivation function:** `generate_cips()`  
**Derivation rules:**

When admidate == previous admidate, or epistart==previous_epistart, or previous_dismeth is 8 or 9 (unknown) & epistart=previous_epidend then 0 (Continuation of previous spell)

Otherwise default = 1

**Dependencies:** admidate, epistart, epiend, dismeth  
**Usage:** Used to group episodes into provider spells.

### p_spell_order

**Label:** Provider spell sequence order  
**Description:** Sequential index of provider spell for a person within a provider.  
**Source data:** HES APC  
**Data type:** Integer  
**Values:** Starts from 1 and increments  
**Missing values:** None  
**Derivation function:** `generate_cips()`  
**Derivation rules:** `cumsum(new_p_spell)` within person_id, procode5  
**Dependencies:** new_p_spell  
**Usage:** Used to identify provider spells.

### p_spell_id

**Label:** Provider spell ID  
**Description:** Unique identifier for each provider spell for a person.  
**Source data:** HES APC  
**Data type:** Character  
**Values:** Concatenation of person_id, procode5, and p_spell_order  
**Missing values:** None  
**Derivation function:** `generate_cips()`  
**Derivation rules:** `paste0(person_id, "-", procode5, "-", p_spell_order)`  
**Dependencies:** person_id, procode5, p_spell_order  
**Usage:** Used to link episodes within the same provider spell and for CIPS derivation.

### p_spell_first_episode / p_spell_last_episode

**Label:** First/last episode in provider spell  
**Description:** Binary flag for whether an episode is the first or last in its provider spell.  
**Source data:** HES APC  
**Data type:** Integer  
**Values:** 1 = Yes, 0 = No  
**Missing values:** None  
**Derivation function:** `generate_cips()`  
**Derivation rules:** 
- `p_spell_first_episode = if_else(p_spell_epiorder == 1, 1, 0)`  
- `p_spell_last_episode = if_else(p_spell_epiorder == p_spell_epicount, 1, 0)`

**Dependencies:** p_spell_epiorder, p_spell_epicount  
**Usage:** Used to extract start/end info for provider spells.

### new_cips

**Label:** New CIPS indicator  
**Description:** Binary flag indicating whether a provider spell starts a new Continuous Inpatient Spell (CIPS).  
**Source data:** HES APC  
**Data type:** Integer  
**Values:** 1 = New CIPS, 0 = Continuation  
**Missing values:** None  
**Derivation function:** `generate_cips()`  
**Derivation rules:**

When spell_date_difference <= 3 & spell_date_difference >= 0 & (previous_spell_disdest or previous_p_spell_admisorc or previous_p_spell_admimeth has a transfer code), then 0 (continuation)

Otherwise default = 1

**Dependencies:** p_spell_epistart, prev_p_spell_epiend, p_spell_admisorc, p_spell_admimeth, prev_p_spell_disdest  
**Usage:** Used to group provider spells into CIPS.

### cips_order

**Label:** CIPS sequence order  
**Description:** Sequential index of CIPS per person.  
**Source data:** HES APC  
**Data type:** Integer  
**Values:** Starts from 1  
**Missing values:** None  
**Derivation function:** `generate_cips()`  
**Derivation rules:** `cumsum(new_cips)` within person_id  
**Dependencies:** new_cips  
**Usage:** Used to order CIPS.

### cips_id

**Label:** CIPS ID  
**Description:** Unique identifier for each CIPS instance.  
**Source data:** HES APC  
**Data type:** Character  
**Values:** Concatenation of person_id and cips_order  
**Missing values:** None  
**Derivation function:** `generate_cips()`  
**Derivation rules:** `paste0(person_id, "-", cips_order)`  
**Dependencies:** person_id, cips_order  
**Usage:** Key identifier for each continuous inpatient spell.

### cips_first_spell / cips_last_spell

**Label:** First/last provider spell in a CIPS  
**Description:** Binary flag for first or last spell in a continuous inpatient spell.  
**Source data:** HES APC  
**Data type:** Integer  
**Values:** 1 = Yes, 0 = No  
**Missing values:** None  
**Derivation function:** `generate_cips()`  
**Derivation rules:**

- `cips_first_spell = if_else(cips_spell_order == 1, 1, 0)`
- `cips_last_spell = if_else(cips_spell_order == cips_spell_count, 1, 0)`

**Dependencies:** cips_spell_order, cips_spell_count  
**Usage:** Used to identify first and last CIPS spells

## 3. prepare_ons_deaths()

The variables listed here are derived when the `prepare_ons_deaths()` function is executed.

### mi_code_present

**Label:** MI code present  
**Description:** MI code (I21 or I22) present in data as underlying cause of death, or in first or second 'secondary' cause of death  
**Source data:** ONS deaths  
**Data type:** logical  
**Values:**

- TRUE = MI mentioned (ICD-10: I21 or I22 underlying cause of death, or in first or second 'secondary' cause of death)
- FALSE = MI not mentioned

**Missing values:** None (explicitly set to FALSE if NA)  
**Derivation function:** inline in `prepare_ons_deaths()`  
**Derivation rules:**

- TRUE if any of the following contain "I21" or "I22":
  - underlying_cod
  - cod_mentioned_1
  - cod_mentioned_2
- FALSE otherwise or if value is missing

**Dependencies:** underlying_cod, cod_mentioned_1, cod_mentioned_2  
**Usage:** Used to identify individuals who have MI code present, used for removing duplicated records

### non_duplicated_record

**Label:** Deduplicated death record flag  
**Description:** Identifies one unique death record per person based on date and MI status  
**Source data:** ONS deaths  
**Data type:** logical  
**Values:**

- TRUE = retained record
- FALSE = duplicate or lower-priority record

**Missing values:** None  
**Derivation function:** inline in `prepare_ons_deaths()`  
**Derivation rules:**

- If only one record per person, retain it
- If multiple records:
  - Keep the earliest death
  - Prefer records with mi_cod == TRUE

**Dependencies:** person_id, date_of_death, mi_cod  
**Usage:** Ensures dataset contains only one death record per individual for clean downstream analysis

### known_person_id

**Label:** Known person ID  
**Description:** Indicates whether person_id is present  
**Source data:** ONS deaths  
**Data type:** logical  
**Values:**

- TRUE = person ID present
- FALSE = person ID missing

**Missing values:** None  
**Derivation function:** inline in `prepare_ons_deaths()`  
**Derivation rules:**

- TRUE if person_id is not NA
- FALSE otherwise

**Dependencies:** person_id  
**Usage:** Used in inclusion criteria for dataset cleaning

### known_death_date

**Label:** Known date of death  
**Description:** Indicates whether date_of_death is present  
**Source data:** ONS deaths  
**Data type:** logical  
**Values:**

- TRUE = valid death date present
- FALSE = missing or placeholder date

**Missing values:** None  
**Derivation function:** inline in `prepare_ons_deaths()`  
**Derivation rules:**

- TRUE if date_of_death is not NA and not one of the placeholder dates ("1800-01-01", "1801-01-01")

**Dependencies:** date_of_death  
**Usage:** Used in inclusion filters to clean out invalid death records

### c0, c1, c2, c3

**Label:** Inclusion criteria flags  
**Description:** Sequential quality control steps applied to filter valid death records  
**Source data:** ONS deaths  
**Data type:** logical  
**Values:**

- TRUE = passes criterion
- FALSE = fails criterion

**Missing values:** None  
**Derivation function:** inline in `prepare_ons_deaths()`  
**Derivation rules:**

- c0: all rows (set to TRUE)
- c1: c0 & known_person_id
- c2: c1 & known_death_date
- c3: c2 & non_duplicated_record

**Dependencies:** known_person_id, known_death_date, non_duplicated_record  
**Usage:** Input for include flag and used in flowchart of dataset cleaning

### include

**Label:** Final inclusion flag  
**Description:** Composite indicator that a row passes all quality checks  
**Source data:** ONS deaths  
**Data type:** logical  
**Values:**

- TRUE = include row in final dataset
- FALSE = exclude from analysis

**Missing values:** None  
**Derivation function:** inline in `prepare_ons_deaths()`  
**Derivation rules:**

- `include = c3`

**Dependencies:** c0, c1, c2, c3  
**Usage:** Used to filter the final ONS dataset saved to file

## 4. process_hes_apc_mi()

The variables listed here are derived when the `process_hes_apc_mi()` function is executed.

### diag_i21

**Label:** ICD-10 I21 diagnosis flag  
**Description:** Indicator for presence of an I21 diagnosis code in concatenated diagnosis string  
**Source data:** HES APC  
**Data type:** logical  
**Values:** TRUE = contains I21 code, FALSE = does not  
**Missing values:** FALSE if diagnosis is missing  
**Derivation function:** Inline in `process_hes_apc_mi()`  
**Derivation rules:** TRUE if diag_3_concat contains "I21"  
**Dependencies:** diag_3_concat  
**Usage:** Input to MI algorithm logic

### diag_i22

**Label:** ICD-10 I22 diagnosis flag  
**Description:** Indicator for presence of an I22 diagnosis code in concatenated diagnosis string  
**Source data:** HES APC  
**Data type:** logical  
**Values:** TRUE = contains I22 code, FALSE = does not  
**Missing values:** FALSE if diagnosis is missing  
**Derivation function:** Inline in `process_hes_apc_mi()`  
**Derivation rules:** TRUE if diag_3_concat contains "I22"  
**Dependencies:** diag_3_concat  
**Usage:** Input to MI algorithm logic

### diag_i21_or_i22

**Label:** I21 or I22 diagnosis flag  
**Description:** Combined indicator for presence of I21 or I22 code  
**Source data:** HES APC  
**Data type:** logical  
**Values:** TRUE if I21 or I22 present, FALSE otherwise  
**Missing values:** FALSE  
**Derivation function:** Inline in `process_hes_apc_mi()`  
**Derivation rules:** `diag_i21 OR diag_i22`  
**Dependencies:** diag_i21, diag_i22  
**Usage:** Primary trigger for entry into MI algorithm

### diag_i21_and_i22

**Label:** I21 and I22 co-diagnosis flag  
**Description:** Indicator that both I21 and I22 codes are present in same episode  
**Source data:** HES APC  
**Data type:** logical  
**Values:** TRUE if both I21 and I22 present, FALSE otherwise  
**Missing values:** FALSE  
**Derivation function:** Inline in `process_hes_apc_mi()`  
**Derivation rules:** `diag_i21 AND diag_i22`  
**Dependencies:** diag_i21, diag_i22  
**Usage:** Determines whether one or two MI events occurred

### index_num

**Label:** Row index per person  
**Description:** Unique row index for each episode per person  
**Source data:** HES APC  
**Data type:** integer  
**Values:** Integer ≥ 1  
**Missing values:** None  
**Derivation function:** Inline in `process_hes_apc_mi()`  
**Derivation rules:** `row_number()` per person_id  
**Dependencies:** person_id  
**Usage:** Ordering of episodes and identifying first MI

### any_mi_diag

**Label:** Any MI diagnosis indicator  
**Description:** Logical flag for whether person has any I21 or I22 code  
**Source data:** HES APC  
**Data type:** logical  
**Values:** TRUE if any diag_i21_or_i22 = TRUE, FALSE otherwise  
**Missing values:** None  
**Derivation function:** Inline in `process_hes_apc_mi()`  
**Derivation rules:** `any(diag_i21_or_i22)` within person_id  
**Dependencies:** diag_i21_or_i22  
**Usage:** Used to identify those with or without MI

### first_mi_diagnosis

**Label:** First MI diagnosis  
**Description:** Indicates the first episode with I21 or I22 per individual  
**Source data:** HES APC  
**Data type:** logical  
**Values:** TRUE = first, FALSE = not first  
**Missing values:** FALSE if no MI  
**Derivation function:** Inline in `process_hes_apc_mi()`  
**Derivation rules:** TRUE where index_num equals first occurrence of diag_i21_or_i22  
**Dependencies:** diag_i21_or_i22, index_num  
**Usage:** Input to decision tree logic

### qualify

**Label:** Qualifying MI episode  
**Description:** Flag indicating whether episode qualifies as an MI event  
**Source data:** HES APC  
**Data type:** logical  
**Values:** TRUE = qualifying MI, FALSE = not qualifying  
**Missing values:** None  
**Derivation function:** Inline in `process_hes_apc_mi()`  
**Derivation rules:** Logic tree based on diagnosis, timing, and CIPS structure  
**Dependencies:** diag_i21_or_i22, first_mi_diagnosis, timing to last MI, CIPS ID  
**Usage:** Identifies valid MI episodes

### mi_date

**Label:** MI date  
**Description:** Start date of qualifying MI episode  
**Source data:** HES APC  
**Data type:** date  
**Values:** epistart if qualify == TRUE, NA otherwise  
**Missing values:** NA if not qualifying  
**Derivation function:** Inline in `process_hes_apc_mi()`  
**Derivation rules:** epistart where qualify == TRUE  
**Dependencies:** qualify, epistart  
**Usage:** Identifies date of MI for downstream analysis

### mi_count

**Label:** MI event count  
**Description:** Number of MI events identified in episode  
**Source data:** HES APC  
**Data type:** integer  
**Values:** 1 = single MI, 2 = double MI  
**Missing values:** NA if not qualifying  
**Derivation function:** Inline in `process_hes_apc_mi()`  
**Derivation rules:** Based on presence of both I21 and I22  
**Dependencies:** diag_i21_and_i22  
**Usage:** Used to count MI events per episode

### terminal_node

**Label:** Terminal node code  
**Description:** Code for terminal node of MI classification decision tree  
**Source data:** HES APC  
**Data type:** integer  
**Values:** 0-11 (see MI_algorithm_decision_tree in docs/)  
**Missing values:** NA for unprocessed rows  
**Derivation function:** Inline in `process_hes_apc_mi()`  
**Derivation rules:** Nested decision tree logic  
**Dependencies:** Multiple flags including qualify, diag_i21, diag_i22, etc.  
**Usage:** Categorical indicator of MI logic outcome

### terminal_node_description

**Label:** Terminal node description  
**Description:** Description of MI logic result  
**Source data:** HES APC  
**Data type:** character  
**Values:** T0 to T11  
**Missing values:** NA for unprocessed  
**Derivation function:** Inline in `process_hes_apc_mi()`  
**Derivation rules:** Based on terminal_node integer  
**Dependencies:** terminal_node  
**Usage:** Interpretation and reporting of MI logic results

### last_qualifying_mi_date

**Label:** Last MI date  
**Description:** Date of previous qualifying MI for same person  
**Source data:** HES APC  
**Data type:** date  
**Values:** mi_date from most recent qualifying episode  
**Missing values:** NA if no prior MI  
**Derivation function:** Inline in `process_hes_apc_mi()`  
**Derivation rules:** Fetch from previous rows in grouped person_id  
**Dependencies:** qualify, mi_date  
**Usage:** Time interval logic for 28-day MI checks

### episode_lt_28d_from_mi

**Label:** Episode within 28 days of last MI  
**Description:** Indicator if current episode is within 28 days of prior MI  
**Source data:** HES APC  
**Data type:** logical  
**Values:** TRUE, FALSE  
**Missing values:** NA if no previous MI  
**Derivation function:** Inline in `process_hes_apc_mi()`  
**Derivation rules:** `epistart - last_qualifying_mi_date < 28`  
**Dependencies:** epistart, last_qualifying_mi_date  
**Usage:** Input to decision logic

### prev_mi_had_i22

**Label:** Previous MI had I22  
**Description:** Flag indicating if prior MI contained an I22 diagnosis  
**Source data:** HES APC  
**Data type:** logical  
**Values:** TRUE, FALSE  
**Missing values:** NA if no previous MI  
**Derivation function:** Inline in `process_hes_apc_mi()`  
**Derivation rules:** Pull diag_i22 from previous MI row  
**Dependencies:** qualify, diag_i22  
**Usage:** Decision rule for repeated MI episodes

### same_cips_as_last_mi

**Label:** Same CIPS as prior MI  
**Description:** Logical indicator whether current episode is in same spell as last MI  
**Source data:** HES APC  
**Data type:** logical  
**Values:** TRUE, FALSE  
**Missing values:** NA if no prior MI  
**Derivation function:** Inline in `process_hes_apc_mi()`  
**Derivation rules:** cips_id == cips_id of last qualifying MI  
**Dependencies:** cips_id, last_qualifying_mi_date  
**Usage:** Input to decision logic

### any_gap_in_mi_diagnosis

**Label:** Gap in MI diagnosis  
**Description:** Indicator of non-MI episode between current and last MI within same spell  
**Source data:** HES APC  
**Data type:** logical  
**Values:** TRUE, FALSE  
**Missing values:** NA if no prior MI  
**Derivation function:** Inline in `process_hes_apc_mi()`  
**Derivation rules:** At least one episode without I21/I22 between current and prior MI  
**Dependencies:** diag_i21_or_i22, index_num  
**Usage:** Input to decision logic

## 5. process_ons_deaths_mi()

The variables listed here are derived when the `process_ons_deaths_mi()` function is executed.

### mi_cod

**Label:** MI code present  
**Description:** MI code (I21 or I22) present in data as underlying cause of death, or in first or second 'secondary' cause of death  
**Source data:** ONS deaths  
**Data type:** logical  
**Values:** TRUE (MI mentioned), FALSE (not mentioned)  
**Missing values:** FALSE if NA  
**Derivation function:** inline in `process_ons_deaths_mi()`  
**Derivation rules:**

- TRUE if any of underlying_cod, cod_mentioned_1, or cod_mentioned_2 contain "I21" or "I22"
- FALSE otherwise

**Dependencies:** underlying_cod, cod_mentioned_1, cod_mentioned_2  
**Usage:** Used to identify MI-related deaths

### in_hospital_death

**Label:** In-hospital death  
**Description:** Indicator for whether death occurred during a hospital admission  
**Source data:** ONS deaths and HES APC  
**Data type:** integer (0/1)  
**Values:** 1 = in-hospital death, 0 = not in-hospital  
**Missing values:** NA if all values are NA for person  
**Derivation function:** inline in `process_ons_deaths_mi()`  
**Derivation rules:**

- TRUE if either:
  - death occurred within 1 day of discharge (date_of_death - disdate <= 1) **and** discharge was to death (dismeth == 4 or disdest == 79)
  - OR death occurred before the recorded hospital discharge, where discharge was to death

**Dependencies:** date_of_death, disdate, dismeth, disdest, epiend  
**Usage:** Used to classify terminal node of MI algorithm

### mi_event_7_days_before_death

**Label:** MI within 7 days before death  
**Description:** Indicator for a qualifying MI admission occurring less than 7 days before death  
**Source data:** ONS deaths and HES APC  
**Data type:** integer (0/1)  
**Values:** 1 = qualifying MI within 7 days, 0 = otherwise  
**Missing values:** NA if MI date is missing  
**Derivation function:** inline in `process_ons_deaths_mi()`  
**Derivation rules:**

TRUE if qualify == TRUE in HES-APC MI dataset and date_of_death - mi_date < 7

**Dependencies:** date_of_death, mi_date, qualify  
**Usage:** Used to classify terminal node of MI algorithm

### qualify

**Label:** Qualifying MI event  
**Description:** Final algorithm flag for MI event identified only in ONS death records, not linked to recent admission in HES APC  
**Source data:** ONS deaths  
**Data type:** logical  
**Values:** TRUE (MI event), FALSE (excluded by other criteria)  
**Missing values:** None  
**Derivation function:** inline in `process_ons_deaths_mi()`  
**Derivation rules:**

- TRUE if mi_cod == TRUE and both in_hospital_death == 0 and mi_event_less_than_7_days_prior == 0

**Dependencies:** mi_cod, in_hospital_death, mi_event_less_than_7_days_prior  
**Usage:** Filters events for MI event counts and provided as a part of the outputs

### terminal_node

**Label:** Terminal node classification  
**Description:** Integer code indicating terminal classification of the MI algorithm  
**Source data:** ONS deaths  
**Data type:** integer  
**Values:**

- 0: Not an MI event
- 1: In-hospital MI death
- 2: In hospital MI within 7 days of death
- 3: Qualifying MI death event

**Missing values:** NA if data incomplete  
**Derivation function:** inline in `process_ons_deaths_mi()`  
**Derivation rules:**

- Nested conditions based on mi_cod, in_hospital_death, mi_event_less_than_7_days_prior

**Dependencies:** mi_cod, in_hospital_death, mi_event_less_than_7_days_prior  
**Usage:** Used to classify MI events based on MI algorithm decision tree -- provided as part of the outputs

### mi_date

**Label:** Date of MI  
**Description:** Date of death if qualify is TRUE (i.e., date_of_death is date of MI when it qualifies as an MI death event)  
**Source data:** ONS deaths  
**Data type:** date  
**Values:** date_of_death if qualify == TRUE, otherwise NA  
**Missing values:** NA  
**Derivation function:** inline in `process_ons_deaths_mi()`  
**Derivation rules:**

- `mi_date = date_of_death` if qualify == TRUE

**Dependencies:** qualify, date_of_death  
**Usage:** Date of MI for qualifying MI death events