import uvicorn
import os
import tempfile
from fastapi import FastAPI, BackgroundTasks, File, UploadFile, Form, HTTPException
from fastapi.responses import JSONResponse
from agents.call import call_handler, list_handler
from agents.parser import parse_resume

app = FastAPI(title="Hireloom", description="", version="1.0.0")


@app.get("/")
async def root():
    return {"message": "Server OK"}


@app.post("/make_call")
async def make_call(background_tasks: BackgroundTasks):
    return await call_handler(background_tasks)


@app.get("/get_recordings")
async def get_recordings():
    return list_handler()


@app.post("/parse_resume")
async def parse_resume_endpoint(
    resume_pdf: UploadFile = File(...),
    job_description: str = Form(...)
):
    try:
        if not resume_pdf.filename.lower().endswith('.pdf'):
            raise HTTPException(status_code=400, detail="File must be a PDF")
        
        if not job_description.strip():
            raise HTTPException(status_code=400, detail="Job description cannot be empty")
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
            content = await resume_pdf.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        try:
            result = parse_resume(job_description, temp_file_path)
            return JSONResponse(content=result)
        
        finally:
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing resume: {str(e)}")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
