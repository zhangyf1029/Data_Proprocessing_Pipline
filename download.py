
#sample url for zip file of beneficiary_summary other than de1_0_2010 sample_1
#https://www.cms.gov/research-statistics-data-and-systems/downloadable-public-use-files/synpufs/downloads/de1_0_2008_beneficiary_summary_file_sample_1.zip
#sample url for zip file of beneficiary_summary of de1_0_2010 sample_1
#https://www.cms.gov/sites/default/files/2020-09/DE1_0_2010_Beneficiary_Summary_File_Sample_1.zip
#sample url for zip file of inpatient_claims of de1_0_2010 sample_1
#https://www.cms.gov/research-statistics-data-and-systems/downloadable-public-use-files/synpufs/downloads/de1_0_2008_to_2010_inpatient_claims_sample_1.zip

import logging
import os
import sys
import hydra
import zipfile 
import requests
logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger(__name__)
#Helper function: Download the zip file from the url and extract it to out_dir
def download(url, out_dir, zip_name):
    LOGGER.info(f"Downloaded {zip_name}")
    r = requests.get(url)
    #check if the download is successful
    if r.status_code != 200:
        msg = f"Failed to download from{url}"
        LOGGER.error(msg)
        raise Exception(msg)
    #save the zip file to out_dir
    zip_path = os.path.join(out_dir, "tempfile.zip")
    with open(zip_path, 'wb') as f:
        f.write(r.content)
    #extract the zip file
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(out_dir)
    os.remove(zip_path)
    LOGGER.info(f"{zip_name} extracted to {out_dir}")   

@hydra.main(config_path="./conf", config_name="config", version_base=None)
def main(cfg):
    #get values for Year and Sample from the config file, to download the files of specific years and samples
    Years = cfg.download.Years
    if Years.Full is None and Years.Part is None:
        Years = [2008, 2009, 2010]
        LOGGER.info(f"Download all {Years}, since no years specified in 'Part'")
    else:
        Years = cfg.download.Years.Part
        LOGGER.info(f"Download years {Years}")
    Samples = cfg.download.Samples
    if Samples.Full is None and Samples.Part is None:
        Samples = [i for i in range(1, 21)]
        LOGGER.info(f"Download all samples {Samples}, since no samples specified in 'Part'")
    else:
        Samples = cfg.download.Samples.Part
        LOGGER.info(f"Download samples {Samples}")
        
    
    out_dir = cfg.download.out_dir #get the out_dir from the config file
    
    #check if out_dir exists if not create it
    if not os.path.exists(out_dir):
        LOGGER.info(f"Creating directory {out_dir}")
        os.makedirs(out_dir)
    #the cms_url except del1_0_2010 sample_1
    cms_url = "https://www.cms.gov/research-statistics-data-and-systems/downloadable-public-use-files/synpufs/downloads/" 
    inpatient_prefix = "de1_0_2008_to_2010_inpatient_claims_" 
    #download beneficiary_fummary file and inpatient_claims file
    for sample in Samples:
        #download inpatient_claims file
        if sample < 1 or sample > 20:
            msg = f"Sample {sample} is not supported"
            LOGGER.error(msg)
            raise Exception(msg)
        url = f"{cms_url}{inpatient_prefix}sample_{sample}.zip"
        zip_name = f"{inpatient_prefix}sample_{sample}.zip"
        download(url, out_dir, zip_name)
        #download beneficiary_summary file for each year in each sample
        for year in Years:
            #check if the year is supported
            if year>2010 or year<2008:
                msg = f"Year {year} is not supported"
                LOGGER.error(msg)
                raise Exception(msg)
            mbsf_prefix = f"de1_0_{year}_beneficiary_summary_file_" 
            #if the download file is de1_0_2010 sample_1 use the reassigned url below, otherwise use the url above
            if year == 2010 and sample == 1:
                zip_name = "DE1_0_2010_Beneficiary_Summary_File_Sample_1.zip"
                url = f"https://www.cms.gov/sites/default/files/2020-09/{zip_name}"
            else:
                partition_id = f"sample_{sample}"
                url = f"{cms_url}{mbsf_prefix}{partition_id}.zip"
                zip_name = f"{mbsf_prefix}{partition_id}.zip"    
            download(url, out_dir, zip_name)
                    
    #replace file name with "- Copy.csv" to ".csv"
    for file in os.listdir(out_dir):
        if file.endswith("- Copy.csv"):
            new_file = file.replace("- Copy.csv", ".csv")
            os.rename(os.path.join(out_dir, file), os.path.join(out_dir, new_file))
    
    
if __name__ == "__main__":
    main()

    