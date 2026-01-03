## Usage

### Anonymizer

```bash
python vcf_anonymizer.py \
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
```bash
python vcf_anonymization_verifier.py \
  -o <origin_dir> \
  -a <anonymized_dir> \
  --maf 0.01
```
The verifier takes the original directory (`-o`) and the anonymized directory (`-a`), then validates files by matching them 1:1 using the filename rule.

**Matching rule**: the anonymized filename uses the substring after `anony_` as the original filename
(e.g., `high_0.01_anony_sample2.vcf.gz` → `sample2.vcf.gz`).

The validation results are saved as a CSV file under the `./reports/` folder after execution
(default filename: `VCF_anonymization_verification_report.csv`).
If a file with the same name already exists, new reports will be created with suffixes like `_2`, `_3`, …
