# VCF Anonymization Verifier (`vcf_anonymization_verifier.py`)

`vcf_anonymization_verifier.py` validates whether anonymization rules were applied correctly by comparing:
- an **original VCF directory** (`-o`)
- an **anonymized VCF directory** (`-a`)

It verifies:
- **metadata anonymization** (header lines)
- **variant anonymization** (STR masking / MAF-based ALT masking) for **high-level outputs**

Validation is performed at the **site level** (unique `(CHROM, POS)`), and results are saved as a **CSV report** under `./reports/`.

## What this script verifies

### 1) Metadata verification (applies to both low/high)
It checks whether the anonymized header contains expected anonymized metadata:

- If the original header contains `##cmdline=...`  
  → anonymized header must contain `##cmdline=.`

- If the original header contains `##reference=...`  
  → anonymized header must contain a `##reference=` line **without path separators (`/`)**  
  (i.e., path removed and filename-only form)

> Note: this verifier checks the *presence/form* of anonymized metadata in the anonymized header.

### 2) Variant verification (high-level files only)
For **high-level outputs** (filename prefix: `high_` or `strong_`), this verifier validates variant masking using a two-step approach:

#### Step A. Collect anonymization targets from the original VCF
It scans the original VCF and collects “target sites” that should be anonymized, based on:
- **STR target**: any ALT contains an STR-like repeat pattern
- **MAF target**: site-level MAF from `INFO` is `< --maf`

**Priority rule:** if a site is both STR and MAF target, it is treated as **STR**  
(same priority as the anonymizer).

Targets are stored as:
- key: `(CHROM, POS)`
- value: `kind = STR or MAF`, and `alt_orig = original ALT tuple`

#### Step B. Check anonymized VCF at the same sites
For each target site `(CHROM, POS)` in the anonymized VCF:

- **STR target success condition**
  - anonymized ALT is **different from** original ALT, and
  - at least one ALT contains `'N'`

- **MAF target success condition**
  - First, recompute site-level MAF from anonymized record `INFO` (same logic as anonymizer: `MAF` → `AF` → `AC/AN`)
  - If MAF cannot be computed (`None`): treated as **success**
  - Else if MAF is still `< --maf`:
    - ALT must be fully masked as `"."` (i.e., ALT is empty / `(".",)`)
  - Else (no longer rare): treated as **success** (interpreted as reduced identifiability)


## File matching rule (origin ↔ anonymized)

This verifier matches files by filename using the substring after `anony_`.

Example:
- anonymized filename: `high_0.01_anony_sample2.vcf.gz`
- matched original filename: `sample2.vcf.gz`

The script scans all `.vcf.gz` / `.vcf.bgz` files in the origin directory and finds corresponding anonymized files in the anonymized directory using:

- `f.split("anony_", 1)[-1] == <origin_filename>`

If no anonymized match exists, it prints a warning and skips that origin file.

## Usage

Run from repository root:

```bash
python VCF_Verifier/vcf_anonymization_verifier.py \
  -o <origin_dir> \
  -a <anonymized_dir> \
  --maf 0.01
```

### Options

* `-o, --origin` : directory containing original VCF files
* `-a, --anony` : directory containing anonymized VCF files
* `--maf <float>` : MAF threshold used for identifying MAF targets (default: `0.01`)

> STR detection parameters are fixed in this script to:
>
> * min motif = 1, max motif = 6, min repeat = 7
>   (same defaults as the anonymizer)


## Output

### 1) CSV report

The report is saved under `./reports/` with the name:

* `VCF_anonymization_verification_report.csv`

If the file already exists, it creates:

* `VCF_anonymization_verification_report_2.csv`
* `VCF_anonymization_verification_report_3.csv`
* ...

### 2) Report columns

| Column                | Description                                                                     |
| --------------------- | ------------------------------------------------------------------------------- |
| `filename`            | anonymized filename                                                             |
| `anonymization_level` | inferred from prefix (`high_`/`strong_` → high, `low_`/`weak_` → low)           |
| `anonymization_rate`  | overall pass rate in `% (masked/targets)` format                                |
| `verification_result` | `ok` if all targets satisfied, else `fail`                                      |
| `total_targets`       | metadata targets + variant targets                                              |
| `metadata_targets`    | number of metadata checks required                                              |
| `variant_targets`     | number of target sites `(CHROM, POS)` for variant anonymization (high only)     |
| `metadata_masked`     | number of metadata checks passed                                                |
| `variant_masked`      | number of variant target sites passed                                           |
| `unmasked_positions`  | for `fail`, list of `CHROM:POS` that did not satisfy masking rules; `-` if none |


## Expected console logs

During execution, the script prints per pair:

* `[CHECK] origin=<orig_filename>, anony=<anonymized_filename>`

After finishing, it prints a summary:

* total checked pairs
* number of failed pairs (needs re-anonymization)
* elapsed time
* report path

And then prints one-line results per anonymized file:

```
<filename>: <ok/fail>  <rate>  (meta x/y, variant x/y)
```

Example (format):

```
================ 검증 결과 요약 ================
총 검증 파일 쌍 수 (origin-anony): 2
재익명화 필요 파일 수: 1
총 처리 시간: 3.214 sec
리포트 저장 위치: /.../reports/VCF_anonymization_verification_report.csv
================================================

high_0.01_anony_sample2.vcf.gz: ok  100.00%(10/10)  (meta 2/2, variant 8/8)
low_anony_sample2.vcf.gz: ok  100.00%(2/2)  (meta 2/2, variant 0/0)
```

## Notes / Pitfalls

* Only `.vcf.gz` and `.vcf.bgz` files are scanned in both origin/anonymized directories.
* Validation is **site-level** by `(CHROM, POS)`. If multiple records share the same site, the last observed target definition may overwrite earlier ones.
* For high-level verification:

  * STR targets require ALT change **and** presence of `'N'` in ALT.
  * MAF targets expect ALT to be masked as `"."` when still rare (`maf < --maf`).
* Make sure anonymized filenames follow the expected prefix + `anony_` rule; otherwise matching may fail.
