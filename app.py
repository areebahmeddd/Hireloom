import uvicorn
import os
import tempfile
from fastapi import (
    FastAPI,
    BackgroundTasks,
    Request,
    File,
    UploadFile,
    Form,
    HTTPException,
)
from fastapi.responses import JSONResponse
from agents.parser import parse_resume
from agents.message import send_message
from agents.call import call_handler, list_handler
from agents.database import init_firestore

app = FastAPI(title="Hireloom", description="", version="1.0.0")


@app.get("/candidates/{candidate_name}")
async def search_candidate(candidate_name: str):
    db = init_firestore()
    doc_id = candidate_name.replace(" ", "_")
    doc_ref = db.collection("resumes").document(doc_id)
    doc = doc_ref.get()
    if doc.exists:
        return JSONResponse(content=doc.to_dict())
    else:
        raise HTTPException(status_code=404, detail="Candidate not found")

@app.delete("/candidates/{candidate_name}")
async def delete_candidate(candidate_name: str):
    db = init_firestore()
    doc_id = candidate_name.replace(" ", "_")
    doc_ref = db.collection("resumes").document(doc_id)
    if doc_ref.get().exists:
        doc_ref.delete()
        return {"message": f"Candidate '{candidate_name}' deleted."}
    else:
        raise HTTPException(status_code=404, detail="Candidate not found")


@app.get("/")
async def root():
    return {"message": "Server OK"}


@app.post("/parse_resume")
async def parse_endpoint(
    resume: UploadFile = File(...), job_description: str = Form(...)
):
    try:
        if not resume.filename.lower().endswith(".pdf"):
            raise HTTPException(status_code=400, detail="File must be a PDF")

        if not job_description.strip():
            raise HTTPException(
                status_code=400, detail="Job description cannot be empty"
            )

        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
            content = await resume.read()
            temp_file.write(content)
            temp_file_path = temp_file.name

        try:
            result = parse_resume(job_description, temp_file_path)
            return JSONResponse(content=result)

        finally:
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error processing resume: {str(e)}"
        )


@app.post("/make_call")
async def make_call(tasks: BackgroundTasks):
    return await call_handler(tasks)


@app.get("/get_recordings")
async def get_recordings():
    return list_handler()


@app.post("/send_message")
async def send_endpoint(request: Request):
    body = await request.json()
    result = send_message(body["message"])
    return JSONResponse(content=result)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
