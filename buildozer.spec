[app]
title = JULIE AI OS
package.name = julieaios
package.domain = org.julie.ai
source.dir = .
source.include_exts = py,png,jpg,jpeg,kv,json,txt
source.exclude_dirs = .buildozer,bin,__pycache__,.git,apk
version = 6.6.1
requirements = python3,kivy,pyjnius,android
orientation = portrait
fullscreen = 0
android.api = 35
android.minapi = 21
android.ndk_api = 21
android.archs = arm64-v8a
android.accept_sdk_license = True
android.permissions = INTERNET, RECORD_AUDIO, MODIFY_AUDIO_SETTINGS

[buildozer]
log_level = 2
warn_on_root = 0
