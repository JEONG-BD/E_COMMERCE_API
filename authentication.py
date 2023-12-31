from passlib.context import CryptContext 
from dotenv import dotenv_values
from models import User 
from fastapi.exceptions import HTTPException
from fastapi import status
import jwt 

config_credential = dotenv_values('.env')

pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')


def get_hashed_password(password):
    return pwd_context.hash(password)


async def verify_token(token: str):
    try :
        payload = jwt.decode(token, config_credential['SECRET'], algorithms='HS256')
        user = await User.get(id= payload.get('id'))
    except :
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND,
            detail='Invalid', 
            headers={'WWW-Authenticate': 'Bearer'}
        )
    return user 


async def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


async def authenticate_user(username: str, password:str):
    user = await User.get(username = username)

    if user and await verify_password(password, user.password):
        return user 
    return False         
    
        
async def token_generator(username: str, password: str):
    user = await authenticate_user(username, password)
    
    if not user :
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail='Invalid Token or password',
            headers={'WWW-Authenticate': 'Bearer'}
        )
    print('----------')
    print(user.id)
    print('==========')
    toeken_data = {
        'id':user.id, 
        'username' :user.username
    }
    
    token = jwt.encode(toeken_data, config_credential['SECRET'])
    
    return token 
    