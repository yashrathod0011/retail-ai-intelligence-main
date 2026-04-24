# src/api/chat.py
# Chat endpoints for the Report Chatbot tab
# Plug into app.py with:
#   from src.api.chat import chat_bp
#   app.register_blueprint(chat_bp)

import json
import logging
from datetime import datetime
from flask import Blueprint, jsonify, request
from bson import ObjectId
from google import genai
from src.database.mongo_manager import db_manager
from config.settings import settings

logger = logging.getLogger(__name__)

chat_bp = Blueprint("chat", __name__, url_prefix="/api/chat")

# ── Gemini client ─────────────────────────────────────────────────────────────
_gemini_client = None

def get_gemini():
    global _gemini_client
    if _gemini_client is None:
        _gemini_client = genai.Client(api_key=settings.gemini_api_key)
    return _gemini_client


# ── Helper: serialize ObjectId / datetime ─────────────────────────────────────
def _clean(doc: dict) -> dict:
    out = {}
    for k, v in doc.items():
        if isinstance(v, ObjectId):
            out[k] = str(v)
        elif isinstance(v, datetime):
            out[k] = v.isoformat()
        elif isinstance(v, dict):
            out[k] = _clean(v)
        elif isinstance(v, list):
            out[k] = [
                _clean(i) if isinstance(i, dict)
                else (str(i) if isinstance(i, ObjectId) else i)
                for i in v
            ]
        else:
            out[k] = v
    return out


# ── Helper: build a readable text summary of a report ────────────────────────
def _report_to_text(report: dict) -> str:
    """
    Converts a MongoDB report document into a plain-text block
    that Gemini can reason about.
    """
    analysis = report.get("analysis", {})
    lines = []

    lines.append(f"Report ID     : {report.get('_id', 'N/A')}")
    lines.append(f"Report Type   : {report.get('report_type', 'N/A')}")
    lines.append(f"Platform      : {report.get('platform', 'N/A')}")
    lines.append(f"Category      : {report.get('category', 'N/A')}")
    lines.append(f"Generated At  : {report.get('generated_at', 'N/A')}")
    lines.append(f"Products Analysed: {report.get('products_analyzed', 'N/A')}")
    lines.append("")

    # ── Quick analysis fields ──────────────────────────────────────────────
    pr = analysis.get("price_range", {})
    if pr:
        lines.append("── Price Range ──")
        lines.append(f"  Min     : ₹{pr.get('min', 'N/A')}")
        lines.append(f"  Max     : ₹{pr.get('max', 'N/A')}")
        lines.append(f"  Average : ₹{pr.get('average', 'N/A')}")
        lines.append("")

    top = analysis.get("top_rated_product", {})
    if top:
        lines.append("── Top Rated Product ──")
        lines.append(f"  Title  : {top.get('title', 'N/A')}")
        lines.append(f"  Rating : {top.get('rating', 'N/A')}")
        lines.append(f"  Price  : ₹{top.get('price', 'N/A')}")
        lines.append("")

    best = analysis.get("best_value_product", {})
    if best:
        lines.append("── Best Value Product ──")
        lines.append(f"  Title  : {best.get('title', 'N/A')}")
        lines.append(f"  Reason : {best.get('reason', 'N/A')}")
        lines.append("")

    insights = analysis.get("price_insights", [])
    if insights:
        lines.append("── Price Insights ──")
        for ins in insights:
            lines.append(f"  • {ins}")
        lines.append("")

    recs = analysis.get("recommendations", [])
    if recs:
        lines.append("── Recommendations ──")
        for i, rec in enumerate(recs, 1):
            lines.append(f"  {i}. {rec}")
        lines.append("")

    # ── Deep analysis (CrewAI) fields ─────────────────────────────────────
    agent_outputs = analysis.get("agent_outputs", [])
    if agent_outputs:
        lines.append("── Agent Analysis ──")
        for ao in agent_outputs:
            lines.append(f"\n[ {ao.get('agent', 'Agent')} ]")
            lines.append(ao.get("output", ""))
        lines.append("")

    final = analysis.get("final_report", "")
    if final:
        lines.append("── Final Report ──")
        lines.append(final)

    return "\n".join(lines)


# ── Helper: build Gemini messages from history ────────────────────────────────
def _build_prompt(report_text: str, history: list, user_message: str) -> str:
    """
    Builds the full prompt string sent to Gemini.
    history = [{ "role": "user"|"assistant", "content": "..." }, ...]
    """
    system = f"""You are a smart retail business analyst assistant.
The user is chatting about a specific retail intelligence report. 
Your job is to answer questions, summarise sections, compare metrics, 
and give actionable advice — all strictly based on the report data below.

You also understand Hinglish (mixed Hindi-English). Reply in the same 
language style the user uses (if they write in Hinglish, reply in Hinglish; 
if English, reply in English).

Rules:
- Only use information from the report. Do not make up data.
- Be concise but complete.
- If the user asks something not covered in the report, say so clearly.
- Format numbers with ₹ symbol and commas where relevant.

━━━━━━━━━━━━━━ REPORT DATA ━━━━━━━━━━━━━━
{report_text}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

    conversation = []
    for msg in history:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        if role == "user":
            conversation.append(f"User: {content}")
        else:
            conversation.append(f"Assistant: {content}")

    conversation.append(f"User: {user_message}")
    conversation.append("Assistant:")

    return system + "\n\n" + "\n\n".join(conversation)


# ══════════════════════════════════════════════════════════════════════════════
# ENDPOINT 1 — GET /api/chat/reports
# Returns list of all saved reports (id, type, platform, category, date)
# Used by the frontend to populate the report selector
# ══════════════════════════════════════════════════════════════════════════════
@chat_bp.route("/reports", methods=["GET"])
def list_reports():
    try:
        raw = list(
            db_manager.reports.find(
                {"report_type": {"$in": ["quick_analysis", "deep_analysis"]}},
                # Only fetch metadata, NOT the full analysis blob (keeps response small)
                {"_id": 1, "report_type": 1, "platform": 1,
                 "category": 1, "generated_at": 1, "products_analyzed": 1}
            ).sort([("generated_at", -1)]).limit(50)   # Sort by newest first
        )

        total_reports = len(raw)
        reports = []
        for i, r in enumerate(raw):
            report_num = total_reports - i  # Newest gets highest number, oldest gets 1
            reports.append({
                "id"               : str(r["_id"]),
                "report_number"    : report_num,                  # e.g., "Report 5" for newest
                "report_type"      : r.get("report_type", "N/A"),
                "platform"         : r.get("platform", "all"),
                "category"         : r.get("category", "all"),
                "products_analyzed": r.get("products_analyzed", 0),
                "generated_at"     : r["generated_at"].isoformat()
                                     if isinstance(r.get("generated_at"), datetime)
                                     else str(r.get("generated_at", "")),
                # Human-readable label shown in the UI dropdown / sidebar
                "label"            : (
                    f"Report {report_num} — "
                    f"{r.get('report_type','').replace('_',' ').title()} | "
                    f"{r.get('platform','all').upper()} | "
                    f"{r.get('category','all').capitalize()}"
                )
            })

        return jsonify({"reports": reports, "total": len(reports)})

    except Exception as e:
        logger.error(f"list_reports error: {e}")
        return jsonify({"error": str(e)}), 500


# ══════════════════════════════════════════════════════════════════════════════
# ENDPOINT 2 — POST /api/chat
# Body: { "message": str, "report_id": str, "history": [...] }
# Returns: { "reply": str, "report_id": str }
# ══════════════════════════════════════════════════════════════════════════════
@chat_bp.route("", methods=["POST"])
def chat():
    body = request.get_json() or {}

    user_message = body.get("message", "").strip()
    report_id    = body.get("report_id", "").strip()
    history      = body.get("history", [])   # list of {role, content}

    # ── Validate ──────────────────────────────────────────────────────────
    if not user_message:
        return jsonify({"error": "message is required"}), 400

    if not report_id:
        return jsonify({"error": "report_id is required. Ask the user to select a report first."}), 400

    # ── Fetch report from MongoDB ─────────────────────────────────────────
    try:
        report = db_manager.reports.find_one({"_id": ObjectId(report_id)})
    except Exception:
        return jsonify({"error": "Invalid report_id format"}), 400

    if not report:
        return jsonify({"error": f"No report found with id: {report_id}"}), 404

    report = _clean(report)

    # ── Convert report to readable text ───────────────────────────────────
    report_text = _report_to_text(report)

    # ── Build prompt with full conversation history ────────────────────────
    prompt = _build_prompt(report_text, history, user_message)

    # ── Call Gemini ───────────────────────────────────────────────────────
    try:
        client   = get_gemini()
        response = client.models.generate_content(
            model="models/gemini-2.5-flash",
            contents=prompt
        )
        reply = response.text.strip()
    except Exception as e:
        logger.error(f"Gemini error: {e}")
        return jsonify({"error": f"AI error: {str(e)}"}), 500

    return jsonify({
        "reply"    : reply,
        "report_id": report_id,
    })


# ══════════════════════════════════════════════════════════════════════════════
# ENDPOINT 3 — POST /api/chat/upload-pdf
# Accepts a multipart/form-data PDF upload, runs RAG ingestion,
# returns { session_id, filename, page_count, chunk_count }
# Nothing is persisted to MongoDB or disk — entirely ephemeral.
# ══════════════════════════════════════════════════════════════════════════════
@chat_bp.route("/upload-pdf", methods=["POST"])
def upload_pdf():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded. Send the PDF as form field 'file'."}), 400

    f = request.files["file"]
    if not f.filename:
        return jsonify({"error": "Empty filename."}), 400
    if not f.filename.lower().endswith(".pdf"):
        return jsonify({"error": "Only PDF files are supported."}), 400

    pdf_bytes = f.read()
    if len(pdf_bytes) > 20 * 1024 * 1024:   # 20 MB cap
        return jsonify({"error": "PDF too large (max 20 MB)."}), 413

    try:
        from src.utils.rag_pdf_chat import ingest_pdf, get_session_info
        session_id = ingest_pdf(pdf_bytes, f.filename)
        info       = get_session_info(session_id)
        return jsonify({
            "session_id":  session_id,
            "filename":    info["filename"],
            "page_count":  info["page_count"],
            "chunk_count": info["chunk_count"],
        })
    except ValueError as e:
        return jsonify({"error": str(e)}), 422
    except Exception as e:
        logger.error(f"upload_pdf error: {e}", exc_info=True)
        return jsonify({"error": f"Ingestion failed: {str(e)}"}), 500


# ══════════════════════════════════════════════════════════════════════════════
# ENDPOINT 4 — POST /api/chat/pdf
# Body: { "message": str, "session_id": str, "history": [...] }
# Returns: { "reply": str, "session_id": str }
# ══════════════════════════════════════════════════════════════════════════════
@chat_bp.route("/pdf", methods=["POST"])
def chat_pdf():
    body = request.get_json() or {}

    user_message = body.get("message", "").strip()
    session_id   = body.get("session_id", "").strip()
    history      = body.get("history", [])

    if not user_message:
        return jsonify({"error": "message is required"}), 400
    if not session_id:
        return jsonify({"error": "session_id is required"}), 400

    try:
        from src.utils.rag_pdf_chat import answer
        reply = answer(session_id, user_message, history)
        return jsonify({"reply": reply, "session_id": session_id})
    except KeyError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        logger.error(f"chat_pdf error: {e}", exc_info=True)
        return jsonify({"error": f"AI error: {str(e)}"}), 500


# ══════════════════════════════════════════════════════════════════════════════
# ENDPOINT 5 — DELETE /api/chat/pdf/<session_id>
# Immediately frees the in-memory session (optional — called on tab clear)
# ══════════════════════════════════════════════════════════════════════════════
@chat_bp.route("/pdf/<session_id>", methods=["DELETE"])
def delete_pdf_session(session_id):
    from src.utils.rag_pdf_chat import delete_session
    deleted = delete_session(session_id)
    return jsonify({"deleted": deleted})