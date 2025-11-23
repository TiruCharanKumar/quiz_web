from flask import Flask, request, jsonify, render_template
import json, os, random
from datetime import datetime
from pathlib import Path

app = Flask(__name__)

# ---------------- CONFIG ----------------
DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)

QUESTIONS_FILE = DATA_DIR / "questions.json"
MARKS_FILE = DATA_DIR / "marks.json"
STUDENTS_FILE = DATA_DIR / "students.json"

NUM_QUESTIONS_PER_TEST = 5


# ---------------- JSON HELPERS ----------------
def load_json(path, default):
    if not path.exists():
        save_json(path, default)
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        save_json(path, default)
        return default


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


# ---------------- DEFAULT DATA ----------------
DEFAULT_QUESTIONS = {
    "1": {"q": "What is 2*2 ?", "a": "4"},
    "2": {"q": "What is 5+5 ?", "a": "10"},
    "3": {"q": "What is 52-44 ?", "a": "8"},
    "4": {"q": "What is 10//3 ?", "a": "3"},
    "5": {"q": "What is 3**2 ?", "a": "9"},
}

questions = load_json(QUESTIONS_FILE, DEFAULT_QUESTIONS)
marks_record = load_json(MARKS_FILE, {})
students = load_json(STUDENTS_FILE, {})


# ---------------- UTIL ----------------
def is_valid_regno(reg):
    return reg.isdigit() and len(reg) == 8


# ---------------- ROUTES (HTML) ----------------
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/admin")
def admin_page():
    return render_template("admin.html")


# ---------------- API ----------------
@app.post("/api/check_reg")
def api_check_reg():
    reg = request.json.get("reg")
    if not is_valid_regno(reg):
        return jsonify({"ok": False, "error": "Invalid registration number"}), 400

    return jsonify({"ok": True, "admin": reg in ["00000000", "11111111", "22222222"]})


@app.get("/api/get_questions")
def api_get_questions():
    global questions
    total_q = min(NUM_QUESTIONS_PER_TEST, len(questions))
    ids = random.sample(list(map(int, questions.keys())), total_q)

    return jsonify({
        "ok": True,
        "questions": [{"id": i, "q": questions[str(i)]["q"]} for i in ids]
    })


@app.post("/api/submit_attempt")
def api_submit_attempt():
    global marks_record, students, questions

    data = request.json
    reg = data["reg"]
    name = data["name"]
    answers = data["answers"]
    qids = data["qids"]

    students[reg] = name
    save_json(STUDENTS_FILE, students)

    question_texts = []
    correct_answers = []

    for qid in qids:
        item = questions[str(qid)]
        question_texts.append(item["q"])
        correct_answers.append(item["a"])

    score = sum(1 for s, c in zip(answers, correct_answers) if s.strip() == c.strip())
    percent = (score / len(qids)) * 100

    attempt = {
        "name": name,
        "datetime": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "score": score,
        "total_questions": len(qids),
        "percentage": percent,
        "questions": qids,
        "question_texts": question_texts,
        "student_answers": answers,
        "correct_answers": correct_answers
    }

    if reg not in marks_record:
        marks_record[reg] = []
    marks_record[reg].append(attempt)
    save_json(MARKS_FILE, marks_record)

    return jsonify({"ok": True, "attempt": attempt})


# ---------------- ADMIN ----------------
@app.get("/api/admin/questions")
def admin_get_questions():
    return jsonify({"ok": True, "questions": questions})


@app.post("/api/admin/questions")
def admin_add_question():
    q = request.json.get("q")
    a = request.json.get("a")
    next_id = str(len(questions) + 1)

    questions[next_id] = {"q": q, "a": a}
    save_json(QUESTIONS_FILE, questions)

    return jsonify({"ok": True})


@app.delete("/api/admin/questions")
def admin_delete_question():
    ids = request.json.get("ids", [])
    ids = set(map(str, ids))

    for i in list(questions.keys()):
        if i in ids:
            del questions[i]

    # reindex
    new = {}
    n = 1
    for old in sorted(questions.keys(), key=int):
        new[str(n)] = questions[old]
        n += 1
    questions.clear()
    questions.update(new)

    save_json(QUESTIONS_FILE, questions)
    return jsonify({"ok": True})


@app.get("/api/admin/marks")
def admin_marks():
    return jsonify({"ok": True, "marks": marks_record})


# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(debug=True)
