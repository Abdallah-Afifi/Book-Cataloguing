import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
import cv2
import os
import zxingcpp
import torch
from ultralytics import YOLO
import google.generativeai as genai
from ArabicOcr import arabicocr
from PIL import Image as PILImage
import requests
import json

# Load API keys from config.json
try:
    with open('config.json') as config_file:
        config = json.load(config_file)
except FileNotFoundError:
    raise FileNotFoundError("The config.json file was not found. Make sure it is present in the root directory.")
except json.JSONDecodeError:
    raise ValueError("There was an error decoding the config.json file. Ensure it is properly formatted.")

google_books_api_key = config.get('google_books_api_key')
generative_ai_api_key = config.get('generative_ai_api_key')

if not google_books_api_key or not generative_ai_api_key:
    raise ValueError("API keys are missing in the config.json file.")

# Configure Generative AI API Key
genai.configure(api_key=generative_ai_api_key)

# Load the pretrained YOLO model
model = YOLO('best.torchscript', task='detect')

# Load or create the local JSON database
db_file = 'book_database.json'

if not os.path.exists(db_file):
    with open(db_file, 'w') as db:
        json.dump({"books": []}, db)

# Function to start the live camera feed
def start_camera(label, var, capture_button, file_prefix):
    def capture_image():
        cap = cv2.VideoCapture(0)  # Open the device's default camera
        if not cap.isOpened():
            messagebox.showerror("Camera Error", "Unable to open the camera.")
            return

        def update_frame():
            ret, frame = cap.read()
            if ret:
                # Convert the frame to an image compatible with Tkinter
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(frame)
                img.thumbnail((300, 300))  # Adjust size as needed
                img_tk = ImageTk.PhotoImage(image=img)
                label.config(image=img_tk)
                label.image = img_tk  # Keep a reference to avoid garbage collection

            label.after(10, update_frame)  # Update the frame every 10 ms

        update_frame()

        def release_and_capture():
            ret, frame = cap.read()
            if ret:
                file_path = f"{file_prefix}_cover.jpg"
                cv2.imwrite(file_path, frame)
                var.set(file_path)
                messagebox.showinfo("Image Captured", f"{file_prefix.capitalize()} cover has been captured and saved successfully.")
            capture_button.config(state="disabled")
            cap.release()  # Release the camera after capturing the image

        capture_button.config(command=release_and_capture)

    return capture_image

# Function to search for the book by ISBN or OCR
def search_book():
    if not front_cover_path.get() or not back_cover_path.get():
        messagebox.showwarning("Missing Images", "Please capture both the front and back covers.")
        return

    # Try to detect ISBN from both images
    isbn = detect_isbn(front_cover_path.get()) or detect_isbn(back_cover_path.get())

    book_info = None

    if isbn:
        found, status, book_info = get_book_info_google_books(isbn, google_books_api_key)
        if not found:
            messagebox.showinfo("Book Not Found in Google Books", f"Book not found with status code: {status}")
            return
    else:
        # Apply OCR to the front cover if no ISBN is found
        ocr_results = apply_ocr(front_cover_path.get())
        if ocr_results:
            book_info = extract_book_info(ocr_results)
        else:
            messagebox.showerror("OCR Error", "Failed to extract text from the front cover. Please try again.")
            return

    if not book_info:
        messagebox.showerror("Book Info Error", "Unable to retrieve book information. Please try again.")
        return

    # Now search for the book in the local database
    found, local_book_info = search_local_database(book_info["title"], book_info["authors"][0], book_info["publisher"])

    if found:
        messagebox.showinfo("Book Found in Local Database", f"Book found: {local_book_info}")
    else:
        # If the book is not found, confirm with the user and add it to the local database
        confirm_and_add_book(book_info)

# Function to detect ISBN using YOLO and ZXing
def detect_isbn(image_path):
    try:
        frame = cv2.imread(image_path)
        results = model(frame)
        cropped_barcode = None
        for result in results:
            for box in result.boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                conf = box.conf.item()
                if conf < 0.82:
                    continue
                cropped_barcode = frame[y1:y2, x1:x2]
                break
        if cropped_barcode is not None:
            barcode_results = zxingcpp.read_barcodes(cropped_barcode)
            for barcode in barcode_results:
                return barcode.text
    except Exception as e:
        messagebox.showerror("Error", f"An error occurred while detecting ISBN: {e}")
    return None

# Function to query Google Books API
def get_book_info_google_books(isbn, api_key):
    try:
        url = f"https://www.googleapis.com/books/v1/volumes?q=isbn:{isbn}&key={api_key}"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            if "items" in data:
                book_info = data["items"][0]["volumeInfo"]
                return True, response.status_code, {
                    "isbn": isbn,
                    "title": book_info.get("title", "N/A"),
                    "authors": book_info.get("authors", ["N/A"]),
                    "publisher": book_info.get("publisher", "N/A"),
                }
            else:
                return False, response.status_code, {"error": "Book not found"}
        else:
            return False, response.status_code, {"error": "Failed to fetch data"}
    except requests.RequestException as e:
        messagebox.showerror("Error", f"An error occurred while fetching book data: {e}")
        return False, None, {}

# Function to apply OCR on the front cover
def apply_ocr(image_path):
    try:
        image = PILImage.open(image_path).convert('L')
        gray_image_path = 'gray_image.jpg'
        image.save(gray_image_path)
        out_image = 'out.jpg'
        results = arabicocr.arabic_ocr(gray_image_path, out_image)
        return results
    except Exception as e:
        messagebox.showerror("Error", f"An error occurred during OCR processing: {e}")
        return None

# Function to extract book info using Generative AI
def extract_book_info(ocr_results):
    try:
        response = genai.GenerativeModel(model_name="gemini-1.5-flash").generate_content(
            [f"""- Given the OCR results of a book cover: {ocr_results}, 
                - Correct the OCR results.
                - return as a JSON Object: the title, author, publisher.
                - Do not generate anything other than the JSON object."""]
        )
        book_info = json.loads(response.text)
        return {
            "title": book_info["title"],
            "authors": [book_info["author"]],
            "publisher": book_info["publisher"]
        }
    except Exception as e:
        messagebox.showerror("Error", f"An error occurred while extracting book info: {e}")
        return None

# Function to search the local JSON database
def search_local_database(title, author, publisher):
    try:
        with open(db_file, 'r') as db:
            data = json.load(db)
            for book in data["books"]:
                if (
                    book["title"].lower() == title.lower()
                    and book["authors"][0].lower() == author.lower()
                    and book["publisher"].lower() == publisher.lower()
                ):
                    return True, book
        return False, None
    except Exception as e:
        messagebox.showerror("Error", f"An error occurred while searching the local database: {e}")
        return False, None

# Function to add book to local database
def add_book_to_local_database(book_info):
    try:
        with open(db_file, 'r') as db:
            data = json.load(db)
        data["books"].append(book_info)
        with open(db_file, 'w') as db:
            json.dump(data, db, indent=4)
    except Exception as e:
        messagebox.showerror("Error", f"An error occurred while adding the book to the local database: {e}")

# Function to confirm and add the book to the local database
def confirm_and_add_book(book_info):
    confirmation_message = (
        f"Title: {book_info['title']}\n"
        f"Author: {book_info['authors'][0]}\n"
        f"Publisher: {book_info['publisher']}\n\n"
        "Do you want to add this book to the local database?"
    )
    response = messagebox.askyesno("Book Not Found", confirmation_message)
    if response:
        add_book_to_local_database(book_info)
        messagebox.showinfo("Success", "Book has been successfully added to the catalog.")
    else:
        messagebox.showinfo("Cancelled", "Book addition cancelled.")

# Setting up the main window
root = tk.Tk()
root.title("Book Cataloguing App")

# Set window size and position
root.geometry("600x600")
root.configure(bg="#f7f7f7")

# Adding a title label
title_label = tk.Label(root, text="Book Cataloguing App", font=("Arial", 20, "bold"), bg="#4a90e2", fg="white", pady=10)
title_label.pack(fill=tk.X)

# Adding a logo to the top left
logo = Image.open("/home/abdallah/Pictures/logo.jpeg")  # Replace with the actual path
logo.thumbnail((50, 50))  # Increase the size of the logo
logo_img = ImageTk.PhotoImage(logo)
logo_label = tk.Label(root, image=logo_img, bg="#4a90e2")
logo_label.place(x=10, y=10)

# Variables to hold file paths
front_cover_path = tk.StringVar(value="")
back_cover_path = tk.StringVar(value="")

# Front Cover Section with live camera preview
front_cover_frame = tk.Frame(root, bg="#f7f7f7")
front_cover_frame.pack(pady=10, fill=tk.X, padx=20)

front_cover_label = tk.Label(front_cover_frame, bg="#f7f7f7")
front_cover_label.pack(pady=5)  # Display live feed here
front_capture_button = tk.Button(front_cover_frame, text="Capture Front Cover", bg="#4a90e2", fg="white", font=("Arial", 12), padx=10, pady=5)
front_capture_button.pack(pady=5)  # Center the button

# Back Cover Section with live camera preview
back_cover_frame = tk.Frame(root, bg="#f7f7f7")
back_cover_frame.pack(pady=10, fill=tk.X, padx=20)

back_cover_label = tk.Label(back_cover_frame, bg="#f7f7f7")
back_cover_label.pack(pady=5)  # Display live feed here
back_capture_button = tk.Button(back_cover_frame, text="Capture Back Cover", bg="#4a90e2", fg="white", font=("Arial", 12), padx=10, pady=5)
back_capture_button.pack(pady=5)  # Center the button

# Start the camera and set capture button commands
front_capture_command = start_camera(front_cover_label, front_cover_path, front_capture_button, "front")
back_capture_command = start_camera(back_cover_label, back_cover_path, back_capture_button, "back")

front_capture_button.config(command=front_capture_command)
back_capture_button.config(command=back_capture_command)

# Search Button with a different color
search_button = tk.Button(root, text="Search Book", command=search_book, bg="#f44336", fg="white", font=("Arial", 14), padx=20, pady=10)
search_button.pack(pady=20)  # Center the button

# Start the GUI event loop
root.mainloop()
