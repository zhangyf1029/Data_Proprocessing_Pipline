# Harvard_Interview_Homework
* Download the `CMS Beneficiary Summary DE-SynPUF` and `CMS Beneficiary Summary DE-SynPUF` zip files, and unzip the contents as CSV files.
* Obtain yearly state-level all-cause hospitalization risk stratified by sex, race, and age prespecified groups.
* Also contains Snakefile for workflow management and .yaml files for configurations.

## Content
**conf**
* [conf/config.yaml](https://github.com/zhangyf1029/Harvard_Interview_Homework/tree/main/conf) contains default configurations for [download.py](https://github.com/zhangyf1029/Harvard_Interview_Homework/tree/main) and [database.py](https://github.com/zhangyf1029/Harvard_Interview_Homework/tree/main).
* [conf/download/download.yaml](https://github.com/zhangyf1029/Harvard_Interview_Homework/tree/main/conf/download) specifies the download options of `Years`, `Samples` and output path as `out_dir`.
> Examples of download.py
> 1. Download `all available years` in `all samples` to the directory `./Data`
>   ```
>    Years:
>      Full: null
>      Part: null
>     Samples:
>      Full: null
>      Part: null
>    out_dir: ./Data
>   ```
> 2. Download years `2008 and 2009` in samples `1, 2, 4, 8 and 10` to the directory `./Data`
>   ```
>   Years:
>     Full: null
>   Part:
>     - 2008
>     - 2009
>   Samples:
>     Full: null
>     Part: 
>       - 1
>       - 2
>       - 4
>       - 8
>       - 10
>   out_dir: ./Data
>   ```
* [conf/database/database.yaml](https://github.com/zhangyf1029/Harvard_Interview_Homework/tree/main/conf/database) specifies the sample(s) to obtain the yearly state-level all-cause hospitalization risk, and Age_Groups for the stratification.
> Example of database.py
> * Processed samples `1, 2, 4, 8, and 10`(specific samples in database.yaml have to be a `subset` of samples in download.yaml). Stratified the Age into groups of `<18`, `18-30`, `30-50`, `50-70`, `70-100` and `>100`. Output the processed data to `./Output_Data/`.
>  ```
>  Samples:
>    Full: null
>    Part: 
>      - 1
>      - 2
>      - 4
>      - 8
>      - 10
>  Groups:
>    Sex: null
>    Race: null
>    Age_Groups: 
>      - 18
>      - 30
>      - 50
>      - 70
>      - 100
>  Data_Path: ./Data/
>  Output_Path: ./Output_Data/
>  ```
* [Snakefile.smk](https://github.com/zhangyf1029/Harvard_Interview_Homework/tree/main) manage the workflow. Please adjust `.yaml` file according to needs.

## Run
**Conda Environment**
1. Clone the GitHub repository.
```
git clone <https://github.com/<user>/repo>
cd <repo>
```
2. Create a conda environment with `requirements.yaml`
```
conda env create -f requirements.yaml
conda activate <env_name> #Here environment name is Harvard-interview-homework
```
3. Run the pipeline
> Way 1: run through Snakefile
>  ```
>  snakemake -s Snakefile.smk --core all
>  ```


> Way 2: run step by step manually
>  ```
>  python download.py
>  ```
> Download data will be in `./Data` set in `download.yaml`. The directory will be created by scripts if it does not exist.
>  ```
>  python database.py
>  ```
> Processed results will be in `./Output_Data` set in `database.yaml`. The firectory will also be created by scripts if it does not exist.


