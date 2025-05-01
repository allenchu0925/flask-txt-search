import os
from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import time

app = Flask(__name__)
CORS(app)

# 定義版本號
VERSION = "v1.1.0"

TXT_FOLDER_PATH = "./output_txt"
INDEX_DB_PATH = "txt_index.db"

# 啟動時記錄版本號和服務資訊
print(f"[START] Flask Text Search Server {VERSION} starting...")

# 新增根路由
@app.route('/')
def home():
    print(f"[HOME] [Version: {VERSION}] Received request for root route")
    return "Welcome to Flask Text Search! Use /search to search for text or /txt/<filename> to view a file."

@app.route('/search', methods=['POST'])
def search():
    start_time = time.time()  # 記錄開始時間
    try:
        print(f"[SEARCH] [Version: {VERSION}] Received search request")
        data = request.json
        input_text = data.get("input_text", "")
        print(f"[SEARCH] [Version: {VERSION}] Search query: {input_text}")

        # 資料庫操作
        print(f"[SEARCH] [Version: {VERSION}] Connecting to database: {INDEX_DB_PATH}")
        conn = sqlite3.connect(INDEX_DB_PATH)
        conn.execute("PRAGMA journal_mode=WAL")
        cursor = conn.cursor()
        print(f"[SEARCH] [Version: {VERSION}] Executing search query...")
        cursor.execute("SELECT file_name, content FROM txt_index WHERE content MATCH ?", (input_text,))
        results = [{"file_name": row[0], "count": row[1].count(input_text)} for row in cursor.fetchall()]
        conn.close()

        elapsed_time = time.time() - start_time
        print(f"[SEARCH] [Version: {VERSION}] Search completed, found {len(results)} results in {elapsed_time:.2f} seconds")
        return jsonify(results)
    except Exception as e:
        elapsed_time = time.time() - start_time
        print(f"[SEARCH] [Version: {VERSION}] Error occurred: {e} after {elapsed_time:.2f} seconds")
        return jsonify({"error": "搜尋過程中發生錯誤"}), 500

@app.route('/txt/<filename>', methods