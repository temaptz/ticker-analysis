import os
from dotenv import load_dotenv

load_dotenv()  # env нужен до чтения секретов ниже

DB_FILENAME = 'db.sqlite'
DB_HOST = os.getenv('DB_HOST', 'postgres')
DB_NAME = os.getenv('POSTGRES_DB', 'main_db')
DB_USERNAME = os.getenv('POSTGRES_USER', 'main_db_user')
DB_PASSWORD = os.getenv('POSTGRES_PASSWORD', 'main_db_password')
TINKOFF_INVEST_TOKEN = os.getenv('TINKOFF_INVEST_TOKEN', '')
TELEGRAM_BOT_API_KEY = os.getenv('TELEGRAM_BOT_API_KEY', '')
TELEGRAM_CHAT_IDS: list[int] = [
    int(chat_id) for chat_id in os.getenv('TELEGRAM_CHAT_IDS', '').split(',') if chat_id.strip()
]
Y_DISK_TOKEN = os.getenv('Y_DISK_TOKEN', '')
Y_API_KEY_ID = os.getenv('Y_API_KEY_ID', '')
Y_API_SECRET = os.getenv('Y_API_SECRET', '')
Y_API_FOLDER_ID = os.getenv('Y_API_FOLDER_ID', '')
TICKER_LIST: list[str] = [
    'OZON',
    'SBER',
    'SBERP',
    'MGNT',
    'RTKM',
    'NVTK',
    'LKOH',
    'GAZP',
    'X5',
    'YDEX',
    'FIXP',
    'MTLR',
    'MTLRP',
    'ALRS',
    'MVID',
    'QIWI',
    'RASP',
    'FLOT',
    'CHMF',
    'SNGSP',
    'MTSS',
    'AFLT',
    'VTBR',
    'GMKN',
    'PHOR',
    'HEAD',
    'RTKMP',
    'CNRU',
    'NLMK',
    'ENPG',
    'AKRN',
    'VSMO',
    'ROLO',
    'SIBN',
    'MAGN',
    'ROSN',
    'AGRO',
    'RUAL',
    'SGZH',
    'TATNP',
    'SELG',
    'UGLD',
    'RNFT',
    'SVCB',
    'NMTP',
    'GCHE',
    'NKHP',
    'BELU',
    'TRMK',
    'ETLN',
    'OKEY',
    'LSNG',
    'MSNG',
    'GTRK',
    'SFIN',
    'FESH',
    'UWGN',
    'EUTR',
    'LEAS',
    'WUSH',
    'UNAC',
    'KMAZ',
    'SVAV',
    'DELI',
    'BLNG',
    'MSTT',
    'KROT',
    'RKKE',
    'AFKS',
    'IRAO',
    'VKCO',
    'MDMG',
    'LNZL',
    'LNZLP',
    'ABIO',
    'ASTR',
    'PLZL',
]
IS_NEWS_CLASSIFY_ENABLED = False
