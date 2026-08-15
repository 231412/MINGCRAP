# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller 打包配置。

构建：python -m PyInstaller MINGAGENT.spec --noconfirm --clean
产物：dist/MINGAGENT.exe（单文件，控制台模式）
"""

from PyInstaller.utils.hooks import collect_all, collect_submodules

datas = [
    ("app.py", "."),
    (".streamlit", ".streamlit"),
]
binaries = []
hiddenimports = []

# streamlit 本体及其静态资源
s_datas, s_bins, s_hidden = collect_all("streamlit")
datas += s_datas
binaries += s_bins
hiddenimports += s_hidden

# mingagent 仅在 app.py 运行时被加载（launcher 不直接导入），需显式收集
hiddenimports += collect_submodules("mingagent")

a = Analysis(
    ["launcher.py"],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["tkinter", "pytest"],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="MINGAGENT",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
