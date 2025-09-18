from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import subprocess
import asyncio
import os
import re
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Xin chào! Gửi URL TikTok cho tôi để kiểm tra video trùng lặp nhé.")
async def reply_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    tiktok_pattern = r'https?://(?:www\.)?tiktok\.com/@[\w.-]+/(?:video|photo)/\d+'
    
    if re.search(tiktok_pattern, user_text):
        await update.message.reply_text("🔍 Đang kiểm tra video trùng lặp, vui lòng đợi...")
        try:
            cmd = f'python video_duplicate_checker.py --url={user_text}'
            env = os.environ.copy()
            env['PYTHONIOENCODING'] = 'utf-8'
            env['PYTHONUTF8'] = '1'
            process = await asyncio.create_subprocess_shell(
                cmd,
                cwd=r'/home/tranhuy/Desktop/Project/Tools/tools-tiktok-check-duplicate',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env  
            )
            
            stdout, stderr = await process.communicate()
            output = stdout.decode('utf-8', errors='replace')
            error_output = stderr.decode('utf-8', errors='replace')
            
            if process.returncode == 0:
                if output:
                    if len(output) > 4000:
                        lines = output.split('\n')
                        important_lines = []
                        capture = False
                        
                        for line in lines:
                            if '📊 THÔNG TIN VIDEO' in line or capture:
                                capture = True
                                important_lines.append(line)
                            elif '🔍 BẮT ĐẦU KIỂM TRA' in line:
                                important_lines.append(line)
                        
                        output = '\n'.join(important_lines[-50:]) 
                    output = output.strip()
                    await update.message.reply_text(f"```\n{output}\n```", parse_mode='Markdown')
                else:
                    await update.message.reply_text("✅ Kiểm tra hoàn tất nhưng không có output.")
            else:
                if error_output:
                    if len(error_output) > 3500:
                        error_output = error_output[-3500:]
                    error_msg = f"❌ Lỗi khi kiểm tra video:\n```\n{error_output}\n```"
                else:
                    error_msg = f"❌ Script thực thi thất bại với return code: {process.returncode}"
                
                await update.message.reply_text(error_msg, parse_mode='Markdown')
                
        except Exception as e:
            await update.message.reply_text(f"❌ Lỗi hệ thống: {str(e)}")
    else:
        await update.message.reply_text(
            "⚠️ Vui lòng gửi URL TikTok hợp lệ!\n"
            "Ví dụ: https://www.tiktok.com/@username/video/1234567890"
        )

if __name__ == "__main__":
    app = ApplicationBuilder().token("8153645699:AAHW3gxKvyGNu7BikeLwguR3mQ5SUYO_Tic").build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, reply_message))
    print("Bot đang chạy...")
    app.run_polling()
