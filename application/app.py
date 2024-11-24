from fastapi import FastAPI, Request, Form
from fastapi.middleware.cors import CORSMiddleware 
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

import datetime
import os
import logging
import oracledb
import uvicorn

d = os.environ.get("ORACLE_HOME")               # Defined by the file `oic_setup.sh`
oracledb.init_oracle_client(lib_dir=d)          # Thick mode

# These environment variables come from `env.sh` file.
user_name = os.environ.get("DB_USERNAME")
user_pswd = os.environ.get("DB_PASSWORD")
db_alias  = os.environ.get("DB_ALIAS")

# make sure to setup connection with the DATABASE SERVER FIRST. refer to python-oracledb documentation for more details on how to connect, and run sql queries and PL/SQL procedures.

app = FastAPI()

logger = logging.getLogger('uvicorn.error')
logger.setLevel(logging.DEBUG)

origins = ['*']

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
) 
app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")


# -----------------------------
# API Endpoints
# -----------------------------

# ---------- GET methods for the pages ----------
@app.get("/", response_class=HTMLResponse)
async def get_index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# Bill payment page
@app.get("/bill-payment", response_class=HTMLResponse)
async def get_bill_payment(request: Request):
    return templates.TemplateResponse("bill_payment.html", {"request": request})

# Bill generation page
@app.get("/bill-retrieval", response_class=HTMLResponse)
async def get_bill_retrieval(request: Request):
    return templates.TemplateResponse("bill_retrieval.html", {"request": request})

# Adjustments page
@app.get("/bill-adjustments", response_class=HTMLResponse)
async def get_bill_adjustment(request: Request):
    return templates.TemplateResponse("bill_adjustment.html", {"request": request})


# ---------- POST methods for the pages ----------
@app.post("/bill-payment", response_class=HTMLResponse)
async def post_bill_payment(request: Request, bill_id: int = Form(...), amount: float = Form(...), payment_method_id: int = Form(...)):
    # Handle billing payment here

    # Retrive the details required in the dictionary, by querying your database, or running appropriate functions
    payment_details = {
        "bill_id": bill_id,
        "amount": amount,
        "payment_method_id": payment_method_id,
        "payment_method_description": "Sample description",
        "payment_date": datetime.datetime.now(),
        "payment_status": "Fully paid",
        "outstanding_amount": 0.0,
    }

    return templates.TemplateResponse("payment_receipt.html", {"request": request, "payment_details": payment_details})


@app.post("/bill-retrieval", response_class=HTMLResponse)
async def post_bill_retrieval(request: Request, customer_id: str = Form(...), connection_id: str = Form(...), month: str = Form(...), year: str = Form(...)):
    # Here, you would generate the bill

    # Retrive the details required in the dictionary, by querying your database, or running appropriate functions
    # the values in this dict are hardcoded for now. you will be populating it dynamically.
    bill_details = {
        "customer_id": customer_id,
        "connection_id": connection_id,
        "customer_name": "John Doe",
        "customer_address": "123 Main Street, City, Country",
        "customer_phone": "+1234567890",
        "customer_email": "asd@gmail.com",
        "connection_type": "Residential",
        "division": "Lahore",
        "subdivision": "DHA",
        "installation_date": "2021-01-01",
        "meter_type": "abc",
        "issue_date": "2021-01-01",
        "net_peak_units": 'xx',
        "net_off_peak_units": 'xx',
        "bill_amount": 100.50,
        "due_date": "2021-01-15",
        "amount_after_due_date": 110.50,
        "month": month,
        "arrears_amount": 'xx',
        "fixed_fee_amount": 50.00,
        "tax_amount": 25.00,
        # all the applicable tariffs
        "tariffs": [
            {"name": "Residential Customer 5KW Slab 1 - Peak Hour", "units": 150, "rate": 0.2, "amount": 30.00},
            {"name": "Off-Peak Tariff", "units": 200, "rate": 0.15, "amount": 30.00},
        ],
        # applicable taxes
        "taxes": [
            {"name": "GST", "amount": 15.75},
            {"name": "Electricity Duty", "amount": 10.00},
        ],
        # applicable subsidies
        "subsidies": [
            {"name": "GOP-Protected-Cust1", "provider_name": "GOP", "rate_per_unit": 15.00},
        ],
        # applicable fixed fees
        "fixed_fee": [
            {"name": "Meter rent", "amount": 15.75},
            {"name": "PTV Fee", "amount": 10.00},
        ],
        # the last 10 (or lesser) bills of the customer
        "bills_prev": [
            {"month": "2020-12", "amount": 90.00, "due_date": "2021-01-15", "status": "Paid"},
            {"month": "2020-11", "amount": 80.00, "due_date": "2020-12-15", "status": "Paid"},
            {"month": "2020-10", "amount": 70.00, "due_date": "2020-11-15", "status": "Paid"},
            {"month": "2020-12", "amount": 90.00, "due_date": "2021-01-15", "status": "Paid"},
            {"month": "2020-11", "amount": 80.00, "due_date": "2020-12-15", "status": "Paid"},
            {"month": "2020-10", "amount": 70.00, "due_date": "2020-11-15", "status": "Paid"},
            {"month": "2020-12", "amount": 90.00, "due_date": "2021-01-15", "status": "Paid"},
            {"month": "2020-11", "amount": 80.00, "due_date": "2020-12-15", "status": "Paid"},
            {"month": "2020-10", "amount": 70.00, "due_date": "2020-11-15", "status": "Paid"}
        ]
    }
    
    return templates.TemplateResponse("bill_details.html", {"request": request, "bill_details": bill_details})


# Code for handling adjustments goes here
@app.post("/bill-adjustments", response_class=HTMLResponse)
async def post_bill_adjustments(
    request: Request,
    bill_id: int = Form(...),
    officer_name: str = Form(...),
    officer_designation: str = Form(...),
    original_bill_amount: float = Form(...),
    adjustment_amount: float = Form(...),
    adjustment_reason: str = Form(...),
):
    raise NotImplementedError

if __name__ == "__main__":
    uvicorn.run(app, host='0.0.0.0', port=8000)