BATTERY THERMAL MODELING | STAGE 01
Khani Solutions | Independent public engineering study

This release models a rectangular pouch-cell equivalent with one uniform
temperature. Its dimensions, density, heat capacity, heat source and ambient
loss coefficient are illustrative assumptions, not manufacturer measurements.
It is numerically verified against the analytical response and energy balance;
it is not experimentally validated and predicts no specific product performance.

Inputs: 36 x 78 x 4.45 mm cell; density 2400 kg/m3; cp 1000 J/(kg K);
effective combined surface loss 8 W/(m2 K); initial and ambient temperature 25 C;
prescribed heat generation 1 W for 600 s followed by 1200 s with zero generation.
Radiation is not added separately to the combined effective loss coefficient.
1 W denotes heat generation, not electrical charging power.

Equation: C*dT/dt = Q_in - G*(T-T_ambient)
C=rho*V*cp; G=h_effective*A; tau=C/G.
Run: python3 -m pip install -r source/requirements.txt
Then: python3 source/run_model.py
Python, NumPy, SciPy and Matplotlib are free/open-source dependencies.
The exact versions originally used are in results/summary.json.
Run outputs include CSV/JSON plus PNG/SVG figures under review/.

The editable cell CAD is in cad/. The 0D model does not require a spatial mesh;
there are no spatial VTK fields in this release. The website's separate full-phone
CAD viewer is geometry context for later stages, not the solved thermal domain.

Study: https://khanisolutions.com/AISolutions/battery-thermal.html
