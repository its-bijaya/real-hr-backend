(window["webpackJsonp"]=window["webpackJsonp"]||[]).push([["chunk-3e3cef65","chunk-da62e0c8","chunk-2d22d378"],{"3be1":function(t,e,o){"use strict";o.r(e);var i=function(){var t=this,e=t.$createElement,o=t._self._c||e;return t.details?o("v-card",[o("v-card-text",{staticClass:"scrollbar-md"},[t.nonFieldErrors?o("non-field-form-errors",{attrs:{"non-field-errors":t.nonFieldErrors}}):t._e(),t.loading?o("v-row",{attrs:{align:"center",justify:"center"}},[o("default-svg-loader")],1):o("div",[o("v-row",[["hr","supervisor"].includes(t.as)?o("v-col",{attrs:{cols:"12",md:"4"}},[o("div",{staticClass:"font-weight-medium"},[o("v-icon",{attrs:{small:""},domProps:{textContent:t._s("mdi-account-check-outline")}}),t._v(" Requested By: ")],1),o("div",{staticClass:"pl-4"},[o("vue-user",{attrs:{user:t.details.created_by}})],1)]):t._e(),o("v-col",{attrs:{md:"4",cols:"12"}},[o("div",{staticClass:"font-weight-medium"},[o("v-icon",{attrs:{small:""},domProps:{textContent:t._s("mdi-calendar-month-outline")}}),t._v(" Requested Date: ")],1),o("div",{staticClass:"font-weight-bold pl-5"},[t._v(" "+t._s(t.humanizeDate(t.details.created_at))+" ")]),o("div",{staticClass:"pl-5"},[t._v(" "+t._s(t.humanizeTime(t.details.created_at))+" ")])]),o("v-col",{attrs:{md:"4",cols:"12"}},[o("div",{staticClass:"font-weight-medium"},[o("v-icon",{attrs:{small:""},domProps:{textContent:t._s("mdi-information-outline")}}),t._v(" Status: ")],1),o("div",{staticClass:"ml-4 pt-1"},["Requested"===t.details.status?o("approval-chip",{attrs:{"user-detail":t.details.recipient,status:t.details.status}}):o("v-chip",{attrs:{color:t.$options.tabs[t.details.status],outlined:"",small:""}},[t._v(" "+t._s(t.details.status)+" ")])],1)])],1),o("v-row",[o("v-col",{attrs:{cols:"12",md:"4"}},[o("div",{staticClass:"font-weight-medium"},[o("v-icon",{attrs:{small:""},domProps:{textContent:t._s("mdi-information-outline")}}),t._v(" Operation/Project : ")],1),o("div",{staticClass:"font-weight-bold pl-5",domProps:{textContent:t._s(t.get(t.details.rate.operation,"title"))}})]),o("v-col",{attrs:{cols:"12",md:"4"}},[o("div",{staticClass:"font-weight-medium"},[o("v-icon",{attrs:{small:""},domProps:{textContent:t._s("mdi-information-outline")}}),t._v(" Code/Task : ")],1),o("div",{staticClass:"font-weight-bold pl-5",domProps:{textContent:t._s(t.get(t.details.rate.operation_code,"title"))}})]),o("v-col",{attrs:{cols:"12",md:"4"}},[o("div",{staticClass:"font-weight-medium"},[o("v-icon",{attrs:{small:""},domProps:{textContent:t._s("mdi-information-outline")}}),t._v(" Rate: ")],1),o("span",{staticClass:"font-weight-bold pl-5"},[t._v(" "+t._s(t.details.rate.rate))])]),o("v-col",{attrs:{cols:"12",md:"4"}},[o("div",{staticClass:"font-weight-medium"},[o("v-icon",{attrs:{small:""},domProps:{textContent:t._s("mdi-information-outline")}}),t._v(" Quantity/Hours: ")],1),o("span",{staticClass:"font-weight-bold pl-5"},[t._v(" "+t._s(t.details.quantity))])]),o("v-col",{attrs:{cols:"6"}},[o("v-icon",{attrs:{small:""},domProps:{textContent:t._s("mdi-text-box-multiple-outline")}}),t._v(" Support Document: "),t.details.attachment?o("div",{staticClass:"ml-4 pt-1"},[o("v-btn",{attrs:{href:t.details.attachment,text:"",outlined:"",small:"",target:"_blank"},domProps:{textContent:t._s("View Attachment")}},[o("v-icon",{staticClass:"mx-2 pointer",attrs:{size:"30",small:"",color:"primary",title:"View/Download Document"},domProps:{textContent:t._s("mdi-file-document-outline")}})],1)],1):o("div",{staticClass:"pl-5"},[t._v("N/A")])],1)],1),o("div",{staticClass:"pt-2 font-weight-medium"},[o("v-icon",{attrs:{small:""},domProps:{textContent:t._s("mdi-file-document-outline")}}),t._v(" Reason for Request: ")],1),o("div",{staticClass:"pl-5",domProps:{textContent:t._s(t.details.remarks)}}),o("v-row",{staticClass:"blue-grey my-4 lighten-5"},[o("v-col",{attrs:{cols:"10"}},[o("v-timeline",{staticClass:"py-0 my-0"},t._l(t.details.histories,(function(e,i){return o("v-timeline-item",{key:i,staticClass:"pt-3",attrs:{right:"",color:"Denied"===e.action_performed||"Canceled"===e.action_performed?"danger":"success",icon:"Denied"===e.action_performed||"Canceled"===e.action_performed?"mdi-close":"mdi-check","show-dot":"",small:""}},[o("div",{staticClass:"font-weight-medium",domProps:{textContent:t._s(e.message)}}),o("template",{slot:"opposite"},[o("div",{staticClass:"font-weight-bold",domProps:{textContent:t._s(t.humanizeDate(e.created_at))}}),o("div",{domProps:{textContent:t._s(t.humanizeTime(e.created_at))}})])],2)})),1)],1)],1),t.details.recipient&&t.supervisorId===t.details.recipient.id&&(t.permissions.deny||t.permissions.approve||t.permissions.forward)&&("Requested"===t.details.status||"Forwarded"===t.details.status)||t.admin&&("Forwarded"===t.details.status||"Approved"===t.details.status||"Requested"===t.details.status)?o("v-row",{attrs:{"no-gutters":""}},[o("v-col",{attrs:{cols:"12"}},[o("v-row",{attrs:{"no-gutters":""}},[o("v-icon",{attrs:{small:""},domProps:{textContent:t._s("mdi-file-document-outline")}}),o("span",[t._v("Remarks*: ")])],1),o("v-text-field",t._b({directives:[{name:"validate",rawName:"v-validate",value:"required|max:255",expression:"'required|max:255'"}],staticClass:"py-0 my-0",attrs:{counter:255},model:{value:t.actionRemarks.remarks,callback:function(e){t.$set(t.actionRemarks,"remarks",e)},expression:"actionRemarks.remarks"}},"v-text-field",t.veeValidate("remarks",""),!1))],1)],1):t._e()],1)],1),o("v-card-actions",{staticClass:"py-0 very-light-blue"},[o("v-col",{staticClass:"text-right",attrs:{md:"12"}},[o("v-btn",{attrs:{text:""},domProps:{textContent:t._s("Cancel")},on:{click:function(e){return t.$emit("close")}}}),t.details.recipient&&t.supervisorId===t.details.recipient.id&&t.permissions.deny&&("Requested"===t.details.status||"Forwarded"===t.details.status)||t.admin&&("Forwarded"===t.details.status||"Requested"===t.details.status||"Approved"===t.details.status)?o("v-btn",{attrs:{depressed:"",color:"error"},domProps:{textContent:t._s("Deny")},on:{click:function(e){return t.processRequest("deny")}}}):t._e(),t.details.recipient&&t.supervisorId===t.details.recipient.id&&t.permissions.forward&&("Requested"===t.details.status||"Forwarded"===t.details.status)?o("v-btn",{staticClass:"purple lighten-1 white--text",attrs:{depressed:""},domProps:{textContent:t._s("Forward")},on:{click:function(e){return t.processRequest("forward")}}}):t._e(),t.details.recipient&&t.supervisorId===t.details.recipient.id&&t.permissions.approve&&("Requested"===t.details.status||"Forwarded"===t.details.status)||t.admin&&("Forwarded"===t.details.status||"Requested"===t.details.status)?o("v-btn",{attrs:{depressed:"",color:"teal white--text"},domProps:{textContent:t._s("Approve")},on:{click:function(e){return t.processRequest("approve")}}}):t._e(),!t.admin||"Forwarded"!==t.details.status&&"Approved"!==t.details.status&&"Requested"!==t.details.status?t._e():o("v-btn",{attrs:{depressed:"",color:"success"},domProps:{textContent:t._s("Confirm")},on:{click:function(e){return t.processRequest("confirm")}}})],1)],1)],1):t._e()},s=[],n=o("1da1"),a=o("5530"),r=(o("96cf"),o("a9e3"),o("c197")),c=o("e540"),d=o("02cb"),l=o("bf02"),u=o("eb03"),p=o("e88d"),m=o("f12b"),f=o("2f62"),v={name:"UnitOfWorkDetails",components:{DefaultSvgLoader:r["default"],VueUser:d["default"],ApprovalChip:p["a"]},mixins:[m["a"]],props:{itemRequest:{type:Object,default:void 0},as:{type:[Number,String],default:""},requestId:{type:[Number,String],default:""},notificationId:{type:[Number,String],default:""}},tabs:{Requested:"orange",Approved:"teal",Denied:"indigo",Forwarded:"purple",Confirmed:"green",Canceled:"danger",All:"blue"},data:function(){return{details:null,actionRemarks:{},permissions:{},admin:!1,supervisorId:null}},computed:Object(a["a"])({},Object(f["c"])({getSupervisorOrgSlug:"supervisor/getOrganizationSlug",getAppView:"common/getAppView"})),created:function(){this.getDetails()},methods:Object(a["a"])(Object(a["a"])({},Object(f["d"])({setUnreadNotificationCount:"notification/setUnreadNotificationCount"})),{},{humanizeDate:function(t){return this.$dayjs(t).format("YYYY-MM-DD")},humanizeTime:function(t){var e=this.$dayjs(t).format("h:mm:ss a");return"Invalid date"===e?"N/A":e},getDetails:function(){var t=this;this.supervisorId="supervisor"===this.as?this.getAuthStateUserId:null;var e=this.notificationId?this.requestId:this.itemRequest.id;"hrAdminView"===this.getAppView&&(this.admin=!0),this.notificationId&&"userView"===this.getAppView&&(this.supervisorId=this.getAuthStateUserId);var o=this.admin?"?as=hr":this.supervisorId?"?as=supervisor":"",i=this.supervisorId?this.getSupervisorOrgSlug:this.getOrganizationSlug;this.getData(c["a"].getUnitOfWorkDetails(i,e)+o).then((function(e){t.details=e,t.supervisorId&&t.getSupervisorPermission()}))},getSupervisorPermission:function(){var t=this;(this.supervisorId||this.notificationId)&&(this.permissions={},this.getData(l["a"].getSubordinatePermission(this.details.user.id)).then((function(e){t.permissions=e})))},processRequest:function(t){var e=this;return Object(n["a"])(regeneratorRuntime.mark((function o(){var i,s,n,a;return regeneratorRuntime.wrap((function(o){while(1)switch(o.prev=o.next){case 0:return i=e.supervisorId?e.getSupervisorOrgSlug:e.getOrganizationSlug,s="",n="","confirm"===t?(s=c["a"].confirmRequest(i,e.details.id),n="Unit of Work request Confirmed."):"deny"===t?(s=c["a"].declineRequest(i,e.details.id),n="Unit of Work request Denied."):"forward"===t?(s=c["a"].forwardRequest(i,e.details.id),n="Unit of Work request Forwarded."):(s=c["a"].approveRequest(i,e.details.id),n="Unit of Work request Approved."),e.crud.message=n,a=e.admin?"hr":"supervisor",s+="?as=".concat(a),o.next=9,e.validateAllFields();case 9:if(!o.sent){o.next=11;break}e.insertData(s,e.actionRemarks).then((function(){e.refresh()}));case 11:case"end":return o.stop()}}),o)})))()},refresh:function(){var t=this;this.notificationId&&this.postData(u["a"].readNotification(this.notificationId)).then((function(){t.setUnreadNotificationCount(0)})).catch((function(){t.notifyUser("Something went wrong","red")})),this.$emit("close")}})},h=v,g=o("2877"),w=o("6544"),C=o.n(w),_=o("8336"),k=o("b0af"),y=o("99d9"),b=o("cc20"),x=o("62ad"),q=o("132d"),R=o("0fd9b"),D=o("8654"),P=o("8414"),I=o("1e06"),F=Object(g["a"])(h,i,s,!1,null,null,null);e["default"]=F.exports;C()(F,{VBtn:_["a"],VCard:k["a"],VCardActions:y["a"],VCardText:y["c"],VChip:b["a"],VCol:x["a"],VIcon:q["a"],VRow:R["a"],VTextField:D["a"],VTimeline:P["a"],VTimelineItem:I["a"]})},"6c6f":function(t,e,o){"use strict";o("d3b7");e["a"]={data:function(){return{deleteNotification:{dialog:!1,heading:"Confirm Delete",text:"Are you sure you want to delete ?"}}},methods:{deleteData:function(t,e){var o=this;return new Promise((function(i,s){!o.loading&&t&&(o.loading=!0,o.$http.delete(t,e||{}).then((function(t){o.crud.message&&setTimeout((function(){o.notifyUser(o.crud.message)}),1e3),i(t),o.loading=!1})).catch((function(t){o.pushErrors(t),o.notifyInvalidFormResponse(),s(t),o.loading=!1})).finally((function(){o.deleteNotification.dialog=!1})))}))}}}},"983c":function(t,e,o){"use strict";o("d3b7");e["a"]={methods:{getData:function(t,e,o){var i=this,s=arguments.length>3&&void 0!==arguments[3]&&arguments[3];return new Promise((function(n,a){!i.loading&&t&&(i.clearNonFieldErrors(),i.$validator.errors.clear(),i.loading=s,i.$http.get(t,o||{params:e||{}}).then((function(t){n(t),i.loading=!1})).catch((function(t){i.pushErrors(t),i.notifyInvalidFormResponse(),a(t),i.loading=!1})))}))},getBlockingData:function(t,e,o){var i=this;return new Promise((function(s,n){i.getData(t,e,o,!0).then((function(t){s(t)})).catch((function(t){n(t)}))}))}}}},e540:function(t,e,o){"use strict";o("99af");e["a"]={getOperationList:function(t){return"/payroll/".concat(t,"/settings/unit-of-work/operations/")},postOperation:function(t){return"/payroll/".concat(t,"/settings/unit-of-work/operations/")},editOperation:function(t,e){return"/payroll/".concat(t,"/settings/unit-of-work/operations/").concat(e)},getCodeList:function(t){return"/payroll/".concat(t,"/settings/unit-of-work/operation-codes/")},postCode:function(t){return"/payroll/".concat(t,"/settings/unit-of-work/operation-codes/")},editCode:function(t,e){return"/payroll/".concat(t,"/settings/unit-of-work/operation-codes/").concat(e)},getRateList:function(t){return"/payroll/".concat(t,"/settings/unit-of-work/operation-rates/")},postRate:function(t){return"/payroll/".concat(t,"/settings/unit-of-work/operation-rates/")},editRate:function(t,e){return"/payroll/".concat(t,"/settings/unit-of-work/operation-rates/").concat(e)},importOperation:function(t){return"/payroll/".concat(t,"/settings/unit-of-work/operations/import/")},downloadOperation:function(t){return"/payroll/".concat(t,"/settings/unit-of-work/operations/import/sample")},importCode:function(t){return"/payroll/".concat(t,"/settings/unit-of-work/operation-codes/import/")},downloadCode:function(t){return"/payroll/".concat(t,"/settings/unit-of-work/operation-codes/import/sample/")},importRate:function(t){return"/payroll/".concat(t,"/settings/unit-of-work/operation-rates/import/")},downloadRate:function(t){return"payroll/".concat(t,"/settings/unit-of-work/operation-rates/import/sample")},postRequest:function(t){return"/payroll/".concat(t,"/unit-of-work/requests/")},getUnitOfWork:function(t){return"/payroll/".concat(t,"/unit-of-work/requests/")},cancelUnitOfWorkRequest:function(t,e){return"/payroll/".concat(t,"/unit-of-work/requests/").concat(e,"/cancel/")},getUnitOfWorkDetails:function(t,e){return"/payroll/".concat(t,"/unit-of-work/requests/").concat(e,"/")},declineRequest:function(t,e){return"/payroll/".concat(t,"/unit-of-work/requests/").concat(e,"/deny/")},approveRequest:function(t,e){return"/payroll/".concat(t,"/unit-of-work/requests/").concat(e,"/approve/")},forwardRequest:function(t,e){return"/payroll/".concat(t,"/unit-of-work/requests/").concat(e,"/forward/")},confirmRequest:function(t,e){return"/payroll/".concat(t,"/unit-of-work/requests/").concat(e,"/confirm/")},exportUnitOfWork:function(t){return"/payroll/".concat(t,"/unit-of-work/requests/export/")}}},e88d:function(t,e,o){"use strict";var i=function(){var t=this,e=t.$createElement,o=t._self._c||e;return o("div",[o("v-menu",{attrs:{"nudge-width":10,"open-on-hover":!0,bottom:"",right:"",transition:"scale-transition",origin:"top left"},scopedSlots:t._u([{key:"activator",fn:function(e){var i=e.on;return[o("v-chip",{staticClass:"white--text",attrs:{small:"",outlined:"",color:"orange"}},[o("v-avatar",{staticStyle:{"margin-left":"-12px"},attrs:{left:""}},[o("v-img",t._g({attrs:{src:t.userDetail.profile_picture_thumb||t.userDetail.profile_picture}},i))],1),t._v(" "+t._s(t.status)+" ")],1)]}}])},[o("vue-hover-card",{attrs:{user:t.userDetail}})],1)],1)},s=[],n=o("49bb"),a={components:{VueHoverCard:n["a"]},props:{userDetail:{type:Object,required:!0},status:{type:String,required:!0}}},r=a,c=o("2877"),d=o("6544"),l=o.n(d),u=o("8212"),p=o("cc20"),m=o("adda"),f=o("e449"),v=Object(c["a"])(r,i,s,!1,null,"5cafa090",null);e["a"]=v.exports;l()(v,{VAvatar:u["a"],VChip:p["a"],VImg:m["a"],VMenu:f["a"]})},f0d5:function(t,e,o){"use strict";o("d3b7"),o("3ca3"),o("ddb0");var i=o("c44a");e["a"]={components:{NonFieldFormErrors:function(){return o.e("chunk-6441e173").then(o.bind(null,"ab8a"))}},mixins:[i["a"]],data:function(){return{crud:{name:"record",message:"",addAnother:!1},formValues:{},loading:!1}}}},f12b:function(t,e,o){"use strict";var i=o("f0d5"),s=o("983c"),n=o("f70a"),a=o("6c6f");e["a"]={mixins:[i["a"],s["a"],n["a"],a["a"]]}},f70a:function(t,e,o){"use strict";o("d3b7"),o("caad");e["a"]={methods:{insertData:function(t,e){var o=this,i=arguments.length>2&&void 0!==arguments[2]?arguments[2]:{},s=i.validate,n=void 0===s||s,a=i.clearForm,r=void 0===a||a,c=arguments.length>3?arguments[3]:void 0;return new Promise((function(i,s){!o.loading&&t&&(o.clearErrors(),o.$validator.validateAll().then((function(a){n||(a=!0),a&&(o.loading=!0,o.$http.post(t,e,c||{}).then((function(t){o.clearErrors(),r&&(o.formValues={}),o.crud.addAnother||o.$emit("create"),o.crud.message&&setTimeout((function(){o.notifyUser(o.crud.message)}),1e3),i(t),o.loading=!1})).catch((function(t){o.pushErrors(t),o.notifyInvalidFormResponse(),s(t),o.loading=!1})))})))}))},patchData:function(t,e){var o=this,i=arguments.length>2&&void 0!==arguments[2]?arguments[2]:{},s=i.validate,n=void 0===s||s,a=i.clearForm,r=void 0===a||a,c=arguments.length>3?arguments[3]:void 0;return new Promise((function(i,s){o.updateData(t,e,{validate:n,clearForm:r},"patch",c).then((function(t){i(t)})).catch((function(t){s(t)}))}))},putData:function(t,e){var o=this,i=arguments.length>2&&void 0!==arguments[2]?arguments[2]:{},s=i.validate,n=void 0===s||s,a=i.clearForm,r=void 0===a||a,c=arguments.length>3?arguments[3]:void 0;return new Promise((function(i,s){o.updateData(t,e,{validate:n,clearForm:r},"put",c).then((function(t){i(t)})).catch((function(t){s(t)}))}))},updateData:function(t,e){var o=this,i=arguments.length>2&&void 0!==arguments[2]?arguments[2]:{},s=i.validate,n=void 0===s||s,a=i.clearForm,r=void 0===a||a,c=arguments.length>3?arguments[3]:void 0,d=arguments.length>4?arguments[4]:void 0;return new Promise((function(i,s){!o.loading&&t&&["put","patch"].includes(c)&&(o.clearErrors(),o.$validator.validateAll().then((function(a){n||(a=!0),a&&(o.loading=!0,o.$http[c](t,e,d||{}).then((function(t){o.$emit("update"),o.clearErrors(),r&&(o.formValues={}),o.crud.message&&setTimeout((function(){o.notifyUser(o.crud.message)}),1e3),i(t),o.loading=!1})).catch((function(t){o.pushErrors(t),o.notifyInvalidFormResponse(),s(t),o.loading=!1})))})))}))},clearErrors:function(){this.clearNonFieldErrors(),this.$validator.errors.clear()}}}}}]);