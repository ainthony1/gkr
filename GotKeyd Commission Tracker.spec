# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['main.py'],
    pathex=['src'],
    binaries=[],
    datas=[('assets/logo.png', 'assets'), ('assets/f1099nec.pdf', 'assets'), ('assets/agent_info.xlsx', 'assets'), ('assets/icons', 'assets/icons'), ('venv/lib/python3.14/site-packages/customtkinter', 'customtkinter')],
    hiddenimports=['customtkinter', 'fitz', 'core', 'core.models', 'core.constants', 'core.database', 'core.commission_engine', 'generators', 'generators.pdf_generator', 'generators.tax_generator', 'utils', 'utils.import_agents', 'ui', 'ui.theme', 'ui.dashboard_frame', 'ui.agent_select_frame', 'ui.transaction_form', 'ui.review_frame', 'ui.history_frame', 'ui.agent_manage_frame', 'ui.taxes_frame', 'ui.cap_tracker_frame'],
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
    [],
    exclude_binaries=True,
    name='GotKeyd Commission Tracker',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='GotKeyd Commission Tracker',
)
app = BUNDLE(
    coll,
    name='GotKeyd Commission Tracker.app',
    icon=None,
    bundle_identifier=None,
)
