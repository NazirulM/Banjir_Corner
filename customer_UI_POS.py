import streamlit as st
import pandas as pd
import datetime
import time
from logic_POS import add_to_order, submit_order, update_order_status, update_payment_status, setup_session_state, remove_from_order
from db_POS import get_orders_from_db, get_single_order_from_db
from menu_dict import MENU, FOOD_CLASSIFIER

# --- General Helper Functions ---

def get_menu_item_details(category, item_name):
    """Safely retrieves the item's configuration dict or base price."""
    item_data = MENU.get(category, {}).get(item_name)
    print(item_data)
    
    if isinstance(item_data, dict):
        base_price = item_data.get("base_price", 0.00)
        is_configurable = True
    else:
        base_price = item_data
        is_configurable = False
        
    return base_price, is_configurable, item_data

def finalize_configuration(item_data, key_to_reset, remarks_text):
    """Handles submission, calculates final price, and adds the custom item to order."""
    
    base_item = item_data['name']
    base_price = item_data['base_price']
    
    final_price = base_price
    config_details = []
    
    # 1. Process Variants and Add-ons dynamically
    config_settings = get_menu_item_details(item_data['category'], base_item)[2]

    # Check Requirements and Calculate Price
    required_variant_selected = True
    
    for key, config in config_settings.items():
        if isinstance(config, dict) and key != 'base_price': 
            session_key = f"{base_item}_{key}_selection" 
            selection = st.session_state.get(session_key)

            if config.get('required') and not selection:
                required_variant_selected = False
                st.error(f"Sila pilih satu dari {config['label']}.")
                break
            
            if selection:
                if config['type'] == 'radio':
                    final_price += config['options'][selection]
                    config_details.append(selection)
                elif config['type'] == 'multiselect':
                    for add_on in selection:
                        final_price += config['options'][add_on]
                        config_details.append(add_on)

    if not required_variant_selected:
        return

    # 2. Final Item Name
    customized_item_name = f"{base_item}"
    if config_details:
        customized_item_name += f" ({', '.join(config_details)})"
    
    # 3. If editing, replace existing order entry
    if "edit_index" in item_data:
        idx = item_data["edit_index"]
        st.session_state.current_order[idx] = {
            "Item": customized_item_name,
            "Harga": final_price,
            "Kuantiti": 1,
            "Subtotal": final_price,
            "Catatan": remarks_text,
            "Configurable": True
        }
        del st.session_state.item_to_configure["edit_index"]
    else:
        # Normal add flow
        add_to_order(customized_item_name, final_price, 1, remarks_text, configurable=True)
    
    # Clear remarks field state
    remarks_key = f"{item_data['name']}_remarks"
    if remarks_key in st.session_state:
        del st.session_state[remarks_key]
        
    # Update the input box to reflect the total quantity for this base item
    total_qty = get_total_item_quantity(base_item)
    st.session_state[key_to_reset] = total_qty

    # hide config and refresh UI
    st.session_state.item_to_configure = None

    # if we came from edit mode, go back to checkout
    if st.session_state.get("return_to_checkout", False):
        st.session_state.view_state = "checkout"
        st.session_state.return_to_checkout = False
    else:
        st.session_state.view_state = "menu"

    st.rerun()

def calculate_current_cost(item_name, base_price, config_settings):
    """Calculates the current cost based on selections stored in st.session_state."""
    current_cost = base_price

    if config_settings:
        for key, config in config_settings.items():
            if isinstance(config, dict) and key != 'base_price':
                session_key = f"{item_name}_{key}_selection"
                selection = st.session_state.get(session_key)

                if selection:
                    if config['type'] == 'radio':
                        # Variant (single selection)
                        # Selection is the string name, use it to look up the price
                        current_cost += config['options'].get(selection, 0)
                    elif config['type'] == 'multiselect':
                        # Add-ons (multiple selection)
                        for add_on in selection:
                            # Selection is a list of string names
                            current_cost += config['options'].get(add_on, 0)
    return current_cost


def show_item_config(item_data):
    """Renders a reusable, dynamic configuration pop-up for any complex item."""
    
    item_name = item_data['name']
    base_price = item_data['base_price']
    quantity = item_data['quantity']
    key_to_reset = item_data['key_to_reset']
    category = item_data['category']
    
    config_settings = get_menu_item_details(category, item_name)[2]

    remarks_key = f"{item_name}_remarks" 
    
    # CRITICAL FIX: Removed st.form() and replaced it with st.container()
    with st.container(border=True):
        st.subheader(f"Customize your {item_name}")
        
        # --- Dynamically Render Variants and Add-ons ---
        
        if config_settings:
            for key, config in config_settings.items():
                if isinstance(config, dict) and key != 'base_price':
                    st.markdown("---")
                    st.markdown(f"##### **{config['label']}**")
                    
                    price_options = config['options']
                    price_str = ", ".join([f"{opt} (+RM{price:.2f})" for opt, price in price_options.items()])
                    st.caption(f"Pilihan Harga: {price_str}")
                    
                    session_key = f"{item_name}_{key}_selection" 
                    
                    # Ensure selection key is initialized for the first render
                    if session_key not in st.session_state:
                        st.session_state[session_key] = None if config['type'] == 'radio' else []

                    if config['type'] == 'radio' and config.get('required'):
                        # Variants (Required Radio Button)
                        st.radio(
                            config['label'],
                            list(price_options.keys()),
                            index=None,
                            key=session_key,
                            label_visibility="collapsed"
                        )
                        
                    elif config['type'] == 'multiselect':
                        # Add-ons (Optional Multiselect)
                        st.multiselect(
                            config['label'],
                            list(price_options.keys()),
                            key=session_key,
                            # Default is handled by the initial state setup above
                            label_visibility="collapsed"
                        )
        
        # 🚀 START: NEW REMARKS FIELD 🚀
        st.markdown("---")
        st.markdown("##### **Nota Khas/Permintaan (Pilihan)**")
        st.text_area(
            "Sila masukkan permintaan khas anda di sini (e.g., Kurang Pedas, Taknak Sayur)",
            key=remarks_key,
            height=70,
            label_visibility="collapsed"
        )
        # 🚀 END: NEW REMARKS FIELD 🚀
        
        # --- Dynamic Price Estimation (This now reruns with the app state) ---
        
        # Calculation is called here:
        current_cost = calculate_current_cost(item_name, base_price, config_settings)
        
        st.markdown("---")
        st.metric(label="Harga per Unit", value=f"RM{current_cost:.2f}")

        # --- Submission Buttons (Now use regular st.button) ---
        col_submit, col_cancel = st.columns(2)
        
        with col_submit:
            # Check requirements manually before finalizing
            is_valid = True
            for key, config in config_settings.items():
                if key == 'variants' and config.get('required'):
                    session_key = f"{item_name}_{key}_selection" 
                    if not st.session_state.get(session_key):
                        is_valid = False
                        st.error("Sila pilih satu varian yang wajib (Mandatory Variant).")
                        break # Stop checking if mandatory variant is missing
            
            if st.button("✅ Sahkan Pesanan", use_container_width=True, disabled=not is_valid):
                # The finalize function validates and adds the item
                finalize_configuration(item_data, key_to_reset, remarks_key)
        
        with col_cancel:
            if st.button("❌ Batal Pesanan", type="secondary", use_container_width=True):
                st.session_state[key_to_reset] = 0
                st.session_state.item_to_configure = None

                if st.session_state.get("return_to_checkout", False):
                    st.session_state.view_state = "checkout"
                    st.session_state.return_to_checkout = False
                else:
                    st.session_state.view_state = "menu"

                st.rerun() 

# --- Helper Functions (Remaining functions are unchanged) ---

def quantity_changed(item_name, category, unique_key):
    """
    Handles changes in the st.number_input for an item.
    Updates order quantity directly instead of resetting to 0.
    """
    
    new_qty = st.session_state[unique_key]
    
    # Do nothing if quantity is zero AND there is no existing entry (to avoid noise)
    base_price, is_configurable, _ = get_menu_item_details(category, item_name)

    if base_price is None:
        st.error(f"⚠️ Base price not found for {item_name} (category: {category})")
        return

    if is_configurable:
        # Trigger configuration pop-up only if new_qty > 0
        if new_qty > 0:
            st.session_state.item_to_configure = {
                'name': item_name,
                'base_price': base_price,
                'quantity': new_qty,
                'key_to_reset': unique_key,
                'category': category
            }
            # keep the input value as-is (we will update it after config is added)
    else:
        # Update existing exact-match item if present; otherwise add new
        found = False
        for item in list(st.session_state.current_order):  # copy to allow remove
            if item['Item'] == item_name:
                found = True
                if new_qty > 0:
                    item['Kuantiti'] = new_qty
                    item['Subtotal'] = base_price * new_qty
                else:
                    # remove item if user sets to 0
                    st.session_state.current_order.remove(item)
                break

        if not found and new_qty > 0:
            add_to_order(item_name, base_price, new_qty, "")
        # DO NOT reset st.session_state[unique_key] here — leave the box showing the chosen qty


def get_total_item_quantity(base_item):
    """Calculates the total quantity of a base item (ignoring variations) in the current order."""
    total_qty = 0
    if not st.session_state.current_order:
        return 0
        
    for item in st.session_state.current_order:
        # Check if the item name starts with the base item name (e.g., "Mi Bandung" is the start of "Mi Bandung (Ayam, Telur)")
        if item['Item'].startswith(base_item):
            total_qty += item['Kuantiti']
    return total_qty

def render_menu_item(item_name, table_number, category_name):
    """Helper to render a single menu item with quantity control."""
    unique_key = f"qty_{item_name}_{table_number}_{category_name}"

    if unique_key not in st.session_state:
        st.session_state[unique_key] = 0

    current_ordered_qty = get_total_item_quantity(item_name)
    st.session_state[unique_key] = current_ordered_qty  # keep in sync

    col_item_name, col_item_qty_input = st.columns([3, 1])
    with col_item_name:
        st.write(item_name)
    with col_item_qty_input:
        st.number_input(
            "Kuantiti",
            min_value=0,
            value=current_ordered_qty,
            key=unique_key,
            on_change=quantity_changed,
            args=(item_name, category_name, unique_key),
            label_visibility="collapsed"
        )

def render_menu_category(category_name, menu_items, table_number):
    """
    Renders the menu for a specific category.
    - If category_name == "makanan", it expands into food subcategories (Mi Bandung, Sup & Bakso, Western).
    - Otherwise, it falls back to showing items directly from menu_items[category_name].
    """

    # --- Special handling: makanan expands into food subcategories ---
    if category_name == "makanan":
        subcategories = ["Mi Bandung", "Sup & Bakso", "Western"]
        for subcat in subcategories:
            with st.container(border=True):
                st.subheader(subcat)

                # Get items for this subcategory using FOOD_CLASSIFIER
                items_in_subcat = [
                    item_name for item_name in menu_items.keys()
                    if FOOD_CLASSIFIER.get(item_name) == subcat
                ]

                if not items_in_subcat:
                    st.info(f"Tiada menu dalam kategori {subcat}.")
                    continue

                for item_name in items_in_subcat:
                    render_menu_item(item_name, table_number, "makanan")
        return

    # other categories (menu_items is already that category's dict)
    items_in_category = menu_items.keys()

    if not items_in_category:
        st.info(f"Tiada menu dalam kategori {category_name}.")
        return

    with st.container(border=True):
        st.subheader(category_name)
        for item_name in items_in_category:
            render_menu_item(item_name, table_number, category_name)



def reset_customer_view_state():
    """Function to clear all customer-related session state keys and return to menu."""
    if 'submitted_order_id' in st.session_state:
        del st.session_state.submitted_order_id
    if 'view_state' in st.session_state:
        st.session_state.view_state = 'menu'
    if 'takeaway_order_id' in st.session_state:
        del st.session_state.takeaway_order_id
    if 'create_new_order' in st.session_state:
        del st.session_state.create_new_order
    if 'item_to_configure' in st.session_state:
        del st.session_state.item_to_configure


def display_order_status(order_id_input):
    """Displays the status of the submitted order without elapsed time."""
    st.header("⏳ Status Pesanan Anda")
    
    with st.spinner(f"Memuatkan status pesanan `{order_id_input}`..."):
        time.sleep(1) 
        order_details = get_single_order_from_db(order_id_input) 
        
    if not order_details:
        st.error(f"Pesanan dengan ID `{order_id_input}` tidak ditemui.")
        st.markdown("---")
        if st.button("➡️ Buat Pesanan Baru", use_container_width=True):
            st.session_state.create_new_order = True
            st.rerun()
        return

    status = order_details[3]

    if status == 'Siap Dihidangkan':
         st.success(f"Status: **{status}**! Sila tunggu kakitangan menghidangkan pesanan anda.")
    elif status == 'Dalam Dapur':
         st.warning(f"Status: **{status}**. Pesanan anda baru sahaja dimasukkan.")
    else:
         st.info(f"Status: **{status}**. Pesanan anda sedang disiapkan.")

    st.markdown(f"**ID Pesanan:** `{order_id_input}`")
    st.markdown(f"**Pilihan:** `{order_details[1]}`")
    
    st.markdown("---")
    
    if st.button("➡️ Buat Pesanan Baru", use_container_width=True):
        st.session_state.create_new_order = True
        st.rerun()


# --- Main Interface ---

def customer_interface(table_number, user_type):
    """Renders the UI for the customer to place an order or view status."""
    setup_session_state()
    
    if st.session_state.get('create_new_order', False):
        reset_customer_view_state() 
    
    if st.session_state.get('item_to_configure'):
        show_item_config(st.session_state.item_to_configure)
        return

    # --- Initialization & Status Check (Unchanged) ---
    is_takeaway_only = user_type == "customer" and not table_number
    if table_number:
        order_id_input = f"MEJA-{table_number}"
        dine_option_default = "Dine-In"
    else:
        if 'takeaway_order_id' not in st.session_state or st.session_state.view_state == 'menu':
             timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
             st.session_state.takeaway_order_id = f"TAKEAWAY-{timestamp}"
             
        order_id_input = st.session_state.takeaway_order_id
        dine_option_default = "Take-Away"
    
    if 'view_state' not in st.session_state:
        st.session_state.view_state = 'menu'
    
    if 'menu_category' not in st.session_state:
        st.session_state.menu_category = 'makanan' 
    
    if st.session_state.get('submitted_order_id') and not st.session_state.get('create_new_order', False):
        display_order_status(st.session_state.submitted_order_id)
        return
        
    with st.sidebar:
        pass
            
    # --- MAIN CONTENT: Checkout State ---
    if st.session_state.view_state == 'checkout' and st.session_state.current_order:
        st.header("🧾 Checkout Pesanan")
        
        st.info(f"ID Pesanan: **`{order_id_input}`**")
        if table_number:
            st.info(f"Nombor Meja: **`{table_number}`**")
            
        st.markdown("---")
        st.markdown("### **Ringkasan Pesanan**")
        
        for index, item_data in enumerate(st.session_state.current_order):
            with st.container(border=True): 
                col_item_name, col_item_qty = st.columns([4, 2])
                with col_item_name:
                    st.markdown(f"**{item_data['Item']}**")
                with col_item_qty:
                    st.write(f"Kuantiti: **{item_data['Kuantiti']}**")

                col_price, col_actions = st.columns([3, 4])
                with col_price:
                    st.subheader(f"RM{item_data['Subtotal']:.2f}")
                with col_actions:
                    action_cols = st.columns([1, 1])
                    
                    # ✅ Edit button for configurable items
                    if item_data.get("Configurable", False):
                        if action_cols[0].button("✏️ Edit", key=f"edit_{index}", use_container_width=True):
                            st.session_state.item_to_configure = {
                                "name": item_data['Item'].split(" (")[0],
                                "base_price": item_data['Harga'],
                                "quantity": item_data['Kuantiti'],
                                "key_to_reset": f"{item_data['Item']}_qty",
                                "category": item_data.get("Category", "makanan"),
                                "edit_index": index
                            }
                            st.session_state.return_to_checkout = True
                            st.session_state.view_state = "menu"
                            st.rerun()
                    else:
                        # keep spacing consistent
                        action_cols[0].write("")  

                    # ❌ Cancel button (always shown)
                    if action_cols[1].button("❌ Batal", key=f"cancel_{index}", use_container_width=True):
                        remove_from_order(index) 

        if st.session_state.current_order:
            order_df = pd.DataFrame(st.session_state.current_order)
            total_price = order_df['Subtotal'].sum()
        else:
            total_price = 0.00
            
        st.markdown("---")
        st.metric(label="Total Perlu Dibayar", value=f"RM{total_price:.2f}")
        st.markdown("---")
        
        with st.form("checkout_form"):
            if is_takeaway_only or dine_option_default == "Take-Away":
                dine_option = st.selectbox("Pilihan (Wajib)", ["Take-Away"], disabled=True)
            elif dine_option_default == "Dine-In":
                dine_option = st.selectbox("Pilihan (Wajib)", ["Dine-In", "Take-Away"], index=0)
            else:
                dine_option = st.selectbox("Pilihan (Wajib)", ["Dine-In", "Take-Away"])
            
            submitted = st.form_submit_button("✅ Hantar Pesanan ke Dapur", use_container_width=True)
            
            if submitted:
                if dine_option:
                    st.session_state.submitted_order_id = order_id_input
                    submit_order(order_id_input, dine_option) 
                else:
                    st.error("Sila pilih pilihan 'Dine-In' atau 'Take-Away'.")

        if st.button("⬅️ Kembali ke Menu", use_container_width=True):
            st.session_state.view_state = 'menu'
            st.rerun()

    elif st.session_state.view_state == 'checkout' and not st.session_state.current_order:
        st.session_state.view_state = 'menu'
        st.rerun()

    # --- MAIN CONTENT: Menu State ---
    else: 
        st.header("Selamat Datang Encik/Cik nak order apa? 😊")
        
        if is_takeaway_only:
            # st.warning("Anda kini membuat pesanan **Bawa Pulang**.")
            st.info(f"ID Pesanan: **`{order_id_input}`**")
        
        st.markdown("---")
        
        # --- CATEGORY NAVIGATION AREA ---
        st.subheader("Pilih Kategori Menu:")
        col_food, col_drink = st.columns(2)
        
        food_style = "primary" if st.session_state.menu_category == 'makanan' else "secondary"
        drink_style = "primary" if st.session_state.menu_category == 'minuman' else "secondary"

        with col_food:
            if st.button("🍽️ Makanan", use_container_width=True, type=food_style):
                st.session_state.menu_category = 'makanan'
                st.rerun() 
        with col_drink:
            if st.button("☕ Minuman", use_container_width=True, type=drink_style):
                st.session_state.menu_category = 'minuman'
                st.rerun() 
                
        st.markdown("---")
        
        selected_category = st.session_state.menu_category
        
        render_menu_category(selected_category, MENU[selected_category], table_number)

        # 🚀 START: SIMPLIFIED FOOTER 🚀
        if st.session_state.current_order:
            st.markdown("---")
            
            # Recalculate total for the checkout button help
            order_df = pd.DataFrame(st.session_state.current_order)
            total_price = order_df['Subtotal'].sum()
            
            checkout_label = f"🧾 Checkout Pesanan (RM{total_price:.2f})"

            if st.button(checkout_label, key="main_checkout_btn", type="primary", use_container_width=True):
                st.session_state.view_state = 'checkout'
                st.rerun()



