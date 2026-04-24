from src.api.app import app

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    print(f"\nRetail Intelligence Platform")
    print(f"-> Running on http://localhost:{port}\n")
    app.run(
        debug=True,
        port=port,
        host="0.0.0.0",
        use_reloader=False
    )