package org.julie.ai;

import android.accessibilityservice.AccessibilityService;
import android.accessibilityservice.GestureDescription;
import android.graphics.Path;
import android.graphics.Rect;
import android.os.Bundle;
import android.view.accessibility.AccessibilityEvent;
import android.view.accessibility.AccessibilityNodeInfo;
import org.json.JSONArray;
import org.json.JSONObject;

public class JulieAccessibilityService extends AccessibilityService {

    private static JulieAccessibilityService instance;

    @Override
    public void onServiceConnected() {
        super.onServiceConnected();
        instance = this;
    }

    public static synchronized JulieAccessibilityService getInstance() {
        return instance;
    }

    @Override
    public void onAccessibilityEvent(AccessibilityEvent event) {}

    @Override
    public void onInterrupt() {}

    // =========================================================================
    // 1. AUTODROID / OMNIPARSER: पूरी स्क्रीन को 5ms में स्कैन करके JSON बनाना
    // =========================================================================
    public String dumpScreenHierarchy() {
        AccessibilityNodeInfo root = getRootInActiveWindow();
        if (root == null) return "[]";

        JSONArray nodesArray = new JSONArray();
        int[] indexCounter = new int[]{1};
        parseNodeRecursive(root, nodesArray, indexCounter);
        return nodesArray.toString();
    }

    private void parseNodeRecursive(AccessibilityNodeInfo node, JSONArray array, int[] counter) {
        if (node == null || !node.isVisibleToUser()) return;

        if (node.isClickable() || node.isEditable() || (node.getText() != null && node.getText().length() > 0)) {
            try {
                JSONObject obj = new JSONObject();
                Rect bounds = new Rect();
                node.getBoundsInScreen(bounds);

                obj.put("index", counter[0]++);
                obj.put("text", node.getText() != null ? node.getText().toString() : "");
                obj.put("desc", node.getContentDescription() != null ? node.getContentDescription().toString() : "");
                obj.put("id", node.getViewIdResourceName() != null ? node.getViewIdResourceName() : "");
                obj.put("clickable", node.isClickable());
                obj.put("editable", node.isEditable());
                obj.put("x", bounds.centerX()); // बटन का सेंटर पॉइंट
                obj.put("y", bounds.centerY());

                array.put(obj);
            } catch (Exception e) {}
        }

        for (int i = 0; i < node.getChildCount(); i++) {
            parseNodeRecursive(node.getChild(i), array, counter);
        }
    }

    // =========================================================================
    // 2. ALIBABA & UI-TARS: स्क्रीन पर 50ms का बिजली जैसा टच (Tap)
    // =========================================================================
    public boolean tapCoordinate(int x, int y) {
        Path clickPath = new Path();
        clickPath.moveTo(x, y);
        GestureDescription.StrokeDescription clickStroke = 
            new GestureDescription.StrokeDescription(clickPath, 0, 50);
        
        GestureDescription.Builder builder = new GestureDescription.Builder();
        builder.addStroke(clickStroke);
        return dispatchGesture(builder.build(), null, null);
    }

    // =========================================================================
    // 3. ALIBABA: स्क्रीन पर स्वाइप और स्क्रॉल करना
    // =========================================================================
    public boolean swipe(int fromX, int fromY, int toX, int toY, int durationMs) {
        Path swipePath = new Path();
        swipePath.moveTo(fromX, fromY);
        swipePath.lineTo(toX, toY);
        
        GestureDescription.StrokeDescription swipeStroke = 
            new GestureDescription.StrokeDescription(swipePath, 0, durationMs);
        
        GestureDescription.Builder builder = new GestureDescription.Builder();
        builder.addStroke(swipeStroke);
        return dispatchGesture(builder.build(), null, null);
    }

    // =========================================================================
    // 4. AUTODROID: इनपुट बॉक्स में सीधे टेक्स्ट टाइप करना
    // =========================================================================
    public boolean setTextToNode(String targetId, String textToSet) {
        AccessibilityNodeInfo root = getRootInActiveWindow();
        if (root == null) return false;
        
        var list = root.findAccessibilityNodeInfosByViewId(targetId);
        if (list != null && !list.isEmpty()) {
            AccessibilityNodeInfo targetNode = list.get(0);
            Bundle arguments = new Bundle();
            arguments.putCharSequence(AccessibilityNodeInfo.ACTION_ARGUMENT_SET_TEXT_CHARSEQUENCE, textToSet);
            return targetNode.performAction(AccessibilityNodeInfo.ACTION_SET_TEXT, arguments);
        }
        return false;
    }

    // =========================================================================
    // 5. ग्लोबल बटन्स: बैक, होम और रीसेंट्स
    // =========================================================================
    public boolean pressBack() { return performGlobalAction(GLOBAL_ACTION_BACK); }
    public boolean pressHome() { return performGlobalAction(GLOBAL_ACTION_HOME); }
}
