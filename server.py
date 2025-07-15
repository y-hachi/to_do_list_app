from flask import Flask, render_template
import sqlite3
from flask import Flask, render_template, request, redirect, url_for
from flask import send_from_directory
from datetime import datetime

app = Flask(__name__)

@app.route('/favicon.ico')
def favicon():
    return send_from_directory('static/icon', '/favicon.ico', mimetype='image/vnd.microsoft.icon')

@app.route("/")
def home():
    conn = sqlite3.connect("app.db")
    cursor = conn.cursor()

    # 課題情報（既存）
    cursor.execute("""
        SELECT lectures.lecture_name, assignments.session, assignments.due_date
        FROM assignments
        JOIN lectures ON assignments.lecture_id = lectures.lecture_id
        ORDER BY assignments.priority DESC, assignments.due_date ASC
        LIMIT 5
    """)
    assignments = cursor.fetchall()
    while len(assignments) < 5:
        assignments.append(("-", "-", "-"))

    # テスト情報（変更後）
    cursor.execute("""
        SELECT lectures.lecture_name, tests.session, tests.test_date, tests.test_type
        FROM tests
        JOIN lectures ON tests.lecture_id = lectures.lecture_id
        ORDER BY tests.test_date ASC
        LIMIT 5
    """)
    tests = cursor.fetchall()
    while len(tests) < 5:
        tests.append(("-", "-", "-", "-"))

    conn.close()

    # 現在時刻を渡す
    now = datetime.now().strftime("%Y年%m月%d日 %H:%M:%S")
    return render_template("toppage.html", assignments=assignments, tests=tests, now=now)

@app.route("/detail", methods=["GET", "POST"])
def detail():
    conn = sqlite3.connect("app.db")
    cursor = conn.cursor()

    # 提出状況の更新処理（POST）
    if request.method == "POST":
        assignment_id = request.form.get("assignment_id")
        new_status = request.form.get("new_status")
        if assignment_id and new_status:
            cursor.execute("UPDATE assignments SET status = ? WHERE assignment_id = ?", (new_status, assignment_id))
            conn.commit()

    cursor.execute("SELECT * FROM lectures")
    lectures = cursor.fetchall()

    # 講義情報を取得
    cursor.execute("SELECT lecture_id, lecture_name FROM lectures")
    lectures = cursor.fetchall()

    lecture_data = {}
    for lecture_id, lecture_name in lectures:
        # 出席情報
        cursor.execute("""
            SELECT attendance_id, session, attendance_status
            FROM attendances
            WHERE lecture_id = ?
            ORDER BY session
        """, (lecture_id,))
        attendance = cursor.fetchall()

        # 課題情報
        cursor.execute("""
            SELECT assignment_id, session, due_date, status, priority
            FROM assignments
            WHERE lecture_id = ?
            ORDER BY session
        """, (lecture_id,))
        assignments = cursor.fetchall()

        # テスト情報
        cursor.execute("""
            SELECT test_id, session, test_type, test_date
            FROM tests
            WHERE lecture_id = ?
            ORDER BY session
        """, (lecture_id,))
        tests = cursor.fetchall()

        # メモ
        cursor.execute("""
            SELECT memo_id, session, content
            FROM memos
            WHERE lecture_id = ?
            ORDER BY session
        """, (lecture_id,))
        memos = cursor.fetchall()

        # リンク
        cursor.execute("""
            SELECT resource_id, link
            FROM resources
            WHERE lecture_id = ?
        """, (lecture_id,))
        resources = cursor.fetchall()

        lecture_data[lecture_name] = {
            "attendance": attendance,
            "assignments": assignments,
            "tests": tests,
            "memos": memos,
            "resources": resources
        }

    conn.close()
    return render_template("detail.html", lectures=lectures, lecture_data=lecture_data)

@app.route("/edit", methods=["GET", "POST"])
def edit():
    conn = sqlite3.connect("app.db")
    cursor = conn.cursor()

    message = ""
    message_at = ""
    message_as = ""
    message_te = ""
    message_memo = ""
    message_re = ""

    if request.method == "POST":
        form_type = request.form.get("form_type")

        # --- 講義追加処理 ---
        if form_type == "lecture":
            lecture_name = request.form["lecture_name"]
            cursor.execute("SELECT * FROM lectures WHERE lecture_name = ?", (lecture_name,))
            if cursor.fetchone():
                message = "⚠️ 同じ講義名は既に登録されています。"
            else:
                cursor.execute("INSERT INTO lectures (lecture_name) VALUES (?)", (lecture_name,))
                conn.commit()
                message = "✅ 講義を追加しました。"
            return redirect(url_for("edit", scroll_to="le", msg="lecture_added"))

        # --- 出席追加処理 ---
        elif form_type == "attendance":
            lecture_id = request.form["lecture_id"]
            session = request.form["session"]
            status = request.form["attendance_status"]
            cursor.execute("SELECT 1 FROM attendances WHERE lecture_id = ? AND session = ?", (lecture_id, session))
            if cursor.fetchone():
                return redirect(url_for("edit", msg="duplicate", scroll_to="at"))
            else:
                cursor.execute("""
                    INSERT INTO attendances (lecture_id, session, attendance_status)
                    VALUES (?, ?, ?)
                """, (lecture_id, session, status))
                conn.commit()
                return redirect(url_for("edit", msg="success", scroll_to="at"))

        # --- 課題追加処理 ---
        elif form_type == "assignment":
            lecture_id = request.form["lecture_id"]
            session = request.form["session"]
            due_date = request.form["due_date"]
            status = request.form["status"]
            priority = request.form["priority"]
            cursor.execute("""
                INSERT INTO assignments (lecture_id, session, due_date, status, priority)
                VALUES (?, ?, ?, ?, ?)
            """, (lecture_id, session, due_date, status, priority))
            conn.commit()
            message_as = "✅ 課題を追加しました。"
            return redirect(url_for("edit", scroll_to="as"))

        elif "test_lecture_id" in request.form and "test_session" in request.form and "test_type" in request.form and "test_date" in request.form:
            lecture_id = request.form["test_lecture_id"]
            session = request.form["test_session"]
            test_type = request.form["test_type"]
            test_date = request.form["test_date"]

            cursor.execute("""
                INSERT INTO tests (lecture_id, session, test_type, test_date)
                VALUES (?, ?, ?, ?)
            """, (lecture_id, session, test_type, test_date))
            conn.commit()
            message_te = "✅ テスト情報を追加しました。"
            return redirect(url_for("edit", scroll_to="te"))

        elif form_type == "memo":
            lecture_id = request.form["lecture_id"]
            session = request.form["memo_session"]
            content = request.form["memo_content"]

            cursor.execute("""
                INSERT INTO memos (lecture_id, session, content)
                VALUES (?, ?, ?)
            """, (lecture_id, session, content))
            conn.commit()
            message_memo = "✅ メモを追加しました。"
            return redirect(url_for("edit", scroll_to="me", msg="memo_added"))

        elif "resource_lecture_id" in request.form and "resource_link" in request.form:
            lecture_id = request.form["resource_lecture_id"]
            link = request.form["resource_link"]
            description = request.form["resource_description"]

            cursor.execute("""
                INSERT INTO resources (lecture_id, link, description)
                VALUES (?, ?)
            """, (lecture_id, link, description))
            conn.commit()
            message_re = "✅ 参考リンクを追加しました。"
            return redirect(url_for("edit", scroll_to="re"))

    # 出席メッセージ
    msg_code = request.args.get("msg")
    if msg_code == "duplicate":
        message_at = "⚠ 同じ講義・講義回の出席情報は既に登録されています。"
    elif msg_code == "success":
        message_at = "✅ 出席情報を追加しました。"

    # データ取得
    cursor.execute("SELECT * FROM lectures")
    lectures = cursor.fetchall()

    cursor.execute("""
        SELECT a.attendance_id, l.lecture_name, a.session, a.attendance_status
        FROM attendances a
        JOIN lectures l ON a.lecture_id = l.lecture_id
    """)
    attendances = cursor.fetchall()

    cursor.execute("""
        SELECT a.assignment_id, l.lecture_name, a.session, a.due_date, a.status, a.priority
        FROM assignments a
        JOIN lectures l ON a.lecture_id = l.lecture_id
    """)
    assignments = cursor.fetchall()

    conn.close()
    return render_template("edit.html", lectures=lectures, attendances=attendances,assignments=assignments,
                            message=message, message_at=message_at,message_as=message_as, message_te=message_te,
                            message_memo=message_memo,message_re=message_re)


@app.route("/delete_lecture/<int:id>", methods=["POST"])
def delete_lecture(id):
    conn = sqlite3.connect("app.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM lectures WHERE lecture_id = ?", (id,))
    conn.commit()
    conn.close()
    return redirect(url_for("edit"))

@app.route("/delete_attendance/<int:id>", methods=["POST"])
def delete_attendance(id):
    conn = sqlite3.connect("app.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM attendances WHERE attendance_id = ?", (id,))
    conn.commit()
    conn.close()
    return redirect(url_for("edit"))

@app.route("/delete_assignment/<int:id>", methods=["POST"])
def delete_assignment(id):
    conn = sqlite3.connect("app.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM assignments WHERE assignment_id = ?", (id,))
    conn.commit()
    conn.close()
    return redirect(url_for("detail"))

@app.route("/delete_test/<int:id>", methods=["POST"])
def delete_test(id):
    conn = sqlite3.connect("app.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM tests WHERE test_id = ?", (id,))
    conn.commit()
    conn.close()
    return redirect(url_for("detail"))

@app.route("/delete_memo/<int:id>", methods=["POST"])
def delete_memo(id):
    conn = sqlite3.connect("app.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM memos WHERE memo_id = ?", (id,))
    conn.commit()
    conn.close()
    return redirect(url_for("detail"))

@app.route("/delete_resource/<int:id>", methods=["POST"])
def delete_resource(id):
    conn = sqlite3.connect("app.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM resources WHERE resource_id = ?", (id,))
    conn.commit()
    conn.close()
    return redirect(url_for("detail"))

if __name__ == "__main__":
    app.run(debug=True)