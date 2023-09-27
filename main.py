from fastapi import FastAPI, Query  
import pyodbc

conn = pyodbc.connect('Driver={SQL Server};'
                      'Server=DESKTOP-LR7RPC4\DAMIR;'
                      'Database=EstateBook;'
                      'Trusted_Connection=yes'
                      )



app = FastAPI()





@app.get("/")
async def root():
    return {"hi"}

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
                      "Estate_Rating": data.Estate_Rating,
                       "Estate_Images_ID": data.Estate_Images_ID,
                        
                  
                  }
        estates.append(estate)
    
    return estates


@app.get("/getEstatesOnMainPage")
async def getEstatesOnMainPage(page: int = Query(default=1, description="Номер страницы", ge=1), 
                               items_per_range:int = Query(default=1, description="Кол-во элементов на странице", ge = 1)):
    cursor = conn.cursor()
    offset = (page - 1) * items_per_range
    fetch = items_per_range     
    frozenset
    cursor.execute(f"SELECT * FROM Estate order by [ID_Estate] offset {offset} Rows fetch next {fetch} rows only")
    rows = cursor.fetchall()
    estates = []
    for data in rows:
        estate = {"ID_Estate": data.ID_Estate,
                  "Ad_Name": data.Ad_Name,
                  "Location": data.Location,
                  "Price": data.Price,
                  "Area":data.Area,
                   
                  }
        estates.append(estate)
    return estates



@app.get("/getNameOnMainPage")
async def getNameOnMainPage(page: int = Query(default=1, description="Номер страницы", ge=1), 
                               items_per_range:int = Query(default=1, description="Кол-во элементов на странице", ge = 1)):
    cursor = conn.cursor()
    offset = (page - 1) * items_per_range
    fetch = items_per_range     
    frozenset
    cursor.execute(f"SELECT * FROM Estate order by [ID_Estate] offset {offset} Rows fetch next {fetch} rows only")
    rows = cursor.fetchall()
    estates = []
    for data in rows:
        estate = {"ID_Estate": data.ID_Estate,
                  "Ad_Name": data.Ad_Name,
                  
                   
                  }
        estates.append(estate)
    
    return estates


