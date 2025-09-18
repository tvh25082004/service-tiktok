# TikTok Duplicate Checker — Luồng xử lý và cách chạy

## Mục tiêu
- Xử lý dữ liệu video TikTok từ nhiều nguồn JSON, tạo hash 64-bit cho mỗi video.
- Kiểm tra video trùng lặp nhanh và chính xác: ưu tiên ID (O(1)) rồi đến so khớp xấp xỉ bằng Hamming với prefilter `prefix16`.

## Luồng xử lý
1. Thu thập JSON thô trong thư mục `JP_result/`, `result/`.
2. Gộp và chuẩn hóa dữ liệu bằng `process_multiple_datasets.py` → tạo `data_final.json` với:
   - Các trường: `aweme_id`, `author_uid`, `video_url`, `create_time`, thống kê, trạng thái...
   - Hash 64-bit từ metadata và `hash_prefix16` (16 bit đầu) để tiền lọc nhanh.
3. (Tùy chọn) Enrich pHash nội dung bằng `enrich_phash_database.py` → `data_final_enriched.json` với:
   - `phash_bits` (64 bit), `phash` (0b...), cập nhật `hash_prefix16` từ pHash.
4. Kiểm tra trùng lặp với `video_duplicate_checker.py` cho một URL TikTok:
   - B1: trích `aweme_id` từ URL, tra DB → nếu có, kết luận trùng ngay (Hamming = 0).
   - B2: nếu không có, dùng hash 64-bit: prefilter theo `prefix16` → tính Hamming → nếu ≤ 12 thì duplicate.

## Thuật toán
- Hash 64-bit (mặc định trong DB): SHA-256 trên chuỗi metadata ổn định `aweme_id|author_uid|create_time|duration|widthxheight|play_count|digg_count|music_id`, lấy 16 hex đầu (64 bit) → nhị phân.
- `prefix16`: 16 bit đầu của hash nhị phân, dùng để lọc ứng viên cực nhanh trước khi so Hamming.
- Hamming distance: số bit khác nhau giữa 2 chuỗi 64-bit; duplicate nếu `distance ≤ 12` (có thể tinh chỉnh).
- pHash (tùy chọn): từ nội dung video bằng `videohash` (DCT-based), chính xác với biến thể encode nhưng tốn thời gian do tải/giải mã.

Tài liệu tham khảo
- Prefilter (ý tưởng tiền lọc ứng viên): https://techdocs.zebra.com/dcs/rfid/android/2-0-2-82/tutorials/prefilters/
- Perceptual hash, pHash: https://apiumhub.com/tech-blog-barcelona/introduction-perceptual-hashes-measuring-similarity/
- Hamming distance: https://www.datacamp.com/tutorial/hamming-distance

## Cấu trúc file chính
- `process_multiple_datasets.py`: gộp nhiều JSON → `data_final.json` (kèm `hash_prefix16`).
- `video_duplicate_checker.py`: kiểm tra trùng cho một URL dựa trên DB (`data_final.json` hoặc `data_final_enriched.json`).
- `enrich_phash_database.py`: tính pHash + `hash_prefix16` (từ pHash) → `data_final_enriched.json`.
- `run_processor.sh`: cài dependencies, kiểm tra thư mục, chạy gộp dữ liệu.

## Yêu cầu
- Python 3, pip3
- ffmpeg (bắt buộc nếu dùng pHash/videohash)

Cài đặt ffmpeg (macOS):
```bash
brew install ffmpeg
```

## Cài đặt dependencies
```bash
pip3 install -r requirements.txt
```
Bao gồm: `requests`, `videohash`, `yt-dlp`, `Pillow`.

## Cách chạy sau khi clone
### 1) Gộp dữ liệu (tạo data_final.json)
Cách 1 — Script:
```bash
bash run_processor.sh
```
Cách 2 — Thủ công:
```bash
python3 process_multiple_datasets.py
```
Kết quả: file `data_final.json`.

### 2) (Tùy chọn) Enrich pHash nội dung
Chậm vì cần tải/giải mã video cho nhiều bản ghi. Khuyến nghị chỉ xử lý incremental.
```bash
python3 enrich_phash_database.py
```
Kết quả: file `data_final_enriched.json`.

### 3) Kiểm tra trùng lặp cho một URL
Nhanh nhất (không cần pHash):
```bash
python3 video_duplicate_checker.py \
  --database data_final.json \
  --url "https://www.tiktok.com/@user/video/1234567890123456789" \
  --threshold 12 | cat
```
Nếu đã enrich pHash:
```bash
python3 video_duplicate_checker.py \
  --database data_final_enriched.json \
  --url "https://www.tiktok.com/@user/video/1234567890123456789" \
  --threshold 12 | cat
```

## Gợi ý vận hành
- Kiểm tra 1 URL:
  - Có `aweme_id` trong DB → tức thì.
  - Không có → hash 64-bit + `prefix16` → Hamming → nhanh.
- pHash nên tính incremental (hằng ngày cho video mới) hoặc khi cần độ chính xác cao.
- Khi scale lớn: dùng SQLite/Postgres với chỉ mục
  - `PRIMARY KEY (aweme_id)`
  - `INDEX (prefix16)` (nên lưu `prefix16` dạng số nguyên 16-bit để index hiệu quả).

## Lưu ý
- Dùng URL chuẩn (hạn chế query string dư thừa) để trích `aweme_id` ổn định.
- Có thể tinh chỉnh `threshold` và số bit `prefix16` theo dữ liệu thực tế.
# tools-tiktok-check-duplicate
