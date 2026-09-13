[app]
title = Medicine Scanner
package.name = medicinescanner
package.domain = org.vimleshpatel
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,txt,json
version = 1.0
requirements = python3,kivy,reportlab,pytesseract,pillow,plyer
orientation = portrait
fullscreen = 0

android.permissions = CAMERA,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE
android.api = 33
android.minapi = 21
android.archs = arm64-v8a, armeabi-v7a

[buildozer]
log_level = 2
warn_on_root = 1
