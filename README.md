
# VCF Anonymization

This is an anonymization tool designed to selectively remove/replace information in VCF (Variant Call Format) files that carries a high risk of re-identification, reducing privacy exposure while preserving the VCF structure and downstream analysis usability as much as possible.


## Repository Structure

### `vcf_anonymizer.py`
  - `low` : header/metadata only
  - `high` : metadata + STR masking + rare-variant ALT masking by MAF threshold
### `vcf_anonymization_verifier.py`
  - Compare original vs. anonymized VCFs and export a CSV report

## Download VCF Anonymization

```
git clone 
```

## Requirements and Install

This tool runs in a Python environment and requires the `pysam` package.

```
pip install pysam
```

⚠️ **Important Note**: If the input VCF is compressed (e.g., `.vcf.gz` or `.vcf.bgz`), `pysam` needs an index file (`.tbi` or `.csi`) to iterate records via `fetch()`.
The demo setup in `testdata/` provides the corresponding index files (VCF files are downloaded separately; see below).


## Usage

### Anonymizer

```
python anonymization transformation/vcf_anonymizer.py \
  -i <input_vcf_dir> \
  -o <output_vcf_dir> \
  --level <low|high> \
  [--maf 0.01] \
  [--min-motif 1] \
  [--max-motif 6] \
  [--min-repeat 7]
```

**Options**

* `-i` : input VCF directory
* `-o` : output (anonymized results) directory
* `--level` : `low` or `high`
* `--maf` : MAF threshold (only meaningful for `high`, default: `0.01`)
* `--min-motif`, `--max-motif`, `--min-repeat` : STR detection parameters
  (default: motif length 1–6 bp, minimum 7 repeats)

**Output filename prefix**

* `low` : `low_anony_<original>`
* `high`: `high_<maf>_anony_<original>`

An index file is also generated automatically for the output VCF (e.g., `.tbi` or `.csi`, depending on the environment).



### Verifier

```
python anonymization validation/vcf_anonymization_verifier.py \
  -o <origin_dir> \
  -a <anonymized_dir> \
  --maf 0.01
```

**Matching rule**: the anonymized filename uses the substring after `anony_` as the original filename
(e.g., `high_0.01_anony_sample2.vcf.gz` → `sample2.vcf.gz`).



## Example

The example below uses the demo data under the `testdata/` folder.

### 1. Prepare demo input folders

```
mkdir -p ./demo_origin_vcfs ./demo_anonymized_vcfs
cp ./testdata/sample2.vcf.gz*   ./demo_origin_vcfs/
cp ./testdata/sample3.vcf.bgz*  ./demo_origin_vcfs/
```

### 2. Anonymization

#### Run High-level anonymization

```bash
python anonymization transformation/vcf_anonymizer.py \
  -i ./demo_origin_vcfs \
  -o ./demo_anonymized_vcfs \
  --level high \
  --maf 0.01
```

#### Run Low-level anonymization

```bash
python anonymization transformation/vcf_anonymizer.py \
  -i ./demo_origin_vcfs \
  -o ./demo_anonymized_vcfs \
  --level low
```

### 3. Validation

The verifier takes the original directory (`-o`) and the anonymized directory (`-a`), then validates files by matching them 1:1 using the filename rule.

* **Matching rule**: the substring after `anony_` in the anonymized filename is treated as the original filename
  (e.g., `high_0.01_anony_sample2.vcf.gz` → original: `sample2.vcf.gz`)
* The anonymization level is inferred from the filename prefix:

  * `high_` → high validation (metadata + STR + MAF)
  * `low_` → low validation (metadata only)

```
python anonymization validation/vcf_anonymization_verifier.py \
  -o ./demo_origin_vcfs \
  -a ./demo_anonymized_vcfs \
  --maf 0.01
```

The validation results are saved as a CSV file under the `./reports/` folder after execution
(default filename: `VCF_anonymization_verification_report.csv`).
If a file with the same name already exists, new reports will be created with suffixes like `_2`, `_3`, …



## Test Dataset (Demo Data)

⚠️ **Important Note**: The `testdata/` folder contains **index files only** for the demo VCFs (due to file size limits).

**Included (index only)**

* `sample2.vcf.gz.csi`
* `sample3.vcf.bgz.tbi`

### Download demo VCFs (Google Drive)

Download the corresponding VCF files from [Google Drive](https://drive.google.com/drive/folders/1JN3Fvuv6b_JbqYwq1Dm-XOR_vt1l7A0o):

* `sample2.vcf.gz`
* `sample3.vcf.bgz`

After downloading, place them into the `testdata/` directory so that filenames match the index files:

```
testdata/
├─ sample2.vcf.gz
├─ sample2.vcf.gz.csi
├─ sample3.vcf.bgz
├─ sample3.vcf.bgz.tbi
└─ download.md
```

In addition, the data sources and download instructions are described in:

`testdata/README.md`

* Download chromosome-level VCFs from IGSR (1000 Genomes FTP)
* Download chromosome-level genomes VCFs from the gnomAD downloads page
* It is recommended to download the index files as well (e.g., `.tbi`)

