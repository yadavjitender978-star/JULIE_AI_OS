[app]
title = JULIE AI OS
package.name = julieaios
package.domain = org.julie.ai
source.dir = .
source.include_exts = py,png,jpg,jpeg,kv,json,txt,xml
source.exclude_dirs = .buildozer,bin,__pycache__,.git,apk,data/logs
version = 1.2.6
requirements = python3,kivy,pyjnius,android
orientation = portrait
fullscreen = 0
android.api = 35
android.minapi = 21
android.ndk_api = 21
android.archs = arm64-v8a
android.accept_sdk_license = True
android.permissions = INTERNET, RECORD_AUDIO, MODIFY_AUDIO_SETTINGS
android.extra_manifest_xml = extra_manifest.xml

[buildozer]
log_level = 2
warn_on_root = 0
