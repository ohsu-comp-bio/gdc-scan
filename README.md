# gdc-scan

This utility aims to provide a programmatic interface to the (GDC API)[https://gdc.cancer.gov/developers/gdc-application-programming-interface-api].

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