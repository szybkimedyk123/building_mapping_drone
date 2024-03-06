"""This is the library for displaying mesh data and point clouds. Contains also basic operation on mesh"""
import os

import numpy as np
import open3d as o3d
import sys


class MeshLib:
    """
    Class to load point cloud in .ply format and convert it to triangle mesh also in .ply

    Args:
            - param point_cloud_path    (str): Path to .ply file which contains point cloud

            - param output_mesh_path    (str): Path to .ply file where output file will be saved

    """
    def __init__(self, point_cloud_path: str, output_mesh_path: str):
        """
        Initialise class parameters

        Args:
            - param point_cloud_path    (str): Path to .ply file which contains point cloud

            - param output_mesh_path    (str): Path to .ply file where output file will be saved

        """
        self.point_cloud_path = point_cloud_path
        self.output_mesh_path = output_mesh_path
        self.point_cloud = None
        self.mesh = None

    def load_point_cloud(self):
        """
        Load file with point cloud
        """
        self.point_cloud = o3d.io.read_point_cloud(self.point_cloud_path)

    def visualize(self, geometry: o3d.geometry):
        """
        Visualize 3D object in open3d window

        Args:
            - param geometry    (o3d.geometry):

        """
        vis = o3d.visualization.Visualizer()
        vis.create_window()
        if isinstance(geometry, o3d.geometry.TriangleMesh):
            geometry.compute_vertex_normals()
        vis.add_geometry(geometry)
        vis.run()
        vis.destroy_window()

    def perform_bpa(self):
        """
        Ball pivoting algorithm, which convert point cloud into triangle mesh
        """
        pcd_with_normals = self.point_cloud
        if not pcd_with_normals.has_normals():
            pcd_with_normals.estimate_normals()

        distances = pcd_with_normals.compute_nearest_neighbor_distance()
        avg_dist = np.mean(distances)
        radius = 3 * avg_dist

        bpa_mesh = o3d.geometry.TriangleMesh.create_from_point_cloud_ball_pivoting(pcd_with_normals, o3d.utility.DoubleVector([radius, radius * 2]))
        dec_mesh = bpa_mesh.simplify_quadric_decimation(100000)
        dec_mesh.remove_degenerate_triangles()
        dec_mesh.remove_duplicated_triangles()
        dec_mesh.remove_duplicated_vertices()
        dec_mesh.remove_non_manifold_edges()

        o3d.io.write_triangle_mesh(self.output_mesh_path, bpa_mesh)
        self.mesh = bpa_mesh

    def load_mesh(self):
        """
        Load file with triangle mesh
        """
        self.mesh = o3d.io.read_triangle_mesh(self.output_mesh_path)


if __name__ == '__main__':
    default_flag = bool({'True': True, 'False': False}[sys.argv[1]])
    default_path = sys.argv[2]

    default_flag = False
    mesh_path = (
        "default/scene_dense_mesh.ply"
        if default_flag
        else os.path.join(
            default_path, "scene_dense_mesh.ply"
        )
    )
    visualizer = MeshLib('../out/scene_dense.ply', mesh_path)
    visualizer.load_mesh()
    visualizer.visualize(visualizer.mesh)
