## Repository Structure

```text
IND320vilde/
│
├── main.py
├── requirements.txt
├── log_and_ai_declaration.ipynb
├── links.txt
├── README.md
├── .gitignore
│
├── CA_notebooks/ 
│   ├── CA_1.ipynb
│   ├── CA_2.ipynb
│   ├── CA_3.ipynb
│   └── CA_4.ipynb
│ 
├── CA_pdf_files/
│   ├── CA_1.pdf
│   ├── CA_2.pdf
│   ├── CA_3.pdf
│   └── CA_4.pdf
│
├── data/
│   ├── nve/ 
│   │   └── Budområder/
│   │       ├── Budområder.dbf
│   │       ├── Budområder.prj
│   │       ├── Budområder.shp
│   │       └── Budområder.shx
│   │ 
│   │   └── NVE_region/
│   │       ├── NVE_region.dbf
│   │       ├── NVE_region.prj
│   │       ├── NVE_region.shp
│   │       └── NVE_region.shx
│   │    
│   └── open_meteo
│       ├── NO_1.parquet
│       ├── NO_2.parquet
│       ├── NO_3.parquet
│       ├── NO_4.parquet
│       └── NO_5.parquet
│
├── utils/
│   ├── utils.py
│   └── APIs/ 
│       ├── ENTSOE_API.py
│       ├── METEO_API.py
│       └── NVE_API.py
│
├── styling/
│   ├── colours.py
│   └── style_funcs.py
│
└── pages/
    ├── 0_home.py
    ├── 1_imported_data.py
    ├── 2_plot.py
    ├── 3_power_flows.py
    ├── 4_magasin_analysis.py
    └── 5_meteorological_analysis.py

```
