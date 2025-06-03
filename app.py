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

    selected_fields = [
    "id", "admin_graphql_api_id", "app_id", "browser_ip", "buyer_accepts_marketing",
    "cart_token", "checkout_id", "checkout_token", "client_details", "confirmation_number",
    "confirmed", "contact_email", "created_at", "currency", "current_subtotal_price",
    "current_subtotal_price_set", "current_total_discounts", "current_total_discounts_set",
    "current_total_price", "current_total_price_set", "current_total_tax", "current_total_tax_set",
    "customer_locale", "discount_codes", "duties_included", "email", "estimated_taxes",
    "financial_status", "landing_site", "name", "number", "order_number", "order_status_url",
    "payment_gateway_names", "presentment_currency", "processed_at", "source_name", "subtotal_price",
    "subtotal_price_set", "tax_exempt", "tax_lines", "taxes_included", "test", "token",
    "total_discounts", "total_discounts_set", "total_line_items_price", "total_line_items_price_set",
    "total_price", "total_price_set", "total_tax", "total_tax_set", "total_weight", "updated_at",
    "billing_address", "customer", "line_items"
    ]

    selected_fields=sorted(selected_fields)
    si = StringIO()
    cw = csv.writer(si)

    cw.writerow(selected_fields)

    for order in orders:
        row = [order.get(field, '') for field in selected_fields]
        cw.writerow(row)

    return Response(
        si.getvalue(),
        mimetype="text/csv",
        headers={
            "Content-disposition":
            f"attachment; filename={product_filters[0]}_{datetime.now().strftime('%Y%m%d%H%M%S')}.csv"
        }
    )

if __name__ == '__main__':
    app.run(debug=True)
