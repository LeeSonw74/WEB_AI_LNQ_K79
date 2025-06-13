from flask import Flask, render_template, request, jsonify, session
import sqlite3
import markdown
import uuid
from datetime import datetime
import smtplib
from email.message import EmailMessage
import requests

app = Flask(__name__)
app.secret_key = 'chimtokhonglochetdoi'

API_KEYS = [
    "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"
]

MODEL = "cohere/command-r-plus"
API_URL = "https://openrouter.ai/api/v1/chat/completions"

EMAIL_SENDER = "lnqaik79@gmail.com"
EMAIL_PASSWORD = "gsyhoyoeaeuzsbqb"
EMAIL_RECEIVER = "levansona6k79@gmail.com"

# Gửi email
def send_email(subject, body, receiver, is_html=False):
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = EMAIL_SENDER
    msg["To"] = receiver
    if is_html:
        msg.add_alternative(body, subtype='html')
    else:
        msg.set_content(body)
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(EMAIL_SENDER, EMAIL_PASSWORD)
            smtp.send_message(msg)
        print(f"Email gửi thành công đến {receiver}")
        return True
    except Exception as e:
        print(f"Lỗi gửi email đến {receiver}: {e}")
        return False

# Gửi prompt tới OpenRouter
def get_response(prompt, max_tokens=1000):
    for key in API_KEYS:
        headers = {
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json"
        }

        data = {
            "model": MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens
        }

        try:
            response = requests.post(API_URL, json=data, headers=headers, timeout=10)
            result = response.json()

            if "error" in result:
                code = result["error"].get("code", "")
                msg = result["error"].get("message", "")
                print(f"[!] Lỗi với key {key}: {msg}")
                if code in [402, 429, 401]:
                    continue
                else:
                    return f"Lỗi từ API: {msg}"

            return result['choices'][0]['message']['content'].strip()

        except requests.exceptions.RequestException as e:
            print(f"[!] Lỗi mạng với key {key}: {e}")
            continue

        except Exception as e:
            print(f"[!] Lỗi không xác định với key {key}: {e}")
            continue

    return "Tất cả API key đều lỗi hoặc hết token. Hãy thử lại sau."

# Cơ sở dữ liệu
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

@app.template_filter('timestamp')
def format_timestamp(value):
    try:
        dt = datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
        return dt.strftime('%H:%M %d/%m/%Y')
    except:
        return datetime.now().strftime('%H:%M %d/%m/%Y')

def get_chat_history(limit=5):
    session_id = session.get("session_id")
    if not session_id:
        return []
    try:
        with sqlite3.connect("chat_history.db") as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT user_input, bot_response, timestamp FROM chat_history WHERE session_id = ? ORDER BY id DESC LIMIT ?", (session_id, limit))
            rows = cursor.fetchall()
            return [(row[0], row[1], format_timestamp(row[2])) for row in rows][::-1]
    except:
        return []

def process_message(user_input):
    try:
        prompt = f"Trả lời bằng tiếng Việt: {user_input}"
        text = get_response(prompt)
        cleaned_text = "\n".join(line.strip() for line in text.splitlines() if line.strip())
        bot_response = markdown.markdown(cleaned_text)

        session_id = session.get("session_id")
        if not session_id:
            session_id = str(uuid.uuid4())
            session["session_id"] = session_id

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

@app.route("/history")
def history():
    with sqlite3.connect("chat_history.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT user_input, bot_response, timestamp FROM chat_history ORDER BY id DESC")
        history = [(row[0], row[1], format_timestamp(row[2])) for row in cursor.fetchall()]
    return render_template("history.html", history=history)

@app.route("/get_history", methods=["GET"])
def get_history():
    session_id = session.get("session_id")
    if not session_id:
        return jsonify({"status": "error", "message": "Không tìm thấy phiên làm việc.", "history": []})
    try:
        with sqlite3.connect("chat_history.db") as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT user_input, bot_response, timestamp FROM chat_history WHERE session_id = ? ORDER BY id DESC", (session_id,))
            history = [(row[0], row[1], format_timestamp(row[2])) for row in cursor.fetchall()]
        return jsonify({"status": "success", "history": history})
    except sqlite3.Error as e:
        return jsonify({"status": "error", "message": f"Lỗi khi truy xuất lịch sử: {str(e)}", "history": []})

@app.route("/clear_history", methods=["POST"])
def clear_history():
    session_id = session.get("session_id")
    if not session_id:
        return jsonify({"status": "error", "message": "Không tìm thấy phiên làm việc."})
    try:
        with sqlite3.connect("chat_history.db") as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM chat_history WHERE session_id = ?", (session_id,))
            affected_rows = conn.total_changes
            conn.commit()
            session["chat_count"] = 0
            if affected_rows > 0:
                return jsonify({"status": "success", "message": "Lịch sử đã được xóa thành công."})
            else:
                return jsonify({"status": "success", "message": "Không có lịch sử để xóa."})
    except sqlite3.Error as e:
        return jsonify({"status": "error", "message": f"Lỗi khi xóa lịch sử: {str(e)}"})

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
    except:
        return jsonify({"status": "error", "message": "Lỗi khi lọc lịch sử."})

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

@app.route("/generate_itinerary", methods=["POST"])
def generate_itinerary():
    prompt = request.form.get("prompt", "").strip()
    if not prompt:
        return jsonify({"status": "error", "message": "Vui lòng cung cấp thông tin để tạo hành trình."})
    try:
        itinerary = get_response(prompt)
        cleaned = "\n".join(line.strip() for line in itinerary.splitlines() if line.strip())
        return jsonify({"status": "success", "itinerary": cleaned})
    except Exception as e:
        return jsonify({"status": "error", "message": f"Lỗi khi tạo hành trình: {str(e)}"})

@app.route("/send_form", methods=["POST"])
def send_form():
    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip()
    message = request.form.get("message", "").strip()

    if not name or not email or not message:
        return jsonify({"status": "error", "message": "Vui lòng điền đầy đủ thông tin."})

    admin_subject = f"Liên hệ từ {name} - {email}"
    admin_body = f"Tên: {name}\nEmail: {email}\n\nNội dung:\n{message}"
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
    admin_success = send_email(admin_subject, admin_body, EMAIL_RECEIVER)
    user_success = send_email(user_subject, user_body, email, is_html=True)

    if admin_success and user_success:
        return jsonify({"status": "success", "message": "Đã gửi tin nhắn thành công! Kiểm tra email để nhận phản hồi."})
    else:
        return jsonify({"status": "error", "message": "Lỗi khi gửi email. Vui lòng thử lại sau."})

@app.route("/contact")
def contact():
    return render_template("form.html")

if __name__ == '__main__':
    app.run(debug=True) 