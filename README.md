# gdc-scan

![GDC](https://github.com/ohsu-computational-biology/gdc-scan/blob/master/resources/public/scan.png)

This utility aims to provide a programmatic interface to the [GDC API](https://gdc.cancer.gov/developers/gdc-application-programming-interface-api).

## usage

`gdc-scan` provides a command tree to access the GDC API. Here is a quick tree of the available commands:

    projects
    ├── list
    └── mapping
    cases
    ├── list
    ├── files
    └── mapping
    files
    ├── list
    ├── facets
    ├── download
    └── mapping

So for instance, to find a list of all projects on the GDC you can invoke:

    python gdc-scan.py projects list

Other commands take optional arguments, for instance:

    python gdc-scan.py files download --format MAF --project TCGA-PAAD

The `mapping` commands tell you every property available from GDC for that particular category.

## projects



## cases



## files

### find all data types

In order to find all data types stored in the GDC, you can use the `facets` command:

    python gdc-scan.py files facets data_type

Current output for this:

    {"data_type": {"Copy Number Segment": 22376, "Clinical Supplement": 11168, "Masked Somatic Mutation": 33, "Annotated Somatic Mutation": 45577, "Masked Copy Number Segment": 22376, "miRNA Expression Quantification": 11488, "Aligned Reads": 45988, "Aggregated Somatic Mutation": 144, "Isoform Expression Quantification": 11488, "Gene Expression Quantification": 34722, "Raw Simple Somatic Mutation": 45577, "Biospecimen Supplement": 11356}}

### download all files of a given type

Then, you can download all files of a given type (say, "Gene Expression Quantification") with the following command:

    python gdc-scan.py files download --type "Gene Expression Quantification"

### find the file_id and submitter_id for each file of a given type

Say you want to get all the `submitter_id`s for all of the legacy BAM files in the system. Here is the command for that:

    python gdc-scan.py files list --type "Aligned reads" --key file_id,submitter_id --legacy

This will return a list of dictionaries with the keys provided. If you want to find out all of the possible keys you could use, try `mapping`:

    python gdc-scan.py files mapping