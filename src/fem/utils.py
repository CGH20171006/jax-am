import meshio
import os
import numpy as onp


def save_sol(problem, sol, sol_file, cell_infos=None):
    # Create a directory if not exists
    sol_dir = os.path.dirname(sol_file)
    if not os.path.exists(sol_dir):
        os.makedirs(sol_dir)

    out_mesh = meshio.Mesh(points=problem.points, cells={'hexahedron': problem.cells})
    out_mesh.point_data['sol'] = onp.array(sol, dtype=onp.float32)
    if cell_infos is not None:
        for cell_info in cell_infos:
            name, data = cell_info
            assert data.shape == (problem.num_cells,), "cell data wrong shape!"
            out_mesh.cell_data[name] = [onp.array(data, dtype=onp.float32)]
    out_mesh.write(sol_file)


def modify_vtu_file(input_file_path, output_file_path):
    """Convert version 2.2 of vtu file to version 1.0
    meshio does not accept version 2.2, raising error of
    meshio._exceptions.ReadError: Unknown VTU file version '2.2'.
    """
    fin = open(input_file_path, "r")
    fout = open(output_file_path, "w")
    for line in fin:
        fout.write(line.replace('<VTKFile type="UnstructuredGrid" version="2.2">', '<VTKFile type="UnstructuredGrid" version="1.0">'))
    fin.close()
    fout.close()
