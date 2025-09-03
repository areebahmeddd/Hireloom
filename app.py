import os
import uvicorn
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
from database import db_init

app = FastAPI(title="Hireloom API", description="", version="1.0.0")


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
            file_content = await resume.read()
            temp_file.write(file_content)
            temp_path = temp_file.name

        try:
            parse_result = parse_resume(job_description, temp_path)
            return JSONResponse(content=parse_result)

        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

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
    request_body = await request.json()
    send_result = send_message(request_body["message"])
    return JSONResponse(content=send_result)


@app.get("/candidates/{candidate_name}")
async def search_candidate(candidate_name: str):
    firestore_db = db_init()
    doc_id = candidate_name.replace(" ", "_")
    doc_ref = firestore_db.collection("resumes").document(doc_id)
    candidate_doc = doc_ref.get()
    if candidate_doc.exists:
        return JSONResponse(content=candidate_doc.to_dict())
    else:
        raise HTTPException(status_code=404, detail="Candidate not found")


@app.delete("/candidates/{candidate_name}")
async def delete_candidate(candidate_name: str):
    firestore_db = db_init()
    doc_id = candidate_name.replace(" ", "_")
    doc_ref = firestore_db.collection("resumes").document(doc_id)
    if doc_ref.get().exists:
        doc_ref.delete()
        return {"message": f"Candidate '{candidate_name}' deleted."}
    else:
        raise HTTPException(status_code=404, detail="Candidate not found")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
