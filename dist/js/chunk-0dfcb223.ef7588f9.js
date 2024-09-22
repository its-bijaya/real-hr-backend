(window["webpackJsonp"]=window["webpackJsonp"]||[]).push([["chunk-0dfcb223","chunk-da62e0c8","chunk-2d22d378"],{"271b":function(t,e,n){"use strict";n("99af");e["a"]={sendActivationEmail:"/users/activation/send/",activateHere:function(t,e){return"/hris/".concat(t,"/users/").concat(e,"/activate/")},blockEmployee:function(t,e){return"/hris/".concat(t,"/users/").concat(e,"/block/")},unblockEmployee:function(t,e){return"/hris/".concat(t,"/users/").concat(e,"/unblock/")},assignAuditUser:function(t,e){return"hris/".concat(t,"/users/").concat(e,"/enable-audit-user/")},removeAuditUser:function(t,e){return"hris/".concat(t,"/users/").concat(e,"/disable-audit-user/")}}},"6c6f":function(t,e,n){"use strict";n("d3b7");e["a"]={data:function(){return{deleteNotification:{dialog:!1,heading:"Confirm Delete",text:"Are you sure you want to delete ?"}}},methods:{deleteData:function(t,e){var n=this;return new Promise((function(r,o){!n.loading&&t&&(n.loading=!0,n.$http.delete(t,e||{}).then((function(t){n.crud.message&&setTimeout((function(){n.notifyUser(n.crud.message)}),1e3),r(t),n.loading=!1})).catch((function(t){n.pushErrors(t),n.notifyInvalidFormResponse(),o(t),n.loading=!1})).finally((function(){n.deleteNotification.dialog=!1})))}))}}}},"8da0":function(t,e,n){"use strict";n("99af");e["a"]={getGeneratedPayroll:"/payroll/payrolls/",getUserPackageDetails:function(t){return"/payroll/".concat(t,"/user-experience-package-list/")},getIndividualUserPackageDetails:function(t,e){return"/payroll/".concat(t,"/user-experience-package-list/").concat(e,"/")},getUserPayrollHistory:function(t){return"/payroll/employee-payroll/".concat(t,"/edits/")},getDisbursementReport:function(t,e){return"/payroll/".concat(t,"/payrolls/").concat(e,"/reports/disbursement/")},getPayrollTaxReport:function(t,e){return"/payroll/".concat(t,"/payrolls/").concat(e,"/reports/tax/")},exportPayrollTaxReport:function(t,e){return"/payroll/".concat(t,"/payrolls/").concat(e,"/reports/tax/export/")},getPayrollProvidentFundReport:function(t,e){return"/payroll/".concat(t,"/payrolls/").concat(e,"/reports/pf/")},getPayrollSSFReport:function(t,e){return"/payroll/".concat(t,"/payrolls/").concat(e,"/reports/ssf/")},exportPayrollProvidentFundReport:function(t,e){return"/payroll/".concat(t,"/payrolls/").concat(e,"/reports/pf/export/")},getGeneralInfoReport:function(t){return"/payroll/".concat(t,"/reports/general-info/")},getPackageWiseSalaryReport:function(t){return"/payroll/".concat(t,"/reports/package-info/")},exportPackageWiseSalaryReport:function(t){return"/payroll/".concat(t,"/reports/package-info/export/")},exportGeneralInfoReport:function(t){return"/payroll/".concat(t,"/reports/general-info/export/")},approvePayroll:function(t){return"/payroll/".concat(t,"/settings/payroll-approval/")},setPayrollPersonalHeadingReportSetting:function(t){return"payroll/".concat(t,"/payroll-extra-heading-setting/")},setPayrollDetailReportSetting:function(t){return"payroll/".concat(t,"/payroll-collection-report-setting/")},setSSFReportSetting:function(t){return"payroll/".concat(t,"/ssf-report-setting/")},setPayrollDifferenceSetting:function(t){return"payroll/".concat(t,"/payroll-difference-heading-setting/")},disbursementReportSetting:function(t){return"/payroll/".concat(t,"/disbursement-report-setting/")},setTaxReportSetting:function(t){return"payroll/".concat(t,"/tax-report-setting/")},monthlyInsightTable:function(t){return"payroll/".concat(t,"/employee-metrics-report/")},exportMonthlyInsightTable:function(t){return"payroll/".concat(t,"/employee-metrics-report/export/")},exportAssignPackage:function(t){return"payroll/".concat(t,"/user-experience-package-list/export/")},setInsightHeadingSetting:function(t){return"payroll/".concat(t,"/employee-metrics-report-setting/")},getPayrollActivity:function(t){return"payroll/".concat(t,"/payroll-package-activity/")}}},"983c":function(t,e,n){"use strict";n("d3b7");e["a"]={methods:{getData:function(t,e,n){var r=this,o=arguments.length>3&&void 0!==arguments[3]&&arguments[3];return new Promise((function(a,s){!r.loading&&t&&(r.clearNonFieldErrors(),r.$validator.errors.clear(),r.loading=o,r.$http.get(t,n||{params:e||{}}).then((function(t){a(t),r.loading=!1})).catch((function(t){r.pushErrors(t),r.notifyInvalidFormResponse(),s(t),r.loading=!1})))}))},getBlockingData:function(t,e,n){var r=this;return new Promise((function(o,a){r.getData(t,e,n,!0).then((function(t){o(t)})).catch((function(t){a(t)}))}))}}}},a019:function(t,e,n){"use strict";n("99af");e["a"]={getUserResultAreas:function(t,e){return"/hris/".concat(t,"/user-result-areas/").concat(e,"/")}}},d132:function(t,e,n){"use strict";n("99af");e["a"]={getUserSetting:function(t){return"/attendance/".concat(t,"/users/settings/")},postUserSetting:function(t){return"/attendance/".concat(t,"/users/settings/")},updateUserSetting:function(t,e){return"/attendance/".concat(t,"/users/settings/").concat(e,"/")},deleteUserSetting:function(t,e){return"/attendance/".concat(t,"/users/settings/").concat(e,"/")}}},ecac:function(t,e,n){"use strict";n.r(e);var r=function(){var t=this,e=t.$createElement,n=t._self._c||e;return n("v-card",[n("vue-card-title",{attrs:{title:"Profile Completeness Summary",subtitle:"Profile Completeness of "+t.userInfo.user.name.partial,icon:"mdi-chart-donut-variant"}},[n("template",{slot:"actions"},[n("v-progress-circular",{attrs:{color:t.getProgressColor(t.userInfo.user.profile_completeness),value:t.userInfo.user.profile_completeness,rotate:"-90",size:"40",width:"3"}},[n("div",{staticClass:"text-subtitle-2"},[t._v(" "+t._s(t.userInfo.user.profile_completeness)+" % ")])])],1)],2),n("v-divider"),t.userData.particulars&&t.userData.profile_details?n("v-card-text",[n("v-row",[n("v-col",[n("span",{staticClass:"blueGrey--text font-weight-bold"},[t._v(" Profile Details")]),n("span",[t._v(" (Section marked with * contributes to profile completeness percentage.)")])])],1),n("v-row",{attrs:{align:"center"}},[t._l(t.userData.profile_details,(function(e,r){return[n("v-col",{key:"name-"+r,staticClass:"primary--text pointer",attrs:{cols:"3"},on:{click:function(n){return t.$emit("open-tab",t.profileDetailMapper[e.name].name)}}},[n("v-icon",{staticClass:"primary--text pointer",attrs:{small:""},domProps:{textContent:t._s(t.profileDetailMapper[e.name].icon)}}),t._v(" "+t._s(t.profileDetailMapper[e.name].name)+" "+t._s(t.profileDetailMapper[e.name].required?"*":"")+" ")],1),n("v-col",{key:"status-"+r,attrs:{cols:"3"}},[n("status-pill-button",{attrs:{status:e.exists}})],1)]}))],2),n("v-divider"),n("v-row",[n("v-col",[n("span",{staticClass:"blueGrey--text font-weight-bold"},[t._v(" Settings and Packages")])])],1),n("v-row",{attrs:{align:"center"}},[n("v-col",{attrs:{cols:"3"}},[n("v-icon",{attrs:{small:""},domProps:{textContent:t._s("mdi-account-circle-outline")}}),t._v(" User Status: ")],1),n("v-col",{attrs:{cols:"8"}},[n("status-pill-button",{attrs:{status:"Active"===t.userData.particulars.user_status,"status-text":t.userData.particulars.user_status}})],1),"hr"===t.as?n("v-col",[n("v-btn",{attrs:{"x-small":"",icon:"",disabled:!t.userData.particulars.has_current_experience},on:{click:function(e){return t.setUserStatusForm(t.userData.particulars.user_status)}}},[n("v-icon",{attrs:{small:"",color:"primary"},domProps:{textContent:t._s("mdi-square-edit-outline")}})],1)],1):t._e()],1),n("v-row",{attrs:{align:"center"}},[n("v-col",{attrs:{cols:"3"}},[n("v-icon",{attrs:{small:""},domProps:{textContent:t._s("mdi-account-circle-outline")}}),t._v(" Supervisors: ")],1),n("v-col",{attrs:{cols:"8"}},[n("thumbnail-users",{attrs:{users:t.userData.particulars.supervisors.map((function(t){return t.supervisor})),"img-size":"30","total-users":t.userData.particulars.supervisors.length}})],1),"hr"===t.as?n("v-col",[n("v-btn",{attrs:{"x-small":"",icon:""},on:{click:t.setSupervisorForm}},[n("v-icon",{attrs:{small:"",color:"primary"},domProps:{textContent:t._s("mdi-square-edit-outline")}})],1)],1):t._e()],1),n("v-row",{attrs:{align:"center"}},[n("v-col",{attrs:{cols:"3"}},[n("v-icon",{attrs:{small:""},domProps:{textContent:t._s("mdi-clock-outline")}}),t._v(" Work Shift: ")],1),n("v-col",{attrs:{cols:"8"}},[n("span",{staticClass:"blueGrey--text font-weight-medium"},[t._v(" "+t._s(t.get(t.userData.particulars.work_shift,"name")||"N/A")+" ")])]),"hr"===t.as?n("v-col",[n("v-btn",{attrs:{"x-small":"",icon:""},on:{click:t.setBulkAttendanceForm}},[n("v-icon",{attrs:{small:"",color:"primary"},domProps:{textContent:t._s("mdi-square-edit-outline")}})],1)],1):t._e()],1),n("v-row",{attrs:{align:"center"}},[n("v-col",{attrs:{cols:"3"}},[n("v-icon",{attrs:{small:""},domProps:{textContent:t._s("mdi-clock-outline")}}),t._v(" Overtime Settings: ")],1),n("v-col",{attrs:{cols:"8"}},[n("span",{staticClass:"blueGrey--text font-weight-medium"},[t._v(" "+t._s(t.get(t.userData.particulars.overtime_settings,"name")||"N/A")+" ")])]),"hr"===t.as?n("v-col",[n("v-btn",{attrs:{"x-small":"",icon:""},on:{click:t.setBulkAttendanceForm}},[n("v-icon",{attrs:{small:"",color:"primary"},domProps:{textContent:t._s("mdi-square-edit-outline")}})],1)],1):t._e()],1),n("v-row",{attrs:{align:"center"}},[n("v-col",{attrs:{cols:"3"}},[n("v-icon",{attrs:{small:""},domProps:{textContent:t._s("mdi-clock-outline")}}),t._v(" Credit Hour: ")],1),n("v-col",{attrs:{cols:"8"}},[n("span",{staticClass:"blueGrey--text font-weight-medium"},[t._v(" "+t._s(t.get(t.userData.particulars.credit_hour,"name")||"N/A")+" ")])]),"hr"===t.as?n("v-col",[n("v-btn",{attrs:{"x-small":"",icon:""},on:{click:t.setBulkAttendanceForm}},[n("v-icon",{attrs:{small:"",color:"primary"},domProps:{textContent:t._s("mdi-square-edit-outline")}})],1)],1):t._e()],1),n("v-row",{attrs:{align:"center"}},[n("v-col",{attrs:{cols:"3"}},[n("v-icon",{attrs:{small:""},domProps:{textContent:t._s("mdi-web")}}),t._v(" Web Attendance Settings: ")],1),n("v-col",{attrs:{cols:"8"}},[n("status-pill-button",{attrs:{status:!!t.userData.particulars.web_attendance_setting,"status-text":t.userData.particulars.web_attendance_setting?"Enabled":"Disabled"}})],1),"hr"===t.as?n("v-col",[n("v-btn",{attrs:{"x-small":"",icon:""},on:{click:function(e){return t.setWebAttendanceForm()}}},[n("v-icon",{attrs:{small:"",color:"primary"},domProps:{textContent:t._s("mdi-square-edit-outline")}})],1)],1):t._e()],1),n("v-row",{attrs:{align:"center"}},[n("v-col",{attrs:{cols:"3"}},[n("v-icon",{attrs:{small:""},domProps:{textContent:t._s("mdi-fingerprint")}}),t._v(" Device Bio-id Settings: ")],1),n("v-col",{attrs:{cols:"8"}},[0===t.userData.particulars.device_bio_id_settings.length?n("span",{staticClass:"blueGrey--text font-weight-medium"},[t._v("N/A")]):t._e(),t._l(t.userData.particulars.device_bio_id_settings,(function(e,r){return n("span",{key:r,staticClass:"blueGrey--text font-weight-medium"},[n("v-chip",{staticClass:"mx-1",attrs:{color:"blue-grey lighten-5"}},[t._v(t._s(e))])],1)}))],2),"hr"===t.as?n("v-col",[n("v-btn",{attrs:{"x-small":"",icon:""},on:{click:t.setAssignDeviceForm}},[n("v-icon",{attrs:{small:"",color:"primary"},domProps:{textContent:t._s("mdi-square-edit-outline")}})],1)],1):t._e()],1),n("v-row",{attrs:{align:"center"}},[n("v-col",{attrs:{cols:"3"}},[n("v-icon",{attrs:{small:""},domProps:{textContent:t._s("mdi-calendar-range-outline")}}),t._v(" Leave Settings: ")],1),n("v-col",{attrs:{cols:"8"}},[0===t.userData.particulars.leave_settings.length?n("span",{staticClass:"blueGrey--text font-weight-medium"},[t._v("N/A")]):t._e(),t._l(t.userData.particulars.leave_settings,(function(e,r){return[n("v-chip",{key:r,staticClass:"indigo--text text--accent-2 font-weight-medium ma-1",attrs:{small:""}},[n("span",[t._v(" "+t._s(e)+" ")])])]}))],2),"hr"===t.as?n("v-col",[n("v-btn",{attrs:{"x-small":"",icon:""},on:{click:t.openLeaveSettingsPage}},[n("v-icon",{attrs:{small:"",color:"primary"},domProps:{textContent:t._s("mdi-square-edit-outline")}})],1)],1):t._e()],1),n("v-row",{attrs:{align:"center"}},[n("v-col",{attrs:{cols:"3"}},[n("v-icon",{attrs:{small:""},domProps:{textContent:t._s("mdi-cash")}}),t._v(" Payroll Package: ")],1),n("v-col",{attrs:{cols:"8"}},[n("span",{staticClass:"blueGrey--text font-weight-medium"},[t._v(" "+t._s(t.userData.particulars.payroll_package||"N/A")+" ")])]),"hr"===t.as?n("v-col",[n("v-btn",{attrs:{"x-small":"",icon:""},on:{click:t.setPayrollPackageForm}},[n("v-icon",{attrs:{small:"",color:"primary"},domProps:{textContent:t._s("mdi-square-edit-outline")}})],1)],1):t._e()],1),n("v-row",{attrs:{align:"center"}},[n("v-col",{attrs:{cols:"3"}},[n("v-icon",{attrs:{small:""},domProps:{textContent:t._s("mdi-file-document-outline")}}),t._v(" RA and Core Tasks: ")],1),n("v-col",{attrs:{cols:"8"}},[n("status-pill-button",{attrs:{status:!!t.userData.particulars.ra_and_core_tasks_assigned,"status-text":t.userData.particulars.ra_and_core_tasks_assigned?"Assigned":"Not Assigned"}})],1),"hr"===t.as?n("v-col",[n("v-btn",{attrs:{"x-small":"",icon:""},on:{click:t.setAssignCoreTaskForm}},[n("v-icon",{attrs:{small:"",color:"primary"},domProps:{textContent:t._s("mdi-square-edit-outline")}})],1)],1):t._e()],1),n("v-row",{attrs:{align:"center"}},[n("v-col",{attrs:{cols:"3"}},[n("v-icon",{attrs:{small:""},domProps:{textContent:t._s("mdi-file-document-outline")}}),t._v(" Email Notifications: ")],1),n("v-col",{attrs:{cols:"8"}},[n("status-pill-button",{attrs:{status:!!t.get(t.userData.particulars.email_notifications,"late_in_notification_email"),"status-text":"Late In"}}),n("status-pill-button",{staticClass:"px-4",attrs:{status:!!t.get(t.userData.particulars.email_notifications,"absent_notification_email"),"status-text":"Absent"}}),n("status-pill-button",{staticClass:"px-4",attrs:{status:!!t.get(t.userData.particulars.email_notifications,"weekly_attendance_report_email"),"status-text":"Weekly Attendance Report"}}),n("status-pill-button",{attrs:{status:!!t.get(t.userData.particulars.email_notifications,"overtime_remainder_email"),"status-text":"Overtime"}})],1),"hr"===t.as?n("v-col",[n("v-btn",{attrs:{"x-small":"",icon:""},on:{click:t.setBulkAttendanceForm}},[n("v-icon",{attrs:{small:"",color:"primary"},domProps:{textContent:t._s("mdi-square-edit-outline")}})],1)],1):t._e()],1)],1):t._e(),t.editForm.showBottomSheet?n("v-bottom-sheet",{attrs:{persistent:"",scrollable:"",fullscreen:t.editForm.fullScreen},on:{keydown:function(e){return!e.type.indexOf("key")&&t._k(e.keyCode,"esc",27,e.key,["Esc","Escape"])?null:t.refreshView.apply(null,arguments)}},model:{value:t.editForm.showBottomSheet,callback:function(e){t.$set(t.editForm,"showBottomSheet",e)},expression:"editForm.showBottomSheet"}},[n("v-card",[n("vue-card-title",{attrs:{title:t.editForm.title,subtitle:t.editForm.subtitle,icon:t.editForm.icon,closable:"",dark:""},on:{close:t.refreshView}}),n("v-divider"),t.editForm.showCardText?n("v-card-text",[n(t.editForm.template,t._g(t._b({tag:"component"},"component",t.objectToBind,!1),t.eventToListen))],1):n(t.editForm.template,t._g(t._b({tag:"component"},"component",t.objectToBind,!1),t.eventToListen))],1)],1):t._e(),t.editForm.showOriginalForm?n("v-bottom-sheet",{on:{keydown:function(e){if(!e.type.indexOf("key")&&t._k(e.keyCode,"esc",27,e.key,["Esc","Escape"]))return null;t.editForm.showOriginalForm=!1}},model:{value:t.editForm.showOriginalForm,callback:function(e){t.$set(t.editForm,"showOriginalForm",e)},expression:"editForm.showOriginalForm"}},[n(t.editForm.template,t._g(t._b({tag:"component"},"component",t.objectToBind,!1),t.eventToListen))],1):t._e(),n("vue-dialog",{attrs:{notify:t.deleteNotify},on:{agree:function(e){return t.blockUnblockUser()},close:function(e){t.deleteNotify.dialog=!1}}})],1)},o=[],a=n("1da1"),s=(n("96cf"),n("d3b7"),n("3ca3"),n("ddb0"),n("7db0"),n("f12b")),i=n("fab2"),c=n("271b"),l=n("d132"),u=n("8da0"),d=n("a019"),m={components:{ThumbnailUsers:function(){return Promise.resolve().then(n.bind(null,"cde3"))},StatusPillButton:function(){return n.e("chunk-2d0dd661").then(n.bind(null,"80e8"))},EmployeeListForm:function(){return n.e("chunk-c7220e98").then(n.bind(null,"b9ff"))},AssignSupervisor:function(){return n.e("chunk-511bcae8").then(n.bind(null,"0a33"))},BulkAttendanceSetting:function(){return n.e("chunk-6a005d83").then(n.bind(null,"8dee"))},AttendanceSettings:function(){return n.e("chunk-49f26688").then(n.bind(null,"b624"))},AssignDevice:function(){return n.e("chunk-5059bca8").then(n.bind(null,"ecb6"))},AssignPackageForm:function(){return Promise.all([n.e("chunk-2d0aa5b8"),n.e("chunk-2d212b99"),n.e("chunk-5213a055"),n.e("chunk-1ad3548a")]).then(n.bind(null,"99ff"))},AssignCoreTaskForm:function(){return n.e("chunk-5a1f7100").then(n.bind(null,"371f"))}},mixins:[s["a"]],props:{userInfo:{type:Object,required:!0},as:{type:String,default:""}},data:function(){return{userData:{particulars:{supervisors:[],device_bio_id_settings:[],leave_settings:[]}},editForm:{showBottomSheet:!1,showOriginalForm:!1,showCardText:!0,title:"",subtitle:"",icon:"",template:""},profileDetailMapper:{general_information:{icon:"mdi-information-outline",name:"General Information",required:!0},contact_details:{icon:"mdi-card-account-mail-outline",name:"Contact",required:!0},address:{icon:"mdi-map-outline",name:"Address",required:!0},education_details:{icon:"mdi-school-outline",name:"Education",required:!0},documents:{icon:"mdi-file-document-outline",name:"Documents"},bank_details:{icon:"mdi-cash",name:"Bank"},medical_information:{icon:"mdi-hospital-box-outline",name:"Medical Information",required:!0},insurance_details:{icon:"mdi-folder-account-outline",name:"Insurance"},past_experience:{icon:"mdi-bullhorn-outline",name:"Past Experience"},employment_experience:{icon:"mdi-account-outline",name:"Employment Experience"},training_details:{icon:"mdi-school-outline",name:"Training"},volunteering_experience:{icon:"mdi-hand-heart",name:"Volunteer Experience"},legal_information:{icon:"mdi-text-box-outline",name:"Legal Information",required:!0},language:{icon:"mdi-web",name:"Language",required:!0},social_activity:{icon:"mdi-rotate-orbit",name:"Social Activity"}},deleteNotify:{dialog:!1,heading:"Confirm",subheading:"Please confirm your action.",text:""},blockUnblock:!1,objectToBind:{},eventToListen:{}}},created:function(){this.loadData()},methods:{loadData:function(){var t=this;this.getData(i["a"].getProfileCompleteness(this.userInfo.user.id),{as:this.as}).then((function(e){t.userData=e})),this.getData(i["a"].getUserDetail(this.userInfo.user.id)+"?send_supervisor=true&send_subordinates=true&as=".concat(this.as)).then((function(e){t.userInfo.user.profile_completeness=e.user.profile_completeness}))},setUserStatusForm:function(t){var e=this;"Not Activated"===t?(this.editForm.template="EmployeeListForm",this.editForm.title="You can activate the user here.",this.editForm.subtitle="You can activate the user here.",this.editForm.icon="mdi-account-outline",this.editForm.showBottomSheet=!0,this.objectToBind={user:this.userInfo},this.eventToListen={"close-form":function(){return e.refreshView()}}):(this.blockUnblock="Blocked"===t,this.blockUnblock?this.deleteNotify.text="Are you sure you want unblock this User?":this.deleteNotify.text="Are you sure you want block this User?",this.deleteNotify.dialog=!0)},blockUnblockUser:function(){var t=this;this.blockUnblock?(this.crud.message="Successfully Unblocked Employee.",this.insertData(c["a"].unblockEmployee(this.getOrganizationSlug,this.userInfo.user.id)).then((function(){t.deleteNotify.dialog=!1,t.loadData()})).catch((function(e){t.notifyInvalidFormResponse(e.response.data[0])}))):(this.crud.message="Successfully Blocked Employee.",this.insertData(c["a"].blockEmployee(this.getOrganizationSlug,this.userInfo.user.id)).then((function(){t.deleteNotify.dialog=!1,t.loadData()})))},setSupervisorForm:function(){var t=this;this.editForm.template="AssignSupervisor",this.editForm.title="You can assign and revoke supervisor for the user here.",this.editForm.subtitle="You can assign and revoke supervisor for the user here.",this.editForm.icon="mdi-account-outline",this.editForm.showBottomSheet=!0,this.objectToBind={"assign-for":this.userInfo.user.id,"reassign-data":this.userData.particulars.supervisors},this.eventToListen={refreshDataTable:function(){return t.refreshView()}}},setBulkAttendanceForm:function(){var t=this;this.editForm.template="BulkAttendanceSetting",this.editForm.showOriginalForm=!0,this.objectToBind={"user-list":[this.userInfo.user.id]},this.eventToListen={refresh:function(){return t.refreshView()},"close-form":function(){return t.editForm.showOriginalForm=!1}}},setWebAttendanceForm:function(){var t=this;return Object(a["a"])(regeneratorRuntime.mark((function e(){var n;return regeneratorRuntime.wrap((function(e){while(1)switch(e.prev=e.next){case 0:return t.editForm.template="AttendanceSettings",e.next=3,t.getAttendanceSetting();case 3:n=e.sent,t.editForm.title="You can configure web attendance settings for user.",t.editForm.subtitle="You can configure web attendance settings for user.",t.editForm.icon="mdi-web",t.editForm.showBottomSheet=!0,t.editForm.showCardText=!1,t.objectToBind={"action-data":n.results[0]},t.eventToListen={"dismiss-form":function(){return t.refreshView()}};case 11:case"end":return e.stop()}}),e)})))()},setAssignDeviceForm:function(){var t=this;return Object(a["a"])(regeneratorRuntime.mark((function e(){var n;return regeneratorRuntime.wrap((function(e){while(1)switch(e.prev=e.next){case 0:return t.editForm.template="AssignDevice",e.next=3,t.getAttendanceSetting();case 3:n=e.sent,t.editForm.title="Assign Employee to Device.",t.editForm.subtitle="-",t.editForm.icon="mdi-file-document-outline",t.editForm.showBottomSheet=!0,t.objectToBind={"setting-id":n.results[0].id,user:n.results[0].user},t.eventToListen={refresh:function(){return t.refreshView()}};case 10:case"end":return e.stop()}}),e)})))()},openLeaveSettingsPage:function(){var t=this.$router.resolve({name:"admin-slug-leave-settings-master-settings",params:{slug:this.$route.params.slug}});window.open(t.href,"_blank")},setPayrollPackageForm:function(){var t=this;this.getData(u["a"].getUserPackageDetails(this.getOrganizationSlug),{user_id:this.userInfo.user.id,as:this.as,user_status:this.userData.particulars.has_current_experience?"":"past"}).then((function(e){t.editForm.template="AssignPackageForm",t.editForm.title="You can assign payroll package for user.",t.editForm.subtitle="You can assign payroll package for user.",t.editForm.icon="mdi-cash",t.editForm.showBottomSheet=!0,t.editForm.fullScreen=!0,t.objectToBind={"selected-user-data":e.results.find((function(e){return e.id===t.userInfo.user.id})),"is-past-employee":!t.userData.particulars.has_current_experience},t.eventToListen={"form-response":function(){return t.refreshView()}}}))},setAssignCoreTaskForm:function(){var t=this;this.getData(d["a"].getUserResultAreas(this.getOrganizationSlug,this.userInfo.user.id)).then((function(e){t.editForm.template="AssignCoreTaskForm",t.editForm.title="You can assign result area and core task for user.",t.editForm.subtitle="You can assign result area and core task for user.",t.editForm.icon="mdi-cash",t.editForm.showBottomSheet=!0,t.objectToBind={"selected-user-data":e},t.eventToListen={formResponse:function(){return t.refreshView()}}}))},refreshView:function(){this.editForm.showBottomSheet=!1,this.editForm.showOriginalForm=!1,this.editForm.showCardText=!0,this.loadData()},getAttendanceSetting:function(){var t=this;return Object(a["a"])(regeneratorRuntime.mark((function e(){return regeneratorRuntime.wrap((function(e){while(1)switch(e.prev=e.next){case 0:return e.next=2,t.getData(l["a"].getUserSetting(t.getOrganizationSlug),{id:t.userInfo.user.id,user_status:t.userData.particulars.has_current_experience?"all":"past"}).then((function(t){return t}));case 2:return e.abrupt("return",e.sent);case 3:case"end":return e.stop()}}),e)})))()},getProgressColor:function(t){return t<50?"red":t<80?"orange":"green"}}},p=m,f=n("2877"),h=n("6544"),g=n.n(h),v=n("288c"),b=n("8336"),_=n("b0af"),y=n("99d9"),k=n("cc20"),x=n("62ad"),F=n("ce7e"),w=n("132d"),D=n("490a"),P=n("0fd9b"),S=Object(f["a"])(p,r,o,!1,null,null,null);e["default"]=S.exports;g()(S,{VBottomSheet:v["a"],VBtn:b["a"],VCard:_["a"],VCardText:y["c"],VChip:k["a"],VCol:x["a"],VDivider:F["a"],VIcon:w["a"],VProgressCircular:D["a"],VRow:P["a"]})},f0d5:function(t,e,n){"use strict";n("d3b7"),n("3ca3"),n("ddb0");var r=n("c44a");e["a"]={components:{NonFieldFormErrors:function(){return n.e("chunk-6441e173").then(n.bind(null,"ab8a"))}},mixins:[r["a"]],data:function(){return{crud:{name:"record",message:"",addAnother:!1},formValues:{},loading:!1}}}},f12b:function(t,e,n){"use strict";var r=n("f0d5"),o=n("983c"),a=n("f70a"),s=n("6c6f");e["a"]={mixins:[r["a"],o["a"],a["a"],s["a"]]}},f70a:function(t,e,n){"use strict";n("d3b7"),n("caad");e["a"]={methods:{insertData:function(t,e){var n=this,r=arguments.length>2&&void 0!==arguments[2]?arguments[2]:{},o=r.validate,a=void 0===o||o,s=r.clearForm,i=void 0===s||s,c=arguments.length>3?arguments[3]:void 0;return new Promise((function(r,o){!n.loading&&t&&(n.clearErrors(),n.$validator.validateAll().then((function(s){a||(s=!0),s&&(n.loading=!0,n.$http.post(t,e,c||{}).then((function(t){n.clearErrors(),i&&(n.formValues={}),n.crud.addAnother||n.$emit("create"),n.crud.message&&setTimeout((function(){n.notifyUser(n.crud.message)}),1e3),r(t),n.loading=!1})).catch((function(t){n.pushErrors(t),n.notifyInvalidFormResponse(),o(t),n.loading=!1})))})))}))},patchData:function(t,e){var n=this,r=arguments.length>2&&void 0!==arguments[2]?arguments[2]:{},o=r.validate,a=void 0===o||o,s=r.clearForm,i=void 0===s||s,c=arguments.length>3?arguments[3]:void 0;return new Promise((function(r,o){n.updateData(t,e,{validate:a,clearForm:i},"patch",c).then((function(t){r(t)})).catch((function(t){o(t)}))}))},putData:function(t,e){var n=this,r=arguments.length>2&&void 0!==arguments[2]?arguments[2]:{},o=r.validate,a=void 0===o||o,s=r.clearForm,i=void 0===s||s,c=arguments.length>3?arguments[3]:void 0;return new Promise((function(r,o){n.updateData(t,e,{validate:a,clearForm:i},"put",c).then((function(t){r(t)})).catch((function(t){o(t)}))}))},updateData:function(t,e){var n=this,r=arguments.length>2&&void 0!==arguments[2]?arguments[2]:{},o=r.validate,a=void 0===o||o,s=r.clearForm,i=void 0===s||s,c=arguments.length>3?arguments[3]:void 0,l=arguments.length>4?arguments[4]:void 0;return new Promise((function(r,o){!n.loading&&t&&["put","patch"].includes(c)&&(n.clearErrors(),n.$validator.validateAll().then((function(s){a||(s=!0),s&&(n.loading=!0,n.$http[c](t,e,l||{}).then((function(t){n.$emit("update"),n.clearErrors(),i&&(n.formValues={}),n.crud.message&&setTimeout((function(){n.notifyUser(n.crud.message)}),1e3),r(t),n.loading=!1})).catch((function(t){n.pushErrors(t),n.notifyInvalidFormResponse(),o(t),n.loading=!1})))})))}))},clearErrors:function(){this.clearNonFieldErrors(),this.$validator.errors.clear()}}}}}]);