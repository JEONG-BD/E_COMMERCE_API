import os 
from dotenv import dotenv_values 
from fastapi import (BackgroundTasks, UploadFile, File, Form, Depends, HTTPException, status)
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig 
from pydantic import BaseModel, EmailStr
from typing import List 
from models import User 
import jwt 

config_credentials = dotenv_values('.env')

conf = ConnectionConfig(
    MAIL_USERNAME = config_credentials['MAIL_USERNAME'], 
    MAIL_PASSWORD = config_credentials['MAIL_PASSWORD'], 
    MAIL_FROM = config_credentials['MAIL_USERNAME'], 
    MAIL_PORT = config_credentials['MAIL_PORT'],
    MAIL_SERVER = config_credentials['MAIL_SERVER'], 
    MAIL_STARTTLS = config_credentials['MAIL_USE_TLS'],
    MAIL_SSL_TLS = config_credentials['MAIL_USE_SSL'],
    USE_CREDENTIALS = True, 
    VALIDATE_CERTS= True 
)

class EmailSchema(BaseModel):
    email: List[EmailStr]
    
async def send_register_email(email: List, instance: User):
    #print(isinstance, type(isinstance), isinstance.__dict__)
    print("------------------")
    token_data = {
        'id': instance.id, 
        'username': instance.username 
    }
    
    token = jwt.encode(token_data, config_credentials['SECRET'], algorithm='HS256')
    
    template = f"""
        <!DOCTYPE html>
            <html lang="en">
                <head>
                    <meta charset="UTF-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    <title>Document</title>
                </head>
                <body>
                    <div style= "display: flex; align-items: center; justif-content:
                    center; flex-direction: column">
                        <h3>Account Verification</h3>
                        <br>
                        <p>Thanks for choosing EasyShops, 
                            Please click on the button below
                            to verify your account</p> 
                        <a style="margin top: 1rem; padding: 1rem; border-radius: 0.5rem;
                            font-size: 1rem; text-decoration: none; background: #0275d8; color:
                            white;" href="http://localhost:8000/verification/?token={token}"> 
                            Verify your email</a>
                        <p>Please kindly ignore this email if you did not register for EasyShops and nothing will happend. Thanks</p>
                    </div>         
                </body>
            </html>
    """
    message = MessageSchema(
        subject='EasyShop Account Verification Email', 
        recipients=email, 
        body = template, 
        subtype = 'html'
    )
    
    fm = FastMail(conf)
    
    await fm.send_message(message=message)