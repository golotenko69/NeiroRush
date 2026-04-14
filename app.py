from flask import Flask, render_template, request, jsonify, session, redirect

from game.generator import *
from game.scoring import calculate_score
import json, os

import os
import json

def load_users():
    path = os.path.join("data", "users.json")

    if not os.path.exists(path):
        return {}

    with open(path, "r") as f:
        return json.load(f)

def save_users(users):
    with open("data/users.json", "w") as f:
        json.dump(users, f, indent=4)
app = Flask(__name__)
app.secret_key = "secret"


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

def get_user_stats(name):
    users = load_users()
    user = users[session["user"]]
    user = users.get(name, {})

    games = user.get("games_played", 0)
    correct = user.get("correct", 0)
    best_streak = user.get("best_streak", 0)

    accuracy = 0
    if games > 0:
        accuracy = int((correct / games) * 100)

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
    return progress, next_xp

def get_level(xp):
    return xp // 100 + 1



@app.route("/achievements")
def achievements():
    return render_template("achievements.html")


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
        users = load_users()

        if username not in users:
            users[username] = {
                "records": {"math": 0, "memory": 0, "logic": 0, "2back": 0, "multi": 0},
                "history": [],
                "xp": 0
            }
            save_users(users)

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

    users = load_users()
    user = users[session["user"]]

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


@app.route("/game/<mode>")
def game(mode):
    session["correct"] = 0
    session["wrong"] = 0
    session['mode'] = mode
    session["score"] = 0
    session["combo"] = 0
    if "user" not in session:
        return redirect("/")

    users = load_users()
    user = users[session["user"]]

    # защита от отсутствия xp
    xp = user.get("xp", 0)
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
    users = load_users()
    user = users[session["user"]]

    user["xp"] += score

    save_users(users)
    if correct:
        session['correct'] += 1
        session['combo'] += 1
    else:
        session['wrong'] += 1
        session['combo'] = 1

    session['score'] += score
    if session["score"] < 0:
        session["score"] = 0


    return jsonify({
        "score": user["xp"],
        "combo": session['combo'],
        "correct": correct
    })


@app.route("/result")
def result():
    correct = session.get("correct", 0)
    wrong = session.get("wrong", 0)

    total = correct + wrong
    accuracy = int((correct / total) * 100) if total > 0 else 0

    xp = session.get("xp", 0)
    record = session.get("record", 0)

    if xp > record:
        session["record"] = xp
        record = xp
        new_record = True
    else:
        new_record = False

    return render_template(
        "result.html",
        xp=xp,
        record=record,
        accuracy=accuracy,
        new_record=new_record
    )
@app.route("/leaderboard")
def leaderboard():
    users = load_users()

    rating = sorted(
        users.items(),
        key=lambda x: x[1].get("xp", 0),
        reverse=True
    )

    # преобразуем в нормальный формат
    result = [
        {"name": name, "xp": data.get("xp", 0)}
        for name, data in rating[:10]
    ]

    return jsonify(result)



if __name__ == "__main__":
    app.run(debug=True)