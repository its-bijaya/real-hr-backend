# Changelog

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)

---
## 3.0.44.0+240322 Changelog of March 22, 2024
## Added
- Added a feature to cancel approved expense requests.Cancellation requests follow the same approval workflow as the original expense request, ensuring that the request is routed to the appropriate approvers for confirmation.
- Added a feature to view edited package history.
- Added a feature  for supervisors to view monthly insight reports of all level  subordinates.
- Added environment variable “DELETE_ALLOWED_TIMESHEET_ENTRY_METHODS” to specify allowed methods for deleting timesheet entries.
- Added a feature to allow users to revise denied or canceled expense management forms without re-entering information.
- Added Timesheet Entries and Attendance Sync columns in the Excel report and data table of Employees Attendance Insights report.
- Added Attendance sync filter in Employee Attendance Insights report
-
## Changes
- Modified  Payroll collection to enable HR admins or Users with appropriate permissions to delete confirmed and approved payroll entries.Also,implemented a feature to keep history of modified payroll entries

## Fixes
- Resolved  an issue where a validation error was thrown upon selecting an onsite room for meetings, seminars, or training sessions.Previously, all available rooms from other organizations were displayed.However, upon selecting a room, a validation error occurred, preventing successful selection.
- Resolved an issue where attempting to delete a branch  triggered an alert message, but performing any action in the pop-up resulted in the page becoming unresponsive.
- Resolved 500 errors in On-Boarding Employee process due to rebate heading.
- Resolved payroll calculation inaccuracy when an employee joins in the middle of the month after a holiday, incorrectly counting the holiday as a working day.
- Resolved 404 error,when HR admins attempt to search users in the payroll collection.
- Resolved necessary adjustments to ensure that unselecting the country name clears the province field as expected.
- Resolved issue where re-adding the same employee to the collection after editing or deletion resulted in inaccurate calculations of the total amount.

## 3.0.43.0+240307 Changelog of March 07, 2024
## Added
- Added a feature  in the attendance settings which allows HR admin to remove assigned web attendance entries in bulk.
- Added a new feature to export branch details.
- Added a feature so that Hr admins can assign survey forms using filters such as Gender, Branch, Employment Type, Employment Level, Job Title, Division, and Current Duty Station.
- Added a feature to add attendance entries after assigning training to particular users

## Changes
- Modified (replaced) the "Email" column with a new "Province" column in the Organization Branch table.

## Fixes
- Fixed issue in Yearly leave report and Individual leave report to ensure that the data displayed in the datatable and the Excel download match accurately.
- Fixed  issue with payroll package search functionality.
- Implemented a fix for earned leave encashment to be based on the remaining balance.
- Fixed the issue causing a 500 error when HR admins attempts to bulk assign packages without selecting a user-defined start date.
- Fixed heading bar in all attendance report

## 3.0.42.0+240223 Changelog of February 23, 2024
## Added
- Added title and date filter in payroll collection
- Added a validation to check if  user's last working date falls between the cutoff date and the last day of the month during payroll generation
- Added branch,employment type and email column in survey and report form
- Added a validation to prevent HR admins from adding or deleting a payroll heading to a package that is already assigned to one or more employees, and payroll has been generated.
- Added a feature in  attendance settings so that Hr admin can assign web attendance for multiple employees simultaneously.
- Added a filter  to facilitate the filtering of employees by employment type.

## Changes
- Modified general and time off leave type .This changes now  enables HR to configure leave calculations after the user's probation end date.
- When attempting to access an account with an inactive status, the user status icon is now automatically disabled.

## Fixes
- Fixed issues related to backdated leave calculations.
- Fixed  issue where the cutoff date was not being applied correctly when adding employees from  payroll collection.
- Fixed issue where filtering employees by employment type in payroll addons was not functioning.
- Fixed issue where rating answers were not being displayed in survey and forms responses
- Fixed issue where the Consolidate Overtime Report failed to display unclaimed data when a supervisor directly claimed unclaimed overtime.
- Fixed issue where the "On Travel" count was not being removed from the Notice Board and Calendar (Calendar and Events) interfaces upon approval of a Travel delete request.

## 3.0.41.0+240209 Changelog of February 09, 2024
## Added
- Added a heading-wise search filter in the Employee’s Insight Report, allowing users to efficiently search for specific information under different headings.
- Added title,fiscal year and status filter in payroll addon.
- Added filter such as  branch,employment level and division  in roster management
- Added a feature to select multiple employees in Employees Attendance Insights, Monthly Insights and Package Wise Salary Report
- Added a feature allowing supervisors to view all-level subordinates in the timesheet calendar
- Added a functionality to maintain an export log in the organization  export log report feature.(Monthly insight, duty station,employee’s insight,rebate)
- Added a validation message while generating payroll if employees last working date lies between cutoff date and end date of payroll.

## Changes
## Fixes
- Fixed   issue where the confirmed date was displayed as "N/A" in the Payroll Addon.
- Fixed issue where insurance attachments requested by the user were not displaying on the change request section.
- Performed UI fixes in the Performance Appraisal Form to enhance usability and visual appeal.
- Fixed issue where the password reset button was not visible after sending a password reset link.
- Fixed issue of contract end date showing the same every day.
- Fixed date validation in expense management request.

## 3.0.40.0+240116 Changelog of January 26, 2024
## Added
- Added a feature to download payroll yearly report in excel
- Added an employee-level hierarchical order column  in payroll collection. Also, included those columns in excel download report.
- Added a switch to enable users to view duty stations for all fiscal years.
- Added search filters for all headings in Monthly Insight.
- Added a script/code to download profile pictures of users of Laxmi Bank. (One Time Link)
- Added a feature to export month wise payroll difference report
- Added a feature to include addons detail in payroll yearly report

## Changes
- Modified the yearly payslip report to include information for all employees, including those who have resigned or been terminated.
- Modified payroll addons to include past employee

## Fixes
- Fixed 403 error , when clicking on the action icon to view an employee's payslip
- Fixed 500 error in Attendance today’s log
- Fixed formatting issues in the "Employees Attendance Insights" and "Monthly Insights" headings.
- Fixed issues in rebate export
- Fixed default end time for expense form submission to 5:00 PM.

## 3.0.39.0+240112 Changelog of January 12, 2024
## Added
- Added supervisor and reviewer columns in  key achievement and rating report of Performance Appraisal module . Also, included those columns in the excel report.
- Added a feature to download the assigned package list.
- Added a feature to automatically cancel or adjust compensatory leave and overtime when the originally designated off-day/holiday  is changed to a workday due to a shift change.
- Added a message “Allowed extensions are: jpg,jpeg,png “ in profile picture upload pop up .
- Added a feature to export duty stations .
- Added a feature to bulk import the list of trainees in add training modules.
- Added SSF,PF,Disbursement and tax report in payroll generated status too.
- Added a feature to view month wise payroll differences

## Changes

## Fixes
- Fixed validation error message  while uploading profile picture
- Optimized Payroll generation process to enhance performance, reduce processing time, and ensure smooth execution.
- Optimized Payroll validation process.
- Fixed issue where generating payroll addons reports for one collection was impacting other payroll addons collections..

## 3.0.38.0+231229 Changelog of December 29, 2023
## Added
- Added the "Pray Sign" icon to be displayed alongside people's names in Condolence Posts on the Noticeboard
- Added a feature that allows HR admin to export office equipment data to Excel sheets
- Added a feature for HR Admins to navigate to the next tab by clicking on the action icon of individual objectives.
- Added Gender, Branch , Employment type , Employment Level , Division , Current Station filter in Survey and form report
- Added a feature to export duty station (From Common Settings)
- Added a feature to add the employee in previously generated payroll collection
- Added a feature to import rebate in bulk

## Changes
- Modified Expense Management:
      a) All signatures and remarks made by signatories are now visible in downloaded expense download report
      b) Updated default submission time to 9:00 AM as the start time and 5:00 PM as the end time.
      c)Replicated default values from the per diem section to the lodging and attendance sections
- Removed CAPTCHA for Internal Vacancies
- Implemented an enhancement allowing users with appropriate permissions to click the Extra App icon when data is available.

## Fixes
- Fixed an issue where 500 error was thrown when clicking on the sorting icon for candidate names on both the preliminary shortlist and final shortlist pages.
- Fixed  an issue where payroll for new employees joining in the middle of the month was not generating correctly.
- Fixed 404 error in key Achievements and Rating report

## 3.0.37.0+231215 Changelog of December 15, 2023
## Added
- Added a username column in the downloaded report of Package Wise Salary Report.
- Added a feature which allows users to view the total overtime limit while requesting Pre-requested overtime.
- Added a hyperlink in the Goals and Objectives score  in the dignity report  to   redirect users to the specific organizational goal page.
- Added different sections in the training module such as program cost, TADA , Accommodation & trainers fee. Also,added a permission  to edit Budget allocation and participant list even after the training is completed
- Added a new module “Monthly Insight” in payroll module
- Added a feature allowing users to receive email notifications when their leave is deducted due to penalties

## Changes
- Modified Anniversary template for laxmi bank (Added branch in template).
- Modified the MCA Dignity Appraisal Report to hide individual organizational goals. Now, only the average score of organizational goals will be visible to HR, Supervisors, and Users.
- Modified the collapsed credit hour leave in employee balance history from minutes to HH:MM:SS format

## Fixes
- Fixed test case in payroll addons.
- Fixed the issue where editing a pinned post in the noticeboard would unintentionally unpin it.
- Fixed lost hour calculation in the case of payroll generation using cut-off date.
- Fixed an issues in add training module :
       a)  Fixed an issue where the end date of the training could be set before the start date during the update process.
       b)   Addressed an issue  where the total budget limit could be updated to a value lower than the total sum of allocated budgets for that particular training type.
       c)  Fixed an issue where the validation message in the allocated budget calculation was mismatched.
- Fixed an issue  where HR admins encountered a validation error while approving pre-approved overtime for the new fiscal month.
- Fixed  an issue  where changing the rebate amount in the Addons section while HR is requesting a rebate on behalf of employees did not correctly impact the tax and net payable calculations.
- Fixed an issue while calculating the tax amount in payroll addons after assigning the CIT deduction the tax must be deducted and tax is calculated only on taxable amount.
- Fixed an issue  to correctly handle package assignment during bulk import, ensuring that each package is uniquely identified.

## 3.0.36.0+231201 Changelog of December 1, 2023
## Added
- Added an additional field  in the report of the Performance Appraisal (Key Achievements and rating) ,which allows Employees and HR to view their complete form from the report
- Added a new column “score” and “weightage” in peer to peer report(Dignity Appraisal)
- Added a feature in the payroll generation section to download the non-eligible employee list
- Added a break in/out  filter in Employees Attendance Insights
- Added a feature to generate bank letter in disbursement report
- Added a bank filter in disbursement report
- Added a customized attendance report (Employees Attendance Insights) feature in both HR admins and Supervisors section
- Added a feature which enables user to view the total overtime limit while requesting the pre-requested overtime
- Added a username column and username filter in Package wise salary report
- Added  evaluator page  permission on permission setting page
- Added INR currency in expense management

## Changes
- Modified expense management module :
   a) Excluded Empty "Travel Request Module" List
   b) Modified the download feature to include a comprehensive view of all missing portions below the signature section
   c) Downloaded files will now be named with the TAARF number
- Modified  the Encashed Balance to be rounded up to the nearest  integer value(For Laxmi Bank)
- Modified the remarks field to be mandatory in reviewer form (Key Achievement and rating appraisal).

## Fixes
- Resolved an issue where the amount was incorrectly displayed as zero when the Payroll approval level is from a different organization in payroll.
- Resolved an issue where Supervisors were unable to view unclaimed overtime approved/confirmed by HR for their subordinates using the checkbox.
- Optimized permission page
- Resolved ordering and mapping issues in the Performance Appraisal Form
- Resolved path issue in three sixty performance appraisal
- Resolved  the issue related to extended to the next day shifts with confirmed overtime causing restrictions on applying leave for the previous and  following day.
- Fixed test case in payroll addons

## 3.0.35.0+231110 Changelog of November 10, 2023
## Added
- Added a new headings i.e. Average Collaboration Score, Average Score, Average Execution Score and Average Objective score in dignity report
- Added a new settings  “Condolence Post” in noticeboard post
- Added a new supervisor search filter in assign supervisor section
- Added a new feature  in supervisor section to search employee by their  username
- Added a new chart (Internal Reviewer PA status and External Reviewer PA status) in dignity overview page
- Added a new username column in SSF report,Disbursement Sheet,PF report and Tax report
- Added a feature to filter rebate by different rebate headings and download all the employee rebate (12 months +all addons) in an excel report
- Added a branch column in bulk employment experience
- Added a filter in user feedback  section of dignity module
- Registered weekly attendance in dj-admin.

## Changes
- Modified Anniversary post template for laxmi Bank
- Changed the location,vacancy and deadline icon in career page

## Fixes
- Addressed the issue related to extended to the next day shifts with confirmed overtime causing restrictions on applying leave for the following day.
- Fixed issue where shift could not be changed after the cutoff date is applied.
- Identified and resolved the issue causing data to be cleared in the hiring information page during the update process.
- Resolved issue when generating a timesheet by clicking on a past employee, the name of the employee disappears, and the dropdown list shows the current employee list.

## 3.0.34.0+231030 Changelog of October 30, 2023
## Added
- Added a download button in dignity module
- Added additional column with heading username,employment level,branch and job title in excel report of survey form
- Added a feature where Hr admin can view, edit and update peer evaluation score report
- Added a feature to download Performance Appraisal Report(For Laxmi Bank)
- Added a username column in PA status download report (Key Performance and Achievements)
- Added a feature where Hr will be able to view,edit and update the peer to peer form by clicking the score in PA status
- Added a search filter in user-side Performance Appraisal Form
- Integrated a drop-down menu within the Dignity Module to provide access to Milestones and a quick option for creating new Milestones.
- Added a feature to be able to search the employee by username in dignity module

## Changes
- Implemented changes to provide HR with the capability to complete pending checklists and undo completed checklists for individual objectives and milestones.

## Fixes
- Fixed 500 error at employment review module
- Resolved the issue where the job title of an employee was not updated when HR performed bulk imports to change a user's employment experience
- Fixed the issue in the search filter, enabling HR Admins to search for employees by their complete name in payroll addons .
- Fixed issue where the count of user score was not visible in PA status of Appraisal (Dignity PA)
- Fixed 404 error while assigning objective by Hr (Dignity Module)
- Fixed the issue where the payroll processing state remained stuck when the total working days were divided, and the variable was linked with the annual function.
- Fixed the issue where canceling the alert dialogue box in the PA user form incorrectly closed the entire form.
- Fixed 500 error in filter by KPI job title
- Fixed 500 error while generating the timesheet
- Fixed redirection issue in Performance Appraisal notification
- Fixed 404 error in goal period and goal filter
- Fixed issue of showing 0 and 1 instead of true and false in Performance Appraisal Excel report

## 3.0.33.0+231006 Changelog of October 06, 2023
## Added
- Added a feature to create an evaluate in peer to peer evaluators (MCA Dignity)
- Added a feature to view dignity dashboard (MCA Dignity)
- Added a feature which enables user to view their supervisor and reviewer in performance appraisal (Laxmi PA)
- Added a feature to delete the attachment in milestone and individual objective
- Added a feature where Hr can be able to assign  Individual Objectives to employees (MCA)
- Added a feature where Hr can add evaluator on behalf of the employee (MCA Dignity)
- Added a column in supervisor data table which enables supervisor to view score provided by their subordinates (Laxmi PA)
- Added module in Django admin of performance appraisal
- Added an alert dialogue box before user submits the self performance appraisal form (Laxmi PA)
- Added a feature which enables supervisor to generate time sheet of their subordinates

## Changes
- Modified the user-side performance appraisal slot.The slot is now auto-expanded without requiring users to click on the action expand button (Laxmi PA)
- User must not be  able to view the change in evaluator list done by HR (MCA)
- The supervisor evaluation will only be visible when supervisor sends the form (Laxmi PA)

## Fixes
- Fixed White space issue in Performance Appraisal  excel download report
- Fixed issue where users were unable to send attendance adjustment  entries when another users payroll is in generated state
- Fixed gender and work experience filter in applicant list of recruitment and selection module
- Fixed Validation issues in expense management
- Fixed different dignity bug issues
- Fixed a bug in the key Achievement and Rating appraisal type where, when HR unassigns the previous appraiser and assigns a new one, the form was not being received by the newly assigned appraise

## 3.0.32.0+230925 Changelog of September 25, 2023
## Added
- Added a new appraisal type “Key Achievement and Rating” in performance appraisal (For laxmi Bank)
- A new feature has been added that allows PA forms to be sent just to individuals whose KPI is confirmed. (For Laxmi Bank )
- Added a new feature to resend PA form when reviewer disagrees with the score (For Laxmi Bank)
- Added a new feature to filter KPI by job title besides their own.
- Added a new appraisal type “Dignity Appraisal “ in dignity module (For MCA)
- Added a new feature to provide score once “Individual Objectives“ has been completed
- Added a new evaluator list in dignity module where employee can choose their evaluator for performance appraisal
- Added a new feature “Coaching Tool” in Dignity Module
- Added a new feature to sort payroll collection report by Employment level hierarchy and branch code
- Added a new feature to download payroll collection report in excel
- Added a new module named dignity with setting to create goal period,goal and milestone
- Added a new feature to assign duty station through excel import
- Added a refresh button to download the Excel report in the general information report for payroll.

## Changes
- Changed banner and logo in career page (For SHTC)

## Fixes
- Fix issue of signature been hidden in other approval level in expense management request
- Enhanced the performance of the payroll generation process to provide a smoother and more responsive experience.
- Optimized Payroll addons import to enhance performance, reduce processing time, and ensure smooth execution.
- Optimized Bulk package processing
- Fixed issue of Bulk Payroll package being stuck in processing state
- Fixed issue of tax report heading with amount zero not displayed in Excel report, although the setting is set to display heading with 0.
- Fixed the issue of the page being scrolled to the bottom of the page when the supervisor or HR visits the employee profile by clicking on the employee's name.
- Fixed 500 error when clicked on the initialize application process in applicant list
- Fixed issue of showing only 10 list in expense management request table
- Fixed issue of user not being able to send attendance adjustment when other employee’s payroll is in generated state
- White space fix in PA word download report

## 3.0.31.0+230825 Changelog of August 25, 2023
## Added
- Added a new module named “dignity” with sub modules  “Individual objectives to me” and “Individual objectives by me”
- Added a feature that sends notifications when a supervisor assigns specific objectives to an employee, as well as a notification when employees or the supervisor comments on the objectives.
- Added a feature to download assigned KPI
- Added a feature to search username/name  alphabetically
- Added a filter in replace supervisor to select past employees

## Changes
- Changed Dignity notification language.

## Fixes
- Fixed the issue  where the payroll title was not  displayed at payroll approval side
- The issue with the side navigation bar has been resolved.
- Fixed 500 error when importing payroll in bulk for employees with usernames in numbers rather than alphabets.
- Fixed issue of payroll generation of eligible employees
- Fixed text area issues in performance appraisal. Also,included a feedback section in downloaded report of performance appraisal
- Enhanced the performance of the user auto-complete list feature to provide a smoother and more responsive experience.

## [3.0.30.0+230811] Changelog of August 11, 2023
## Added
- Added a feature to generate the payroll by using division filter 

## Changes
- Amount of claimed overtime will be included in the generated month rather than the confirmed month(For khajurico only)
- Removed “Happy Work Anniversary” text from anniversary post (For Laxmi Bank only)
- Data reconciliation report will be displayed in supervisor section too (For Khajurico only )

## Fixes 
- Fixed issue of throwing validation message “you can't perform this action” when normal supervisor try to approve overtime of their subordinates
- Fixed issues of bulk employment experience 
- Fixed issue of blocking payroll generation  of this month when overtime of next month is in approved or requested stage 
- Fixed a 500 error when downloading payroll payslips in Excel format
- Fixed checkbox issues in individual attendance settings
- Resolved the roster search filter bug and data table showing all subordinates when clicked on immediate subordinates only toggle

## [3.0.29.0+230728] Changelog of July 28, 2023
## Added
- Added a feature in Attendance device to export assigned employee
- Added a toggle in roster to switch to nepali date and vice-versa
- Added a text field in generate payroll page to write title of payroll
- Added a patch to make leave accrual date to shrawan 1 [SHTC , PATCH]
- Added a dropdown button in “My team” of noticeboard
- Added a feature to assign supervisor in bulk

## Changes
- Employee directory and noticeboard is hidden for employees[Khajurico only]
- When ignore second is true in environment,second is excluded in irregularity report while counting lost hour
- When rebate is in requested state payroll cannot be generated
- Work anniversary template is changed [laxmi bank]

## Fixes
- Fixed login issues when performing any action using web attendance from login page
- Fixed redirection issues when hr clicks on action icon of task
- Fixed validation error in event when user click in date picker
- Fixed redirection issue when hr view bulk package list
- Fixed permission issue while assigning package to user when payroll module is enabled for hr only
- Fixed issue of timesheet generation even after last working date
- Fixed issue of amount of absent and unpaid leave not deducted in payroll when cut off date is not selected
- Fixed the issue of signatures not being downloaded in the PDF of the advance expense request sheet
- Fixed issue of applicant not being forwarded to next stage when category is selected in preliminary shortlist
- Fixed issue with month names appearing as invalid in the roster calendar
- Fixed UI alignment issues in calendar
- Fixed issue of showing small box in extra app icon when there is no data or count
- Reduced response time of noticeboard stats api
- Fixed filter and count issues in event
- Fixed 403 error when supervisor generates leave report of subordinates

## [3.0.28.0+230714] Changelog of July 14, 2023
## Added
- Added a feature to generate overtime if the employees' shift is assigned via roster.
- Added a username/employee name filter in assign duty station
- Added a new PA setting with three modes of appraisal :self appraisal,supervisor appraiser & reviewer
- Added a patch to download link of picture and signature in excel [Patch]
- Added a progress bar while uploading addons data via excel

## Changes
- System icon changed in different module
- Roster heading was fixed
- Notification count must be determined by metric prefixes such as 1.1k ,1.2M

## Fixes
- Fixed validation error in career page.
- Fixed the auto selection of questions set in performance appraisal.
- Fixed 500 error when Hr tries to claim unclaimed overtime of an employee whose supervisor is not assigned.
- Fixed issue of signature hidden in Advance Expense Request
- Fixed issue of 500 error in Recruitment and selection, when no stages is selected while creating vacancy
- Fixed issue of showing bulk assign package page in normal/Hr who don't have permission to access the page
- Fixed issue of clear button not working in multiple feature inside common organization settings
- Fixed issue of approved rebate amount not been updated while importing addon details from excel


## [3.0.27.0+230630] Changelog of June 30, 2023
## Added

- Added lost hour in both payslip(template-1 and 2)
- Added a feature  to generate payroll by selecting branch
- Added a feature to select multiple employees in attendance roster
- Added a feature to sent notification to employees when KSAO is assigned to them
- Added a username column, a search field to search with username, and a username to be displayed in downloaded reports in payroll addons.
- Added variable in environment to control whether to select or enter  days in expense management
- Added a feature to assign Kpi using employment level and employment type



## Changes

- Past payroll package cannot be deleted without deleting the latest one
- The division and employment fields in Create KPI are made non-mandatory
- In recruitment and selection if reference is not mandatory then reference field should not be visible in career page


## Fixes

- Fixed the issue of throwing a 404 error when username or leave type is not selected .
- Fixed issue of showing selected KSAO in dropdown list
- Fixed issue of not being able to perform cross-organization appraisal
- Fixed issue of not being able to submit more than one education information in career page
- Fixed issue of displaying incorrect holiday count, working days count and total lost hour count in yearly payslip report

## [3.0.26.0+230616]2023-06-16
## Added
- Added feature to control the sending of email notification of payroll module
- Added username field in summarized  yearly leave report and downloadable excel of that report
- Added feature to acknowledge user’s KPI by supervisors
- Added feature for user to review and update the KPI and success criteria
- Added feature to add legal and bank information and contact details in bulk through excel
- Added variable in environment file to control whether to show days in drop down or enter days manually in per diem form of travel in advance expense request
- Added sample download and feature to import through excel in import overtime claim, leave import and leave balance import

## Changes
- “Deduct tax now” toggle is now hidden in addons creating form
- Total lost hour, which is in format HH:MM:SS is now converted in number(excluding seconds) in payslip
- If supervisor is not assigned for any user, it now displays N/A in user’s profile instead of “RealHRSoft”

## Fixes
- Fix issue of heading not showing when hr search an employee in monthly attendance report
- Fixed issue of showing failed excel of previous payroll import even next import is successful
- Fixed issue of showing bio id and assigned device of other  users too in one user’s bio device setting when I deactivate the user’s account
- Fixed issue of showing title in user’s view which should’ve been in hr’s view in monthly attendance
- Fixed issue of lost hour not being calculated properly after attendance adjustment in irregularities report
- Fixed issue of showing 403 error when supervisor clicks on cancel leave request
- Fixed issue of showing 500 error when I search text in email template of common setting

## [3.0.25.0+230602]2023-06-02
## Added
- Added feature to add username and marital status via excel in user import
- Added feature to send email whenever action is taken on generated payroll
- Added feature to send email based on action taken in rebate and advance salary
- Added feature to assign kpi in bulk
- Added search field by username/empname in roster

## Changes
- In per diem section of expense request, number of days should be in dropdown with option 1 and 0.75
- Naming format of package generated by bulk package is changed to empname_username_assignfrom date.

## Fixes
- Fixed issue of heading source data being reversed when choosing hourly records in dj-admin
- Fixed issue of leave import getting stuck in processing state
- Fixed issue of user being able to request multiple leave on same range
- Fixed issue of dropdown field not being cleared in add shift
- Fixed issue of color code not changing accordingly after adjusting attendance
- Fixed issue of actor not being able to claim total overtime after editing
- Fixed issue of text overlapping in assign task form
- Fixed issue of amount mapping in settle expense
- Fixed issue while importing attendance of employee with shift extend to next day
- Fixed issue of showing 500 error while generating payroll if overtime is pending

## [3.0.24.0+230519]2023-05-19
## Added
- Added variable in environment file which controls whether or not to include the amount of claimed overtime in the same month in payroll rather than overtime confirmed month
- Added username column in downloadable report and data table throughout the system
- Added bank details field in the generate report of HRIS
- Added a category to display username in generate report of HRIS
- Added a search field with username in generate payroll page


## Changes
- HR admin and supervisor can now change shift for individual days and past days as well
- When payroll is generated upto future date, then generation date is now considered as cutoff date such that user can request for leave
- HR admin and supervisor now can edit unclaimed overtime generated by system
- Hyphen(-) is now accepted in the username
- Addons details is now included in yearly payslip


## Fixes
- Fixed 404 error while assigning payroll package from user profile summary
- Fixed issue of approved field not updated in supervisor’s view when supervisor claims the unclaimed overtime
- Fixed issue of employee not being able to request travel attendance if supervisor is not assigned
- Fixed 500 error when clicked on the rooster management tab of recruitment
- Fixed issue of displaying all projects when assigning task to user  instead of only displaying projects associated to that user
- Fixed logo of “RealHRSoft” in the email
- Fixed issue of rate of per diem and lodging being exchanged in expense management
- Fixed issue of total extra hour not calculated in the attendance overview
- Fixed issue of table not rendering properly in the weekly attendance report email

## [3.0.23.0+230505]2023-05-05
## Added
- Added feature to send travel attendance request from expense management request form
- Added KPI feature
- Added feature to map template of weekly attendance report to send via email
- Added feature to claim the unclaimed overtime of subordinate by supervisor
- Added search field on the basis on username in multiple modules and reports

## Changes
- Employment types tabs are removed from current employee list

## Fixes
- Fixed issue of displaying past employee while generating payroll without selecting employee
- Fixed issue of file remaining in the file selecting field even after we post in noticeboard
- Fixed issue of labeling users as past employee while hovering over names in modules redirected from extra app
- Fixed issue of text are not closing when we make it fullscreen in event of type meeting
- Fixed issue of showing employees of different organization while assigning worklog

## [3.0.22.0+230424]2023-04-24
## Added
- Added a feature to acknowledge the assigned KPI to me by the user (is not merged)
- Added a feature to assign KPI to subordinates by HR admin and supervisor (is not merged)
- Added feature to update employment experience through excel upload
- Added filter in payroll collection so that HR can download report according to applied filter
- Added a variable “total working days” in payroll heading
- Added a variable “total lost hours” in payroll heading
- Added a variable “total holiday count” in payroll heading

## Changes
- As HR Admin, now I can edit the payroll rejected by approver

## Fixes
- Fixed issue of showing employee’s designation instead of their name in the name field

## [3.0.21.0+230407]2023-04-07
## Added
- Added feature to deduct allowances form payroll if employee is on remote work
- Added KPI collection feature in the performance appraisal module
- Added patch to activate users in bulk
- Added feature to skip the recruitment and selection stages.

## Changes
- Changed birthday card design.

## Fixes
- Fixed console error while assigning interviewer in preliminary screening interview
- Fixed console error while approving/denying rebate request from view details
- Fixed redirection issue in different sections of overview of dashboard, HRIS, attendance and task
- Fixed issue of displaying “employee from different organization” in post of the same organization
- Fixed internal server issue when user go to the following sections in the fresh database: payslip and tax, claim overtime, attendance overview and overtime claim history report
- [console] Fixed issue of moderator being able to decline the already approved trial  request

## [3.0.20.0+230324]2023-03-24
## Added
- Added feature to assign bio-id for multiple users at same time via excel import
- Added feature to add weightage for interviewer so that final score will be based on weightage

## Changes
- When user resignation is approved then contract expiration notification and email should not be displayed of those employee
- Email template is changed/ redesigned throughout the system

## Fixes
- [Console]Fixed issue of “sign in” button not being clickable
- Fixed issue of  showing start time as invalid in enrolled user section of assessment when user take assessment after it is expired
- Fixed issue of showing past employee when hovering over the user’s supervisor name
- Fixed issue of displaying page not found error when clicking employees from different organization
- Fixed issue of not displaying core task when enabling “associate with task” and disabling it again
- Fixed issue of not displaying image in training even after uploading image
- [Console] Fixed issue of displaying password in plaintext  when we sign in by pressing enter

## [3.0.19.0+230310]2023-03-10
## Added
- Added heading in clickable sections of the dashboard
- Added switch to control whether or not to show vacancy number in recruitment
- Added remote work feature to track remote work of an employee
- Added feature to send email for weekly attendance report of an user
- Added penalty report which displays the occurrence and absent count from penalty setting

## Changes
- Total worked hour is now being displayed in HH:MM:SS format in attendance irregularities report
- If web attendance is not enabled for user, then log button shouldn’t be visible to that user
- [Console] “Verify” button removed from “RealHRSoft setup complete” and “Declined” email

## Fixes
- Fixed issue of not displaying selected category in generate hris report
- Fixed issue of displaying error message when updating previously assigned payroll package
- Fixed issue of “Assign Leave” function not working from profile summary
- Fixed issue of amount of extra heading being zero when hr edit payroll in any heading
- Fixed issue of sorting not working in profile completeness report
- Fixed issue of displaying the user name in credit hour details remark instead of the person who approve or deny it
- [console] Fixed pagination error in trial request page
- [Console] Fixed issue of displaying approve and decline button to previously approved or denied trial request
- Fixed issue of new question being created when editing one
- [Console] Fixed issue of requesters being able to access their previous verification email even when their previous request is denied.

## [3.0.18.0+230224]2023-02-24
## Added
- Missing module of leave added in django admin
- Missing module of payroll added in django admin
- Added feature to display the penalty absent count in the attendance irregularities reports

## Changes
- HR Admin can now delete/cancel approved leave of payroll generated time-frame
- HR Admin can now assign leave balance to user in decimal value as well
- Archive feature removed from rebate for both HR and normal user

## Fixes
- Fixed issue of displaying data of pending and closed status in pending section of task
- Fixed issue of HR admin being able to generate payroll of next month despite of being payroll of previous month in forwarded stage
- Fixed issue of pagination not working in worklog overview page
- Fixed multiple issue of attendance module in django admin
- Fixed internal server issue when generating letter template with hints “payroll” for offboarding process

## [3.0.17.0+230213]2023-02-13
## Added
- Added payroll addons feature to calculate incentive
- Missing module of performance appraisal added in django admin
- Missing module of recruitment added in django admin
- Missing module of HRIS added in django admin
-  New status column is added in credit hour requests page which indicated whether approved credit hour has been added to leave balance or not
- Added patch to import employment experience in bulk
- Added feature to see addons amount in rebate detail
- Added feature to add employee via excel upload in empty addons list

## Fixes
- Fixed issue of religion and ethnicity disappearing when user uploads profile and cover image
- Fixed issue of checked employee being unchecked after we change page in leave assign page
- Fixed issue of user being able to see assessment answer through api
- Fixed issue of HR admin not being able to delete approved attendance entries
- Fixed issue of user not being able to see the data of “on travel” and attendance card in dashboard(as  HR)
- Fixed issue of canceled and declined credit hour counted as pending while requesting another credit hour

## [3.0.16.0+230127]2023-01-27
## Added
- Added question clone feature in questionnaire
- Added show remarks button for failed incentive excel update
- Added missing model of attendance in dj-admin

## Changes
- Character limit increased in questionnaire
- Changes in add employee section in payroll addons

## Fixes
- Fixed issue of displaying error when there is space after email and when email is repeated while uploading payroll data via excel
- Fixed issue of pagination not working properly in profile completeness report
- Fixed issue of showing profile completeness score 0% for all employee in profile completeness report
- Fixed issue of HR admin not being notified after generating profile completeness and Dynamic HRIS report
- Fixed page not found issue when user select past employee in assign task page
- Fixed issue of labeling full day credit hour leave as absent in payslip
- Fixed issue of labeling first/second half covering credit hour leave as absent in payslip
- Fixed issue of close button not working on remarks history of employees change type
- Fixed page not found issue when supervisor of one organization clicks on the profile of his subordinates of different organization

## [3.0.15.0+230113]2023-01-13
## Added
- Added patch to generate penalty from certain days for certain organizations only
- Added advance penalty column to be displayed in individual attendance setting

## Changes
- Cancel button replaced with approve in leave cancel request from user side

## Fixes
- Fixed issue of displaying year of service in negative for employees whose join date is in the future
- Fixed issue of user not being able to request leave from calendar
- Fixed issue of displaying leave of all status in the requested tab from HR and supervisor side
- Fixed issue of not displaying error message when remarks field(mandatory) is left blank while     regenerating timesheet
- Fixed issue of HR admin being able to select any cutoff date while generating payroll
- Fixed issue of profile change and leave request being redirected to another status from what status we clicked from central dashboard
- Fixed count issue when HR clicks the attendance and travel attendance pending count in the dashboard
- Fixed issue of package more than 2000 not being displayed in package assign section

## [3.0.14.0+221230]2022-12-30
## Added
- Added refresh button in individual monthly leave report for report generation
- Added filter in cancel leave request module on hr side
- Added attendance penalty feature

## Changes
- As an hr overall remarks is now not a mandatory field for preliminary shortlist in recruitment

## Fixes
- Fixed timesheet report generated issue for employee whose join date is in future
- Fixed permission issue in task module where user can view data whose access was only to hr
- Fixed incorrect amount issue in excel downloaded tax report from hr and user side
- Fixed comment notification issue in birthday and anniversary post when user replies to comment
- Fixed reload issue in events when an employee is removed by hr
- Fixed validation issue in  experience end date in pre-employment when a new employee is added in the organization
- Fixed 404 issue when user clicks the notification after generating report of unit of work done
- Fixed sorting issue on end date in project section of task
- Fixed 404 issue while generating missing timesheet in the case where hr is not the employee of that organization
- Fixed irrelevant pop up message issue while enabling and disabling the events
- Fixed gaping issue when hr adds rule without expanding the leave type
- Fixed search issue when hr tries to filter the document name in organization document
- Fixed attendance and leave disappearance issue in dashboard in mobile view
- Fixed issue in travel attendance when hr and user was not able to request travel attendance on the same date again once the previous approved request  is deleted
- Fixed cutoff date mandatory issue when hr selects the date and cancels it later 
- Fixed issue of count being clickable even if there are no employees and vice versa in attendance overview and dashboard
- Fixed issue of displaying unspecified error  message while creating payroll heading.
- Fixed multiple issues in the central dashboard: counting issue, number being clickable issue
- Fixed issue of admin not being able to create leave rule without enabling the non mandatory toggle
- Fixed internal server issue when hr sort contract expire date in past employee list

## [3.0.13.0+221219]2022-12-19
## Added
- Added missing models in django admin.
- Added feature to remove assigned employee from training module.

## Changes
- Redirection of all pending leave requests, adjustment entries ,web attendance in all tab sections while generating payroll.
- Hr and User should not be able to request negative value in yearly rebate
- Payroll calculation optimization

## Fixes
- Fixed comment display issue in task detail page from supervisor side.
- Removed cross icon from mandatory field while creating payroll headings.
- Fixed  contract expired date displaying issue  in past employees list.
- Fixed issue of displaying same time in breakin-breakout entries of employees when updated from hr side.
- Fixed UI issue when hr adds training without uploading any image.
- Fixed count issue in all pending web attendance of employee while generating payroll.
- Fixed issue in leave when hr applies leave on behalf of user when there is option to select similar types of leave if user has it.
- Fixed issue in compile server when user can’t change password with the provided link when forgot password is clicked.
- Fixed issue in django admin while importing compensatory rule leave settings from one organization to another. 
- Fixed issue in bulk package when past employee is assigned package when they had current user experience on that day.
- Fixed issue where supervisor was not able to take action when advance salary request notification was clicked.
- Fixed pagination issue in monthly attendance report and sorting issue in task report. Sorting option is removed from user leave history and contract status in my team reports.
- Capitalized the first letter in rebate settings.

##[3.0.12.2+221205]2022-12-05
## Added
- Patch to request leave after payroll confirmation.

## Changes
- Pagination icon changed in aggregate report of recruitment and selection.
- Error message displayed when start and end time is not selected in credit hour leave.

## Fixes
- Fixed year of service counting issue of employee.
- Fixed blank space issue in the events list.
- Fixed name reappearing issue when hr opens the create new form while creating a new payroll package.
- Fixed error message disappearance issue in offline leave.
- Fixed status not changing issue in bulk package assign.
- Fixed name reappearing issue when hr opens create new form while assigning package in bulk.
- Fixed payroll generation issue when there is pending leave request and adjustment after cutoff date.
- Fixed multiple credit hour request issue when there is limitation in leave type.
- Fixed issue of displaying pending requests of all employees when generating payroll of one employee.
- Fixed issue of not generating full salary even after selecting cutoff date.
- Fixed issue of supervisor not being able to take action after clicking the notification regarding advance salary.

##[3.0.11.0+221121]2022-11-21
## Added
- Added feature to make Travel report mandatory or not from expense management settings
- Added feature to display and download latitude and longitude in break in/out report for supervisor section
- Added feature to display latitude and longitude in break in/out report for normal user
- Added feature to make reference and CV field mandatory or not in recruitment
- Added feature of sending emails by system for credit hour delete module
- Added feature to restrict updating employment experience, rebate, package change, leave request, attendance adjustment request, amount change in package etc when payroll is in generating stage
- Patch to change initial balance on renewal rule of sick leave for SHTC and laxmi bank leave cancellation.
- Registered missing models in django admin

## Changes
- Changed the text excel package name to Name
- Maintained UI consistency module wise in supervisor view
- Changed max_user_count to max_active_user_count field in the .env file
- Maintained UI consistency module wise in admin view

## Fixes
- Fixed issue of absent details in attendance overview and report section as an hr and as supervisor
- Fixed counting issue in the field heading and sorting in every stage of recruitment and selection
- Fixed issue in rebate form when the rebate requested by hr is approved first time and again archived the same rebate request second time
- Fixed issue in heading amount when user requests rebate is updated by hr after generating payroll
- Fixed Icon pagination issue in recruitment and selection
- Fixed 500 error issue in payslip when payslip setting is not set
- Fixed issue in career page when education information not required is set but marked as mandatory
- Fixed mandatory issue in preliminary and final shortlist,email sending issue in rejected candidate,applicant name repeating and missing issue.
- Fixed multiple request issue when general information is updated by the user
- Fixed 403 permission denied issue when payroll module is enabled for hr
- Fixed 404 issue when hr admin assigned package to past employee.

##[3.0.10.0+221104]2022-11-04
## Added
- Added feature to upload file in noticeboard
- Added feature to replace supervisors in bulk
- Added feature to request prior approval in days and hours
- Added feature to download failed list when updating generated payroll and also added validation for Excel file
- Added feature to revoke assigned package in bulk package assign
- Added feature to add taxable amount in annual taxable salary so that tax is deducted from starting month but amount is paid to user at any month
- Added feature to display latitude and longitude in break in/out report from hr side

## Changes
- Cache timeout is now defined from env
- Changed display text in noticeboard and revamp noticeboard text editor
- Leave coefficient are also displayed when generating missing timesheet
- Removed previous static rebate type data from system
- UI consistency in Noticeboard, Task, Calendar and Events, Task, Worklog, Attendance, Leave, Payroll in user side

## Fixes
- Fixed value error in payroll when hr admin update package from update user package heading
- HR Admin can now view the schedule post request immediately
- Fixed search issue in payroll collection
- Fixed payroll generation issue for employee whose joining date is last of fiscal month
- Fixed pagination issues in recruitment and selection
- Fixed legal information redirection issue instead of showing validation message.
- Fixed payroll upload status and payroll bulk assign status in compiled server
- Fixed payroll heading update issue
- Fixed permission denied issue in preliminary shortlist, salary declaration when no objections are initialized for applicants and preliminary shortlist data were displayed in final shortlist.


##[3.0.9.0+220930]2022-09-30

## Added
- Added feature to approve/Decline rebate request from view detail page .
- Added feature to view payroll import completed in percentage/count and estimated time to know the status of it .
- Added feature to configure multiple rules for generating compensatory leave,so that employees compensatory leaves are generated on that basis.
- Added feature cutoff date in payroll generation and ignore attendance and leave request after cutoff date.
- Added patch to send candidate from final shortlist to no objection for category A and B for vacancy assistant to DED -Management [MCA]
- Added feature to view payroll generation completed percentage/count and estimated time to know the status of it .
- Added feature to display all previous data and updated data in change request .
- Added feature to display all the agendas discussion,decision,task details and other information details in pdf format in events details page of event type meeting.
- Added feature to create and assign payroll packages in bulk
- Added feature to view bulk package assign completed percentage/count and estimated time to know the status of it.


## Fixes
- Fixed issue when user/hr tries to download excel file after viewing payslip.
- Fixed issue in added description in Questionnaire in Survey and forms when viewing from normal user section.
- Fixed issue in events when user clicks first heading for editing then other headings are redirected to edit page without clicking edit option .
- Fixed issue when user adds agenda description in discussed section and saves but the data is removed and replaced in to be discussed section .
- Fixed issue when first rebate requested by user is approved and second request is denied ,then approved amount was not shown in rebate request form .
- Fixed issue when a user is assigned a different package in the same month .
 - Fixed issue when admin tries to delete heading and package name which has dependencies
- Fixed issue where hr should be able to apply  offline leave after the payroll has generated .

## [3.0.8.0+220916] 2022-09-16 From this point move completely to django3

## Added
- Added filter in employee directory API for chat
- Added feature to display the heading with their values   not equal to zero
- When system (server)restarts,circus should run automatically
- Added text editor feature in noticeboard post
- Added feature to upload amount in generated payroll using username


## Fixes
- Fixed calculation issue when user is assigned same package multiple times in same month
- Fixed issue when user rebate request is archived and the requested amount was still shown in the rebate request form after the payroll is generated .
- Fixed issue when hr requests rebate on behalf of employee and when the request is archived,the rebate amount was shown in the rebate request form .
- Fixed issue in tax report in projected amount of full fiscal year and yearly report  for off boarded employee
- Fixed issue  when fiscal year,summarized yearly leave report , leave types and employee was selected (500 error)
- Fixed issue when unpaid leave is counted as paid in payroll for offday when offday/holiday inclusive is enabled

## [2.9.28+220905] 2022-09-05

## Added
- Added feature select by employee as approval level in Expense Management module
- Added feature to include off-boarded employee name in task title when assigning task from employee separation
- Added feature to display tax report in HR section once payroll is generated
- Added feature to download tax report in Excel format

## Fixes
- Fixed issue in payroll while uploading data through Excel
- Fixed issue in rebate when HR request rebate on behalf of an employee and archived the request but is still shown in rebate request form
- Fixed 500 error when fiscal year and month is not selected
- Fixed issue in attendance where leave coefficient was incorrect after changing shift of employee
- Fixed issue in leave coefficient when working shift  of employee is changed

## [2.9.27+220819] 2022-08-19

## Added

- Added employment level as variable in payroll
- Added patch for changing leave rule details
- Added username field in the downloaded report of daily and individual monthly attendance report in attendance and in individual leave balance and yearly leave report in leave
- Added feature of rebate planning
- Added feature to download payslip in Excel format
- Added feature payslip setting in payroll so that the selected heading is displayed in monthly and yearly payslip

## Fixes

- Fixed loading  issue in overtime claim button when user requests without adding remarks
- Fixed issue in form setting when id was shown in place of question set name


## Changes
- In rebate request form ,when payroll is generated of certain month ,those months data is now displayed in readonly mode
- When importing payroll data ,it is done by adding either username or email in Excel sheet

## [2.9.26+220729] 2022-07-29

## Added

- Added Rebate list in payroll setting in payroll
- Added Separate level of approval in expense management for settlement
- Added settings to control advance amount request in  percentage
- Added multiple prior approval settings with multiple number of request for (days), request prior in days, hours and minutes
- Added username column in downloaded general information report in payroll
- Added patch when leave balance is added multiple times while new fiscal year arrives (For Laxmi bank)

## Changes

- Removed company logo from all excel downloaded report
- In carry forward leave report and yearly leave report ,leave fiscal year should be compared with leave fiscal year and global year with global fiscal year
- Changes in multiple prior approval was verified in previous data
- Removed update feature for holiday

## Fixes

- Fixed console errors in multiple prior approval in leave
- Fixed issue when employee can apply is disabled, admin as a user was able to apply for leave

## [2.9.25+220718] 2022-07-18

## Added

- Added  currency options in advance expense and settlement form
- Added patch to export email list from job vacancy (MCA)

## Fixes

- Fixed 500 issue in performance appraisal
- Fixed save issue in attendance penalty setting
- Fixed redirection issue in daily attendance when clicked in punch_in punch_out
- Fixed issue in profile completeness scoring
- Fixed pagination issue in  yearly,carry forward,summarized leave report
- Fixed 404 issue in remark history in leave
- Fixed 404 issue in django-admin when clicked in quick action
- Fixed issue regarding payslip comment in payroll
- Fixed 500 issue in demo when applied with education degree as diploma
- Fixed issue in payroll where level of approval selected can approve and deny the payslip
- Extra count issue fixed in recruitment

## [2.9.24+220704] 2022-07-04

## Added

- Added user signature in HRIS generate report
- Added feature to display payslip for normal user when payroll is in generated state
- Added feature to log attendance from login page

## Changes

- Replaced like button by birthday cake emoticon for birthday post
- Replaced like button by clap emoticon for work anniversary post
- Payroll Optimization

## Fixes

- Fixed attendance import issue
- Fixed redirection issue in daily attendance report
- Fixed travel attendance request pop up issue
- Fixed permission issue in payroll.
- Fixed pagination issue in leave request page
- Fixed notification issue in HR admin section
- Fixed color displayed issue when user punch-in in grace time.

## [2.9.23+220610] 2022-06-10

## Added

- Added feature to display payslip before confirming payroll.
- Added feature to generate past employee details in HRIS generate report

## Changes

- Removed auto generated text for birthday, anniversary and welcome card in noticeboard.
- Employee List displayed in popup when clicking on Absent Today, On Leave and On Travel are displayed in ascending order in noticeboard page.

## Fixes

- Fixed recruitment and selection bugs
- Fixed late email send issue in travel attendance.
- Fixed division dropdown issue in employment experience.


## [2.9.22+220527] 2022-05-27

## Added

- Added feature to display experience change type like job title, employment type and branch in employment overview page.
- Added feature to download leave request history in Excel format.
- Added additional information of new joined employee in system generated welcome card
- Added in progress tab in all stages of recruitment and selection

## Changes

- Change employee name position in system generated anniversary card.
- Change logo and bot name from “RealHR Soft” to “Laxmi Bank” for client laxmi bank.

## Fixes

- Fixed user address delete issue
- Fixed leave request filter issue in supervisor section
- Fixed leave filter issue in individual monthly leave report
- Removed popup message displayed in step up/down recommendation settings in performance appraisal
- Fixed report download issue in interview section of recruitment.

## [2.9.21+220512] 2022-05-12

#### Added

- Added conflict of interest while scoring the candidate in recruitment
- Added feature to filter user details and heading list in payroll collection report.

#### Change

- Added field Province/state, District and Postal code in user profile address

#### Fixes

- Fixed sorting issue in performance appraisal report
- Fixed default email sender selector issue
- Fixed vue autocomplete bug
- Fixed credit hour generation issue

## [2.9.20+220502] 2022-05-02

#### Added
- Added Laxmi bank logo in login page for server laxmi bank.
- Created patch for leave balance mismatch in laxmi bank after leave balance import and leave request import

#### Changed
- Changed theme color to orange for laxmi bank

#### Fixes
- Fixed age report filter issue in leave
- Fixed offline leave request when ens date is smaller than start date
- Fixed password reset issues

## [2.9.19+220415] 2022-04-15

#### Added

- In recruitment stages when user click on candidate profile, candidate details should be displayed.
- Added issue place and issue date of citizenship and passport number in LegalInfo
- Search by employee code filter in employee list page

#### Changed

- Payroll calculation optimization.

#### Fixes

- Attendance report download issue in User and Supervisor section.
- Hidden character issues in input fields.
- 404 error when tried to delete training type.
- Non-downloadable ethics view issue.
- Filter by branch in assign supervisor page.

## [2.9.18+220401] 2022-04-01

#### Added
- Travel attendance on behalf of employees by HR Admin
- Travel attendance on behalf of subordinates by Supervisor
- Added country, province and geographical region fields for branch
- Branch import
- Employment level filter in individual attendance page
- Candidate name filter applicant list page
- Import leave balance from django admin
- Branch and Division filter in supervisor assign page
- Added relations and dependent information in user’s contact information
- Insurance amount, policy amount field in user’s insurance information

#### Changed
- Nepali calendar dependency to year 2099

#### Fixes
- Bypass validation pop up when applying offline leave by HR and Supervisor
- Leave assign bottom sheet filters
- Email settings bugs

## [2.9.17+220318] 2022-03-18

#### Added
- Request overtime on behalf of user by HR Admin/Supervisor

#### Changed
- Holiday delete confirmation message
- Payroll generation optimization

#### Fixes
- 500 error when generating offer letter
- 500 error when requesting advance expense and expense settlement
- When candidate fills and submits the salary declaration form, no response is displayed.
- Reset SMTP server
- Travel attendance delete request notification date range
- Permission issue while creating vacancy.
- Fix unit test: test_overtime_claim_bulk_action.py
- 500 error when adding employee in review

## [2.9.16+220304] 2022-03-04

#### Changed
- Performance Appraisal form seen by users only after HR Admin sends the forms
- Bar chart step calculations
- Email settings page redesign
- Setup runtime variables for frontend build

#### Fixes
- Event invitation accept/reject issue from email details page
- HTML tags are displayed in survey and forms descriptions.
- Permission error while creating vacancy
- Overtime forward by second level supervisor

## [2.9.15+220218] 2022-02-18

#### Added

- Added email settings for overtime
- Update shift applicable from date

#### Changed

- Performance Appraisal module changed to save score
- Unique Username and Email combination across all organization

#### Fixes

- Adding other information in meeting
- Salary declaration file attachment url
- Individual attendance report generation notification
- Round off score of recruitment and selection
- Rejected email template while creating vacancy
- Number of deleted days in travel attendance delete request
- Email setting unit test
- Resolve Invalid HTTP_HOST header
- Salary payment chart in payroll overview page

## [2.9.14+220204] 2022-02-04

#### Added

-   Added email settings for credit hour
-   Added email settings for travel attendance
-   Unit test for Preliminary Shortlist, Final Shortlist and Job apply step of Recruitment

#### Changed

-   Attendance adjustment request view details page
-   Display the attendance entries deleted by HR in Deleted tab of attendance adjustment page

#### Fixes

-   Payroll edit issue
-   403 while selecting payroll package in on-boarding process
-   Attendance adjustment date issue in adjustment request bottom sheet
-   Scoring issue in preliminary shortlisting step
-   Individual monthly leave report issue

#### Portal

-   Create trial server from the portal by the potential clients

## [2.9.13+220121] Changelog of January 21, 2022

#### Added

-   Added Email settings for attendance adjustment
-   Added Feature to create internal vacancy

#### Changed

-   Registered all submodules of recruitment and selection in django admin

#### Fixes

-   Performance appraisal bugs
-   Aggregate report of recruitment and selection
-   Overtime bulk claim request
-   Amount formatting in type two payslip
-   Attendance adjustment cancel bugs
-   Advance salary request in compiled server

#### Portal

-   Show demo message in trial server
-   Implementation of background task for multiple databases
-   Token validation across multiple tenants

## [2.9.12+220107] - 2022-01-07

### Added

-   Documentation of Expense Management module

### Changed

-   Leave balance chip color removed
-   Exclude verifying overtime request when generating payroll

### Fixed

-   Performance Appraisal bugs
-   Issue in attendance overview page
-   Issue in attendance penalty report page
-   Unit test fixed
-   Swagger issues

## [2.9.11+211224] - 2021-12-24

#### Added

-   Added leave balance history for supervisor
-   Documentation of task work log module
-   Email settings for Expense Management

#### Fixed

-   Advance Request cancel notification
-   Individual Leave Balance Report Issue
-   Leave Request for attendance calendar
-   403 error in performance appraisal
-   Minor fixes

## [2.9.10+211210] - 2021-12-10

#### Added

-   Added save feature in Pre-screening stage of recruitment

#### Changed

-   Performance Appraisal file download to doc file form PDF file
-   Can create multiple holiday with different branch for same day

#### Fixed

-   Payroll heading sorting issue

## [2.9.9+211126] - 2021-11-26

#### Added

-   Select multiple leave type while applying leave when selected leave type does not have enough leave balance

#### Changed

-   Migrated demo.realhrsoft.com to demo.realhrsoft.com.np
-   Create Frontend docker on every push to master branch

#### Fixed

-   Employment Review bug
-   Attendance adjustment bug
-   Questionnaire bug
-   Recruitment bug
-   Payroll bugs

### Portal

-   Added feature to send email to client when portal admin takes action on the server request.
-   Host portal in portal.realhrsoft.com

## [2.9.8+211112] - 2021-11-12

#### Added

-   Added sections for performance appraisal question set
-   Performance appraisal reports for normal user

#### Changed

-   Removed remarks field while selecting appraisers for peer to peer appraisal
-   Download performance appraisal report in excel format
-   Hide pricing from realhrsoft website

#### Fixed

-   403 error when Payroll module is disabled for normal users
-   404 issue when clicking "Apply Now" in careers page
-   Bugs in survey and forms
-   Leave comparison between division report issue
-   Worklog bug
-   Leave Coefficient "First Half" is displayed when full leave is applied for shift having extend to next day.

### Portal

-   Maintain activity log of server

## [2.9.7+211029] - 2021-10-29

#### Added

-   Added “Branch” column in attendance irregularities report
-   Added feature to automatically shown punch in and punch out time in attendance adjustment
-   Added answer type multiple choice grid and checkbox grid in questionnaire
-   Added option to hide Expected Salary in job apply page

#### Changed

-   Updated travel attendance api from organization specific to common

#### Fixed

-   Fixed Round off issues in payroll and leave
-   Fixed payroll edit issue for settings type extra heading
-   Fixed loading issue when clicking extra heading field in generate payroll page
-   Fixed Survey & Forms response lost issue when updating question sets

### Portal

-   Redesign server details page
-   Added version control push update

## [2.9.6+211008] - 2021-10-08

#### Added

-   Added ‘Requested Advance’ and ‘Balance’ details in settlement form
-   Added Dropdown answer type in survey & form
-   Added feature to display summary report for normal user for selected question in survey & forms

#### Changed

-   Support ‘0’ zero in rate per day in expense management

#### Fixed

-   Fixed Credit Hour not generated issue for leave approved date
-   Fixed individual attendance report download issue
-   Fixed 500 error when onboarding employees in newly created organization
-   Fixed ‘Order with particular package already exists’ issue while updating package heading in bulk.
-   Fixed 403 permission issue while creating vacancy

### Portal

-   Added database backup feature

## [2.9.5+210928] - 2021-09-28

#### Added

-   Added offday column in Attendance and Leave report
-   Added patch for updating holiday
-   Added feature to update package in bulk

#### Changed

-   Removed mandatory field “Start Time” and “End Time” in worklog create/edit form.

#### Fixed

-   Fixed yearly heading proportionate calculation issue
-   Fixed second half leave display issue when work shift of user is changed from past date with extend to next day check
-   Fixed fail payroll test
-   Fixed update package in bulk update issue
-   Fixed 403 issues when punch in/out
-   Fixed performance appraisal bugs

### Portal

-   Added employee and company limit settings
-   Added feature to block/unblock user
-   Added feature to update user profile by admin and user

## [2.9.4+210910] - 2021-09-10

#### Added

-   Added feature to generate payroll by excluding employees having pending requests and merge error messages in a single page.
-   Added feature to display employee list on clicking remaining request count when generating payroll
-   Added feature to set default calendar in filter
-   Added notification to employee when his/her employment review is completed

#### Changed

-   Removed import/export feature for confirmed payroll
-   Changed Individual Daily Attendance download to background processing

#### Fixed

-   Fixed permission issue in payroll

### Portal

-   Fixed portal bugs
-   Fixed payroll package auto assign issue in employment review

## [2.9.3+210827] - 2021-08-27

#### Added

-   Added feature to custom fiscal year
-   Added feature to link shift count with payroll
-   Added feature to enable/disable modules/sub-modules

#### Changed

-   Revamp penalty summary report

#### Fixed

-   Fixed RealHRSoft blog bugs
-   Fixed present employee count issue in supervisor section
-   Fixed two leave master activate at once issues
-   Fixed penalty settings update issues
-   Fixed expired master settings leave display in user section issues
-   Fixed Gender change issue from HR section

## [2.9.2+210813] - 2021-08-13

#### Added

Added answer type Date, Time and File Upload in questionnaire
Added summary report and question wise report in Form module
Added heading select feature in payroll collection tax report
Added functional plugin for rebate
Added feature to apply leave for extend to next day scenario
Added profile completeness report
Added worked day column in payroll collection report

#### Changed

Revamp email notification settings page

#### Fixed

Fixed backdated calculation issue when changing package and amount in package
Fixed PA bugs
Fixed Responsiveness bugs
Fixed Advance salary approval level bugs
Fixed permission issue on payroll when disable payroll for normal user
Fixed payroll generation issue in compiled code
Fixed Timesheet report bugs
Fixed leave balance issue in offboarding steps
Fixed working day issue in payroll collection report

## [2.9.1 +210730] - 2021-07-30

#### Added

-   Added number of days in leave request history.
-   Added features to assign shifts in past.

#### Changed

-   Change message displayed in tax report when settings are not defined.
-   Revamp form page as suggested in demo

#### Fixed

-   Fixed Form Bugs
-   Fixed copy paste feature in payroll rule and condition
-   Fixed resign employee last working day login issue
-   Fixed page response bugs
-   Fixed Performance Appraisal bugs
-   Fixed payroll advance salary approval issue
-   Fixed manual attendance issue for employee without shift
-   Fixed payroll permission bugs

## [2.9.0+210715] - 2021-07-15

#### Added

-   Added new feature Form (Survey)
-   Added penalty details to payroll payslip
-   Added paylog report and is also linked with payroll.
-   Added meeting room image as training and event background picture.

#### Changed

-   Revamp Worklog feature
-   Revamp equipment view details page

#### Fixed

-   Fixed package update issue

## [2.8.9+210630] - 2021-06-30

### Added

-   Added feature to request rebate by user and respond to the request by HR Admin.
-   Added email settings for Training, Resignation
-   Register performance appraisal in dj-admin

#### Changed

-   Removed employee from absent list until shift not started and if applied for credit hour leave.
-   UI/UX refactor
-   Verify and remove unused component found in frontend section
-   Separate notification settings for HR and supervisor added for web attendance
-   Punch in/ punch out time displayed in calendar if employee punch in/out in holidays
-   Remove TDS type from payroll

#### Fixed

-   Fixed user profile bugs
-   Fixed Leave balance renew issue
-   Fixed backend test failure and errors
-   Fixed events bugs
-   Fixed performance appraisal bugs
-   Fixed 500 error on employment separation steps
-   Fixed leave clone issue
-   Fixed payroll extra addition edit issue

## [2.8.8+210616] - 2021-06-16

### Added

-   Added option to request multiple credit hours by HR admin on behalf of employees.
-   Added feature to remove off-boarded employees from the permission group.
-   Added email settings for assessment, contract status, event and holiday
-   Added organization-name and organization-logo in downloaded payslip

### Changed

-   Changed default settings "All" for Marital status and enabled "Visible By default".
-   Changed default settings 'Editable' to be enabled by default in payroll headings.
-   Changed view details page of employment review.
-   Changed amount in payslip and tax-reports to be right aligned
-   Redesign attendance entry form
-   Edit pre overtime request is not visible when editable is disabled from settings
-   Redesign RealHRSoft website

### Fixed

-   Fixed proportionate leave balance on updating employment contract
-   Fixed credit hour bugs
-   Fixed attendance adjustment issue
-   Fixed overtime expire issue
-   Fixed punch in/out not found sentry issue
-   Fixed multiple validation message while applying job
-   Fixed 500 error when same user is in multiple approval levels

## [2.8.7+210602] - 2021-06-02

### Added

-   Added background process timeout message
-   Added Feature to clone payroll heading from one organization to other organization
-   Added payroll details in employee profile
-   Added feature to request credit hour in range
-   Added settings to generate more overtime than requested in pre overtime settings
-   Added Year of service in employee profile

### Changed

-   Change events details in noticeboard events and holiday section
-   Redesign Profile summary page

### Fixed

-   Fixed proportionate leave balance updated on updating employee contract
-   Fixed 500 error displayed while approving resignation from supervisor
-   Fixed all employee displayed issue while assigning bio id from employee profile
-   Fixed onboarding/offboarding bugs
-   Fixed employees displayed in the past and current employee list when the employee contract expired.
-   Fixed payroll bugs
-   Fixed overtime calibration multiple notification
-   Other major and minor bug fixes

## [2.8.6+210519] - 2021-05-19

### Added

-   Generating letters from the system.
-   Unit of work done report download.
-   Task assign setting (setting to enable/disable if employee can assign to higher employment level ?)
-   Setting to deduct unpaid leave immediately before/next days in case the employee applies for leave before or after offday and holiday.
-   Leave encashment report while offboarding employees and process the encashed amount in payroll.
-   Penalty report to process lost hours in leave.
-   Import/Export leave master setting between organizations.
-   Tax calculations of a backdated package to be done in the same month as the amount is processed in payroll.
-   Define benefits as taxable and deduct tax for those benefits.
-   Create a duty station category and assign them to employees.

### Changed

-   Changed naming of Operation to Operation/Project and Code to Code/Task in Unit Of Work Done.
-   Separated permission for payroll headings and packages.
-   Changed setting to calculate penalty for lost hours.
-   Assign training to the employees based on different HRIS aspects.
-   Update the payroll heading amount in bulk by import.
-   Expenses can be classified as taxable and non-taxable.
-   Leave accrual policy setting.
-   Export consolidated overtime report.

### Fixed

-   Contract Renew bugs.
-   Other minor bugs.

## [2.8.3+210423] - 2021-04-23

### Added

-   Merged Performance Appraisal Feature into master.

## [2.8.3+210421] - 2021-04-21

### Added

-   Added feature to generate backdated calculation
-   Added column “Total” in Yearly payslip
-   Added sum of each headings in downloads of Payroll General Information report and also added personal details in reports.
-   Added notification for supervisor when HR apply leave on behalf of employee.
-   Added individual leave encashment balance report
-   Added feature to cancel approved leave by HR admin

### Changed

-   Replace view details page of employee onboarding reports
-   Replace view details page of employee offboarding reports
-   Variable component such as Hourly headings are not projected for calculating AGS
-   Skipped certain leave validation When HR Admin apply offline leave.

### Fixed

-   Fixed multiple timesheet issues
-   Fixed on-boarding/off-boarding bugs

## [2.8.1 +210324] - 2021-03-24

### Added

-   TimeSheet Entry can now be deleted and remark category can be changed.
-   "Personal Break" is now added in TimeSheetEntry remark category.

### Changed

-   Mandatory field “Number” and “Number Type” for children allowance in contact details is removed.

### Fixed

-   Fixed tax deduction issues for extra headings
-   Fixed advance salary surplus issues
-   Fixed credit hour issues

## [2.8.0 +210310] - 2021-03-10

### Added

-   Roster attendance shift.
-   Delete option in attendance calendar to delete entries.
-   Overtime Slots settings.
-   Default variables for Children allowance payroll calculation.

### Changes

-   Redirection button to Employment review from Contract status report page.

### Fixes

-   Recruitment process questions not being populated.
-   MAC FE issues.
-   Payroll PF report generation issue.
-   Travel attendance request issue while requesting for multiple days.
-   Uniform Print functionality.
-   Leave balance not visible in summarized yearly leave report.
-   Minor bug fixes.

## [2.7.11 +210224] - 2021-02-24

### Added

-   Pre-Shortlisting report download
-   Assign default leave balance while assigning leave
-   Reject candidate from preliminary shortlist
-   Shift without timings can be created

### Changed

-   Email templates are not mandatory while creating vacancy

### Fixed

-   Assign supervisor bug fix

## [2.7.10b+210223] - 2021-02-23

### HotFixes

-   Fix assessment hotfix.

## [2.7.10a+210219] - 2021-02-19

### HotFixes

-   Squashed migrations for all apps.

## [2.7.10 +210210] - 2021-02-10

### Added

-   Profile Completeness Summary section added in user profile page.
-   HR can now cancel approved attendance adjustment.
-   New permission available for HR Admin event page.
-   Assessment expiration time for normal user

### Changed

-   Validation for employment experience update has been altered.

### Fixed

-   Leave module bug fixes
-   Attendance adjustment issue fixes
-   Recruitment bug fixes
-   Minor bug fixes

## [2.7.9+210129] - 2021-01-29

### Added

-   Credit hour request option added in HR section
-   HR can cancel approved attendance adjustment
-   When requesting travel attendance on offday, user can now select for specific start and end time
-   Added employee code auto generate feature

### Changed

-   Expense Management: oldest settlement request must be resolved first

### Fixed

-   Expense Management bugs
-   Travel Attendance bugs
-   Minor bug fixes
-   PA bug fixes

## [2.7.7+201218] - 2020-12-18

### Added

-   Added feature to deduct amount for type daily if employee is on leave
-   Added feature to earn leave balance monthly and weekly
-   Added “Division” filter in punctuality report

### Fixed

-   Fixed user experience update issue
-   Fixed 500 error while canceling leave requests by employees who do not have
    supervisor.
-   Fixed 404 error while viewing private events by HR
-   Minor bug fixes

## [2.7.6+201127] - 2020-11-27

### Added

-   Added option to generate letter template from HRIS setting
-   Added statistics bar in generate payroll section

### Changed

-   In daily allowance, for half leave request half amount should be paid
-   Django Admin customization
-   Optimize payroll package assign and package edit

### Fixes

-   Fixed PDF report download issues
-   Leave bug fixes
-   Recruitment bug fixes
-   Payroll bug fixes
-   Minor bug fixes

## [2.7.5+201106] - 2020-11-06

##Added

-   Tax deduction in bonus amount of a month
-   View details page of yearly payslip
-   Column “Branch” added on report and download of payroll collection
-   Notification for background processing report

##Changed

-   Summed up of multiple credit hours leave for a single day
-   Field name changes in off-boarding
-   Removal of Resign Employee from current employee list page

##Fixed

-   Multiple insurance details in user profile
-   Payroll, Attendance, Leave Bugs

## [2.7.3+201016] - 2020-10-16

### Added

-   Added “Day” in attendance report
-   Added Filter by Leave Type in Individual leave balance report
-   Added punch in/punch out category column and filter in daily attendance report
-   Added new template of payslip in payroll

### Fixed

-   Fixed Timesheet report generation issues
-   Fixed Attendance Adjustment count issues in Attendance overview page
-   Fixed Permission issues
-   Fixed minor issues

## [2.7.1] - 2020-08-28

### Added

-   SMTP Server setting added.
-   Expense Management
-   Advance amount editable by approver
-   Multiple approval
-   Signature of each approval level in expense view details
-   "All" option for supervisor as approver
-   Expense Request Details PDF Download
-   Organization Wrapper Implementation on Downloaded Excel file
-   Sync method added in Attendance Device Setting
-   Added CV Download
    ##Changed
-   Leave Cancel Request to supervisor
-   Insurance Documentation View

##Fixed

-   Attendance Report bug
-   ID download bugs
-   Leave Report Bugs
-   Off-boarding ,last working date issues
-   Noticeboard auto-generated post actor name fix
-   Minor bug Fixes

## [2.7.0] - 2020-08-14

#### Added

-   Added read-only permission in all module
-   Added Settings and report part for lost hour penalty deduction
-   Added location field in the travel request
-   Added web attendance approval mechanism with settings
-   Added notification and notification settings for web attendance
-   Added common dashboard report page
-   Added signature in downloaded payroll - Signature, name and job title are
    displayed in same rows should be in the different rows
-   Added stats of pending web attendance while generating payroll
-   Added missing variables like name, position, duty location, etc in letter
    template for recruitment and selection
-   Added report of the score given by all panel member to all candidate along
    with remarks and download feature in recruitment and selection
-   Added feature to display the overall question of recruitment and selection
    in a single page
-   Added Agriculture Sector in industry type
-   Added unit test of payroll generation

#### Changed

-   Replace delete with cancel and delete an icon from cancel icon in leave
    cancel section
-   The tax-exempt list is separated in downloaded payroll
-   Downloaded payroll is sorted by employer code
-   Removed Hiring information step in job vacancy post and changes the preview
    page accordingly for the supervisor section
-   Changes in payslip according to changes in future payroll generation
-   Date filter in all training page
-   Replaced "OT & Leave" Section with "Leave" section

### Bug Fixes

-   Fixed expense management bugs
-   Fixed credit leave delete issue
-   Fixed disable application bugs
-   Fixed minor training bugs
-   Lost hour data incorrect in user-profile page
-   404 error in core
-   Fixed Event attendance bugs
-   Fixed Off boarding bugs
-   Fixed Credit Leave issues

## [2.5.5] - 2020-04-27

##### Added

-   Unit Of Work Done in Payroll
-   Expense Management Module
-   Super Admin Portal to manage permissions
-   Additional detail about in task detail page
-   App icon for advance salary

##### Changed

-   Change in Noticeboard's "Attendance & Leave" detail

##### Fixes

-   Console errors at HR Admin section
-   Manual Attendance Punch In/Punch Out details
-   Responsive errors of HRIS, Attendance and Leave in HR Admin section
-   Forgot Password and Activation Link expiration issue
-   Prevent XSS

## [2.5.4] - 2020-04-16

##### Added

-   Sidebar Slider
-   Attendance Adjustment request bulk action for HR Admin
-   Attendance Adjustment request bulk action for Supervisor
-   Overtime Claim request bulk action for HR Admin
-   Overtime Claim request bulk action for Supervisor
-   Leave Request bulk action for HR Admin
-   Leave Request bulk action for Supervisor
-   Attendance Geolocation Report for HR Admin
-   Attendance Geolocation Report for Supervisor

##### Changed

-   VueRouter Consistency
-   Page Responsiveness

##### Fixes

-   Organization logo in payslip
-   Console errors

## [2.5.3] - 2020-03-27

##### Added

-   Sidebar notification in task.
-   Date-time for remarks history in leave, adjustment and overtime request
    history is now available.
-   Supervisor can now access detailed profile of their subordinates.
-   Text editor in questionnaire now supports subscript and superscript.
-   Search by name in payroll headings is now available.
-   Progress bar is visible when request is in pending state.

#### Changed

-   Improved logic for getting stats for app icon.
-   VueSearch is implemented.
-   Updated hints in Letter Template.
-   Count Formatting in Likes, Comment and Notification.
-   New implementation of remember me.

#### Fixes

-   Code refactor and optimization.
-   Noticeboard url preview.

## [2.5.2] - 2020-03-13

##### Added

-   Training Need Analysis, act on Training request in bulk.
-   App icon added for interview and reference check page in top navigation panel.
-   After payroll generation error message displayed for pending attendance and Leave request, numbers displayed is
    clickable and clicking on it redirected to respective page.
-   Payroll collection >> Added Nepali date of payroll generation, search employee filter, package name, working days,
    worked hours, overtime hours, absent days, step columns.
-   Option to delete individual payroll from the list of generated payrolls.
-   Option to regenerate offer letter.
-   Salary structure can be viewed in the offer letter.

#### Changed

-   Allowed holiday rules to have multiple branches, divisions, ethnicities and religions.
-   Employee Separation, edit option to add/change last working date.
-   Payroll collection can now be sorted by `from date`, `to date`.
-   Change request will be sent from HR’s normal user profile. Previously it was directly updated.
-   Validation added when deleting the used division, employment level, employment type, job title, branch.
-   Noticeboard >> My subordinate, Attendance and Leave card single API implementation.
-   Added expected working hours in the Payslip.
-   Block SVG image from the application.
-   Maintained checklist order in Task and Task template.

#### Fixed

-   Travel Attendance deletion issue. Previously, other entries beside the travel attendance request also got deleted
    after the travel attendance request deletion.
-   Two digit after decimal point in amount values and right aligned the amount value.
-   Permission implementation for HR in noticeboard. HR was unable to delete Noticeboard post.
-   Multiple click issue in Leave request, attendance adjustment request and overtime request.
-   Auto-complete issues.

## [2.5.1] - 2020-02-28

###### Added

-   Added Travel Attendance
-   Delete feature in travel attendance
-   Extra addition/ deduction heading edit feature added
-   Added Download feature in General Information Report of Payroll.
-   Past employee list are displayed in assign payroll package page by clicking on past employee button.

###### Changed

-   After payroll is generated, user should not be able to edit step in employment experience as well as should not be able to delete employment experience.
-   If there are multiple advance salary request in same payroll month than amount from the first advance salary requests, repayment plan is deducted and in next payroll second advance salary requests, repayment plan is deducted and so on.
-   Amount should be deducted from the payroll date after the Advance salary generation date. Currently is deducted from past date payroll too.
-   HR should not be able to delete already used Division, Employment Level
    , Employment Type, Job title and Branch. Error message should be displayed while deleting such list.
-   If an employee has pending review and is off-boarding than during off
    -boarding process need to add validation to stop the review process before off-boarding.
-   Remove percentage from Hobbies in profile completeness

###### Fixed

-   Major and minor bug fixes

### [Hot Fix]

## [2.5.0.3] - 2020-02-25

##### Fixes

-   Can generate payroll for past users now.

### [Hot Fix]

## [2.5.0.1] - 2020-02-17

###### Fixes

-   Prevent user from updating step of experience whose payroll has been
    generated.
-   Fixed errors in event calendar
-   Fixed merge issues

## [2.5.0] - 2020-02-17

###### Added

-   Added advance salary approvals and clearance option
-   Added feature to deduct advance salary from payroll
-   Added APIs for Travel Attendance Request
-   **Added modules `Questionnaire`, `Assessment`, `Training`, and `Recruitment and Selection`**

###### Fixed

-   Payroll Edit issues
-   Prevent user experience edit of start date is before last payroll generation date

### [Unreleased]

## [2.4.9] - 2020-01-31

###### Added

-   TDS type added in add heading form when Payroll Settings Type is Salary TDS and Type is Tax.
-   Added payroll edit history report.
-   Added tax report
-   Added advance salary.
-   Added General information report in payroll

###### Changed

-   Revamp provident fund report page.
-   File format not supported message is displayed when malformed image is uploaded.
-   Revamp employee import page.
-   Payroll generation method changed to background.
-   Consistent context menu in normal user section and supervisor section.

###### Fixed

-   Fixed delete issue in noticeboard post for HR Admin.
-   Other bug fixes

## [2.4.8] - 2020-01-17

###### Added

-   Added KSAO in user profile section and assign KSAO feature by bulk and in single

###### Changed

-   Changed payroll generation async and use locking mechanism
-   Implemented cache in organization settings
-   While editing payroll package which is already used error message displayed in backend "This package heading cannot be changed" but not visible in frontend.

###### Fixed

-   After payroll is generated headings amount which are not applicable to the following user should not be editable.
-   Major and minor bug fixes

## [2.4.7] - 2020-01-03

###### Added

-   Password protect database backup
-   Auto logout from all device when password changed.
-   Blank layout used in switch organization and common settings

###### Changed

-   API separated for supervisor and Organization
-   Optimize API of user autocomplete, noticeboard , holiday, mission and vision, division, branch, employment level and employment status
-   Sync method change in holiday import from synchronous to asynchronous

###### Fixed

-   Fixed text editors bugs
-   Fixed side bar collapse issues
-   Fixed HTML title
-   Minor bug fixes

## [2.4.6] - 2019-12-30

###### Added

-   Added Attendance sync ADMS .
-   Shortcut added in employment experience page, on board employee page and
    add employee page to add job title, employment level etc. from the same page.
-   Added Skills, Ability, Knowledge and Other Characteristics in organization settings.
-   Added category filter and show "Idle", "Used" and "Damaged" counts in office equipment page.
-   Added import feature in Meeting Room, Office Equipment , Equipment Category, Job title, Employment Type, Employment Level and Division.
-   Added Compensatory rule in holiday in overtime settings.
-   Added edit option after payroll is saved.
-   Notification will be sent to respective user for their anniversary and birthday posts in noticeboard.
-   Save and Add Another" button added in user details page like Contact Details, Education Details etc

###### Changed

-   While sending adjustment request start and end time is set to shift start and end time as default.
-   Changed Birthday and Anniversary image.
-   Simplified create working shift page.

###### Fixed

-   Compensatory leave balance deduction issues after leave expire when it is in request state.
-   package amount is recalculated once it is updated.
-   Salary generated is not divided into ratio for employee who join or left organization in mid of month.
-   Minor bug fixes and style changes.

## [2.4.5] - 2019-12-09

###### Added

-   Individual Attendance settings revamp
-   Normal user can now send multiple change request
-   Client data successfully sync in portal and host portal in aws
-   ADMS - attendance sync method added

###### Changed

-   Changed by default date filter from "This Month" to "This Year" in supervisor section and HR admin section of adjustment request page.
-   Changed by default date filter from "This Month" to "This Year" in supervisor section and HR admin section of overtime claim request page.
-   Changed by default date filter from "This Month" to "This Year" in supervisor section and HR admin section of leave request page.

###### Fixed

-   Account log out after super admin permission is removed
-   Leave count for an employee is shown in leave overview whose leave has been deleted.
-   Punctuality issues in Noticeboard for employee who joined in mid of month.
-   Lost hour displayed is full day for approved half leave.
-   404 error message displayed when clicking on already responded notification.
-   Fixed events bugs
-   500 error from dashboard
-   500 error on auto generated post in noticeboard.
-   Leave/Overtime/Adjustment request issues for user, whose supervisor is set to "Do not assign any supervisor?".
-   Reduced punctuality report loading time.

## [2.4.4] - 2019-11-15

-   Added permission in on-boarding/off-boarding modules with dependencies

###### Fixed

-   Fixed daily attendance page issues of HR admin section.
-   Past employee displayed in assign supervisor page
-   Save button missing in create new MasterSettings
-   Page not refresh when adding/ updating individual attendance settings, master settings.
-   While updating leave balance by hr admin, visible by default symbol changes to false, but after page reload it is changed as it is.
-   Leave balance issues in employee separation steps.
-   404 error while assigning supervisor from on-boarding process.
-   Task details not displayed in employment review reports.
-   Break in/out details not displayed clicking on number in HR admin/supervisor section.
-   Irregularities report time format issues.
-   Other minor bug fixes

## [2.4.3] - 2019-10-25

###### Added

-   Added supervisor switch option
-   Added column "Package Amount" and "Difference" in payslip
-   Added Meeting Room
-   Added meeting module in events
-   Organization search added in switch organization page and redesign page.
-   Office equipment can be assign to meeting room.
-   Added Nepali calendar in date time picker and single date picker in date filter.
-   Equipment category added in common settings

###### Changed

-   Redesign task Gantt chart.
-   Changed html header pattern to similar format
-   Revamp remember me
-   Revamp events
-   Revamp fiscal year settings page.

###### Fixed

-   Leave UI bugs
-   Fixed organization holiday console error
-   Fixed fiscal year in date filter
-   Fixed assign core task issue
-   Fixed login page, Reset password and change password UI issues
-   Employee import issues
-   Fixed attendance irregularities issues
-   Fixed mater Report UI bugs

## [2.4.2] - 2019-10-04

###### Added

-   Added fiscal year (Nepali) calendar in date filters.
-   Added office equipment
-   Added equipments and possessions in employment profile.
-   Added hints in payroll create/update heading page.
-   Added Contract Settings notification for HR Admin when contract status
    changed to medium to critical of any employee.
-   Added message "I acknowledge if contract not updated in time,HR Admin
    and first level supervisor will get notification each day until contract
    not updated and respective employee will be moved to past employee." in
    contract settings page.
-   Added search in payroll package list page.
-   Added objectives and job description with text editor in add employee
    stepper.
-   Download option added in generated payroll.

###### Changed

-   While sharing the realhrsoft noticeboard link, "irealhrsoft-frontend"
    was displayed in link instead of "RealHRsoft".
-   Fixed heading row and name column in payroll generate page and payroll
    collection page.
-   Fixed heading row in payroll heading page.

###### Fixed

-   Console error from overall system
-   Late In Late Out email for template not assigned notification will be
    send to HR Admin.
-   Fixed stats issue when date filter applied in contract change request
    page and task report page.
-   Fixed UI bugs which appeared due to vuetify upgrade.
-   When the Employees end date is set and "is active" is set to false.
    Employee is shown in past employee list but is still Active.
-   Fixed issue in Overtime re-calibration and generation for Leave applied.
-   Master settings clone issue while clicking save button.
-   Absent email send issues
-   Fixed 500 error message displayed when generating payroll with one
    heading with rules `015*_Basic_Salary_`. While creating heading 015 will
    not be accepted by system.
-   Fixed pagination issue in payroll generated page.
-   While creating new employment experience with active current
    employment experience in contract, both employment experience are saved
    as current experience issue fixed.

## [2.4.1] - 2019-09-19

###### Added

-   When HR admin and Supervisor click on notification for adjustment/overtime/leave/task request or forwarded request, request detail is opened in bottom sheet.
-   Notification added in HR section when the payslip is Acknowledged With Remarks by the employees.
-   **Employment Profile**
-   Implement auto step increment in every change in fiscal year
-   Notification permissions in HR section
-   Option added to keep the supervisor not assigned and send leave requests to HR.
-   Checklist ordering feature added while creating task
-   Added status filter in task feedback page of normal user
-   **Employee hierarchy chart**
-   Added field objective with text editor and added text editor in job description in employment experience.
-   When auto step increment list is added in employment review page status "Waiting Confirmation" is added with new employment experience as well as payroll package and core task copied to new experience.

###### Changed

-   In attendance adjustment request details date is also added in "Requested In Time" and "Requested out Time". Previously only time was displayed.

###### Fixed

-   Unable to update/delete own post in Noticeboard
-   Multiple Employment Current Experience is being added.
-   Fixed error displayed while editing headings with decimal values.
-   Fixed payroll generation issue due to hold.
-   Background tasks of overtime fixed.
-   Leave delete request issue fixed.
-   Fixed page not found error When supervisor from different organization deny or forward leave request.
-   Fixed issue of not being able to type text in title, checklist and description of assign task page.
-   UI bugs fixes after vuetify upgrade

## [2.4.0] - 2019-09-06

###### Added

-   Package clone option added in payroll.
-   Add type "Extra Addition" in settings type "Fringe Benefit"
-   Add type "Deduction" in settings type "Social Security Fund"
-   Added easy method to add heading in package.
-   Auto Birthday post
-   Auto Anniversary post
-   Re-amp permission feature
-   New day feature added in calendar
-   New chart added in reports

###### Changed

-   Bulk assign package in payroll.
-   Removed all non functional buttons
-   For shiftless employee punctuality is changed to "N/A"

###### Fixed

-   When generating payroll full leave is counted as absent days issues
-   Payroll bugs fixing
-   When employee join in mid and left in mid, such employee get full payment for whole month while generating for certain days issues
-   Leave request delete issues
-   when employee click on like count to see who like the post, all employee are not displayed issues
-   While changing employment experience, Change type are displayed from organization settings. It should be shown from HRIS settings issues
-   When employee tries to delete employment experience for which package is assigned, error message must be displayed issues
-   Adding hints in letter template issues.

##### Major application upgrade

-   Vuetify 1.15 upgrade to 2.0.14
-   Node packages upgrade

## [2.3.0] - 2019-08-26

###### Added

-   Bank details for normal user
-   Leave Request Delete History feature
-   Events in HR Admin section
-   Break In Break Out report for normal user
-   Interactive Events
-   Noticeboard image download option
-   Rebate in payroll
-   Hold payroll
-   Payslip Response in HR Admin section
-   Tax details page from payslip
-   Normal user tax details page
-   Payroll start fiscal year settings
-   Disabled Applications (To disable worklog in organization)
-   Assign To and Status added in task report download
-   Preparation sheet while generating payroll
-   Payroll Overview
-   Payroll overview settings
-   Permisssion

###### Changed

-   Redesign payslip page
-   Redesign add package page
-   Redesign Create package page
-   Redesign payroll assign page

###### Fixed

-   Work hours updated to shift or vice-versa, changes are occurred instantly
-   Payroll bug fixing
-   Casual leave and compensatory leave not generated issues
-   Changing status issue in task when computer date and time is changed to past.
-   Profile picture picture change issue
-   Past employee are displayed in assign package page
-   In today's log page the attendance entry details are not loaded for employee with no shift assigned.
-   Pop-up issue in Attendance Adjustment request

### [2.2.2] - 2019-07-23

##### Added

-   Gantt chart for Task Planning
-   Yearly Leave Report
-   Summarized yearly Leave Report
-   Carry Forward Leave Report

### [2.2.1] - 2019-07-20

##### Added

-   Export feature in all reports added in previous release (Leave Reports and Attendance Reports)
-   Master Setting Clone
-   Dynamic HRIS report with fields select.
-   Task approval cycle
-   Filters for past user in reports.

##### Changed

-   Leave renew logic refactor. Takes reference from Fiscal Year
-   Fiscal Year logic revamped

## [2.2.0] - 2019-07-05

###### Added

-   Attendance overview for normal user
-   Leave overview for normal user
-   ID Card Feature
-   Leave Reports(Compensatory Leave Report,Monthly Leave Report ,
    Attendance and Leave Report Added in Generalized Report,
    Individual Monthly Leave Report) For Hr
-   Attendance Report(Comparative Overtime Report,Attendance Adjustment Report,
    Overtime Detail Report,Attendance Irregularity Report,
    Attendance Monthly Report)
-   HR Post Acknowledge feature added in Noticeboard
-   WorkLog Feature (Logging by user and reviewing by supervisor)

## [2.1.1] - 2019-06-21

###### Added

-   Holiday list Normal User View.
-   Holiday list download to Normal User.
-   Holiday list import to the HR.
-   Clickable task overview from noticeboard.
-   Task search from name.
-   Color indexing added in task efficiency report.
-   Show RA and KRA in task assign page.

###### Changed

-   Leave rule validation refactor.
-   Same UI when uploading and updating the pictures in notice board.
-   Side Bar Finalization.
-   Changed Employment Status to Employment Type from all the places.

###### Fixed

-   Fixed multiple click issue.
-   Other bug fixes.

## [2.1.0] - 2019-05-25

###### Added

-   Daily/Monthly attendance report for Normal User , Supervisor and HR
-   Task Efficiency report on Task Overview for Normal User
-   Member of Task Project can view it from Normal User section and can view task associated with the project
-   Tags(ie:New,Promoted) for User in Employee Directory as well as Hr View
-   Scheduled Post view page for HR
-   Activate, Block/Unblock user manually by HR
-   Date Filters applied on any data is displayed. [Y] for Year,[M] for month, [C] for custom date range
-   Task reminders can now be sent to every person involved in Task
-   Supervisor can now view Sub-ordinate task
-   Separate Organization Notification for HR

###### Changed

-   Task Overview Page for Normal User now consist of Task statistics
-   User can now see efficiency breakdown to understand how the total efficiency is calculated
-   Updated Dashboard for HR
-   Recurring Task whole architecture has been changed

###### Fixed

-   Validation message for Noticeboard image upload
-   case insensitive email/username login
-   Payroll bug fixes
-   Bug fixes

## [2.0.0] - 2019-05-25

###### Added

-   On-boarding /Off-Boarding Feature
-   Report builder template update
-   Login Mechanism for better UX
-   TOC , About Us and Privacy Policy Added
-   Sub-task count and Result Area are shown in Task detail page

###### Changed

-   Navigation Bar and page structure complete redesigned
-   Extension number of user is now not a mandatory field
-   Noticeboard Post has now 10000 characters limitation
-   Noticeboard Post Comments has now 1000 characters limitation
-   Task Description has now 100000 characters limitation

###### Fixed

-   Breadcrumb issue resolved
-   Empty page issue on Fresh installation of project
-   Report Builder bugs
-   Payroll Bugs

##### Removed

-   Unused page

## [1.1.1] - 2019-05-02

-   Refactored migrations [Affected 192.168.99.55]

## [1.1.0] - 2019-04-26

###### Added

-   **Report Builder**
-   **Export Log**: Export logs are now kept for all exports.
-   **Attendance Import**
-   **Attendance Calendar for Supervisors**: Can view subordinates' attendance calendar
-   **Notifications** in overtime, attendance adjustment requests, Task Comments

###### Changed

-   Result Area can only be edit if it has no users assigned.
-   Update Leave Irregularity Report generation logic
-   Overtime : User has to update generated overtime not to exceed claimable overtime before claim request
-   Optimize organization settings check and counts

###### Fixed

-   Block multiple delete change requests for same record
-   Fix change request generation for medical info
-   Check supervisor permissions before showing action buttons in all requests for supervisor
-   Reduce balance for holiday inclusive leaves on holidays
-   Fix today's issues not displayed in attendance issues
-   Parent Task's deadline should be greater than sub task's deadline while updating parent task
-   Minor fix on delayed flag for task

---

## [1.0.0] - 2019-04-12

###### Added

-   Payroll module
-   Task module revamped which consist of
    scheduled task and Task Completion Ack Feature ,Efficiency Calculation and Task Disassociate feature
-   Task Overview and Report Section for HR
-   Email Logs
-   Nepali Calender
-   OverTime Calculation
-   Added notification generator for Task , Leave Request , Attendance Adjustment

###### Changed

-   Approved Task will preserve its status to COMPLETED , previously Approved Task were CLOSED
-   Authorization Token architecture has been changed so as to support token expiration and refresh
-   Punctuality of a user for a day decreases by 1.6% every min until it reaches 0
-   Attendance Extended Shift logic
-   Attendance Adjustment can be sent separately for Punch In and Punch Out

###### Fixed

-   Recurring task bugs while creating recurring task
-   Compensatory leave expiring the next day
-   Daily time sheet generator was generating time sheet for a single user only
-   Noticeboard post likes count

---

## [0.0.1] - 2019-02-01

###### Added

-   HRIS , TASK , EVENTS & Calendar , LEAVE , Organization ,Attendance Module and related Feature
-   Permission Handler
