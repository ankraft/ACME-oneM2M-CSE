;;
;;	jupyterNotebooksWiki.as
;;
;;	Open the Jupyter Notebooks page on the oneM2M Wiki
;;
;;	(c) 2023 by Andreas Kraft
;;	License: BSD 3-Clause License. See the LICENSE file for further details.
;;
;;	This script opens the oneM2M's Jupyter Notebooks page in the default browser.
;;

@name oneM2M Tutorial Notebooks (Wiki)
@category oneM2M Resources and Tutorials
@tuiTool
@description oneM2M provides a series of introductional hands-on tutorials to various oneM2M concepts, resource types and requests.\nThe **Open...** button opens a web browser and launches the oneM2M Wiki page.
@tuiExecuteButton Open Wiki in Browser

(open-web-browser "https://wiki.onem2m.org/index.php?title=OneM2M_Tutorials_using_Jupyter_Notebooks")