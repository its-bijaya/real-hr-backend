(window["webpackJsonp"]=window["webpackJsonp"]||[]).push([["chunk-0370db5e","chunk-2d2160c2","chunk-2d2160c2","chunk-ec2dc8e2","chunk-2d2160c2","chunk-2d2160c2","chunk-2d2160c2"],{"0798":function(t,e,s){"use strict";var a=s("5530"),o=s("ade3"),r=(s("caad"),s("0c18"),s("10d2")),l=s("afdd"),n=s("9d26"),i=s("f2e7"),c=s("7560"),d=s("f40d"),u=s("58df"),v=s("d9bd");e["a"]=Object(u["a"])(r["a"],i["a"],d["a"]).extend({name:"v-alert",props:{border:{type:String,validator:function(t){return["top","right","bottom","left"].includes(t)}},closeLabel:{type:String,default:"$vuetify.close"},coloredBorder:Boolean,dense:Boolean,dismissible:Boolean,closeIcon:{type:String,default:"$cancel"},icon:{default:"",type:[Boolean,String],validator:function(t){return"string"===typeof t||!1===t}},outlined:Boolean,prominent:Boolean,text:Boolean,type:{type:String,validator:function(t){return["info","error","success","warning"].includes(t)}},value:{type:Boolean,default:!0}},computed:{__cachedBorder:function(){if(!this.border)return null;var t={staticClass:"v-alert__border",class:Object(o["a"])({},"v-alert__border--".concat(this.border),!0)};return this.coloredBorder&&(t=this.setBackgroundColor(this.computedColor,t),t.class["v-alert__border--has-color"]=!0),this.$createElement("div",t)},__cachedDismissible:function(){var t=this;if(!this.dismissible)return null;var e=this.iconColor;return this.$createElement(l["a"],{staticClass:"v-alert__dismissible",props:{color:e,icon:!0,small:!0},attrs:{"aria-label":this.$vuetify.lang.t(this.closeLabel)},on:{click:function(){return t.isActive=!1}}},[this.$createElement(n["a"],{props:{color:e}},this.closeIcon)])},__cachedIcon:function(){return this.computedIcon?this.$createElement(n["a"],{staticClass:"v-alert__icon",props:{color:this.iconColor}},this.computedIcon):null},classes:function(){var t=Object(a["a"])(Object(a["a"])({},r["a"].options.computed.classes.call(this)),{},{"v-alert--border":Boolean(this.border),"v-alert--dense":this.dense,"v-alert--outlined":this.outlined,"v-alert--prominent":this.prominent,"v-alert--text":this.text});return this.border&&(t["v-alert--border-".concat(this.border)]=!0),t},computedColor:function(){return this.color||this.type},computedIcon:function(){return!1!==this.icon&&("string"===typeof this.icon&&this.icon?this.icon:!!["error","info","success","warning"].includes(this.type)&&"$".concat(this.type))},hasColoredIcon:function(){return this.hasText||Boolean(this.border)&&this.coloredBorder},hasText:function(){return this.text||this.outlined},iconColor:function(){return this.hasColoredIcon?this.computedColor:void 0},isDark:function(){return!(!this.type||this.coloredBorder||this.outlined)||c["a"].options.computed.isDark.call(this)}},created:function(){this.$attrs.hasOwnProperty("outline")&&Object(v["a"])("outline","outlined",this)},methods:{genWrapper:function(){var t=[this.$slots.prepend||this.__cachedIcon,this.genContent(),this.__cachedBorder,this.$slots.append,this.$scopedSlots.close?this.$scopedSlots.close({toggle:this.toggle}):this.__cachedDismissible],e={staticClass:"v-alert__wrapper"};return this.$createElement("div",e,t)},genContent:function(){return this.$createElement("div",{staticClass:"v-alert__content"},this.$slots.default)},genAlert:function(){var t={staticClass:"v-alert",attrs:{role:"alert"},on:this.listeners$,class:this.classes,style:this.styles,directives:[{name:"show",value:this.isActive}]};if(!this.coloredBorder){var e=this.hasText?this.setTextColor:this.setBackgroundColor;t=e(this.computedColor,t)}return this.$createElement("div",t,[this.genWrapper()])},toggle:function(){this.isActive=!this.isActive}},render:function(t){var e=this.genAlert();return this.transition?t("transition",{props:{name:this.transition,origin:this.origin,mode:this.mode}},[e]):e}})},"0c18":function(t,e,s){},b49b:function(t,e,s){"use strict";s.r(e);var a=function(){var t=this,e=t.$createElement,s=t._self._c||e;return s("div",[t.loading&&!t.payrollDetails.employee?s("default-svg-loader"):t.payrollDetails.employee?s("v-row",{staticClass:"mx-0",attrs:{id:"payslipPrint"}},[s("v-col",{staticClass:"text-center",attrs:{cols:"12"}},[s("v-alert",{staticClass:"rounded-0 blue-grey white--text py-1 my-0",attrs:{dense:""}},[s("div",{staticClass:"text-title"},[t._v("Employee Payslip")]),s("div",{staticClass:"text-subtitle-2"},[t._v(" "+t._s(t.payrollDate)+" ")])])],1),s("v-col",{staticClass:"py-0 pr-1",attrs:{cols:"6"}},[s("v-row",{attrs:{"no-gutters":""}},[s("v-col",{attrs:{cols:"4"}},[t._v("Employee Name")]),s("v-col",{attrs:{cols:"8"}},[t._v(": "+t._s(t.get(t.payrollDetails.employee,"full_name")||"N/A")+" ")])],1),s("v-row",{attrs:{"no-gutters":""}},[s("v-col",{attrs:{cols:"4"}},[t._v("Job Title")]),s("v-col",{attrs:{cols:"8"}},[t._v(": "+t._s(t.get(t.payrollDetails.employee,"job_title")||"N/A")+" ")])],1),s("v-row",{attrs:{"no-gutters":""}},[s("v-col",{attrs:{cols:"4"}},[t._v("Division")]),s("v-col",{attrs:{cols:"8"}},[t._v(": "+t._s(t.get(t.payrollDetails.employee,"division.name")||"N/A")+" ")])],1),s("v-row",{attrs:{"no-gutters":""}},[s("v-col",{attrs:{cols:"4"}},[t._v("Marital status")]),s("v-col",{attrs:{cols:"8"}},[t._v(": "+t._s(t.get(t.payrollDetails.employee,"marital_status")||"N/A")+" ")])],1)],1),s("v-col",{staticClass:"py-0 pl-1",attrs:{cols:"6"}},[s("v-row",{attrs:{"no-gutters":""}},[s("v-col",{attrs:{cols:"4"}},[t._v("Employee Code")]),s("v-col",{attrs:{cols:"8"}},[t._v(": "+t._s(t.get(t.payrollDetails.employee,"code")||"N/A")+" ")])],1),s("v-row",{attrs:{"no-gutters":""}},[s("v-col",{attrs:{cols:"4"}},[t._v("Username")]),s("v-col",{attrs:{cols:"8"}},[t._v(": "+t._s(t.get(t.payrollDetails.employee,"username")||"N/A")+" ")])],1),s("v-row",{attrs:{"no-gutters":""}},[s("v-col",{attrs:{cols:"4"}},[t._v("DOJ")]),s("v-col",{attrs:{cols:"8"}},[t._v(": "+t._s(t.get(t.payrollDetails.employee,"joined_date")||"N/A")+" ")])],1),s("v-row",{attrs:{"no-gutters":""}},[s("v-col",{attrs:{cols:"4"}},[t._v("Branch")]),s("v-col",{attrs:{cols:"8"}},[t._v(": "+t._s(t.get(t.payrollDetails.employee,"branch")||"N/A")+" ")])],1)],1),s("v-col",{staticClass:"py-4",attrs:{cols:"12"}},[s("v-divider")],1),s("v-col",{staticClass:"py-0 pr-1",attrs:{cols:"6"}},[s("v-alert",{staticClass:"\n          rounded-0\n          text-center\n          grey--text\n          text--darken-2 text-body-2\n          font-weight-medium\n        ",attrs:{dense:"",color:"grey lighten-3"}},[t._v(" Earnings ")])],1),s("v-col",{staticClass:"py-0 pl-1",attrs:{cols:"6"}},[s("v-alert",{staticClass:"\n          rounded-0\n          text-center\n          grey--text\n          text--darken-2 text-body-2\n          font-weight-medium\n        ",attrs:{dense:"",color:"grey lighten-3"}},[t._v(" Deductions ")])],1),s("v-col",{staticClass:"py-0 pr-1 mt-n3",attrs:{cols:"6"}},t._l(t.earnings,(function(e,a){return s("v-row",{key:a,attrs:{"no-gutters":""}},[s("v-col",{attrs:{cols:"6"}},[t._v(t._s(e.heading)+" :")]),s("v-col",{staticClass:"pr-1 text-right",attrs:{cols:"6"}},[t._v(t._s(t.formatCurrency(e.amount))+" ")])],1)})),1),s("v-col",{staticClass:"py-0 pl-1 mt-n3",attrs:{cols:"6"}},t._l(t.deductions,(function(e,a){return s("v-row",{key:a,attrs:{"no-gutters":""}},[s("v-col",{attrs:{cols:"6"}},[t._v(t._s(e.heading)+" :")]),s("v-col",{staticClass:"pr-1 text-right",attrs:{cols:"6"}},[t._v(t._s(t.formatCurrency(e.amount))+" ")])],1)})),1),s("v-col",{staticClass:"py-1 pr-1",attrs:{cols:"6"}},[s("v-alert",{staticClass:"rounded-0 text-body-2 px-0 mb-0",attrs:{dense:"",color:"very-light-blue"}},[s("v-row",{attrs:{"no-gutters":""}},[s("v-col",{staticClass:"pa-0 font-weight-medium",attrs:{cols:"6"}},[t._v(" Total Earnings : ")]),s("v-col",{staticClass:"pa-0 pr-1 font-weight-medium text-right",attrs:{cols:"6"}},[t._v(t._s(t.formatCurrency(t.totalEarnings))+" ")])],1)],1)],1),s("v-col",{staticClass:"py-1 pl-1",attrs:{cols:"6"}},[s("v-alert",{staticClass:"rounded-0 text-body-2 px-0 mb-0",attrs:{dense:"",color:"very-light-blue"}},[s("v-row",{attrs:{"no-gutters":""}},[s("v-col",{staticClass:"pa-0 font-weight-medium",attrs:{cols:"6"}},[t._v(" Total Deductions : ")]),s("v-col",{staticClass:"pa-0 pr-1 font-weight-medium text-right",attrs:{cols:"6"}},[t._v(t._s(t.formatCurrency(t.totalDeductions))+" ")])],1)],1)],1),s("v-col",{staticClass:"py-4",attrs:{cols:"12"}},[s("v-divider")],1),s("v-col",{staticClass:"py-0 pr-1",attrs:{cols:"6"}},[s("v-row",{attrs:{"no-gutters":""}},[s("v-col",{attrs:{cols:"6"}},[t._v("Payment Date")]),s("v-col",{attrs:{cols:"6"}},[t._v(" : "+t._s(t.$dayjs(t.payrollDetails.approved_date).format("YYYY-MM-DD")||"N/A")+" ")])],1),s("v-row",{attrs:{"no-gutters":""}},[s("v-col",{attrs:{cols:"6"}},[t._v("Bank Name")]),s("v-col",{attrs:{cols:"6"}},[t._v(": "+t._s(t.get(t.payrollDetails.bank,"bank.name")||"N/A")+" ")])],1),s("v-row",{attrs:{"no-gutters":""}},[s("v-col",{attrs:{cols:"6"}},[t._v("Bank Account Number")]),s("v-col",{attrs:{cols:"6"}},[t._v(": "+t._s(t.get(t.payrollDetails.bank,"account_number")||"N/A")+" ")])],1),s("v-row",{attrs:{"no-gutters":""}},[s("v-col",{attrs:{cols:"6"}},[t._v("PAN Number")]),s("v-col",{attrs:{cols:"6"}},[t._v(": "+t._s(t.get(t.payrollDetails.employee.legal_info,"pan_number")||"N/A")+" ")])],1),s("v-row",{attrs:{"no-gutters":""}},[s("v-col",{attrs:{cols:"6"}},[t._v("SSF ID")]),s("v-col",{attrs:{cols:"6"}},[t._v(": "+t._s(t.get(t.payrollDetails.employee.legal_info,"ssfid")||"N/A")+" ")])],1),s("v-row",{attrs:{"no-gutters":""}},[s("v-col",{attrs:{cols:"6"}},[t._v("CIT Number")]),s("v-col",{attrs:{cols:"6"}},[t._v(": "+t._s(t.get(t.payrollDetails.employee.legal_info,"cit_number")||"N/A")+" ")])],1)],1),s("v-col",{staticClass:"py-0 pl-1 text-center",attrs:{cols:"6"}},[s("v-alert",{staticClass:"rounded-0 text-body-2 px-0 py-1 ma-0",attrs:{dense:"",color:"grey lighten-2"}},[t._v(" No. of Pay Day ")]),s("v-alert",{staticClass:"rounded-0 text-body-2 px-0 py-1 ma-0",attrs:{dense:"",color:"very-light-blue"}},[t._v(" "+t._s(t.get(t.payrollDetails.attendance_details,"paid_days")||"-")+" ")]),s("v-alert",{staticClass:"\n          rounded-0\n          text-body-2\n          px-0\n          py-1\n          ma-0\n          grey--text\n          text--darken-2\n          font-weight-bold\n        ",attrs:{dense:"",color:"grey lighten-2"}},[t._v(" NET PAY ")]),s("v-alert",{staticClass:"rounded-0 text-body-2 px-0 ma-0 py-3 font-weight-bold",attrs:{dense:"",color:"very-light-blue"}},[t._v(" "+t._s(t.formatCurrency(t.get(t.payrollDetails.masked_values,"cash_in_hand")||t.totalEarnings-t.totalDeductions))+" ")])],1),s("v-col",{staticClass:"py-4",attrs:{cols:"12"}},[s("v-divider")],1),s("v-col",{staticClass:"py-0 pr-1",attrs:{cols:"12"}},[s("v-data-table",{attrs:{headers:t.leaveDetails.headers,items:t.payrollDetails.leave_details,"hide-default-footer":"","mobile-breakpoint":0,dense:""},scopedSlots:t._u([{key:"item",fn:function(e){return[s("tr",[s("td",{domProps:{textContent:t._s(e.item.leave_type)}}),s("td",{domProps:{textContent:t._s(["Time Off","Credit Hour"].includes(e.item.category)?t.getHourMinuteFromTotalMinute(e.item.opening):e.item.opening)}}),s("td",{domProps:{textContent:t._s(["Time Off","Credit Hour"].includes(e.item.category)?t.getHourMinuteFromTotalMinute(e.item.used):e.item.used)}}),s("td",{domProps:{textContent:t._s(["Time Off","Credit Hour"].includes(e.item.category)?t.getHourMinuteFromTotalMinute(e.item.closing):e.item.closing)}})])]}}])},[s("template",{slot:"no-data"},[s("v-col",[t._v(" You have not consumed any Leave.")])],1)],2)],1),s("v-col",{attrs:{cols:"12"}},[s("v-row",[s("v-col",[s("v-data-table",{attrs:{headers:t.attendanceDetails.headers,items:t.attendanceDetails.items,"hide-default-footer":"","mobile-breakpoint":0,dense:""},scopedSlots:t._u([{key:"item",fn:function(e){return[s("tr",[s("td",{domProps:{textContent:t._s(e.item.text)}}),t.payrollDetails.attendance_details?s("td",{domProps:{textContent:t._s(t.payrollDetails.attendance_details[e.item.value])}}):t._e()])]}}])},[s("template",{slot:"no-data"},[s("data-table-no-data",{attrs:{loading:t.loading}})],1)],2)],1),s("v-col",[s("v-data-table",{attrs:{headers:t.overtimeDetails.headers,items:t.overtimeDetails.items,"hide-default-footer":"","mobile-breakpoint":0,dense:""},scopedSlots:t._u([{key:"item",fn:function(e){return[s("tr",[s("td",{domProps:{textContent:t._s(e.item.text)}}),t.payrollDetails.hourly_attendance?s("td",[t.payrollDetails.hourly_attendance[e.item.value]?s("div",{domProps:{textContent:t._s(t.payrollDetails.hourly_attendance[e.item.value])}}):t.payrollDetails[e.item.value]?s("div",[t._v(" "+t._s(t.payrollDetails[e.item.value])+" ")]):s("div",{domProps:{textContent:t._s("-")}})]):t._e()])]}}])},[s("template",{slot:"no-data"},[s("data-table-no-data",{attrs:{loading:t.loading}})],1)],2)],1)],1)],1),s("v-col",{staticClass:"text-center text-caption",attrs:{cols:"12"}},[s("div",[t._v("(Private and Confidential)")]),s("div",[t._v(" This is a system generated pay-slip and requires no signature. ")])]),t.payrollDetails.payslip_note?s("v-col",{staticClass:"text-caption py-0",attrs:{cols:"12"}},[t._v(" NOTE: "+t._s(t.payrollDetails.payslip_note)+" ")]):t._e(),t.payrollDetails.user_note?s("v-col",{staticClass:"text-caption",attrs:{cols:"12"}},[t._v(" USER NOTE: "+t._s(t.payrollDetails.user_note)+" ")]):t._e()],1):t._e()],1)},o=[],r=(s("4de4"),s("caad"),s("2532"),s("d81d"),s("cf45")),l=s("ce0c"),n=s("c197"),i={components:{DefaultSvgLoader:n["default"]},props:{payrollDetails:{type:Object,required:!0},reports:{type:Array,required:!0},payrollDate:{type:String,required:!0},loading:{type:Boolean,required:!0}},data:function(){return{leaveDetails:{headers:[{text:"Leaves",sortable:!1},{text:"Initial",sortable:!1},{text:"Used",sortable:!1},{text:"Closing",sortable:!1}]},attendanceDetails:{headers:[{text:"Attendance",sortable:!1},{text:"Days",sortable:!1}],items:[{text:"Working Days",value:"working_days"},{text:"Worked Days",value:"worked_days"},{text:"Absent Days",value:"absent_days"},{text:"Leave Days",value:"leave_days"},{text:"Leave Days on Workdays",value:"leave_days_on_workdays"},{text:"Leave Without Pay",value:"unpaid_leave_days"},{text:"Days Deduction from Penalty",value:"days_deduction_from_penalty"}]},overtimeDetails:{headers:[{text:"Particulars",sortable:!1},{text:"Details",sortable:!1}],items:[{text:"Total Worked Hours",value:"total_worked_hours"},{text:"Actual Overtime Hours",value:"actual_overtime_hours"},{text:"Normalized Overtime",value:"normalized_overtime_hours"},{text:"Expected Work Hours",value:"expected_working_hours"},{text:"Lost Hours",value:"lost_hours"}]},earningHeadings:[],deductionHeadings:[]}},computed:{earnings:function(){var t=this;return this.reports.filter((function(e){return t.earningHeadings.includes(e.heading_id)}))},totalEarnings:function(){return this.earnings.map((function(t){return t.amount})).reduce((function(t,e){return t+e}),0)},deductions:function(){var t=this;return this.reports.filter((function(e){return t.deductionHeadings.includes(e.heading_id)}))},totalDeductions:function(){return this.deductions.map((function(t){return t.amount})).reduce((function(t,e){return t+e}),0)}},created:function(){this.getHeadings()},methods:{formatCurrency:r["d"],getHourMinuteFromTotalMinute:l["a"],getDifference:function(t,e){var s=e-t;return this.formatCurrency(Math.abs(s))},getHeadings:function(){var t=this,e="payroll/".concat(this.getOrganizationSlug,"/payslip-setting/?as=hr");this.$http.get(e).then((function(e){e.length&&(e[0].headings&&(t.earningHeadings=e[0].headings),e[1].headings&&(t.deductionHeadings=e[1].headings))}))}}},c=i,d=s("2877"),u=s("6544"),v=s.n(u),p=s("0798"),h=s("62ad"),g=s("8fea"),m=s("ce7e"),_=s("0fd9b"),y=Object(d["a"])(c,a,o,!1,null,null,null);e["default"]=y.exports;v()(y,{VAlert:p["a"],VCol:h["a"],VDataTable:g["a"],VDivider:m["a"],VRow:_["a"]})},c197:function(t,e,s){"use strict";s.r(e);var a=function(){var t=this,e=t.$createElement,s=t._self._c||e;return s("div",{class:t.divClass},[s("v-img",{class:t.imgClass,attrs:{src:"/svg/three-dots.svg",height:t.height,contain:""}}),s("h3",{staticClass:"text-center grey--text",domProps:{textContent:t._s(t.message)}})],1)},o=[],r={props:{message:{type:String,default:"Please wait. Fetching data just for you ..."},divClass:{type:String,default:"pa-12"},imgClass:{type:String,default:"my-6"},height:{type:String,default:"20"}},data:function(){return{}}},l=r,n=s("2877"),i=s("6544"),c=s.n(i),d=s("adda"),u=Object(n["a"])(l,a,o,!1,null,null,null);e["default"]=u.exports;c()(u,{VImg:d["a"]})},ce0c:function(t,e,s){"use strict";s.d(e,"b",(function(){return o})),s.d(e,"c",(function(){return l})),s.d(e,"a",(function(){return n}));var a=s("3835");s("d3b7"),s("25f0"),s("ac1f"),s("1276");function o(t,e){if(!t&&0!==t)return"N/A";var s=parseInt(t/3600),a=parseInt(t%3600/60);return r(s,a,e)}function r(t,e,s){var a=e.toString().length<2&&e<10?"0":"",o=t.toString().length<2&&t<10?"0":"",r=a+e,l=o+t;return":"===s?l+":"+r:0===t?r+" Minutes":l+" Hours "+r+" Minutes"}function l(t){if(!t)return"N/A";if("00:00:00"===t)return"N/A";var e=t.split(":"),s=Object(a["a"])(e,3),o=s[0],r=s[1],l=s[2];return"00"===o&&"00"===r?l+" Seconds":"00"===o?r+" Minutes":o+" Hours "+r+" Minutes"}function n(t){if(isNaN(parseInt(t)))return"-";var e=parseInt(t/60);e.toString().length<2&&(e="0"+e.toString());var s=parseInt(t%60);return s.toString().length<2&&(s="0"+s.toString()),e+":"+s}}}]);