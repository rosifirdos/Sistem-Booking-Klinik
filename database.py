import sqlite3
import logging

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

class DatabaseManager:
    def __init__(self, db_name="klinik_awan.db"):
        self.db_name = db_name
        self.conn = None

    def get_connection(self):
        """Mendapatkan koneksi database."""
        try:
            self.conn = sqlite3.connect(self.db_name)
            self.conn.execute("PRAGMA foreign_keys = ON") # Mengaktifkan foreign key enforcement
            return self.conn
        except sqlite3.Error as e:
            logging.error(f"Error connecting to database: {e}")
            return None

    def create_tables(self):
        """Membuat tabel Doctors, Schedules, dan Bookings jika belum ada."""
        conn = self.get_connection()
        if conn:
            try:
                cursor = conn.cursor()
                # Tabel Doctors
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS Doctors (
                        DoctorID INTEGER PRIMARY KEY AUTOINCREMENT,
                        Name TEXT NOT NULL,
                        Specialty TEXT NOT NULL
                    )
                """)

                # Tabel Schedules
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS Schedules (
                        ScheduleID INTEGER PRIMARY KEY AUTOINCREMENT,
                        DoctorID INTEGER NOT NULL,
                        Date TEXT NOT NULL, -- Format YYYY-MM-DD
                        StartTime TEXT NOT NULL, -- Format HH:MM
                        EndTime TEXT NOT NULL,   -- Format HH:MM
                        IsBooked INTEGER DEFAULT 0, -- 0 for false, 1 for true
                        FOREIGN KEY (DoctorID) REFERENCES Doctors (DoctorID)
                            ON DELETE CASCADE ON UPDATE CASCADE
                    )
                """)

                # Tabel Bookings
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS Bookings (
                        BookingID INTEGER PRIMARY KEY AUTOINCREMENT,
                        ScheduleID INTEGER UNIQUE NOT NULL, -- Satu jadwal hanya bisa punya satu booking
                        DoctorID INTEGER NOT NULL,
                        PatientName TEXT NOT NULL,
                        PatientPhone TEXT,
                        BookingDate TEXT NOT NULL, -- Format YYYY-MM-DD
                        BookingTime TEXT NOT NULL, -- Format HH:MM (dari StartTime jadwal)
                        Status TEXT DEFAULT 'Confirmed', -- e.g., 'Confirmed', 'Cancelled', 'Completed'
                        FOREIGN KEY (ScheduleID) REFERENCES Schedules (ScheduleID)
                            ON DELETE CASCADE ON UPDATE CASCADE,
                        FOREIGN KEY (DoctorID) REFERENCES Doctors (DoctorID)
                            ON DELETE CASCADE ON UPDATE CASCADE
                    )
                """)
                conn.commit()
                logging.info("Database tables checked/created successfully.")
            except sqlite3.Error as e:
                logging.error(f"Error creating tables: {e}")
            finally:
                conn.close()

    def close_connection(self):
        """Menutup koneksi database."""
        if self.conn:
            self.conn.close()
            self.conn = None
            logging.info("Database connection closed.")