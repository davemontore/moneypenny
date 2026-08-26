import unittest
from unittest.mock import Mock, patch

from gui import MoneyPennyGUI


class CorrectionDialogVisibilityTests(unittest.TestCase):
    def test_confirmation_does_not_restore_the_main_window(self):
        gui = MoneyPennyGUI.__new__(MoneyPennyGUI)
        gui.app = Mock()
        gui.window = Mock()
        gui._deiconify = Mock()
        gui._log_activity = Mock()

        with patch("gui.messagebox.askyesno", return_value=False) as askyesno:
            gui._confirm_correction("alternative", "alternative to Meta and others")

        gui._deiconify.assert_not_called()
        askyesno.assert_called_once()
        self.assertIs(askyesno.call_args.kwargs["parent"], gui.window)


if __name__ == "__main__":
    unittest.main()
