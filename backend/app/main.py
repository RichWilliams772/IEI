from fastapi import FastAPI

app = FastAPI(
    title="Intelligent Energy Monitoring Platform"
)

@app.get("/")
def root():
    return {
        "message": "Energy Monitoring API Running"
    }