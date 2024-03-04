import sys
import qdarktheme
import socket
import logging
import os
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QLineEdit, QGridLayout, QPushButton, QLabel, QHBoxLayout, QRadioButton
from PyQt6.QtGui import QIcon
from datetime import datetime


def path_(yol):
    if hasattr(sys, '_MEIPASS'):
        path = os.path.join(sys._MEIPASS, yol)
    else:
        path = yol
    return path


class POSUI(QMainWindow):
    def __init__(self):
        super().__init__()

        # self.setWindowTitle('POS Cihazı Uygulaması')
        self.setWindowTitle('POS Gerät Anwendung')
        self.setWindowIcon(QIcon(path_('logo.png')))  # İkonu ayarla
        self.setGeometry(100, 100, 300, 400)
        self.kasa_tutarı = 0.0
        self.son_giriş = 0.0  # Son girişi saklamak için
        self.aktif_islem = None  # 'Giriş' veya 'Çıkış' durumunu saklamak için
        # Loglama yapılandırması
        self.setup_logging()
        self.initUI()

    def initUI(self):
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        # Vertical layout
        vbox = QVBoxLayout()
        central_widget.setLayout(vbox)

        # Radio buttons for Einzahlung (Giriş) / Auszahlung (Çıkış)
        self.giris_radio = QRadioButton("Einzahlung")
        self.cikis_radio = QRadioButton("Auszahlung")
        self.giris_radio.setChecked(True)  # Einzahlung'ı varsayılan yap

        hbox = QHBoxLayout()
        hbox.addWidget(self.giris_radio)
        hbox.addWidget(self.cikis_radio)
        vbox.addLayout(hbox)

        # Text field for input/output
        self.text_field = QLineEdit()
        self.text_field.returnPressed.connect(self.on_enter)
        vbox.addWidget(self.text_field)

        # Kassa Betrag Anzeige (Kasa tutarı gösterimi)
        self.kasa_tutari_label = QLabel(f"Kassenbetrag: {self.kasa_tutarı} €")
        vbox.addWidget(self.kasa_tutari_label)

        # Grid layout for buttons
        grid_layout = QGridLayout()
        vbox.addLayout(grid_layout)

        # Adding buttons
        buttons = [
            ('7', 0, 0), ('8', 0, 1), ('9', 0, 2),
            ('4', 1, 0), ('5', 1, 1), ('6', 1, 2),
            ('1', 2, 0), ('2', 2, 1), ('3', 2, 2),
            ('0', 3, 1),
            ('Abbrechen', 4, 0) # İptal yerine Abbrechen
        ]

        for btn_text, row, col in buttons:
            button = QPushButton(btn_text)
            button.clicked.connect(self.on_button_clicked)
            grid_layout.addWidget(button, row, col)

    def setup_logging(self):
        log_directory = "logs"
        if not os.path.exists(log_directory):
            os.makedirs(log_directory)

        current_time = datetime.now()
        log_filename = f"{log_directory}/{current_time.strftime('%Y-%m-%d')}.log"

        logging.basicConfig(filename=log_filename, level=logging.INFO,
                            format='%(asctime)s: %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

    def on_button_clicked(self):
        button = self.sender()
        if button.text() == 'Abbrechen':
            self.islem_iptal()  # İptal işlemi yap
        else:
            current_text = self.text_field.text()
            new_text = current_text + button.text()
            self.text_field.setText(new_text)

    def on_enter(self):
        miktar_str = self.text_field.text()
        try:
            miktar = float(miktar_str)
            # Negatif miktar için otomatik olarak 'Çıkış' işlemi olarak ayarla
            if miktar < 0:
                islem_turu = 'Auszahlung'
                miktar = -miktar  # Miktarı pozitife çevir
            else:
                islem_turu = 'Einzahlung' if self.giris_radio.isChecked() else 'Auszahlung'

            self.kasa_tutarı += miktar if islem_turu == 'Einzahlung' else -miktar

            self.son_giriş = miktar if islem_turu == 'Einzahlung' else -miktar  # Son girişi güncelle

            self.kasa_tutari_label.setText(f"Kassenbetrag: {self.kasa_tutarı} €")

            # Yazıcıya ve log dosyasına mesaj gönderme
            # Drucker und Log-Datei Nachricht senden
            current_time = datetime.now()
            time_str = current_time.strftime("%Y-%m-%d %H:%M:%S")
            drucker_nachricht = f"Transaktion: {islem_turu}\nBetrag: {miktar}\nZeit: {time_str}\n\n"
            self.print_to_printer(drucker_nachricht)
            logging.info(drucker_nachricht)
        except ValueError:
            self.kasa_tutari_label.setText("Fehlerhafte Eingabe!")  # "Hatalı Giriş"
        self.text_field.clear()


    def print_to_printer(self, message):
        # Test amaçlı olarak mesajı konsola yazdır
        print("An Drucker gesendete Nachricht:\n", message)  # Almanca mesaj
        
        printer_ip = "192.168.0.107"  # Yazıcının IP adresi
        printer_port = 9100  # Yazıcının port numarası

        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((printer_ip, printer_port))
            sock.sendall(message.encode())
            sock.close()
        except Exception as e:
            print(f"Yazıcıya bağlanırken hata oluştu: {e}")

    def islem_iptal(self):
        if self.son_giriş != 0.0:
            # İptal işlemi, son işlemin tersini uygular
            self.kasa_tutarı -= self.son_giriş

            # Yazıcıya ve log dosyasına iptal mesajı gönderme
            current_time = datetime.now()
            time_str = current_time.strftime("%Y-%m-%d %H:%M:%S")
            printer_message = f"Stornierung\nBetrag: {self.son_giriş}\nZeit: {time_str}\n\n"
            self.print_to_printer(printer_message)
            logging.info(printer_message)

            self.kasa_tutari_label.setText(f"Kassenbetrag: {self.kasa_tutarı} €")

        self.son_giriş = 0.0  # Son işlemi sıfırla
        self.text_field.clear()  # Text alanını temizle


def main():
    app = QApplication(sys.argv)
    qdarktheme.enable_hi_dpi()
    qdarktheme.setup_theme()
    main_win = POSUI()
    main_win.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
