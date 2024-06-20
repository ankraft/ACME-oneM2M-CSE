;;
;;	StackOverflow.as
;;
;;	Open the oneM2M Stack Overflow tag in the default browser.
;;
;;	(c) 2023 by Andreas Kraft
;;	License: BSD 3-Clause License. See the LICENSE file for further details.
;;
;;	This script opens the oneM2M Stack Overflow in the default browser.
;;

@name oneM2M Q&A @ Stack Overflow
@category oneM2M Resources and Tutorials
@tuiTool
@tuiSortOrder 600
@description Stack Overflow, the question and answer site for programmers, offers a oneM2M tag for questions and answers. The tag `#onem2m` is used for questions related to the oneM2M standard, its implementations, and its usage.\n\nThe **Open...** button opens a web browser and launches the "oneM2M @ Stack Overflow" tag's page.
@tuiExecuteButton Open "oneM2M @ Stack Overflow" Page in Browser

(open-web-browser "https://stackoverflow.com/questions/tagged/onem2m")