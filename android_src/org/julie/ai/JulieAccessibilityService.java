package org.julie.ai;

import android.accessibilityservice.AccessibilityService;
import android.view.accessibility.AccessibilityEvent;
import android.view.accessibility.AccessibilityNodeInfo;
import android.util.Log;


public class JulieAccessibilityService
        extends AccessibilityService {

    private static final String TAG =
            "JULIE_ACCESSIBILITY";

    private static JulieAccessibilityService instance;


    public static synchronized
    JulieAccessibilityService getInstance() {

        return instance;
    }


    @Override
    protected void onServiceConnected() {

        super.onServiceConnected();

        instance = this;

        Log.i(
            TAG,
            "JULIE Accessibility Service CONNECTED"
        );
    }


    @Override
    public void onAccessibilityEvent(
            AccessibilityEvent event) {

        if (event == null) {
            return;
        }

        int eventType =
                event.getEventType();

        CharSequence packageName =
                event.getPackageName();

        CharSequence className =
                event.getClassName();

        Log.d(
            TAG,
            "eventType=" + eventType
            + " package=" + packageName
            + " class=" + className
        );
    }


    @Override
    public void onInterrupt() {

        Log.w(
            TAG,
            "JULIE Accessibility Service INTERRUPTED"
        );
    }


    @Override
    public void onDestroy() {

        Log.i(
            TAG,
            "JULIE Accessibility Service DESTROYED"
        );

        if (instance == this) {
            instance = null;
        }

        super.onDestroy();
    }


    public boolean isServiceRunning() {

        return instance != null;
    }


    public AccessibilityNodeInfo
    getActiveWindowRoot() {

        try {
            return getRootInActiveWindow();

        } catch (Exception e) {

            Log.e(
                TAG,
                "Unable to get active window root",
                e
            );

            return null;
        }
    }
}
