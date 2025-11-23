async function postJSON(url, data) {
    let res = await fetch(url, {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify(data)
    });
    return res.json();
}

// STUDENT FLOW
if (document.getElementById("startBtn")) {

    startBtn.onclick = async () => {
        let reg = document.getElementById("reg").value.trim();
        let name = document.getElementById("name").value.trim();

        if (!/^[0-9]{8}$/.test(reg)) {
            alert("Registration must be 8 digits");
            return;
        }

        let chk = await postJSON("/api/check_reg", {reg});
        if (!chk.ok) return alert(chk.error);

        if (chk.admin) {
            window.location = "/admin";
            return;
        }

        let qres = await fetch("/api/get_questions");
        let qjson = await qres.json();

        let quizBox = document.getElementById("quizBox");
        let form = document.getElementById("quizForm");

        form.innerHTML = "";
        qjson.questions.forEach((q, i) => {
            form.innerHTML += `
            <div class="question">
                <label>Q${i+1}. ${q.q}</label>
                <input data-qid="${q.id}">
            </div>
        `;
        });

        document.getElementById("questionCount").innerText =
            `Answer ${qjson.questions.length} question(s)`;

        quizBox.style.display = "block";

        submitBtn.onclick = async () => {
            let inputs = form.querySelectorAll("input");
            let answers = [];
            let qids = [];
            inputs.forEach(i => {
                answers.push(i.value || "");
                qids.push(parseInt(i.dataset.qid));
            });

            let result = await postJSON("/api/submit_attempt", {
                reg, name, answers, qids
            });

            let att = result.attempt;

            document.getElementById("resultBox").style.display = "block";
            document.getElementById("resultText").innerText =
                `Score: ${att.score}/${att.total_questions}\nPercentage: ${att.percentage.toFixed(2)}%\n`;
        };
    };
}

// ADMIN FLOW
if (document.getElementById("addBtn")) {

    async function loadQuestions() {
        let res = await fetch("/api/admin/questions");
        let json = await res.json();

        let box = document.getElementById("questionsList");
        box.innerHTML = "";

        for (let id of Object.keys(json.questions).sort((a,b)=>a-b)) {
            let q = json.questions[id];
            box.innerHTML += `${id}. ${q.q} (Ans: ${q.a})<br>`;
        }
    }

    loadQuestions();

    addBtn.onclick = async () => {
        let q = newQ.value.trim();
        let a = newA.value.trim();

        await postJSON("/api/admin/questions", {q, a});
        loadQuestions();
    };

    delBtn.onclick = async () => {
        let ids = delIds.value.split(",").map(i => parseInt(i.trim()));

        await fetch("/api/admin/questions", {
            method: "DELETE",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({ids})
        });

        loadQuestions();
    };

    refreshMarks.onclick = async () => {
        let res = await fetch("/api/admin/marks");
        let json = await res.json();
        marksBox.innerText = JSON.stringify(json.marks, null, 2);
    };
}
