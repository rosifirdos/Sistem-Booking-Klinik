from PyQt5.QtWidgets import QLayout, QWidget

def clear_layout(layout):
    """
    Menghapus semua item (widget dan sub-layout) dari sebuah QLayout.
    Ini digunakan untuk membersihkan layout secara dinamis.
    """
    if layout is not None:
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
            else:
                sub_layout = item.layout()
                if sub_layout is not None:
                    clear_layout(sub_layout) # Rekursif untuk sub-layout