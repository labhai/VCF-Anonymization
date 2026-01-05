# VCF Anonymizer (`vcf_anonymizer.py`)

`vcf_anonymizer.py` is a VCF anonymization script designed to reduce re-identification risk by anonymizing:
- VCF header/metadata (common to all levels)
- ALT (Alternate Allele): in each VCF variant record, `REF` is the reference allele and `ALT` lists one or more alternate alleles observed at that genomic position. In this repository, `ALT` is the main variant-level target in `high` mode.
  - ALT sequences via STR masking (high level)
  - rare variants via MAF-threshold-based ALT masking (high level)

It processes all compressed VCF files in an input directory (`.vcf.gz`, `.vcf.bgz`) and writes anonymized outputs to an output directory.  
After writing each anonymized VCF, it also generates an index file using `pysam.tabix_index()`.

## What this script does

### 1. Metadata anonymization (always applied)
For each input VCF, it rewrites specific header lines:

- `##cmdline=...` → replaced with `##cmdline=.`
- `##reference=...` → keeps only the filename (removes any path / `file://` prefix)

All other header lines are preserved, and sample IDs are copied as-is.

### 2. Variant anonymization (high level only)

#### STR masking on ALT sequences
If `--level high`, the script detects STR-like repeats in ALT sequences using regex patterns defined by:

- motif length: `--min-motif` to `--max-motif`
- minimum repeat count: `--min-repeat`

Masking rules:
- motif length 1 bp: replace the repeated segment fully with `N`
- motif length 2–6 bp: keep the first base of each motif and replace the rest with `N`
- If multiple motifs could match, only the first detected motif is applied per ALT sequence.

#### MAF-based rare variant masking (only if STR was NOT applied)
If STR masking did not modify any ALT in a record, the script computes a site-level MAF from `INFO` and applies rare-variant masking:

- If `maf < --maf`, ALT is replaced with `"."` (masked)

## Usage

### Command (run from repository root)

```bash
python vcf_anonymizer/vcf_anonymizer.py \
  -i <input_vcf_dir> \
  -o <output_vcf_dir> \
  --level <low|high> \
  [--maf 0.01] \
  [--min-motif 1] \
  [--max-motif 6] \
  [--min-repeat 7]
```

### Options

* `-i, --input` : input VCF directory

  * Script scans files ending with `.vcf.gz` or `.vcf.bgz` only.
* `-o, --output` : output directory for anonymized VCFs

  * Directory is created if it does not exist.
* `--level {low,high}` : anonymization level

  * `low` = metadata only
  * `high` = metadata + STR masking + MAF-based ALT masking
* `--maf <float>` : MAF threshold (default: `0.01`)

  * Only meaningful in `high` mode.
* `--min-motif <int>` (default: `1`)
* `--max-motif <int>` (default: `6`)
* `--min-repeat <int>` (default: `7`)

  * STR detection parameters (motif length range and minimum repeats)


## Output

### Output filename prefix

* `low` : `low_anony_<original>`
* `high`: `high_<maf>_anony_<original>`

Examples:

* `low_anony_sample2.vcf.gz`
* `high_0.01_anony_sample2.vcf.gz`

### Index generation

After writing each anonymized VCF, the script creates a Tabix index:

```python
pysam.tabix_index(output_path, preset="vcf", csi=True, force=True)
```

So each output VCF will have an index file generated (typically `.csi` when `csi=True`).

### Expected Console Logs

The script prints progress per file:

* `[+] Processing <filename>`
* `[OK] Written → <output_path>`
* `[OK] Index created → <output_path>.<index>`
* A final summary with:

  * total processed files
  * elapsed time

Example format:

```
[+] Processing sample2.vcf.gz
[OK] Written → ./anonydata/high_0.01_anony_sample2.vcf.gz
[OK] Index created → ./anonydata/high_0.01_anony_sample2.vcf.gz.csi

======================================
[DONE] Total processed files : 2
[TIME] Elapsed time          : 12.34 seconds
======================================
```

## Notes

* Only `.vcf.gz` and `.vcf.bgz` files are processed.
* In `high` mode, STR masking has priority.
  MAF masking is applied only if STR masking did not modify the record.
* Output indexing uses `csi=True`, so index extension may be `.csi` depending on the environment.
