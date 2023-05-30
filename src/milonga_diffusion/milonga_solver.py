import sys, os
from os.path import join
import kgm_gmsh_api as gmsh_api
import kgm_gmsh_api.gmsh as gmsh
import numpy as np
import pandas
import math
import json
import re, logging, pathlib
import subprocess
import string
import datetime
import shutil
import time

class MilongaSolver:
    def __init__(self, temp_root, cells_string, u=5, lc=1.25):

        self.u = u
        self.lc = lc

        self.id = id = str(datetime.datetime.now().strftime("%H%M%S%s"))
        self.file_root = os.path.join(temp_root, id)
        logging.info("here-2")
        #os.mkdir(self.file_root)
        pathlib.Path(self.file_root).mkdir(parents=True, exist_ok=True)
        logging.info("here0")

        self.cells_string = cells_string
        self.mil_path = join(self.file_root, f"{id}.mil")
        self.msh_path = join(self.file_root, f"{id}.msh")
        self.gp_path = join(self.file_root, f"{id}.gp")
        self.fast_png_path = join(self.file_root, f"{id}_fast.png")
        self.thermal_png_path = join(self.file_root, f"{id}_thermal.png")
        self.dat_path = join(self.file_root, f"{id}.dat")

    def generate_mesh(self):

        u = self.u
        lc = self.lc

        cells = json.loads(self.cells_string)
        gmsh.initialize()#sys.argv
        gmsh.model.add(self.id)

        # cells = {'0,0': 'fuel', '1,0': 'fuel', '2,0': 'water', '0,1': 'water', '1,1': 'fuel', '2,1': 'fuel', '0,2': 'water', '1,2': 'fuel', '2,2': 'fuel'}
        max_x = 0
        max_y = 0
        for cell in cells:
            coords = cell.split(',')
            x = int(coords[0])
            y = int(coords[1])
            # print(x)
            # print(y)
            if x > max_x:
                max_x = x
            if y > max_y:
                max_y = y

        pointDict = {}
        for j in range(max_y+2):
            for i in range(max_x+2):
                x = i*u
                y = j*u
                id = gmsh.model.geo.addPoint(x, y, 0, lc)
                pointDict.update({str(i)+','+str(j): id})


        innerlines = 0
        matDict = {}
        lineDict = {}
        for cell in cells:
            coords = cell.split(',')
            x = int(coords[0])
            y = int(coords[1])

            p1 = pointDict[str(x)+','+str(y)]
            p2 = pointDict[str(x+1)+','+str(y)]
            p3 = pointDict[str(x)+','+str(y+1)]
            p4 = pointDict[str(x+1)+','+str(y+1)]
            
            #make or get line 1
            l1v = str(x)+","+str(y)+","+str(x+1)+","+str(y)
            if l1v not in lineDict.keys():
                l1 = gmsh.model.geo.addLine(p1, p2)
                lineDict.update({l1v: l1})
            else:
                innerlines += 1
                l1 = lineDict[l1v]

            #make or get line 2
            l2v = str(x)+","+str(y+1)+","+str(x+1)+","+str(y+1)
            if l2v not in lineDict.keys():
                l2 = gmsh.model.geo.addLine(p3, p4)
                lineDict.update({l2v: l2})
            else:
                innerlines += 1
                l2 = lineDict[l2v]

            #make or get line 3
            l3v = str(x)+","+str(y)+","+str(x)+","+str(y+1)
            if l3v not in lineDict.keys():
                l3 = gmsh.model.geo.addLine(p1, p3)
                lineDict.update({l3v: l3})
            else:
                innerlines += 1
                l3 = lineDict[l3v]

            #make or get line 4
            l4v = str(x+1)+","+str(y)+","+str(x+1)+","+str(y+1)
            if l4v not in lineDict.keys():
                l4 = gmsh.model.geo.addLine(p2, p4)
                lineDict.update({l4v: l4})
            else:
                innerlines += 1
                l4 = lineDict[l4v]


            curveid = gmsh.model.geo.addCurveLoop([-l4, l1, l2, l3])
            curveid = gmsh.model.geo.addCurveLoop([l1, l4, -l2, -l3])
            cellid = gmsh.model.geo.addPlaneSurface([curveid])

            mat = cells[cell]
            if mat in matDict.keys():
                matDict[mat].append(cellid)
            else:
                matDict.update({mat: [cellid]})

        j = 1
        for mat in matDict:
            gmsh.model.addPhysicalGroup(2, matDict[mat], j) #2d, surf 1, tag 1
            gmsh.model.setPhysicalName(2, j, mat) # 2d, surf 1, name
            j += 1

        top = str(max_y+1)
        right = str(max_x+1)

        #get boundary lines
        bottom_boundary = []
        top_boundary = []
        for i in range(max_x+1):
            bottom_boundary.append(lineDict[str(i)+",0,"+str(i+1)+",0"])
            top_boundary.append(lineDict[str(i)+","+top+","+str(i+1)+","+top])

        right_boundary = []
        left_boundary = []
        for j in range(max_y+1):
            right_boundary.append(lineDict[right+','+str(j)+','+right+','+str(j+1)])
            left_boundary.append(lineDict["0,"+str(j)+",0,"+str(j+1)])

        boundary_loop = bottom_boundary + right_boundary + list(map(lambda x: "-"+str(x), top_boundary)) + list(map(lambda x: "-"+str(x), left_boundary))

        p = gmsh.model.addPhysicalGroup(1, boundary_loop) #2d, surf 1, tag 1

        gmsh.model.setPhysicalName(1, p, 'boundary') # 2d, surf 1, name

        gmsh.model.occ.synchronize()
        gmsh.model.mesh.generate(2) # 2d
        gmsh.write(self.msh_path)
        gmsh.finalize()


    def generate_mil(self):

        t_string = self.mil_template.format(msh_path=self.msh_path, dat_path=self.dat_path)

        with open(self.mil_path, 'w+') as f:
            f.write(t_string)

        out = subprocess.check_output(['milonga', self.mil_path])

        try:
            self.keff = float(re.findall("k:\t(\d\.\d*)", out.decode())[0])
        except:
            self.keff = 0
            #print('k is zero')


    def generate_plot(self, gnuplot_palette_path):

        with open(self.gp_path, 'w+') as f2:
            f2.write(f'''
            load "{gnuplot_palette_path}"
            set term png
            set output "{self.fast_png_path}"
            set view map
            set size ratio -1
            set title "Fast Neutron Flux"
            set object 1 rectangle from screen 0,0 to screen 1,1 fillcolor rgb"#FFFFFF" behind
            set pm3d interpolate 8,8
            set dgrid3d
            unset border
            set lmargin at screen 0.05;
            set rmargin at screen 0.9;
            set bmargin at screen 0.1;
            set tmargin at screen 0.87;
            splot "{self.dat_path}" using 1:2:3 with pm3d notitle

            set term png
            set output "{self.thermal_png_path}"
            set view map
            set size ratio -1
            set title "Thermal Neutron Flux"
            set object 1 rectangle from screen 0,0 to screen 1,1 fillcolor rgb"#FFFFFF" behind
            set dgrid3d
            unset border
            set lmargin at screen 0.0;
            set rmargin at screen 1;
            set bmargin at screen 0.1;
            set tmargin at screen 0.87;
            splot "{self.dat_path}" using 1:2:4 with pm3d notitle'''
            )

        if self.keff > 0:
            os.system('chmod 775 ' + self.gp_path)
            os.system('gnuplot ' + self.gp_path)

        #os.system('chmod 775 ' + )
        #os.system('gnuplot '+root_dir + 'static/' +id+'_diffusion.gp')
        #os.remove(root_dir + 'static/' +id+'_diffusion.gp')
        #os.remove(root_dir + 'static/' +id+'.dat')
        
    mil_template = r"""MESH NAME unstructured FILE_PATH {msh_path}

    # define the formulation, scheme, dimensions and energy groups
    MILONGA_PROBLEM FORMULATION diffusion SCHEME volumes DIMENSIONS 2 GROUPS 2 
    #MILONGA_PROBLEM FORMULATION s4 SCHEME volumes DIMENSIONS 2 GROUPS 2 

    # define materials and cross sections according to the two-group constants
    # each material corresponds to a physical entity in the geometry file
    #Bg2 = 0.8e-4  # axial geometric buckling in the z direction
    #Bg2 = 1
    MATERIAL fuel   SigmaT_1    0.650917       SigmaT_2    2.13800      \
                    SigmaS_1.1  0.             SigmaS_1.2 0.0342008     \
                    SigmaS_2.1  0              SigmaS_2.2 2.06880       \
                    nuSigmaF_1  1.004*0.61475  nuSigmaF_2  2.5*0.045704 \

    MATERIAL air    SigmaT_1 0.1  SigmaT_2 0.05


    MATERIAL water  SigmaT_1    1.331518007    SigmaT_2    4.37350       \
                    SigmaS_1.1  1.226381244    SigmaS_1.2  0.1046395340  \
                    SigmaS_2.1  0              SigmaS_2.2  4.35470 \


    #MATERIAL source_abs    S 50 SigmaT 50 SigmaS 0
    MATERIAL poison      S 0  SigmaT_1 5  SigmaT_2 5
    #MATERIAL void          S 0  SigmaT 0  SigmaS 0
    #MATERIAL source_scat   S 1  SigmaT 1  SigmaS 0.9
    #MATERIAL reflector     S 0  SigmaT 1  SigmaS 0.9

    # define boundary conditions as requested by the problem, applied
    # to appropriate physical entities defined in the geometry file
    PHYSICAL_ENTITY NAME fuel MATERIAL fuel
    PHYSICAL_ENTITY NAME water MATERIAL water
    PHYSICAL_ENTITY NAME air MATERIAL air
    PHYSICAL_ENTITY NAME poison MATERIAL poison

    #PHYSICAL_ENTITY NAME external BC albedo 0.5

    MILONGA_SOLVER EPS_TYPE krylovschur

    # set the power setpoint equal to the volume of the core
    # (and set eSigmaF_2 = nuSigmaF_2 as above)
    #power = 1

    # finally ask milonga to solve the eigenvalue problem
    MILONGA_STEP

    # compute location of maximum thermal flux
    VAR phi_max x_max y_max
    #MESH_FIND_MAX FUNCTION phi2 MAX phi_max X_MAX x_max Y_MAX y_max

    # write a row of a gfm table
    PRINT "k:" %.5f keff

    # give some information in a markdown-formatted text file
    #MILONGA_DEBUG FILE_PATH replace_this.txt

    # gmsh & vtk postprocessing (in background)
    #MESH_POST FILE_PATH squares_post.msh phi1 phi2
    #MESH_POST FILE_PATH squares.vtk phi1 phi2

    # SHELL "gmsh squares.msh &"

    # and gnuplot with the power
    PRINT_FUNCTION FILE_PATH {dat_path} phi1 phi2


    # dump the matrices in sng format, convert them to png with
    # 
    # $ sng *.sng
    # MILONGA_DEBUG FILE_PATH squares MATRICES_SNG MATRICES_SNG_STRUCT

    # -----8<----- milonga's solution ends here -----8<-----
    """