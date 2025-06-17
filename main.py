import sys
import os
import logging
import json

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QTableWidget, QTableWidgetItem, QMessageBox, QDateEdit,
    QHeaderView, QComboBox, QLineEdit, QTextBrowser, QPushButton, QVBoxLayout,
    QHBoxLayout, QLabel, QStackedWidget, QFrame, QSizePolicy, QSpacerItem, QDialog, QGridLayout, QScrollArea,
    QGraphicsDropShadowEffect
)
from PyQt5 import QtCore, QtGui
from PyQt5.QtCore import Qt, QDate, QThread, pyqtSignal
from PyQt5.QtGui import QPixmap, QColor

# Tambahkan direktori project ke PYTHONPATH agar modul lokal dapat diimpor
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from database import DatabaseManager
from services.booking_service import BookingService
import services.app_tools
from services.chatbot import GeminiChatbotWorker, GeminiChatbotService
from config import DATABASE_NAME, GEMINI_API_KEY # Pastikan GEMINI_API_KEY ada di config.py

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

class BookingDialog(QDialog):
    booking_confirmed = pyqtSignal()

    def __init__(self, parent_window, doctor_id, doctor_name, specialty, initial_date=None):
        super().__init__(parent_window)
        self.parent_window = parent_window
        self.doctor_id = doctor_id
        self.doctor_name = doctor_name
        self.specialty = specialty
        self.initial_date = initial_date if initial_date else QDate.currentDate()
        self.setWindowTitle(f"Buat Booking untuk {self.doctor_name}")
        self.setGeometry(200, 200, 400, 300)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Doctor Info
        layout.addWidget(QLabel(f"<b>Dokter:</b> {self.doctor_name}"))
        layout.addWidget(QLabel(f"<b>Spesialisasi:</b> {self.specialty}"))

        # Patient Name
        layout.addWidget(QLabel("Nama Pasien:"))
        self.patientNameInput = QLineEdit()
        self.patientNameInput.setPlaceholderText("Masukkan nama pasien")
        layout.addWidget(self.patientNameInput)

        # Patient Phone
        layout.addWidget(QLabel("Nomor Telepon Pasien:"))
        self.patientPhoneInput = QLineEdit()
        self.patientPhoneInput.setPlaceholderText("Masukkan nomor telepon pasien")
        layout.addWidget(self.patientPhoneInput)

        # Booking Date
        layout.addWidget(QLabel("Tanggal Booking:"))
        self.bookingDateInput = QDateEdit(self.initial_date)
        self.bookingDateInput.setCalendarPopup(True)
        self.bookingDateInput.setMinimumDate(QDate.currentDate())
        self.bookingDateInput.dateChanged.connect(self.populate_schedule_combobox)
        layout.addWidget(self.bookingDateInput)

        # Schedule ComboBox
        layout.addWidget(QLabel("Pilih Jadwal:"))
        self.scheduleIdComboBox = QComboBox()
        layout.addWidget(self.scheduleIdComboBox)

        # Confirm Button
        confirm_button = QPushButton("Konfirmasi Booking")
        confirm_button.clicked.connect(self.confirm_booking)
        layout.addWidget(confirm_button)

        self.setLayout(layout)

        # Populate schedule initially
        self.populate_schedule_combobox()

    def populate_schedule_combobox(self):
        self.scheduleIdComboBox.clear()
        selected_date = self.bookingDateInput.date().toString(Qt.ISODate) # FormatSCAPE-MM-DD
        
        logging.info(f"Fetching schedules for doctor_id: {self.doctor_id} on date: {selected_date}")
        schedules = self.parent_window.booking_service.get_doctor_schedules(self.doctor_id, selected_date)
        
        if schedules:
            self.scheduleIdComboBox.addItem("-- Pilih Jadwal --", None)
            for schedule_id, doctor_id, date, start_time, end_time, is_booked in schedules:
                display_text = f"{start_time} - {end_time}"
                if is_booked:
                    display_text += " (Terisi)"
                    self.scheduleIdComboBox.addItem(display_text, None) # Jangan tambahkan data jika terisi
                    self.scheduleIdComboBox.model().item(self.scheduleIdComboBox.count() - 1).setEnabled(False)
                else:
                    self.scheduleIdComboBox.addItem(display_text, schedule_id)
        else:
            self.scheduleIdComboBox.addItem("Tidak ada jadwal tersedia", None)
        
        logging.info(f"Populated schedule combobox with {self.scheduleIdComboBox.count()} items.")


    def confirm_booking(self):
        logging.info("Confirming booking from dialog.")
        selected_schedule_id = self.scheduleIdComboBox.currentData(Qt.UserRole)
        nama_pasien = self.patientNameInput.text().strip()
        no_telepon_pasien = self.patientPhoneInput.text().strip()
        tanggal_booking = self.bookingDateInput.date()

        waktu_booking_text = self.scheduleIdComboBox.currentText()
        waktu_booking = ""
        if waktu_booking_text != "-- Pilih Jadwal --":
            waktu_booking = waktu_booking_text.split(' - ')[0].strip()

        if not selected_schedule_id or not nama_pasien or not no_telepon_pasien or not waktu_booking:
            QMessageBox.warning(self, "Input Kurang", "Mohon lengkapi semua data booking dan pilih jadwal.")
            logging.warning("Missing input for booking dialog.")
            return

        success, message = self.parent_window.add_new_booking(
            doctor_id=self.doctor_id,
            doctor_name=self.doctor_name,
            patient_name=nama_pasien,
            patient_phone=no_telepon_pasien,
            booking_date=tanggal_booking,
            schedule_id=selected_schedule_id,
            waktu_booking=waktu_booking
        )

        if success:
            self.booking_confirmed.emit()
            self.accept()
        else:
            QMessageBox.critical(self, "Booking Gagal", message)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.db_manager = DatabaseManager(DATABASE_NAME)
        self.booking_service = BookingService(self.db_manager)
        self.chatbot_service = GeminiChatbotService()
        
        # Inisialisasi thread dan worker sebagai None
        self.chatbot_thread = None
        self.chatbot_worker = None
        self.chat_history = [] # Untuk menyimpan riwayat chat

        self.doctor_cards_layout = None # Akan diinisialisasi di init_ui

        self.setWindowTitle("Sistem Booking Dokter")
        self.setGeometry(100, 100, 1200, 800) # Ukuran jendela utama yang lebih besar
        
        # PENTING: Panggil ini pertama untuk memastikan tabel dibuat sebelum digunakan
        self.check_and_insert_initial_data() 
        
        self.init_ui()
        self.load_initial_data() # Ini akan memuat data setelah tabel dipastikan ada
        self.populate_doctor_comboboxes()
        self.populate_doctor_cards()
        self.populate_booking_table()

        # Inisialisasi Gemini Chatbot Service
        if not self.chatbot_service.initialize_model(GEMINI_API_KEY):
            QMessageBox.warning(self, "API Key Error", "Gagal menginisialisasi Gemini API. Pastikan API Key benar dan koneksi internet tersedia.")
            logging.error("Failed to initialize Gemini API service.")

    def init_ui(self):
        # Main layout (vertical)
        main_layout = QVBoxLayout()

        # Top section (comboboxes and buttons)
        top_hbox = QHBoxLayout()
        self.doctor_filter_combo = QComboBox()
        # Connect to populate_doctor_cards when selection changes
        self.doctor_filter_combo.currentIndexChanged.connect(self.populate_doctor_cards) 
        top_hbox.addWidget(QLabel("Filter Dokter (Spesialisasi):"))
        top_hbox.addWidget(self.doctor_filter_combo)
        top_hbox.addStretch(1) # Push elements to the left

        self.show_doctors_button = QPushButton("Daftar Dokter")
        self.show_doctors_button.clicked.connect(self.show_doctors_view)
        top_hbox.addWidget(self.show_doctors_button)

        self.show_bookings_button = QPushButton("Daftar Booking")
        self.show_bookings_button.clicked.connect(self.show_bookings_view)
        top_hbox.addWidget(self.show_bookings_button)

        self.show_chatbot_button = QPushButton("Chatbot Asisten")
        self.show_chatbot_button.clicked.connect(self.show_chatbot_view)
        top_hbox.addWidget(self.show_chatbot_button)

        main_layout.addLayout(top_hbox)

        # Stacked widget for different views
        self.stacked_widget = QStackedWidget()
        main_layout.addWidget(self.stacked_widget)

        # 1. Doctors View (Scrollable Grid)
        self.doctors_page = QWidget()
        self.doctors_page_layout = QVBoxLayout(self.doctors_page) # Main layout for the page
        
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area_content = QWidget()
        self.doctor_cards_layout = QGridLayout(self.scroll_area_content) # Grid inside scroll area
        self.scroll_area.setWidget(self.scroll_area_content)
        
        self.doctors_page_layout.addWidget(self.scroll_area)
        self.stacked_widget.addWidget(self.doctors_page)

        # 2. Bookings View (Table)
        self.bookings_page = QWidget()
        bookings_layout = QVBoxLayout(self.bookings_page)
        self.booking_table = QTableWidget()
        # Tambahkan 1 kolom untuk tombol Hapus
        self.booking_table.setColumnCount(9) 
        self.booking_table.setHorizontalHeaderLabels([
            "ID Booking", "Nama Pasien", "No. Telepon", "Dokter", 
            "Spesialisasi", "Tanggal Booking", "Waktu Booking", "Status", "Aksi" # Label untuk tombol Aksi
        ])
        self.booking_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        # Atur lebar kolom Aksi agar tidak terlalu lebar
        self.booking_table.horizontalHeader().setSectionResizeMode(8, QHeaderView.Fixed) 
        self.booking_table.setColumnWidth(8, 100) # Sesuaikan lebar jika perlu
        
        bookings_layout.addWidget(self.booking_table)
        self.stacked_widget.addWidget(self.bookings_page)

        # 3. Chatbot View
        self.chatbot_page = QWidget()
        chatbot_layout = QVBoxLayout(self.chatbot_page)

        self.chatMessages = QTextBrowser()
        self.chatMessages.setReadOnly(True)
        self.chatMessages.setLineWrapMode(QTextBrowser.WidgetWidth)
        self.chatMessages.setStyleSheet("background-color: #f0f0f0; border: 1px solid #ccc; padding: 10px;")
        chatbot_layout.addWidget(self.chatMessages)

        chat_input_hbox = QHBoxLayout()
        self.chatInput = QLineEdit()
        self.chatInput.setPlaceholderText("Ketik pesan Anda di sini...")
        self.chatInput.returnPressed.connect(lambda: self.send_message_to_chatbot(self.chatInput.text()))
        chat_input_hbox.addWidget(self.chatInput)

        self.chatSendButton = QPushButton("Kirim")
        self.chatSendButton.clicked.connect(lambda: self.send_message_to_chatbot(self.chatInput.text()))
        chat_input_hbox.addWidget(self.chatSendButton)

        chatbot_layout.addLayout(chat_input_hbox)
        self.stacked_widget.addWidget(self.chatbot_page)

        # Set central widget
        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

        # Set initial view
        self.show_doctors_view()

    def check_and_insert_initial_data(self):
        # Memastikan tabel ada dan menyisipkan data jika kosong
        self.db_manager.create_tables() # Pastikan tabel dibuat!
        # Setelah tabel dibuat, cek apakah ada dokter. Jika tidak ada, sisipkan data awal.
        if not self.booking_service.get_all_doctors_with_specialty(): 
            logging.info("Database is empty or no doctors found. Inserting initial data.")
            self.booking_service.insert_initial_data()
            logging.info("Initial dokter and jadwal data inserted successfully.")
        else:
            logging.info("Database already contains doctor data. Skipping initial data insertion.")

    def load_initial_data(self):
        # Memastikan data awal dimuat (seperti kartu dokter dan booking)
        self.populate_doctor_cards()
        self.populate_booking_table()
        logging.info("Initial data (doctor cards and bookings) loaded.")
    
    def add_new_booking(self, doctor_id, doctor_name, patient_name, patient_phone, booking_date, schedule_id, waktu_booking):
        # Format tanggal dari QDate ke string 'YYYY-MM-DD'
        formatted_date = booking_date.toString(Qt.ISODate)
        
        success, message = self.booking_service.add_booking(
            schedule_id, doctor_id, patient_name, patient_phone, formatted_date, waktu_booking
        )
        if success:
            QMessageBox.information(self, "Booking Berhasil", message)
            self.populate_booking_table() # Refresh table
            self.populate_doctor_cards() # Refresh doctor cards (to update "available" status)
            logging.info(f"Booking confirmed for {doctor_name} on {formatted_date} at {waktu_booking} by {patient_name}.")
        return success, message

    def populate_doctor_comboboxes(self):
        self.doctor_filter_combo.clear()
        self.doctor_filter_combo.addItem("Semua Spesialisasi") # Ubah teks filter
        
        # Ambil daftar spesialisasi unik dari database
        specialties = self.booking_service.get_all_specialties()
        logging.info(f"Fetched specialties: {specialties}")
        for specialty in specialties:
            self.doctor_filter_combo.addItem(specialty)
        logging.info(f"Doctor filter combobox populated with specialties. (Count: {len(specialties)})")


    def populate_doctor_cards(self):
        # Hapus kartu dokter yang ada
        if self.doctor_cards_layout:
            services.app_tools.clear_layout(self.doctor_cards_layout)
        
        selected_specialty = self.doctor_filter_combo.currentText()
        
        doctors_data = []
        if selected_specialty == "Semua Spesialisasi":
            doctors_data = self.booking_service.get_all_doctors_with_specialty()
        else:
            doctors_data = self.booking_service.get_doctors_by_specialty(selected_specialty)

        logging.info(f"Fetched doctors for display based on filter '{selected_specialty}': {len(doctors_data)} entries.")

        row, col = 0, 0
        for doc_id, name, specialty in doctors_data:
            card = self.create_doctor_card(doc_id, name, specialty)
            self.doctor_cards_layout.addWidget(card, row, col)
            col += 1
            if col == 3: # 3 cards per row
                col = 0
                row += 1
        
        # Tambahkan spacer untuk memastikan kartu dokter rata atas
        if self.doctor_cards_layout.count() > 0:
            self.doctor_cards_layout.addItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding), row + 1, 0)
        
        logging.info(f"Populated {self.doctor_cards_layout.count()} doctor cards in grid layout.")


    def create_doctor_card(self, doctor_id, name, specialty):
        card_frame = QFrame()
        card_frame.setFrameShape(QFrame.StyledPanel)
        card_frame.setFrameShadow(QFrame.Raised)
        card_frame.setMinimumWidth(250)
        card_frame.setMaximumWidth(350)
        card_frame.setStyleSheet("""
            QFrame {
                border: 1px solid #dcdcdc;
                border-radius: 8px;
                background-color: #ffffff;
                padding: 15px;
                margin: 5px;
            }
            QLabel {
                font-size: 14px;
                color: #333333;
            }
            QLabel.doctor_name {
                font-size: 16px;
                font-weight: bold;
                color: #0056b3;
                margin-bottom: 5px;
            }
            QPushButton {
                background-color: #007bff;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 15px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
            QPushButton:pressed {
                background-color: #004080;
            }
        """)

        effect = QGraphicsDropShadowEffect()
        effect.setBlurRadius(10)
        effect.setXOffset(3)
        effect.setYOffset(3)
        effect.setColor(QColor(0, 0, 0, 50))
        card_frame.setGraphicsEffect(effect)

        card_layout = QVBoxLayout(card_frame)
        card_layout.setContentsMargins(10, 10, 10, 10)
        card_layout.setSpacing(8)

        name_label = QLabel(name)
        name_label.setObjectName("doctor_name") # Untuk CSS
        specialty_label = QLabel(f"Spesialisasi: {specialty}")
        
        # Cek ketersediaan jadwal
        today = QDate.currentDate().toString(Qt.ISODate)
        available_schedules = self.booking_service.get_doctor_schedules(doctor_id, today, include_booked=False)
        
        status_text = "Tidak Ada Jadwal Hari Ini"
        status_color = "red"
        if available_schedules:
            status_text = f"{len(available_schedules)} Jadwal Tersedia Hari Ini"
            status_color = "green"

        status_label = QLabel(f"<span style='color: {status_color}; font-weight: bold;'>{status_text}</span>")
        status_label.setAlignment(Qt.AlignCenter) # Pusatkan teks status

        booking_button = QPushButton("Booking Sekarang")
        booking_button.clicked.connect(lambda: self.open_booking_dialog(doctor_id, name, specialty))
        
        card_layout.addWidget(name_label)
        card_layout.addWidget(specialty_label)
        card_layout.addStretch() # Mendorong status dan tombol ke bawah
        card_layout.addWidget(status_label)
        card_layout.addWidget(booking_button)
        
        return card_frame

    def open_booking_dialog(self, doctor_id, doctor_name, specialty):
        dialog = BookingDialog(self, doctor_id, doctor_name, specialty)
        dialog.booking_confirmed.connect(self.populate_booking_table) # Refresh table on booking
        dialog.booking_confirmed.connect(self.populate_doctor_cards) # Refresh cards on booking
        dialog.exec_()

    def populate_booking_table(self):
        bookings = self.booking_service.get_all_bookings()
        logging.info(f"Retrieved {len(bookings)} bookings.")
        self.booking_table.setRowCount(0) # Clear existing rows
        
        # Ubah jumlah kolom menjadi 9 karena ada kolom 'Aksi'
        self.booking_table.setColumnCount(9) 
        self.booking_table.setHorizontalHeaderLabels([
            "ID Booking", "Nama Pasien", "No. Telepon", "Dokter", 
            "Spesialisasi", "Tanggal Booking", "Waktu Booking", "Status", "Aksi" # Label untuk tombol Aksi
        ])
        self.booking_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.booking_table.horizontalHeader().setSectionResizeMode(8, QHeaderView.Fixed) # Kolom Aksi
        self.booking_table.setColumnWidth(8, 100) # Lebar kolom Aksi
        
        for row_num, booking in enumerate(bookings):
            self.booking_table.insertRow(row_num)
            for col_num, data in enumerate(booking):
                self.booking_table.setItem(row_num, col_num, QTableWidgetItem(str(data)))
            
            # Tambahkan tombol Hapus Booking di kolom terakhir (indeks 8)
            delete_button = QPushButton("Hapus")
            delete_button.setStyleSheet("background-color: #dc3545; color: white; border-radius: 4px; padding: 5px;")
            delete_button.clicked.connect(lambda _, b_id=booking[0]: self.delete_booking(b_id))
            self.booking_table.setCellWidget(row_num, 8, delete_button) # Masukkan tombol ke sel
            
        logging.info(f"Loaded {len(bookings)} bookings into table with delete buttons.")

    def delete_booking(self, booking_id):
        # Konfirmasi penghapusan
        reply = QMessageBox.question(self, 'Konfirmasi Hapus', 
                                    f"Anda yakin ingin menghapus booking ID {booking_id}?",
                                    QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            success, message = self.booking_service.delete_booking(booking_id)
            if success:
                QMessageBox.information(self, "Berhasil", message)
                self.populate_booking_table() # Refresh table setelah penghapusan
                self.populate_doctor_cards() # Refresh kartu dokter jika ketersediaan berubah
            else:
                QMessageBox.critical(self, "Gagal", message)
        logging.info(f"Attempted to delete booking ID {booking_id}. Success: {success}, Message: {message}")


    def show_doctors_view(self):
        self.stacked_widget.setCurrentWidget(self.doctors_page)
        self.show_doctors_button.setStyleSheet("background-color: #0056b3; color: white;")
        self.show_bookings_button.setStyleSheet("")
        self.show_chatbot_button.setStyleSheet("")
        logging.info("Switched to Doctors View.")

    def show_bookings_view(self):
        self.stacked_widget.setCurrentWidget(self.bookings_page)
        self.populate_booking_table() # Refresh table when showing view
        self.show_bookings_button.setStyleSheet("background-color: #0056b3; color: white;")
        self.show_doctors_button.setStyleSheet("")
        self.show_chatbot_button.setStyleSheet("")
        logging.info("Switched to Bookings View.")

    def show_chatbot_view(self):
        self.stacked_widget.setCurrentWidget(self.chatbot_page)
        self.show_chatbot_button.setStyleSheet("background-color: #0056b3; color: white;")
        self.show_doctors_button.setStyleSheet("")
        self.show_bookings_button.setStyleSheet("")
        logging.info("Switched to Chatbot View.")
        
        # --- Pesan Pembuka Chatbot ---
        self.chatMessages.clear() 
        self.chatMessages.append("<p style='color: #0056b3; text-align: left;'><b>MediBot:</b> Hai! Saya MediBot, asisten virtual Klinik Awan. Apa yang bisa saya bantu hari ini?</p>")
        # --- AKHIR Pesan Pembuka Chatbot ---

    def _cleanup_chatbot_thread(self):
        logging.debug("Cleaning up chatbot thread references.")
        # Slot ini dipanggil ketika sinyal finished dari self.chatbot_thread dipancarkan,
        # menunjukkan bahwa thread telah selesai dieksekusi dan akan dihapus.
        if self.chatbot_thread is not None:
            # Putuskan koneksi sinyal untuk mencegah koneksi yang tertinggal (opsional tapi baik)
            try:
                self.chatbot_thread.started.disconnect(self.chatbot_worker.run)
            except TypeError: # Tangani kasus di mana sudah terputus
                pass

            # Setel referensi ke None agar Python GC bisa membersihkan dan mencegah RuntimeError
            self.chatbot_thread = None
            self.chatbot_worker = None
        logging.debug("Chatbot thread references set to None.")


    def send_message_to_chatbot(self, message):
        if not message.strip():
            logging.info("Chat message is empty, not sending.")
            return

        # Periksa apakah ada thread yang sedang berjalan.
        # Jika ada, dan belum selesai dibersihkan, abaikan pesan baru.
        if self.chatbot_thread is not None and self.chatbot_thread.isRunning():
            logging.warning("Chatbot thread is already running, ignoring new message.")
            return

        user_message_html = f"<p style='color: #000080; text-align: right;'><b>Anda:</b> {message}</p>"
        self.chatMessages.append(user_message_html)
        self.chatInput.clear()

        self._remove_typing_indicator() # Hapus indicator "Mengetik..." sebelumnya
        
        # Tambahkan indicator "Mengetik..." baru
        self.chatMessages.append("<p style='color: #808080; text-align: left;'><b>MediBot:</b> Mengetik...</p>")
        QApplication.processEvents() # Paksa UI untuk update

        self.chatInput.setEnabled(False)
        self.chatSendButton.setEnabled(False)
        
        # --- LOGIKA RAG DIMULAI DI SINI ---
        base_instruction = "Anda adalah asisten virtual untuk Klinik Awan. Jawab pertanyaan pengguna HANYA berdasarkan informasi yang saya berikan. Jika informasi tidak tersedia dalam data yang saya berikan, katakan 'Maaf, saya tidak memiliki informasi tersebut.' "

        full_prompt_for_gemini = f"{base_instruction}\n\nPertanyaan pengguna: {message}\n"
        
        context_data = ""
        message_lower = message.lower()

        # RAG Logic for General Doctor List
        if "daftar dokter" in message_lower or "dokter siapa" in message_lower or "dokter yang tersedia" in message_lower:
            doctors = self.booking_service.get_all_doctors_with_specialty()
            if doctors:
                context_data += "\nInformasi Dokter dari database:\n"
                for doc_id, name, specialty in doctors:
                    context_data += f"- Nama: {name}, Spesialisasi: {specialty}\n"
                # Instruksi langsung ke Gemini untuk menampilkan daftar dokter
                full_prompt_for_gemini += "\nBerdasarkan informasi dokter di atas, berikan daftar dokter yang tersedia dalam format poin-poin yang jelas (misalnya: - Nama: dr. [Nama], Spesialisasi: [Spesialisasi])."
            else:
                context_data += "\n\nInformasi Dokter dari database: Saat ini tidak ditemukan data dokter yang terdaftar."
                full_prompt_for_gemini += "\nBerdasarkan informasi di atas, beritahu pengguna bahwa saat ini tidak ada dokter yang terdaftar dalam sistem."
        
        # RAG Logic for Symptom-Based Doctor Recommendation
        elif any(keyword in message_lower for keyword in ["sakit gigi", "gigi", "dokter gigi", "sakit kepala", "demam", "flu", "batuk", "pilek", "anak", "bayi", "bayi saya"]):
            matched_specialty = None
            
            # Simple keyword matching untuk keluhan ke spesialisasi
            if "sakit gigi" in message_lower or "gigi" in message_lower or "dokter gigi" in message_lower:
                matched_specialty = "Gigi"
            elif "sakit kepala" in message_lower or "demam" in message_lower or "flu" in message_lower or "batuk" in message_lower or "pilek" in message_lower:
                matched_specialty = "Umum"
            elif "anak" in message_lower or "bayi" in message_lower or "bayi saya" in message_lower:
                matched_specialty = "Anak"

            if matched_specialty:
                doctors = self.booking_service.get_doctors_by_specialty(matched_specialty)
                if doctors:
                    context_data += f"\nInformasi Dokter Spesialis {matched_specialty} dari database:\n"
                    for doc_id, name, specialty in doctors:
                        context_data += f"- Nama: {name}, Spesialisasi: {specialty}\n"
                    full_prompt_for_gemini += f"\nBerdasarkan informasi dokter di atas, jika pengguna memiliki keluhan terkait {matched_specialty.lower()}, rekomendasikan dokter yang cocok. Berikan nama dan spesialisasi dokter tersebut dalam format poin-poin yang jelas (misalnya: - Nama: dr. [Nama], Spesialisasi: [Spesialisasi]). Jika tidak ada dokter yang cocok, katakan maaf."
                else:
                    context_data += f"\n\nInformasi Dokter Spesialis {matched_specialty} dari database: Saat ini tidak ditemukan dokter spesialis {matched_specialty} yang terdaftar."
                    full_prompt_for_gemini += f"\nBerdasarkan informasi di atas, beritahu pengguna bahwa saat ini tidak ada dokter spesialis {matched_specialty} yang terdaftar dalam sistem."
        
        # RAG Logic for Klinik Information
        elif any(keyword in message_lower for keyword in ["alamat klinik", "lokasi klinik", "info klinik", "kontak klinik", "nomor telepon klinik", "jam buka klinik", "klinik awan"]):
            context_data += """
            Informasi Detail Klinik Awan:
            Alamat: Jalan Merdeka No. 123, Semarang, Jawa Tengah.
            Nomor Telepon: (024) 12345678
            Jam Buka: Senin - Jumat, 08:00 - 20:00; Sabtu, 09:00 - 17:00; Minggu Tutup.
            """
            full_prompt_for_gemini += "\nBerdasarkan informasi di atas, berikan detail alamat, nomor telepon, dan jam buka Klinik Awan kepada pengguna."
        
        # RAG Logic for Chatbot Capabilities
        elif any(keyword in message_lower for keyword in ["bisa apa", "fungsi", "kemampuan", "fitur", "apa saja", "tentang kamu", "tentang chatbot", "kamu bisa apa"]):
            context_data += """
            Informasi tentang kemampuan Chatbot Asisten:
            Chatbot Asisten ini dirancang untuk membantu Anda dengan informasi terkait dokter di Klinik Awan.
            Kemampuan utamanya meliputi:
            - Memberikan daftar semua dokter yang tersedia.
            - Merekomendasikan dokter berdasarkan keluhan atau spesialisasi (misalnya, untuk sakit gigi, sakit kepala, demam, flu, batuk, pilek, atau terkait anak/bayi).
            - Menjawab pertanyaan terkait informasi umum klinik seperti alamat, nomor telepon, dan jam buka.
            Chatbot ini tidak dapat membuat booking atau mengubah jadwal secara langsung, tetapi dapat memandu Anda untuk menemukan informasi dokter.
            """
            full_prompt_for_gemini += "\nBerdasarkan informasi di atas, jelaskan kepada pengguna apa saja yang bisa Anda lakukan sebagai Chatbot Asisten Klinik Awan dalam format poin-poin yang mudah dimengerti."
        
        if context_data:
            full_prompt_for_gemini += context_data

        logging.info(f"Full prompt sent to Gemini: {full_prompt_for_gemini}")
        # --- LOGIKA RAG SELESAI ---

        logging.info("Starting new chatbot worker thread.")
        self.chatbot_worker = GeminiChatbotWorker(GEMINI_API_KEY, full_prompt_for_gemini, chat_history=self.chat_history)
        self.chatbot_thread = QThread()
        self.chatbot_worker.moveToThread(self.chatbot_thread)

        self.chatbot_worker.response_received.connect(self.display_chatbot_response)
        self.chatbot_worker.error_occurred.connect(self.display_chatbot_error)
        self.chatbot_thread.started.connect(self.chatbot_worker.run)
        
        # Hubungkan sinyal finished untuk quit dan cleanup
        self.chatbot_worker.finished.connect(self.chatbot_thread.quit)
        self.chatbot_worker.finished.connect(self.chatbot_worker.deleteLater)
        self.chatbot_thread.finished.connect(self.chatbot_thread.deleteLater)
        
        # Hubungkan ke metode cleanup kustom setelah semua panggilan deleteLater
        self.chatbot_thread.finished.connect(self._cleanup_chatbot_thread) 

        self.chatbot_thread.start()

    def _remove_typing_indicator(self):
        cursor = self.chatMessages.textCursor()
        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.select(QtGui.QTextCursor.BlockUnderCursor)
        last_block_text = cursor.selectedText()
        if "Mengetik..." in last_block_text:
            cursor.removeSelectedText()
            # Hapus karakter newline yang mungkin tersisa setelah menghapus block
            if not cursor.atEnd():
                cursor.deletePreviousChar()
            self.chatMessages.setTextCursor(cursor)
            QApplication.processEvents()


    def display_chatbot_response(self, response_text, updated_history):
        logging.info("Displaying chatbot response and updating history.")
        self._remove_typing_indicator()

        bot_message_html = f"<p style='color: #0056b3; text-align: left;'><b>MediBot:</b> {response_text}</p>"
        self.chatMessages.append(bot_message_html)

        self.chat_history = updated_history
        logging.debug(f"Chat history updated. New size: {len(self.chat_history)}")

        self.chatInput.setEnabled(True)
        self.chatSendButton.setEnabled(True)
        self.chatInput.setFocus()

    def display_chatbot_error(self, error_message):
        logging.error(f"Displaying chatbot error: {error_message}")
        self._remove_typing_indicator()

        error_html = f"<p style='color: red; text-align: left;'><b>MediBot (Error):</b> {error_message}</p>"
        self.chatMessages.append(error_html)
        self.chatInput.setEnabled(True)
        self.chatSendButton.setEnabled(True)
        self.chatInput.setFocus()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec_())