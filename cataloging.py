import cv2
import torch
from ultralytics import YOLO
import os
import zxingcpp
import requests
# Load the pretrained YOLO model from TorchScript
model = YOLO('best.torchscript', task = 'detect')

# Open a connection to the camera (0 is usually the default camera)
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("Error: Could not open video stream from the camera.")
    exit()
running = True
output_dir = 'cropped_barcodes'
os.makedirs(output_dir, exist_ok=True)
frame_count = 0
cropped_barcode = None
while running:
    # Capture frame-by-frame
    ret, frame = cap.read()
    if not ret:
        print("Error: Could not read frame.")
        break

    # Run the YOLO model on the frame
    results = model(frame)

    # Extract the predicted bounding boxes and labels
    for result in results:
        for box in result.boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())  # Convert tensor to list and then to int
            conf = box.conf.item()  # Get the confidence score
            label = box.cls.item()  # Get the label
            if(conf < 0.82): 
                continue
            # Draw the bounding box and label on the frame
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(frame, f'{label} {conf:.2f}', (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
            # Crop the detected barcode region from the frame
            cropped_barcode = frame[y1:y2, x1:x2]
            # Save the cropped image
            cropped_filename = os.path.join(output_dir, f'cropped_barcode_{frame_count}.png')
            cv2.imwrite(cropped_filename, cropped_barcode)
            #frame_count += 1q
            running = False


    # Display the resulting frame
    cv2.imshow('YOLOv8 Real-Time Detection', frame)

    # Break the loop on 'q' key press
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# When everything is done, release the capture
cap.release()
cv2.destroyAllWindows()
results = zxingcpp.read_barcodes(cropped_barcode)
isbn = None
for result in results:
    isbn = result.text
    print('Found barcode:'
          f'\n Text:    "{result.text}"'
          f'\n Format:   {result.format}'
          f'\n Content:  {result.content_type}'
          f'\n Position: {result.position}')
       
if len(results) == 0:
	print("Could not find any barcode.")

# Function to query Google Books API
def get_book_info_google_books(isbn, api_key):
    url = f"https://www.googleapis.com/books/v1/volumes?q=isbn:{isbn}&key={api_key}"
    response = requests.get(url)
    found = False
    if response.status_code == 200:
        data = response.json()
        if "items" in data:
            found = True
            book_info = data["items"][0]["volumeInfo"]
            return found, response.status_code, {
                "title": book_info.get("title", "N/A"),
                "authors": book_info.get("authors", "N/A"),
                "publishedDate": book_info.get("publishedDate", "N/A"),
                "description": book_info.get("description", "N/A"),
                "pageCount": book_info.get("pageCount", "N/A"),
                "categories": book_info.get("categories", "N/A"),
                "averageRating": book_info.get("averageRating", "N/A"),
                "thumbnail": book_info.get("imageLinks", {}).get("thumbnail", "N/A"),
            }
        else:
            return found, response.status_code, {"error": "Book not found"}
    else:
        return found, response.status_code, {"error": "Failed to fetch data"}

# Query Google Books API with the ISBN
api_key = "AIzaSyDOLH0ln7zoMNFLT1S4w5EmhP1cvwywJoA"  # Replace with your API key
found, status, book_info = get_book_info_google_books(isbn, api_key)
if found:
    print(f"Book found: {book_info}")
else:
    print(f"Not found with status code: {status}")