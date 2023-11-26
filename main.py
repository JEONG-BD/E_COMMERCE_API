from fastapi import FastAPI, Request, status, HTTPException, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates 

from tortoise import BaseDBAsyncClient 
from tortoise.signals import post_save
from tortoise.contrib.fastapi import register_tortoise 

from authentication import * 
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi import File, UploadFile 
from fastapi.staticfiles import StaticFiles 
from PIL import Image
from models import * 
from typing import List, Optional, Type 
from emails import send_register_email

import secrets 
import uvicorn 

app = FastAPI()

oauth2_schema = OAuth2PasswordBearer(tokenUrl='token')

templtes = Jinja2Templates(directory='templates')

app.mount('/static', StaticFiles(directory='static'), name='static')

@app.post('/token')
async def generate_token(request_form: OAuth2PasswordRequestForm = Depends()):
    token = await token_generator(request_form.username, request_form.password)
    return {'access_token':token, 'token_type':'bearer'} 


async def get_current_user(token: str = Depends(oauth2_schema)):
    try :
        payload = jwt.decode(token, config_credential['SECRET'], algorithms='HS256')
        user = await User.get(id = payload.get('id'))
        print(user, type(user), user.__dict__)
    except :
        raise HTTPException(
            status_code= status.HTTP_401_UNAUTHORIZED, 
            detail = 'Invalid username or password', 
            headers = {'WWW-Authenticate':'Bearer'} 
        ) 
    return await user 


@app.post('/user/me')
async def user_login(user: user_pydanticIn = Depends(get_current_user)):
    business = await Business.get(owner = user)
    print(business.__dict__, type(business), business)
    print("=================")
    return {
        'status': 'ok',
        'data': {
            'username': user.username, 
            'email': user.email, 
            'verified': user.is_verified, 
            'joined_date': user.join_date.strftime('%b %d %Y')
        }
    }
    

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
    user = await verify_token(token)

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


@app.post('/uploadfile/profile', tags=['Upload File'])
async def create_upload_file(file: UploadFile = File(...), 
                             user: user_pydantic = Depends(get_current_user)): 
    FILEPATH = './static/images'
    filename = file.filename 
    extension = filename.split('.')[1]
    
    if extension not in ['png', 'jpg'] : 
        return {
            'status': 'error', 
            'detail': 'File extenstion not allowed', 
        }
        
    token_name = secrets.token_hex(10)+ '.' + extension 
    generate_name = FILEPATH + token_name 
    file_content = await file.read() 
    
    with open(generate_name, 'wb') as file : 
        file.write(file_content)
    
    img = Image.open(generate_name)
    img = img.resize(size = (200, 200))
    img.save(generate_name)
    
    file.close()
    
    business = await Business.get(owner = user)
    owner = await business.owner 
    
    if owner == user: 
        business.logo = token_name 
        await business.save() 
    
    raise HTTPException(
            status_code = status.HTTP_401_UNAUTHORIZED,
            detail='Not authenticated to perform this action', 
            headers={'WWW-Authenticate': 'Bearer'}
    )
    

@app.post('/uploadfile/product/{id}', tags=['Upload File'])
async def create_upload_file(id: int, file: UploadFile = File(...), 
                             user : user_pydantic = Depends(get_current_user)):
    FILEPATH = './static/images'
    filename = file.filename 
    extension = filename.split('.')[1]
    
    if extension not in ['png', 'jpg'] : 
        return {
            'status': 'error', 
            'detail': 'File extenstion not allowed', 
        }
        
    token_name = secrets.token_hex(10)+ '.' + extension 
    generate_name = FILEPATH + token_name 
    file_content = await file.read() 
    
    with open(generate_name, 'wb') as file : 
        file.write(file_content)
    
    img = Image.open(generate_name)
    img = img.resize(size = (200, 200))
    img.save(generate_name)
    
    file.close()
    
    product = await Product.get(id = id)
    business = await product.business 
    owner = await business.owner 
    
    if owner == user : 
        product.product_image = token_name 
        await product.save() 
    
    raise HTTPException(
            status_code = status.HTTP_401_UNAUTHORIZED,
            detail='Not authenticated to perform this action', 
            headers={'WWW-Authenticate': 'Bearer'}
    )

    
register_tortoise(
    app, 
    db_url="postgres://admin:1234@localhost:5431/postgres",
    modules={'models': ['models']}, 
    generate_schemas=True,
    add_exception_handlers=True
)
