# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for Password Vault Pro Windows exe."""

from PyInstaller.utils.hooks import collect_all, collect_submodules

datas = [
    ('templates', 'templates'),
    ('static', 'static'),
]
binaries = []
hiddenimports = collect_submodules('sqlalchemy') + [
    'flask',
    'flask_sqlalchemy',
    'jinja2',
    'werkzeug',
    'cryptography',
    'cryptography.fernet',
    'cryptography.hazmat.primitives.kdf.pbkdf2',
    'argon2',
    'argon2.exceptions',
    'models',
    'crypto',
    'auth',
    'backup',
]

for pkg in ('cryptography', 'argon2'):
    pkg_datas, pkg_binaries, pkg_hidden = collect_all(pkg)
    datas += pkg_datas
    binaries += pkg_binaries
    hiddenimports += pkg_hidden

a = Analysis(
    ['app.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='PasswordVaultPro',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
