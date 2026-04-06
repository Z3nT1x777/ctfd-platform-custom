from flask import Flask, request, render_template_string
import os

app = Flask(__name__)

FLAG = open("flag.txt").read()

@app.route("/", methods=["GET", "POST"])
def index():
    note = ""
    if request.method == "POST":
        note = request.form.get("note", "")

    template = f"""
    <h1>📝 Flasky Notes</h1>
    <form method="POST">
        <textarea name="note" rows="5" cols="40">{note}</textarea><br><br>
        <button type="submit">Save</button>
    </form>

    <h2>Your note:</h2>
    <div style="border:1px solid #ccc;padding:10px;">
        {note}
    </div>
    """

    return render_template_string(template)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
