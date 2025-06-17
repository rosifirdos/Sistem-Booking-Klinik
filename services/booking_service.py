import logging
from PyQt5.QtCore import QDate # Asumsi QDate digunakan untuk tanggal dalam main.py

# Pastikan Anda memiliki modul database.py yang sesuai
# dari mana DatabaseManager diimpor
# from database import DatabaseManager 

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

class BookingService:
    def __init__(self, db_manager):
        self.db_manager = db_manager

    def insert_initial_data(self):
        """Menyisipkan data dokter dan jadwal awal jika database kosong."""
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        try:
            # Cek apakah sudah ada dokter
            cursor.execute("SELECT COUNT(*) FROM Doctors")
            if cursor.fetchone()[0] == 0:
                logging.info("Inserting initial doctor data...")
                doctors_data = [
                    ("dr. Budi Santoso", "Umum"),
                    ("drg. Citra Dewi", "Gigi"),
                    ("dr. Ana Maria", "Anak"),
                    ("dr. Surya Perkasa", "Umum"),
                    ("drg. Dewi Lestari", "Gigi")
                ]
                cursor.executemany("INSERT INTO Doctors (Name, Specialty) VALUES (?, ?)", doctors_data)
                conn.commit()
                logging.info("Initial doctor data inserted.")

                # Dapatkan ID dokter yang baru saja disisipkan untuk jadwal
                cursor.execute("SELECT DoctorID, Name FROM Doctors")
                doctors = cursor.fetchall()

                # Tambahkan jadwal untuk setiap dokter
                schedules_data = []
                today = QDate.currentDate() # Gunakan QDate untuk konsistensi
                
                for doc_id, doc_name in doctors:
                    # Contoh jadwal untuk beberapa hari ke depan
                    for i in range(5): # Jadwal untuk 5 hari ke depan
                        schedule_date = today.addDays(i).toString("yyyy-MM-dd")
                        if doc_name == "dr. Budi Santoso" or doc_name == "dr. Surya Perkasa": # Dokter Umum
                            schedules_data.append((doc_id, schedule_date, "09:00", "12:00", 0))
                            schedules_data.append((doc_id, schedule_date, "14:00", "17:00", 0))
                        elif doc_name == "drg. Citra Dewi" or doc_name == "drg. Dewi Lestari": # Dokter Gigi
                            schedules_data.append((doc_id, schedule_date, "10:00", "13:00", 0))
                            schedules_data.append((doc_id, schedule_date, "15:00", "18:00", 0))
                        elif doc_name == "dr. Ana Maria": # Dokter Anak
                            schedules_data.append((doc_id, schedule_date, "08:30", "11:30", 0))
                            schedules_data.append((doc_id, schedule_date, "13:30", "16:30", 0))
                            
                logging.info(f"Inserting {len(schedules_data)} initial schedule entries...")
                cursor.executemany("INSERT INTO Schedules (DoctorID, Date, StartTime, EndTime, IsBooked) VALUES (?, ?, ?, ?, ?)", schedules_data)
                conn.commit()
                logging.info("Initial schedule data inserted.")
            else:
                logging.info("Doctors data already exists. Skipping initial data insertion.")
        except Exception as e:
            conn.rollback()
            logging.error(f"Error inserting initial data: {e}")
        finally:
            conn.close()

    def get_all_doctors_with_specialty(self):
        """Mengambil semua dokter beserta spesialisasinya."""
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT DoctorID, Name, Specialty FROM Doctors")
            doctors = cursor.fetchall()
            return doctors
        except Exception as e:
            logging.error(f"Error getting all doctors with specialty: {e}")
            return []
        finally:
            conn.close()

    def get_doctor_names(self):
        """Mengambil hanya nama-nama dokter."""
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT Name FROM Doctors ORDER BY Name")
            names = [row[0] for row in cursor.fetchall()]
            return names
        except Exception as e:
            logging.error(f"Error getting doctor names: {e}")
            return []
        finally:
            conn.close()
            
    def get_all_specialties(self):
        """Mengambil daftar semua spesialisasi unik dari tabel Doctors."""
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT DISTINCT Specialty FROM Doctors ORDER BY Specialty")
            specialties = [row[0] for row in cursor.fetchall()]
            return specialties
        except Exception as e:
            logging.error(f"Error getting all specialties: {e}")
            return []
        finally:
            conn.close()

    def get_doctors_by_specialty(self, specialty_name):
        """Mengambil daftar dokter berdasarkan spesialisasi tertentu."""
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT DoctorID, Name, Specialty FROM Doctors WHERE Specialty = ?", (specialty_name,))
            doctors = cursor.fetchall()
            return doctors
        except Exception as e:
            logging.error(f"Error getting doctors by specialty '{specialty_name}': {e}")
            return []
        finally:
            conn.close()

    def get_doctor_schedules(self, doctor_id, date, include_booked=True):
        """
        Mengambil jadwal dokter untuk tanggal tertentu.
        Jika include_booked=False, hanya jadwal yang belum terisi akan dikembalikan.
        """
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        try:
            query = "SELECT ScheduleID, DoctorID, Date, StartTime, EndTime, IsBooked FROM Schedules WHERE DoctorID = ? AND Date = ?"
            params = (doctor_id, date)
            
            if not include_booked:
                query += " AND IsBooked = 0"
            
            query += " ORDER BY StartTime"
            
            cursor.execute(query, params)
            schedules = cursor.fetchall()
            logging.debug(f"Schedules found for doctor {doctor_id} on {date}: {schedules}")
            return schedules
        except Exception as e:
            logging.error(f"Error getting doctor schedules for doctor {doctor_id} on {date}: {e}")
            return []
        finally:
            conn.close()

    def add_booking(self, schedule_id, doctor_id, patient_name, patient_phone, booking_date, waktu_booking):
        """Menambahkan booking baru dan memperbarui status jadwal."""
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        try:
            # Periksa apakah jadwal sudah terisi
            cursor.execute("SELECT IsBooked FROM Schedules WHERE ScheduleID = ?", (schedule_id,))
            is_booked = cursor.fetchone()
            if is_booked and is_booked[0] == 1:
                return False, "Jadwal ini sudah terisi. Mohon pilih jadwal lain."

            # Tambahkan booking
            cursor.execute(
                "INSERT INTO Bookings (ScheduleID, DoctorID, PatientName, PatientPhone, BookingDate, BookingTime, Status) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (schedule_id, doctor_id, patient_name, patient_phone, booking_date, waktu_booking, "Confirmed")
            )
            
            # Perbarui status jadwal menjadi terisi (IsBooked = 1)
            cursor.execute("UPDATE Schedules SET IsBooked = 1 WHERE ScheduleID = ?", (schedule_id,))
            
            conn.commit()
            logging.info(f"New booking added for schedule {schedule_id} by {patient_name}.")
            return True, "Booking berhasil ditambahkan!"
        except Exception as e:
            conn.rollback()
            logging.error(f"Error adding booking for schedule {schedule_id}: {e}")
            return False, f"Gagal menambahkan booking: {e}"
        finally:
            conn.close()

    def get_all_bookings(self):
        """Mengambil semua booking beserta detail dokter dan spesialisasinya."""
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        try:
            query = """
            SELECT 
                b.BookingID, 
                b.PatientName, 
                b.PatientPhone, 
                d.Name AS DoctorName, 
                d.Specialty, 
                b.BookingDate, 
                b.BookingTime, 
                b.Status
            FROM Bookings b
            JOIN Doctors d ON b.DoctorID = d.DoctorID
            ORDER BY b.BookingDate DESC, b.BookingTime DESC
            """
            cursor.execute(query)
            bookings = cursor.fetchall()
            return bookings
        except Exception as e:
            logging.error(f"Error getting all bookings: {e}")
            return []
        finally:
            conn.close()
            
    def delete_booking(self, booking_id):
        """Menghapus booking dari database berdasarkan booking_id dan memperbarui status jadwal."""
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        try:
            # Dapatkan schedule_id dari booking yang akan dihapus
            cursor.execute("SELECT ScheduleID FROM Bookings WHERE BookingID = ?", (booking_id,))
            result = cursor.fetchone()
            if not result:
                return False, "Booking tidak ditemukan."
            
            schedule_id = result[0]

            # Hapus booking
            cursor.execute("DELETE FROM Bookings WHERE BookingID = ?", (booking_id,))
            
            # Ubah status is_booked di tabel Schedules menjadi 0 (False)
            cursor.execute("UPDATE Schedules SET IsBooked = 0 WHERE ScheduleID = ?", (schedule_id,))
            
            conn.commit()
            logging.info(f"Booking ID {booking_id} and associated Schedule ID {schedule_id} successfully deleted/updated.")
            return True, f"Booking ID {booking_id} berhasil dihapus."
        except Exception as e:
            conn.rollback()
            logging.error(f"Error deleting booking ID {booking_id}: {e}")
            return False, f"Gagal menghapus booking: {e}"
        finally:
            conn.close()