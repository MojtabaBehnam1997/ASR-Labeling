from fastapi import FastAPI, UploadFile, File, HTTPException
import os
import uuid
from typing import List
import sqlalchemy
from databases import Database
import time
from sqlalchemy.exc import OperationalError

# Database setup with retry
DATABASE_URL = "postgresql://admin:secret@db/asr_labeling"
database = Database(DATABASE_URL)
metadata = sqlalchemy.MetaData()

def create_db_engine():
    max_retries = 5
    retry_delay = 5
    
    for attempt in range(max_retries):
        try:
            engine = sqlalchemy.create_engine(DATABASE_URL)
            engine.connect()
            return engine
        except OperationalError:
            if attempt == max_retries - 1:
                raise
            print(f"Database connection failed (attempt {attempt + 1}), retrying...")
            time.sleep(retry_delay)

engine = create_db_engine()

# Models
audio_files = sqlalchemy.Table(
    "audio_files",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.String, primary_key=True),
    sqlalchemy.Column("filename", sqlalchemy.String),
    sqlalchemy.Column("filepath", sqlalchemy.String),
    sqlalchemy.Column("uploaded_by", sqlalchemy.String),
)

metadata.create_all(engine)

app = FastAPI()

@app.on_event("startup")
async def startup():
    await database.connect()
    try:
        await database.execute("SELECT 1")
    except Exception as e:
        print(f"Database connection error: {e}")
        raise

def save_audio_file(file: UploadFile):
    file_id = str(uuid.uuid4())
    upload_folder = os.getenv("AUDIO_UPLOAD_FOLDER", "/data/audio_files")
    os.makedirs(upload_folder, exist_ok=True)
    
    file_extension = file.filename.split(".")[-1]
    filename = f"{file_id}.{file_extension}"
    filepath = os.path.join(upload_folder, filename)
    
    with open(filepath, "wb") as buffer:
        buffer.write(file.file.read())
    
    return {"id": file_id, "filename": file.filename, "filepath": filepath}

@app.post("/upload/")
async def upload_audio(file: UploadFile = File(...)):
    file_data = save_audio_file(file)
    query = audio_files.insert().values(
        id=file_data["id"],
        filename=file_data["filename"],
        filepath=file_data["filepath"],
        uploaded_by="admin"
    )
    await database.execute(query)
    return {"message": "File uploaded successfully", "file_id": file_data["id"]}

@app.get("/files/", response_model=List[dict])
async def get_files():
    query = audio_files.select()
    return await database.fetch_all(query)