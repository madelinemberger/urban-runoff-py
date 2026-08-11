# Urban Runoff

This repository contains notes, code, inputs and QAQC records for the creation of the Urban Runoff driver layer.

**NOTE:** As of July 2025, all prep work for the urban layer is now done in Python. Offshore coastal modelling done here in R. See [`urban-runoff-py`](https://github.com/madelinemberger/urban-runoff-py) repository on GitHub for fully reproducible input prep and watershed area calculation.

- Model process and notes documented in `urban_runoff_model_FINAL.Rmd`. Within the code blocks, R scripts are called to execute specific steps in the model.
- `R` folder contains the standalone scripts executed in the markdown
- `QAQC` contains scripts used by team members to execute QAQC steps
- `figs` is a catchall for figures used in past meetings and presentations to team members. These are not official publication figs and may show intermediate or outdated products

Final outputs from this model are saved back to the Donovan Lab Dropbox.

Remaining steps:

- Link the python and R processes into one fully reproducible workflow.
