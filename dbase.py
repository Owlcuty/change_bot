import sqlite3
from sqlite3 import Error


def my_create_connection(file_name):
    conn = None;
    try:
        conn = sqlite3.connect(file_name)
        print(sqlite3.version)
    except Error as err:
        print("conncreate_connection:: ", err)

    return conn

def my_create_table(conn, create_table_sql):
    assert conn

    try:
        cursor = conn.cursor()
        cursor.execute(create_table_sql)
    except Error as err:
        print("create_table:: ", err)

def my_insert_into(conn, table_name, params_str, num_params, values_list):

    sql = f''' INSERT OR REPLACE INTO  {table_name}({params_str})

            VALUES({"?," * (num_params - 1) + "?"});
    '''
    cursor = conn.cursor()
    cursor.executemany(sql, values_list)
    conn.commit()

    return cursor.lastrowid

def my_drop_table(conn, table_name):

    cursor = conn.cursor()
    conn.execute(f'''DROP TABLE IF EXISTS {table_name}''')

def my_get_data(conn, table_name):

    cursor = conn.cursor()
    cursor.execute(f'''SELECT * FROM {table_name}''')
    return cursor.fetchall()
