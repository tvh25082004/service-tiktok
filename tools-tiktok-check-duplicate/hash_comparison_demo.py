#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TikTok Hash Comparison Demo
Demo cách so sánh hash để phát hiện video trùng lặp
"""

import json
import hashlib
from typing import List, Dict, Any

def load_processed_data(file_path: str) -> List[Dict[str, Any]]:
    """Load dữ liệu đã xử lý"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def find_duplicate_videos(data: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """
    Tìm video trùng lặp dựa trên hash
    
    Args:
        data: List các video đã xử lý
        
    Returns:
        Dictionary với hash làm key và list video trùng lặp làm value
    """
    hash_groups = {}
    
    for video in data:
        video_hash = video.get('hash', '')
        if video_hash not in hash_groups:
            hash_groups[video_hash] = []
        hash_groups[video_hash].append(video)
    
    # Chỉ trả về các nhóm có nhiều hơn 1 video (trùng lặp)
    duplicates = {hash_val: videos for hash_val, videos in hash_groups.items() if len(videos) > 1}
    
    return duplicates

def compare_video_similarity(hash1: str, hash2: str) -> int:
    """
    So sánh độ tương đồng giữa 2 hash bằng Hamming distance
    
    Args:
        hash1: Hash đầu tiên (binary string với format 0bxxxxxxxx...)
        hash2: Hash thứ hai (binary string với format 0bxxxxxxxx...)
        
    Returns:
        Số bit khác nhau (0 = giống nhau hoàn toàn)
    """
    try:
        # Lấy phần binary (bỏ prefix '0b')
        bin1 = hash1[2:] if hash1.startswith('0b') else hash1
        bin2 = hash2[2:] if hash2.startswith('0b') else hash2
        
        # Đảm bảo cùng độ dài 64 bit
        bin1 = bin1.zfill(64)
        bin2 = bin2.zfill(64)
        
        # Tính Hamming distance
        distance = sum(c1 != c2 for c1, c2 in zip(bin1, bin2))
        return distance
        
    except Exception as e:
        print(f"Lỗi so sánh hash: {e}")
        return -1

def analyze_hash_distribution(data: List[Dict[str, Any]]):
    """Phân tích phân bố hash"""
    print("🔍 PHÂN TÍCH PHÂN BỐ HASH:")
    print("=" * 50)
    
    # Thống kê cơ bản
    total_videos = len(data)
    unique_hashes = len(set(video['hash'] for video in data))
    
    print(f"📊 Tổng số videos: {total_videos}")
    print(f"🔑 Số hash unique: {unique_hashes}")
    print(f"📈 Tỷ lệ unique: {unique_hashes/total_videos*100:.2f}%")
    
    # Tìm video trùng lặp
    duplicates = find_duplicate_videos(data)
    
    if duplicates:
        print(f"\n⚠️  Phát hiện {len(duplicates)} nhóm video trùng lặp:")
        for hash_val, videos in duplicates.items():
            print(f"\n🔗 Hash: {hash_val[:16]}...")
            print(f"   Số video trùng: {len(videos)}")
            for video in videos:
                print(f"   - {video['aweme_id']} | {video['ngay_dang']} | {video['quoc_gia']}")
    else:
        print("\n✅ Không có video trùng lặp!")
    
    # Phân tích độ tương đồng
    print(f"\n🔬 PHÂN TÍCH ĐỘ TƯƠNG ĐỒNG:")
    print("=" * 50)
    
    hashes = [video['hash'] for video in data]
    similarities = []
    
    for i in range(len(hashes)):
        for j in range(i + 1, len(hashes)):
            distance = compare_video_similarity(hashes[i], hashes[j])
            if distance >= 0:
                similarities.append(distance)
    
    if similarities:
        avg_distance = sum(similarities) / len(similarities)
        min_distance = min(similarities)
        max_distance = max(similarities)
        
        print(f"📊 Khoảng cách Hamming trung bình: {avg_distance:.2f}")
        print(f"📊 Khoảng cách tối thiểu: {min_distance}")
        print(f"📊 Khoảng cách tối đa: {max_distance}")
        
        # Phân loại độ tương đồng
        similar_count = sum(1 for d in similarities if d <= 10)
        moderate_count = sum(1 for d in similarities if 10 < d <= 50)
        different_count = sum(1 for d in similarities if d > 50)
        
        print(f"\n📈 Phân loại độ tương đồng:")
        print(f"   🔴 Rất giống (≤10 bit khác): {similar_count}")
        print(f"   🟡 Tương đồng (11-50 bit khác): {moderate_count}")
        print(f"   🟢 Khác biệt (>50 bit khác): {different_count}")

def demo_hash_comparison():
    """Demo so sánh hash"""
    print("🎬 DEMO SO SÁNH HASH VIDEO TIKTOK")
    print("=" * 60)
    
    # Load dữ liệu
    data = load_processed_data('/Users/tranvanhuy/Desktop/project/Tiktok/processed_tiktok_dataset.json')
    
    # Hiển thị một vài hash mẫu
    print("\n📋 MẪU HASH CỦA CÁC VIDEO:")
    print("-" * 60)
    for i, video in enumerate(data[:5]):
        print(f"{i+1}. Video ID: {video['aweme_id']}")
        print(f"   Hash: {video['hash']}")
        print(f"   Ngày: {video['ngay_dang']} | Quốc gia: {video['quoc_gia']}")
        print()
    
    # Phân tích phân bố hash
    analyze_hash_distribution(data)
    
    # Demo so sánh cụ thể
    print(f"\n🔍 DEMO SO SÁNH CỤ THỂ:")
    print("=" * 60)
    
    if len(data) >= 2:
        video1 = data[0]
        video2 = data[1]
        
        print(f"Video 1: {video1['aweme_id']}")
        print(f"Hash 1:  {video1['hash']}")
        print()
        print(f"Video 2: {video2['aweme_id']}")
        print(f"Hash 2:  {video2['hash']}")
        print()
        
        distance = compare_video_similarity(video1['hash'], video2['hash'])
        print(f"🔬 Khoảng cách Hamming: {distance} bit")
        
        if distance == 0:
            print("✅ Hai video GIỐNG NHAU HOÀN TOÀN!")
        elif distance <= 10:
            print("🟡 Hai video RẤT GIỐNG NHAU!")
        elif distance <= 50:
            print("🟠 Hai video TƯƠNG ĐỒNG!")
        else:
            print("🔴 Hai video KHÁC BIỆT!")

if __name__ == "__main__":
    demo_hash_comparison()
