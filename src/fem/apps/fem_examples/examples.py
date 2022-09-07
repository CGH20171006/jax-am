import numpy as onp
import numpy.testing as onptest
import jax
import jax.numpy as np
import meshio
import os
from src.fem.jax_fem import Mesh, Plasticity 
from src.fem.solver import solver
from src.fem.utils import modify_vtu_file, save_sol


def plasticity():
    problem_name = "plasticity"
    plasticity_path =  f"src/fem/applications/fem_examples/data/"
    fenicsx_vtu_path_raw = os.path.join(plasticity_path, 'vtk', problem_name, 'fenicsx/sol_p0_000000.vtu')
    fenicsx_vtu_path = os.path.join(plasticity_path, 'vtk', problem_name, 'fenicsx/sol.vtu')
    modify_vtu_file(fenicsx_vtu_path_raw, fenicsx_vtu_path)
    fenicsx_vtu = meshio.read(fenicsx_vtu_path)
    cells = fenicsx_vtu.cells_dict['VTK_LAGRANGE_HEXAHEDRON8'] # 'hexahedron'
    points = fenicsx_vtu.points
    mesh = Mesh(points, cells)
    H = 10.

    def top(point):
        return np.isclose(point[2], H, atol=1e-5)

    def bottom(point):
        return np.isclose(point[2], 0., atol=1e-5)

    def dirichlet_val_bottom(point):
        return 0.

    def get_dirichlet_top(disp):
        def val_fn(point):
            return disp
        return val_fn

    disps_path = os.path.join(plasticity_path, 'numpy', problem_name, 'fenicsx/disps.npy')
    disps = np.load(disps_path)

    location_fns = [bottom, bottom, bottom, top, top, top]
    value_fns = [dirichlet_val_bottom, dirichlet_val_bottom, dirichlet_val_bottom, 
                 dirichlet_val_bottom, dirichlet_val_bottom, get_dirichlet_top(disps[0])]
    vecs = [0, 1, 2, 0, 1, 2]
    dirichlet_bc_info = [location_fns, vecs, value_fns]

    problem = Plasticity(f"{problem_name}", mesh, dirichlet_bc_info)
    avg_stresses = []

    for i, disp in enumerate(disps):
        print(f"\nStep {i} in {len(disps)}, disp = {disp}")
        dirichlet_bc_info[-1][-1] = get_dirichlet_top(disp)
        problem.update_Dirichlet_boundary_conditions(dirichlet_bc_info)
        sol = solver(problem)
        problem.update_stress_strain(sol)
        avg_stress = problem.compute_avg_stress()
        print(avg_stress)
        avg_stresses.append(avg_stress)

    avg_stresses = np.array(avg_stresses)

    jax_vtu_path = os.path.join(plasticity_path, 'vtk', problem_name, 'jax_fem/sol.vtu')

    save_sol(problem, sol, jax_vtu_path)
    jax_fem_vtu = meshio.read(jax_vtu_path)

    jax_fem_sol = jax_fem_vtu.point_data['sol']
    fenicsx_sol = fenicsx_vtu.point_data['sol'].reshape(jax_fem_sol.shape)

    print(f"Solution absolute value differs by {np.max(np.absolute(jax_fem_sol - fenicsx_sol))} between FEniCSx and JAX-FEM")

    fenicsx_avg_stresses_path = os.path.join(plasticity_path, 'numpy', problem_name, 'fenicsx/avg_stresses.npy')
    jax_fem_avg_stresses_path = os.path.join(plasticity_path, 'numpy', problem_name, 'jax_fem/avg_stresses.npy')

    fenicsx_avg_stresses = np.load(fenicsx_avg_stresses_path)
    jax_fem_avg_stresses = avg_stresses[:, 2, 2]
    np.save(jax_fem_avg_stresses_path, jax_fem_avg_stresses)

    print(f"FEniCSx computes stresses to be {fenicsx_avg_stresses}")
    print(f"JAX-FEM computes stresses to be {jax_fem_avg_stresses}")



if __name__ == "__main__":
    plasticity()