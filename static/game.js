document.addEventListener("DOMContentLoaded", () => {

let currentAnswer = null;
let startTime = Date.now();
let timeLeft = typeof TIMER !== "undefined" ? TIMER : 60;

async function loadTask() {
    let mode = window.location.pathname.split("/").pop();

    let diff = localStorage.getItem("difficulty") || "medium";
    let res = await fetch(`/task/${mode}?difficulty=` + diff);
    let data = await res.json();

    let task = document.getElementById("task");
    task.innerText = "";

    if (data.type === "math") {
        task.innerText = data.q;
        currentAnswer = data.a;
    }
    else if (data.type === "compare") {
        task.innerText = data.q + " (>, <, =)";
        currentAnswer = data.a;
    }
    else if (data.type === "memory") {
        task.innerText = data.seq.join(" ");
        currentAnswer = data.a;

        setTimeout(() => {
            task.innerText = "???";
        }, 2000);
    }
    else if (data.type === "logic") {
        task.innerText = data.seq.join(", ") + ", ?";
        currentAnswer = data.a;
    }
    else if (data.type === "2back") {
        task.innerText = data.seq.join(" ");
        currentAnswer = data.a;
    }
    else if (data.type === "multi") {
        task.innerText = data.math_q + " | " + data.seq.join(" ");
        currentAnswer = data.a;
    }

    startTime = Date.now();
}

async function send() {
    let answer = document.getElementById("answer").value;
    let time = (Date.now() - startTime) / 1000;

    let diff = localStorage.getItem("difficulty") || "medium";

    let res = await fetch("/check", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({
            answer: answer,
            correct: currentAnswer,
            time: time,
            difficulty: diff
        })
    });

    let data = await res.json();

    document.getElementById("xp").innerText = data.score;

    let combo = data.combo;
    let comboBox = document.getElementById("comboBox");
    let comboText = document.getElementById("comboText");

    comboText.innerText = "x" + combo;

    comboBox.className = "combo-box";

    if (combo < 3) comboBox.classList.add("combo-low");
    else if (combo < 6) comboBox.classList.add("combo-mid");
    else if (combo < 10) comboBox.classList.add("combo-high");
    else comboBox.classList.add("combo-god");

    animate(data.correct);

    document.getElementById("answer").value = "";
    loadTask();
}

function animate(correct) {
    let body = document.body;

    body.style.background = correct ? "#064e3b" : "#7f1d1d";

    setTimeout(() => body.style.background = "#0f172a", 200);
}

document.getElementById("answer").addEventListener("keydown", function(e) {
    if (e.key === "Enter") {
        send();
    }
});

window.send = send;

function startTimer() {
    setInterval(() => {
        timeLeft--;

        document.getElementById("timer").innerText = "⏱ " + timeLeft;

        if (timeLeft <= 0) {
            window.location.href = "/result";
        }
    }, 1000);
}
comboBox.style.transform = "scale(1.2)";
setTimeout(() => comboBox.style.transform = "scale(1)", 150);
startTimer();
loadTask();

});
