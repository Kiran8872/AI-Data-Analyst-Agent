import time
import os
import pandas as pd
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
import chromadb
from langchain_google_genai import GoogleGenerativeAIEmbeddings
import json
import uuid
from typing import List

import models, auth, database, schemas, file_storage
from langchain_groq import ChatGroq
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_experimental.agents.agent_toolkits import create_pandas_dataframe_agent
from langchain_core.messages import HumanMessage, AIMessage
from langchain_mistralai import ChatMistralAI

GOOGLE_EMBEDDING_MODEL = os.getenv("GOOGLE_EMBEDDING_MODEL", "models/gemini-embedding-001")

router = APIRouter(
    prefix="/chat",
    tags=["chat"],
)

class ChatRequest(BaseModel):
    dataset_ids: List[int]
    question: str
    session_id: str | None = None

class ChatResponse(BaseModel):
    answer: str
    session_id: str

def get_llm():
    # Use global models with fallback
    groq_llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)
    mistral_llm = ChatMistralAI(model="mistral-large-latest", temperature=0, mistral_api_key=os.getenv("MISTRAL_API_KEY"))
    
    google_key = os.getenv("GOOGLE_API_KEY")
    if google_key:
        pro_llm = ChatGoogleGenerativeAI(model="gemini-1.5-pro-latest", temperature=0, google_api_key=google_key)
        flash_llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash-latest", temperature=0, google_api_key=google_key)
        return pro_llm.with_fallbacks([flash_llm, groq_llm, mistral_llm])
    
    return groq_llm.with_fallbacks([mistral_llm])

llm = get_llm()

FORBIDDEN_PHRASES = [
    "ignore all previous instructions",
    "you are not a data analyst",
    "drop table",
    "system prompt",
    "bypass",
    "import os",
    "subprocess",
    "sys.",
    "__import__",
    "eval(",
    "exec(",
    "os.system"
]

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

# Lazy-initialized embeddings are loaded on first use, not at import time
# Uses Google's API so no local model is downloaded (saves 400MB+ RAM)
_embeddings = None

def get_embeddings():
    global _embeddings
    if _embeddings is None:
        google_key = os.getenv("GOOGLE_API_KEY")
        if google_key:
            _embeddings = GoogleGenerativeAIEmbeddings(
                model=GOOGLE_EMBEDDING_MODEL,
                google_api_key=google_key
            )
        else:
            # Fallback: use Groq LLM to generate a simple keyword embedding
            raise RuntimeError("GOOGLE_API_KEY is required for embeddings")
    return _embeddings

@router.get("/sessions", response_model=List[schemas.ChatSessionResponse])
def get_chat_sessions(
    current_user: models.User = Depends(auth.get_current_active_user),
    db: Session = Depends(database.get_db)
):
    # Fetch all user messages to determine sessions
    messages = db.query(models.Message).filter(
        models.Message.user_id == current_user.id,
        models.Message.role == "user"
    ).order_by(models.Message.created_at.asc()).all()
    
    sessions = {}
    for m in messages:
        if m.session_id not in sessions:
            title = m.content[:30] + "..." if len(m.content) > 30 else m.content
            sessions[m.session_id] = {
                "session_id": m.session_id,
                "dataset_ids": m.dataset_ids,
                "title": title,
                "created_at": m.created_at
            }
            
    return list(sessions.values())

@router.get("/history/{session_id}", response_model=List[schemas.MessageResponse])
def get_chat_history(
    session_id: str,
    current_user: models.User = Depends(auth.get_current_active_user),
    db: Session = Depends(database.get_db)
):
    messages = db.query(models.Message).filter(
        models.Message.session_id == session_id,
        models.Message.user_id == current_user.id
    ).order_by(models.Message.created_at.asc()).all()
    return messages

@router.delete("/sessions/{session_id}")
def delete_chat_session(
    session_id: str,
    current_user: models.User = Depends(auth.get_current_active_user),
    db: Session = Depends(database.get_db)
):
    messages = db.query(models.Message).filter(
        models.Message.session_id == session_id,
        models.Message.user_id == current_user.id
    ).all()
    
    if not messages:
        raise HTTPException(status_code=404, detail="Session not found")
        
    for m in messages:
        db.delete(m)
    db.commit()
    return {"message": "Session deleted"}

_df_cache = {}
def get_cached_dataframe(dataset_id: int, filepath: str):
    if dataset_id not in _df_cache:
        if filepath.endswith('.csv'):
            _df_cache[dataset_id] = pd.read_csv(filepath)
        else:
            _df_cache[dataset_id] = pd.read_excel(filepath)
    return _df_cache[dataset_id].copy()

@router.post("/", response_model=ChatResponse)
def chat_with_dataset(
    request: ChatRequest,
    current_user: models.User = Depends(auth.get_current_active_user),
    db: Session = Depends(database.get_db)
):
    lower_q = request.question.lower()
    if any(phrase in lower_q for phrase in FORBIDDEN_PHRASES):
        raise HTTPException(status_code=400, detail="Invalid query detected.")

    if not request.dataset_ids:
        raise HTTPException(status_code=400, detail="At least one dataset must be selected.")

    datasets = db.query(models.Dataset).filter(
        models.Dataset.id.in_(request.dataset_ids),
        models.Dataset.owner_id == current_user.id
    ).all()
    
    if len(datasets) != len(request.dataset_ids):
        raise HTTPException(status_code=404, detail="One or more datasets not found or access denied")

    dataset_paths = {dataset.id: file_storage.ensure_dataset_file(db, dataset) for dataset in datasets}

    try:
        start_time = time.time()
        session_id = request.session_id or str(uuid.uuid4())
        dataset_ids_str = ",".join(map(str, request.dataset_ids))
        
        user_msg = models.Message(session_id=session_id, dataset_ids=dataset_ids_str, user_id=current_user.id, role="user", content=request.question)
        db.add(user_msg)
        db.commit()
        
        # Determine if we have structured, unstructured, or mixed data
        structured_datasets = [d for d in datasets if dataset_paths[d.id].endswith(('.csv', '.xlsx', '.xls'))]
        unstructured_datasets = [d for d in datasets if dataset_paths[d.id].endswith(('.pdf', '.txt', '.docx'))]
        
        retrieved_context = ""
        client = get_chroma_client()
        collection = client.get_or_create_collection(name="dataset_insights")
        vector = get_embeddings().embed_query(request.question)
        
        try:
            # Query chroma for context (both insights and document chunks)
            results = collection.query(
                query_embeddings=[vector],
                n_results=5,
                where={"dataset_id": {"$in": request.dataset_ids}}
            )
            if results["documents"] and len(results["documents"][0]) > 0:
                retrieved_context = "\n".join(results["documents"][0])
        except Exception as e:
            print(f"ChromaDB retrieval failed: {e}")

        # If ONLY unstructured, use a direct LLM chain (RAG)
        if unstructured_datasets and not structured_datasets:
            prompt = f"Answer the following question based on the provided document excerpts:\n\nExcerpts:\n{retrieved_context}\n\nQuestion: {request.question}"
            try:
                response = llm.invoke([HumanMessage(content=prompt)])
                answer = response.content
            except Exception as e:
                answer = f"I'm sorry, I encountered an issue generating the answer: {e}"
        else:
            # We have structured datasets. Load them all.
            dfs = [get_cached_dataframe(d.id, dataset_paths[d.id]) for d in structured_datasets]
            
            # Smart Query Router
            router_prompt = f"""
            You are an intelligent Query Router.
            Evaluate the following user question: "{request.question}"
            
            Does this question require generating a chart/graph/plot, OR require complex multi-step reasoning, OR debugging? If YES to any of these, output COMPLEX.
            If it is a simple textual data lookup (e.g., "what is the average", "how many rows"), output SIMPLE.
            
            Output ONLY the word COMPLEX or SIMPLE.
            """
            
            try:
                route_decision = llm.invoke([HumanMessage(content=router_prompt)]).content.strip().upper()
            except Exception:
                route_decision = "SIMPLE" # Default to fast path
                
            if "COMPLEX" in route_decision:
                print("ROUTING TO LANGCHAIN PANDAS AGENT (COMPLEX)")
                df_arg = dfs if len(dfs) > 1 else dfs[0]
                
                agent = create_pandas_dataframe_agent(
                    llm, 
                    df_arg, 
                    verbose=True,
                    allow_dangerous_code=True,
                    handle_parsing_errors=True,
                    max_iterations=7
                )
                
                complex_prompt = f"""
                You are a highly capable Data Analyst AI. You have access to {len(structured_datasets)} structured dataset(s) loaded as pandas dataframe(s).
                Additionally, here is some text context (insights or document excerpts) retrieved for this query:
                {retrieved_context}
                
                User Question: {request.question}
                
                CRITICAL INSTRUCTIONS FOR PLOTTING:
                If the user asks you to create a chart, graph, or plot:
                1. DO NOT use matplotlib or seaborn. DO NOT use plt.show().
                2. You MUST use plotly.express (px) or plotly.graph_objects (go) to create an interactive chart.
                3. Generate the plotly figure `fig`.
                4. Get the JSON representation of the figure by calling `fig.to_json()`.
                5. In your final text answer to the user, you MUST include this exact markdown format to pass the JSON to the frontend:
                ```plotly
                <paste the JSON string here>
                ```
                Explain your analysis in text, and include the plotly block if a chart was requested.
                """
                
                def extract_llm_output(err_str: str) -> str:
                    import re
                    # Strip LangChain's automatic troubleshooting URLs which corrupt the markdown
                    err_str = re.sub(r"For troubleshooting, visit: https://docs\.langchain\.com/.*", "", err_str).strip()
                    err_str = re.sub(r"Invalid or incomplete response\n?", "", err_str).strip()
                    
                    if "Agent stopped due to iteration limit" in err_str or "Agent stopped due to time limit" in err_str:
                        return "I'm sorry, the analysis took too many steps and was stopped. Please try asking a more specific question."
                    
                    final_ans = None
                    fa_match = re.search(r"Final Answer:\s*(.*)", err_str, re.DOTALL | re.IGNORECASE)
                    if fa_match:
                        final_ans = fa_match.group(1).strip()
                    else:
                        match = re.search(r"Could not parse LLM output: `(.*?)`", err_str, re.DOTALL)
                        if match:
                            final_ans = match.group(1).strip()
                        elif "Could not parse LLM output:" in err_str:
                            final_ans = err_str.split("Could not parse LLM output:")[-1].strip(" `'\"")
                        elif "Parsing LLM output produced both a final answer and a parse-able action::" in err_str:
                            parts = err_str.split("Parsing LLM output produced both a final answer and a parse-able action::")
                            final_ans = parts[-1].strip(" `'\"")
                    
                    if final_ans:
                        # Sometimes the LLM forgets to close the plotly block if truncated, or appends garbage inside it.
                        # We try to ensure the JSON is clean.
                        plotly_match = re.search(r"```plotly\n(\{.*?\})\n?```", err_str, re.DOTALL)
                        if plotly_match and "```plotly" not in final_ans:
                            final_ans += "\n```plotly\n" + plotly_match.group(1) + "\n```"
                        
                        # If the final_ans HAS a plotly block but it's corrupted with trailing text, clean it up
                        final_ans = re.sub(r"(```plotly\n\{.*?\})[^\}]+$", r"\1\n```", final_ans, flags=re.DOTALL)
                        return final_ans
                        
                    return None

                try:
                    response = agent.invoke(complex_prompt)
                    answer = response.get("output", "Could not determine the answer.")
                except Exception as agent_error:
                    error_str = str(agent_error)
                    extracted = extract_llm_output(error_str)
                    if extracted:
                        answer = extracted
                    else:
                        print(f"Primary Agent failed: {agent_error}. Attempting fallback...")
                        try:
                            groq_llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)
                            mistral_llm = ChatMistralAI(model="mistral-large-latest", temperature=0, mistral_api_key=os.getenv("MISTRAL_API_KEY"))
                            fallback_llm = groq_llm.with_fallbacks([mistral_llm])
                            fallback_agent = create_pandas_dataframe_agent(
                                fallback_llm, df_arg, verbose=True, allow_dangerous_code=True, max_iterations=7
                            )
                            response = fallback_agent.invoke(complex_prompt)
                            answer = response.get("output", "Could not determine the answer.")
                        except Exception as fallback_error:
                            fb_error_str = str(fallback_error)
                            fb_extracted = extract_llm_output(fb_error_str)
                            if fb_extracted:
                                answer = fb_extracted
                            else:
                                answer = f"I'm sorry, I encountered an issue analyzing the data with all available models. Error: {fallback_error}."
            else:
                print("ROUTING TO DUCKDB ENGINE (SIMPLE)")
                import duckdb
                
                schema_info = ""
                for i, df in enumerate(dfs):
                    schema_info += f"\nDataset `dfs[{i}]` Schema:\nColumns: {list(df.columns)}\nTypes: {df.dtypes.to_dict()}\n"
                
                augmented_prompt = f"""
                You are a blazing fast Data Analyst AI. 
                You have access to {len(structured_datasets)} structured dataset(s) loaded as pandas dataframe(s) in a list called `dfs`.
                {schema_info}
                
                Additionally, here is the pre-computed statistical context retrieved for this query:
                {retrieved_context}
                
                User Question: {request.question}
                
                CRITICAL INSTRUCTIONS:
                1. If the user asks for a chart, graph, or plot, YOU MUST WRITE PYTHON CODE using `dfs`. DO NOT rely solely on the statistical context.
                2. If you need to perform data filtering or aggregations, you MUST write Python code to analyze `dfs`.
                3. If the question can be fully answered with the pre-computed context WITHOUT a chart, you may output the final text directly without writing code.
                4. You can use `duckdb`. It is already imported. You can query dataframes directly like: `duckdb.query("SELECT * FROM dfs[0]").df()`
                5. Enclose your Python code in ```python ... ```.
                6. Your Python code MUST store the final string answer in a variable named `result_text`.
                7. If a chart is requested, use `plotly.express` as `px` and append the chart JSON to `result_text` like this (use literal `\\n` instead of actual newlines in strings):
                ```python
                import plotly.express as px
                fig = px.bar(...)
                result_text += "\\n```plotly\\n" + fig.to_json() + "\\n```"
                ```
                """
                
                chart_requested = any(w in request.question.lower() for w in ['chart', 'graph', 'plot', 'visualize'])
                if chart_requested:
                    augmented_prompt += "\n\nTHE USER HAS REQUESTED A CHART. YOU ARE ABSOLUTELY REQUIRED TO WRITE PYTHON CODE. DO NOT PROVIDE A TEXT-ONLY ANSWER."
                    
                try:
                    response = llm.invoke([HumanMessage(content=augmented_prompt)])
                    content = response.content
                    
                    import re
                    code_match = re.search(r"```python(.*?)```", content, re.DOTALL)
                    if code_match:
                        code = code_match.group(1).strip()
                        
                        # SECURITY GATE: Prevent arbitrary code execution
                        dangerous_patterns = [r'import\s+os', r'import\s+subprocess', r'import\s+sys', r'__import__', r'eval\(', r'exec\(']
                        is_safe = True
                        for pattern in dangerous_patterns:
                            if re.search(pattern, code):
                                is_safe = False
                                break
                                
                        if not is_safe:
                            answer = "I'm sorry, I cannot execute that query as it triggered a security policy violation."
                        else:
                            local_vars = {'dfs': dfs, 'pd': pd, 'json': json, 'duckdb': duckdb}
                            try:
                                exec(code, {}, local_vars)
                                answer = local_vars.get('result_text', "Analysis completed, but `result_text` was not set by the code.")
                            except Exception as exec_error:
                                print(f"Code execution failed. Attempting fallback. Error: {exec_error}")
                                print(f"Failed Code:\n{code}")
                                fallback_prompt = f"The following code failed with error: {exec_error}\n\nCode:\n{code}\n\nPlease provide a text answer based on the context instead."
                                fb_resp = llm.invoke([HumanMessage(content=augmented_prompt), AIMessage(content=content), HumanMessage(content=fallback_prompt)])
                                answer = fb_resp.content
                    else:
                        answer = content
                except Exception as e:
                    answer = f"I'm sorry, I encountered an issue analyzing the data: {e}."

        latency_ms = (time.time() - start_time) * 1000
        
        ai_msg = models.Message(session_id=session_id, dataset_ids=dataset_ids_str, user_id=current_user.id, role="ai", content=answer)
        db.add(ai_msg)
        
        audit_log = models.AuditLog(
            user_id=current_user.id, action="CHAT_QUERY", details=f"Q: {request.question}", latency_ms=latency_ms, cost_usd=0.001
        )
        db.add(audit_log)
        db.commit()
        
        return {"answer": answer, "session_id": session_id}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
