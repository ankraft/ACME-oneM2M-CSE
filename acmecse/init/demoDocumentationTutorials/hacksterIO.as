;;
;;	hacksterIO.as
;;
;;	Open the oneM2M hackster.io channel in the default browser.
;;
;;	(c) 2023 by Andreas Kraft
;;	License: BSD 3-Clause License. See the LICENSE file for further details.
;;
;;	This script opens the oneM2M hackster.io channel page in the default browser.
;;

@name oneM2M Projects @ hackster.io
@category oneM2M Resources and Tutorials
@tuiTool
@tuiSortOrder 610
@description hackster<void>.io, the community dedicated to learning hardware, offers a "oneM2M" channel for projects and tutorials. This channel hosts projects and tutorials related to the oneM2M standard, its implementations, and its usage. This also include tutorials and many projects from past oneM2M hackathons.\n\nThe **Open...** button opens a web browser and launches the "oneM2M @ hackster<void>.io" channel page.
@tuiExecuteButton Open "oneM2M @ hackster.io" Page in Browser

(open-web-browser "https://www.hackster.io/onem2m")