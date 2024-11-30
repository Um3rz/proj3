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
# user_name = os.environ.get("DB_USERNAME")
# user_pswd = os.environ.get("DB_PASSWORD")
# db_alias  = os.environ.get("DB_ALIAS")

# make sure to setup connection with the DATABASE SERVER FIRST. refer to python-oracledb documentation for more details on how to connect, and run sql queries and PL/SQL procedures.
def get_db_connection():
    user_name = os.environ.get("DB_USERNAME")
    user_pswd = os.environ.get("DB_PASSWORD")
    db_alias = os.environ.get("DB_ALIAS")
    
    connection = oracledb.connect(
        user=user_name,
        password=user_pswd,
        dsn=db_alias
    )
    return connection

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


def execute_plsql_function(function_name: str, params: List):
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        # Example PL/SQL call
        return_value = cursor.callfunc(function_name, oracledb.NUMBER, params)
        return return_value
    except oracledb.DatabaseError as e:
        print(f"Database error: {e}")
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'connection' in locals():
            connection.close()

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

    # Initialize variables
    BillAmount = 0
    bill_details = {}

    try:
        # Connect to DB
        connection = get_db_connection()
        cursor = connection.cursor()

        # Query to retrieve the bill details based on parameters
        query = """
            SELECT customer_name, customer_address, customer_phone, customer_email, connection_type, 
                   division, subdivision, installation_date, meter_type, issue_date, 
                   net_peak_units, net_off_peak_units, bill_amount, due_date, arrears_amount
            FROM bill
            WHERE connection_id = :connection_id AND month = :month AND year = :year
        """
        cursor.execute(query, {"connection_id": connection_id, "month": int(month), "year": int(year)})

        bill_row = cursor.fetchone()
        
        if bill_row:
            # Extracting data from DB response
            customer_name, customer_address, customer_phone, customer_email, connection_type, \
            division, subdivision, installation_date, meter_type, issue_date, \
            net_peak_units, net_off_peak_units, BillAmount, due_date, arrears_amount = bill_row

            # Populate bill details
            bill_details = {
                "customer_id": customer_id,
                "connection_id": connection_id,
                "customer_name": customer_name,
                "customer_address": customer_address,
                "customer_phone": customer_phone,
                "customer_email": customer_email,
                "connection_type": connection_type,
                "division": division,
                "subdivision": subdivision,
                "installation_date": installation_date,
                "meter_type": meter_type,
                "issue_date": issue_date,
                "net_peak_units": net_peak_units,
                "net_off_peak_units": net_off_peak_units,
                "bill_amount": BillAmount,
                "due_date": due_date,
                "amount_after_due_date": BillAmount,  # Assuming this is the same as the BillAmount for simplicity
                "month": month,
                "arrears_amount": arrears_amount,
                "fixed_fee_amount": 50.00,  # Hardcoded for now
                "tax_amount": 25.00,  # Hardcoded for now
                "tariffs": [],  # Will populate below
                "taxes": [],  # Will populate below
                "subsidies": [],  # Will populate below
                "fixed_fee": [],  # Will populate below
                "bills_prev": []  # Will populate below
            }
            
            # Fetch and populate tariffs, taxes, subsidies, fixed fees, and previous bills
            # For example, querying tariffs
            tariffs_query = """
                SELECT tariff_name, units, rate, amount 
                FROM tariffs 
                WHERE connection_id = :connection_id AND month = :month AND year = :year
            """
            cursor.execute(tariffs_query, {"connection_id": connection_id, "month": int(month), "year": int(year)})
            tariffs = cursor.fetchall()
            for row in tariffs:
                tariff = {
                    "name": row[0],
                    "units": row[1],
                    "rate": row[2],
                    "amount": row[3]
                }
                bill_details["tariffs"].append(tariff)

            # Query taxes
            taxes_query = """
                SELECT tax_name, tax_amount 
                FROM taxes 
                WHERE connection_id = :connection_id AND month = :month AND year = :year
            """
            cursor.execute(taxes_query, {"connection_id": connection_id, "month": int(month), "year": int(year)})
            taxes = cursor.fetchall()
            for row in taxes:
                tax = {
                    "name": row[0],
                    "amount": row[1]
                }
                bill_details["taxes"].append(tax)

            # Query subsidies
            subsidies_query = """
                SELECT subsidy_name, provider_name, rate_per_unit
                FROM subsidies 
                WHERE connection_id = :connection_id AND month = :month AND year = :year
            """
            cursor.execute(subsidies_query, {"connection_id": connection_id, "month": int(month), "year": int(year)})
            subsidies = cursor.fetchall()
            for row in subsidies:
                subsidy = {
                    "name": row[0],
                    "provider_name": row[1],
                    "rate_per_unit": row[2]
                }
                bill_details["subsidies"].append(subsidy)

            # Query fixed fees
            fixed_fee_query = """
                SELECT fee_name, fee_amount 
                FROM fixed_fees 
                WHERE connection_id = :connection_id AND month = :month AND year = :year
            """
            cursor.execute(fixed_fee_query, {"connection_id": connection_id, "month": int(month), "year": int(year)})
            fixed_fees = cursor.fetchall()
            for row in fixed_fees:
                fee = {
                    "name": row[0],
                    "amount": row[1]
                }
                bill_details["fixed_fee"].append(fee)

            # Fetch previous bills for the customer
            previous_bills_query = """
                SELECT month, amount, due_date, status 
                FROM bills 
                WHERE customer_id = :customer_id
                ORDER BY issue_date DESC
                FETCH FIRST 10 ROWS ONLY
            """
            cursor.execute(previous_bills_query, {"customer_id": customer_id})
            previous_bills = cursor.fetchall()
            for row in previous_bills:
                bill = {
                    "month": row[0],
                    "amount": row[1],
                    "due_date": row[2],
                    "status": row[3]
                }
                bill_details["bills_prev"].append(bill)

        else:
            print("No bill found for the given parameters.")

    except oracledb.DatabaseError as e:
        print(f"Database error: {e}")
        return {"error": str(e)}

    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'connection' in locals():
            connection.close()

    # Return the populated bill details to the front end
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