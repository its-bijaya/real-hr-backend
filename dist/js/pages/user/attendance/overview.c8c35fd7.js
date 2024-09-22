(window["webpackJsonp"]=window["webpackJsonp"]||[]).push([["pages/user/attendance/overview"],{"0a18":function(t,e,n){"use strict";n.r(e);var r=function(){var t=this,e=t.$createElement,n=t._self._c||e;return n("vue-page-wrapper",{attrs:{title:t.htmlTitle,"bread-crumbs":t.breadCrumbItems}},[n("v-row",[n("v-col",{attrs:{cols:"12"}},[n("information-bar",{on:{"update:appliedFilterText":function(e){t.appliedFilterText=e},filter:function(e){t.filters=e}}})],1),n("v-col",{attrs:{cols:"12",md:"4"}},[n("adjustment",{attrs:{filters:t.filters}})],1),n("v-col",{attrs:{cols:"12",md:"4"}},[n("attendance-behaviour",{attrs:{filters:t.filters}})],1),n("v-col",{attrs:{cols:"12",md:"4"}},[n("overtime",{attrs:{filters:t.filters}})],1),n("v-col",{attrs:{cols:"12",md:"4"}},[n("break-in-out",{attrs:{filters:t.filters,"applied-filter-text":t.appliedFilterText}})],1)],1)],1)},a=[],i=n("0549"),o=function(){var t=this,e=t.$createElement,n=t._self._c||e;return n("v-card",{attrs:{align:"center"}},[n("v-row",{staticClass:"text-caption grey--text",attrs:{dense:"",align:"center",justify:"center"}},[n("v-col",{staticClass:"px-3 text-left",attrs:{md:"4",sm:"12",cols:"12"}},[n("v-row",{attrs:{dense:""}},[n("v-col",[n("div",{domProps:{textContent:t._s("Total Worked Hours")}})]),n("v-col",[n("div",{staticClass:"success--text",domProps:{textContent:t._s(t.getHoursAndMinutes(t.summary.total_worked_minutes))}})])],1),n("v-row",{attrs:{dense:""}},[n("v-col",[n("div",{domProps:{textContent:t._s("Expected Working Hours")}})]),n("v-col",[n("div",{staticClass:"blue--text",domProps:{textContent:t._s(t.getHoursAndMinutes(t.summary.expected_minutes))}})])],1),n("v-row",{attrs:{dense:""}},[n("v-col",[n("div",{domProps:{textContent:t._s(t.summary.total_lost_minutes>0?"Total Lost Hours":"Total Extra Hours")}})]),n("v-col",[n("div",{class:t.summary.total_lost_minutes>0?"red--text":"green--text",domProps:{textContent:t._s(t.getHoursAndMinutes(Math.abs(t.summary.total_lost_minutes)))}})])],1)],1),n("v-divider",{attrs:{vertical:""}}),n("v-col",[n("div",{staticClass:"primary--text text-h4",domProps:{textContent:t._s(null===t.summary["absent_days"]?"N/A":t.summary["absent_days"])}}),n("div",{domProps:{textContent:t._s("Absent Days")}})]),n("v-col",[n("div",{staticClass:"info--text text-h4",domProps:{textContent:t._s(t.summary["present_days"])}}),n("div",{domProps:{textContent:t._s("Present Days")}})]),n("v-col",[n("div",{staticClass:"warning--text text-h4",domProps:{textContent:t._s(t.summary["working_days"])}}),n("div",{domProps:{textContent:t._s("Total Working Days")}})]),n("v-col",[n("v-progress-circular",{attrs:{rotate:1,size:40,width:7,value:""+Math.floor(t.summary.punctuality),color:t.getProgressColor(t.summary.punctuality)}},[t._v(" "+t._s(""+Math.floor(t.summary.punctuality))+" ")]),n("div",{domProps:{textContent:t._s("Punctuality")}})],1),n("v-col",{staticClass:"pt-4"},[n("date-filter-menu",{attrs:{default:"This Month","no-input":""},on:{input:function(e){t.getAttendanceOverview(),t.$emit("filter",e)},update:function(e){return t.$emit("update:appliedFilterText",e.dateStatus)}},model:{value:t.dateFilter,callback:function(e){t.dateFilter=e},expression:"dateFilter"}})],1)],1)],1)},s=[],c=n("ac94"),d=(n("99af"),{getOverview:function(t,e){return"/attendance/".concat(t,"/reports/user-overview/").concat(e,"/")},getAttendanceBehaviour:function(t,e){return"/attendance/".concat(t,"/reports/user-overview/").concat(e,"/behavior/")}}),l={components:{DateFilterMenu:c["a"]},props:{appliedFilterText:{type:String,default:"This Month"}},data:function(){return{summary:{},dateFilter:{start_date:"",end_date:""}}},methods:{getAttendanceOverview:function(){var t=this,e=d.getOverview(this.getOrganizationSlug,this.getAuthStateUserId);this.$http.get(e,{params:this.dateFilter}).then((function(e){t.summary=e}))},getHoursAndMinutes:function(t){if(null===t)return"N/A";if(t<60){var e=t>1?" Minutes ":" Minute ";return t+e}var n=t/60,r=Math.floor(n),a=60*(n-r),i=Math.round(a),o=i>1?" Minutes ":" Minute ",s=r>1?" Hours ":" Hour ";return r+s+i+o},getProgressColor:function(t){return t<50?"red":t<80?"orange":"green"}}},u=l,m=n("2877"),v=n("6544"),p=n.n(v),f=n("b0af"),h=n("62ad"),g=n("ce7e"),y=n("490a"),x=n("0fd9b"),C=Object(m["a"])(u,o,s,!1,null,null,null),_=C.exports;p()(C,{VCard:f["a"],VCol:h["a"],VDivider:g["a"],VProgressCircular:y["a"],VRow:x["a"]});var I=function(){var t=this,e=t.$createElement,n=t._self._c||e;return n("v-card",{attrs:{height:"100%"}},[n("vue-card-title",{attrs:{title:"Attendance Entries",subtitle:"Your attendance entry information",icon:"mdi-calendar-edit"}}),n("v-divider"),t.loading?n("v-progress-linear",{attrs:{indeterminate:"",height:"2"}}):t._e(),t.loading?n("v-col",t._l(3,(function(t){return n("list-loader",{key:t,attrs:{"primary-color":"#eee","secondary-color":"#d5d5d7"}})})),1):t._e(),t.loading?t._e():n("div",[n("v-list",{staticClass:"py-0"},[t._l(t.adjustments,(function(e,r,a){return[n("v-list-item",{key:a},[n("v-list-item-icon",[n("v-icon",{attrs:{size:"20"},domProps:{textContent:t._s(t.mapIcons[r])}})],1),n("v-list-item-content",[n("v-list-item-title",{domProps:{textContent:t._s(r)}})],1),n("v-list-item-action",[n("v-list-item-title",{class:t.mapColors[r]+"--text",domProps:{textContent:t._s(e)}})],1)],1),a+1<Object.keys(t.adjustments).length?n("v-divider",{key:"D-"+a}):t._e()]}))],2)],1)],1)},b=[],O=n("5530"),w=n("6e60"),A=n("e330"),k={components:{ListLoader:A["d"]},props:{filters:{type:Object,default:function(){return{}}}},data:function(){return{loading:!0,adjustments:{},mapColors:{Requested:"orange",Approved:"green",Forwarded:"purple",Denied:"pink"},mapIcons:{Requested:"mdi-dots-vertical",Approved:"mdi-check",Forwarded:"mdi-send-outline",Denied:"mdi-close"}}},watch:{filters:function(){this.getAttendanceAdjustments()}},methods:{getAttendanceAdjustments:function(){var t=this;this.loading=!0;var e=w["a"].getAdjustment(this.getOrganizationSlug);this.$http.get(e,{params:Object(O["a"])({user_id:this.getAuthStateUserId,limit:0},this.filters)}).then((function(e){t.adjustments={Requested:e.counts.Requested,Approved:e.counts.Approved,Forwarded:e.counts.Forwarded,Denied:e.counts.Declined},t.loading=!1}))}}},V=k,L=n("132d"),j=n("8860"),P=n("da13"),D=n("1800"),T=n("5d23"),S=n("34c3"),M=n("8e36"),B=Object(m["a"])(V,I,b,!1,null,null,null),F=B.exports;p()(B,{VCard:f["a"],VCol:h["a"],VDivider:g["a"],VIcon:L["a"],VList:j["a"],VListItem:P["a"],VListItemAction:D["a"],VListItemContent:T["a"],VListItemIcon:S["a"],VListItemTitle:T["c"],VProgressLinear:M["a"]});var R=function(){var t=this,e=t.$createElement,n=t._self._c||e;return n("v-card",{attrs:{height:"100%"}},[n("vue-card-title",{attrs:{title:"Attendance Behaviour",subtitle:"Your attendance behaviour information",icon:"mdi-chart-line"}}),n("v-divider"),t.loading?n("v-progress-linear",{attrs:{indeterminate:"",height:"2"}}):t._e(),t.loading?n("v-col",t._l(3,(function(t){return n("list-loader",{key:t,attrs:{"primary-color":"#eee","secondary-color":"#d5d5d7"}})})),1):t._e(),t.loading?t._e():n("div",[n("v-list",{staticClass:"py-0"},[t._l(t.attendanceBehaviour,(function(e,r,a){return[n("v-list-item",{key:a,staticClass:"py-2"},[n("v-list-item-content",[n("v-list-item-title",{domProps:{textContent:t._s(r)}})],1),n("v-list-item-action",[n("v-list-item-title",{domProps:{textContent:t._s(e)}})],1)],1),5!==a?n("v-divider",{key:"D-"+a}):t._e()]}))],2)],1)],1)},$=[],U={components:{ListLoader:A["d"]},props:{filters:{type:Object,default:function(){return{}}}},data:function(){return{loading:!0,attendanceBehaviour:{}}},watch:{filters:function(){this.getAttendanceBehaviour()}},methods:{getAttendanceBehaviour:function(){var t=this;this.loading=!0;var e=d.getAttendanceBehaviour(this.getOrganizationSlug,this.getAuthStateUserId);this.$http.get(e,{params:this.filters}).then((function(e){t.loading=!1,t.attendanceBehaviour={"Early In":e["Early In"],"Late In":e["Late In"],"Timely In":e["Timely In"],"Early Out":e["Early Out"],"Late Out":e["Late Out"],"Timely Out":e["Timely Out"]}}))}}},Y=U,q=Object(m["a"])(Y,R,$,!1,null,null,null),E=q.exports;p()(q,{VCard:f["a"],VCol:h["a"],VDivider:g["a"],VList:j["a"],VListItem:P["a"],VListItemAction:D["a"],VListItemContent:T["a"],VListItemTitle:T["c"],VProgressLinear:M["a"]});var H=function(){var t=this,e=t.$createElement,n=t._self._c||e;return n("v-card",{attrs:{height:"100%"}},[n("vue-card-title",{attrs:{title:"Overtime Overview",subtitle:"Your overtime information",icon:"mdi-alarm-plus"}}),n("v-divider"),t.loading?n("v-progress-linear",{attrs:{indeterminate:"",height:"2"}}):t._e(),t.loading?n("v-col",t._l(3,(function(t){return n("list-loader",{key:t,attrs:{"primary-color":"#eee","secondary-color":"#d5d5d7"}})})),1):t._e(),t.loading?t._e():n("div",[n("v-list",{staticClass:"py-0"},[t._l(t.overtimeInformation,(function(e,r,a){return[n("v-list-item",{key:r},[n("v-list-item-icon",[n("v-icon",{attrs:{size:"20"},domProps:{textContent:t._s(t.mapIcons[r])}})],1),n("v-list-item-content",[n("v-list-item-title",{domProps:{textContent:t._s(r)}})],1),n("v-list-item-action",[n("v-list-item-title",{class:t.mapColors[r]+"--text",domProps:{textContent:t._s(e||0)}})],1)],1),5!==a?n("v-divider",{key:"D-"+a}):t._e()]}))],2)],1)],1)},z=[],N=n("ad9d"),K={components:{ListLoader:A["d"]},props:{filters:{type:Object,default:function(){return{}}}},data:function(){return{loading:!0,overtimeInformation:{},mapColors:{Requested:"orange",Approved:"green",Confirmed:"cyan",Forwarded:"purple",Declined:"red",Unclaimed:"grey"},mapIcons:{Requested:"mdi-dots-vertical",Approved:"mdi-check",Confirmed:"mdi-check-all",Forwarded:"mdi-send-outline",Declined:"mdi-close",Unclaimed:"mdi-help-circle-outline"}}},watch:{filters:function(){this.getOvertimeInformation()}},methods:{getOvertimeInformation:function(){var t=this;this.loading=!0;var e=N["a"].getOvertime(this.getOrganizationSlug);this.$http.get(e,{params:Object(O["a"])(Object(O["a"])({},this.filters),{},{user:this.getAuthStateUserId})}).then((function(e){t.loading=!1,t.overtimeInformation={Requested:e.counts.Requested,Approved:e.counts.Approved,Confirmed:e.counts.Confirmed,Forwarded:e.counts.Forwarded,Declined:e.counts.Declined,Unclaimed:e.counts.Unclaimed}}))}}},W=K,G=Object(m["a"])(W,H,z,!1,null,null,null),J=G.exports;p()(G,{VCard:f["a"],VCol:h["a"],VDivider:g["a"],VIcon:L["a"],VList:j["a"],VListItem:P["a"],VListItemAction:D["a"],VListItemContent:T["a"],VListItemIcon:S["a"],VListItemTitle:T["c"],VProgressLinear:M["a"]});var Q=function(){var t=this,e=t.$createElement,n=t._self._c||e;return n("v-card",[n("vue-card-title",{attrs:{title:"Break In/Out",subtitle:"Your break in/out information",icon:"mdi-swap-horizontal"}}),n("v-divider"),t.loading?n("v-progress-linear",{attrs:{indeterminate:"",height:"2"}}):t._e(),t.loading?n("v-col",t._l(3,(function(t){return n("list-loader",{key:t,attrs:{"primary-color":"#eee","secondary-color":"#d5d5d7"}})})),1):n("v-list",{staticClass:"py-0"},[n("v-list-item",[n("v-list-item-content",[n("v-list-item-title",{staticClass:"grey--text",domProps:{textContent:t._s("Category")}})],1),n("v-list-item-content",[n("v-list-item-title",{staticClass:"grey--text",domProps:{textContent:t._s("Today")}})],1),n("v-list-item-action",[n("v-list-item-title",{staticClass:"grey--text",domProps:{textContent:t._s("Month")}})],1)],1),n("v-divider"),t._l(t.breakInOutInfo,(function(e,r,a){return[n("v-list-item",{key:r},[n("v-list-item-content",[n("v-list-item-title",{domProps:{textContent:t._s(r)}})],1),n("v-list-item-content",[n("v-list-item-title",{domProps:{textContent:t._s(e)}})],1),n("v-list-item-action",[n("v-list-item-title",{domProps:{textContent:t._s(t.breakInOutInfoInDateRange[r])}})],1)],1),4!==a?n("v-divider",{key:"D-"+a}):t._e()]}))],2)],1)},X=[],Z={components:{ListLoader:A["d"]},props:{filters:{type:Object,default:function(){return{}}},appliedFilterText:{type:String,default:"This Month"}},data:function(){return{loading:!0,headers:[{text:"Category",sortable:!1,align:"text-left"},{text:"Today",sortable:!1,align:"text-center"}],filterChoices:["Today","This Week","This Month","Last Month","This Year","Till Date"],breakInOutInfo:{},breakInOutInfoInDateRange:{}}},watch:{filters:function(){this.getBreakInOutInfoInDateRange()}},created:function(){this.getBreakInOutInfo()},methods:{getBreakInOutInfo:function(){var t=this,e={start_date:this.$dayjs().format("YYYY-MM-DD"),end_date:this.$dayjs().format("YYYY-MM-DD")},n="/attendance/".concat(this.getOrganizationSlug,"/reports/user-overview/").concat(this.getAuthStateUserId,"/break-out/");this.$http.get(n,{params:e}).then((function(e){t.breakInOutInfo=e}))},getBreakInOutInfoInDateRange:function(){var t=this;this.loading=!0;var e="/attendance/".concat(this.getOrganizationSlug,"/reports/user-overview/").concat(this.getAuthStateUserId,"/break-out/");this.$http.get(e,{params:this.filters}).then((function(e){t.loading=!1,t.breakInOutInfoInDateRange=e}))}}},tt=Z,et=Object(m["a"])(tt,Q,X,!1,null,null,null),nt=et.exports;p()(et,{VCard:f["a"],VCol:h["a"],VDivider:g["a"],VList:j["a"],VListItem:P["a"],VListItemAction:D["a"],VListItemContent:T["a"],VListItemTitle:T["c"],VProgressLinear:M["a"]});var rt={components:{VuePageWrapper:i["default"],InformationBar:_,Adjustment:F,AttendanceBehaviour:E,Overtime:J,BreakInOut:nt},data:function(){return{htmlTitle:"Overview | Attendance | User",breadCrumbItems:[{text:"Attendance",disabled:!0},{text:"Overview",disabled:!0}],filters:{start_date:"",end_date:""},appliedFilterText:"This Month"}}},at=rt,it=Object(m["a"])(at,r,a,!1,null,null,null);e["default"]=it.exports;p()(it,{VCol:h["a"],VRow:x["a"]})},"6e60":function(t,e,n){"use strict";n("99af");e["a"]={getAdjustment:function(t){return"/attendance/".concat(t,"/adjustments/")},getAdjustmentDetail:function(t,e){return"/attendance/".concat(t,"/adjustments/").concat(e,"/")},approve:function(t,e){return"/attendance/".concat(t,"/adjustments/").concat(e,"/approve/")},decline:function(t,e){return"/attendance/".concat(t,"/adjustments/").concat(e,"/decline/")},forward:function(t,e){return"/attendance/".concat(t,"/adjustments/").concat(e,"/forward/")},cancel:function(t,e){return"/attendance/".concat(t,"/adjustments/").concat(e,"/cancel/")},sendAdjustment:function(t){return"/attendance/".concat(t,"/adjustments/bulk-update/")},getAdjustmentHistory:function(t,e){return"/attendance/".concat(t,"/adjustments/").concat(e,"/history/")},postBulkAttendanceAdjustment:function(t){return"/attendance/".concat(t,"/adjustments/bulk-action/")},editAttendance:function(t){return"/attendance/".concat(t,"/edit-entry/")},softDeleteShiftTiming:function(t,e,n){return"/attendance/".concat(t,"/timesheets/").concat(e,"/soft-delete-entry/").concat(n,"/")},deleteShiftTimingByUser:function(t){return"/attendance/".concat(t,"/delete-entry/")}}},"92fa":function(t,e){var n=/^(attrs|props|on|nativeOn|class|style|hook)$/;function r(t,e){return function(){t&&t.apply(this,arguments),e&&e.apply(this,arguments)}}t.exports=function(t){return t.reduce((function(t,e){var a,i,o,s,c;for(o in e)if(a=t[o],i=e[o],a&&n.test(o))if("class"===o&&("string"===typeof a&&(c=a,t[o]=a={},a[c]=!0),"string"===typeof i&&(c=i,e[o]=i={},i[c]=!0)),"on"===o||"nativeOn"===o||"hook"===o)for(s in i)a[s]=r(a[s],i[s]);else if(Array.isArray(a))t[o]=a.concat(i);else if(Array.isArray(i))t[o]=[a].concat(i);else for(s in i)a[s]=i[s];else t[o]=e[o];return t}),{})}},ad9d:function(t,e,n){"use strict";n("99af");e["a"]={getOvertime:function(t){return"/attendance/".concat(t,"/overtime/claims/")},getOvertimeDetail:function(t,e){return"/attendance/".concat(t,"/overtime/claims/").concat(e,"/")},putOvertime:function(t,e){return"/attendance/".concat(t,"/overtime/claims/").concat(e,"/edit/")},claimOvertime:function(t){return"/attendance/".concat(t,"/overtime/claims/bulk-update/")},getOvertimeCalculation:function(t,e){return"/attendance/".concat(t,"/overtime/claims/").concat(e,"/normalization/")},putClaim:function(t,e){return"/attendance/".concat(t,"/overtime/claims/").concat(e,"/")},postBulkOvertimeClaim:function(t){return"/attendance/".concat(t,"/overtime/claims/bulk-action/")},unexpire:function(t){return"/attendance/".concat(t,"/overtime/claims/unexpire/")},getOvertimeSettings:function(t){return"/attendance/".concat(t,"/overtime/settings/")},postOvertimeSettings:function(t){return"/attendance/".concat(t,"/overtime/settings/")},updateOvertimeSettings:function(t,e){return"/attendance/".concat(t,"/overtime/settings/").concat(e,"/")},deleteOvertimeSettings:function(t,e){return"/attendance/".concat(t,"/overtime/settings/").concat(e,"/")},postAssignOvertime:function(t){return"/attendance/".concat(t,"/assign-overtime/")},getOvertimeHistory:function(t,e){return"/attendance/".concat(t,"/overtime/claims/").concat(e,"/history/")},getOvertimeOverviewDetails:function(t){return"/attendance/".concat(t,"/overtime/claims/summary/")}}},e330:function(t,e,n){"use strict";n.d(e,"b",(function(){return o})),n.d(e,"a",(function(){return s})),n.d(e,"c",(function(){return c})),n.d(e,"d",(function(){return d}));var r=n("92fa"),a=n.n(r),i=function(){return Math.random().toString(36).substring(2)},o={name:"ContentLoader",functional:!0,props:{width:{type:[Number,String],default:400},height:{type:[Number,String],default:130},speed:{type:Number,default:2},preserveAspectRatio:{type:String,default:"xMidYMid meet"},baseUrl:{type:String,default:""},primaryColor:{type:String,default:"#f9f9f9"},secondaryColor:{type:String,default:"#ecebeb"},primaryOpacity:{type:Number,default:1},secondaryOpacity:{type:Number,default:1},uniqueKey:{type:String},animate:{type:Boolean,default:!0}},render:function(t,e){var n=e.props,r=e.data,o=e.children,s=n.uniqueKey?n.uniqueKey+"-idClip":i(),c=n.uniqueKey?n.uniqueKey+"-idGradient":i();return t("svg",a()([r,{attrs:{viewBox:"0 0 "+n.width+" "+n.height,version:"1.1",preserveAspectRatio:n.preserveAspectRatio}}]),[t("rect",{style:{fill:"url("+n.baseUrl+"#"+c+")"},attrs:{"clip-path":"url("+n.baseUrl+"#"+s+")",x:"0",y:"0",width:n.width,height:n.height}}),t("defs",[t("clipPath",{attrs:{id:s}},[o||t("rect",{attrs:{x:"0",y:"0",rx:"5",ry:"5",width:n.width,height:n.height}})]),t("linearGradient",{attrs:{id:c}},[t("stop",{attrs:{offset:"0%","stop-color":n.primaryColor,"stop-opacity":n.primaryOpacity}},[n.animate?t("animate",{attrs:{attributeName:"offset",values:"-2; 1",dur:n.speed+"s",repeatCount:"indefinite"}}):null]),t("stop",{attrs:{offset:"50%","stop-color":n.secondaryColor,"stop-opacity":n.secondaryOpacity}},[n.animate?t("animate",{attrs:{attributeName:"offset",values:"-1.5; 1.5",dur:n.speed+"s",repeatCount:"indefinite"}}):null]),t("stop",{attrs:{offset:"100%","stop-color":n.primaryColor,"stop-opacity":n.primaryOpacity}},[n.animate?t("animate",{attrs:{attributeName:"offset",values:"-1; 2",dur:n.speed+"s",repeatCount:"indefinite"}}):null])])])])}},s={name:"BulletListLoader",functional:!0,render:function(t,e){var n=e.data;return t(o,n,[t("circle",{attrs:{cx:"10",cy:"20",r:"8"}}),t("rect",{attrs:{x:"25",y:"15",rx:"5",ry:"5",width:"220",height:"10"}}),t("circle",{attrs:{cx:"10",cy:"50",r:"8"}}),t("rect",{attrs:{x:"25",y:"45",rx:"5",ry:"5",width:"220",height:"10"}}),t("circle",{attrs:{cx:"10",cy:"80",r:"8"}}),t("rect",{attrs:{x:"25",y:"75",rx:"5",ry:"5",width:"220",height:"10"}}),t("circle",{attrs:{cx:"10",cy:"110",r:"8"}}),t("rect",{attrs:{x:"25",y:"105",rx:"5",ry:"5",width:"220",height:"10"}})])}},c={name:"FacebookLoader",functional:!0,render:function(t,e){var n=e.data;return t(o,n,[t("rect",{attrs:{x:"70",y:"15",rx:"4",ry:"4",width:"117",height:"6.4"}}),t("rect",{attrs:{x:"70",y:"35",rx:"3",ry:"3",width:"85",height:"6.4"}}),t("rect",{attrs:{x:"0",y:"80",rx:"3",ry:"3",width:"350",height:"6.4"}}),t("rect",{attrs:{x:"0",y:"100",rx:"3",ry:"3",width:"380",height:"6.4"}}),t("rect",{attrs:{x:"0",y:"120",rx:"3",ry:"3",width:"201",height:"6.4"}}),t("circle",{attrs:{cx:"30",cy:"30",r:"30"}})])}},d={name:"ListLoader",functional:!0,render:function(t,e){var n=e.data;return t(o,n,[t("rect",{attrs:{x:"0",y:"0",rx:"3",ry:"3",width:"250",height:"10"}}),t("rect",{attrs:{x:"20",y:"20",rx:"3",ry:"3",width:"220",height:"10"}}),t("rect",{attrs:{x:"20",y:"40",rx:"3",ry:"3",width:"170",height:"10"}}),t("rect",{attrs:{x:"0",y:"60",rx:"3",ry:"3",width:"250",height:"10"}}),t("rect",{attrs:{x:"20",y:"80",rx:"3",ry:"3",width:"200",height:"10"}}),t("rect",{attrs:{x:"20",y:"100",rx:"3",ry:"3",width:"80",height:"10"}})])}}}}]);