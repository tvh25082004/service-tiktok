#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TikTok Dataset Processor
Xử lý dataset TikTok và trích xuất các trường cần thiết
"""

import json
import os
import hashlib
from datetime import datetime
from typing import Dict, List, Any, Optional
import logging

# Cấu hình logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TikTokDatasetProcessor:
    """Class xử lý dataset TikTok"""
    
    def __init__(self, input_file: str, output_file: str = None):
        """
        Khởi tạo processor
        
        Args:
            input_file: Đường dẫn file JSON input
            output_file: Đường dẫn file JSON output (optional)
        """
        self.input_file = input_file
        self.output_file = output_file or f"processed_{os.path.basename(input_file)}"
        self.processed_data = []
        
    def convert_timestamp_to_datetime(self, timestamp: int) -> str:
        """
        Chuyển đổi timestamp thành datetime string
        
        Args:
            timestamp: Unix timestamp
            
        Returns:
            Datetime string format: YYYY-MM-DD HH:MM:SS
        """
        try:
            dt = datetime.fromtimestamp(timestamp)
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        except (ValueError, OSError) as e:
            logger.warning(f"Lỗi chuyển đổi timestamp {timestamp}: {e}")
            return "Unknown"
    
    def get_device_type(self, source_platform: int) -> str:
        """
        Chuyển đổi source_platform thành loại thiết bị
        
        Args:
            source_platform: Platform code từ TikTok API
            
        Returns:
            Device type string
        """
        device_mapping = {
            72: "PC",
            24: "Mobile", 
            1: "Mobile",
            2: "Mobile",
            3: "Mobile",
            4: "Mobile",
            5: "Mobile",
            6: "Mobile",
            7: "Mobile",
            8: "Mobile",
            9: "Mobile",
            10: "Mobile",
            11: "Mobile",
            12: "Mobile",
            13: "Mobile",
            14: "Mobile",
            15: "Mobile",
            16: "Mobile",
            17: "Mobile",
            18: "Mobile",
            19: "Mobile",
            20: "Mobile",
            21: "Mobile",
            22: "Mobile",
            23: "Mobile",
            25: "Mobile",
            26: "Mobile",
            27: "Mobile",
            28: "Mobile",
            29: "Mobile",
            30: "Mobile",
            31: "Mobile",
            32: "Mobile",
            33: "Mobile",
            34: "Mobile",
            35: "Mobile",
            36: "Mobile",
            37: "Mobile",
            38: "Mobile",
            39: "Mobile",
            40: "Mobile",
            41: "Mobile",
            42: "Mobile",
            43: "Mobile",
            44: "Mobile",
            45: "Mobile",
            46: "Mobile",
            47: "Mobile",
            48: "Mobile",
            49: "Mobile",
            50: "Mobile",
            51: "Mobile",
            52: "Mobile",
            53: "Mobile",
            54: "Mobile",
            55: "Mobile",
            56: "Mobile",
            57: "Mobile",
            58: "Mobile",
            59: "Mobile",
            60: "Mobile",
            61: "Mobile",
            62: "Mobile",
            63: "Mobile",
            64: "Mobile",
            65: "Mobile",
            66: "Mobile",
            67: "Mobile",
            68: "Mobile",
            69: "Mobile",
            70: "Mobile",
            71: "Mobile",
            73: "PC",
            74: "PC",
            75: "PC",
            76: "PC",
            77: "PC",
            78: "PC",
            79: "PC",
            80: "PC",
            81: "PC",
            82: "PC",
            83: "PC",
            84: "PC",
            85: "PC",
            86: "PC",
            87: "PC",
            88: "PC",
            89: "PC",
            90: "PC",
            91: "PC",
            92: "PC",
            93: "PC",
            94: "PC",
            95: "PC",
            96: "PC",
            97: "PC",
            98: "PC",
            99: "PC",
            100: "PC"
        }
        
        return device_mapping.get(source_platform, "Unknown")
    
    def generate_video_hash(self, video_data: Dict[str, Any]) -> str:
        """
        Tạo video hash từ metadata của video (64-bit binary format như videohash)
        
        Args:
            video_data: Dữ liệu video từ TikTok API
            
        Returns:
            Video hash string (64-bit binary format: 0bxxxxxxxx...)
        """
        try:
            # Lấy các thông tin quan trọng để tạo hash
            aweme_id = str(video_data.get("aweme_id", ""))
            author_uid = str(video_data.get("author", {}).get("uid", ""))
            create_time = str(video_data.get("create_time", ""))
            
            # Thông tin video
            video_info = video_data.get("video", {})
            duration = str(video_info.get("duration", ""))
            width = str(video_info.get("width", ""))
            height = str(video_info.get("height", ""))
            
            # Thông tin thống kê
            stats = video_data.get("statistics", {})
            play_count = str(stats.get("play_count", ""))
            digg_count = str(stats.get("digg_count", ""))
            
            # Thông tin âm nhạc
            music_info = video_data.get("music", {})
            music_id = str(music_info.get("id", ""))
            
            # Tạo chuỗi để hash
            hash_string = f"{aweme_id}|{author_uid}|{create_time}|{duration}|{width}x{height}|{play_count}|{digg_count}|{music_id}"
            
            # Tạo SHA256 hash
            hash_object = hashlib.sha256(hash_string.encode('utf-8'))
            hash_hex = hash_object.hexdigest()
            
            # Chuyển đổi hex thành 64-bit binary
            # Lấy 16 ký tự đầu của SHA256 (64 bit)
            hash_hex_64 = hash_hex[:16]
            
            # Chuyển hex thành integer rồi thành binary
            hash_int = int(hash_hex_64, 16)
            hash_binary = bin(hash_int)[2:]  # Bỏ '0b' prefix
            
            # Đảm bảo đúng 64 bit
            hash_binary = hash_binary.zfill(64)
            
            # Thêm prefix '0b'
            video_hash = f"0b{hash_binary}"
            
            logger.info(f"Tạo hash thành công cho video {aweme_id}: {video_hash[:20]}...")
            return video_hash
            
        except Exception as e:
            logger.error(f"Lỗi tạo video hash: {e}")
            # Fallback hash nếu có lỗi
            fallback_string = f"{video_data.get('aweme_id', 'unknown')}|{video_data.get('create_time', 'unknown')}"
            fallback_hex = hashlib.sha256(fallback_string.encode('utf-8')).hexdigest()[:16]
            fallback_int = int(fallback_hex, 16)
            fallback_binary = bin(fallback_int)[2:].zfill(64)
            return f"0b{fallback_binary}"
    
    
    def process_single_video(self, video_data: Dict[str, Any], index: int) -> Dict[str, Any]:
        """
        Xử lý một video đơn lẻ
        
        Args:
            video_data: Dữ liệu video từ TikTok API
            index: Index của video trong dataset
            
        Returns:
            Dictionary chứa các trường đã xử lý
        """
        try:
            logger.info(f"Đang xử lý video {index + 1}...")
            
            # Trích xuất các trường cơ bản
            processed_video = {
                "index": index,
                "aweme_id": video_data.get("aweme_id", "Unknown"),
                "ngay_dang": self.convert_timestamp_to_datetime(video_data.get("create_time", 0)),
                "quoc_gia": video_data.get("author", {}).get("region", "Unknown"),
                "thiet_bi_dang": self.get_device_type(video_data.get("music", {}).get("source_platform", 0)),
                "views": video_data.get("statistics", {}).get("play_count", 0),
                "likes": video_data.get("statistics", {}).get("digg_count", 0),
                "comments": video_data.get("statistics", {}).get("comment_count", 0),
                "shadow_ban_status": video_data.get("status", {}).get("is_prohibited", False),
                "muted_status": not video_data.get("status", {}).get("allow_comment", True),
                "video_url": video_data.get("share_url", "Unknown"),
                "hash": None
            }
            
            # Tạo video hash từ metadata
            processed_video["hash"] = self.generate_video_hash(video_data)
            
            return processed_video
            
        except Exception as e:
            logger.error(f"Lỗi xử lý video {index + 1}: {e}")
            return {
                "index": index,
                "aweme_id": "Error",
                "ngay_dang": "Error",
                "quoc_gia": "Error",
                "thiet_bi_dang": "Error",
                "views": 0,
                "likes": 0,
                "comments": 0,
                "shadow_ban_status": False,
                "muted_status": False,
                "video_url": "Error",
                "hash": "error_hash"
            }
    
    def load_dataset(self) -> List[Dict[str, Any]]:
        """
        Load dataset từ file JSON
        
        Returns:
            List các video data
        """
        try:
            logger.info(f"Đang load dataset từ {self.input_file}...")
            
            with open(self.input_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if isinstance(data, list):
                logger.info(f"Đã load {len(data)} videos từ dataset")
                return data
            else:
                logger.error("Dataset không phải là array")
                return []
                
        except Exception as e:
            logger.error(f"Lỗi load dataset: {e}")
            return []
    
    def save_processed_data(self) -> bool:
        """
        Lưu dữ liệu đã xử lý vào file JSON
        
        Returns:
            True nếu thành công, False nếu thất bại
        """
        try:
            logger.info(f"Đang lưu dữ liệu đã xử lý vào {self.output_file}...")
            
            with open(self.output_file, 'w', encoding='utf-8') as f:
                json.dump(self.processed_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Đã lưu thành công {len(self.processed_data)} videos vào {self.output_file}")
            return True
            
        except Exception as e:
            logger.error(f"Lỗi lưu dữ liệu: {e}")
            return False
    
    def process_dataset(self) -> bool:
        """
        Xử lý toàn bộ dataset
        
        Returns:
            True nếu thành công, False nếu thất bại
        """
        try:
            # Load dataset
            dataset = self.load_dataset()
            if not dataset:
                logger.error("Không thể load dataset")
                return False
            
            # Xử lý từng video
            total_videos = len(dataset)
            logger.info(f"Bắt đầu xử lý {total_videos} videos...")
            
            for i, video_data in enumerate(dataset):
                processed_video = self.process_single_video(video_data, i)
                self.processed_data.append(processed_video)
                
                # Log progress mỗi 10 videos
                if (i + 1) % 10 == 0:
                    logger.info(f"Đã xử lý {i + 1}/{total_videos} videos...")
            
            # Lưu dữ liệu đã xử lý
            if self.save_processed_data():
                logger.info("Hoàn thành xử lý dataset!")
                return True
            else:
                logger.error("Lỗi lưu dữ liệu đã xử lý")
                return False
                
        except Exception as e:
            logger.error(f"Lỗi xử lý dataset: {e}")
            return False

def main():
    """Hàm main để chạy processor"""
    
    # Đường dẫn file input
    input_file = "/Users/tranvanhuy/Desktop/project/Tiktok/dataset_fast-tiktok-api_2025-09-13_05-22-06-209.json"
    
    # Đường dẫn file output
    output_file = "/Users/tranvanhuy/Desktop/project/Tiktok/processed_tiktok_dataset.json"
    
    # Tạo processor
    processor = TikTokDatasetProcessor(input_file, output_file)
    
    # Xử lý dataset
    success = processor.process_dataset()
    
    if success:
        print("✅ Xử lý dataset thành công!")
        print(f"📁 File output: {output_file}")
        print(f"📊 Số lượng videos đã xử lý: {len(processor.processed_data)}")
    else:
        print("❌ Xử lý dataset thất bại!")

if __name__ == "__main__":
    main()
