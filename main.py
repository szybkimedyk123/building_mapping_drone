"""This is the main function of the whole project. Here you can find MainWindow class which purpose is to process
interaction with the user and running of other scripts. There are specific params connected with animations,
display options and communication."""
import multiprocessing
import sys
import threading
import markdown2

import numpy as np
import subprocess

from PySide2.QtGui import QPixmap, QCursor, QTransform
from PySide2.QtWidgets import QStackedWidget, QApplication, QMainWindow, QFileDialog, QLabel
from PySide2.QtUiTools import QUiLoader
from PySide2.QtCore import Qt, QTimer, QPoint

from srcUI.images import main_ui_bit

WRONG_DIRECTORY_MESSAGE = 'Please select correct directory.'

ANIMATION_X_POS = 100
ANIMATION_Y_POS = 245
TRAMPOLINE_X_POS = 125
TRAMPOLINE_Y_POS = 475

TEST_MODE_ON = False


class MainWindow(QMainWindow):
    """
    Purpose of this class is to:

    - process interactions between user and main_ui or options_ui;
    - run the main algorithms and update the UI status as they execute;
    - create loading screen animation and text messages to user;
    - display effects of algorithms in interactive windows.

    See functions descriptions for more detailed information.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        # Application parameters
        self.input_directory = None
        self.output_directory = None
        self.script_completed = False  # Initialize the flag
        self.process_timer = QTimer()
        self.process_timer.timeout.connect(self.check_script_status)
        self.process_not_finished = True

        """LOAD AND CONFIGURE MAIN UI"""
        loader = QUiLoader()
        self.window = loader.load(r"srcUI/main_ui.ui", self)

        # Connect signals to main_ui
        self.window.close_butt.clicked.connect(self.close_app)
        self.window.input_dir_butt.clicked.connect(self.select_input_directory)
        self.window.output_dir_butt.clicked.connect(self.select_output_directory)
        self.window.options_butt.clicked.connect(self.options_dialog)
        self.window.start_butt.clicked.connect(self.start_process)
        self.window.cloud_butt.clicked.connect(self.cloud_display)
        self.window.mesh_butt.clicked.connect(self.mesh_display)
        self.window.help_butt.clicked.connect(self.open_help)

        # Init buttons states for main_ui
        self.window.cloud_butt.setEnabled(True)
        self.window.mesh_butt.setEnabled(True)

        # Load the image for background of main_ui
        background_image = QPixmap(':/labels/background')
        self.window.background.setPixmap(background_image)

        # Load the image for logo of main_ui
        logo_image = QPixmap(':/labels/logo')
        self.window.logo.setPixmap(logo_image)

        # Set funny cursor of main_ui
        cursor_image = QPixmap(':/labels/cursor')
        hot_x = 0  # Set hotspot X coordinate
        hot_y = 0  # Set hotspot Y coordinate
        cursor = QCursor(cursor_image, hot_x, hot_y)
        self.window.setCursor(cursor)

        """LOAD AND CONFIGURE OPTIONS UI"""
        loader = QUiLoader()
        self.options_window = loader.load(r"srcUI/options_ui.ui", self)

        # Connect main signals to options_ui
        self.options_window.close_opt_butt.clicked.connect(self.close_options_window)
        self.options_window.apply_butt.clicked.connect(self.apply_options)
        # Connect sliders to sliders update
        self.options_window.options_1_max_res_slid.valueChanged.connect(self.options_value_changed)
        self.options_window.options_1_est_roi_slid.valueChanged.connect(self.options_value_changed)
        self.options_window.options_1_verb_slid.valueChanged.connect(self.options_value_changed)
        self.options_window.options_2_decim_slid.valueChanged.connect(self.options_value_changed)
        self.options_window.options_2_smot_iter_slid.valueChanged.connect(self.options_value_changed)
        self.options_window.options_2_min_dis_slid.valueChanged.connect(self.options_value_changed)
        self.options_window.options_2_ext_type_rad.clicked.connect(self.options_value_changed)

        # Load the image for background of options_ui
        background_no_drone_image = QPixmap(':/labels/background_no_drone')
        self.options_window.background.setPixmap(background_no_drone_image)

        # Load the image for logo of options_ui
        self.options_window.logo.setPixmap(logo_image)

        # Set funny cursor of options_ui
        self.options_window.setCursor(cursor)

        """LOAD AND CONFIGURE HELP UI"""
        loader = QUiLoader()
        self.help_window = loader.load(r"srcUI/help_ui.ui", self)
        # Connect main signals to help_ui
        self.help_window.close_butt.clicked.connect(self.close_help)
        self.help_window.drone_butt.clicked.connect(self.show_drone_help)
        self.help_window.user_butt.clicked.connect(self.show_user_help)

        # Load the image for background of options_ui
        background_no_drone_image = QPixmap(':/labels/background_no_drone')
        self.help_window.background.setPixmap(background_no_drone_image)

        # Set funny cursor of options_ui
        self.help_window.setCursor(cursor)

        """ANIMATION VARIABLES"""
        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self.animate_drone)
        self.rotation = 0
        self.loading_image = QPixmap(':/labels/loading')
        self.loading_image_w = self.loading_image.width()
        self.loading_image_h = self.loading_image.height()
        self.loading_label = None
        self.trampoline_label = None
        self.window.loading_mess_butt.setVisible(False)

        """WINDOW MOVEMENT VARIABLES"""
        self.dragging = False
        self.offset = QPoint()
        self.original_position = QPoint()

        """THREADING VARIABLES"""
        self.cloud_process = None
        self.mesh_process = None

        # Set up start view
        self.options_window.close()
        self.help_window.close()
        self.window.show()

    """
    INSTRUCTIONS FOR USER AND DRONE OPERATOR STUFF 
    """

    def open_help(self):
        """
        This function changes displayed UI from main_ui to options_ui
        """
        # Close the current main window
        self.window.close()
        # Show the new options window
        self.help_window.show()

    def close_help(self):
        """
        This function changes displayed UI from options_ui to main_ui
        """
        # Close the current main window
        self.help_window.close()
        # Show the new options window
        self.window.show()

    def show_drone_help(self):
        """
        This function changes displayed help message to drone operator's instruction
        """
        # Read content from the TXT file and with markdown2 convert to html
        with open("default/drone_instruction.txt", "r") as txt_file:
            html_content = markdown2.markdown(txt_file.read(), extras=["fenced-code-blocks"])
        # Set the HTML content to QTextBrowser
        self.help_window.display_brow.setHtml(html_content)

    def show_user_help(self):
        """
        This function changes displayed help message to user's instruction
        """
        # Read content from the TXT file and with markdown2 convert to html
        with open("default/user_instruction.txt", "r") as txt_file:
            html_content = markdown2.markdown(txt_file.read(), extras=["fenced-code-blocks"])
        # Set the HTML content to QTextBrowser
        self.help_window.display_brow.setHtml(html_content)


    """
    ONLY INTERACTIONS BETWEEN USER AND MAIN_UI
    """

    def close_app(self):
        """
        Save close of whole application
        """
        if self.cloud_process is not None:
            self.cloud_process.terminate()
        if self.mesh_process is not None:
            self.mesh_process.terminate()
        self.window.close()
        app.quit()  # Assuming 'app' is the QApplication instance

    def select_input_directory(self):
        """
        Display of QFileDialog.Options window to enable changing input directory plus checking if it is valid via
        QFileDialog.getExistingDirectory.
        """
        options = QFileDialog.Options()
        options |= QFileDialog.ShowDirsOnly
        if directory := QFileDialog.getExistingDirectory(
                self, "Select Directory", options=options
        ):
            self.input_directory = directory
            self.window.input_text_browser.setPlainText(directory)
        else:
            self.window.input_text_browser.setPlainText(WRONG_DIRECTORY_MESSAGE)

    def select_output_directory(self):
        """
        Display of QFileDialog.Options window to enable changing output directory plus checking if it is valid via
        QFileDialog.getExistingDirectory.
        """
        options = QFileDialog.Options()
        options |= QFileDialog.ShowDirsOnly
        if directory := QFileDialog.getExistingDirectory(
                self, "Select Directory", options=options
        ):
            self.output_directory = directory
            self.window.output_text_browser.setPlainText(directory)
        else:
            self.window.output_text_browser.setPlainText(WRONG_DIRECTORY_MESSAGE)

    def options_dialog(self):
        """
        Here is changed displayed window from main_ui to options_ui.
        """
        # Close the current main window
        self.window.close()
        # Show the new options window
        self.options_window.show()

    """
    ONLY INTERACTIONS BETWEEN USER AND OPTIONS_UI
    """

    def close_options_window(self):
        """
        Here is changed currently shown window from options_ui to main_u without applying of chosen settings (if they
        are).
        """
        # Close the current options window
        self.options_window.close()
        # Show the new main window
        self.window.show()

    def apply_options(self):
        """
        Here is changed currently shown window from options_ui to main_ui with applying of chosen settings (if they
        are).
        """
        # Close the current options window
        self.options_window.close()

        # Show the new main window
        self.window.show()

    def options_value_changed(self):
        """
        Here display of sliders and radio buttons values in options_ui window is updated.
        """
        self.options_window.options_1_max_res_butt.setText(f"Max resolution: "
                                                           f"{self.options_window.options_1_max_res_slid.value()}")
        self.options_window.options_1_est_roi_butt.setText(f"Estimate roi: "
                                                           f"{self.options_window.options_1_est_roi_slid.value()}")
        self.options_window.options_1_verb_butt.setText(f"Verbosity: "
                                                        f"{self.options_window.options_1_verb_slid.value()}")
        self.options_window.options_2_decim_butt.setText(f"Decimate mesh: "
                                                         f"{self.options_window.options_2_decim_slid.value()/10}")
        self.options_window.options_2_smot_iter_butt.setText(f"Smoothing iterations: "
                                                             f"{self.options_window.options_2_smot_iter_slid.value()}")
        self.options_window.options_2_min_dis_butt.setText(f"Minimal point distance: "
                                                           f"{self.options_window.options_2_min_dis_slid.value()}")
        if self.options_window.options_2_ext_type_rad.isChecked():
            self.options_window.options_2_ext_type_rad.setText("Export type: .ply")
        else:
            self.options_window.options_2_ext_type_rad.setText("Export type: .obj")

    """
    MOVING THE WINDOWS
    """

    def mousePressEvent(self, event):
        """
        Overwritten mousePressEvent function from QMainWindow. Done for purpose of enabling moving whole application
        window.
        """
        if event.button() == Qt.LeftButton:
            self.dragging = True
            self.offset = event.globalPos() - self.parent().pos()
            self.original_position = self.parent().pos()

    def mouseMoveEvent(self, event):
        """
        Overwritten mouseMoveEvent function from QMainWindow. Done for purpose of enabling moving whole application
        window.
        """
        if self.dragging:
            new_pos = event.globalPos() - self.offset
            self.parent().move(new_pos)

    def mouseReleaseEvent(self, event):
        """
        Overwritten mouseReleaseEvent function from QMainWindow. Done for purpose of enabling moving whole application
        window.
        """
        if event.button() == Qt.LeftButton:
            self.dragging = False
            self.original_position = QPoint()

    """
    CORE ALGORITHM PROCESSING AND INTERACTION FUNCTIONS
    """

    def run_processing_script(self, test_windows: bool = False):
        """
        Here is called execution of main application .sh script on chosen data or test_win.py script depends on flags.

        Args:

            - test_windows (bool): Indicates to call test_win.py from src package instead of starting execution of script

        """
        def run_script():
            try:
                if test_windows:
                    command = ["python3", "src/test_win.py"]
                else:
                    # Build the command as a list of strings
                    command = ["./tools/pipeline.sh"]
                    command.extend(["-i", str(self.input_directory),
                                    "-o", str(self.output_directory),
                                    "-m", str(self.options_window.options_1_max_res_slid.value()),
                                    "-e", str(self.options_window.options_1_est_roi_slid.value()),
                                    "-v", str(self.options_window.options_1_verb_slid.value()),
                                    "-s", str(float(self.options_window.options_2_decim_slid.value() / 10)),
                                    "-d", str(int(self.options_window.options_1_rem_dmaps_rad.isChecked())),
                                    "-r", str(int(self.options_window.options_2_integrate_roi_rad.isChecked())),
                                    "-t", str(self.options_window.options_2_smot_iter_slid.value()),
                                    "-p", str(self.options_window.options_2_min_dis_slid.value()),
                                    "-x", str(int(self.options_window.options_2_ext_type_rad.isChecked())),
                                    ])
                result = subprocess.run(command, check=True, text=True)
                self.script_completed = result.returncode == 0
                print("Script output:", result.stdout)

            except subprocess.CalledProcessError as e:
                print(f"Script failed with exit code {e.returncode}. Error message: {e.stderr}")

        # Start the timer to periodically check the script status
        self.process_timer.start(1000)  # Check every 1 second
        # Run the script in a separate thread
        script_thread = threading.Thread(target=run_script)
        script_thread.start()

    def check_script_status(self):
        """
        Purpose of this function is to check every 1 second if algorithm ended. It is done via connection with QTimer.
        When process ends a few things takes place:

        - turning off animation;
        - checking back background to previous one;
        - enabling functional buttons again.
        """
        if self.script_completed:
            print("Script completed successfully.")
            # When process ends change status of buttons for display and animation
            self.loading_label.close()
            self.loading_label = None
            self.trampoline_label.close()
            self.trampoline_label = None
            self.rotation = 0
            # Stop animation, hide message
            self.animation_timer.stop()
            self.window.loading_mess_butt.setVisible(False)
            # Change background
            self.window.background.setPixmap(QPixmap(':/labels/background'))
            # Show ui buttons and so on
            self.set_main_window_status(True)
            self.script_completed = False
            self.process_timer.stop()
            # Set flag for display
            self.process_not_finished = False

    def set_main_window_status(self, flag: bool):
        """
        Function which blocs and hides interface for purpose of processing algorithm and loading screen.

        Args:
            - flag (bool): Indicates visibility of the core UI functionalities.
        """
        # Set status of buttons
        self.window.close_butt.setEnabled(flag)
        self.window.input_dir_butt.setEnabled(flag)
        self.window.output_dir_butt.setEnabled(flag)
        self.window.options_butt.setEnabled(flag)
        self.window.start_butt.setEnabled(flag)
        self.window.cloud_butt.setEnabled(flag)
        self.window.mesh_butt.setEnabled(flag)
        self.window.help_butt.setEnabled(flag)

        self.window.close_butt.setVisible(flag)
        self.window.input_dir_butt.setVisible(flag)
        self.window.output_dir_butt.setVisible(flag)
        self.window.options_butt.setVisible(flag)
        self.window.start_butt.setVisible(flag)
        self.window.cloud_butt.setVisible(flag)
        self.window.mesh_butt.setVisible(flag)
        self.window.help_butt.setVisible(flag)
        # Set status of text edits
        self.window.output_text_browser.setVisible(flag)
        self.window.input_text_browser.setVisible(flag)

    def start_process(self):
        """
        This function starts processing of input data via OpenMVG and OpenMVS. It also checks if user set proper input
        and output paths for the process.
        """
        if self.input_directory:
            if self.output_directory:
                # Init loading gui and run
                self.loading_screen()
                self.run_processing_script(test_windows=TEST_MODE_ON)
            else:
                self.window.output_text_browser.setPlainText(WRONG_DIRECTORY_MESSAGE)
        else:
            self.window.input_text_browser.setPlainText(WRONG_DIRECTORY_MESSAGE)

    """
    LOADING SCREEN'S ANIMATION AND TEXT
    """

    def loading_screen(self):
        """
        Target of this function is to:

        - change the background image of UI;
        - call set_main_window_status to hide core UI functionalities;
        - create animation and start loading screen.
        """
        # Disable buttons set up position of label
        self.set_main_window_status(False)
        self.loading_label = QLabel(self.window)
        self.loading_label.move(ANIMATION_X_POS, ANIMATION_Y_POS)
        # Create trampoline
        self.trampoline_label = QLabel(self.window)
        self.trampoline_label.setPixmap(QPixmap(':/labels/trampoline'))
        self.trampoline_label.move(TRAMPOLINE_X_POS, TRAMPOLINE_Y_POS)
        self.trampoline_label.show()
        # Change background
        self.window.background.setPixmap(QPixmap(':/labels/background_no_drone'))
        # Start animation, display message
        self.animation_timer.start(10)
        self.window.loading_mess_butt.setVisible(True)

    def animate_drone(self):
        """
        This function updates move and rotation of a drone's picture for purpose of loading screen.
        """
        if self.rotation == 360:
            self.rotation = 0
        else:
            self.rotation += 1
        # Rotate drone
        transform = QTransform()
        transform.rotate(self.rotation)
        rotated_pixmap = self.loading_image.transformed(transform)

        self.loading_label.setPixmap(rotated_pixmap)
        # Change its position
        temp_x = ANIMATION_X_POS + (self.loading_image_w - rotated_pixmap.width()) / 2
        temp_y = ANIMATION_Y_POS - self.loading_image_h / 2 * np.abs(np.cos(np.deg2rad(self.rotation)))
        self.loading_label.move(temp_x, temp_y)

        self.loading_label.show()

    """
    DISPLAY FUNCTIONS
    """

    def cloud_display(self):
        """
        Here is called point_cloud_visualizer from src package to create display window for effects of OpenMVG.
        """

        def run_cloud_display():
            subprocess.run(["python3", "src/point_cloud_visualizer.py", str(self.process_not_finished),
                           self.window.output_text_browser.toPlainText()], stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE, stdin=subprocess.PIPE)

        if self.cloud_process is None:
            self.cloud_process = multiprocessing.Process(target=run_cloud_display)
            self.cloud_process.start()
        elif self.cloud_process.is_alive():
            self.cloud_process.terminate()
            self.cloud_process = multiprocessing.Process(target=run_cloud_display)
            self.cloud_process.start()

    def mesh_display(self):
        """
        This function creates display for mesh objects which represents the final effect.
        """

        def run_mesh_display():
            subprocess.run(["python3", "src/mesh_lib.py", str(self.process_not_finished),
                            self.window.output_text_browser.toPlainText()])

        if self.mesh_process is None:
            self.mesh_process = multiprocessing.Process(target=run_mesh_display)
            self.mesh_process.start()
        elif self.mesh_process.is_alive():
            self.mesh_process.terminate()
            self.mesh_process = multiprocessing.Process(target=run_mesh_display)
            self.mesh_process.start()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    win = MainWindow()

    widget = QStackedWidget()
    widget.addWidget(win)
    widget.setFixedWidth(600)
    widget.setFixedHeight(800)
    widget.setWindowFlag(Qt.FramelessWindowHint)
    widget.show()

    sys.exit(app.exec_())
