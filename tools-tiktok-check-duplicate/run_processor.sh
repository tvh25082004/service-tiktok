#!/usr/bin/env bash
# Script cài đặt và chạy TikTok Multi-Dataset Processor

echo "🚀 Bắt đầu cài đặt TikTok Multi-Dataset Processor..."

# Kiểm tra Python version
python_version=$(python3 --version 2>&1 | awk '{print $2}' | cut -d. -f1,2)
echo "📋 Python version: $python_version"

# Cài đặt dependencies
echo "📦 Đang cài đặt dependencies..."
pip3 install -r requirements.txt

# Kiểm tra ffmpeg
if ! command -v ffmpeg >/dev/null 2>&1; then
  echo "⚠️  Thiếu ffmpeg. Vui lòng cài đặt: brew install ffmpeg"
fi

# Kiểm tra các folder cần xử lý
echo "📁 Kiểm tra các folder cần xử lý..."

if [ ! -d "JP_result" ]; then
    echo "⚠️  Folder JP_result không tồn tại!"
    exit 1
fi

if [ ! -d "result" ]; then
    echo "⚠️  Folder result không tồn tại!"
    exit 1
fi

# Đếm số file JSON trong mỗi folder
jp_count=$(find JP_result -name "*.json" | wc -l)
result_count=$(find result -name "*.json" | wc -l)

echo "📊 Số file JSON tìm thấy:"
echo "   - JP_result: $jp_count files"
echo "   - result: $result_count files"

if [ $jp_count -eq 0 ] && [ $result_count -eq 0 ]; then
    echo "❌ Không tìm thấy file JSON nào trong cả 2 folder!"
    exit 1
fi

# Chạy multi-dataset processor
echo "🎬 Bắt đầu xử lý tất cả dataset..."
python3 process_multiple_datasets.py

echo "🎉 Hoàn thành xử lý tất cả dataset!"
