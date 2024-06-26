;;
;;	oneM2MSpecifications.as
;;
;;	Open the oneM2M specification page in the default browser.
;;
;;	(c) 2023 by Andreas Kraft
;;	License: BSD 3-Clause License. See the LICENSE file for further details.
;;
;;	This script opens the oneM2M specification page in the default browser.
;;

@name oneM2M Specifications
@category oneM2M Resources and Tutorials
@tuiTool
@tuiSortOrder 15
@description The specifications section of oneM2M's home page offers the published documents and technical reports for Release 1 - 5.\n\nThe **Open...** button opens a web browser and launches the "Specifications" page.
@tuiExecuteButton Open "oneM2M Specifications" Page in Browser

(open-web-browser "https://onem2m.org/technical/published-specifications")