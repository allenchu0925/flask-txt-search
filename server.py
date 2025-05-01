from flask import Flask, request, jsonify
import sqlite3
import os

app = Flask(__name__)

# 簡單的密碼（實際應用中應使用更安全的認證方式，例如 JWT）
ADMIN_PASSWORD = "your_secure_password"  # 請自行設定密碼

# 確保 output_txt 目錄存在
if not os.path.exists('output_txt'):
    os.makedirs('output_txt')

@app.route('/')
def home():
    return "Welcome to Flask Text Search! Use /search to search for text or /txt/<filename> to view a file."

@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('q', '')
    conn = sqlite3.connect('txt_index.db')
    cursor = conn.cursor()
    cursor.execute("SELECT filename FROM txt_index WHERE content LIKE ?", ('%' + query + '%',))
    results = cursor.fetchall()
    conn.close()
    return jsonify({'results': [row[0] for row in results]})

@app.route('/txt/<filename>')
def get_file(filename):
    file_path = os.path.join('output_txt', filename)
    if not os.path.exists(file_path):
        return jsonify({'error': 'File not found'}), 404
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()

@app.route('/upload', methods=['POST'])
def upload_file():
    # 檢查密碼
    password = request.form.get('password')
    if password != ADMIN_PASSWORD:
        return jsonify({'message': '密碼錯誤'}), 403

    # 檢查是否有檔案
    if 'file' not in request.files:
        return jsonify({'message': '未選擇檔案'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'message': '未選擇檔案'}), 400
    if not file.filename.endswith('.txt'):
        return jsonify({'message': '僅支援 TXT 檔案'}), 400

    # 儲存檔案
    filename = file.filename
    file_path = os.path.join('output_txt', filename)
    if os.path.exists(file_path):
        return jsonify({'message': '檔案已存在，請選擇其他檔案'}), 409
    file.save(file_path)

    # 讀取檔案內容
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 更新資料庫
    try:
        conn = sqlite3.connect('txt_index.db')
        cursor = conn.cursor()
        cursor.execute("INSERT INTO txt_index (filename, content) VALUES (?, ?)", (filename, content))
        conn.commit()
    except sqlite3.Error as e:
        conn.rollback()
        return jsonify({'message': f'資料庫更新失敗：{str(e)}'}), 500
    finally:
        conn.close()

    return jsonify({'message': f'檔案 {filename} 上傳成功並已更新資料庫'}), 200

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)