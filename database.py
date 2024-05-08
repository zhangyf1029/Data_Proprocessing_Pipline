import os
import duckdb
import glob
import hydra
import logging

logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger(__name__)

#Helpar function

def create_table(file_pattern_Beneficiary, file_pattern_Claim, Groups, Age_case_statement):
    """
    Union the Beneficiary_Summary data for all three years of a sample into one table, and join it with the Inpatient_Claims data.
    Obtain yearly state level all-cause hospitalization risk by Sex, Race, and prespecified Age groups.
    All-cause hospitalization risk is defined as the number of unique hospitalizations per group.
    """
    Group_by = ", ".join(Groups) #get groups to use for GROUP BY
    files_Beneficiary = glob.glob(file_pattern_Beneficiary) #get all Beneficiary_Summary files that match the pattern
    conn = duckdb.connect(database=':memory:')
    #check if files are found
    if not files_Beneficiary:
        LOGGER.error(f"No files found for pattern {file_pattern_Beneficiary}/{file_pattern_Claim}")
        raise FileNotFoundError(f"No files found")
    else:    
        #Union all years Beneficiary_Summary files in one sample into a single table with specific columns
        LOGGER.info(f"Creating table for Beneficiary Summary files .......")
        query = " UNION ALL ".join(
        [f"""SELECT '{file.split('_')[2]}' AS year, 
         DESYNPUF_ID, BENE_BIRTH_DT, BENE_DEATH_DT, BENE_SEX_IDENT_CD AS Sex, BENE_RACE_CD AS Race, SP_STATE_CODE, BENE_HMO_CVRAGE_TOT_MONS,
         CAST(SUBSTR(CAST(BENE_BIRTH_DT AS VARCHAR), 1, 4) || '-' || 
            SUBSTR(CAST(BENE_BIRTH_DT AS VARCHAR), 5, 2) || '-' || 
            SUBSTR(CAST(BENE_BIRTH_DT AS VARCHAR), 7, 2) AS DATE) AS birth_date,
         CASE
            WHEN BENE_DEATH_DT IS NOT NULL THEN
                DATE_PART('year', AGE(
                CAST(SUBSTR(CAST(BENE_DEATH_DT AS VARCHAR), 1, 4) || '-' || 
                     SUBSTR(CAST(BENE_DEATH_DT AS VARCHAR), 5, 2) || '-' || 
                     SUBSTR(CAST(BENE_DEATH_DT AS VARCHAR), 7, 2) AS DATE),
                birth_date))
            ELSE
                DATE_PART('year', AGE(CURRENT_DATE, birth_date))
         END AS Age,
         {Age_case_statement}
            FROM read_csv_auto('{file}')""" 
         for file in files_Beneficiary]) #get specific columns from each file
        conn.execute(f"CREATE TABLE unified_table AS {query}")
        LOGGER.info(f"Table created successfully")
        LOGGER.info(f"Creating table for Inpatient Claims file .......")
        #Create table for Inpatient Claims file
        conn.execute(f"""
                     CREATE TABLE claims_table AS SELECT CAST(CLM_ID AS VARCHAR) AS CLM_ID, DESYNPUF_ID,
                     CAST(SUBSTR(CAST(CLM_ADMSN_DT AS VARCHAR), 1, 4) || '-' || 
                        SUBSTR(CAST(CLM_ADMSN_DT AS VARCHAR), 5, 2) || '-' || 
                        SUBSTR(CAST(CLM_ADMSN_DT AS VARCHAR), 7, 2) AS DATE) AS CLM_ADMSN_DT
                     FROM read_csv_auto('{file_pattern_Claim}')
                     """)
        LOGGER.info(f"Table created successfully")
        LOGGER.info(f"Obtaining yearly state level all-cause hospitalization risk stratified by {Group_by}")
        #Join the two tables
        query = """
        SELECT unified_table.*, claims_table.CLM_ID, claims_table.CLM_ADMSN_DT
        FROM unified_table
        LEFT JOIN claims_table
        ON unified_table.DESYNPUF_ID = claims_table.DESYNPUF_ID
        """
        conn.execute(f"CREATE TABLE result_table AS {query}")
        
        #Obtain yearly state level all-cause hospitalization risk stratified by sex, race, and age prespecified groups
        result = conn.execute(f"""
        SELECT year, SP_STATE_CODE, {Group_by}, 
        COUNT(DISTINCT CLM_ID) AS Hospitalization_Risk
        FROM result_table
        Group BY year, SP_STATE_CODE, {Group_by}  
        ORDER BY year, SP_STATE_CODE, {Group_by}    
        """).fetchdf()
        return result
       
def generate_age_case(Age_Groups):
    """
    Generate CASE WHEN statement for prespecified age groups.
    """
    if not Age_Groups:
        msg = "The age range list cannot be empty."
        LOGGER.error(msg)
        raise ValueError(msg)
    case_ = "CASE "
    case_ += f"WHEN Age < {Age_Groups[0]} THEN '<{Age_Groups[0]}' "
    for start, end in zip(Age_Groups, Age_Groups[1:]):
        case_ += f"WHEN Age BETWEEN {start} AND {end} THEN '{start}-{end}' "
    case_ += f"WHEN Age > {Age_Groups[-1]} THEN '>{Age_Groups[-1]}' "
    case_ += "END AS Age_Groups"
    return case_


@hydra.main(config_path="./conf", config_name="config", version_base=None)
def main(cfg):
    """
    Create a large table for data in one sample file (all three years are loaded by default).
    "Obtain yearly state level all-cause hospitalization risk stratified by sex, race, and age prespecified groups."
    """
    out_path = cfg.database.Output_Path
    #check if output path exists if not create it
    if not os.path.exists(out_path):
        LOGGER.info(f"Creating directory {out_path}")
        os.makedirs(out_path)
    
    #get number of samples, if no specify, default will be all samples
    samples = cfg.database.Samples
    if samples.Full is None and samples.Part is not None:
        samples = samples.Part
        LOGGER.info(f"Using samples {samples}")
    else:
        samples = [i for i in range(1, 21)]
        LOGGER.info(f"Using all samples {samples}, since no samples specified in 'Part'")
        
    #Groups to stratify by, and generate CASE WHEN statement for prespecified age groups
    Groups = list(cfg.database.Groups.keys()) #get groups to stratify by
    LOGGER.info(f"Groups to stratify by: {Groups}")
    Age_case_statement = generate_age_case(cfg.database.Groups.Age_Groups) #Get SQL CASE WHEN statement for prespecified age groups
    LOGGER.info(f"Generated Age Groups SQL statement")
    
    #create table for each sample
    for sample in samples:
        try:
            path = cfg.database.Data_Path #path to downloaded csv files
        except:
            msg = "Data_path not found"
            LOGGER.error(msg)
            raise FileNotFoundError(msg)
        file_pattern_Beneficiary = f'{path}DE1_0_*_Beneficiary_Summary_File_Sample_{sample}.csv'#Pattern for Beneficiary Summary file sample
        file_pattern_Claim = f'{path}DE1_0_2008_to_2010_Inpatient_Claims_Sample_{sample}.csv' #File name for Inpatient Claims file
        LOGGER.info(f"Creating table for sample {sample}")
        table = create_table(file_pattern_Beneficiary, file_pattern_Claim, Groups, Age_case_statement)
        table.to_csv(f"{out_path}sample_{sample}_result.csv", index=False) #save result to csv file
        LOGGER.info(f"Result for sample {sample} saved successfully")
  
  
  
if __name__ == "__main__":
    main()