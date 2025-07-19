from flask import Flask, jsonify

app = Flask(__name__)

@app.route("/api/risks")
def risks():
    return jsonify([{"Risk": "Test Risk 1"}, {"Risk": "Test Risk 2"}])

if __name__ == "__main__":
    app.run(debug=True)
