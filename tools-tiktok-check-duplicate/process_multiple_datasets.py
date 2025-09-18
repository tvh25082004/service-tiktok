#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script xử lý nhiều dataset TikTok từ các folder khác nhau
Tạo hash cho tất cả video và xuất kết quả riêng cho mỗi folder
"""

import json
import os
import hashlib
import logging
from datetime import datetime
from typing import Dict, List, Any
from pathlib import Path

# Cấu hình logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('multi_dataset_processor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class MultiDatasetProcessor:
    """Class xử lý nhiều dataset TikTok từ các folder khác nhau"""
    
    def __init__(self):
        self.processed_data = {}
        
    def convert_timestamp_to_datetime(self, timestamp: int) -> str:
        """Chuyển đổi timestamp thành datetime string"""
        try:
            if timestamp and timestamp > 0:
                dt = datetime.fromtimestamp(timestamp)
                return dt.strftime("%Y-%m-%d %H:%M:%S")
            return "N/A"
        except Exception as e:
            logger.warning(f"Lỗi chuyển đổi timestamp {timestamp}: {e}")
            return "N/A"
    
    def get_device_type(self, source_platform: int) -> str:
        """Xác định loại thiết bị từ source_platform"""
        device_mapping = {
            0: "Unknown",
            1: "iPhone",
            2: "Android", 
            3: "iPad",
            4: "Android Tablet",
            5: "Web Browser",
            6: "Desktop App",
            7: "Smart TV",
            8: "Other"
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
        """Xử lý một video đơn lẻ"""
        try:
            # Lấy thông tin cơ bản
            aweme_id = video_data.get("aweme_id", f"unknown_{index}")
            
            # Xử lý thời gian đăng
            create_time = self.convert_timestamp_to_datetime(video_data.get("create_time"))
            
            # Xử lý thông tin tác giả
            author_info = video_data.get("author", {})
            region = author_info.get("region", "Unknown")
            author_uid = author_info.get("uid", "")
            
            # Xử lý thông tin âm nhạc
            music_info = video_data.get("music", {})
            source_platform = music_info.get("source_platform", 0)
            device_type = self.get_device_type(source_platform)
            
            # Xử lý thống kê
            stats = video_data.get("statistics", {})
            play_count = stats.get("play_count", 0)
            digg_count = stats.get("digg_count", 0)
            comment_count = stats.get("comment_count", 0)
            
            # Xử lý trạng thái
            status_info = video_data.get("status", {})
            is_prohibited = status_info.get("is_prohibited", False)
            allow_comment = status_info.get("allow_comment", True)
            
            # Xử lý URL video
            share_url = video_data.get("share_url", "N/A")
            
            # Tạo video hash
            video_hash = self.generate_video_hash(video_data)
            # Tính prefix16 cho metadata-hash (dùng prefilter khi chưa có pHash)
            normalized_hash = video_hash[2:] if isinstance(video_hash, str) and video_hash.startswith('0b') else str(video_hash)
            normalized_hash = normalized_hash.zfill(64)
            hash_prefix16 = normalized_hash[:16]
            
            # Tạo kết quả
            result = {
                "aweme_id": aweme_id,
                "author_uid": author_uid,
                "create_time": create_time,
                "region": region,
                "device_type": device_type,
                "views": play_count,
                "likes": digg_count,
                "comments": comment_count,
                "shadow_ban": is_prohibited,
                "muted": not allow_comment,
                "video_url": share_url,
                "hash": video_hash,
                "hash_prefix16": hash_prefix16
            }
            
            logger.info(f"✅ Xử lý video {index + 1}: {aweme_id}")
            return result
            
        except Exception as e:
            logger.error(f"❌ Lỗi xử lý video {index + 1}: {e}")
            return {
                "aweme_id": f"error_{index}",
                "create_time": "N/A",
                "region": "Unknown",
                "device_type": "Unknown",
                "views": 0,
                "likes": 0,
                "comments": 0,
                "shadow_ban": False,
                "muted": False,
                "video_url": "N/A",
                "hash": f"0b{'0' * 64}"
            }
    
    def load_json_file(self, file_path: str) -> List[Dict[str, Any]]:
        """Đọc file JSON"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Kiểm tra cấu trúc dữ liệu
            if isinstance(data, list):
                return data
            elif isinstance(data, dict) and 'data' in data:
                return data['data']
            else:
                logger.warning(f"⚠️ Cấu trúc file không mong đợi: {file_path}")
                return []
                
        except Exception as e:
            logger.error(f"❌ Lỗi đọc file {file_path}: {e}")
            return []
    
    def process_folder(self, folder_path: str, folder_name: str) -> bool:
        """Xử lý tất cả file JSON trong một folder"""
        try:
            folder_path = Path(folder_path)
            if not folder_path.exists():
                logger.error(f"❌ Folder không tồn tại: {folder_path}")
                return False
            
            # Tìm tất cả file JSON
            json_files = list(folder_path.glob("*.json"))
            if not json_files:
                logger.warning(f"⚠️ Không tìm thấy file JSON nào trong {folder_path}")
                return False
            
            logger.info(f"📁 Xử lý folder: {folder_name}")
            logger.info(f"📊 Tìm thấy {len(json_files)} file JSON")
            
            all_videos = []
            total_videos = 0
            
            # Xử lý từng file
            for i, json_file in enumerate(json_files):
                logger.info(f"📄 Xử lý file {i+1}/{len(json_files)}: {json_file.name}")
                
                videos = self.load_json_file(str(json_file))
                if not videos:
                    continue
                
                logger.info(f"   📹 Tìm thấy {len(videos)} video trong file")
                
                # Xử lý từng video
                for j, video_data in enumerate(videos):
                    processed_video = self.process_single_video(video_data, total_videos)
                    all_videos.append(processed_video)
                    total_videos += 1
                    
                    if (j + 1) % 100 == 0:
                        logger.info(f"   ⏳ Đã xử lý {j + 1}/{len(videos)} video...")
            
            # Lưu kết quả
            output_file = f"processed_{folder_name}_dataset.json"
            self.save_processed_data(all_videos, output_file)
            
            logger.info(f"✅ Hoàn thành xử lý folder {folder_name}")
            logger.info(f"📊 Tổng cộng: {total_videos} video đã được xử lý")
            logger.info(f"💾 Kết quả lưu tại: {output_file}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Lỗi xử lý folder {folder_name}: {e}")
            return False
    
    def process_folder_for_merge(self, folder_path: str, folder_name: str) -> List[Dict[str, Any]]:
        """Xử lý tất cả file JSON trong một folder và trả về danh sách video (không lưu file)"""
        try:
            folder_path = Path(folder_path)
            if not folder_path.exists():
                logger.error(f"❌ Folder không tồn tại: {folder_path}")
                return None
            
            # Tìm tất cả file JSON
            json_files = list(folder_path.glob("*.json"))
            if not json_files:
                logger.warning(f"⚠️ Không tìm thấy file JSON nào trong {folder_path}")
                return []
            
            logger.info(f"📊 Tìm thấy {len(json_files)} file JSON")
            
            all_videos = []
            total_videos = 0
            
            # Xử lý từng file
            for i, json_file in enumerate(json_files):
                logger.info(f"📄 Xử lý file {i+1}/{len(json_files)}: {json_file.name}")
                
                videos = self.load_json_file(str(json_file))
                if not videos:
                    continue
                
                logger.info(f"   📹 Tìm thấy {len(videos)} video trong file")
                
                # Xử lý từng video
                for j, video_data in enumerate(videos):
                    processed_video = self.process_single_video(video_data, total_videos)
                    all_videos.append(processed_video)
                    total_videos += 1
                    
                    if (j + 1) % 100 == 0:
                        logger.info(f"   ⏳ Đã xử lý {j + 1}/{len(videos)} video...")
            
            logger.info(f"✅ Hoàn thành xử lý folder {folder_name}")
            logger.info(f"📊 Tổng cộng: {total_videos} video đã được xử lý")
            
            return all_videos
            
        except Exception as e:
            logger.error(f"❌ Lỗi xử lý folder {folder_name}: {e}")
            return None
    
    def save_processed_data(self, data: List[Dict[str, Any]], output_file: str) -> bool:
        """Lưu dữ liệu đã xử lý"""
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"💾 Đã lưu {len(data)} video vào {output_file}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Lỗi lưu file {output_file}: {e}")
            return False
    
    def process_all_folders(self, folders: Dict[str, str]) -> bool:
        """Xử lý tất cả các folder và gộp thành 1 file duy nhất"""
        logger.info("🚀 Bắt đầu xử lý nhiều dataset TikTok...")
        
        all_videos = []
        success_count = 0
        total_folders = len(folders)
        
        for folder_name, folder_path in folders.items():
            logger.info(f"\n{'='*50}")
            logger.info(f"📁 Xử lý folder: {folder_name}")
            logger.info(f"📂 Đường dẫn: {folder_path}")
            logger.info(f"{'='*50}")
            
            folder_videos = self.process_folder_for_merge(folder_path, folder_name)
            if folder_videos is not None:
                all_videos.extend(folder_videos)
                success_count += 1
                logger.info(f"✅ Thành công: {folder_name} - {len(folder_videos)} video")
            else:
                logger.error(f"❌ Thất bại: {folder_name}")
        
        # Lưu tất cả video vào 1 file duy nhất
        if all_videos:
            output_file = "data_final.json"
            if self.save_processed_data(all_videos, output_file):
                logger.info(f"\n🎉 Hoàn thành! Đã gộp {len(all_videos)} video từ {success_count}/{total_folders} folder")
                logger.info(f"💾 File kết quả: {output_file}")
                return True
        
        logger.error(f"❌ Không có dữ liệu để lưu!")
        return False

def main():
    """Hàm chính"""
    processor = MultiDatasetProcessor()
    
    # Định nghĩa các folder cần xử lý
    folders = {
        "JP_result": "JP_result",
        "result": "result"
    }
    
    # Xử lý tất cả folder
    success = processor.process_all_folders(folders)
    
    if success:
        logger.info("🎉 Tất cả dataset đã được xử lý thành công!")
    else:
        logger.error("❌ Một số dataset xử lý thất bại!")
    
    return success

if __name__ == "__main__":
    main()
