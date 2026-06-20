from fastapi import FastAPI

from .user_router import router


app = FastAPI(title="Sample User API")
app.include_router(router)
