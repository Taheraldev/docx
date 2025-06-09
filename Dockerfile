# استخدم صورة بايثون الرسمية
FROM python:3.10-slim

# تثبيت tesseract OCR و poppler-utils لتحويل PDF إلى صورة
RUN apt-get update && \
    apt-get install -y tesseract-ocr poppler-utils && \
    rm -rf /var/lib/apt/lists/*

# أنشئ مجلّد العمل
WORKDIR /app

# انسخ ملفات المشروع وثبّت المتطلبات
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY bot.py .

# ضع التوكن كمتغيّر بيئي
ENV TOKEN="6334414905:AAFK59exfc4HuQQJdxk-mwONn5K4yODCIJg"

# شغّل البوت
CMD ["python", "bot.py"]
