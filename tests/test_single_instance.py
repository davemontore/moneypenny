import ctypes
import sys
import unittest
import uuid
from ctypes import wintypes
from unittest.mock import patch

import voice_to_text


@unittest.skipUnless(sys.platform == "win32", "Windows named-object behavior")
class SingleInstanceActivationTests(unittest.TestCase):
    def setUp(self):
        unique_suffix = uuid.uuid4().hex
        self.original_mutex_name = voice_to_text.SINGLE_INSTANCE_MUTEX_NAME
        self.original_event_name = voice_to_text.ACTIVATE_WINDOW_EVENT_NAME
        voice_to_text.SINGLE_INSTANCE_MUTEX_NAME = (
            f"Local\\MoneyPennyTestMutex-{unique_suffix}"
        )
        voice_to_text.ACTIVATE_WINDOW_EVENT_NAME = (
            f"Local\\MoneyPennyTestEvent-{unique_suffix}"
        )

        self.kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        self.kernel32.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
        self.kernel32.WaitForSingleObject.restype = wintypes.DWORD
        self.kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
        self.kernel32.CloseHandle.restype = wintypes.BOOL
        self.handles = []

    def tearDown(self):
        for handle in self.handles:
            self.kernel32.CloseHandle(handle)
        voice_to_text.SINGLE_INSTANCE_MUTEX_NAME = self.original_mutex_name
        voice_to_text.ACTIVATE_WINDOW_EVENT_NAME = self.original_event_name

    def test_second_lock_attempt_is_rejected(self):
        first_handle = voice_to_text._acquire_single_instance_lock()
        self.assertTrue(first_handle)
        self.handles.append(first_handle)

        self.assertIsNone(voice_to_text._acquire_single_instance_lock())

    def test_second_launch_sets_primary_activation_event(self):
        event_handle = voice_to_text._create_activation_event()
        self.assertTrue(event_handle)
        self.handles.append(event_handle)

        with patch.object(voice_to_text, "_focus_existing_window", return_value=True):
            voice_to_text._signal_existing_instance()

        WAIT_OBJECT_0 = 0
        self.assertEqual(
            self.kernel32.WaitForSingleObject(event_handle, 0),
            WAIT_OBJECT_0,
        )


if __name__ == "__main__":
    unittest.main()
