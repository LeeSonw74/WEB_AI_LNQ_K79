from flask import Flask, render_template, request, jsonify, session
import google.generativeai as genai
import sqlite3
import markdown
import uuid

app = Flask(__name__)
app.secret_key = 'chimtokhonglochetdoi'

# Hard-code API keys
api_keys = [
    "AIzaSyCPUEoGr6GsEo6TkBT-dg9E0PJUJcm5JqE"
]

# Cấu hình model theo key
def key_model(api_key):
    genai.configure(api_key=api_key)
    return genai.GenerativeModel(model_name="gemini-1.5-flash")

# Thay key tự độngđộng
def get_response(prompt):
    for key in api_keys:
        if not key:
            response = "API key rỗng hoặc không được cấu hình"
            continue
        try:
            model = key_model(key)
            response = model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            print(f"Lỗi với API key {key[:10]}...: {str(e)}")
            continue
    return "Tất cả API key đã hết hạn hoặc lỗi. Vui lòng thử lại sau."

# Khởi tạo cơ sở dữ liệu
def init_db():
    try:
        with sqlite3.connect("chat_history.db") as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS chat_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT,
                    user_input TEXT NOT NULL,
                    bot_response TEXT NOT NULL
                )
            ''')
            conn.commit()
            print("Cơ sở dữ liệu được khởi tạo thành công.")
    except sqlite3.Error as e:
        print(f"Lỗi khởi tạo cơ sở dữ liệu: {e}")

# Lấy lịch sử theo session
def get_chat_history(limit=5):
    session_id = session.get("session_id")
    if not session_id:
        print("Không tìm thấy session_id.")
        return []
    try:
        with sqlite3.connect("chat_history.db") as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT user_input, bot_response FROM chat_history WHERE session_id = ? ORDER BY id DESC LIMIT ?", (session_id, limit))
            return cursor.fetchall()[::-1]
    except sqlite3.Error as e:
        print(f"Lỗi truy vấn cơ sở dữ liệu: {e}")
        return []

# Xử lý tin nhắn
def process_message(user_input):
    try:
        prompt = f"Trả lời: {user_input}"
        text = get_response(prompt)
        if text.startswith("Lỗi:") or text == "Tất cả API key đã hết hạn hoặc lỗi. Vui lòng thử lại sau.":
            return text

        cleaned_text = "\n".join(line.strip() for line in text.splitlines() if line.strip())
        bot_response = markdown.markdown(cleaned_text)

        session_id = session.get("session_id")
        if not session_id:
            session_id = str(uuid.uuid4())
            session["session_id"] = session_id

        with sqlite3.connect("chat_history.db") as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO chat_history (user_input, bot_response, session_id) VALUES (?, ?, ?)",
                (user_input, bot_response, session_id)
            )
            conn.commit()

        return bot_response
    except Exception as e:
        return f"Lỗi xử lý: {str(e)}"

# Trang chính
@app.route("/", methods=["GET", "POST"])
def index():
    user_input = ""
    bot_response = ""
    history = get_chat_history()

    if request.method == "POST":
        user_input = request.form.get("input", "").strip()
        if user_input:
            bot_response = process_message(user_input)
            history = get_chat_history()
        else:
            bot_response = "Vui lòng nhập câu hỏi."

    return render_template("index.html", user_input=user_input, bot_response=bot_response, history=history)

# Trang /chat
@app.route("/chat", methods=["GET", "POST"])
def chat():
    user_input = ""
    bot_response = ""
    history = get_chat_history()
    if request.method == "POST":
        user_input = request.form.get("input", "").strip()
        if user_input:
            bot_response = process_message(user_input)
            history = get_chat_history()
        else:
            bot_response = "Vui lòng nhập câu hỏi."
    return render_template("chat.html", user_input=user_input, bot_response=bot_response, history=history)

# Xem lịch sử hiện tại
@app.route("/history")
def history():
    with sqlite3.connect("chat_history.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT user_input, bot_response FROM chat_history ORDER BY id DESC")
        history = cursor.fetchall()
    return render_template("history.html", history=history)

# Gửi tin nhắn qua ajax
@app.route("/send_message", methods=["POST"])
def send_message():
    user_input = request.form.get("input", "").strip()
    if user_input:
        bot_response = process_message(user_input)
        history = get_chat_history()
        return jsonify({
            "status": "success",
            "user_input": user_input,
            "bot_response": bot_response,
            "history": history
        })
    return jsonify({"status": "error", "message": "Vui lòng nhập câu hỏi."})

# Xóa lịch sử của session hiện tại
@app.route("/clear_history", methods=["POST"])
def clear_history():
    session_id = session.get("session_id")
    if not session_id:
        return jsonify({"status": "error", "message": "Không tìm thấy phiên làm việc."})
    try:
        with sqlite3.connect("chat_history.db") as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM chat_history WHERE session_id = ?", (session_id,))
            conn.commit()
        return jsonify({"status": "success"})
    except sqlite3.Error as e:
        print(f"Lỗi xóa lịch sử: {e}")
        return jsonify({"status": "error", "message": "Lỗi khi xóa lịch sử."})
if __name__ == "__main__":
    init_db()
    app.run(debug=True)