import random

def generate_math(difficulty="medium"):
    if difficulty == "easy":
        a = random.randint(1, 20)
        b = random.randint(1, 10)
    elif difficulty == "hard":
        a = random.randint(50, 200)
        b = random.randint(10, 50)
    else:
        a = random.randint(10, 100)
        b = random.randint(2, 20)

    op = random.choice(['+', '-', '*'])
    q = f"{a} {op} {b}"

    return {"type": "math", "q": q, "a": int(eval(q))}

def generate_memory():
    seq = [random.randint(0,9) for _ in range(5)]
    return {"type":"memory","seq":seq,"a":"".join(map(str,seq))}

def generate_logic():
    import random

    pattern_type = random.choice([
        "add",          # +n
        "multiply",     # ×n
        "alternate",    # чередование
        "progressive",  # +1, +2, +3...
        "power"         # ×2 (степени)
    ])

    seq = []

    # ➕ ПРОСТОЕ СЛОЖЕНИЕ
    if pattern_type == "add":
        start = random.randint(1, 20)
        step = random.randint(2, 10)

        seq = [start + i * step for i in range(5)]
        answer = seq[-1]

    # ✖ УМНОЖЕНИЕ
    elif pattern_type == "multiply":
        start = random.randint(1, 5)
        mult = random.randint(2, 4)

        seq = [start]
        for _ in range(4):
            seq.append(seq[-1] * mult)

        answer = seq[-1]

    # 🔁 ЧЕРЕДОВАНИЕ
    elif pattern_type == "alternate":
        start = random.randint(1, 10)
        seq = [start]

        for i in range(4):
            if i % 2 == 0:
                seq.append(seq[-1] + random.randint(2, 5))
            else:
                seq.append(seq[-1] * 2)

        answer = seq[-1]

    # 📈 ПРОГРЕССИЯ (+1, +2, +3...)
    elif pattern_type == "progressive":
        start = random.randint(1, 10)
        seq = [start]

        inc = 1
        for _ in range(4):
            seq.append(seq[-1] + inc)
            inc += 1

        answer = seq[-1]

    # ⚡ СТЕПЕНИ (2,4,8...)
    else:
        start = random.randint(1, 3)
        seq = [start]

        for _ in range(4):
            seq.append(seq[-1] * 2)

        answer = seq[-1]

    return {
        "type": "logic",
        "seq": seq[:-1],
        "a": answer
    }

def generate_2back():
    s = [random.choice(['A','B','C']) for _ in range(5)]
    return {"type":"2back","seq":s,"a":"yes" if s[-1]==s[-3] else "no"}

def generate_multitask():
    m = generate_math()
    s = [random.choice(['A','B','C']) for _ in range(5)]
    a2 = "yes" if s[-1]==s[-3] else "no"
    return {"type":"multi","math_q":m['q'],"seq":s,"a":f"{m['a']}|{a2}"}

def generate_math_chain():
    import random

    a = random.randint(5, 20)
    b = random.randint(2, 10)
    c = random.randint(1, 5)

    q = f"{a} + {b} * {c}"
    return {"type": "math", "q": q, "a": int(eval(q))}

def generate_math_compare():
    import random

    a = random.randint(2, 10)
    b = random.randint(2, 10)
    c = random.randint(2, 10)
    d = random.randint(2, 10)

    left = a * b
    right = c * d

    if left > right:
        answer = ">"
    elif left < right:
        answer = "<"
    else:
        answer = "="

    return {
        "type": "compare",
        "q": f"{a}×{b} ? {c}×{d}",
        "a": answer
    }