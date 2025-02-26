# main.py
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uvicorn
import os
from fastapi.middleware.cors import CORSMiddleware
from function import urlSpliter, load_retriever, Rag, ollama, textToEmbedding

app = FastAPI()
# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust origins as needed in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class EmbeddingPayload(BaseModel):
    url: str

class QuestionPayload(BaseModel):
    question: str

class OllamaPayload(BaseModel):
    prompt: str

class TextPathPayload(BaseModel):
    file_path: str

@app.post("/create_embeddings")
async def create_embeddings(payload: EmbeddingPayload):
    try:
        urlSpliter(payload.url)
        return {"message": "Embeddings created successfully from the provided URL."}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to create embeddings: {str(e)}")

@app.post("/rag")
async def process_rag(payload: QuestionPayload):
    try:
        retriever = load_retriever()
        answer = Rag(payload.question, retriever)
        return {"rag_answer": answer}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"RAG processing failed: {str(e)}")

@app.post("/ollama")
async def get_ollama(payload: OllamaPayload):
    try:
        result = ollama(payload.prompt)
        return {"result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ollama processing failed: {str(e)}")

@app.post("/text_to_embedding")
async def text_to_embedding(payload: TextPathPayload):
    try:
        if not os.path.exists(payload.file_path):
            raise HTTPException(status_code=404, detail=f"File not found: {payload.file_path}")
            
        textToEmbedding(payload.file_path)
        return {"message": f"Text file at {payload.file_path} has been successfully embedded."}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to process text file: {str(e)}")

@app.post("/upload_and_embed")
async def upload_and_embed(file: UploadFile = File(...)):
    if not file:
        raise HTTPException(status_code=400, detail="No file provided")
        
    temp_file_path = f"temp_{file.filename}"
    try:
        with open(temp_file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        textToEmbedding(temp_file_path)
        
        os.remove(temp_file_path)
        
        return {"message": f"File {file.filename} has been successfully embedded."}
    except Exception as e:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        raise HTTPException(status_code=400, detail=f"Failed to process uploaded file: {str(e)}")

# Add a simple health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run(app, host="localhost", port=8000)