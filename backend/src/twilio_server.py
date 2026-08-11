from flask import Flask, Response

app = Flask(__name__)

@app.route("/voice", methods=["GET", "POST"])
def voice():
    twiml = """<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say>
        Hello, I am ASHA Sathi, a healthcare support assistant.
        I am calling to remind you about your scheduled health reminder.
        If you do not want to receive these calls, you can say stop at any time.
        Please follow your healthcare provider's instructions.
        Take care and stay healthy.
    </Say>
</Response>"""

    return Response(twiml, mimetype="text/xml")


if __name__ == "__main__":
    app.run(port=5000)