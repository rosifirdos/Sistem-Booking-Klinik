# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['main.py'],
    pathex=['D:\\aplikasi_dokter'], # <-- Pastikan path ini benar sesuai lokasi folder project Anda
    binaries=[],
    datas=[],
    hiddenimports=[ # <--- BARIS INI PENTING! SUDAH SAYA ISI.
        'google',
        'google.generativeai',
        'google.auth',
        'google.cloud',
        'google.protobuf',
        'google_auth_oauthlib',
        'googleapiclient',
        # Tambahkan modul lain di sini jika ada ModuleNotFoundError lainnya di masa depan
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='AplikasiDokter', # <-- Ganti nama file .exe akhir Anda di sini jika mau
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False, # <--- UBAH INI JADI TRUE UNTUK DEBUGGING (agar konsol tetap terbuka)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

# coll = COLLECT(exe,
#                a.binaries,
#                a.zipfiles,
#                a.datas,
#                strip=False,
#                upx=True,
#                upx_exclude=[],
#                name='AplikasiDokter') # <-- KOMENTARI SELURUH BAGIAN INI jika Anda ingin 1 file .exe saja