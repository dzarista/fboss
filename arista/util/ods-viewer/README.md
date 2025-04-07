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

## Google Colaboratory Usage

Use the following instructions to run within a Chrome browser.

### Installing Google Colaboratory

1. Go to Google Drive
2. Press the `+ New` button
3. In the `More->` sub-menu, select `+ Connect more apps`
4. Search for `Colaboratory` and install it.
This will now appear in the `More->` submenu.

### First time Chrome MetaOdsViewer Usage

1. Go to Google Drive.
2. Press the `+ New` button and select `Google Colaboratory`
3. Upload `MetaOdsViewer.ipynb`
   This will be saved in a `Colab Notebooks` folder in Google Drive. The next
   time, you can just double-click `MetaOdsViewer.ipynb` in this folder.

### Running

To run, select `Run all` from the `Run` menu.

### Additional Chrome MetaOdsViewer Notes
Use the file-folder icon on the left to expose the file pane. This is used to
manage the files known to the Colaboratory workspace.

To upload a csv file, press the upload button and select a file from your laptop.
Then modify the `odsCsvFile` to the filename of the file uploaded.

In order to reference Google Drive files, click on the Google Drive icon
and give permission to access your Google Drive. The file path should start with
`drive/MyDrive`. For example:
`drive/MyDrive/Meta Escalations/ssw015-s002-f01-ncg3.csv`
No need to escape spaces.

Starting from the top logic pane, either press the play button or press Shift-return.
This will run the pane and then highlight the next one. Do this for each of them.
There are about 7. The last one generates the graph.
