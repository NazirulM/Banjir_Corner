# --- Data & Menu (Updated for Configuration) ---
MENU = {
    "makanan": {
        "Mi Bandung Biasa": {
            "base_price": 6.00,
            "addons": {
                "label": "Add-Ons (Optional)",
                "type": "multiselect",
                "options": {"Extra Telur": 1.00, "Extra Mi": 1.00, "Extra Protein": 2.00},
                "required": False,
            }
        },
        "Mi Bandung Daging": {
            "base_price": 9.00,
            "addons": {
                "label": "Add-Ons (Optional)",
                "type": "multiselect",
                "options": {"Extra Telur": 1.00, "Extra Mi": 1.00, "Extra Protein": 2.00},
                "required": False,
            }
        },
        "Mi Bandung Ayam": {
            "base_price": 8.00,
            "addons": {
                "label": "Add-Ons (Optional)",
                "type": "multiselect",
                "options": {"Extra Telur": 1.00, "Extra Mi": 1.00, "Extra Protein": 2.00},
                "required": False,
            }
        },
        "Mi Bandung Kerang": {
            "base_price": 8.00,
            "addons": {
                "label": "Add-Ons (Optional)",
                "type": "multiselect",
                "options": {"Extra Telur": 1.00, "Extra Mi": 1.00, "Extra Protein": 2.00},
                "required": False,
            }
        },
        "Mi Bandung Udang": {
            "base_price": 12.00,
            "addons": {
                "label": "Add-Ons (Optional)",
                "type": "multiselect",
                "options": {"Extra Telur": 1.00, "Extra Mi": 1.00, "Extra Protein": 2.00},
                "required": False,
            }
        },
        "Mi Bandung Special": {
            "base_price": 18.00,
            "addons": {
                "label": "Add-Ons (Optional)",
                "type": "multiselect",
                "options": {"Extra Telur": 1.00, "Extra Mi": 1.00, "Extra Protein": 2.00},
                "required": False,
            }
        },
        "Sup Ayam": {
            "base_price": 8.00,
            "carbo": {
                "label": "Carbo",
                "type": "radio",
                "options": {"Bihun": 1.00, "Nasi Putih": 1.00, "Nasi Impit": 1.00, "Mi Kuning": 1.00},
                "required": True
            },
            "addons": {
                "label": "Add-Ons",
                "type": "multiselect",
                "options": {"Bihun": 1.00, "Nasi Putih": 1.00, "Nasi Impit": 1.00, "Mi Kuning": 1.00,
                            "Ayam": 2.00, "Daging": 2.00, "tetel": 2.00, "kambing": 2.00, "gearbox": 10.00},
                "required": False
            }
        },
        "Sup Daging": {
            "base_price": 9.00,
            "carbo": {
                "label": "Carbo",
                "type": "radio",
                "options": {"Bihun": 1.00, "Nasi Putih": 1.00, "Nasi Impit": 1.00, "Mi Kuning": 1.00},
                "required": True
            },
            "addons": {
                "label": "Add-Ons",
                "type": "multiselect",
                "options": {"Bihun": 1.00, "Nasi Putih": 1.00, "Nasi Impit": 1.00, "Mi Kuning": 1.00,
                            "Ayam": 2.00, "Daging": 2.00, "tetel": 2.00, "kambing": 2.00, "gearbox": 10.00},
                "required": False
            }
        },
        "Sup Tetel": {
            "base_price": 8.00,
            "carbo": {
                "label": "Carbo",
                "type": "radio",
                "options": {"Bihun": 1.00, "Nasi Putih": 1.00, "Nasi Impit": 1.00, "Mi Kuning": 1.00},
                "required": True
            },
            "addons": {
                "label": "Add-Ons",
                "type": "multiselect",
                "options": {"Bihun": 1.00, "Nasi Putih": 1.00, "Nasi Impit": 1.00, "Mi Kuning": 1.00,
                            "Ayam": 2.00, "Daging": 2.00, "tetel": 2.00, "kambing": 2.00, "gearbox": 10.00},
                "required": False
            }
        },
        "Sup Kambing": {
            "base_price": 12.00,
            "carbo": {
                "label": "Carbo",
                "type": "radio",
                "options": {"Bihun": 1.00, "Nasi Putih": 1.00, "Nasi Impit": 1.00, "Mi Kuning": 1.00},
                "required": True
            },
            "addons": {
                "label": "Add-Ons",
                "type": "multiselect",
                "options": {"Bihun": 1.00, "Nasi Putih": 1.00, "Nasi Impit": 1.00, "Mi Kuning": 1.00,
                            "Ayam": 2.00, "Daging": 2.00, "tetel": 2.00, "kambing": 2.00, "gearbox": 10.00},
                "required": False
            }
        },
        "Sup Gearbox": {
            "base_price": 15.00,
            "carbo": {
                "label": "Carbo",
                "type": "radio",
                "options": {"Bihun": 1.00, "Nasi Putih": 1.00, "Nasi Impit": 1.00, "Mi Kuning": 1.00},
                "required": True
            },
            "addons": {
                "label": "Add-Ons",
                "type": "multiselect",
                "options": {"Bihun": 1.00, "Nasi Putih": 1.00, "Nasi Impit": 1.00, "Mi Kuning": 1.00,
                            "Ayam": 2.00, "Daging": 2.00, "tetel": 2.00, "kambing": 2.00, "gearbox": 10.00},
                "required": False
            }
        },
        "Bakso Biasa": {
            "base_price": 6.00,
            "carbo": {
                "label": "Carbo",
                "type": "radio",
                "options": {"Bihun": 1.00, "Nasi Putih": 1.00, "Nasi Impit": 1.00, "Mi Kuning": 1.00},
                "required": True
            },
            "addons": {
                "label": "Add-Ons (Optional)",
                "type": "multiselect",
                "options": {"Sayur": 0.50, "Kentang": 0.50},
                "required": False
            }
        },
        "Bakso Daging": {
            "base_price": 9.00,
            "carbo": {
                "label": "Carbo",
                "type": "radio",
                "options": {"Bihun": 1.00, "Nasi Putih": 1.00, "Nasi Impit": 1.00, "Mi Kuning": 1.00},
                "required": True
            },
            "addons": {
                "label": "Add-Ons (Optional)",
                "type": "multiselect",
                "options": {"Sayur": 0.50, "Kentang": 0.50},
                "required": False
            }
        },
        "Bakso Ayam": {
            "base_price": 8.00,
            "carbo": {
                "label": "Carbo",
                "type": "radio",
                "options": {"Bihun": 1.00, "Nasi Putih": 1.00, "Nasi Impit": 1.00, "Mi Kuning": 1.00},
                "required": True
            },
            "addons": {
                "label": "Add-Ons (Optional)",
                "type": "multiselect",
                "options": {"Sayur": 0.50, "Kentang": 0.50},
                "required": False
            }
        },
        "Bakso Mercun": {
            "base_price": 10.00,
            "carbo": {
                "label": "Carbo",
                "type": "radio",
                "options": {"Bihun": 1.00, "Nasi Putih": 1.00, "Nasi Impit": 1.00, "Mi Kuning": 1.00},
                "required": True
            },
            "addons": {
                "label": "Add-Ons (Optional)",
                "type": "multiselect",
                "options": {"Sayur": 0.50, "Kentang": 0.50},
                "required": False
            }
        },
        "Bakso Beranak": {
            "base_price": 12.00,
            "carbo": {
                "label": "Carbo",
                "type": "radio",
                "options": {"Bihun": 1.00, "Nasi Putih": 1.00, "Nasi Impit": 1.00, "Mi Kuning": 1.00},
                "required": True
            },
            "addons": {
                "label": "Add-Ons (Optional)",
                "type": "multiselect",
                "options": {"Sayur": 0.50, "Kentang": 0.50},
                "required": False
            }
        },
        "Chicken Chop": 7.00,
        "Chicken Chop Cheese": 8.00,
        "Lamb Chop": 19.00,
        "Grilled Chicken Chop": 13.00,
        "French Fries": 5.00,
        "Spaghetti Bolognese": 7.00,
        "Spaghetti Carbonara": 7.00,
        "Fish N Chips": 7.00,
        "Chicken Popcorn": 8.00
    },
    "minuman": {
        "Teh O Ais": 3.00,
        "Sirap Limau": 3.50,
        "Kopi Panas": 2.50,
        "Jus Oren": 4.00,
    }
}

food_category = ["Mi Bandung", "Sup & Bakso", "Western"]

FOOD_CLASSIFIER = {
    # Mi Bandung Category
    "Mi Bandung Biasa": food_category[0],
    "Mi Bandung Daging": food_category[0],
    "Mi Bandung Ayam": food_category[0],
    "Mi Bandung Kerang": food_category[0],
    "Mi Bandung Udang": food_category[0],
    "Mi Bandung Special": food_category[0], 

    # Sup & Bakso Category
    "Sup Daging": food_category[1],
    "Sup Ayam": food_category[1],
    "Sup Kambing": food_category[1],
    "Sup Tetel": food_category[1],
    "Sup Gearbox": food_category[1],
    "Bakso Daging": food_category[1],
    "Bakso Ayam": food_category[1],
    "Bakso Kambing": food_category[1],
    "Bakso Tetel": food_category[1],

    # Western Category
    "Chicken Chop": food_category[2],
    "Chicken Chop Cheese": food_category[2],
    "Grilled Chicken Chop": food_category[2],
    "Nasi Putih Grilled Chicken Chop": food_category[2],
    "Lamb Chop": food_category[2],
    "French Fries": food_category[2],
    "Spaghetti Carbonara": food_category[2],
    "Spaghetti Bolognese": food_category[2]
}