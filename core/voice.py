import gc, logging, os, threading
from typing import Callable, Dict, Optional
is_android = "ANDROID_STORAGE" in os.environ or "ANDROID_ROOT" in os.environ

if is_android:
    try:
        from android.runnable import run_on_ui_thread
        from android.permissions import check_permission, Permission
        from jnius import autoclass, PythonJavaClass, java_method

        SPEECH_ERRORS = {
            1: "नेटवर्क टाइमआउट।",
            2: "नेटवर्क त्रुटि।",
            3: "ऑडियो रिकॉर्डिंग त्रुटि।",
            4: "सर्वर त्रुटि।",
            5: "क्लाइंट त्रुटि।",
            6: "कोई आवाज़ नहीं सुनी गई। कृपया पुनः बोलें।",
            7: "पहचान नहीं हो सकी। कृपया दोबारा बोलें।",
            8: "स्पीच इंजन व्यस्त है। कृपया 1 सेकंड बाद दबाएं।",
            9: "माइक्रोफ़ोन अनुमति आवश्यक है।"
        }

        class RecognitionListenerImpl(PythonJavaClass):
            __javainterfaces__ = ['android/speech/RecognitionListener']
            __javacontext__ = 'app'

            def __init__(self, parent_engine):
                super().__init__()
                self.parent = parent_engine

            @java_method('(Landroid/os/Bundle;)V')
            def onReadyForSpeech(self, params): pass

            @java_method('()V')
            def onBeginningOfSpeech(self): pass

            @java_method('(F)V')
            def onRmsChanged(self, rms): pass

            @java_method('([B)V')
            def onBufferReceived(self, buffer): pass

            @java_method('()V')
            def onEndOfSpeech(self): pass

            @java_method('(I)V')
            def onError(self, code):
                msg = SPEECH_ERRORS.get(int(code), f"स्पीच कोड: {code}")
                if self.parent and self.parent.error_callback:
                    self.parent.error_callback(msg)
                if self.parent:
                    self.parent.is_listening = False

            @java_method('(Landroid/os/Bundle;)V')
            def onResults(self, results):
                try:
                    SpeechRecognizer = autoclass('android.speech.SpeechRecognizer')
                    matches = results.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION)
                    final_text = ""
                    if matches and matches.size() > 0:
                        final_text = str(matches.get(0))
                    
                    if self.parent and self.parent.success_callback:
                        self.parent.success_callback(final_text)
                except Exception as e:
                    if self.parent and self.parent.error_callback:
                        self.parent.error_callback(f"Parsing error: {e}")
                finally:
                    if self.parent:
                        self.parent.is_listening = False

            @java_method('(Landroid/os/Bundle;)V')
            def onPartialResults(self, partialResults): pass

            @java_method('(ILandroid/os/Bundle;)V')
            def onEvent(self, eventType, params): pass

    except Exception:
        RecognitionListenerImpl = None
        def run_on_ui_thread(f): return f
else:
    RecognitionListenerImpl = None
    def run_on_ui_thread(f): return f

class JulieVoiceEngine:
    def __init__(self):
        self.is_android = is_android
        self.logger = logging.getLogger("julie.voice")
        self.speech_recognizer = None
        self._listener_ref = None  # Strong reference to avoid Garbage Collection
        self.tts = None
        self.is_listening = False
        self.tts_ready = False
        self.success_callback = None
        self.error_callback = None
        self._lock = threading.RLock()

    def speak(self, text: str) -> bool:
        if not text or not isinstance(text, str): return False
        with self._lock:
            if self.is_android:
                try:
                    from jnius import autoclass
                    PythonActivity = autoclass('org.kivy.android.PythonActivity')
                    TextToSpeech = autoclass('android.speech.tts.TextToSpeech')
                    activity = PythonActivity.mActivity
                    if activity and self.tts is None:
                        self.tts = TextToSpeech(activity, None)
                        self.tts_ready = True
                    if self.tts:
                        self.tts.speak(text, TextToSpeech.QUEUE_FLUSH, None, "julie_tts_msg")
                        return True
                except Exception as e:
                    self.logger.error("TTS error: %s", e)
                    return False
            else:
                return True

    def start_listening(self, callback: Callable[[str], None], error_callback: Optional[Callable[[str], None]] = None) -> bool:
        with self._lock:
            self.success_callback = callback
            self.error_callback = error_callback
            self.is_listening = True

            if self.is_android:
                try:
                    from android.permissions import check_permission, Permission
                    if not check_permission(Permission.RECORD_AUDIO):
                        self.is_listening = False
                        if error_callback: error_callback("माइक्रोफ़ोन अनुमति की आवश्यकता है।")
                        return False

                    @run_on_ui_thread
                    def _start_ui_recognizer():
                        try:
                            from jnius import autoclass
                            PythonActivity = autoclass('org.kivy.android.PythonActivity')
                            SpeechRecognizer = autoclass('android.speech.SpeechRecognizer')
                            RecognizerIntent = autoclass('android.speech.RecognizerIntent')
                            Intent = autoclass('android.content.Intent')

                            activity = PythonActivity.mActivity
                            if not activity:
                                if error_callback: error_callback("Android Activity तैयार नहीं है।")
                                self.is_listening = False
                                return

                            if not SpeechRecognizer.isRecognitionAvailable(activity):
                                if error_callback: error_callback("फ़ोन में Speech Recognizer उपलब्ध नहीं है।")
                                self.is_listening = False
                                return

                            # 1. Reset previous recognizer cleanly to avoid BUSY error
                            if self.speech_recognizer is not None:
                                try:
                                    self.speech_recognizer.cancel()
                                    self.speech_recognizer.destroy()
                                except Exception: pass
                                self.speech_recognizer = None

                            self.speech_recognizer = SpeechRecognizer.createSpeechRecognizer(activity)

                            if self.speech_recognizer and RecognitionListenerImpl:
                                self._listener_ref = RecognitionListenerImpl(self)
                                self.speech_recognizer.setRecognitionListener(self._listener_ref)

                                intent = Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH)
                                intent.putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL, RecognizerIntent.LANGUAGE_MODEL_FREE_FORM)
                                intent.putExtra(RecognizerIntent.EXTRA_CALLING_PACKAGE, activity.getPackageName())
                                intent.putExtra(RecognizerIntent.EXTRA_LANGUAGE, "hi-IN")
                                intent.putExtra(RecognizerIntent.EXTRA_LANGUAGE_PREFERENCE, "hi-IN")
                                intent.putExtra(RecognizerIntent.EXTRA_MAX_RESULTS, 1)
                                intent.putExtra(RecognizerIntent.EXTRA_PARTIAL_RESULTS, False)

                                self.speech_recognizer.startListening(intent)
                            else:
                                if error_callback: error_callback("Speech bridge आरंभ नहीं हो सका।")
                                self.is_listening = False
                        except Exception as inner_e:
                            if error_callback: error_callback(f"Recognizer error: {inner_e}")
                            self.is_listening = False

                    _start_ui_recognizer()
                    return True

                except Exception as exc:
                    self.is_listening = False
                    if error_callback: error_callback(f"Mic error: {exc}")
                    return False
            else:
                self.is_listening = False
                callback("डेमो वॉयस इनपुट (PC Test)")
                return True

    def stop_listening(self):
        with self._lock:
            if not self.is_listening: return
            if self.is_android and self.speech_recognizer:
                try:
                    @run_on_ui_thread
                    def _stop_ui():
                        if self.speech_recognizer: self.speech_recognizer.stopListening()
                    _stop_ui()
                except Exception: pass
            self.is_listening = False

    def shutdown(self):
        with self._lock:
            self.stop_listening()
            if self.is_android:
                if self.speech_recognizer:
                    try:
                        @run_on_ui_thread
                        def _destroy_ui():
                            if self.speech_recognizer: self.speech_recognizer.destroy()
                        _destroy_ui()
                    except Exception: pass
                    self.speech_recognizer = None
                if self.tts:
                    try: self.tts.stop(); self.tts.shutdown()
                    except Exception: pass
                    self.tts = None
            self._listener_ref = None
            self.tts_ready = False
            gc.collect()

    def cleanup(self): self.shutdown()
    def get_status(self) -> Dict[str, bool]:
        with self._lock:
            return {"is_android": self.is_android, "is_listening": self.is_listening, "tts_ready": self.tts_ready}
