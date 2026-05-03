from flask import Flask, jsonify, render_template, request

from jarvis_core import JarvisAssistant

app = Flask(__name__, static_folder="public", static_url_path="")
assistant = JarvisAssistant()


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/api/status")
def status():
    return jsonify(assistant.get_status())


@app.post("/api/command")
def command():
    data = request.get_json(silent=True) or {}
    message = str(data.get("message", "")).strip()
    client_state = data.get("client_state") or {}
    result = assistant.handle_command(message, client_state=client_state)
    return jsonify(
        {
            "response": result.response,
            "action": result.action,
            "payload": result.payload or {},
        }
    )


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
