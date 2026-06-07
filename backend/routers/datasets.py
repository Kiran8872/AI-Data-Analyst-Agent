import os
import shutil
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List

import models, schemas, auth, database
from agents.analyst_agent import run_analysis_agent

router = APIRouter(
    prefix="/datasets",
    tags=["datasets"],
    responses={404: {"description": "Not found"}},
)

UPLOAD_DIR = "/tmp/uploads" if os.getenv("VERCEL") == "1" else "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

def process_dataset(dataset_id: int, filepath: str, db: Session):
    try:
        result = run_analysis_agent(filepath, dataset_id)
        report = models.AnalysisReport(
            dataset_id=dataset_id,
            summary=result["insights"],
            charts_json=result["charts_json"]
        )
        db.add(report)
        db.commit()
    except Exception as e:
        print(f"Error processing dataset {dataset_id}: {e}")

@router.post("/upload", response_model=schemas.DatasetResponse)
async def upload_dataset(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    current_user: models.User = Depends(auth.get_current_active_user),
    db: Session = Depends(database.get_db)
):
    if not file.filename.endswith(('.csv', '.xlsx', '.xls', '.pdf', '.txt', '.docx')):
        raise HTTPException(status_code=400, detail="Unsupported file format.")
    
    safe_filename = os.path.basename(file.filename)
    file_location = os.path.join(UPLOAD_DIR, f"{current_user.id}_{safe_filename}")
    
    with open(file_location, "wb+") as file_object:
        shutil.copyfileobj(file.file, file_object)
        
    file_size = os.path.getsize(file_location)
    
    db_dataset = models.Dataset(
        filename=safe_filename,
        filepath=file_location,
        size_bytes=file_size,
        owner_id=current_user.id
    )
    db.add(db_dataset)
    db.commit()
    db.refresh(db_dataset)
    
    # Trigger background analysis
    background_tasks.add_task(process_dataset, db_dataset.id, file_location, database.SessionLocal())
    
    # Audit log
    audit_log = models.AuditLog(
        user_id=current_user.id,
        action="UPLOAD_DATASET",
        details=f"Uploaded {safe_filename}"
    )
    db.add(audit_log)
    db.commit()
    
    return db_dataset


@router.get("/", response_model=List[schemas.DatasetResponse])
def get_user_datasets(
    current_user: models.User = Depends(auth.get_current_active_user),
    db: Session = Depends(database.get_db)
):
    datasets = db.query(models.Dataset).filter(models.Dataset.owner_id == current_user.id).all()
    return datasets

@router.delete("/{dataset_id}")
def delete_dataset(
    dataset_id: int,
    current_user: models.User = Depends(auth.get_current_active_user),
    db: Session = Depends(database.get_db)
):
    dataset = db.query(models.Dataset).filter(models.Dataset.id == dataset_id, models.Dataset.owner_id == current_user.id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    db.delete(dataset)
    db.commit()
    
    if os.path.exists(dataset.filepath):
        try:
            os.remove(dataset.filepath)
        except:
            pass
            
    return {"message": "Dataset deleted"}

import pandas as pd
import json
import re
from collections import Counter
from textblob import TextBlob
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage

@router.get("/{dataset_id}/data")
def get_dataset_data(
    dataset_id: int,
    current_user: models.User = Depends(auth.get_current_active_user),
    db: Session = Depends(database.get_db)
):
    dataset = db.query(models.Dataset).filter(models.Dataset.id == dataset_id, models.Dataset.owner_id == current_user.id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    if not os.path.exists(dataset.filepath):
        raise HTTPException(status_code=404, detail="Data file not found on disk")
        
    try:
        if dataset.filepath.endswith('.csv'):
            df = pd.read_csv(dataset.filepath, nrows=100)
        else:
            df = pd.read_excel(dataset.filepath, nrows=100)
            
        # Convert timestamp/datetime objects to string to prevent JSON serialization errors
        df = df.fillna("")
        for col in df.select_dtypes(include=['datetime64', 'datetimetz']).columns:
            df[col] = df[col].astype(str)
            
        return {"columns": list(df.columns), "data": df.to_dict(orient="records")}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{dataset_id}/profile")
def get_dataset_profile(
    dataset_id: int,
    current_user: models.User = Depends(auth.get_current_active_user),
    db: Session = Depends(database.get_db)
):
    dataset = db.query(models.Dataset).filter(models.Dataset.id == dataset_id, models.Dataset.owner_id == current_user.id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    if not os.path.exists(dataset.filepath):
        raise HTTPException(status_code=404, detail="Data file not found on disk")
        
    try:
        if dataset.filepath.endswith('.csv'):
            df = pd.read_csv(dataset.filepath)
        else:
            df = pd.read_excel(dataset.filepath)
            
        columns_stats = []
        for col in df.columns:
            series = df[col]
            stat = {
                "name": col,
                "type": str(series.dtype),
                "null_count": int(series.isnull().sum()),
                "unique_count": int(series.nunique())
            }
            if pd.api.types.is_numeric_dtype(series):
                stat["min"] = float(series.min()) if pd.notnull(series.min()) else None
                stat["max"] = float(series.max()) if pd.notnull(series.max()) else None
                stat["mean"] = float(series.mean()) if pd.notnull(series.mean()) else None
            else:
                stat["min"] = None
                stat["max"] = None
                stat["mean"] = None
                
            columns_stats.append(stat)
            
        return {
            "total_rows": len(df),
            "total_columns": len(df.columns),
            "columns": columns_stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{dataset_id}")
def get_dataset(
    dataset_id: int,
    current_user: models.User = Depends(auth.get_current_active_user),
    db: Session = Depends(database.get_db)
):
    dataset = db.query(models.Dataset).filter(models.Dataset.id == dataset_id, models.Dataset.owner_id == current_user.id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    return dataset

@router.post("/{dataset_id}/clean")
def clean_dataset(
    dataset_id: int,
    current_user: models.User = Depends(auth.get_current_active_user),
    db: Session = Depends(database.get_db)
):
    dataset = db.query(models.Dataset).filter(models.Dataset.id == dataset_id, models.Dataset.owner_id == current_user.id).first()
    if not dataset or not os.path.exists(dataset.filepath):
        raise HTTPException(status_code=404, detail="Dataset not found")
        
    try:
        if dataset.filepath.endswith('.csv'):
            df = pd.read_csv(dataset.filepath)
        else:
            df = pd.read_excel(dataset.filepath)
            
        initial_rows = len(df)
        df.drop_duplicates(inplace=True)
        
        for col in df.columns:
            if pd.api.types.is_numeric_dtype(df[col]):
                df[col] = df[col].fillna(df[col].mean())
            else:
                df[col] = df[col].fillna("Unknown")
                
        final_rows = len(df)
        
        if dataset.filepath.endswith('.csv'):
            df.to_csv(dataset.filepath, index=False)
        else:
            df.to_excel(dataset.filepath, index=False)
            
        dataset.size_bytes = os.path.getsize(dataset.filepath)
        db.commit()
        
        return {"message": "Cleaned successfully", "rows_removed": initial_rows - final_rows, "final_rows": final_rows}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{dataset_id}/sentiment")
def analyze_sentiment(
    dataset_id: int,
    current_user: models.User = Depends(auth.get_current_active_user),
    db: Session = Depends(database.get_db)
):
    dataset = db.query(models.Dataset).filter(models.Dataset.id == dataset_id, models.Dataset.owner_id == current_user.id).first()
    if not dataset or not os.path.exists(dataset.filepath):
        raise HTTPException(status_code=404, detail="Dataset not found")
        
    try:
        df = pd.read_csv(dataset.filepath) if dataset.filepath.endswith('.csv') else pd.read_excel(dataset.filepath)
        
        # Find string columns
        text_cols = df.select_dtypes(include=['object', 'string']).columns
        if len(text_cols) == 0:
            return {"status": "no_text_columns"}
            
        # Select the column that most likely contains feedback (or just the first one with longest average strings)
        target_col = None
        max_avg_len = 0
        for col in text_cols:
            avg_len = df[col].astype(str).str.len().mean()
            if avg_len > max_avg_len:
                max_avg_len = avg_len
                target_col = col
                
        if max_avg_len < 10:
            return {"status": "no_suitable_text_columns"}
            
        positive = 0
        neutral = 0
        negative = 0
        
        stop_words = {"the", "and", "is", "in", "it", "to", "of", "this", "that", "for", "with", "as", "on", "are", "was", "but", "not", "have", "from", "they"}
        words = []
        
        for text in df[target_col].dropna().astype(str).head(500): # Limit to 500 for performance
            if len(text.strip()) == 0 or text == "Unknown": continue
            polarity = TextBlob(text).sentiment.polarity
            if polarity > 0.1:
                positive += 1
            elif polarity < -0.1:
                negative += 1
            else:
                neutral += 1
                
            clean_text = re.sub(r'[^a-zA-Z\s]', '', text.lower())
            for w in clean_text.split():
                if len(w) > 3 and w not in stop_words:
                    words.append(w)
                    
        top_keywords = [word for word, count in Counter(words).most_common(5)]
                
        return {
            "status": "success",
            "column": target_col,
            "sentiment": {
                "positive": positive,
                "neutral": neutral,
                "negative": negative
            },
            "keywords": top_keywords
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{dataset_id}/summary")
def get_dataset_summary(
    dataset_id: int,
    current_user: models.User = Depends(auth.get_current_active_user),
    db: Session = Depends(database.get_db)
):
    dataset = db.query(models.Dataset).filter(models.Dataset.id == dataset_id, models.Dataset.owner_id == current_user.id).first()
    if not dataset or not os.path.exists(dataset.filepath):
        raise HTTPException(status_code=404, detail="Dataset not found")
        
    try:
        df = pd.read_csv(dataset.filepath) if dataset.filepath.endswith('.csv') else pd.read_excel(dataset.filepath)
        cols = list(df.columns)
        row_count = len(df)
        
        prompt = f"Write a 2-sentence executive summary describing a dataset named '{dataset.filename}'. It has {row_count} rows and the following columns: {', '.join(cols)}. Make it sound highly professional and insightful. Do not include markdown formatting or quotes."
        
        llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash")
        response = llm.invoke([HumanMessage(content=prompt)])
        
        return {"summary": response.content.strip()}
    except Exception as e:
        return {"summary": "An automated AI summary is currently unavailable for this dataset."}
