import google.generativeai as genai
from PyQt5.QtCore import QObject, pyqtSignal, QThread
import logging
import time # Meskipun tidak digunakan untuk timeout, biarkan saja jika ada rencana lain
import google.api_core.exceptions

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

class GeminiChatbotService:
    def __init__(self):
        pass

    def initialize_model(self, api_key):
        if not api_key or not api_key.startswith("AIza"):
            logging.error("API Key for Gemini is missing or seems invalid.")
            return False
        try:
            genai.configure(api_key=api_key)
            # Uji koneksi dengan mengambil instance model, bukan hanya list_models()
            _ = genai.GenerativeModel('gemini-1.5-flash') 
            logging.info("Gemini API key configured successfully and connection validated (initial check).")
            return True
        except google.api_core.exceptions.GoogleAPIError as e:
            logging.error(f"Error validating Gemini API key during initial check: {e}", exc_info=True)
            return False
        except Exception as e:
            logging.error(f"An unexpected error occurred during initial API key validation: {e}", exc_info=True)
            return False

class GeminiChatbotWorker(QObject):
    response_received = pyqtSignal(str, list)
    error_occurred = pyqtSignal(str)
    finished = pyqtSignal()

    def __init__(self, api_key, user_message, chat_history=None, parent=None):
        super().__init__(parent)
        self._api_key = api_key
        self._user_message = user_message
        self._chat_history = chat_history if chat_history is not None else []
        self._model = None
        self._chat_session = None
        logging.debug(f"GeminiChatbotWorker initialized for message: '{user_message[:50]}...'")

    def run(self):
        logging.debug("GeminiChatbotWorker run method started.")
        try:
            genai.configure(api_key=self._api_key)
            
            # Inisialisasi model di dalam thread untuk memastikan konteks yang benar
            self._model = genai.GenerativeModel('gemini-1.5-flash') 
            logging.debug("Gemini model initialized within worker thread.")

            self._chat_session = self._model.start_chat(history=self._chat_history)
            logging.info(f"Gemini chat session started/continued. History size: {len(self._chat_session.history)}")

            logging.debug(f"Sending message to Gemini: '{self._user_message}'")
            
            # --- Perbaikan: Argumen 'timeout' dihapus dari send_message ---
            response = self._chat_session.send_message(self._user_message) 
            logging.debug(f"Response received from Gemini API.")

            self.response_received.emit(response.text, self._chat_session.history)
            logging.debug(f"Emitted response_received signal.")

        except genai.types.BlockedPromptException as e:
            error_msg = f"Respons diblokir karena alasan keamanan. Harap coba lagi dengan pesan lain. Detail: {e}"
            logging.warning(f"BlockedPromptException: {error_msg}")
            self.error_occurred.emit(error_msg)
        except google.api_core.exceptions.GoogleAPICallError as e:
            error_msg = f"Kesalahan saat memanggil Gemini API. Pastikan API Key benar dan ada koneksi internet. Detail: {e}"
            logging.error(f"GoogleAPICallError: {error_msg}", exc_info=True)
            self.error_occurred.emit(error_msg)
        except ConnectionError as e:
            error_msg = f"Kesalahan koneksi jaringan. Pastikan Anda memiliki koneksi internet yang stabil. Detail: {e}"
            logging.error(f"ConnectionError: {error_msg}", exc_info=True)
            self.error_occurred.emit(error_msg)
        except Exception as e:
            error_msg = f"Terjadi kesalahan tak terduga saat berinteraksi dengan Gemini API. Detail: {e}"
            logging.error(f"Unhandled exception in GeminiChatbotWorker: {error_msg}", exc_info=True)
            self.error_occurred.emit(error_msg)
        finally:
            self.finished.emit()
            logging.debug("GeminiChatbotWorker finished its run, emitting finished signal.")