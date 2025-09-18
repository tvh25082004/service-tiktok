#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import os
import sys
from typing import List, Dict, Any

try:
    from videohash import VideoHash
    import PIL.Image  # noqa: F401
except ImportError:
    print("Thiếu thư viện. Hãy chạy: pip3 install -r requirements.txt")
    sys.exit(1)

INPUT_DB = "data_final.json"
OUTPUT_DB = "data_final_enriched.json"


def normalize_bits(bits: str) -> str:
    if not bits:
        return ""
    if bits.startswith("0b"):
        bits = bits[2:]
    return bits.zfill(64)[:64]


def compute_prefix16(bits64: str) -> str:
    return normalize_bits(bits64)[:16]


def enrich_database(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    enriched = []
    total = len(records)
    for i, rec in enumerate(records):
        if i % 200 == 0:
            print(f"⏳ {i}/{total}...")
        video_url = rec.get("video_url") or rec.get("url") or ""
        # Nếu đã có hash_prefix16 hoặc prefix16 và có pHash bits hợp lệ thì bỏ qua
        has_prefix = ("hash_prefix16" in rec) or ("prefix16" in rec)
        # Ưu tiên giữ nguyên hash hiện tại
        existing_hash = rec.get("hash", "")
        # Cố gắng tính pHash nếu có URL
        if video_url:
            try:
                vh = VideoHash(url=video_url)
                # Lấy 64-bit bits
                if hasattr(vh, 'hash_bits') and isinstance(vh.hash_bits, str):
                    bits64 = normalize_bits(vh.hash_bits)
                else:
                    hhex = getattr(vh, 'hash_hex', '')[:16]
                    bits64 = bin(int(hhex, 16))[2:].zfill(64) if hhex else ""

                if bits64:
                    rec["phash_bits"] = bits64
                    rec["hash_prefix16"] = compute_prefix16(bits64)
                    # Lưu thêm dạng '0b' để đồng bộ với các nơi khác
                    rec["phash"] = f"0b{bits64}"
                else:
                    # Fallback: tính prefix từ hash metadata nếu có
                    if existing_hash:
                        bits_meta = normalize_bits(existing_hash)
                        rec["hash_prefix16"] = compute_prefix16(bits_meta)
            except Exception as e:
                # Lỗi pHash: fallback prefix từ metadata hash nếu có
                if existing_hash and (not has_prefix):
                    bits_meta = normalize_bits(existing_hash)
                    rec["hash_prefix16"] = compute_prefix16(bits_meta)
        else:
            # Không có URL: chỉ có thể lấy prefix từ metadata hash
            if existing_hash and (not has_prefix):
                bits_meta = normalize_bits(existing_hash)
                rec["hash_prefix16"] = compute_prefix16(bits_meta)

        enriched.append(rec)
    return enriched


def main():
    if not os.path.exists(INPUT_DB):
        print(f"❌ Không tìm thấy {INPUT_DB}")
        sys.exit(1)
    with open(INPUT_DB, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        print("❌ DB không phải dạng list")
        sys.exit(1)

    print(f"📂 Tải {len(data)} bản ghi. Bắt đầu enrich pHash + prefix16...")
    enriched = enrich_database(data)

    with open(OUTPUT_DB, "w", encoding="utf-8") as f:
        json.dump(enriched, f, ensure_ascii=False, indent=2)
    print(f"✅ Đã lưu: {OUTPUT_DB} (tổng {len(enriched)} bản ghi)")


if __name__ == "__main__":
    main()
