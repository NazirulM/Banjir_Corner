import streamlit as st
import pandas as pd

# ==================== EMPLOYEE INTERFACE ====================

def employee_interface():
    st.title("👩‍🍳 Employee Dashboard")

    # Tabs for different employee functions
    tab_orders, tab_menu = st.tabs(["📦 Orders", "🍽️ Menu Management"])

    with tab_orders:
        st.subheader("Incoming Orders")
        if "orders" not in st.session_state:
            st.session_state.orders = []  # Placeholder for DB orders

        if len(st.session_state.orders) == 0:
            st.info("No incoming orders.")
        else:
            for idx, order in enumerate(st.session_state.orders):
                with st.container(border=True):
                    st.write(f"Order ID: {order['id']} | Table: {order.get('table', '-')}")
                    st.write(f"Items: {order['items']}")
                    st.write(f"Status: {order['status']}")

                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("✅ Mark Prepared", key=f"prep_{idx}"):
                            order['status'] = "prepared"
                            st.rerun()
                    with col2:
                        if st.button("✅ Mark Served", key=f"serve_{idx}"):
                            order['status'] = "served"
                            st.rerun()

    with tab_menu:
        st.subheader("Manage Menu")
        if "menu_items" not in st.session_state:
            st.session_state.menu_items = []  # Placeholder for DB menu

        if len(st.session_state.menu_items) == 0:
            st.info("No menu items defined.")
        else:
            menu_df = pd.DataFrame(st.session_state.menu_items)
            st.table(menu_df)

        with st.form("add_item_form"):
            name = st.text_input("Item Name")
            price = st.number_input("Price (RM)", min_value=0.0, step=0.1)
            category = st.selectbox("Category", ["Makanan", "Minuman"])
            submitted = st.form_submit_button("Add Item")
            if submitted:
                st.session_state.menu_items.append({
                    "name": name,
                    "price": price,
                    "category": category
                })
                st.success("Item added.")
                st.rerun()