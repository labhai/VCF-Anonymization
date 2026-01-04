## Prepare demo input/output folders
Before running, download demo VCFs and place them into `testdata/` so filenames match the index files.

Expected structure:
```
testdata/
├─ sample2.vcf.gz
├─ sample2.vcf.gz.csi
├─ sample3.vcf.bgz
├─ sample3.vcf.bgz.tbi
└─ README.md
```

## Sample file examples  
 - IGSR chr10: `sample2.vcf.gz`  
 - gnomAD chr21: `sample3.vcf.bgz`
 - Due to upload size limits, `sample2.vcf.gz` and `sample3.vcf.bgz` were uploaded to Google Drive.

**Link**
https://drive.google.com/drive/folders/1JN3Fvuv6b_JbqYwq1Dm-XOR_vt1l7A0o

## IGSR

**Link**  
- https://ftp.1000genomes.ebi.ac.uk/vol1/ftp

**IGSR brief description**  
- IGSR (International Genome Sample Resource) provides public genomic variant datasets such as the 1000 Genomes Project via FTP, and the VCF files are organized by chromosome.

**How to download**  
1. Open the FTP link above.
2. Navigate to the `release/20130502/` directory.  
3. Inside the directory, there are VCF files for each chromosome.
    - Example: ALL.chr10.phase3_shapeit2_mvncall_integrated_v5b.20130502.genotypes.vcf.gz
      
5. Click the chromosome file (`.vcf.gz`) you want to download.  
6. Download the corresponding index file (`.tbi`) with the same name as well.
    - Example: `...vcf.gz.tbi`
    - The `.tbi` file helps pysam read the VCF more reliably (especially for region queries, etc.).

## gnomAD

**Link**  
- https://gnomad.broadinstitute.org/downloads#v4-browser-tables

**gnomAD brief description**  
- gnomAD is a public resource that aggregates large population-based variant data, and under v4 Downloads you can download genomes VCF files by chromosome.

**How to download**  
1. Open the gnomAD Downloads page using the link above.
2. Scroll to the `v4 Downloads` section in the middle of the page. 
3. Under `genomes`, choose the VCF file you want to download. (VCFs are provided per chromosome, so download the chromosome file you need.)
4. Download links are provided via `Google` / `Amazon`, etc. In this work, the Google link was used.
5. As with IGSR, if possible, also download the index file (`.tbi`).
