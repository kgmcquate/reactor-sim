from django.shortcuts import render
from .forms import AddForm
from django.http import HttpResponse
import json
from .milonga_solver import MilongaSolver
import datetime, os
from django_site.settings import STATIC_TEMP_ROOT, BASE_DIR
import logging

def get_init(request):
    # if this is a POST request we need to process the form data
    if request.method == 'POST':
        # create a form instance and populate it with data from the request:
        form = AddForm(request.POST)
        # check whether it's valid:
        if form.is_valid():
            # process the data in form.cleaned_data as required
            X = int(form.cleaned_data['x_size'])
            Y = int(form.cleaned_data['y_size'])
            if X > 25:
                X = 25
            elif X < 5:
                X = 5
            
            if Y > 25:
                Y = 25
            elif Y < 5:
                Y = 5
            
            return render(request, 'milonga_diffusion/grid.html', {'form': form, 'X': range(X), 'Y': range(Y), 'maxX': X, 'maxY': Y})
        # else:
        #     # warning = 'Dimensions must be between 5 and 25'
        #     return render(request, 'reactor_sim/grid.html', {'form': form, 'X': range(10), 'Y': range(10), 'maxX': 10, 'maxY': 10})

    # if a GET (or any other method) we'll create a blank form
    else:
        form = AddForm()
        return render(request, 'milonga_diffusion/grid.html', {'form': form, 'X': range(12),  'Y': range(12), 'maxX': 12, 'maxY': 12})
        

def solve(request):

    logging.info("here")
    milongaSolver = MilongaSolver(temp_root=STATIC_TEMP_ROOT, cells_string=request.POST.get("data"))
    logging.info("here2")
    milongaSolver.generate_mesh()
    logging.info("here3")
    milongaSolver.generate_mil()
    logging.info("here4")
    milongaSolver.generate_plot(gnuplot_palette_path=os.path.join(BASE_DIR, "milonga_diffusion", "gplot-palettes", "gnbu.pal"))
    logging.info("here5")
    # print(keff)
    keff = float(milongaSolver.keff)
    if keff == 0:
        msg = 'Can\'t Solve'
    elif keff < 0.99:
        msg = "Reactor is Subcritical: k = "+str(keff)
    elif keff > 1.01:
        msg = "Reactor is Supercritical: k = "+str(keff)
    elif (keff > 1.001) or (keff < 0.999):
        msg = "Reactor is Approximately Critical: k = "+str(keff)
    elif (keff > 1.0002) or (keff < 0.9998):
        msg = "Reactor is Nearly Critical: k = "+str(keff)
    else:
        msg = "Reactor is Critical: k = "+str(keff)

    return render(request, 
                "milonga_diffusion/plots.html",
                {
                    'fast_plot_path': "/".join(milongaSolver.fast_png_path.split("/")[-3:]), 
                    'thermal_plot_path': "/".join(milongaSolver.thermal_png_path.split("/")[-3:]), 
                    'k_msg': msg
                }
            )

