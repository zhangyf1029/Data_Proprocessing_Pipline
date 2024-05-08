
rule all:
    input: 
        expand("Output_Data/sample_{sample}_result.csv", sample=[1,2,4,8,10])

rule download: 
    output:
        directory("Data/")
    shell: 
        "python download.py"
    
rule database:
    input:
       directory("Data/")
    output: expand("Output_Data/sample_{sample}_result.csv", sample=[1,2,4,8,10])
    shell:
        "python database.py"