# Meta ODS Viewer

This directory contains a Jupyter Notebook that can be used to easily visualize
ODS data shared by Meta during escalations. The notebook is designed to be run
from your local machine. Please see the official Jupyter documentation for
specifics about how to interact with the notebook:
https://docs.jupyter.org/en/latest/install.html

## Dependencies

To run this notebook, you need to install jupyter notebook, pandas, matplotlib,
and plotly python libraries:
```
pip3 install notebook pandas matplotlib plotly
```

Note that you may need to update your PATH value to include Python binaries.
On my Macbook, this looked like:
```
export PATH=$PATH:/Users/adamc/Library/Python/3.9/bin
```

## Usage

1. Download the ODS CSV file you'd like to view to your local machine.
2. Run the notebook: `jupyter notebook MetaOdsViewer.ipynb`, which should open
   the notebook in your default web browser.
3. In the notebook, update the `odsCsvFile` in cell 3 to point to your local file.
4. Select "Run" -> "Run All Cells": this will run the code and generate an
   interactive time-series graph.

### Interacting with the Graph

The graph is generated using plotly. A couple of notes:
- You can add/omit sensors by clicking the names in the legend.
- You can zoom in on a region of the graph using the zoom button.
- You can download the graph to share.

## Example

The included `rsw021.p001.f01.eag6.csv` file is ODS data taken from a Rackhawk
switch at Meta. You can use this file as an example when exploring this
notebook.
