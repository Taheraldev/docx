import logging
import os
import requests
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

# إعداد السجل (logging)
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

# ضع هنا توكن البوت الخاص بك
TELEGRAM_TOKEN = '5146976580:AAE2yXc-JK6MIHVlLDy-O4YODucS_u7Zq-8'
# المفتاح السري لـ ConvertAPI
CONVERT_API_SECRET = "secret_q4ijKpkWw17sLQx8"
# رابط ConvertAPI لتحويل PDF إلى DOCX
CONVERT_API_URL = "https://v2.convertapi.com/convert/pdf/to/docx"

def start(update: Update, context: CallbackContext):
    update.message.reply_text("مرحباً! أرسل لي ملف PDF وسأقوم بتحويله إلى DOCX.")

def pdf_handler(update: Update, context: CallbackContext):
    document = update.message.document
    if not document or not document.file_name.lower().endswith('.pdf'):
        update.message.reply_text("❌ يرجى إرسال ملف بصيغة PDF فقط.")
        return
    
    # تحميل ملف PDF
    file_obj = context.bot.getFile(document.file_id)
    pdf_path = file_obj.download()
    update.message.reply_text("⏳ جارٍ تحويل الملف...")

    try:
        # استخدام ConvertAPI لتحويل PDF إلى DOCX
        with open(pdf_path, 'rb') as f:
            files = {'File': f}
            params = {'Secret': CONVERT_API_SECRET}
            response = requests.post(CONVERT_API_URL, params=params, files=files)

        # طباعة الاستجابة لفهم بنيتها عند حدوث خطأ
        result = response.json()
        print("استجابة ConvertAPI:", result)

        # التأكد من وجود البيانات الصحيحة في الاستجابة
        file_info = result.get('Files', [])
        if file_info and isinstance(file_info, list) and 'Url' in file_info[0]:
            file_url = file_info[0]['Url']

            # تحميل الملف المحول (DOCX)
            docx_response = requests.get(file_url)
            docx_path = pdf_path.replace('.pdf', '.docx')
            with open(docx_path, 'wb') as docx_file:
                docx_file.write(docx_response.content)

            # إرسال الملف المحول للمستخدم
            context.bot.send_document(chat_id=update.message.chat_id, document=open(docx_path, 'rb'))
            
            # حذف الملفات المؤقتة
            os.remove(pdf_path)
            os.remove(docx_path)
        else:
            update.message.reply_text("⚠️ حدث خطأ أثناء التحويل، لم يتم العثور على رابط الملف المحول.")

    except Exception as e:
        logger.error("❌ Error during conversion: %s", e)
        update.message.reply_text("❌ حدث خطأ أثناء عملية التحويل، يرجى المحاولة لاحقاً.")

def main():
    updater = Updater(TELEGRAM_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.document, pdf_handler))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
