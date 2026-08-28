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


class PunctuationLabFolderTests(unittest.TestCase):
    def test_directory_creation_failure_shows_error(self):
        gui = MoneyPennyGUI.__new__(MoneyPennyGUI)
        output_dir = Mock()
        output_dir.mkdir.side_effect = OSError("disk unavailable")
        gui.app = Mock()
        gui.app.punctuation_lab.output_dir = output_dir

        with (
            patch("gui.os.startfile") as startfile,
            patch("gui.messagebox.showerror") as showerror,
        ):
            gui._open_punctuation_lab_folder()

        startfile.assert_not_called()
        showerror.assert_called_once()


if __name__ == "__main__":
    unittest.main()
