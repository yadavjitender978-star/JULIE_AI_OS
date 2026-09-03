"""
JULIE AI OS — Accessibility Python Bridge
Architecture: AutoDroid + Alibaba MobileAgent + Microsoft OmniParser Protocol
Platform: Android Native via PyJNIus
"""

import json
import time

try:
    from jnius import autoclass
    IS_ANDROID = True
except Exception:
    IS_ANDROID = False


class JulieAccessibilityBridge:
    def __init__(self):
        self._service = None

    def _get_service(self):
        """Android Accessibility Java सर्विस का इंस्टेंस प्राप्त करें"""
        if not IS_ANDROID:
            return None
        if self._service is None:
            try:
                ServiceClass = autoclass("org.julie.ai.JulieAccessibilityService")
                self._service = ServiceClass.getInstance()
            except Exception as e:
                print(f"[JULIE BRIDGE ERROR] Service not connected: {e}")
                self._service = None
        return self._service

    def is_connected(self) -> bool:
        """चेक करें कि फोन की सेटिंग्स में एक्सेसिबिलिटी सर्विस चालू है या नहीं"""
        return self._get_service() is not None

    # =========================================================================
    # 1. OMNIPARSER / AUTODROID: स्क्रीन का साफ़ JSON डेटा पढ़ना
    # =========================================================================
    def get_screen_state(self) -> list:
        """
        पूरी स्क्रीन को स्कैन करके बटन्स और इनपुट्स की साफ़ लिस्ट देता है।
        रिटर्न: [{"index": 1, "text": "Search", "x": 350, "y": 950, "clickable": True}, ...]
        """
        service = self._get_service()
        if not service:
            return []

        try:
            raw_json = str(service.dumpScreenHierarchy())
            elements = json.loads(raw_json)
            return elements
        except Exception as e:
            print(f"[JULIE BRIDGE] Dump error: {e}")
            return []

    # =========================================================================
    # 2. ALIBABA & UI-TARS: बटन या पिक्सल पर क्लिक करना
    # =========================================================================
    def click_element(self, index=None, target_id=None, x=None, y=None) -> bool:
        """
        इंडेक्स नंबर (1, 2), आईडी ('buy_btn') या सीधे (x, y) कोऑर्डिनेट पर क्लिक करता है।
        """
        service = self._get_service()
        if not service:
            return False

        # अगर सीधा (x, y) दिया गया है:
        if x is not None and y is not None:
            return bool(service.tapCoordinate(int(x), int(y)))

        # स्क्रीन एलिमेंट्स स्कैन करें
        elements = self.get_screen_state()

        for el in elements:
            # 1. इंडेक्स से मैच करना
            if index is not None and el.get("index") == index:
                return bool(service.tapCoordinate(el["x"], el["y"]))

            # 2. आईडी या टेक्स्ट से मैच करना
            if target_id is not None:
                tid = target_id.lower()
                if tid in el.get("id", "").lower() or tid in el.get("text", "").lower():
                    return bool(service.tapCoordinate(el["x"], el["y"]))

        return False

    # =========================================================================
    # 3. AUTODROID: इनपुट बॉक्स में सीधे टाइप करना
    # =========================================================================
    def type_text(self, target_id: str, text: str) -> bool:
        """बिना कीबोर्ड खोले सीधे इनपुट बॉक्स में टेक्स्ट टाइप करता है"""
        service = self._get_service()
        if not service:
            return False
        try:
            return bool(service.setTextToNode(str(target_id), str(text)))
        except Exception as e:
            print(f"[JULIE BRIDGE] Type error: {e}")
            return False

    # =========================================================================
    # 4. ALIBABA: स्वाइप और स्क्रॉल
    # =========================================================================
    def swipe(self, from_x: int, from_y: int, to_x: int, to_y: int, duration_ms: int = 300) -> bool:
        """स्क्रीन पर उंगली से स्वाइप/स्क्रॉल करता है"""
        service = self._get_service()
        if not service:
            return False
        return bool(service.swipe(int(from_x), int(from_y), int(to_x), int(to_y), int(duration_ms)))

    # =========================================================================
    # 5. ग्लोबल बटन्स
    # =========================================================================
    def press_back(self) -> bool:
        service = self._get_service()
        return bool(service.pressBack()) if service else False

    def press_home(self) -> bool:
        service = self._get_service()
        return bool(service.pressHome()) if service else False

    # =========================================================================
    # 6. ALIBABA REFLECTOR: एक्शन की पुष्टि (Verification Loop)
    # =========================================================================
    def verify_screen_change(self, previous_state: list, timeout_sec: float = 1.0) -> bool:
        """
        क्लिक करने के बाद चेक करता है कि स्क्रीन सचमुच बदली या नहीं।
        """
        start_time = time.time()
        while time.time() - start_time < timeout_sec:
            current_state = self.get_screen_state()
            if len(current_state) != len(previous_state):
                return True  # स्क्रीन बदल चुकी है (सफल)
            time.sleep(0.2)
        return False
