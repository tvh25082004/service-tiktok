#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Video Duplicate Checker - TikTok Video Hash Comparison Tool
Sử dụng videohash và Hamming distance để kiểm tra video trùng lặp
"""

import json
import os
import sys
import time
import hashlib
from typing import List, Dict, Any, Tuple
from pathlib import Path
import argparse

try:
    from videohash import VideoHash
    import requests
    # Fix PIL compatibility issue
    import PIL.Image
    if not hasattr(PIL.Image, 'ANTIALIAS'):
        PIL.Image.ANTIALIAS = PIL.Image.LANCZOS
except ImportError:
    print("❌ Thiếu thư viện cần thiết!")
    print("📦 Đang cài đặt...")
    os.system("pip install videohash requests")
    from videohash import VideoHash
    import requests
    # Fix PIL compatibility issue
    import PIL.Image
    if not hasattr(PIL.Image, 'ANTIALIAS'):
        PIL.Image.ANTIALIAS = PIL.Image.LANCZOS

class VideoDuplicateChecker:
    """Class kiểm tra video trùng lặp sử dụng hash và Hamming distance"""
    
    def __init__(self, database_path: str = "data_final.json"):
        self.database_path = database_path
        self.database = []
        self.load_database()
        
    def normalize_hash(self, hash_value: str) -> str:
        """Chuẩn hóa hash về 64-bit binary không có prefix '0b'"""
        if not hash_value:
            return ""
        if hash_value.startswith("0b"):
            return hash_value[2:]
        return hash_value

    def compute_prefix16(self, normalized_hash: str) -> str:
        """Lấy 16 bit đầu làm tiền tố để prefilter."""
        if not normalized_hash:
            return ""
        h = normalized_hash
        if h.startswith('0b'):
            h = h[2:]
        return h.zfill(64)[:16]

    def load_database(self) -> bool:
        """Tải database video từ file JSON"""
        try:
            if not os.path.exists(self.database_path):
                print(f"❌ Không tìm thấy file database: {self.database_path}")
                return False
                
            print(f"📂 Đang tải database từ {self.database_path}...")
            with open(self.database_path, 'r', encoding='utf-8') as f:
                self.database = json.load(f)
            
            print(f"✅ Đã tải {len(self.database)} video từ database")
            return True
            
        except Exception as e:
            print(f"❌ Lỗi tải database: {e}")
            return False
    
    def generate_video_hash(self, video_url: str) -> str:
        """Fallback: tạo hash 64-bit từ URL metadata. Tạo hash ổn định dựa trên video ID."""
        try:
            print("🎬 Đang phân tích video URL...")
            print(f"🔗 URL: {video_url}")
            
            # Trích xuất video ID từ URL
            video_id = self.extract_video_id(video_url)
            if not video_id:
                raise ValueError("Không thể trích xuất video ID từ URL")
            
            # Tạo hash ổn định từ video ID (không dùng timestamp để đảm bảo consistency)
            hash_string = f"tiktok_video_{video_id}"
            
            # Tạo SHA256 hash
            hash_object = hashlib.sha256(hash_string.encode('utf-8'))
            hash_hex = hash_object.hexdigest()
            
            # Chuyển đổi hex thành 64-bit binary
            hash_hex_64 = hash_hex[:16]  # Lấy 16 ký tự đầu (64 bit)
            hash_int = int(hash_hex_64, 16)
            hash_binary = bin(hash_int)[2:].zfill(64)  # Đảm bảo đúng 64 bit
            
            print(f"✅ Tạo hash thành công: {hash_binary[:20]}...")
            return hash_binary
            
        except Exception as e:
            print(f"❌ Lỗi tạo video hash: {e}")
            return None
    
    def extract_video_id(self, url: str) -> str:
        """Trích xuất video ID từ TikTok URL"""
        try:
            # Tìm pattern video ID trong URL
            import re
            patterns = [
                r'/video/(\d+)',
                r'video/(\d+)',
                r'/(\d{19})',  # TikTok video ID thường có 19 chữ số
            ]
            
            for pattern in patterns:
                match = re.search(pattern, url)
                if match:
                    return match.group(1)
            
            return None
            
        except Exception:
            return None
    
    def hamming_distance(self, hash1: str, hash2: str) -> int:
        """Tính Hamming distance giữa 2 hash binary"""
        if len(hash1) != len(hash2):
            return -1
            
        distance = 0
        for i in range(len(hash1)):
            if hash1[i] != hash2[i]:
                distance += 1
                
        return distance
    
    def prefilter_by_prefix(self, target_hash: str, prefix_length: int = 16) -> List[Dict[str, Any]]:
        """Prefilter database bằng prefix bits để tăng tốc"""
        target_prefix = self.compute_prefix16(self.normalize_hash(target_hash))[:prefix_length]
        candidates = []
        
        print(f"🔍 Target prefix: {target_prefix}")
        
        for video in self.database:
            # Ưu tiên dùng trường hash_prefix16/prefix16 nếu đã có trong DB (pHash hoặc metadata-hash)
            db_prefix = video.get('hash_prefix16') or video.get('prefix16')
            if isinstance(db_prefix, int):
                # nếu là số, chuyển thành 16-bit binary
                db_prefix = bin(int(db_prefix))[2:].zfill(16)
            if not db_prefix:
                db_hash = self.normalize_hash(video.get('hash', ''))
                db_prefix = self.compute_prefix16(db_hash)
            
            # Đảm bảo db_prefix là string và có đủ độ dài
            db_prefix = str(db_prefix).zfill(16)[:16]
            
            # Debug: print first few prefixes to understand the issue
            if len(candidates) < 3:
                print(f"🔍 DB prefix: {db_prefix}, Target: {target_prefix}, Match: {db_prefix.startswith(target_prefix)}")
            
            if db_prefix.startswith(target_prefix):
                candidates.append(video)
                
        return candidates
    
    def find_duplicates(self, video_url: str, threshold: int = 12) -> Dict[str, Any]:
        """Tìm video trùng lặp trong database"""
        print("\n" + "="*60)
        print("🔍 BẮT ĐẦU KIỂM TRA VIDEO TRÙNG LẶP")
        print("="*60)
        
        # 1) Đối chiếu trực tiếp theo aweme_id/URL
        input_aweme_id = self.extract_video_id(video_url)
        if input_aweme_id:
            for video in self.database:
                if str(video.get('aweme_id')) == str(input_aweme_id) or str(input_aweme_id) in str(video.get('video_url', '')):
                    return {
                        "is_duplicate": True,
                        "similarity": 64,
                        "hamming_distance": 0,
                        "closest_match": video,
                        "threshold": 12,
                        "total_candidates": 1
                    }

        # 2) Nếu không có trùng trực tiếp: tạo videohash pHash từ nội dung
        target_hash = None
        try:
            print("\n🎬 Đang lấy pHash từ nội dung video (videohash)...")
            vh = VideoHash(url=video_url)
            # videohash trả về hash_hex và hash_bits; dùng 64-bit binary cho Hamming
            # Lấy 64 bit đầu từ vh.hash_bits
            if hasattr(vh, 'hash_bits') and isinstance(vh.hash_bits, str):
                bits = vh.hash_bits.zfill(64)[:64]
                target_hash = bits
            else:
                # Fallback: chuyển từ hex sang 64-bit
                hhex = vh.hash_hex[:16]
                target_hash = bin(int(hhex, 16))[2:].zfill(64)
            print("✅ Sử dụng pHash từ videohash thành công")
        except Exception as e:
            print(f"⚠️ Lỗi videohash: {e}")
            print("🔄 Chuyển sang phương pháp fallback metadata-hash...")
            target_hash = self.generate_video_hash(video_url)
        if not target_hash:
            return {"error": "Không thể tạo hash cho video"}
        
        print(f"\n📊 Hash video: {target_hash}")
        
        # Prefilter để tăng tốc
        print(f"\n🔍 Đang prefilter database (prefix {16} bits)...")
        candidates = self.prefilter_by_prefix(target_hash, 16)
        print(f"📋 Tìm thấy {len(candidates)} ứng viên tiềm năng")
        
        if not candidates:
            return {
                "is_duplicate": False,
                "similarity": 0,
                "hamming_distance": 64,
                "closest_match": None,
                "threshold": threshold,
                "total_candidates": 0,
                "message": "Không tìm thấy video tương tự"
            }
        
        # So sánh với các ứng viên
        print(f"\n⚡ Đang so sánh với {len(candidates)} video...")
        min_distance = float('inf')
        closest_match = None
        
        for i, video in enumerate(candidates):
            if i % 100 == 0:
                print(f"   ⏳ Đã xử lý {i}/{len(candidates)} video...")
                
            db_hash = self.normalize_hash(video.get('hash', ''))
            if not db_hash:
                continue
                
            distance = self.hamming_distance(self.normalize_hash(target_hash), db_hash)
            if distance == -1:
                continue
                
            if distance < min_distance:
                min_distance = distance
                closest_match = video
        
        # Xử lý trường hợp không có candidates
        if min_distance == float('inf'):
            min_distance = 64  # Không có video nào để so sánh
        
        # Xác định kết quả
        is_duplicate = min_distance <= threshold
        similarity = max(0, 64 - min_distance)  # Tính similarity percentage
        
        result = {
            "is_duplicate": is_duplicate,
            "similarity": similarity,
            "hamming_distance": min_distance,
            "closest_match": closest_match,
            "threshold": threshold,
            "total_candidates": len(candidates)
        }
        
        return result
    
    def display_result(self, video_url: str, result: Dict[str, Any]):
        """Hiển thị kết quả theo format như trong ảnh"""
        print("\n" + "="*60)
        print("📊 THÔNG TIN VIDEO")
        print("="*60)
        
        # Thông tin cơ bản
        print(f"🔗 Video URL: {video_url}")
        print(f"📅 Thời gian kiểm tra: {time.strftime('%d/%m/%Y %H:%M:%S')}")
        
        if "error" in result:
            print(f"❌ Lỗi: {result['error']}")
            return
        
        # Kết quả so sánh
        print(f"\n📈 KẾT QUẢ SO SÁNH:")
        print(f"   • Hamming Distance: {result['hamming_distance']}/64 bits")
        print(f"   • Độ tương đồng: {result['similarity']:.1f}%")
        print(f"   • Ngưỡng: ≤ {result['threshold']} bits")
        print(f"   • Ứng viên kiểm tra: {result['total_candidates']} video")
        
        # Trạng thái trùng lặp
        print(f"\n🎯 TRẠNG THÁI:")
        if result['is_duplicate']:
            print("   ❌ Trùng lặp: CÓ")
            print("   ⚠️  Video này có thể là reupload!")
        else:
            print("   ✅ Trùng lặp: KHÔNG")
            print("   🆕 Video này có vẻ là nội dung mới!")
        
        # Thông tin video gần nhất
        if result['closest_match']:
            match = result['closest_match']
            print(f"\n🔍 VIDEO GẦN NHẤT:")
            print(f"   • ID: {match.get('aweme_id', 'N/A')}")
            print(f"   • Ngày đăng: {match.get('create_time', 'N/A')}")
            print(f"   • Quốc gia: {match.get('region', 'N/A')}")
            print(f"   • Views: {match.get('views', 0):,}")
            print(f"   • Likes: {match.get('likes', 0):,}")
            print(f"   • Comments: {match.get('comments', 0):,}")
            print(f"   • URL: {match.get('video_url', 'N/A')}")
        
        print("\n" + "="*60)
    
    def interactive_mode(self):
        """Chế độ tương tác với người dùng"""
        print("🎬 VIDEO DUPLICATE CHECKER")
        print("="*50)
        print("Kiểm tra video TikTok trùng lặp sử dụng hash và Hamming distance")
        print("="*50)
        
        while True:
            print("\n📝 Nhập link video TikTok (hoặc 'quit' để thoát):")
            video_url = input("🔗 URL: ").strip()
            
            if video_url.lower() in ['quit', 'exit', 'q']:
                print("👋 Tạm biệt!")
                break
            
            if not video_url:
                print("❌ Vui lòng nhập URL video!")
                continue
            
            if not ('tiktok.com' in video_url or 'douyin.com' in video_url):
                print("❌ Vui lòng nhập URL TikTok hợp lệ!")
                continue
            
            try:
                # Kiểm tra video
                result = self.find_duplicates(video_url)
                self.display_result(video_url, result)
                
            except KeyboardInterrupt:
                print("\n\n⏹️  Đã dừng bởi người dùng")
                break
            except Exception as e:
                print(f"\n❌ Lỗi: {e}")
                print("🔄 Vui lòng thử lại...")
            
            print("\n" + "-"*50)

def main():
    """Hàm chính"""
    parser = argparse.ArgumentParser(description='Video Duplicate Checker')
    parser.add_argument('--url', type=str, help='URL video để kiểm tra')
    parser.add_argument('--database', type=str, default='data_final.json', help='Đường dẫn file database')
    parser.add_argument('--threshold', type=int, default=12, help='Ngưỡng Hamming distance (mặc định: 12)')
    
    args = parser.parse_args()
    
    # Khởi tạo checker
    checker = VideoDuplicateChecker(args.database)
    
    if not checker.database:
        print("❌ Không thể tải database. Thoát chương trình.")
        return
    
    if args.url:
        # Chế độ command line
        result = checker.find_duplicates(args.url, args.threshold)
        checker.display_result(args.url, result)
    else:
        # Chế độ tương tác
        checker.interactive_mode()

if __name__ == "__main__":
    main()
