## 샘플 파일 예시  
 - IGSR chr10: `sample2.vcf.gz`  
 - gnomAD chr21: `sample3.vcf.bgz`
 - 업로드 용량문제로 sample2.vcf.gz, sample3.vcf.bgz 를 드라이브에 업로드 하였음

**링크**
https://drive.google.com/drive/folders/1JN3Fvuv6b_JbqYwq1Dm-XOR_vt1l7A0o

## IGSR

**링크**  
- https://ftp.1000genomes.ebi.ac.uk/vol1/ftp

**IGSR 간략 설명**  
- IGSR(International Genome Sample Resource)은 1000 Genomes Project 등 공개 유전체 변이 데이터를 FTP 형태로 제공하며 염색체 단위로 VCF 파일이 구성되어 있다.

**다운로드 방법**  
1. 위 FTP 링크에 접속한다.  
2. `release/20130502/` 디렉토리로 이동한다.  
3. 디렉토리 내부에는 염색체 번호별 VCF 파일이 존재한다.  
   - 예: `ALL.chr10.phase3_shapeit2_mvncall_integrated_v5b.20130502.genotypes.vcf.gz`  
4. 원하는 염색체 파일(`.vcf.gz`)을 클릭하여 다운로드한다.  
5. 같은 이름의 인덱스 파일(`.tbi`)도 함께 다운로드한다.  
   - 예: `...vcf.gz.tbi`  
   - `.tbi` 파일이 있어야 `pysam`에서 VCF를 더 안전하게(특히 region 조회 등) 읽을 수 있다.

---

## gnomAD

**링크**  
- https://gnomad.broadinstitute.org/downloads#v4-browser-tables

**gnomAD 간략 설명**  
- gnomAD는 대규모 인구집단 기반 변이 데이터를 집계해 제공하는 공개 리소스이며, v4 Downloads에서 genomes VCF 파일을 염색체 단위로 내려받을 수 있다.

**다운로드 방법**  
1. 위 링크로 gnomAD Downloads 페이지에 접속한다.  
2. 페이지 중단의 `v4 Downloads` 섹션으로 이동한다.  
3. `genomes` 항목에서 다운로드 받을 VCF 파일을 선택하여 다운로드 한다.(VCF는 염색체별로 구성되어 있으므로 필요한 염색체 파일을 다운로드함) 
4. 다운로드 링크는 `Google` / `Amazon` 등이 제공되며 본 작업에서는 Google 링크를 클릭하여 다운로드하였다.  
5. IGSR과 동일하게, 가능하다면 인덱스 파일(`.tbi`)도 함께 다운로드한다.  
