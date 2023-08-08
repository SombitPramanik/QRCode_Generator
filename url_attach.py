import sys
import qrcode
import PyPDF2
from PyQt5.QtWidgets import QVBoxLayout, QLineEdit, QDialog, QWidget
import os
import tempfile
from decimal import Decimal
from PIL import Image
from PyPDF2 import PdfReader, PdfWriter
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QPushButton,
    QFileDialog,
    QMessageBox,
)
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas


class QRCodeGenerator(QMainWindow):
    def __init__(self):
        super().__init__()

        self.url_input_dialog = None
        self.initUI()

    def initUI(self):
        self.setWindowTitle("QR Code Generator")
        self.setGeometry(100, 100, 400, 200)

        self.url_pdf_button = QPushButton("Generate QR with URL + PDF", self)

        layout = QVBoxLayout()
        layout.addWidget(self.url_pdf_button)

        self.url_pdf_button.clicked.connect(self.show_url_input)

        central_widget = QWidget(self)
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

    def generate_qr_code(self, data, file_name):
        qr_code = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr_code.add_data(data)
        qr_code.make(fit=True)
        img = qr_code.make_image(fill_color="black", back_color="white")
        img.save(file_name)

    def show_url_input(self):
        self.url_input = QLineEdit(self)
        self.url_input.setPlaceholderText("Enter URL")
        self.url_input.setFixedWidth(250)
        self.url_submit_button = QPushButton("Proceed to Load PDF", self)

        layout = QVBoxLayout()
        layout.addWidget(self.url_input)
        layout.addWidget(self.url_submit_button)

        self.url_submit_button.clicked.connect(self.load_pdf_for_url)
        self.url_input_dialog = QDialog(self)
        self.url_input_dialog.setWindowTitle("Enter URL for QR")
        self.url_input_dialog.setLayout(layout)
        self.url_input_dialog.exec_()

    def load_pdf_for_url(self):
        url = self.url_input.text()
        if url:
            pdf_file_path, _ = QFileDialog.getOpenFileName(
                self, "Select PDF File", "", "PDF Files (*.pdf)"
            )
            if pdf_file_path:
                self.generate_qr_with_url_and_pdf(url, pdf_file_path)
                self.url_input_dialog.close()

    def extract_pdf_data(self, file_path):
        pdf_data = ""
        with open(file_path, "rb") as pdf_file:
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            num_pages = len(
                pdf_reader.pages
            )  # Use len(pdf_reader.pages) instead of pdf_reader.getNumPages()
            for page_num in range(num_pages):
                page = pdf_reader.pages[
                    page_num
                ]  # Use pdf_reader.pages instead of pdf_reader.getPage
                pdf_data += page.extract_text()
        return pdf_data

    def generate_qr_with_url_and_pdf(self, url, pdf_file_path):
        qr_url_data = url
        qr_url_image_path = "url_qr_code.png"  # Path to save the QR code image for the URL
        self.generate_qr_code(qr_url_data, qr_url_image_path)  # Generate QR code image for URL
        self.attach_qr_to_pdf(pdf_file_path, qr_url_image_path)

    def attach_qr_to_pdf(self, pdf_file_path, qr_url_image_path):
        output_file_path = f"{pdf_file_path.rsplit('.', 1)[0]}_with_QR.pdf"
        add_qr_to_pdf(qr_url_image_path, pdf_file_path, output_file_path)  # Swap the arguments
        QMessageBox.information(
            self,
            "Success",
            f"QR code generated and attached to PDF: {output_file_path}",
    )


    def closeEvent(self, event):
        reply = QMessageBox.question(
            self,
            "Confirmation",
            "Are you sure you want to exit the application?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()


def add_qr_to_pdf(qr_pdf_image_path, pdf_file_path, output_file_path):
    # Load the QR code image
    qr_pdf_image = Image.open(qr_pdf_image_path)

    # Open the PDF file
    pdf_file = PdfReader(pdf_file_path)
    total_pages = len(pdf_file.pages)

    # Create a new PDF writer
    pdf_writer = PdfWriter()

    with tempfile.TemporaryDirectory() as temp_dir:
        for page_num in range(total_pages):
            # Create a new blank canvas for the page
            canvas_page = canvas.Canvas(
                os.path.join(temp_dir, "temp.pdf"), pagesize=letter
            )

            # Draw the original page content on the canvas
            page = pdf_file.pages[page_num]
            canvas_page.setPageSize(page.mediabox.upper_right)
            canvas_page.setFont("Helvetica", 10)  # Set font size for QR code text

            # Move to the bottom center position
            mediabox = page.mediabox
            canvas_page.translate(
                float(Decimal(mediabox[2]) / 2), float(Decimal(mediabox[3]) / 10) + 70
            )

            # Add the QR code image to the canvas
            qr_width = 50
            qr_height = 50
            canvas_page.drawImage(
                qr_pdf_image_path,
                -qr_width / 2 + 70,
                -qr_height / 2,
                width=qr_width,
                height=qr_height,
            )

            # Merge the original page and canvas with the QR code image
            canvas_page.showPage()
            canvas_page.save()

            modified_page = PdfReader(os.path.join(temp_dir, "temp.pdf")).pages[0]
            modified_page.merge_page(page)

            # Add the modified page to the PDF writer
            pdf_writer.add_page(modified_page)

    # Save the output PDF file
    with open(output_file_path, "wb") as output_file:
        pdf_writer.write(output_file)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = QRCodeGenerator()
    window.show()
    sys.exit(app.exec_())
