import os
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import sqlite3
import time
import re

app = Flask(__name__)
CORS(app)

# 定義版本號
VERSION = "v1.4.0"

TXT_FOLDER_PATH = "./output_txt"
INDEX_DB_PATH = "txt_index.db"
ADMIN_FOLDER_PATH = "./admin"

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
        input_text = data.get("input_text", "").strip().replace(" ", "").replace("\n", "")
        print(f"[SEARCH] [Version: {VERSION}] Search query: {input_text}")

        # 資料庫操作
        print(f"[SEARCH] [Version: {VERSION}] Connecting to database: {INDEX_DB_PATH}")
        conn = sqlite3.connect(INDEX_DB_PATH)
        conn.execute("PRAGMA journal_mode=WAL")
        cursor = conn.cursor()
        print(f"[SEARCH] [Version: {VERSION}] Executing search query...")
        cursor.execute("SELECT file_name, content FROM txt_index WHERE content LIKE ? COLLATE BINARY", ('%' + input_text + '%',))
        results = [{"file_name": row[0], "count": row[1].count(input_text)} for row in cursor.fetchall()]
        conn.close()

        # 按文件名中的數字部分進行數值排序
        def extract_number(filename):
            match = re.match(r'(\d+)_', filename)
            return int(match.group(1)) if match else float('inf')

        results.sort(key=lambda x: extract_number(x["file_name"]))

        elapsed_time = time.time() - start_time
        print(f"[SEARCH] [Version: {VERSION}] Search completed, found {len(results)} results in {elapsed_time:.2f} seconds")
        return jsonify(results)
    except Exception as e:
        elapsed_time = time.time() - start_time
        print(f"[SEARCH] [Version: {VERSION}] Error occurred: {e} after {elapsed_time:.2f} seconds")
        return jsonify({"error": "搜尋過程中發生錯誤"}), 500

@app.route('/txt/<filename>', methods=['GET'])
def get_txt_content(filename):
    start_time = time.time()  # 記錄開始時間
    try:
        print(f"[TXT CONTENT] [Version: {VERSION}] Received request for file: {filename}")
        file_path = os.path.join(TXT_FOLDER_PATH, filename)
        file_path = os.path.normpath(file_path)
        print(f"[TXT CONTENT] [Version: {VERSION}] File path: {file_path}")

        if not os.path.exists(file_path):
            elapsed_time = time.time() - start_time
            print(f"[TXT CONTENT] [Version: {VERSION}] File not found: {file_path} after {elapsed_time:.2f} seconds")
            return jsonify({"error": f"檔案 {filename} 不存在"}), 404

        with open(file_path, 'r', encoding='utf-8') as file:
            text = file.read()

        elapsed_time = time.time() - start_time
        print(f"[TXT CONTENT] [Version: {VERSION}] Successfully read file (length: {len(text)} characters) in {elapsed_time:.2f} seconds")
        return jsonify({"content": text.replace("\n", "<br>")})
    except Exception as e:
        elapsed_time = time.time() - start_time
        print(f"[TXT CONTENT] [Version: {VERSION}] Error reading file '{filename}': {e} after {elapsed_time:.2f} seconds")
        return jsonify({"error": f"無法讀取檔案 {filename}"}), 500

@app.route('/list-files', methods=['GET'])
def list_files():
    start_time = time.time()
    try:
        print(f"[LIST-FILES] [Version: {VERSION}] Listing files and folders")
        
        # 列出根目錄下的檔案和資料夾
        root_files = os.listdir('.')
        print(f"[LIST-FILES] [Version: {VERSION}] Root directory contents: {root_files}")
        
        # 列出 ./output_txt 資料夾的內容（如果存在）
        output_txt_contents = []
        if os.path.exists(TXT_FOLDER_PATH):
            output_txt_contents = os.listdir(TXT_FOLDER_PATH)
            print(f"[LIST-FILES] [Version: {VERSION}] {TXT_FOLDER_PATH} contents: {output_txt_contents}")
        else:
            print(f"[LIST-FILES] [Version: {VERSION}] {TXT_FOLDER_PATH} does not exist")
        
        # 檢查資料庫檔案是否存在
        db_exists = os.path.exists(INDEX_DB_PATH)
        print(f"[LIST-FILES] [Version: {VERSION}] Database file {INDEX_DB_PATH} exists: {db_exists}")
        
        elapsed_time = time.time() - start_time
        print(f"[LIST-FILES] [Version: {VERSION}] File listing completed in {elapsed_time:.2f} seconds")
        return jsonify({
            "root_files": root_files,
            "output_txt_contents": output_txt_contents,
            "database_exists": db_exists
        })
    except Exception as e:
        elapsed_time = time.time() - start_time
        print(f"[LIST-FILES] [Version: {VERSION}] Error listing files: {e} after {elapsed_time:.2f} seconds")
        return jsonify({"error": "無法列出檔案"}), 500

@app.route('/upload', methods=['POST'])
def upload_file():
    start_time = time.time()
    try:
        print(f"[UPLOAD] [Version: {VERSION}] Received upload request")
        
        # 檢查密碼
        password = request.form.get('password')
        ADMIN_PASSWORD = "your_secure_password"  # 請替換為你的實際密碼
        if password != ADMIN_PASSWORD:
            elapsed_time = time.time() - start_time
            print(f"[UPLOAD] [Version: {VERSION}] Invalid password attempt after {elapsed_time:.2f} seconds")
            return jsonify({"error": "密碼錯誤"}), 403

        # 檢查檔案
        if 'file' not in request.files:
            elapsed_time = time.time() - start_time
            print(f"[UPLOAD] [Version: {VERSION}] No file part in request after {elapsed_time:.2f} seconds")
            return jsonify({"error": "沒有選擇檔案"}), 400

        file = request.files['file']
        if file.filename == '':
            elapsed_time = time.time() - start_time
            print(f"[UPLOAD] [Version: {VERSION}] No selected file after {elapsed_time:.2f} seconds")
            return jsonify({"error": "沒有選擇檔案"}), 400

        # 儲存檔案
        if not os.path.exists(TXT_FOLDER_PATH):
            os.makedirs(TXT_FOLDER_PATH)
            print(f"[UPLOAD] [Version: {VERSION}] Created directory: {TXT_FOLDER_PATH}")

        file_path = os.path.join(TXT_FOLDER_PATH, file.filename)
        file.save(file_path)
        print(f"[UPLOAD] [Version: {VERSION}] File saved: {file_path}")

        # 讀取檔案內容並更新資料庫
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        conn = sqlite3.connect(INDEX_DB_PATH)
        conn.execute("PRAGMA journal_mode=WAL")
        cursor = conn.cursor()
        cursor.execute("INSERT OR REPLACE INTO txt_index (file_name, content) VALUES (?, ?)", (file.filename, content))
        conn.commit()
        conn.close()
        print(f"[UPLOAD] [Version: {VERSION}] Database updated for file: {file.filename}")

        elapsed_time = time.time() - start_time
        print(f"[UPLOAD] [Version: {VERSION}] File {file.filename} uploaded and indexed successfully in {elapsed_time:.2f} seconds")
        return jsonify({"message": f"檔案 {file.filename} 上傳成功並已更新資料庫"})
    except Exception as e:
        elapsed_time = time.time() - start_time
        print(f"[UPLOAD] [Version: {VERSION}] Error during upload: {e} after {elapsed_time:.2f} seconds")
        return jsonify({"error": "上傳過程中發生錯誤"}), 500

# 新增路由以提供 admin 資料夾中的靜態檔案
@app.route('/admin/<path:filename>')
def serve_admin_files(filename):
    try:
        print(f"[ADMIN FILE] [Version: {VERSION}] Serving file: {filename}")
        return send_from_directory(ADMIN_FOLDER_PATH, filename)
    except Exception as e:
        print(f"[ADMIN FILE] [Version: {VERSION}] Error serving file '{filename}': {e}")
        return jsonify({"error": f"無法提供檔案 {filename}"}), 404

# 新增路由以刪除檔案
@app.route('/delete', methods=['POST'])
def delete_file():
    start_time = time.time()
    try:
        print(f"[DELETE] [Version: {VERSION}] Received delete request")
        
        # 檢查密碼
        data = request.json
        password = data.get('password')
        ADMIN_PASSWORD = "your_secure_password"  # 請替換為你的實際密碼
        if password != ADMIN_PASSWORD:
            elapsed_time = time.time() - start_time
            print(f"[DELETE] [Version: {VERSION}] Invalid password attempt after {elapsed_time:.2f} seconds")
            return jsonify({"error": "密碼錯誤"}), 403

        # 檢查檔案名稱
        filename = data.get('filename')
        if not filename:
            elapsed_time = time.time() - start_time
            print(f"[DELETE] [Version: {VERSION}] No filename provided after {elapsed_time:.2f} seconds")
            return jsonify({"error": "未提供檔案名稱"}), 400

        # 檢查檔案是否存在
        file_path = os.path.join(TXT_FOLDER_PATH, filename)
        file_path = os.path.normpath(file_path)
        if not os.path.exists(file_path):
            elapsed_time = time.time() - start_time
            print(f"[DELETE] [Version: {VERSION}] File not found: {file_path} after {elapsed_time:.2f} seconds")
            return jsonify({"error": f"檔案 {filename} 不存在"}), 404

        # 從檔案系統中刪除檔案
        os.remove(file_path)
        print(f"[DELETE] [Version: {VERSION}] File deleted from filesystem: {file_path}")

        # 從資料庫中刪除索引
        conn = sqlite3.connect(INDEX_DB_PATH)
        conn.execute("PRAGMA journal_mode=WAL")
        cursor = conn.cursor()
        cursor.execute("DELETE FROM txt_index WHERE file_name = ?", (filename,))
        conn.commit()
        conn.close()
        print(f"[DELETE] [Version: {VERSION}] Database record deleted for file: {filename}")

        elapsed_time = time.time() - start_time
        print(f"[DELETE] [Version: {VERSION}] File {filename} deleted successfully in {elapsed_time:.2f} seconds")
        return jsonify({"message": f"檔案 {filename} 已成功刪除"})
    except Exception as e:
        elapsed_time = time.time() - start_time
        print(f"[DELETE] [Version: {VERSION}] Error during deletion: {e} after {elapsed_time:.2f} seconds")
        return jsonify({"error": "刪除過程中發生錯誤"}), 500

if __name__ == "__main__":
    port = int(os.getenv('PORT', 8000))
    print(f"[START] [Version: {VERSION}] Server running on port {port}")
    app.run(host='0.0.0.0', port=port)