import os
import logging
from fastapi import FastAPI, Request, Query
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from blog_post_factory.graph import graph_app as blog_post_app
import asyncio
import json
from pathlib import Path
from fastapi.concurrency import run_in_threadpool

def create_app():
    app = FastAPI()

    current_dir = Path(__file__).parent

    app.mount("/static", StaticFiles(directory=current_dir / "static"), name="static")

    # Configure logging
    logging.basicConfig(level=logging.INFO)

    templates = Jinja2Templates(directory=current_dir / "templates")

    @app.get("/", response_class=HTMLResponse)
    async def read_root(request: Request):
        logging.info("Serving index.html")
        return templates.TemplateResponse("index.html", {"request": request})

    # The rest of your endpoints and logic remain the same, just indented
    # within the create_app function.

    @app.get("/generate")
    async def generate(topic: str = Query(...)):
        logging.info(f"Received topic for generation: {topic}")
        
        async def event_generator():
            inputs = {"topic": topic}
            post_content = ""
            # Use run_in_threadpool to iterate over the synchronous stream
            for event in await run_in_threadpool(blog_post_app.stream, inputs):
                for key, value in event.items(): # Each `event` is a dict from the graph stream
                    if key == "reviewer" and "post" in value:
                        new_content = value["post"][len(post_content):]
                        if new_content:
                            post_content = value["post"]
                            yield f"data: {json.dumps({'type': 'post_update', 'content': new_content})}\n\n"
                    elif isinstance(value, dict) and "status" in value:
                        # This will capture status updates from any node
                        status = value['status']
                        step = value.get('current_step', '...')
                        yield f"data: {json.dumps({'type': 'status_update', 'status': status, 'step': step})}\n\n"
                        # If the review is complete, this is our last meaningful status before 'end'
                        if key == "reviewer" and status == "Review complete":
                            await asyncio.sleep(0.1) # Give client time to process
                await asyncio.sleep(0.02)
            yield f"data: {json.dumps({'type': 'end'})}\n\n"

        return StreamingResponse(event_generator(), media_type="text/event-stream")
    
    return app
    
app = create_app()
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("fastapi_app:app", host="0.0.0.0", port=8001, reload=True)