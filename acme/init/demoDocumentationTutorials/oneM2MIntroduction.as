;;
;;	oneM2MIntroduction.as
;;
;;	Open the oneM2M Introduction page in the default browser.
;;
;;	(c) 2023 by Andreas Kraft
;;	License: BSD 3-Clause License. See the LICENSE file for further details.
;;
;;	This script opens the oneM2M introduction page in the default browser.
;;

@name oneM2M Home Page - Using oneM2M
@category oneM2M Resources and Tutorials
@tuiTool
@tuiSortOrder 20
@description This section of oneM2M's home page offers various introductions:\n- Benefits of oneM2M\n- Develop with oneM2M\n- Deploy wih oneM2M\n- List of deployments\nThe **Open...** button opens a web browser and launches the "Using oneM2M" page.
@tuiExecuteButton Open "Using oneM2M" Page in Browser

(open-web-browser "https://onem2m.org/using-onem2m/what-is-onem2m")