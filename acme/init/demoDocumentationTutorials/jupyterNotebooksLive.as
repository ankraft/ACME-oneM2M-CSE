;;
;;	jupyterNotebooksLive.as
;;
;;	Open the Jupyter Notebooks application on the MyBinder
;;
;;	(c) 2023 by Andreas Kraft
;;	License: BSD 3-Clause License. See the LICENSE file for further details.
;;
;;	This script opens the Jupyter Notebooks live installation on MyBinder in the default browser.
;;

@name oneM2M Tutorial Notebooks (MyBinder)
@category oneM2M Resources and Tutorials
@tuiTool
@description oneM2M provides a series of introductional hands-on tutorials to various oneM2M concepts, resource types and requests.\nThe **Open...** button opens a web browser and launches the *MyBinder* web site.\n*Note: The MyBinder service is free, but it may take a while to start the Jupyter Notebooks application.*
@tuiExecuteButton Open Jupyter Notebooks in Browser

(open-web-browser "https://mybinder.org/v2/gh/oneM2M/onem2m-jupyter-notebooks/master?urlpath=lab/tree/__START__.ipynb")