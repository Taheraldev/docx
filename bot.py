import os
import tempfile
from functools import partial
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler, CallbackContext
from PyPDF2 import PdfReader, PdfWriter
from pdf2image import convert_from_path
import pytesseract

# Configure your Telegram bot token
TOKEN = '6334414905:AAFK59exfc4HuQQJdxk-mwONn5K4yODCIJg'

# Constants for callback data
OPTIONS = [
    ('encrypt', 'تشفير الملف'),
    ('decrypt', 'فك التشفير'),
    ('merge', 'دمج ملفات'),
    ('split', 'تقسيم الملف'),
    ('rename', 'إعادة تسمية'),
    ('to_images', 'تحويل إلى صور'),
    ('to_text', 'تحويل إلى نص'),
    ('compress', 'ضغط الملف'),
    ('rotate', 'تدوير الملف'),
    ('ocr', 'إضافة OCR'),
    ('add_pages', 'إضافة صفحات'),
    ('del_pages', 'حذف الصفحات'),
    ('format', 'تنسيق ملف'),
    ('zoom', 'تكبير'),
    ('segment', 'تجزئة الملف'),
    ('number', 'إضافة رقم الصفحات'),
]

# Store user-uploaded PDF path in context.user_data

def start(update: Update, context: CallbackContext):
    update.message.reply_text('أرسل لي ملف PDF لأقوم بالعمليات التالية عليه:')


def show_options(update: Update, context: CallbackContext):
    file = update.message.document
    if not file.file_name.lower().endswith('.pdf'):
        update.message.reply_text('الرجاء إرسال ملف PDF فقط.')
        return

    # download PDF
    tmp_fd, tmp_path = tempfile.mkstemp(suffix='.pdf')
    os.close(tmp_fd)
    file.get_file().download(custom_path=tmp_path)
    context.user_data['pdf_path'] = tmp_path

    # build inline keyboard
    keyboard = [[InlineKeyboardButton(label, callback_data=key)] for key, label in OPTIONS]
    markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text('اختر العملية التي تريد تنفيذها:', reply_markup=markup)


def parse_ranges(s: str):
    pages = set()
    for part in s.split(','):
        if ':' in part:
            start, end = part.split(':')
            pages.update(range(int(start)-1, int(end)))
        else:
            pages.add(int(part)-1)
    return sorted(pages)


def callback_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    data = query.data
    pdf_path = context.user_data.get('pdf_path')
    query.answer()

    if data == 'split':
        query.edit_message_text('أرسلَ صفحات التقسيم (مثال: 1:12,33:44,48)')
        context.user_data['next'] = 'split'
    elif data == 'to_images':
        keyboard = [
            [InlineKeyboardButton('استخراج كل الصور', callback_data='images_all')],
            [InlineKeyboardButton('تحديد صفحات', callback_data='images_sel')],
        ]
        query.edit_message_text('اختر:', reply_markup=InlineKeyboardMarkup(keyboard))
    elif data.startswith('images_'):
        choice = data.split('_')[1]
        if choice == 'all':
            images = convert_from_path(pdf_path)
            media = []
            for img in images:
                fname = tempfile.mktemp(suffix='.jpg')
                img.save(fname, 'JPEG')
                media.append(InputMediaPhoto(open(fname, 'rb')))
            for i in range(0, len(media), 10):
                update.effective_chat.send_media_group(media[i:i+10])
        else:
            query.edit_message_text('أرسل صفحات التحويل للصور (مثال: 1:3,5)')
            context.user_data['next'] = 'images_sel'
    elif data == 'to_text':
        keyboard = [[InlineKeyboardButton(n, callback_data=f'text_{n}')] for n in ['message', 'txt', 'html', 'json']]
        query.edit_message_text('اختر تنسيق النص:', reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        query.edit_message_text(f'الخيار {data} غير مفعل حاليًا.')


def text_message_handler(update: Update, context: CallbackContext):
    step = context.user_data.get('next')
    pdf_path = context.user_data.get('pdf_path')
    txt = update.message.text.strip()

    if step == 'split':
        pages = parse_ranges(txt)
        reader = PdfReader(pdf_path)
        writer = PdfWriter()
        for p in pages:
            writer.add_page(reader.pages[p])
        out = tempfile.mktemp(suffix='.pdf')
        with open(out, 'wb') as f:
            writer.write(f)
        update.message.reply_document(open(out, 'rb'))
    elif step == 'images_sel':
        pages = parse_ranges(txt)
        images = convert_from_path(pdf_path, first_page=pages[0]+1, last_page=pages[-1]+1)
        media = []
        for img in images:
            fname = tempfile.mktemp(suffix='.jpg')
            img.save(fname, 'JPEG')
            media.append(InputMediaPhoto(open(fname, 'rb')))
        for i in range(0, len(media), 10):
            update.effective_chat.send_media_group(media[i:i+10])
    else:
        update.message.reply_text('يرجى اختيار ملف PDF أولًا.')

    context.user_data.clear()


def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler('start', start))
    dp.add_handler(MessageHandler(Filters.document.pdf, show_options))
    dp.add_handler(CallbackQueryHandler(callback_handler))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, text_message_handler))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
