import uvicorn 
from fastapi import FastAPI 
from tortoise.contrib.fastapi import register_tortoise 
from models import * 

app = FastAPI()

@app.get("/")
def index():
    return {'Message': "Hello world"}

register_tortoise(
    app, 
    # db_url="",
    modules={'models': ['models']}, 
    generate_schemas=True,
    add_exception_handlers=True
)
