import numpy as np
import open3d as o3d
import os
import sys


GUI_TITLE = "Point cloud display"


class Viewer3D(object):
    """
    Class to visualize point cloud via Open3D.

    Args:
        - test_mode (bool): rewritten parameter from run_cloud_gui function equals to its test_mode_on

        - out_dir    (str): rewritten parameter from run_cloud_gui function equals to its output_directory

    """
    def __init__(self, test_mode: bool, out_dir: str):
        # Create and initialize gui application instance
        app = o3d.visualization.gui.Application.instance
        app.initialize()
        # Create Visualizer with a given title
        self.main_vis = o3d.visualization.O3DVisualizer(GUI_TITLE)
        app.add_window(self.main_vis)
        # Safe test mode setting and directory
        self.test_mode_on = test_mode
        self.output_directory = out_dir
        # Scene variables
        self.point_cloud_o3d = None
        self.point_cloud_o3d_name = None
        # Set up data and scene
        self.setup_point_clouds()
        self.setup_o3d_scene()

    def setup_point_clouds(self):
        """
        Here is created and set up object which represents chosen via test_mode_on flag point cloud.
        """
        self.test_mode_on = False
        file_path = (
            "default/scene_dense.ply"
            if self.test_mode_on
            else os.path.join(
                self.output_directory, "scene_dense.ply"
            )
        )
        self.point_cloud_o3d = o3d.io.read_point_cloud(file_path)
        # the name is necessary to remove from the scene
        self.point_cloud_o3d_name = f"point cloud {file_path}"

    def update_point_clouds(self):
        """
        Purpose of this function is to prepare new point cloud position before next application tick.
        """
        if self.point_cloud_o3d:
            points = np.asarray(self.point_cloud_o3d.points)
            self.point_cloud_o3d.points = o3d.utility.Vector3dVector(points)

    def setup_o3d_scene(self):
        """
        Here is prepared scene for main point cloud
        """
        self.main_vis.add_geometry(self.point_cloud_o3d_name, self.point_cloud_o3d)
        self.main_vis.reset_camera_to_default()

    def run_one_tick(self):
        """
        This function contains what should be done in one iteration of visualization.
        """
        app = o3d.visualization.gui.Application.instance
        tick_return = app.run_one_tick()
        if tick_return:
            self.main_vis.post_redraw()
        return tick_return


def run_cloud_gui(test_mode_on: bool, output_directory: str):
    """
    This function runs instance of Viewer3D class in infinite loop to visualize point cloud created via OpenMVG.

    Args:
        - test_mode_on    (bool): Indicates usage of previously prepared test point cloud from default file or user's one

        - output_directory (str): String which contains path to user's point cloud used if test_mode_on = False

    """
    try:
        viewer3d = Viewer3D(test_mode_on, output_directory)

        while True:
            viewer3d.update_point_clouds()
            viewer3d.run_one_tick()

    except Exception as e:
        print("An error occurred:", e)


if __name__ == "__main__":
    param1 = bool({'True': True, 'False': False}[sys.argv[1]])
    param2 = sys.argv[2]
    run_cloud_gui(param1, param2)
