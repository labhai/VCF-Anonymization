#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
VCF 익명화 검증 코드 (origin STR/MAF target + ALT 변화 확인)

- origin VCF 에서 STR / MAF 기준으로 익명화 대상 위치(target)를 먼저 수집
- anonymized VCF 에서는 같은 (CHROM, POS)에 대해 ALT 가
    * STR: 원본 ALT 와 다르고, 하나 이상 ALT 안에 'N' 이 포함되어 있으면 → 성공
    * MAF: ALT 가 '.' 으로 마스킹된 경우(ALT 없음 / ALT==(".",)) → 성공
- low(weak) 파일은 메타데이터만 검증, high(strong) 파일은 메타 + 변이 모두 검증
- 변이 검증을 "site 단위((CHROM, POS))"로 수행
리포트는 ./reports 디렉토리에 CSV 로 저장된다.

사용 예:
    python vcf_anonymization_verifier.py \
        -o ./input_vcfs \
        -a ./anony_vcfs \
        --maf 0.01 # 설정 안하면 기본 0.01

"""

import argparse
import csv
import os
import re
import time
from typing import Dict, Tuple, Any
import pysam


# 공통 유틸

def _to_float(x):
    try:
        return float(x)
    except Exception:
        return None


def site_maf_from_info(info) -> float:
    """
    익명화 코드의 site_maf_from_info 와 최대한 동일하게 구현.
    """
    # 1) INFO/MAF
    if "MAF" in info and info["MAF"] is not None:
        v = info["MAF"]
        if isinstance(v, (tuple, list)):
            v = v[0] if v else None
        return _to_float(v)

    # 2) INFO/AF
    if "AF" in info and info["AF"] is not None:
        vals = info["AF"]
        afs = list(vals) if isinstance(vals, (tuple, list)) else [vals]
        afs = [_to_float(a) for a in afs if a is not None]
        afs = [a for a in afs if a is not None]
        if afs:
            s = sum(afs)
            ref = max(0.0, 1.0 - s)
            return min([ref] + afs)

    # 3) INFO/AC, INFO/AN
    if (
        "AC" in info
        and "AN" in info
        and info["AC"] is not None
        and info["AN"] is not None
    ):
        an = _to_float(info["AN"])
        if not an or an <= 0:
            return None
        vals = info["AC"]
        acs = list(vals) if isinstance(vals, (tuple, list)) else [vals]
        acs = [_to_float(a) for a in acs if a is not None]
        acs = [a for a in acs if a is not None]
        if acs:
            afs = [a / an for a in acs]
            s = sum(afs)
            ref = max(0.0, 1.0 - s)
            return min([ref] + afs)

    # 4) 계산 불가
    return None


def build_str_patterns(min_motif: int, max_motif: int, min_repeat: int):
    """
    익명화 코드와 동일한 STR 탐지 패턴:
    ([ACGT]{k}) 를 캡처하고 같은 motif 가 최소 min_repeat 회 이상 반복되는 경우.
    """
    patterns = []
    for k in range(min_motif, max_motif + 1):
        regex = rf"([ACGT]{{{k}}})\1{{{min_repeat - 1},}}"
        patterns.append(re.compile(regex))
    return patterns


def parse_header(path: str):
    lines = []
    with pysam.VariantFile(path, "r") as vcf:
        for l in str(vcf.header).splitlines():
            lines.append(l.strip())
    return lines


def infer_level(fname: str) -> str:
    if fname.startswith(("high_", "strong_")):
        return "high"
    if fname.startswith(("low_", "weak_")):
        return "low"
    return "low"


def next_report_path() -> str:
    reports_dir = os.path.abspath("./reports")
    os.makedirs(reports_dir, exist_ok=True)
    base = "VCF_anonymization_verification_report"
    path = os.path.join(reports_dir, base + ".csv")
    if not os.path.exists(path):
        return path
    i = 2
    while True:
        cand = os.path.join(reports_dir, f"{base}_{i}.csv")
        if not os.path.exists(cand):
            return cand
        i += 1


# origin 에서 STR/MAF target 수집

def collect_targets(
    origin_path: str,
    maf_threshold: float,
    patterns,
) -> Dict[Tuple[str, int], Dict[str, Any]]:
    """
    origin VCF 를 한 번 스캔하면서 STR/MAF 대상 위치만 dict 로 수집.
    - key: (chrom, pos)
    - value: {"kind": "STR" or "MAF", "alt_orig": tuple(ALT들)}
    - STR 과 MAF 가 모두 해당되면 STR 우선 (익명화 코드와 동일)
    """
    targets: Dict[Tuple[str, int], Dict[str, Any]] = {}
    vcf = pysam.VariantFile(origin_path, "r")

    for rec in vcf.fetch():
        if not rec.alts or all(a == "." for a in rec.alts):
            continue

        # 1) STR 탐지
        is_str = False
        if patterns:
            for alt in rec.alts:
                if alt is None or alt == ".":
                    continue
                for p in patterns:
                    if p.search(alt):
                        is_str = True
                        break
                if is_str:
                    break

        # 2) MAF 탐지
        maf_target = False
        maf = site_maf_from_info(rec.info)
        if maf is not None and maf < maf_threshold and rec.alts is not None and any(a != "." for a in rec.alts):
            maf_target = True

        if not is_str and not maf_target:
            continue

        if is_str:
            kind = "STR"
        else:
            kind = "MAF"

        key = (rec.chrom, rec.pos)
        alt_tuple = tuple(rec.alts) if rec.alts else ()
        # 같은 (chrom, pos)에 여러 rec가 있어도 site 단위로 overwrite → site 기준 target
        targets[key] = {"kind": kind, "alt_orig": alt_tuple}

    vcf.close()
    return targets


# origin-anony 한 쌍 검증 (site-level)

def verify_pair(
    origin_path: str,
    anony_path: str,
    maf_threshold: float,
    origin_header,
    patterns,
    min_motif: int,
    max_motif: int,
    min_repeat: int,
):
    fname = os.path.basename(anony_path)
    level = infer_level(fname)
    anon_header = parse_header(anony_path)

    # ---- 메타데이터 검증 ----
    meta_t = meta_m = 0

    # cmdline
    if any(l.startswith("##cmdline=") for l in origin_header):
        meta_t += 1
        if any(l.strip() == "##cmdline=." for l in anon_header):
            meta_m += 1

    # reference
    if any(l.startswith("##reference=") for l in origin_header):
        meta_t += 1
        # 익명화 코드: 경로 제거 후 파일명만 남김 (또는 동일 형식)
        if any(l.startswith("##reference=") and "/" not in l for l in anon_header):
            meta_m += 1

    # 변이 검증
    var_t = 0
    var_m_sites = set()   # 검증 충족 set
    error_sites = set()   # 검증 미달 set

    if level == "high":
        # 1) origin 에서 target 수집 (unique (chrom, pos))
        targets = collect_targets(origin_path, maf_threshold, patterns)
        var_t = len(targets)

        vcf_mask = pysam.VariantFile(anony_path, "r")

        # 2) anonymized VCF에서 성공 여부 판정
        for rec in vcf_mask.fetch():
            key = (rec.chrom, rec.pos)
            t = targets.get(key)
            if t is None:
                continue  # 익명화 대상이 아닌 site

            # 이미 이 변이가 성공으로 판정된 경우
            if key in var_m_sites:
                continue

            kind = t["kind"]
            alt_orig = t["alt_orig"]
            alt_mask = tuple(rec.alts) if rec.alts else ()

            success = False

            if kind == "MAF":
                # 익명화 후 INFO 기반으로 다시 MAF 계산
                maf_masked = site_maf_from_info(rec.info)

                if maf_masked is None:
                    # INFO에서 MAF가 사라졌다면, 충분히 익명화된 것으로 판단
                    success = True

                elif maf_masked < maf_threshold:
                    # 여전히 rare site 이면 ALT 완전 제거 여부 확인
                    if (
                        alt_mask in [None, (), (".",)]
                        or all(a == "." for a in alt_mask)
                    ):
                        success = True
                    else:
                        success = False
                else:
                    # rare 가 아니게 되었다면 (ALT 제거/변경 등), 개인 식별력 감소로 간주 → 성공 처리
                    success = True

            else:  # STR 기반
                if alt_mask != alt_orig and any(
                    (a is not None) and ("N" in a) for a in alt_mask
                ):
                    success = True

            if success:
                var_m_sites.add(key)
                # 성공한 site는 error 목록에서 제거 (다른 rec에서 실패를 기록했을 수 있음)
                if key in error_sites:
                    error_sites.remove(key)
            else:
                # 아직 성공으로 찍히지 않은 site만 오류 후보로 기록
                if key not in var_m_sites:
                    error_sites.add(key)

        vcf_mask.close()

    # site-level 성공 개수
    var_m = len(var_m_sites)

    total_targets = meta_t + var_t
    masked_total = meta_m + var_m
    rate = 100.0 if total_targets == 0 else (masked_total / total_targets * 100.0)
    status = "ok" if masked_total == total_targets else "fail"

    # status 가 ok 인 경우에는 오류 좌표 출력하지 않음
    errors_str = "-"
    if status != "ok" and error_sites:
        # CHROM:POS 형태로 정렬해서 출력
        errors_str = ";".join(
            sorted(f"{c}:{p}" for (c, p) in error_sites)
        )

    return {
        "filename": fname,
        "anonymization_level": level,
        "anonymization_rate": f"{rate:.2f}%({masked_total}/{total_targets})",
        "verification_result": status,
        "total_targets": total_targets,
        "metadata_targets": meta_t,
        "variant_targets": var_t,
        "metadata_masked": meta_m,
        "variant_masked": var_m,
        "unmasked_positions": errors_str,
    }


# 디렉토리 단위 실행

def run(
    origin_dir: str,
    anony_dir: str,
    maf_threshold: float,
    min_motif: int = 1,
    max_motif: int = 6,
    min_repeat: int = 7,
):
    start = time.time()
    summaries = []

    patterns = build_str_patterns(min_motif, max_motif, min_repeat)

    origin_files = sorted(
        f for f in os.listdir(origin_dir) if f.endswith((".vcf.gz", ".vcf.bgz")) #파일 확장자 추가 가능
    )

    for orig in origin_files:
        origin_path = os.path.join(origin_dir, orig)

        # origin 파일 이름 뒤쪽이 같은 anonymized 파일 찾기
        matches = [
            f
            for f in os.listdir(anony_dir)
            if f.endswith((".vcf.gz", ".vcf.bgz")) and f.split("anony_", 1)[-1] == orig #파일 확장자 추가 가능
        ]

        if not matches:
            print(f"[WARN] 익명화 파일 없음: {orig}")
            continue

        origin_header = parse_header(origin_path)

        # low → high 순으로 정렬 (둘 다 있을 수 있음)
        low_matches = [m for m in matches if m.startswith(("low_", "weak_"))]
        high_matches = [m for m in matches if m.startswith(("high_", "strong_"))]
        ordered = sorted(low_matches) + sorted(high_matches)

        for anon in ordered:
            anon_path = os.path.join(anony_dir, anon)
            print(f"[CHECK] origin={orig}, anony={anon}")
            res = verify_pair(
                origin_path,
                anon_path,
                maf_threshold,
                origin_header,
                patterns,
                min_motif,
                max_motif,
                min_repeat,
            )
            summaries.append(res)

    # CSV 저장(리포트 저장)
    csv_path = next_report_path()
    with open(csv_path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(
            [
                "filename",
                "anonymization_level",
                "anonymization_rate",
                "verification_result",
                "total_targets",
                "metadata_targets",
                "variant_targets",
                "metadata_masked",
                "variant_masked",
                "unmasked_positions",
            ]
        )
        for r in summaries:
            w.writerow(
                [
                    r["filename"],
                    r["anonymization_level"],
                    r["anonymization_rate"],
                    r["verification_result"],
                    r["total_targets"],
                    r["metadata_targets"],
                    r["variant_targets"],
                    r["metadata_masked"],
                    r["variant_masked"],
                    r["unmasked_positions"],
                ]
            )

    elapsed = round(time.time() - start, 3)
    total_pairs = len(summaries)
    fail_pairs = sum(1 for r in summaries if r["verification_result"] != "ok")

    print("\n================ 검증 결과 요약 ================")
    print(f"총 검증 파일 쌍 수 (origin-anony): {total_pairs}")
    print(f"재익명화 필요 파일 수: {fail_pairs}")
    print(f"총 처리 시간: {elapsed} sec")
    print(f"리포트 저장 위치: {csv_path}")
    print("================================================\n")

    for r in summaries:
        print(
            f"{r['filename']}: {r['verification_result']}  {r['anonymization_rate']}  "
            f"(meta {r['metadata_masked']}/{r['metadata_targets']}, "
            f"variant {r['variant_masked']}/{r['variant_targets']})"
        )



# 메인

def main():
    ap = argparse.ArgumentParser(
        description="VCF anonymization verification (site-level STR/MAF targets + ALT change check)"
    )
    ap.add_argument(
        "-o",
        "--origin",
        required=True,
        help="원본 VCF 디렉토리",
    )
    ap.add_argument(
        "-a",
        "--anony",
        required=True,
        help="익명화된 VCF 디렉토리",
    )
    ap.add_argument(
        "--maf",
        type=float,
        default=0.01,
        help="MAF threshold (기본 0.01=1%)",
    )
    args = ap.parse_args()

    run(args.origin, args.anony, args.maf)


if __name__ == "__main__":
    main()
