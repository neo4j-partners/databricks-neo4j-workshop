"""agent_modules — Python package for cluster scripts and MLflow-bundled modules.

All Python files live here. Scripts submitted via submit.sh (run_lab2_02.py,
run_lab3_03.py, test_hello.py) and modules bundled into the MLflow model
(future agent modules per MEMORY.md) coexist in this package.

Import strategy:
  - Scripts on the cluster use bare imports: from data_utils import ...
    (sys.path includes agent_modules/ because spark_python_task adds
    the script's parent directory)
  - MLflow-bundled modules use relative imports: from .data_utils import ...
    (agent_modules is a package on sys.path via code_paths)
"""
