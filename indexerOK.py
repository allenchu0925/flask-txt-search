import sqlite3
import os

TXT_FOLDER_PATH = "./output_txt"
INDEX_DB_PATH = "txt_index.db"

def clear_existing_index():
    # 檢查資料庫檔案是否存在
    if os.path.exists(INDEX_DB_PATH):
        conn = sqlite3.connect(INDEX_DB_PATH)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM txt_index")
        conn.commit()
        conn.close()
        print("已清除索引資料！")
    else:
        print("索引資料庫不存在，跳過清除步驟")

def create_index():
    conn = sqlite3.connect(INDEX_DB_PATH)
    cursor = conn.cursor()

    # 建立表格（如果不存在）
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS txt_index (
            file_name TEXT,
            content TEXT
        )
    """)
    conn.commit()

    # 遍歷資料夾中的txt檔案
    for file in os.listdir(TXT_FOLDER_PATH):
        file_path = os.path.join(TXT_FOLDER_PATH, file)
        file_path = os.path.normpath(file_path)  # 修正路徑格式

        if file.endswith(".txt"):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    text = f.read()
                cursor.execute("INSERT INTO txt_index (file_name, content) VALUES (?, ?)", (file, text))
            except Exception as e:
                print(f"提取檔案 '{file}' 時出錯: {e}")

    conn.commit()
    conn.close()
    print("索引建立完成！")

if __name__ == "__main__":
    clear_existing_index()
    create_index()