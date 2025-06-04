from flask import Flask, Response, request, render_template
import csv
from io import StringIO
from datetime import datetime
import requests
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)

SHOPIFY_STORE = 'parent-geenee-in.myshopify.com'
API_VERSION = '2025-04'
ACCESS_TOKEN = os.getenv('SHOPIFY_ACCESS_TOKEN')

def fetch_shopify_orders(filter_product_titles):
    url = f"https://{SHOPIFY_STORE}/admin/api/{API_VERSION}/orders.json"
    headers = {
        "X-Shopify-Access-Token": ACCESS_TOKEN,
        "Content-Type": "application/json"
    }

    orders = []
    params = {'limit': 250}
    while True:
        response = requests.get(url, headers=headers, params=params)
        try:
            response.raise_for_status()
            data = response.json()
        except requests.exceptions.JSONDecodeError:
            print("Failed to decode JSON:")
            print("Status Code:", response.status_code)
            print("Response Text:", response.text)
            raise

        batch = data.get('orders', [])
        orders.extend(batch)

        if len(batch) < 250:
            break

    return [
        order for order in orders
        if any(
            any(title.lower() in item.get('name', '').lower() for title in filter_product_titles)
            for item in order.get('line_items', [])
        )
    ]

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/download', methods=['GET'])
def export_orders():
    product_filters = request.args.getlist('product_title')
    orders = fetch_shopify_orders(filter_product_titles=product_filters)

    if product_filters in ["Karnataka","Tamil Nadu"]:
        csv_columns = [
            "S. No",
            "Form ID/Application No.",
            "Student Name",
            "Parent Email",
            "Registered Class Name",
            "Branch",
            "Order Name",
            "Order Created Date",
            "State",
            "Parent Name",
            "Parent Phone No.",
            "Stream",
            "plan"
        ]

        si = StringIO()
        cw = csv.writer(si)
        cw.writerow(csv_columns)

        serial_no = 1
        for order in orders:
            order_name = order.get("name", "")
            order_created_at = order.get("created_at", "")
            customer = order.get("customer", {}) or {}
            state = customer.get("state", "")

            for item in order.get("line_items", []):
            
                properties_list = item.get("properties", [])
                properties = {p['name']: p['value'] for p in properties_list}

                row = [
                    serial_no,
                    properties.get("Form ID/Application No.", ""),
                    properties.get("Student Name", ""),
                    properties.get("Parent Email", customer.get("email", "")),
                    properties.get("Registered Class Name", ""),
                    properties.get("Branch", ""),
                    order_name,
                    order_created_at,
                    state,
                    properties.get("Parent Name", ""),
                    properties.get("Parent Phone No.", ""),
                    properties.get("Stream", ""),
                    item.get("name","")
                ]

                cw.writerow(row)
                serial_no += 1

    elif "Beacon" in product_filters:
        si = StringIO()
        cw = csv.writer(si)
        cw.writerow(["S No", "Order No", "Date of Purchase", "Email ID", "Billing Address", "No of Beacon/Sub Total"])

        for i, order in enumerate(orders, start=1):
            billing = order.get("billing_address", {})
            billing_address = f"{billing.get('address1', '')}, {billing.get('city', '')}, {billing.get('province', '')}, {billing.get('zip', '')}, {billing.get('country', '')}"
            
            row = [
                i,
                order.get("order_number", ""),
                order.get("created_at", ""),
                order.get("email", ""),
                billing_address,
                order.get("subtotal_price", "")  
            ]
            
            cw.writerow(row)


    return Response(
        si.getvalue(),
        mimetype="text/csv",
        headers={
            "Content-disposition":
            f"attachment; filename={product_filters[0]}_{datetime.now().strftime('%Y%m%d%H%M%S')}.csv"
        }
    )

