# VCF Anonymization

This is an anonymization tool designed to selectively remove/replace information in VCF (Variant Call Format) files that carries a high risk of re-identification, reducing privacy exposure while preserving the VCF structure and downstream analysis usability as much as possible.


## Repository Structure

### `VCF_Anonymizer/vcf_anonymizer.py`
  Anonymizes VCFs with two levels:
  - `low` : header/metadata only
  - `high` : metadata + STR masking + rare-variant ALT masking by MAF threshold
### `VCF_Verifier/vcf_anonymization_verifier.py`
  Compare original vs. anonymized VCFs and export a CSV report
### `testdata/`
  Demo dataset folder for quick testing.
  - this repository provides index files only by default (due to file size limits).
  - Demo VCF files must be downloaded separately (see Test Dataset (Demo Data) below).
  - `testdata/README.md` contains the data source description and step-by-step download instructions.

## Download VCF Anonymization
Clone this repository to your local machine:
```
git clone https://github.com/labhai/VCF-Anonymization.git
cd VCF-Anonymization
```

## Requirements and Install

### Requirements
 - Python 3.9+ (recommended: 3.10+)
 - Git (optional, only if you clone the repository)
 - Python package: 'pysam'

⚠️ Important Note: If the input VCF is compressed (e.g., `.vcf.gz` or `.vcf.bgz`), `pysam` needs an index file (`.tbi` or `.csi`) to iterate records via `fetch()`.
For the demo dataset, index files are included in `testdata/` (VCF files are downloaded separately; see Test Dataset (Demo Data)).

### Install (recommended: use a virtual environment)
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

### 1. Prepare demo input/output folders
Before running, download demo VCFs and place them into `testdata/` so filenames match the index files.
See: `testdata/README.md`

Expected structure:
```
testdata/
├─ sample2.vcf.gz
├─ sample2.vcf.gz.csi
├─ sample3.vcf.bgz
├─ sample3.vcf.bgz.tbi
└─ README.md
```

### 2. Run high-level anonymization
```bash
python vcf_anonymizer.py -i ./testdata -o ./anonydata --level high --maf 0.01
```

### 3. Run Low-level anonymization

```bash
python vcf_anonymizer.py -i ./testdata -o ./anonydata --level low
```

### 4. Run Verification
```
python vcf_anonymization_verifier.py -o ./testdata -a ./anonydata
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

In addition, the data sources and download instructions are described in:
`testdata/README.md`

* Download chromosome-level VCFs from IGSR (1000 Genomes FTP)
* Download chromosome-level genomes VCFs from the gnomAD downloads page
* It is recommended to download the index files as well (e.g., `.tbi`)

