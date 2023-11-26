from fastapi import FastAPI 
from tortoise import BaseDBAsyncClient 
from tortoise.signals import post_save
from tortoise.contrib.fastapi import register_tortoise 

from authentication import get_hashed_password
from models import * 
from typing import List, Optional, Type 

import uvicorn 


app = FastAPI()

@post_save(User)
async def create_business(
    sender: 'Type[User]', 
    instance: User, 
    created: bool, 
    using_db: 'Optional[BaseDBAsyncClient]', 
    update_fileds: List[str]
) -> None : 
    if created:
        business_obj = await Business.create(
            business_name = instance.username, owner = instance
        )
        
        await business_pydantic.from_tortoise_orm(business_obj)


@app.post('/registration')
async def user_registrations(user: user_pydanticIn):
    user_info = user.dict(exclude_unset=True)
    user_info['password'] = get_hashed_password(user_info['password'])
    user_obj = await User.create(**user_info)
    new_user = await user_pydantic.from_tortoise_orm(user_obj)
    
    return {
        'status': 'ok',
        'data': f'Hello {new_user.username}, thanks for choosing our services Please check your email inbox and click on the link to confirm your eamil'
    }
     

@app.get('/')
def index():
    return {'Message': "Hello world"}

register_tortoise(
    app, 
    db_url="postgres://admin:1234@localhost:5431/postgres",
    modules={'models': ['models']}, 
    generate_schemas=True,
    add_exception_handlers=True
)
