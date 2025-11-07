import uvicorn

if __name__ == "__main__":
    # Use the import string for the app instance
    uvicorn.run("fastapi_app:app", host="0.0.0.0", port=8001, reload=True)
