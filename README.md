\# Book Cataloguing Application

\## Overview

This project is a desktop application built with PyQt5 that helps users catalog books by taking pictures of their covers, extracting book information using OCR (Optical Character Recognition), and querying book details from the Google Books API. The application also integrates with Google's Generative AI to enhance OCR results.

\## Features

- Capture images of the front and back covers of books.
- Process images to extract book information.
- Use OCR and Generative AI to enhance and correct book information.
- Save processed book information to a CSV file.
- Display processing results in a GUI.

\## Dependencies

- PyQt5
- OpenCV (`cv2`)
- `torch`
- `ultralytics` (for YOLO model)
- `zxingcpp` (for barcode reading)
- `requests`
- `PIL` (Pillow)
- `google.generativeai` (for Google's Generative AI)
- `ArabicOcr` (for Arabic OCR processing)

\## Installation

1. \*\*Clone the repository:\*\*

\```bash

git clone <repository-url>

Navigate to the project directory:

bash

Copy code

cd <project-directory>

Install the required packages:

You can install the necessary Python packages using pip. Create a virtual environment if needed:

bash

Copy code

python -m venv venv

source venv/bin/activate  # On Windows use `venv\Scripts\activate`

Install the dependencies:

bash

Copy code

pip install pyqt5 opencv-python torch ultralytics zxingcpp requests pillow google-generativeai

Make sure you have the ArabicOcr module available in your project.

Usage

Run the application:

bash

Copy code

python main.py

Using the application:

Capture Images: Click the buttons to capture the front and back cover pictures of the book.

Process Images: Click the "Process" button to start processing the images. The application will perform OCR, correct results using Generative AI, and fetch book details from Google Books.

View Results: The processed book information will be displayed in a new window. You can add the information to a CSV file by clicking "Add to Sheet."

Code Description

Functions

get\_book\_info\_google\_books(isbn, api\_key): Queries the Google Books API for book information based on the ISBN.

handle\_ocr\_and\_ai(): Performs OCR on the book cover image and uses Generative AI to correct and enhance the OCR results.

Classes

ResultsWindow: A PyQt5 widget that displays the book title and author. Allows adding the information to a CSV file.

FirstWindow: The main window of the application where users can take pictures of book covers and start processing.

Main Application

The main.py file is the entry point of the application. It initializes the PyQt5 application, creates an instance of FirstWindow, and starts the application event loop.

License

This project is licensed under the MIT License. See the LICENSE file for details.

Contributing

Feel free to open issues or submit pull requests if you have suggestions or improvements for the project.

Acknowledgments

PyQt5: For providing the framework to build the graphical user interface.

OpenCV: For image capturing and processing functionalities.

Google's Generative AI: For enhancing OCR results.

ArabicOcr: For Arabic OCR capabilities.

Google Books API: For fetching book details.
