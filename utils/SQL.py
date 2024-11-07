from main import __anilist_database__
import sqlite3

async def create_connection() -> sqlite3.Connection:
    """Creating Connection To Database"""
    return sqlite3.connect(__anilist_database__)

async def create_tables(server_id: str) -> None:
    """Creating Table"""
    conn = await create_connection()
    with conn:
        conn.execute(f'''CREATE TABLE IF NOT EXISTS s{server_id} (
                    channel_id INTEGER,
                    server_id INTEGER,
                    user_id INTEGER,
                    creation_timestamp TEXT,
                    animeData TEXT,
                    FOREIGN KEY (channel_id) REFERENCES servers (id))''')
    conn.close()

async def add_data(server_id, data) -> None:
    """Adding Data to Database: channel_id, server_id, user_id, creation_timestamp, animeData"""
    conn = await create_connection()
    sql = f'''INSERT INTO s{server_id} (channel_id, user_id, server_id, creation_timestamp, animeData) VALUES (?, ?, ?, ?, ?)'''
    with conn:
        conn.execute(sql, data)
    conn.close()

async def get_data(table) -> list:
    """Getting All Data from table"""
    try:
        conn = await create_connection()
        data = conn.cursor().execute(f"SELECT * FROM s{table}").fetchall()
        conn.close()
        return data
    except sqlite3.OperationalError:
        return []

async def get_all_data():
    try:
        connection = await create_connection()
        cursor = connection.cursor().execute(f"SELECT name FROM sqlite_master WHERE type='table'")
        database = cursor.fetchall()
        cursor.close()
        return database
    except sqlite3.OperationalError:
        return []

async def delete_data(server, id) -> None:
    """Delete Data"""
    conn = await create_connection()
    with conn:
        conn.execute(f'''DELETE FROM s{server} WHERE channel_id = ?''', (id,))
    conn.close()

async def update_data(table: int, name: str, key: int, new: str) -> None:
    """Update Data"""
    conn = await create_connection()
    conn.cursor().execute(f"UPDATE s{table} SET {name} = ? WHERE channel_id = ?", (new, key))
    conn.commit()
    conn.close()
