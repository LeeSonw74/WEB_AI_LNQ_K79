from flask import Flask, render_template, request, session, jsonify
import google.generativeai as genai
import sqlite3
import markdown as md

app = Flask(__name__)
app.secret_key = 'chimtokhonglochetdoi'
genai.configure(api_key="AIzaSyCPUEoGr6GsEo6TkBT-dg9E0PJUJcm5JqE") 
model = genai.GenerativeModel(model_name="gemini-1.5-flash")

#Hàm lưu trữ lịch sử
def init_db():
    #Điều kiện tìm xem có tồn tại file chat_history.db không?
    with sqlite3.connect("chat_history.db") as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS chat_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_input TEXT NOT NULL,
                bot_response TEXT NOT NULL
            )
        ''')
        conn.commit()
        
init_db()

@app.route("/", methods=["GET", "POST"])
def index():
    #Xóa đoạn chat cũ
    session.clear()
    user_input = session.get('user_input', '')
    bot_response = session.get('bot_response', '')
    history = []
    
    # Lấy 5 ptử chat trong history gần nhất để hiển thị
    with sqlite3.connect("chat_history.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT user_input, bot_response FROM chat_history ORDER BY id DESC LIMIT 5")
        history = cursor.fetchall()
        history = history[::-1]
        
    if request.method == "POST":
        user_input = request.form.get('input', '')
        if user_input:
            try:
                #chatbot trả lời 
                prompt = f"Trả lời: {user_input}"
                response = model.generate_content(prompt)
                bot_response = md.markdown(response.text)
                
                try:
                    #Lưu trữ user_input và bot_response vào chat_history
                    with sqlite3.connect("chat_history.db") as conn:
                        cursor = conn.cursor()
                        cursor.execute(
                            "INSERT INTO chat_history (user_input, bot_response) VALUES (?, ?)",
                            (user_input, bot_response)
                        )
                        conn.commit()
                except sqlite3.OperationalError as e:
                    bot_response = f"Lỗi: {str(e)}"
                    
                #Lưu vào list history nếu quá 5 ptử
                history.append((user_input, bot_response))
                if len(history) > 5:
                    history.pop(0)
                    
            except Exception as e:
                bot_response = f"Lỗi: {str(e)}"
        else:
            bot_response = "Vui lòng nhập câu hỏi."
        session['user_input'] = user_input
        session['bot_response'] = bot_response
        # Render chat_body.html và trả về chuỗi HTML
        chat_body_html = render_template('chat_body.html', user_input=user_input, bot_response=bot_response)
        return chat_body_html
    return render_template("index.html", user_input=user_input, bot_response=bot_response, history = history)

@app.route("/chat", methods=["GET", "POST"])
def chat():
    user_input = ""
    bot_response = ""
    history = []
    # Lấy 5 ptử chat trong history gần nhất để hiển thị
    with sqlite3.connect("chat_history.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT user_input, bot_response FROM chat_history ORDER BY id DESC LIMIT 5")
        history = cursor.fetchall()
        history = history[::-1]
        
    if request.method == "POST":
        user_input = request.form.get("input", "")
        if user_input:
            try:
                #chatbot trả lời 
                prompt = f"Trả lời: {user_input}"
                response = model.generate_content(prompt)
                bot_response = md.markdown(response.text)
                
                try:
                    #Lưu trữ user_input và bot_response vào chat_history
                    with sqlite3.connect("chat_history.db") as conn:
                        cursor = conn.cursor()
                        cursor.execute(
                            "INSERT INTO chat_history (user_input, bot_response) VALUES (?, ?)",
                            (user_input, bot_response)
                        )
                        conn.commit()
                except sqlite3.OperationalError as e:
                    bot_response = f"Lỗi: {str(e)}"
                    
                #Lưu vào list history nếu quá 5 ptử
                history.append((user_input, bot_response))
                if len(history) > 5:
                    history.pop(0)
            except Exception as e:
                bot_response = f"Lỗi: {str(e)}"
        else:
            bot_response = "Vui lòng nhập câu hỏi."
    return render_template("chat.html", user_input=user_input, bot_response=bot_response, history = history)

#Xem lịch sử chatbot
@app.route("/history")
def history():
    conn = sqlite3.connect("chat_history.db")
    cursor = conn.cursor()
    #Truy vấn dữ liệu từ history
    cursor.execute("SELECT user_input, bot_response FROM chat_history ORDER BY id DESC")
    row = cursor.fetchall()
    conn.close()
    return render_template("history.html", history=row)

if __name__ == "__main__":
    app.run(debug=True)