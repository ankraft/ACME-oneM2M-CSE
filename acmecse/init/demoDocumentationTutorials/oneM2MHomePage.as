;;
;;	oneM2MHomePage.as
;;
;;	Open the oneM2M home page in the default browser.
;;
;;	(c) 2023 by Andreas Kraft
;;	License: BSD 3-Clause License. See the LICENSE file for further details.
;;
;;	This script opens the oneM2M home page in the default browser.
;;

@name oneM2M Home Page
@category oneM2M Resources and Tutorials
@tuiTool
@tuiSortOrder 10
@description oneM2M's mission statement:\n>oneM2M's goal is to develop technical specifications for a common M2M service layer that can be readily embedded within various hardware and software, and relied upon to connect the myriad of devices in the field with M2M application servers worldwide.\nThe **Open...** button opens a web browser and launches the oneM2M home page.
@tuiExecuteButton Open oneM2M's Home Page in Browser

(open-web-browser "https://onem2m.org")