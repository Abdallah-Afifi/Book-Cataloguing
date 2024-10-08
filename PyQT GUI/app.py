from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import sys
import cv2
import torch
from ultralytics import YOLO 
import zxingcpp
import os
import requests
import csv
from PIL import Image
import google.generativeai as genai
from ArabicOcr import arabicocr
import json

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
                "author": book_info.get("authors", "N/A"),
            }
        else:
            return found, response.status_code, {"error": "Book not found"}
    else:
        return found, response.status_code, {"error": "Failed to fetch data"}

# Function to handle OCR and generative AI
def handle_ocr_and_ai():
    image_path = 'front.jpg'
    image = Image.open(image_path).convert('L')
    gray_image_path = 'tao_gray.jpg'
    image.save(gray_image_path)

    out_image = 'out.jpg'
    results = arabicocr.arabic_ocr(gray_image_path, out_image)

    genai.configure(api_key="AIzaSyCRraP31AXCemHJLmiv38lOIYry-UTw5vE")
    img = Image.open(gray_image_path)

    model = genai.GenerativeModel(model_name="gemini-1.5-flash")
    response = model.generate_content([f"""- Given the OCR results of a book cover: {results}, 
    - Correct the OCR results.
    - Return as a JSON Object: the title and author 
    - Do not generate anything other than the JSON object"""])

    start = str(response.text).find('{')
    end = str(response.text).rfind('}') + 1

    json_response = str(response.text)[start:end]

    return json_response

class ResultsWindow(QWidget):
    def __init__(self, text, parent=None):
        super(ResultsWindow, self).__init__(parent)
        self.setWindowTitle("Processing Results")
        self.setWindowIcon(QIcon('logo.png'))  # Set the window icon

        try:
            book_info = json.loads(text)
            title = book_info.get("title", "N/A")
            author = book_info.get("author", "N/A")
        except json.JSONDecodeError:
            title = "N/A"
            author = "N/A"
            QMessageBox.warning(self, "Error", "Failed to parse the book information.")

        layout = QVBoxLayout()

        self.title_label = QLabel("Title:")
        layout.addWidget(self.title_label)

        self.title_text_edit = QTextEdit()
        self.title_text_edit.setPlainText(title)
        layout.addWidget(self.title_text_edit)

        self.author_label = QLabel("Author:")
        layout.addWidget(self.author_label)

        self.author_text_edit = QTextEdit()
        self.author_text_edit.setPlainText(author)
        layout.addWidget(self.author_text_edit)

        self.add_button = QPushButton("Add to Sheet")
        layout.addWidget(self.add_button)

        self.setLayout(layout)

        self.add_button.clicked.connect(self.add_to_sheet)

    def add_to_sheet(self):
        modified_text = f"Title: {self.title_text_edit.toPlainText()}, Author: {self.author_text_edit.toPlainText()}"
        with open('book_info_modified.csv', 'a') as file:
            file.write(modified_text + '\n')
        QMessageBox.information(self, "Success", "Book information added to the sheet.")

class FirstWindow(QWidget):
    def __init__(self, parent=None):
        super(FirstWindow, self).__init__(parent)
        self.front_taken = False
        self.back_taken = False
        self.setWindowTitle("Cataloguing")
        self.setWindowIcon(QIcon('logo.png'))  # Set the window icon

        welcome_label = QLabel("WELCOME") 
        button_group = QGroupBox("")
        take_front_pic = QPushButton('Take Front Cover Picture')
        take_back_pic = QPushButton('Take Back Cover Picture')
        button_group_layout = QHBoxLayout()
        button_group_layout.addWidget(take_front_pic)
        button_group_layout.addWidget(take_back_pic)
        button_group.setLayout(button_group_layout)
        
        image_group = QGroupBox("")
        self.front_image = QLabel()  
        self.back_image = QLabel()
        image_group_layout = QHBoxLayout()
        image_group_layout.addWidget(self.front_image)
        image_group_layout.addWidget(self.back_image)
        image_group.setLayout(image_group_layout)
        
        self.process_button = QPushButton('Process')
        self.process_button.setEnabled(False)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        
        window_layout = QVBoxLayout()
        window_layout.addWidget(welcome_label)
        window_layout.addWidget(button_group)
        window_layout.addWidget(image_group)
        window_layout.addWidget(self.process_button)
        window_layout.addWidget(self.progress_bar)

        self.setLayout(window_layout)

        take_front_pic.clicked.connect(self.take_front_image)
        take_back_pic.clicked.connect(self.take_back_image)
        self.process_button.clicked.connect(self.process_images)

    def take_front_image(self):
        self.capture_image('front.jpg', 'Capture Front Cover')
        self.progress_bar.setValue(20)

    def take_back_image(self):
        self.capture_image('back.jpg', 'Capture Back Cover')
        self.progress_bar.setValue(40)

    def capture_image(self, filename, window_title):
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("Error: Could not open camera.")
            return
        if filename == 'front.jpg':
            while True:
                ret, frame = cap.read()
                if not ret:
                    print("Failed to grab frame")
                    break

                cv2.imshow(window_title, frame)
                key = cv2.waitKey(1)
                if key != -1:
                    cv2.imwrite(filename, frame)
                    break

            cap.release()
            cv2.destroyAllWindows()

            pixmap = QPixmap(filename)
            self.front_image.setPixmap(pixmap.scaled(400, 400, Qt.KeepAspectRatio))
            self.front_taken = True
        else:
            self.model = YOLO('best.torchscript', task='detect')
            running = True 
            while running:
                ret, frame = cap.read()
                if not ret:
                    print("Failed to grab frame")
                    break
                # Run the YOLO model on the frame
                results = self.model(frame)
                # Extract the predicted bounding boxes and labels
                for result in results:
                    for box in result.boxes:
                        x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())  # Convert tensor to list and then to int
                        conf = box.conf.item()  # Get the confidence score
                        label = box.cls.item()  # Get the label
                        # Draw the bounding box and label on the frame
                        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                        cv2.putText(frame, f'{label} {conf:.2f}', (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
                        # Crop the detected barcode region from the frame
                        cropped_barcode = frame[y1:y2, x1:x2]
                        # Save the cropped image
                        if(conf >= 0.82): 
                            cropped_filename =  'cropped_barcode.png'
                            cv2.imwrite(cropped_filename, cropped_barcode)
                            #frame_count += 1q
                            running = False


                # Display the resulting frame
                # cv2.imshow('YOLOv8 Real-Time Detection', frame)
                cv2.imshow(window_title, frame)
                cv2.imwrite(filename, frame)
                
                # Break the loop on 'q' key press
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break

            cap.release()
            cv2.destroyAllWindows()

            pixmap = QPixmap(filename)
            self.frame = cv2.imread('back.jpg')
            self.results = self.model(self.frame)
            self.back_image.setPixmap(pixmap.scaled(400, 400, Qt.KeepAspectRatio))
            self.back_taken = True
        
        self.process_button.setEnabled(self.front_taken and self.back_taken)

    def process_images(self):
        # self.progress_bar.setValue(20)
        # self.process_detection()
        self.read_barcode()
        self.progress_bar.setValue(60)

    # def process_detection(self):
    #     self.model = YOLO('best.torchscript', task='detect')
    #     self.frame = cv2.imread('back.jpg')
    #     self.results = self.model(self.frame)

    def read_barcode(self):
        # cropped_barcode = None
        # for result in self.results:
        #     for box in result.boxes:
        #         x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
        #         conf = box.conf.item()
        #         if conf < 0.8: 
        #             continue
        #         cropped_barcode = self.frame[y1:y2, x1:x2]
                
        #         break
        cropped_filename = 'cropped_barcode.png'
        # cv2.imwrite(cropped_filename, cropped_barcode)
        cropped_barcode = cv2.imread(cropped_filename)
        if cropped_barcode is not None and cropped_barcode.size > 0:
            self.extract_book_info(cropped_barcode)
            # self.progress_bar.setValue(80)
        else:
            result_text = handle_ocr_and_ai()
            self.progress_bar.setValue(100)
            self.show_results(result_text)

    def extract_book_info(self, cropped_barcode):
        print("Extracting information from the barcode")
        results = zxingcpp.read_barcodes(cropped_barcode)
        isbn = None
        for result in results:
            isbn = result.text
            print("isbn = {}", isbn)
            
        if not results:
            result_text = handle_ocr_and_ai()
            self.progress_bar.setValue(100)
            self.show_results(result_text)
            return
        
        api_key = "AIzaSyDOLH0ln7zoMNFLT1S4w5EmhP1cvwywJoA"  
        found, status, book_info = get_book_info_google_books(isbn, api_key)
        
        if found:
            result_text = '\n'.join([f"{key}: {value}" for key, value in book_info.items()])
            self.show_results(result_text)
            
        else:
            result_text = handle_ocr_and_ai()
            self.progress_bar.setValue(100)
            self.show_results(result_text)

        
    def show_results(self, text):
        self.results_window = ResultsWindow(text)
        self.results_window.show()

if __name__ == '__main__':
    app = QApplication([])
    initial_window = FirstWindow()
    initial_window.show()
    sys.exit(app.exec_())
