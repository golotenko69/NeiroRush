from flask import Flask, render_template, request, jsonify, session, redirect
from database import get_db, init_db
from game.generator import *
from game.scoring import calculate_score
app = Flask(__name__)
app.secret_key = "secret"

ACHIEVEMENT_NAMES = {
    "first_game": "🎮 Первая игра",
    "grinder": "🔁 10 игр",
    "combo_5": "🔥 Комбо 5",
    "combo_10": "⚡ Комбо 10",
    "accuracy_80": "🎯 Точность 80%",
    "perfect": "💎 Идеальная игра",
    "xp_500": "📈 500 XP",
    "xp_1000": "🚀 1000 XP"
}

def add_history(user_id, score):
    db = get_db()
    cur = db.cursor()

    cur.execute(
        "INSERT INTO history (user_id, score) VALUES (?, ?)",
        (user_id, score)
    )
    db.commit()


def update_stats(name, correct, combo):
    db = get_db()
    cur = db.cursor()

    cur.execute("""
        UPDATE users
        SET
            games_played = games_played + 1,
            correct = correct + ?,
            best_streak = MAX(best_streak, ?)
        WHERE name = ?
    """, (correct, combo, name))

    db.commit()

def update_record(user_id, mode, score):
    db = get_db()
    cur = db.cursor()

    cur.execute("""
        INSERT INTO records (user_id, mode, value)
        VALUES (?, ?, ?)
        ON CONFLICT(user_id, mode)
        DO UPDATE SET value = MAX(value, excluded.value)
    """, (user_id, mode, score))

    db.commit()

def get_user(name):
    db = get_db()
    cur = db.cursor()

    cur.execute("SELECT * FROM users WHERE name = ?", (name,))
    user = cur.fetchone()

    return user

def create_user(name):
    db = get_db()
    cur = db.cursor()

    cur.execute("""
        INSERT INTO users (name, xp, games_played, correct, best_streak)
        VALUES (?, 0, 0, 0, 0)
    """, (name,))

    db.commit()


def update_xp(name, xp):
    db = get_db()
    cur = db.cursor()

    cur.execute("UPDATE users SET xp = ? WHERE name = ?", (xp, name))
    db.commit()

DATA_FILE = "data/users.json"
ROUND_TIME = 60

RANKS = [
    (0, "Удаляй игру"),
    (300, "Лишняя хромосома"),
    (600, "Слабый"),
    (1000, "Средне Слабый"),
    (1500, "Среднечок"),
    (2000, "Сильный")  # запас на будущее
]

MODE_NAMES = {
    "math": "⚡ Быстрый счёт",
    "math_chain": "🔗 Цепочки",
    "math_compare": "⚖️ Сравнение",
    "memory": "🧠 Память",
    "2back": "🔁 2-back",
    "logic": "🧩 Логика",
    "multi": "🚀 Мультизадача"
}
def get_rank(xp):
    current = RANKS[0][1]

    for threshold, name in RANKS:
        if xp >= threshold:
            current = name
        else:
            break

    return current

def check_achievements(user_name):
    db = get_db()
    cur = db.cursor()

    # получаем user_id
    cur.execute("SELECT * FROM users WHERE name = ?", (user_name,))
    user = cur.fetchone()

    if not user:
        return []

    user_id = user["id"]

    games = user["games_played"]
    correct = user["correct"]
    streak = user["best_streak"]
    xp = user["xp"]

    accuracy = int((correct / games) * 100) if games > 0 else 0

    unlocked = []

    def unlock(code):
        try:
            cur.execute(
                "INSERT INTO achievements (user_id, code) VALUES (?, ?)",
                (user_id, code)
            )
            unlocked.append(code)
        except:
            pass  # уже есть

    # 🎯 ДОСТИЖЕНИЯ

    if games >= 1:
        unlock("first_game")

    if games >= 10:
        unlock("grinder")

    if streak >= 5:
        unlock("combo_5")

    if streak >= 10:
        unlock("combo_10")

    if accuracy >= 80 and games >= 5:
        unlock("accuracy_80")

    if accuracy == 100 and games >= 5:
        unlock("perfect")

    if xp >= 500:
        unlock("xp_500")

    if xp >= 1000:
        unlock("xp_1000")

    db.commit()
    return unlocked

def get_user_stats(name):
    user = get_user(name)

    if not user:
        return {
            "games": 0,
            "accuracy": 0,
            "streak": 0
        }

    games = user["games_played"]
    correct = user["correct"]
    best_streak = user["best_streak"]

    accuracy = int((correct / games) * 100) if games > 0 else 0

    return {
        "games": games,
        "accuracy": accuracy,
        "streak": best_streak
    }

def get_progress(xp):
    prev = 0
    next_xp = xp

    for threshold, name in RANKS:
        if xp >= threshold:
            prev = threshold
        else:
            next_xp = threshold
            break

    if next_xp == prev:
        return 100, next_xp

    progress = int(((xp - prev) / (next_xp - prev)) * 100)

    # 👇 ВАЖНО — чтобы не было "0%"
    if progress == 0 and xp > 0:
        progress = 2

    return progress, next_xp


@app.route("/rating")
def rating_page():
    return render_template("rating.html")


@app.route("/duels")
def duels():
    return render_template("duels.html")


@app.route("/builder")
def builder():
    return render_template("builder.html")


@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        user = get_user(username)

        if not user:
            create_user(username)

        session["user"] = username
        return redirect("/menu")

    return render_template("login.html")

@app.route("/settings", methods=["POST"])
def settings():
    data = request.json

    session["difficulty"] = data.get("difficulty", "medium")
    session["timer"] = int(data.get("timer", 60))

    return jsonify({"status": "ok"})

@app.route("/menu")
def menu():
    if "user" not in session:
        return redirect("/")

    user = get_user(session["user"])
    xp = user["xp"]

    progress, next_xp = get_progress(xp)
    

    return render_template(
        "menu.html",
        name=session["user"],
        xp=xp,
        rank=get_rank(xp),
        progress=progress,
        next_xp=next_xp
    )

def get_level(xp):
    return xp // 100 + 1

@app.route("/game/<mode>")
def game(mode):
    if "user" not in session:
        return redirect("/")

    # сброс сессии
    session["score"] = 0
    session["correct"] = 0
    session["wrong"] = 0
    session["combo"] = 0
    session["best_combo"] = 0
    session["mode"] = mode

    # получаем пользователя из БД
    user = get_user(session["user"])

    if not user:
        return redirect("/")  # защита

    xp = user["xp"]
    level = get_level(xp)

    names = {
        "math": "⚡ Быстрый счёт",
        "math_chain": "🔗 Цепочки",
        "math_compare": "⚖️ Сравнение",
        "memory": "🧠 Память",
        "2back": "🔁 2-back",
        "logic": "🧩 Логика",
        "multi": "🚀 Мультизадача"
    }

    title = names.get(mode, "Игра")

    return render_template(
        "game.html",
        mode=mode,
        title=title,
        name=session["user"],
        xp=xp,
        level=level,
        difficulty=session.get("difficulty", "medium")
    )


@app.route("/task/<mode>")
def task(mode):
    difficulty = request.args.get("difficulty", "medium")

    if mode == "math":
        return jsonify(generate_math(difficulty))

    if mode == "math_chain":
        return jsonify(generate_math_chain())

    if mode == "math_compare":
        return jsonify(generate_math_compare())

    if mode == "memory":
        return jsonify(generate_memory())

    if mode == "2back":
        return jsonify(generate_2back())

    if mode == "logic":
        return jsonify(generate_logic())

    if mode == "multi":
        return jsonify(generate_multitask())

@app.route("/check", methods=["POST"])
def check():
    d = request.json

    correct = str(d["answer"]) == str(d["correct"])
    difficulty = d.get("difficulty", "medium")

    score = calculate_score(
        correct,
        float(d["time"]),
        session['combo'],
        difficulty
    )

    user = get_user(session["user"])
    new_xp = user["xp"] + score

    if new_xp < 0:
        new_xp = 0

    update_xp(session["user"], new_xp)

    # статистика
    if correct:
        session['correct'] += 1
        session['combo'] += 1
    else:
        session['wrong'] += 1
        session['combo'] = 0

    session["best_combo"] = max(session["best_combo"], session["combo"])

    session["score"] += score
    if session["score"] < 0:
        session["score"] = 0

    return jsonify({
        "score": new_xp,
        "combo": session['combo'],
        "correct": correct
    })


@app.route("/result")
def result():
    correct = session.get("correct", 0)
    wrong = session.get("wrong", 0)

    total = correct + wrong
    accuracy = int((correct / total) * 100) if total > 0 else 0

    user = get_user(session["user"])

    xp = user["xp"]
    score = session.get("score", 0)

    # запись истории
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT id FROM users WHERE name = ?", (session["user"],))
    user_id = cur.fetchone()["id"]

    add_history(user_id, score)

    # обновление статистики
    update_stats(session["user"], correct, session["best_combo"])

    # рекорд
    record = max(score, session.get("record", 0))
    new_record = score > session.get("record", 0)
    update_record(user_id, session.get("mode"), score)

    session["record"] = record
    new_achievements = check_achievements(session["user"])

    return render_template(
        "result.html",
        xp=xp,
        record=record,
        accuracy=accuracy,
        new_record=new_record,
        achievements=new_achievements,
        achievement_names=ACHIEVEMENT_NAMES
    )

@app.route("/leaderboard")
def leaderboard():
    db = get_db()
    cur = db.cursor()

    cur.execute("SELECT name, xp FROM users ORDER BY xp DESC LIMIT 10")
    rows = cur.fetchall()

    result = [{"name": r["name"], "xp": r["xp"]} for r in rows]

    return jsonify(result)

@app.route("/achievements")
def achievements():
    if "user" not in session:
        return redirect("/")

    db = get_db()
    cur = db.cursor()

    cur.execute("SELECT id FROM users WHERE name = ?", (session["user"],))
    user_id = cur.fetchone()["id"]

    cur.execute("SELECT code FROM achievements WHERE user_id = ?", (user_id,))
    unlocked = [row["code"] for row in cur.fetchall()]

    return render_template(
        "achievements.html",
        unlocked=unlocked,
        names=ACHIEVEMENT_NAMES
    )



if __name__ == "__main__":
    init_db()
    app.run(debug=True)

