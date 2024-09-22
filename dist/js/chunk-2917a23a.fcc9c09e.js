(window["webpackJsonp"]=window["webpackJsonp"]||[]).push([["chunk-2917a23a"],{"1fca":function(t,e,s){"use strict";s.d(e,"a",(function(){return o})),s.d(e,"c",(function(){return r})),s.d(e,"b",(function(){return l}));var a=s("30ef"),n=s.n(a);function i(t,e){return{render:function(t){return t("div",{style:this.styles,class:this.cssClasses},[t("canvas",{attrs:{id:this.chartId,width:this.width,height:this.height},ref:"canvas"})])},props:{chartId:{default:t,type:String},width:{default:400,type:Number},height:{default:400,type:Number},cssClasses:{type:String,default:""},styles:{type:Object},plugins:{type:Array,default:function(){return[]}}},data:function(){return{_chart:null,_plugins:this.plugins}},methods:{addPlugin:function(t){this.$data._plugins.push(t)},generateLegend:function(){if(this.$data._chart)return this.$data._chart.generateLegend()},renderChart:function(t,s){if(this.$data._chart&&this.$data._chart.destroy(),!this.$refs.canvas)throw new Error("Please remove the <template></template> tags from your chart component. See https://vue-chartjs.org/guide/#vue-single-file-components");this.$data._chart=new n.a(this.$refs.canvas.getContext("2d"),{type:e,data:t,options:s,plugins:this.$data._plugins})}},beforeDestroy:function(){this.$data._chart&&this.$data._chart.destroy()}}}var o=i("bar-chart","bar"),r=i("horizontalbar-chart","horizontalBar"),l=i("doughnut-chart","doughnut");i("line-chart","line"),i("pie-chart","pie"),i("polar-chart","polarArea"),i("radar-chart","radar"),i("bubble-chart","bubble"),i("scatter-chart","scatter")},"2be4":function(t,e,s){"use strict";var a,n,i=s("1fca"),o={extends:i["b"],props:{chartData:{type:Object,required:!0},responsive:{type:Boolean,default:!0},chartTitle:{type:String,default:""},displayLegend:{type:Boolean,default:!1},padding:{type:Object,default:function(){return{left:50,right:50,top:30,bottom:20}}},options:{type:Object,default:function(){return{responsive:!0,maintainAspectRatio:!1,layout:{padding:{}},animation:{animateScale:!0,animateRotate:!0},legend:{display:!1,position:"right"},title:{display:!0,text:""}}}}},mounted:function(){this.options.legend.display=this.displayLegend,this.options.responsive=this.responsive,this.options.title.text=this.chartTitle,this.options.layout.padding=this.padding,this.options.onClick=this.handle,this.renderChart(this.chartData,this.options)},methods:{handle:function(t,e){if(e&&e.length>0){var s=e[0];this.$emit("click",s._index)}}}},r=o,l=s("2877"),c=Object(l["a"])(r,a,n,!1,null,null,null);e["a"]=c.exports},ce0c:function(t,e,s){"use strict";s.d(e,"b",(function(){return n})),s.d(e,"c",(function(){return o})),s.d(e,"a",(function(){return r}));var a=s("3835");s("d3b7"),s("25f0"),s("ac1f"),s("1276");function n(t,e){if(!t&&0!==t)return"N/A";var s=parseInt(t/3600),a=parseInt(t%3600/60);return i(s,a,e)}function i(t,e,s){var a=e.toString().length<2&&e<10?"0":"",n=t.toString().length<2&&t<10?"0":"",i=a+e,o=n+t;return":"===s?o+":"+i:0===t?i+" Minutes":o+" Hours "+i+" Minutes"}function o(t){if(!t)return"N/A";if("00:00:00"===t)return"N/A";var e=t.split(":"),s=Object(a["a"])(e,3),n=s[0],i=s[1],o=s[2];return"00"===n&&"00"===i?o+" Seconds":"00"===n?i+" Minutes":n+" Hours "+i+" Minutes"}function r(t){if(isNaN(parseInt(t)))return"-";var e=parseInt(t/60);e.toString().length<2&&(e="0"+e.toString());var s=parseInt(t%60);return s.toString().length<2&&(s="0"+s.toString()),e+":"+s}},daca:function(t,e,s){"use strict";s.r(e);var a=function(){var t=this,e=t.$createElement,s=t._self._c||e;return s("v-card",[s("vue-card-title",{attrs:{title:"Employment Overview",subtitle:"Employment Overview of "+t.userInfo.user.name.partial,icon:"mdi-shield-account-outline"}}),s("v-divider"),s("v-card-text",[s("task-details",{attrs:{as:t.as}}),s("v-divider"),s("attendance-details",{attrs:{as:t.as}}),s("v-divider"),s("leave-details",{attrs:{as:t.as}}),s("v-divider"),s("employment-history",{attrs:{as:t.as}}),t.canResign?s("v-divider"):t._e(),t.canResign?s("resignation"):t._e()],1)],1)},n=[],i=(s("caad"),function(){var t=this,e=t.$createElement,s=t._self._c||e;return t.loading?t._e():s("v-row",[s("v-col",{staticClass:"text-h6 font-weight-bold",attrs:{cols:"12"}},[t._v(" Attendance Details ")]),s("v-col",{staticClass:"text-center"},[s("div",{staticClass:"pb-2"},[t._v("Punctuality")]),s("div",[s("v-progress-circular",{staticClass:"font-weight-bold pointer",attrs:{value:t.attendanceDetails.punctuality,color:t.getColor(t.attendanceDetails.punctuality),size:"90",width:"12",rotate:"-90"},on:{click:function(e){return t.openPunctualityDetail()}}},[t.attendanceDetails.punctuality?s("div",[t._v(" "+t._s(t.attendanceDetails.punctuality.toFixed(2)+"%")+" ")]):s("div",[t._v("0%")])])],1)]),s("v-col",[s("div",[s("div",{domProps:{textContent:t._s("Working Days")}}),s("div",{staticClass:"text-h6 primary--text font-weight-bold"},[s("span",{domProps:{textContent:t._s(t.attendanceDetails.working_days)}}),s("span",{staticClass:"text-subtitle-2 primary--text darken-4 font-weight-bold",domProps:{textContent:t._s("DAYS")}})])]),s("div",[s("div",{domProps:{textContent:t._s("Worked Days")}}),s("div",{staticClass:"text-h6",class:t.attendanceDetails.present_days>=t.attendanceDetails.working_days?"success--text":"danger--text"},[s("strong",{domProps:{textContent:t._s(t.attendanceDetails.present_days)}}),s("span",{staticClass:"text-subtitle-2 darken-4 font-weight-bold",domProps:{textContent:t._s("DAYS")}})])])]),s("v-col",[s("div",[s("div",{domProps:{textContent:t._s("Total Hours Work")}}),s("div",[s("span",{staticClass:"text-h6 success--text font-weight-bold",domProps:{textContent:t._s(t.getHours(t.attendanceDetails.total_worked_minutes))}}),s("span",{staticClass:"text-subtitle-2 success--text font-weight-bold",domProps:{textContent:t._s("HH :")}}),s("span",{staticClass:"text-h6 success--text font-weight-bold",domProps:{textContent:t._s(t.getMinutes(t.attendanceDetails.total_worked_minutes))}}),s("span",{staticClass:"text-subtitle-2 success--text font-weight-bold",domProps:{textContent:t._s("MM")}})])]),s("div",[s("div",{domProps:{textContent:t._s("Expected Work Hours")}}),s("div",[s("span",{staticClass:"text-h6 primary--text font-weight-bold",domProps:{textContent:t._s(t.getHours(t.attendanceDetails.expected_minutes))}}),s("span",{staticClass:"text-subtitle-2 primary--text font-weight-bold",domProps:{textContent:t._s("HH :")}}),s("span",{staticClass:"text-h6 primary--text font-weight-bold",domProps:{textContent:t._s(t.getMinutes(t.attendanceDetails.expected_minutes))}}),s("span",{staticClass:"text-subtitle-2 primary--text font-weight-bold",domProps:{textContent:t._s("MM")}})])])]),s("v-col",[s("div",[s("div",{domProps:{textContent:t._s("Overtime Claimed")}}),s("div",{staticClass:"brown--text darken-4"},[s("span",{staticClass:"text-h6 font-weight-bold",domProps:{textContent:t._s(t.getHours(t.attendanceDetails.overtime_claimed))}}),s("span",{staticClass:"text-subtitle-2 font-weight-bold",domProps:{textContent:t._s("HH :")}}),s("span",{staticClass:"text-h6 font-weight-bold",domProps:{textContent:t._s(t.getMinutes(t.attendanceDetails.overtime_claimed))}}),s("span",{staticClass:"text-subtitle-2 font-weight-bold",domProps:{textContent:t._s("MM")}})])]),t.attendanceDetails.total_lost_minutes?s("div",[s("div",{domProps:{textContent:t._s(t.attendanceDetails.total_lost_minutes.toString().includes("-")?"Hours Surplus":"Hours Lost")}}),t.attendanceDetails.total_lost_minutes?s("div",{class:t.attendanceDetails.total_lost_minutes.toString().includes("-")?"success--text":"danger--text"},[s("span",{staticClass:"text-h6 font-weight-bold",domProps:{textContent:t._s(t.getHours(Math.abs(t.attendanceDetails.total_lost_minutes)))}}),s("span",{staticClass:"text-subtitle-2 font-weight-bold",domProps:{textContent:t._s("HH :")}}),s("span",{staticClass:"text-h6 font-weight-bold",domProps:{textContent:t._s(t.getMinutes(Math.abs(t.attendanceDetails.total_lost_minutes)))}}),s("span",{staticClass:"text-subtitle-2 font-weight-bold",domProps:{textContent:t._s("MM")}})]):t._e()]):t._e()])],1)}),o=[],r=s("5530"),l=(s("99af"),s("2f62")),c={props:{as:{type:String,default:""}},data:function(){return{attendanceDetails:{},loading:!1}},computed:Object(r["a"])({},Object(l["c"])({orgSlug:"organization/getCurrentOrganizationSlug"})),created:function(){this.fetchAttendanceDetails()},methods:{fetchAttendanceDetails:function(){var t=this;this.loading=!0;var e=this.$route.params.id===this.getAuthStateUserId?this.orgSlug:this.getOrganizationSlug;this.$http.get("/attendance/".concat(e,"/reports/user-overview/").concat(this.$route.params.id,"/?fiscal_year=current&as=").concat(this.as)).then((function(e){t.attendanceDetails=e,t.loading=!1}))},getHours:function(t,e){var s=parseInt(t%60),a=parseInt(t-s)/60;return"hoursAndMinute"===e?0===a?s+" mins":a+" hrs : "+s+" mins":a},getMinutes:function(t,e){var s=parseInt(t%60),a=parseInt(t-s)/60;return"hoursAndMinute"===e?0===a?s+" mins":a+" hrs : "+s+" mins":s},openPunctualityDetail:function(){var t=this.$route.params.slug?"admin-slug-attendance-reports-monthly-attendance":"user-attendance-reports-monthly-attendance";this.$router.push({name:t,params:{slug:this.$route.params.slug},query:{user:this.$route.params.id}})},getColor:function(t){return t<50?"danger":t<80&&t>50?"warning":t>80?"success":void 0}}},d=c,u=s("2877"),p=s("6544"),h=s.n(p),g=s("62ad"),v=s("490a"),f=s("0fd9b"),m=Object(u["a"])(d,i,o,!1,null,null,null),_=m.exports;h()(m,{VCol:g["a"],VProgressCircular:v["a"],VRow:f["a"]});var C=function(){var t=this,e=t.$createElement,s=t._self._c||e;return s("v-row",{attrs:{align:"center"}},[s("v-col",{staticClass:"text-h6 font-weight-bold",attrs:{cols:"12"}},[t._v(" Leave Details ")]),t.loading||0===t.data.length?t._e():s("v-col",{staticClass:"py-0",attrs:{md:"3"}},[s("doughnut",{attrs:{"chart-data":t.doughnutChartData,width:190,height:200,responsive:!1,padding:{left:0,right:10,top:10,bottom:50}}})],1),t.loading||0===t.data.length?t._e():s("v-col",{attrs:{md:"9"}},[s("v-row",t._l(t.data,(function(e){return s("v-col",{key:e.type,attrs:{md:"4"}},[s("v-tooltip",{attrs:{bottom:""},scopedSlots:t._u([{key:"activator",fn:function(a){var n=a.on;return[s("div",t._g({},n),[t._v(" "+t._s(t._f("truncate")(e.type,20))+" ")])]}}],null,!0)},[s("span",[t._v(t._s(e.type))])]),s("div",{staticClass:"mt-n4 ml-n3"},[s("v-icon",{attrs:{color:e.color,size:"50"},domProps:{textContent:t._s("mdi-minus")}})],1),s("div",{staticClass:"mt-n5"},[s("v-tooltip",{attrs:{bottom:""},scopedSlots:t._u([{key:"activator",fn:function(a){var n=a.on;return[s("span",t._g({},n),[s("span",{staticClass:"text-h6 blue-grey--text darken-4"},[t._v(" "+t._s("Credit Hour"===e.category?t.getHourMinuteFromTotalMinute(e.consumed_balance):e.consumed_balance)+" ")]),s("span",{staticClass:"\n                    text-subtitle-2\n                    blue-grey--text\n                    darken-4\n                    font-weight-bold\n                  "},[t._v(" "+t._s("Credit Hour"!==e.category?e.consumed_balance>1?"DAYS":"DAY":"")+" ")])])]}}],null,!0)},[s("span",[t._v(" Consumed Leave Balance ")])]),s("span",{staticClass:"text-h6"},[t._v("|")]),s("v-tooltip",{attrs:{bottom:""},scopedSlots:t._u([{key:"activator",fn:function(a){var n=a.on;return[s("span",t._g({},n),[s("span",{staticClass:"text-h6 primary--text font-weight-bold"},[t._v(" "+t._s("Credit Hour"===e.category?t.getHourMinuteFromTotalMinute(e.usable_balance):e.usable_balance)+" ")]),s("span",{staticClass:"text-subtitle-2 primary--text font-weight-bold"},[t._v(" "+t._s("Credit Hour"!==e.category?e.consumed_balance>1?"DAYS":"DAY":"")+" ")])])]}}],null,!0)},[s("span",[t._v(" Remaining Leave Balance ")])])],1)],1)})),1)],1),t.loading||0!==t.data.length?t._e():s("v-col",{staticClass:"text-center pa-0 pb-4"},[s("span",{staticClass:"text-subtitle-1 green--text font-weight-bold"},[t._v("Applied Leave Detail not found.")])])],1)},x=[],y=(s("159b"),s("d81d"),s("2be4")),b=s("ce0c"),k={components:{Doughnut:y["a"]},props:{as:{type:String,default:""}},data:function(){return{loading:!1,userId:this.$route.params.id,backgroundColor:["#47ADFB","#34BFA3","#F4516C","#FFB822","#455A64","#3366E6","#43A047","#FFEA00","#716ACA"],data:[],doughnutChartData:{labels:[],datasets:[{label:"Leave Details",backgroundColor:[],data:[]}]}}},mounted:function(){var t=this;this.loading=!0,this.$http.get("/leave/".concat(this.userId,"/detail/?as=").concat(this.as)).then((function(e){t.data=e.results,t.data.forEach((function(e,s){e.color=t.backgroundColor[s]})),t.doughnutChartData.datasets[0].data=e.results.map((function(t){return t.consumed_balance})),t.doughnutChartData.datasets[0].backgroundColor=t.backgroundColor,t.doughnutChartData.labels=e.results.map((function(t){return t.type})),t.loading=!1}))},methods:{getHourMinuteFromTotalMinute:b["a"]}},w=k,D=s("132d"),P=s("3a2f"),$=Object(u["a"])(w,C,x,!1,null,null,null),A=$.exports;h()($,{VCol:g["a"],VIcon:D["a"],VRow:f["a"],VTooltip:P["a"]});var S=function(){var t=this,e=t.$createElement,s=t._self._c||e;return s("v-row",[s("v-col",{staticClass:"text-h6 font-weight-bold py-0",attrs:{cols:"12"}},[t._v(" Task Details ")]),s("v-col",{staticClass:"py-0 text-center",attrs:{cols:"12"}},[s("v-row",[s("v-col",[s("div",{staticClass:"text-h4 pointer info--text",domProps:{textContent:t._s(t.taskDetails["all_tasks"])},on:{click:function(e){return t.openAssignedTask()}}}),s("div",{domProps:{textContent:t._s("All Tasks")}})]),s("v-col",[s("div",{staticClass:"text-h4 pointer indigo--text",domProps:{textContent:t._s(t.taskDetails["pending"])},on:{click:function(e){return t.openAssignedTask("pending")}}}),s("div",{domProps:{textContent:t._s("Pending Tasks")}})]),s("v-col",[s("div",{staticClass:"text-h4 pointer warning--text",domProps:{textContent:t._s(t.taskDetails["in_progress"])},on:{click:function(e){return t.openAssignedTask("in_progress")}}}),s("div",{domProps:{textContent:t._s("In Progress Tasks")}})]),s("v-col",[s("div",{staticClass:"text-h4 pointer danger--text",domProps:{textContent:t._s(t.taskDetails["completed"])},on:{click:function(e){return t.openAssignedTask("completed")}}}),s("div",{domProps:{textContent:t._s("Completed Tasks")}})]),s("v-col",[s("div",{staticClass:"text-h4 pointer indigo--text",domProps:{textContent:t._s(t.taskDetails["closed_and_hold"])},on:{click:function(e){return t.openClosedHold("responsible")}}}),s("div",{domProps:{textContent:t._s("Closed & Onhold Tasks")}})])],1)],1),s("v-col",{staticClass:"text-center",attrs:{cols:"3"}},[s("div",{staticClass:"pb-2"},[t._v("Task Efficiency")]),s("v-progress-circular",{staticClass:"font-weight-bold",class:t.$route.params.slug?"":"pointer",attrs:{value:t.taskDetails.efficiency||0,color:t.getColor(t.taskDetails.efficiency),size:"90",rotate:"-90",width:"12"},on:{click:function(e){return t.openEfficiencyPage()}}},[t.taskDetails.efficiency?s("div",[t._v(" "+t._s(t.taskDetails.efficiency.toFixed(2)+"%")+" ")]):s("div",{staticClass:"grey--text"},[t._v("N/A")])])],1),s("v-col",{staticClass:"pt-10",attrs:{cols:"2"}},[s("div",[s("div",{domProps:{textContent:t._s("Average Score")}}),t.taskDetails.average_score?s("div",{staticClass:"text-h6 font-weight-bold primary--text"},[t._v(" "+t._s(t.taskDetails.average_score.toFixed(2)||"N/A")+" ")]):s("div",{staticClass:"grey--text"},[t._v("N/A")])]),s("div",[s("div",{domProps:{textContent:t._s("Total Score")}}),t.taskDetails.total_score?s("div",{staticClass:"text-h6 font-weight-bold primary--text",domProps:{textContent:t._s(t.taskDetails.total_score)}}):s("div",[t._v("N/A")])])]),t.taskDetails.result_area_efficiency?s("v-col",{staticClass:"py-0",attrs:{cols:"6"}},[s("v-col",{staticClass:"py-0"},[s("v-row",{staticClass:"py-0"},[s("v-divider",{attrs:{vertical:""}}),s("v-col",{attrs:{md:"8"}},[t._v(" Result Areas ")]),s("v-divider",{attrs:{vertical:""}}),s("v-col",{attrs:{md:"3"}},[t._v(" Efficiency ")])],1),t._l(Object.keys(t.taskDetails.result_area_efficiency),(function(e,a){return s("v-row",{key:a},[s("v-divider",{attrs:{vertical:""}}),s("v-col",{staticClass:"primary--text font-weight-bold py-0",attrs:{md:"8"}},[s("v-tooltip",{attrs:{top:""},scopedSlots:t._u([{key:"activator",fn:function(n){var i=n.on;return[s("span",t._g({},i),[t._v(" "+t._s(a+1+". ")+" "+t._s(t._f("truncate")(e,25))+" ")])]}}],null,!0)},[s("span",[t._v(" "+t._s(a+1+". "+e)+" ")])])],1),s("v-divider",{attrs:{vertical:""}}),s("v-col",{staticClass:"py-0 font-weight-bold",attrs:{md:"3"}},[t._v(" "+t._s(t.taskDetails.result_area_efficiency[e].toFixed(2)+"%")+" ")])],1)}))],2)],1):t._e()],1)},H=[],T={props:{as:{type:String,default:""}},data:function(){return{taskDetails:{}}},created:function(){this.fetchTaskDetails()},methods:{fetchTaskDetails:function(){var t=this;this.$http.get("/task/detail/user/".concat(this.$route.params.id,"/?as=").concat(this.as)).then((function(e){t.taskDetails=e}))},openAssignedTask:function(t){var e=this.$route.params.slug?"admin-slug-task-reports-all-task":"user-task-assigned-to-me";this.$router.push({name:e,params:{slug:this.$route.params.slug},query:{user:this.$route.params.id,pre:t}})},openEfficiencyPage:function(){this.$route.params.slug||this.$router.push({name:"user-task-reports-efficiency"})},openClosedHold:function(t){this.$route.params.slug?this.$router.push({name:"admin-slug-task-reports-closed-hold",params:{slug:this.$route.params.slug},query:{as:t}}):this.$router.push({name:"user-task-closed-and-hold",query:{as:t}})},getColor:function(t){return t<50?"danger":t<80&&t>50?"warning":t>80?"success":void 0}}},M=T,O=s("ce7e"),I=Object(u["a"])(M,S,H,!1,null,null,null),V=I.exports;h()(I,{VCol:g["a"],VDivider:O["a"],VProgressCircular:v["a"],VRow:f["a"],VTooltip:P["a"]});var E=function(){var t=this,e=t.$createElement,s=t._self._c||e;return s("v-row",[s("v-col",{staticClass:"text-h6 font-weight-bold",attrs:{cols:"12"},domProps:{textContent:t._s("Employment History")}}),s("v-col",[s("v-timeline",{attrs:{dense:""}},[t._l(t.employmentHistory,(function(e,a){return[s("v-timeline-item",{key:a,attrs:{color:"success",small:""}},[s("div",{staticClass:"grey--text font-weight-bold"},[t._v(" "+t._s(e.start_date)+" ")]),s("div",{staticClass:"text-body-1 font-weight-bold"},[t._v(" "+t._s(e.text)+" ")]),s("div",{staticClass:"grey--text font-weight-bold"},[t._v(" "+t._s(e.change_type)+" ")])])]}))],2)],1)],1)},j=[],R={props:{as:{type:String,default:""}},data:function(){return{employmentHistory:[]}},created:function(){this.fetchEmploymentHistory()},methods:{fetchEmploymentHistory:function(){var t=this;this.$http.get("/users/".concat(this.$route.params.id,"/experience-history/?as=").concat(this.as)).then((function(e){t.employmentHistory=e.results}))}}},F=R,L=s("8414"),N=s("1e06"),z=Object(u["a"])(F,E,j,!1,null,null,null),B=z.exports;h()(z,{VCol:g["a"],VRow:f["a"],VTimeline:L["a"],VTimelineItem:N["a"]});var q=function(){var t=this,e=t.$createElement,s=t._self._c||e;return s("v-row",{attrs:{align:"center"}},[s("v-col",{attrs:{cols:"4"}},[s("v-btn",{staticClass:"danger white--text",attrs:{depressed:"",small:""},on:{click:function(e){return t.openResignationPage()}}},[t._v(" Resign/Terminate the contract ")])],1)],1)},Y=[],U={computed:Object(r["a"])({},Object(l["c"])({getAuthStateUserId:"auth/getAuthStateUserId"})),methods:{openResignationPage:function(){this.$router.push({name:"user-offboarding-resignation",params:{id:this.getAuthStateUserId}})}}},W=U,J=s("8336"),G=Object(u["a"])(W,q,Y,!1,null,null,null),K=G.exports;h()(G,{VBtn:J["a"],VCol:g["a"],VRow:f["a"]});var Q={components:{EmploymentHistory:B,TaskDetails:V,LeaveDetails:A,AttendanceDetails:_,Resignation:K},props:{userInfo:{type:Object,required:!0},as:{type:String,default:""}},data:function(){return{canResign:!1}},created:function(){var t=this;["hr","supervisor"].includes(this.as)||this.$http.options("/hris/".concat(this.getOrganizationSlug,"/resignation/")).then((function(e){t.canResign=e.can_resign}))}},X=Q,Z=s("b0af"),tt=s("99d9"),et=Object(u["a"])(X,a,n,!1,null,null,null);e["default"]=et.exports;h()(et,{VCard:Z["a"],VCardText:tt["c"],VDivider:O["a"]})}}]);