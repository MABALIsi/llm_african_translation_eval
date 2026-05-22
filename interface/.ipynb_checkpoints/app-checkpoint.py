from flask import Flask, render_template, request, jsonify, redirect, url_for
import json
from pathlib import Path

app = Flask(__name__)

def find_file(name, start):
    for p in Path(start).rglob(name):
        return p
    return None

TRANS_FILE = find_file("translations_clean.json", "C:/Users/Albin Mabali")
ANNOT_FILE = Path("C:/Users/Albin Mabali/llm_african_translation/results/evaluations/human_annotations.json")
ANNOT_FILE.parent.mkdir(parents=True, exist_ok=True)

print(f"Fichier trouve : {TRANS_FILE}")

with open(TRANS_FILE, encoding="utf-8") as f:
    all_translations = json.load(f)

def group_by_sentence():
    grouped = {}
    for t in all_translations:
        sid = t["id"]
        if sid not in grouped:
            grouped[sid] = {
                "id":           sid,
                "source_text":  t["source_text"],
                "target_lang":  t["target_lang"],
                "domain":       t["domain"],
                "reference":    t["reference"],
                "translations": []
            }
        grouped[sid]["translations"].append({
            "model":      t["model"],
            "strategy":   t["strategy"],
            "hypothesis": t["hypothesis"],
        })
    return list(grouped.values())

sentences = group_by_sentence()

def load_annotations():
    if ANNOT_FILE.exists():
        with open(ANNOT_FILE, encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_annotation(data):
    annotations = load_annotations()
    key = f"{data['sentence_id']}_{data['model']}_{data['strategy']}"
    annotations[key] = data
    with open(ANNOT_FILE, "w", encoding="utf-8") as f:
        json.dump(annotations, f, ensure_ascii=False, indent=2)

@app.route("/")
def index():
    annotations = load_annotations()
    stats = {
        "total_sentences": len(sentences),
        "total_annotated": len(annotations),
        "lingala": sum(1 for s in sentences if s["target_lang"] == "lin"),
        "bambara": sum(1 for s in sentences if s["target_lang"] == "bam"),
    }
    return render_template("index.html", stats=stats)

@app.route("/annotate/<int:idx>")
def annotate(idx):
    if idx >= len(sentences):
        return redirect(url_for("results"))
    sentence    = sentences[idx]
    annotations = load_annotations()
    return render_template(
        "annotate.html",
        sentence=sentence,
        idx=idx,
        total=len(sentences),
        next_idx=idx + 1,
        prev_idx=max(0, idx - 1),
        annotations=annotations
    )

@app.route("/submit", methods=["POST"])
def submit():
    data = request.get_json()
    save_annotation(data)
    return jsonify({"status": "ok"})

@app.route("/results")
def results():
    annotations = load_annotations()
    scores = []
    for key, ann in annotations.items():
        scores.append({
            "model":     ann.get("model"),
            "strategy":  ann.get("strategy"),
            "lang":      ann.get("target_lang"),
            "adequacy":  ann.get("adequacy", 0),
            "fluency":   ann.get("fluency", 0),
            "score_moy": round(
                (ann.get("adequacy", 0) + ann.get("fluency", 0)) / 2, 2
            )
        })
    return render_template("results.html",
                           scores=scores,
                           total=len(annotations))

if __name__ == "__main__":
    print("Interface demarree sur http://localhost:5000")
    app.run(debug=True, port=5000)