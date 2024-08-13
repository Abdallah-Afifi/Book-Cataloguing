# Book-Cataloguing App

## Overview

The Book-Cataloguing App automates the process of cataloging donated books for AUC Libraries, eliminating manual searches and preventing duplicate holdings. Utilizing machine learning and OCR technology, our app recognizes book title pages, extracts and classifies textual data, and checks against an existing catalog to flag duplicates.

## Key Features

- **Automated Text Extraction:** Leverages OCR to extract text from scanned book title pages.
- **Smart Classification:** Classifies extracted text into personal names, book titles, and publisher information.
- **Duplicate Detection:** Flags potential duplicates in the catalog; if no duplicate is found, the data is saved to a spreadsheet.
- **Advanced Database Management:** Allows users to add new title pages and book titles to the database, with similarity indicators for future comparisons.

## Tech Stack

- **Python**
- **TensorFlow/PyTorch**
- **Tesseract**
- **Django/Flask**
- **OpenCV**

## Quick Start

1. **Upload a Book Title Page:** Use the web interface to upload an image of the book's title page.
2. **OCR Processing:** The app automatically extracts and classifies the text.
3. **Duplicate Check:** The system compares the extracted data against the existing catalog.
4. **Result:** If a duplicate is found, a warning is issued. If not, the data is stored.

## Team

- **Hadj Ahmed Chikh Dahmane**
- **Kareem Sayed**
- **Abdallah Fathi**
- **Abdelaziz Yehia**

---

Ready to automate your library cataloging process? Get started with the Book-Cataloguing App today!
