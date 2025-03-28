import datetime
import sqlite3
import const
from lib.utils import get_file_abspath_recursive
from lib import types, utils

table_name = 'News'
table_name_fts = 'News_fts'


def init_tables():
    connection = sqlite3.connect(get_file_abspath_recursive(const.DB_FILENAME))
    cursor = connection.cursor()

    cursor.execute(f'''
    CREATE TABLE IF NOT EXISTS 
    '{table_name}' 
    (
    'uid' TEXT PRIMARY KEY,
    'date' TIMESTAMP,
    'source_name' TEXT
    )
    ''')

    cursor.execute(f'''
    CREATE VIRTUAL TABLE IF NOT EXISTS 
    '{table_name_fts}' USING fts5 
    (
    'uid',
    'title',
    'text'
    )
    ''')

    connection.commit()
    connection.close()


def get_news():
    connection = sqlite3.connect(get_file_abspath_recursive(const.DB_FILENAME))
    cursor = connection.cursor()
    cursor.execute(f'''
    SELECT 
    N.*, 
    F.title, 
    F.text
    FROM {table_name} N
    JOIN {table_name_fts} F ON N.uid = F.uid;
    ''')
    news = cursor.fetchall()
    connection.close()

    return news


def get_news_by_uid(uid: str):
    connection = sqlite3.connect(get_file_abspath_recursive(const.DB_FILENAME))
    cursor = connection.cursor()
    query = f'''
    SELECT 
    N.*, 
    F.title, 
    F.text
    FROM {table_name} N
    JOIN {table_name_fts} F ON N.uid = F.uid
    WHERE N.uid = ?;
    '''

    cursor.execute(query, (uid,))
    news = cursor.fetchall()
    connection.close()

    return news


def get_news_by_date_keywords_fts(
        start_date: datetime.datetime,
        end_date: datetime.datetime,
        keywords: list[str]
):
    # Подключаемся к базе данных
    conn = sqlite3.connect(get_file_abspath_recursive(const.DB_FILENAME))
    cursor = conn.cursor()

    # # Форматируем даты в строковый формат
    start_date = start_date.strftime('%Y-%m-%d 00:00:00')
    end_date = end_date.strftime('%Y-%m-%d 23:59:59')

    # Строим полнотекстовый поиск с ключевыми словами
    keywords_query = ' OR '.join(keywords)

    # Запрос с фильтрацией по датам и полнотекстовым поиском
    query = f'''
        SELECT N.uid, F.title, F.text, N.date, N.source_name
        FROM {table_name} N
        JOIN {table_name_fts} F ON N.uid = F.uid
        WHERE N.date BETWEEN ? AND ? 
        AND News_fts MATCH ?;
    '''
    query_params = (start_date, end_date, keywords_query)

    # Выполняем запрос с параметрами
    cursor.execute(query, query_params)
    results = cursor.fetchall()

    # Закрываем соединение
    conn.close()

    # Возвращаем результаты
    return results


def insert_news_batch(records: list[types.NewsDbRecord]):
    connection = sqlite3.connect(get_file_abspath_recursive(const.DB_FILENAME))
    cursor = connection.cursor()

    cursor.execute('BEGIN TRANSACTION;')

    for i in records:
        cursor.execute(
            f'INSERT OR REPLACE INTO {table_name} (uid, date, source_name) VALUES (?, ?, ?);',
            (i.uid, i.date, i.source_name)
        )
        cursor.execute(
            f'INSERT OR REPLACE INTO {table_name_fts} (uid, title, text) VALUES (?, ?, ?);',
            (i.uid, i.title, i.text)
        )

    cursor.execute('COMMIT;')

    connection.commit()
    connection.close()


# def insert_news_batch(news: list):
#     connection = sqlite3.connect(get_file_abspath_recursive(const.DB_FILENAME))
#     cursor = connection.cursor()
#
#     cursor.execute('BEGIN TRANSACTION;')
#
#     for i in news:
#         uid = i[0]
#         title = i[1]
#         text = i[2]
#         date = i[3]
#         source_name = i[4]
#
#         cursor.execute(
#             f'INSERT INTO {table_name} (uid, date, source_name) VALUES (?, ?, ?);',
#             (uid, date, source_name)
#         )
#         cursor.execute(
#             f'INSERT INTO {table_name_fts} (uid, title, text) VALUES (?, ?, ?);',
#             (uid, title, text)
#         )
#
#     cursor.execute('COMMIT;')
#
#     connection.commit()
#     connection.close()


def list_list():
    print('LIST')

    news = get_news()

    print(len(news))


# def get_news_legacy():
#     connection = sqlite3.connect(get_file_abspath_recursive(const.DB_FILENAME))
#     cursor = connection.cursor()
#     cursor.execute(f'''SELECT * FROM News_legacy''')
#     news = cursor.fetchall()
#     connection.close()
#
#     return news


# def move_table():
#     optimize_db()
#
#     insert_batch = list()
#     legacy_news = get_news_legacy()
#     legacy_news_len = len(legacy_news)
#
#     for i in legacy_news:
#         uid = i[0]
#         title = i[1]
#         text = i[2]
#         date = i[3]
#         source_name = i[4]
#
#         insert_batch.append([uid, title, text, date, source_name])
#
#     print('WILL INSERT', len(insert_batch))
#
#     insert_news_batch(insert_batch)
#
#     # rebuild_index_fts()


# def get_news_with_links():
#     connection = sqlite3.connect(get_file_abspath_recursive(const.DB_FILENAME))
#     cursor = connection.cursor()
#     query = f'''
#     SELECT
#     N.*,
#     F.title,
#     F.text
#     FROM {table_name} N
#     JOIN {table_name_fts} F ON N.uid = F.uid
#     WHERE N.uid LIKE '%http%';
#     '''
#
#     cursor.execute(query)
#     news = cursor.fetchall()
#     connection.close()
#
#     return news


# def update_uid(currentUid: str, nextUid: str):
#     """Обновляет uid в двух таблицах (обычной и FTS)"""
#     connection = sqlite3.connect(get_file_abspath_recursive(const.DB_FILENAME))
#     cursor = connection.cursor()
#
#     # Обновляем в основной таблице
#     cursor.execute(f"UPDATE '{table_name}' SET uid = ? WHERE uid = ?", (nextUid, currentUid))
#     # Обновляем в FTS-таблице
#     cursor.execute(f"UPDATE '{table_name_fts}' SET uid = ? WHERE uid = ?", (nextUid, currentUid))
#
#     connection.commit()
#     connection.close()
#
#
# def replace_md5():
#     print('MOVE MD5')
#
#     news = get_news()
#
#     counter = 0
#
#     for i in news:
#         if 'http' in i[0]:
#             currentUid = i[0]
#             nextUid = utils.get_md5(i[0])
#             print(nextUid, currentUid)
#             update_uid(currentUid=currentUid, nextUid=nextUid)
#             counter += 1
#             print('UPDATED', counter)
#
#     print('NEWS COUNT', counter, ' / ', len(news))
