from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from datetime import timedelta
import uvicorn
import os

print("Importing modules...")
import models, schemas, auth, database
print("Importing engine...")
from database import engine
print("Importing routers...")
from routers import datasets, chat, admin

print("Creating database tables...")
models.Base.metadata.create_all(bind=engine)
print("Database tables created!")

app = FastAPI(title="AI Data Analyst Agent API", version="1.0.0")

is_vercel = os.getenv("VERCEL") == "1"
frontend_origins = os.getenv("FRONTEND_ORIGINS") or os.getenv("FRONTEND_ORIGIN")
allowed_origins = (
    [origin.strip().rstrip("/") for origin in frontend_origins.split(",") if origin.strip()]
    if frontend_origins
    else ["*"]
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

static_root = "/tmp/static" if is_vercel else "static"
os.makedirs(os.path.join(static_root, "charts"), exist_ok=True)
app.mount("/static", StaticFiles(directory=static_root), name="static")

app.include_router(datasets.router)
app.include_router(chat.router)
app.include_router(admin.router)



@app.post("/token", response_model=schemas.Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(database.get_db)):
    user = db.query(models.User).filter(models.User.email == form_data.username).first()
    if not user or not auth.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user.email, "is_admin": user.is_admin}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/users/", response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: Session = Depends(database.get_db)):
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_password = auth.get_password_hash(user.password)
    # The first user created should probably be an admin for testing purposes
    is_first_user = db.query(models.User).count() == 0
    
    db_user = models.User(email=user.email, hashed_password=hashed_password, is_admin=is_first_user)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.get("/users/me/", response_model=schemas.User)
def read_users_me(current_user: models.User = Depends(auth.get_current_active_user)):
    return current_user

@app.get("/admin/test")
def admin_only_route(current_user: models.User = Depends(auth.get_current_admin_user)):
    return {"message": f"Hello Admin {current_user.email}"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
