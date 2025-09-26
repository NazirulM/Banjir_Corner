import streamlit as st
import psycopg2
import pandas as pd
import datetime
from urllib.parse import urlparse

@st.cache_resource
def get_db_connection():
    #Establishes and returns a connection to the PostgreSQL database.
    #return psycopg2.connect(st.secrets["connections.postgresql"])

    db_uri = st.secrets["connections"]["postgresql"]["uri"]

    # Parse the URI into parts
    parsed = urlparse(db_uri)

    conn = psycopg2.connect(
        dbname=parsed.path.lstrip("/"),
        user=parsed.username,
        password=parsed.password,
        host=parsed.hostname,
        port=parsed.port,
    )
    return conn

@st.cache_data(ttl=5)
def get_orders_from_db():
    """Fetches all orders and their items from the database and returns a DataFrame."""
    conn = get_db_connection()
    df = pd.DataFrame()
    with conn.cursor() as cur:
        cur.execute("SELECT o.order_id, o.dine_option, o.submitted_at, o.status, o.payment_status, o.payment_method, i.item, i.quantity, i.subtotal FROM orders o JOIN order_items i ON o.order_id = i.order_id ORDER BY o.submitted_at DESC;")
        data = cur.fetchall()
        cols = [desc[0] for desc in cur.description]
        df = pd.DataFrame(data, columns=cols)
    #conn.close()
    return df

@st.cache_data(ttl=1)
def get_single_order_from_db(order_id):
    """Fetches a single order's details and items from the database."""
    conn = get_db_connection()
    order_details = None
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM orders WHERE order_id = %s;", (order_id,))
        order_details = cur.fetchone()
    #conn.close()
    return order_details

def insert_new_order(order_id, dine_option, items):
    """Inserts a new order and its items into the database."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM orders WHERE order_id = %s;", (order_id,))
            if cur.fetchone():
                st.error(f"Ralat: ID Pesanan {order_id} sudah wujud.")
                return False
            cur.execute("INSERT INTO orders (order_id, dine_option, submitted_at, status, payment_status, payment_method) VALUES (%s, %s, %s, %s, %s, %s);",
                        (order_id, dine_option, datetime.datetime.now(), 'Dalam Dapur', 'Belum Bayar', 'N/A'))
            for item in items:
                cur.execute("INSERT INTO order_items (order_id, item, quantity, price, subtotal) VALUES (%s, %s, %s, %s, %s);",
                            (order_id, item['Item'], item['Kuantiti'], item['Harga'], item['Subtotal']))
        conn.commit()
    except Exception as e:
        conn.rollback()
        st.error(f"Ralat pangkalan data: {e}")
        return False

    return True

def update_db_status(order_id, new_status):
    """Updates the status of an order in the database."""
    conn = get_db_connection()
    with conn.cursor() as cur:
        cur.execute("UPDATE orders SET status = %s WHERE order_id = %s;", (new_status, order_id))
    conn.commit()
    #conn.close()

def update_db_payment(order_id, payment_method):
    """Updates payment status and method in the database."""
    conn = get_db_connection()
    with conn.cursor() as cur:
        cur.execute("UPDATE orders SET payment_status = %s, payment_method = %s WHERE order_id = %s;", ('Selesai (Bayar)', payment_method, order_id))
    conn.commit()
    #conn.close()
