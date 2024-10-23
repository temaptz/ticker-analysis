from tinkoff.invest.schemas import Quotation
from const import DB_PATH
import os


def get_db_path(db_path: str) -> str:
    root_directory = os.path.abspath('../')
    return root_directory+'/'+os.path.basename(db_path)
