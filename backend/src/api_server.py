import logging

from flask import Flask, jsonify, request

from escalation import list_escalations, update_escalation_status

logger = logging.getLogger("api_server")

app = Flask(__name__)


@app.route("/api/escalations", methods=["GET"])
def get_escalations():
    """Return escalation requests, optionally filtered by status."""
    status = request.args.get("status")
    try:
        items = list_escalations(status=status)
    except Exception:
        logger.exception("Failed to list escalations")
        return jsonify({"error": "Unable to load escalation requests"}), 500

    return jsonify(items)


@app.route("/api/escalations/<int:escalation_id>", methods=["PATCH"])
def patch_escalation(escalation_id: int):
    """Update the status of an escalation request."""
    data = request.get_json(silent=True) or {}
    status = data.get("status")

    if not status:
        return jsonify({"error": "status is required"}), 400

    try:
        result = update_escalation_status(escalation_id, status)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except Exception:
        logger.exception("Failed to update escalation %s", escalation_id)
        return jsonify({"error": "Unable to update escalation request"}), 500

    if result is None:
        return jsonify({"error": "Escalation not found"}), 404

    return jsonify(result)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    app.run(host="127.0.0.1", port=5001)
