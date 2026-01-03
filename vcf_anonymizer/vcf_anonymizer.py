#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
vcf_anonymizer.py

VCF 파일 메타데이터 및 염기 변이 정보를 보호하기 위한 익명화 스크립트
- 저수준 익명화 (metadata only)
- 고수준 익명화 (metadata + STR + MAF 기반 ALT 마스킹)

사용 예:
    python vcf_anonymizer.py \
        -i ./input_vcfs \
        -o ./anony_vcfs \
        --level high \
        --maf 0.01
"""

import argparse
import pysam
import re
import os
import time


# 공통 유틸

def _to_float(x):
    try:
        return float(x)
    except Exception:
        return None


def site_maf_from_info(info):
    """ INFO 필드에서 사이트 레벨 MAF 계산 """
    # 1) 직접 MAF 제공
    if "MAF" in info:
        v = info["MAF"]
        if isinstance(v, (tuple, list)):
            v = v[0]
        return _to_float(v)

    # 2) AF 배열 기반
    if "AF" in info:
        vals = info["AF"]
        afs = list(vals) if isinstance(vals, (tuple, list)) else [vals]
        afs = [_to_float(x) for x in afs if x is not None]
        if afs:
            ref = max(0.0, 1.0 - sum(afs))
            return min([ref] + afs)

    # 3) AC/AN 기반
    if "AC" in info and "AN" in info:
        an = _to_float(info["AN"])
        if not an or an <= 0:
            return None
        vals = info["AC"]
        acs = list(vals) if isinstance(vals, (tuple, list)) else [vals]
        afs = []
        for a in acs:
            fa = _to_float(a)
            if fa is not None:
                afs.append(fa / an)
        if afs:
            ref = max(0.0, 1.0 - sum(afs))
            return min([ref] + afs)

    return None


def build_str_patterns(min_motif, max_motif, min_repeat):
    """모티프 길이 및 최소 반복 횟수를 기준으로 STR 탐지 정규식 컴파일."""
    patterns = []
    for k in range(min_motif, max_motif + 1):
        # ([ACGT]{k})를 캡처하고, 같은 motif가 최소 min_repeat회 이상 반복
        regex = rf"([ACGT]{{{k}}})\1{{{min_repeat - 1},}}"
        patterns.append(re.compile(regex))
    return patterns


def mask_str(seq, motif, min_repeat):
    """
    하나의 ALT 시퀀스에서 주어진 motif(1~6bp)가 min_repeat회 이상 반복되는 구간을 마스킹.
    - 1bp motif: 반복 구간 전체 'N'
    - 2~6bp motif: 각 motif의 첫 염기는 유지, 나머지 염기는 'N'
    """
    motif_len = len(motif)

    if motif_len == 1:
        # 예: motif='A', min_repeat=7 → '(A){7,}' → 전부 'N'
        return re.sub(
            rf"({motif}){{{min_repeat},}}",
            lambda m: "N" * len(m.group(0)),
            seq,
        )

    # 2~6bp motif
    def repl(m):
        segment = m.group(0)
        result = []
        for i in range(0, len(segment), motif_len):
            chunk = segment[i : i + motif_len]
            if chunk == motif:
                # 첫 염기 유지 + 나머지 N
                result.append(chunk[0] + "N" * (motif_len - 1))
            else:
                result.append(chunk)
        return "".join(result)

    return re.sub(
        rf"({motif}){{{min_repeat},}}",
        repl,
        seq,
    )


# 파일 단위 익명화

def anonymize_vcf_file(
    input_vcf,
    output_vcf,
    level: str,
    maf_threshold: float,
    min_motif: int,
    max_motif: int,
    min_repeat: int,
):
    """
    한 개 VCF 파일에 대해:
    - level == "low": 메타데이터만 익명화
    - level == "high": 메타데이터 + STR + MAF 기반 ALT 마스킹
    """
    vcf_in = pysam.VariantFile(input_vcf, "r")

    # 1) 헤더(메타데이터) 익명화
    header_lines = []
    for line in str(vcf_in.header).splitlines():
        if line.startswith("##cmdline="):
            header_lines.append("##cmdline=.")
        elif line.startswith("##reference="):
            ref_value = line.split("=", 1)[1].strip()
            ref_filename = os.path.basename(ref_value.replace("file://", ""))
            header_lines.append(f"##reference={ref_filename}")
        else:
            header_lines.append(line)

    new_header = pysam.VariantHeader()
    for l in header_lines:
        if not l.startswith("#CHROM"):  # CHROM 라인은 자동 처리됨
            new_header.add_line(l)
    # 샘플 정보 복사
    for s in vcf_in.header.samples:
        new_header.add_sample(s)

    # 2) 출력 파일 열기 (헤더 반영)
    vcf_out = pysam.VariantFile(output_vcf, "wz", header=new_header)

    # high 모드인 경우 STR 패턴 준비
    patterns = None
    if level == "high":
        patterns = build_str_patterns(min_motif, max_motif, min_repeat)

    # 3) 레코드 단위 처리
    for rec in vcf_in.fetch():
        # ALT가 '.' 인 non-variant는 그대로 통과
        if rec.alts and all(a == "." for a in rec.alts):
            vcf_out.write(rec)
            continue

        # low: 메타데이터만 익명화, 레코드는 그대로
        if level == "low":
            vcf_out.write(rec)
            continue

        # high: STR / MAF 적용
        str_modified = False

        # 3-1) STR 기반 ALT 마스킹
        if rec.alts:
            new_alts = []
            for alt_seq in rec.alts:
                masked = alt_seq
                for p in patterns:
                    m = p.search(alt_seq)
                    if m:
                        motif = m.group(1)
                        masked = mask_str(alt_seq, motif, min_repeat)
                        if masked != alt_seq:
                            str_modified = True
                        break  # 첫 motif만 사용
                new_alts.append(masked)
            rec.alts = tuple(new_alts)

        # 3-2) STR가 한 번도 적용되지 않은 레코드에만 MAF 기반 ALT='.' 마스킹
        if not str_modified:
            maf = site_maf_from_info(rec.info)
            if maf is not None and maf < maf_threshold:
                # pysam 버전 호환을 위해 튜플 형태로 ALT='.' 지정
                rec.alts = (".",)

        # 최종 레코드 쓰기
        vcf_out.write(rec)

    vcf_in.close()
    vcf_out.close()


# 메인

def main():
    parser = argparse.ArgumentParser(
        description="VCF Metadata / STR / MAF 기반 익명화 도구"
    )
    parser.add_argument(
        "-i", "--input", required=True, help="VCF 파일이 위치한 입력 디렉토리"
    )
    parser.add_argument(
        "-o", "--output", required=True, help="익명화 결과 저장 디렉토리"
    )
    parser.add_argument(
        "--level",
        choices=["low", "high"],
        required=True,
        help="익명화 수준 (low=메타데이터만, high=메타+STR+MAF)",
    )
    parser.add_argument(
        "--maf",
        type=float,
        default=0.01,
        help="MAF threshold (high 모드에서만 사용, 기본값 0.01=1%)",
    )
    parser.add_argument("--min-motif", type=int, default=1)
    parser.add_argument("--max-motif", type=int, default=6)
    parser.add_argument("--min-repeat", type=int, default=7)
    args = parser.parse_args()

    os.makedirs(args.output, exist_ok=True)

    start_time = time.time()
    processed = 0

    for fname in os.listdir(args.input):
        if not fname.endswith((".vcf.gz", ".vcf.bgz")): #파일 확장자 추가 가능
            continue

        processed += 1
        input_path = os.path.join(args.input, fname)

        # 파일명 prefix 설정 (레벨 + maf 포함 여부)
        if args.level == "high":
            prefix = f"high_{args.maf}_anony_"
        else:
            prefix = "low_anony_"

        output_path = os.path.join(args.output, f"{prefix}{fname}")

        print(f"[+] Processing {fname}")
        anonymize_vcf_file(
            input_path,
            output_path,
            level=args.level,
            maf_threshold=args.maf,
            min_motif=args.min_motif,
            max_motif=args.max_motif,
            min_repeat=args.min_repeat,
        )
        print(f"[OK] Written → {output_path}")

        # 생성된 VCF.gz 파일에 대해 인덱스 생성
        pysam.tabix_index(output_path, preset="vcf", csi=True, force=True)
        print(f"[OK] Index created → {output_path}.tbi")

    elapsed = time.time() - start_time
    print("\n======================================")
    print(f"[DONE] Total processed files : {processed}")
    print(f"[TIME] Elapsed time          : {elapsed:.2f} seconds")
    print("======================================\n")


if __name__ == "__main__":
    main()
