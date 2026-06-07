import os
import pandas as pd
from typing import TypedDict, Annotated, Sequence, Any
import operator
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langgraph.graph import StateGraph, END
from langchain_groq import ChatGroq
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_mistralai import ChatMistralAI
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
import chromadb
import json
import fitz # PyMuPDF
import docx

class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    filepath: str
    dataframe: Any # pd.DataFrame or None
    is_structured: bool
    summary_stats: str
    insights: str
    charts_json: str
    dataset_id: int
    text_chunks: list

def get_llm():
    groq_llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)
    mistral_llm = ChatMistralAI(model="mistral-large-latest", temperature=0, mistral_api_key=os.getenv("MISTRAL_API_KEY"))
    google_key = os.getenv("GOOGLE_API_KEY")
    if google_key:
        print("Initializing Google Gemini model for background agent with fallbacks...")
        pro_llm = ChatGoogleGenerativeAI(model="gemini-1.5-pro-latest", temperature=0, google_api_key=google_key)
        flash_llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash-latest", temperature=0, google_api_key=google_key)
        return pro_llm.with_fallbacks([flash_llm, groq_llm, mistral_llm])
    return groq_llm.with_fallbacks([mistral_llm])

llm = get_llm()

def get_chroma_client():
    return chromadb.HttpClient(
        host=os.getenv("CHROMA_HOST", "localhost"),
        ssl=True if os.getenv("CHROMA_HOST") != "localhost" else False,
        headers={
            "x-chroma-token": os.getenv("CHROMA_API_KEY", "")
        },
        tenant=os.getenv("CHROMA_TENANT", "default_tenant"),
        database=os.getenv("CHROMA_DATABASE", "default_database")
    )

print("Loading global HuggingFaceEmbeddings in analyst_agent...")
global_embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
print("Global embeddings loaded.")

def load_data(state: AgentState):
    """Loads either structured data (CSV/Excel) or unstructured text (PDF, DOCX, TXT)."""
    filepath = state["filepath"]
    if filepath.endswith(('.csv', '.xlsx', '.xls')):
        df = pd.read_csv(filepath) if filepath.endswith('.csv') else pd.read_excel(filepath)
        for col in df.columns:
            if pd.api.types.is_numeric_dtype(df[col]):
                df[col] = df[col].fillna(df[col].median())
            else:
                df[col] = df[col].fillna(df[col].mode()[0] if not df[col].mode().empty else "Unknown")
        return {"dataframe": df, "is_structured": True, "messages": [AIMessage(content="Structured data loaded.")]}
    else:
        text = ""
        if filepath.endswith('.pdf'):
            doc = fitz.open(filepath)
            for page in doc:
                text += page.get_text()
        elif filepath.endswith('.docx'):
            doc = docx.Document(filepath)
            for para in doc.paragraphs:
                text += para.text + "\n"
        else:
            with open(filepath, 'r', encoding='utf-8') as f:
                text = f.read()
                
        splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
        chunks = splitter.split_text(text)
        return {"dataframe": None, "is_structured": False, "text_chunks": chunks, "summary_stats": f"Document with {len(chunks)} text chunks.", "messages": [AIMessage(content="Unstructured data loaded.")]}

def perform_eda(state: AgentState):
    if not state["is_structured"]:
        return {"messages": []}
    
    df = state["dataframe"]
    summary = df.describe(include='all').to_string()
    return {"summary_stats": summary, "messages": [AIMessage(content="EDA completed.")]}

def generate_insights(state: AgentState):
    if state["is_structured"]:
        prompt = f"""
        You are an expert AI Data Analyst. Analyze the following summary statistics of a dataset and provide key business insights, anomalies, and observations.
        Summary Statistics:
        {state['summary_stats']}
        Provide a concise, bulleted list of 3-5 key insights.
        """
        response = llm.invoke([HumanMessage(content=prompt)])
        insights = response.content
    else:
        insights = f"Extracted Document. The document has been split into {len(state['text_chunks'])} searchable segments for question answering."
        
    return {"insights": insights, "messages": [AIMessage(content="Insights generated.")]}

def store_insights_in_vectordb(state: AgentState):
    try:
        client = get_chroma_client()
        collection = client.get_or_create_collection(name="dataset_insights")
        
        if state["is_structured"]:
            df = state["dataframe"]
            raw_schema = f"Columns: {list(df.columns)}\nTypes: {df.dtypes.to_dict()}"
            full_document = f"Raw Schema:\n{raw_schema}\n\nSummary Statistics:\n{state['summary_stats']}\n\nGenerated Insights:\n{state['insights']}"
            
            vector = global_embeddings.embed_query(full_document)
            collection.add(
                ids=[f"dataset_{state['dataset_id']}_insights"],
                embeddings=[vector],
                documents=[full_document],
                metadatas=[{"dataset_id": state["dataset_id"], "type": "insight"}]
            )
        else:
            ids = [f"dataset_{state['dataset_id']}_chunk_{i}" for i in range(len(state["text_chunks"]))]
            docs = state["text_chunks"]
            metadatas = [{"dataset_id": state["dataset_id"], "type": "document_chunk"} for _ in range(len(docs))]
            # Batch embedding
            embeddings = global_embeddings.embed_documents(docs)
            collection.add(
                ids=ids,
                embeddings=embeddings,
                documents=docs,
                metadatas=metadatas
            )
    except Exception as e:
        print(f"Failed to store in ChromaDB: {e}")
        
    return {"messages": [AIMessage(content="Data stored in Vector DB.")]}

def generate_charts(state: AgentState):
    if not state["is_structured"]:
        return {"charts_json": "[]", "messages": []}
        
    df = state["dataframe"]
    num_cols = df.select_dtypes(include='number').columns.tolist()
    cat_cols = df.select_dtypes(exclude='number').columns.tolist()
    
    charts = []
    if cat_cols and num_cols:
        top_cats = df[cat_cols[0]].value_counts().head(5).to_dict()
        charts.append({
            "type": "bar",
            "title": f"Top 5 {cat_cols[0]}",
            "labels": list(top_cats.keys()),
            "data": list(top_cats.values())
        })
        
    charts_json = json.dumps(charts)
    return {"charts_json": charts_json, "messages": [AIMessage(content="Charts generated.")]}

def run_analysis_agent(filepath: str, dataset_id: int):
    workflow = StateGraph(AgentState)
    
    workflow.add_node("load_data", load_data)
    workflow.add_node("perform_eda", perform_eda)
    workflow.add_node("generate_insights", generate_insights)
    workflow.add_node("store_insights", store_insights_in_vectordb)
    workflow.add_node("generate_charts", generate_charts)
    
    workflow.set_entry_point("load_data")
    workflow.add_edge("load_data", "perform_eda")
    workflow.add_edge("perform_eda", "generate_insights")
    workflow.add_edge("generate_insights", "store_insights")
    workflow.add_edge("store_insights", "generate_charts")
    workflow.add_edge("generate_charts", END)
    
    app = workflow.compile()
    result = app.invoke({"filepath": filepath, "dataset_id": dataset_id, "messages": []})
    return result
