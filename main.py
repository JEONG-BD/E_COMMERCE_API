from fastapi import FastAPI, Request, status, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates 

from tortoise import BaseDBAsyncClient 
from tortoise.signals import post_save
from tortoise.contrib.fastapi import register_tortoise 

from authentication import get_hashed_password, very_token
from models import * 
from typing import List, Optional, Type 
from emails import send_register_email
import uvicorn 


app = FastAPI()
templtes = Jinja2Templates(directory='templates')


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
        # print(instance, type(isinstance), instance.__dict__)
        await send_register_email([instance.email], instance)


@app.get('/verification', response_class=HTMLResponse)
async def email_verification(request: Request, token: str):
    user = await very_token(token)

    if user and not user.is_verified :
        user.is_verified = True 
        await user.save()
        return templtes.TemplateResponse('verification.html', 
                                         {"request": request, 
                                          "username": user.username})
    raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND,
            detail='Invalid token or expired token', 
            headers={'WWW-Authenticate': 'Bearer'}
    )

    
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
