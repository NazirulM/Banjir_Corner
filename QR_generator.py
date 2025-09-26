import qrcode
import os

# --- Configuration ---
# Set the base URL of your Streamlit app.
# If running locally, this will be http://localhost:8501
# If hosted, this will be your hosted app's URL.
BASE_URL = "http://localhost:8501"

# Define the number of tables for which to generate QR codes.
NUMBER_OF_TABLES = 10

# Define the directory where QR code images will be saved.
OUTPUT_DIR = "qrcodes"

# --- Main Script ---
# Create the output directory if it does not exist
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)
    print(f"Directory '{OUTPUT_DIR}' created.")

print("Generating QR codes...")
print("-" * 25)

for table_number in range(1, NUMBER_OF_TABLES + 1):
    # Construct the URL with the table number as a query parameter
    url = f"{BASE_URL}/?table={table_number}"
    
    # Create the QR code object
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(url)
    qr.make(fit=True)
    
    # Create the QR code image
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Define the file path and save the image
    file_path = os.path.join(OUTPUT_DIR, f"table_{table_number}.png")
    img.save(file_path)
    
    print(f"Generated QR code for Table {table_number}: {file_path}")

print("-" * 25)
print("QR code generation complete. You can find the images in the 'qrcodes' directory.")
