from fastapi import FastAPI

app = FastAPI(title="La Juana API")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
