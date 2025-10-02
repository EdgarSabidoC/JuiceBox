import os
import uvicorn
from dotenv import load_dotenv

# Carga las variables desde .env
dotenv_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(dotenv_path=dotenv_path)

if __name__ == "__main__":
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", 8000))
    debug = os.getenv("DEBUG", "false").lower() == "true"

    uvicorn.run(
        "WebClient.main:app",
        host=host,
        port=port,
        reload=debug,
    )
