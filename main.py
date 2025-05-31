from flask import Flask, render_template, request, jsonify, session
import google.generativeai as genai
import sqlite3
import markdown
import uuid
from datetime import datetime
import os
from dotenv import load_dotenv
import smtplib
from email.message import EmailMessage

app = Flask(__name__)
app.secret_key = 'chimtokhonglochetdoi'

# Load API key từ biến môi trường
load_dotenv()
api_keys = [os.getenv("GOOGLE_API_KEY")] 

# Send_email (Cập nhật để hỗ trợ gửi đến nhiều người nhận)
def send_email(subject, body, receiver, is_html=False):
    sender = os.getenv("EMAIL_SENDER")
    password = os.getenv("EMAIL_PASSWORD")
    
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = receiver
    if is_html:
        msg.add_alternative(body, subtype='html')
    else:
        msg.set_content(body)
    
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(sender, password)
            smtp.send_message(msg)
        print(f"Email gửi thành công đến {receiver}")
        return True
    except Exception as e:
        print(f"Lỗi gửi email đến {receiver}: {e}")
        return False

# Cấu hình model theo key
def key_model(api_key):
    genai.configure(api_key=api_key)
    return genai.GenerativeModel(model_name="gemini-1.5-flash")

# Thay key tự động
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
                    bot_response TEXT NOT NULL,
                    timestamp TEXT NOT NULL
                )
            ''')
            conn.commit()
            print("Cơ sở dữ liệu được khởi tạo thành công.")
    except sqlite3.Error as e:
        print(f"Lỗi khởi tạo cơ sở dữ liệu: {e}")

init_db()

# Định nghĩa filter timestamp
@app.template_filter('timestamp')
def format_timestamp(value):
    if isinstance(value, str):
        try:
            dt = datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
            return dt.strftime('%H:%M %d/%m/%Y')
        except ValueError:
            return datetime.now().strftime('%H:%M %d/%m/%Y')
    return datetime.now().strftime('%H:%M %d/%m/%Y')

# Lấy lịch sử theo session
def get_chat_history(limit=5):
    session_id = session.get("session_id")
    if not session_id:
        print("Không tìm thấy session_id.")
        return []
    try:
        with sqlite3.connect("chat_history.db") as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT user_input, bot_response, timestamp FROM chat_history WHERE session_id = ? ORDER BY id DESC LIMIT ?", (session_id, limit))
            rows = cursor.fetchall()
            return [(row[0], row[1], format_timestamp(row[2])) for row in rows][::-1]
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

        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        try:
            datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')  # Kiểm tra định dạng
        except ValueError:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        with sqlite3.connect("chat_history.db") as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO chat_history (user_input, bot_response, session_id, timestamp) VALUES (?, ?, ?, ?)",
                (user_input, bot_response, session_id, timestamp)
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

# Trang /itinerary
@app.route("/itinerary", methods=["GET", "POST"])
def itinerary():
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

    return render_template("itinerary.html", user_input=user_input, bot_response=bot_response, history=history)

# Xem lịch sử hiện tại
@app.route("/history")
def history():
    with sqlite3.connect("chat_history.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT user_input, bot_response, timestamp FROM chat_history ORDER BY id DESC")
        history = [(row[0], row[1], format_timestamp(row[2])) for row in cursor.fetchall()]
    return render_template("history.html", history=history)

# Lọc lịch sử
@app.route("/filter_history", methods=["POST"])
def filter_history():
    search = request.form.get("search", "").strip().lower()
    date = request.form.get("date", "").strip()
    session_id = session.get("session_id")
    try:
        with sqlite3.connect("chat_history.db") as conn:
            cursor = conn.cursor()
            query = "SELECT user_input, bot_response, timestamp FROM chat_history WHERE session_id = ?"
            params = [session_id]
            if search:
                query += " AND (LOWER(user_input) LIKE ? OR LOWER(bot_response) LIKE ?)"
                params.extend([f"%{search}%", f"%{search}%"])
            if date:
                query += " AND DATE(timestamp) = ?"
                params.append(date)
            query += " ORDER BY id DESC"
            cursor.execute(query, params)
            history = cursor.fetchall()
            return jsonify({
                "status": "success",
                "history": [(row[0], row[1], format_timestamp(row[2])) for row in history]
            })
    except sqlite3.Error as e:
        print(f"Lỗi truy vấn cơ sở dữ liệu: {e}")
        return jsonify({"status": "error", "message": "Lỗi khi lọc lịch sử."})

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
            "history": [(h[0], h[1], h[2]) for h in history]
        })
    return jsonify({"status": "error", "message": "Vui lòng nhập câu hỏi."})

# Tạo hành trình bằng AI
@app.route("/generate_itinerary", methods=["POST"])
def generate_itinerary():
    prompt = request.form.get("prompt", "").strip()
    if not prompt:
        return jsonify({"status": "error", "message": "Vui lòng cung cấp thông tin để tạo hành trình."})

    try:
        itinerary = get_response(prompt)
        if itinerary.startswith("Lỗi:") or itinerary == "Tất cả API key đã hết hạn hoặc lỗi. Vui lòng thử lại sau.":
            return jsonify({"status": "error", "message": itinerary})

        cleaned_itinerary = "\n".join(line.strip() for line in itinerary.splitlines() if line.strip())
        return jsonify({"status": "success", "itinerary": cleaned_itinerary})
    except Exception as e:
        return jsonify({"status": "error", "message": f"Lỗi khi tạo hành trình: {str(e)}"})

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

# Gửi form (Cập nhật để gửi email phản hồi đến người dùng)
@app.route("/send_form", methods=["POST"])
def send_form():
    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip()
    message = request.form.get("message", "").strip()

    if not name or not email or not message:
        return jsonify({"status": "error", "message": "Vui lòng điền đầy đủ thông tin."})

    # Gửi email đến admin
    admin_subject = f"Liên hệ từ {name} - {email}"
    admin_body = f"Tên: {name}\nEmail: {email}\n\nNội dung:\n{message}"
    admin_receiver = os.getenv("EMAIL_RECEIVER")
    admin_success = send_email(admin_subject, admin_body, admin_receiver)

    # Gửi email phản hồi đến người dùng
    user_subject = "Xác nhận nhận được phản hồi từ bạn"
    user_body = f"""
    <html>
        <body>
            <h2>Chào {name},</h2>
            <p>Cảm ơn bạn đã liên hệ với chúng tôi!</p>
            <p>Chúng tôi đã nhận được tin nhắn của bạn:</p>
            <blockquote style="border-left: 4px solid #1abc9c; padding-left: 10px;">
                {message}
            </blockquote>
            <p>Chúng tôi sẽ phản hồi sớm nhất có thể.</p>
            <p><strong>Trân trọng,</strong><br>Đội ngũ hỗ trợ</p>
        </body>
    </html>
    """
    user_success = send_email(user_subject, user_body, email, is_html=True)

    if admin_success and user_success:
        return jsonify({"status": "success", "message": "Đã gửi tin nhắn thành công! Kiểm tra email để nhận phản hồi."})
    else:
        return jsonify({"status": "error", "message": "Lỗi khi gửi email. Vui lòng thử lại sau."})

# Trang gửi form
@app.route("/contact")
def contact():
    return render_template("form.html")

if __name__ == '__main__':
    app.run(debug=True)