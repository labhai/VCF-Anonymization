# VCF Anonymization

This is an anonymization tool designed to selectively remove/replace information in VCF (Variant Call Format) files that carries a high risk of re-identification, reducing privacy exposure while preserving the VCF structure and downstream analysis usability as much as possible.

### What is VCF?
**VCF (Variant Call Format)** is a standard text-based file format used in bioinformatics to store genetic variants (e.g., SNPs, indels) and related annotations. A VCF includes metadata headers (`##...`), a column header (`#CHROM ...`), and variant records with alleles and optional INFO/FORMAT fields.
Because VCFs can contain rich metadata and variant patterns, sharing them without protection may increase re-identification risk.

### Why Anonymization Is Necessary
- **Header (metadata) anonymization**  
Even if a VCF does not contain explicit personal identifiers, the header metadata can include sensitive operational details (e.g., institution-specific paths, usernames, internal server locations, or full command lines used to generate the file). When shared externally, these fields may leak unnecessary environment or provenance information.

- **Variant-level anonymization**  
Genomic variants can be highly identifying. In particular:  
  - **STR (Short Tandem Repeat)** patterns may reflect individual-specific repeat structures.  
  - **Rare variants** (very low population allele frequency) can be unique to an individual or a small subgroup, increasing re-identification risk—especially when combined with other datasets.

## Repository Structure

### `vcf_anonymizer`
  Anonymizes VCFs with two levels:
  - `low`
    - Targets: sensitive header metadata fields
    - Rules: mask `##cmdline` as `.` and strip paths from `##reference` (keep filename only)
  - `high`
    - Includes all `low` rules, plus:
    - STR masking (ALT): detect STR-like repeats in `ALT` alleles (user-configurable; default: motif length 1–6 bp, ≥7 repeats) and mask repeat regions with `N`
    - Rare-variant masking (ALT): for non-STR sites with MAF < threshold (user-configurable; default `0.01`), replace `ALT` with `.`
### `vcf_verifier`
  Compare original vs. anonymized VCFs and export a CSV report
  - Checks (low): header rules (`##cmdline`, `##reference`)
  - Checks (high): header rules + STR masking + MAF-based ALT masking (site-level)
### `testdata/`
  Demo dataset folder for quick testing.
  - This repository provides index files only by default (due to file size limits).
  - Demo VCF files must be downloaded separately (see Test Dataset (Demo Data) below).
  - `testdata/README.md` contains the data source description and step-by-step download instructions.

## Download VCF Anonymization

Clone this repository to your local machine:
```
git clone https://github.com/labhai/VCF-Anonymization.git
cd VCF-Anonymization
```

## Requirements and Installation

### Requirements
 - Python 3.9+ (recommended: 3.10+)
 - Git (optional, only if you clone the repository)
 - Python package: 'pysam'

⚠️ Important Note: If the input VCF is compressed (e.g., `.vcf.gz` or `.vcf.bgz`), `pysam` needs an index file (`.tbi` or `.csi`) to iterate records via `fetch()`.
For the demo dataset, index files are included in `testdata/` (VCF files are downloaded separately; see [Test Dataset (Demo Data)](https://github.com/labhai/VCF-Anonymization/blob/main/README.md#test-dataset-demo-data)).

### Installation (recommended: use a virtual environment)
The steps below use a virtual environment (`.venv`) and include a quick verification command to confirm that `pysam` was installed successfully.

#### macOS / Linux
```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
python -m pip install pysam
python -c "import pysam; print('pysam version:', pysam.__version__)"
```

#### Windows (PowerShell)
```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip setuptools wheel
python -m pip install pysam
python -c "import pysam; print('pysam version:', pysam.__version__)"
```
If Activate.ps1 is blocked by execution policy, run this once in the same PowerShell window and try again:
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

## Example (Quickstart)

This quickstart follows the same demo workflow: `testdata/` (input) → `anonydata/` (output) → verification report.

### 1. Run low-level anonymization
```bash
python vcf_anonymizer/vcf_anonymizer.py -i ./testdata -o ./anonydata --level low
```

### 2. Run high-level anonymization
```bash
python vcf_anonymizer/vcf_anonymizer.py -i ./testdata -o ./anonydata --level high --maf 0.01
```

### 3. Run verification
```bash
python vcf_verifier/vcf_anonymization_verifier.py -o ./testdata -a ./anonydata
```

## Test Dataset (Demo Data)

**Included (index only)**

* `sample2.vcf.gz.csi`
* `sample3.vcf.bgz.tbi`

### Download demo VCFs (Google Drive)

Download the corresponding VCF files from [Google Drive](https://drive.google.com/drive/folders/1JN3Fvuv6b_JbqYwq1Dm-XOR_vt1l7A0o):

* `sample2.vcf.gz`
* `sample3.vcf.bgz`

After downloading, place them into the `testdata/` directory so that filenames match the index files.

More details (data sources and step-by-step instructions) are described in `testdata/README.md`

