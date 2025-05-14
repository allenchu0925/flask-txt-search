from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import os
import re

app = Flask(__name__)
CORS(app)

TXT_FOLDER_PATH = "C:/GSPDF/output_txt"
INDEX_DB_PATH = "txt_index.db"

@app.route('/search', methods=['POST'])
def search():
    try:
        data = request.json
        input_text = data.get("input_text", "").strip().replace(" ", "").replace("\n", "")
        print(f"[SEARCH] 收到的搜尋字串: {input_text}")

        conn = sqlite3.connect(INDEX_DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT file_name, content FROM txt_index WHERE content LIKE ? COLLATE BINARY", ('%' + input_text + '%',))
        results = [{"file_name": row[0], "count": row[1].count(input_text)} for row in cursor.fetchall()]
        conn.close()

        # 按文件名中的數字部分進行數值排序
        def extract_number(filename):
            match = re.match(r'(\d+)_', filename)
            return int(match.group(1)) if match else float('inf')

        results.sort(key=lambda x: extract_number(x["file_name"]))

        print(f"[SEARCH] 搜尋完成，共找到 {len(results)} 個相關結果")
        return jsonify(results)
    except Exception as e:
        print(f"[SEARCH] 發生錯誤: {e}")
        return jsonify({"error": "搜尋過程中發生錯誤"}), 500

@app.route('/txt/<filename>', methods=['GET'])
def get_txt_content(filename):
    try:
        file_path = os.path.join(TXT_FOLDER_PATH, filename)
        file_path = os.path.normpath(file_path)  # 修正路徑格式

        if not os.path.exists(file_path):
            print(f"[TXT CONTENT] 檔案不存在: {file_path}")
            return jsonify({"error": f"檔案 {filename} 不存在"}), 404

        with open(file_path, 'r', encoding='utf-8') as file:
            text = file.read()

        print(f"[TXT CONTENT] 成功提取檔案內容（長度: {len(text)} 字元）")
        return jsonify({"content": text.replace("\n", "<br>")})
    except Exception as e:
        print(f"[TXT CONTENT] 讀取檔案 '{filename}' 時出錯: {e}")
        return jsonify({"error": f"無法讀取檔案 {filename}"}), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)