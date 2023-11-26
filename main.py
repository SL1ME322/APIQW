from fastapi import FastAPI, Query, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from typing import Annotated, Union
from pydantic import BaseModel
from passlib.context import CryptContext
import pyodbc
import subprocess
from jose import JWTError, jwt
import secrets
from datetime import timedelta, datetime, date 
import requests
import base64
from typing import Union, Optional
SECRET_KEY = "24d74866153c2af47069517d910d295cc35bb4443001ee732e3438455c14572e"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
#https://images.ctfassets.net/sfnkq8lmu5d7/1NaIFGyBn0qwXYlNaCJSEl/ad59ce5eefa3c2322b696778185cc749/2021_0825_Kitten_Health.jpg?w=1000&h=750&q=70&fm=webp

app = FastAPI()

conn = pyodbc.connect('Driver={SQL Server};'
                      'Server=DESKTOP-LR7RPC4\DAMIR;'
                      'Database=EstateBook;'
                      'Trusted_Connection=yes'
                      )
 

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: str| None = None

# payload - это claims
def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


 

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class EstateForPost(BaseModel): 
    ID_Estate:int
    Ad_Name: str 
    Location : str
    Price: int
    Price_For_Month: int
    Mortgage_Price: int
    Area: int
    House_Area: int
    Metro_Station: str
    Train_Station: str
    Description: str
    Ad_Date: str
    Building_Date: str #формат date - сломанный
    Status: str 
    Estate_Rating: Optional[int] = None
    Estate_Images_ID: int
    User_ID: int
    
@app.post("/addEstate/")
async def addEstate(estate: EstateForPost):
    cursor = conn.cursor()
    cursor.execute("INSERT INTO [dbo].[Estate] (Ad_Name, Location, Price, "
                   "Price_For_Month, Mortgage_Price, Area, House_Area, Metro_Station, "
                   "Train_Station, Description, Ad_Date, Building_Date, Status, "
                  # "Estate_Rating, "
                   "Estate_Images_ID, User_ID)" 
                   "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,?,?,?, ? )",
                   estate.Ad_Name, estate.Location, estate.Price, estate.Price_For_Month, 
                   estate.Mortgage_Price,
                     estate.Area,estate.House_Area,  estate.Metro_Station, estate.Train_Station, 
                     estate.Description, estate.Ad_Date, estate.Building_Date,
                       estate.Status,
                        # estate.Estate_Rating, 
                       
                       estate.Estate_Images_ID, estate.User_ID )
    conn.commit()
    



class User(BaseModel):
    ID_User: Optional[int] = None
   # Name: Union[str, None] = None
   # Surname: Union[str, None] = None
   # Middle_Name: Union[str, None] = None
    Login: str
    #Email: Union[str, None] = None  # поле может быть str или none
    
    #Phone: Union[str, None] = None
    #Location: Union[str, None] = None
    Registration_Date: str
    Description: Union[str, None] = None
     
    #Average_Mark: Union[str, None] = None
    disabled: Union[bool, None] = None
    Avatar: Union[str, None] = None


class UserInDB(User):
    hashed_password: str
    
 
def get_user(db, username: str):
    cursor = db.cursor()
    cursor.execute("SELECT * FROM [dbo].[User] WHERE Login = ?", username)
    row = cursor.fetchone()
    if row:
        user_dict = {"ID_User":row.ID_User,"Login":row.Login, "hashed_password": row.Password, "Avatar": row.Avatar, 
                     "Registration_Date" : row.Registration_Date,
                     "Description" : row.Description}
        return UserInDB(**user_dict)

def authenticate_user(db, username: str, password: str):
    user = get_user(db, username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user

async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED, 
        detail="Не удалось проверить учетные данные",
        headers={"WWW-Authenticate": "Bearer"},)
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub") #субъект токена
        if username is None:
            raise credentials_exception
        token_data = TokenData(username = username)
    except JWTError:
        raise credentials_exception
    user = get_user(conn, username = token_data.username)
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_user(current_user: Annotated[User, Depends(get_current_user)]):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Неактивный пользователь")
    return current_user


@app.post("/token", response_model=Token)
async def login_for_access_token(
    form_data:Annotated[OAuth2PasswordRequestForm, Depends()]

):
    user = authenticate_user(conn, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Неверный логин или пароль", headers={"WWW-Authenticate": "Bearer"})
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub" :user.Login}, expires_delta=access_token_expires)
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/users/me/", response_model=User)
async def read_users_me(
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    return current_user

@app.get("/")
async def root():
    return {"hi"}

@app.get("/usersEstates")
async def usersEstates(id:int):
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Estate where [User_ID] = ? ",id )
    rows = cursor.fetchall()
    estates = []
    for data in rows:
        estate = {"ID_Estate": data.ID_Estate,
                  "Ad_Name": data.Ad_Name,
                  "Location": data.Location,
                  "Price": data.Price,
                  "Price_For_Month": data.Price_For_Month,
                 "Mortgage_Price": data.Mortgage_Price,
                 "Area": data.Area,
                 "House_Area": data.House_Area,
                 "Metro_Station": data.Metro_Station,
                 "Train_Station": data.Train_Station,
                 "Description": data.Description,
                 "Ad_Date": data.Ad_Date,
                 "Building_Date": data.Building_Date,
                 "Status": data.Status,
                 #"Estate_Rating": data.Estate_Rating,
                 "Estate_Images_ID": data.Estate_Images_ID,
                  "User_ID": data.User_ID,
                  }
        estates.append(estate)
    return estates

@app.get("/getUserById/{id}", response_model= User)
async def getUserById(id:int):
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM [dbo].[User] where [ID_User] = ? ", id )
    row = cursor.fetchone()
    return User(ID_User=row[0] ,Login = row[1], Avatar = row[3], Registration_Date=row[4], Description=row[5], )
    
     
@app.get("/allEstates")
async def getAllEstates():
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Estate")
    rows = cursor.fetchall()
    estates = []
    for data in rows:
        estate = {"ID_Estate": data.ID_Estate,
                  "Ad_Name": data.Ad_Name,
                  "Location": data.Location,
                  "Price": data.Price,
                  "Price_For_Month": data.Price_For_Month,
                  "Mortgage_Price": data.Mortgage_Price,
                  "Area": data.Area,
                  "House_Area": data.House_Area,
                  "Metro_Station": data.Metro_Station,
                  "Train_Station": data.Train_Station,
                  "Description": data.Description,
                  "Ad_Date": data.Ad_Date,
                  "Building_Date": data.Building_Date,
                  "Status": data.Status,
                  #"Estate_Rating": data.Estate_Rating,
                  "Estate_Images_ID": data.Estate_Images_ID,
                  "User_ID": data.User_ID,
                  }
        estates.append(estate)
    return estates
 
 
@app.post("/register_new_user/")
async def register_new_user(user: UserInDB):
    cursor = conn.cursor()
    #cursor.execute("INSERT INTO [dbo].[User](Name, Surname, Middle_Name, Login, Password, Avatar, Phone, Location, Description, Average_Mark) "
    #               "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?) ",
    #              user.Name, user.Surname, user.Middle_Name, user.Login, get_password_hash(user.hashed_password),
    #                user.Avatar, user.Phone, user.Location, user.Description, user.Average_Mark)
    cursor.execute("INSERT INTO [dbo].[User]( Login, Password, Avatar, Registration_Date, Description) "
 
                   "VALUES ( ?, ?, ?, ?, ?) ",
                 user.Login, get_password_hash(user.hashed_password), image_url_to_base64(user.Avatar), user.Registration_Date, user.Description
                  )
    conn.commit()
  
@app.post("/convert_url_tobase64/")
def image_url_to_base64(#id:int
   url:str):
    response = requests.get(url)
    if (response.status_code == 200):

        base64url = base64.b64encode(response.content).decode('utf-8')
       #cursor = conn.cursor()
       #cursor.execute(f"Update [dbo].[User] set [Avatar] = '{base64url}' where [ID_User] = {id}")
        #conn.commit()
        return base64url
    else:
        print('Не удалось преобразовать в base64')
    

@app.get("/getEstatesOnMainPage")
async def getEstatesOnMainPage(page: int = Query(default=1, description="Номер страницы", ge=1),
                               items_per_range: int = Query(default=1, description="Кол-во элементов на странице", ge=1), 
                               search: Optional[str] = None):
    cursor = conn.cursor()
    offset = (page - 1) * items_per_range
    fetch = items_per_range
    query = f"SELECT * FROM Estate "
    #frozenset
   
    
    if search is not None and search.strip() :
        query += f"WHERE Ad_Name LIKE '%{search}%' "
    
    query += f" ORDER by [ID_Estate] offset {offset} Rows fetch next {fetch} rows only"   
    cursor.execute(query) 
    rows = cursor.fetchall()    
    estates = []
    for data in rows:
        estate = {"ID_Estate": data.ID_Estate,
                  "Ad_Name": data.Ad_Name,
                  "Location": data.Location,
                  "Price": data.Price,
                  # "Price_For_Month": data.Price_For_Month,
                  "Mortgage_Price": data.Mortgage_Price,
                  "Area": data.Area,
                  "House_Area": data.House_Area,
                  "Metro_Station": data.Metro_Station,
                  "Train_Station": data.Train_Station,
                  "Description": data.Description,
                  # "Ad_Date": data.Ad_Date,
                  # "Building_Date": data.Building_Date,
                  "Status": data.Status,
                 # "Estate_Rating": data.Status,
                  "User_ID": data.User_ID,
                  }
        estates.append(estate)
    return estates

@app.get("/getNameOnMainPage")
async def getNameOnMainPage(page: int = Query(default=1, description="Номер страницы", ge=1),
                            items_per_range: int = Query(default=1, description="Кол-во элементов на странице", ge=1)):
    cursor = conn.cursor()
    offset = (page - 1) * items_per_range
    fetch = items_per_range
    frozenset
    cursor.execute(
        f"SELECT * FROM Estate order by [ID_Estate] offset {offset} Rows fetch next {fetch} rows only")
    rows = cursor.fetchall()
    estates = []
    for data in rows:
        estate = {"ID_Estate": data.ID_Estate,
                  "Ad_Name": data.Ad_Name,


                  }
        estates.append(estate)

    return estates


@app.post("/getNameOnMainPage")
async def getNameOnMainPage(page: int = Query(default=1, description="Номер страницы", ge=1),
                            items_per_range: int = Query(default=1, description="Кол-во элементов на странице", ge=1)):
    cursor = conn.cursor()
    offset = (page - 1) * items_per_range
    fetch = items_per_range
    frozenset
    cursor.execute(
        f"SELECT * FROM Estate order by [ID_Estate] offset {offset} Rows fetch next {fetch} rows only")
    rows = cursor.fetchall()
    estates = []
    for data in rows:
        estate = {"ID_Estate": data.ID_Estate,
                  "Ad_Name": data.Ad_Name,


                  }
        estates.append(estate)

    return estates


 