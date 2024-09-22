(window["webpackJsonp"]=window["webpackJsonp"]||[]).push([["pages/admin/_slug/report/generalized/attendance-leave","chunk-26c51c79","chunk-2d0c8a11"],{"03df":function(e,t,a){"use strict";var n=function(){var e=this,t=e.$createElement,a=e._self._c||t;return a("v-card-title",{staticClass:"pa-0"},[e.exportGeneration.created_on?e.exportGeneration.url?a("span",[a("div",{staticClass:"grey--text text-caption",domProps:{textContent:e._s("Last Report was generated on")}}),a("div",{staticClass:"text-caption"},[e._v(" "+e._s(e.getGeneratedDate(e.exportGeneration.created_on))+" ")])]):e._e():a("span",{staticClass:"grey--text text-caption mr-2",domProps:{textContent:e._s("Report has not been generated yet")}}),a("v-btn",{staticClass:"mx-1",attrs:{small:"",depressed:"",color:"primary"},domProps:{textContent:e._s(e.exportGeneration.created_on?"Generate Again":e.buttonText)},on:{click:e.exportTasks}}),e.exportGeneration.url?a("v-btn",{attrs:{small:"",depressed:"",color:"primary"},domProps:{textContent:e._s("Download")},on:{click:e.downloadTask}}):e._e(),a("v-tooltip",{attrs:{bottom:""},scopedSlots:e._u([{key:"activator",fn:function(t){var n=t.on;return[a("v-btn",e._g({attrs:{icon:""},on:{click:e.verifyExportGeneration}},n),[a("v-icon",{attrs:{color:"primary"},domProps:{textContent:e._s("mdi-cloud-sync")}})],1)]}}])},[a("span",[e._v("Refresh to see if report is generated.")])])],1)},i=[],s=a("5530"),r=(a("d3b7"),a("3ca3"),a("ddb0"),a("2b3d"),a("a9e3"),a("fb6a"),a("63ea")),o=a.n(r),l=a("2f62"),c={props:{exportUrl:{type:String,required:!0},filters:{type:[Object,URLSearchParams],required:!0},triggerChange:{type:Object,required:!1,default:function(){return{}}},buttonText:{type:String,default:"Generate Now"}},data:function(){return{exportGeneration:{url:null,created_on:""},exportGenerated:!1,useNepaliDate:localStorage.useNepaliDate}},watch:{triggerChange:{handler:function(e,t){o()(e,t)||this.verifyExportGeneration()},deep:!0},"$route.query.export":{handler:function(e){e&&this.verifyExportGeneration()},immediate:!0}},created:function(){this.verifyExportGeneration()},methods:Object(s["a"])(Object(s["a"])({},Object(l["d"])({setSnackBar:"common/setSnackBar"})),{},{verifyExportGeneration:function(){var e=this,t={};if(this.filters instanceof URLSearchParams){var a=this.filters;a.delete("offset"),a.delete("limit"),t="?"+a}else t=this.convertToURLSearchParams(this.filters);this.$http.get(this.exportUrl+t).then((function(t){e.exportGeneration=t}))},exportTasks:function(){var e=this,t={};if(this.filters instanceof URLSearchParams){var a=this.filters;a.delete("offset"),a.delete("limit"),t="?"+a}else t=this.convertToURLSearchParams(this.filters);var n=this.exportUrl+t;this.$http.post(n).then(this.setSnackBar({text:"A new export will be generated soon",color:"green"})).catch((function(t){e.setSnackBar({text:t.response.data[0],color:"danger"})}))},downloadTask:function(){window.open(this.exportGeneration.url)},getGeneratedDate:function(e){var t=this.$dayjs(e).calendar(),a=Number(t.slice(0,2));return"true"===this.useNepaliDate&&a?this.$dayjs(this.ad2bs(t)).format("DD/MM/YYYY"):t}})},d=c,u=a("2877"),p=a("6544"),h=a.n(p),f=a("8336"),m=a("99d9"),v=a("132d"),g=a("3a2f"),y=Object(u["a"])(d,n,i,!1,null,null,null);t["a"]=y.exports;h()(y,{VBtn:f["a"],VCardTitle:m["d"],VIcon:v["a"],VTooltip:g["a"]})},1229:function(e,t,a){"use strict";a("99af");t["a"]={getDivision:function(e){return"/org/".concat(e,"/division/")},postDivision:function(e){return"/org/".concat(e,"/division/")},getDivisionDetails:function(e,t){return"/org/".concat(e,"/division/").concat(t,"/")},putDivision:function(e,t){return"/org/".concat(e,"/division/").concat(t,"/")},deleteDivision:function(e,t){return"/org/".concat(e,"/division/").concat(t,"/")},importDivision:function(e){return"/org/".concat(e,"/division/import/")},downloadSampleDivision:function(e){return"/org/".concat(e,"/division/import/sample")}}},"17cc":function(e,t,a){"use strict";var n=a("b85c"),i=a("1da1"),s=a("5530");a("96cf"),a("ac1f"),a("841c"),a("d3b7"),a("3ca3"),a("ddb0"),a("2b3d"),a("b64b");t["a"]={data:function(){return{fetchedResults:[],response:{},extra_data:"",appliedFilters:{},footerProps:{itemsPerPageOptions:[10,20,30,40,50,100]},pagination:{sortBy:["modified_at"],descending:!1,totalItems:0,page:1,rowsPerPage:10,pageCount:0},triggerDataTable:!0,fullParams:""}},created:function(){this.getParams(this.DataTableFilter)},methods:{getParams:function(e){var t=Object(s["a"])(Object(s["a"])({},e),{},{offset:(this.pagination.page-1)*this.pagination.rowsPerPage,limit:this.pagination.rowsPerPage,ordering:this.pagination.descending?this.pagination.sortBy:"-"+this.pagination.sortBy});this.fullParams=this.convertToURLSearchParams(t)},loadDataTable:function(e){this.response=e,this.fetchedResults=e.results,this.pagination.totalItems=e.count,this.extra_data=e.extra_data,this.triggerDataTable=!0},fetchData:function(e){var t=this;return Object(i["a"])(regeneratorRuntime.mark((function a(){var n,i;return regeneratorRuntime.wrap((function(a){while(1)switch(a.prev=a.next){case 0:return console.warn("DatatableMixin: fetchData has been deprecated. Please use the function in page itself."),n=Object(s["a"])(Object(s["a"])(Object(s["a"])({},e),t.appliedFilters),{},{search:t.search,offset:(t.pagination.page-1)*t.pagination.rowsPerPage,limit:t.pagination.rowsPerPage,ordering:t.pagination.descending?t.pagination.sortBy:"-"+t.pagination.sortBy}),i=t.convertToURLSearchParams(n),t.loading=!0,a.next=6,t.$http.get(t.endpoint,{params:i}).then((function(e){t.response=e,t.fetchedResults=e.results,t.pagination.totalItems=e.count})).finally((function(){t.loading=!1}));case 6:case"end":return a.stop()}}),a)})))()},applyFilters:function(e){this.appliedFilters=e,this.fetchData(e)},convertToURLSearchParams:function(e){for(var t=new URLSearchParams,a=0,i=Object.keys(e);a<i.length;a++){var s=i[a],r=e[s];if(void 0===r&&(r=""),Array.isArray(r)){var o,l=Object(n["a"])(r);try{for(l.s();!(o=l.n()).done;){var c=o.value;t.append(s,c)}}catch(d){l.e(d)}finally{l.f()}}else t.append(s,r)}return t},loadDataTableChange:function(){var e=this;this.triggerDataTable&&(this.getParams(this.DataTableFilter),this.$nextTick((function(){e.fetchDataTable()})))}},watch:{DataTableFilter:function(e){this.fetchedResults=[],this.getParams(e),this.fetchDataTable(),this.pagination.page=1},"pagination.sortBy":function(){this.fetchedResults=[],this.loadDataTableChange()},"pagination.descending":function(){this.fetchedResults=[],this.loadDataTableChange()},"pagination.page":function(){this.fetchedResults=[],this.loadDataTableChange()},"pagination.rowsPerPage":function(){this.fetchedResults=[],this.loadDataTableChange()}}}},"1f09":function(e,t,a){},"2ba5":function(e,t,a){"use strict";a.r(t);var n=function(){var e=this,t=e.$createElement,a=e._self._c||t;return a("vue-page-wrapper",{attrs:{title:e.htmlTitle,"bread-crumbs":e.breadCrumbItems}},[a("attendance-leave",{attrs:{title:"Attendance and Leave Report","sub-title":"Attendance and Leave report information of employee."}})],1)},i=[],s=function(){var e=this,t=e.$createElement,a=e._self._c||t;return a("v-card",[a("vue-card-title",{attrs:{title:e.title,subtitle:e.subTitle,icon:"mdi-file-document-outline"}},[a("template",{slot:"actions"},[a("v-row",{attrs:{justify:"end",align:"center"}},[a("export-report",{attrs:{"export-url":e.exportUrl,filters:e.fullParams}})],1),a("v-btn",{attrs:{icon:""},on:{click:function(t){e.showFilters=!e.showFilters}}},[a("v-icon",{attrs:{small:""},domProps:{textContent:e._s("mdi-filter-variant")}})],1)],1)],2),a("v-divider"),a("v-slide-y-transition",[e.showFilters?a("div",[a("v-row",{staticClass:"px-3",attrs:{align:"center"}},[a("v-col",{attrs:{cols:"2"}},[a("v-text-field",{attrs:{placeholder:"Search for Employee","prepend-inner-icon":"mdi-magnify"},model:{value:e.search,callback:function(t){e.search=t},expression:"search"}})],1),a("v-col",{attrs:{cols:"3"}},[a("vue-auto-complete",{attrs:{endpoint:e.divisionEndpoint,label:"Select Division","item-text":"name","item-value":"slug"},model:{value:e.currentDivision,callback:function(t){e.currentDivision=t},expression:"currentDivision"}})],1),a("v-col",{attrs:{cols:"3"}},[a("date-filter-menu",{attrs:{"exclude-filter":["Till Date"],default:"This Month"},model:{value:e.dateFilter,callback:function(t){e.dateFilter=t},expression:"dateFilter"}})],1),a("v-col",{attrs:{cols:"2"}},[a("v-checkbox",{attrs:{label:"Past Employee","hide-details":""},model:{value:e.pastEmployee,callback:function(t){e.pastEmployee=t},expression:"pastEmployee"}})],1),a("v-col",{attrs:{cols:"2"}},[a("v-btn",{attrs:{depressed:"",color:"primary"},domProps:{textContent:e._s("Search")},on:{click:e.searchResult}})],1)],1),a("v-row",{staticClass:"px-3"},[a("v-col",{attrs:{cols:"12"}},[a("v-autocomplete",{attrs:{items:e.leaveTypes,"prepend-inner-icon":"mdi-calendar-alert","item-text":"name","item-value":"id",label:"Select the leave types","hide-selected":"",clearable:"","small-chips":"","deletable-chips":"",multiple:"","hide-no-data":""},model:{value:e.selectedLeaveTypes,callback:function(t){e.selectedLeaveTypes=t},expression:"selectedLeaveTypes"}})],1)],1)],1):e._e()]),a("v-card-text",{staticClass:"pa-0"},[a("v-col",{attrs:{cols:"12"}},[a("div",[e._v("Total Selected Days : "+e._s(e.totalNoOfDays))])]),a("v-divider"),a("v-data-table",{attrs:{headers:e.activeHeaders,items:e.fetchedResults,"sort-desc":e.pagination.descending,"sort-by":e.pagination.sortBy,page:e.pagination.page,"items-per-page":e.pagination.rowsPerPage,"footer-props":e.footerProps,"server-items-length":e.pagination.totalItems,"hide-default-header":"","must-sort":""},on:{"update:sortDesc":function(t){return e.$set(e.pagination,"descending",t)},"update:sort-desc":function(t){return e.$set(e.pagination,"descending",t)},"update:sortBy":function(t){return e.$set(e.pagination,"sortBy",t)},"update:sort-by":function(t){return e.$set(e.pagination,"sortBy",t)},"update:page":function(t){return e.$set(e.pagination,"page",t)},"update:itemsPerPage":function(t){return e.$set(e.pagination,"rowsPerPage",t)},"update:items-per-page":function(t){return e.$set(e.pagination,"rowsPerPage",t)}},scopedSlots:e._u([{key:"header",fn:function(t){var n=t.props;return[a("thead",[a("tr",e._l(n.headers,(function(t,n){return a("th",{key:n,staticClass:"text-center",class:["column sortable",e.pagination.descending?"desc":"asc",t.value===e.pagination.sortBy?"active":""],on:{click:function(a){return e.changeSort(t.value)}}},[a("v-hover",{scopedSlots:e._u([{key:"default",fn:function(n){var i=n.hover;return a("v-row",{attrs:{align:"center",justify:"center"}},[a("div",{class:t.sorting?"ml-3":"",attrs:{align:t.align}},[a("span",{staticClass:"text-subtitle-2"},[e._v(" "+e._s(t.header1)+" ")]),a("span",{staticClass:"text-subtitle-2"},[e._v(" "+e._s(t.header2)+" ")]),t.header3&&t.header4?a("div",[a("span",{staticClass:"red--text text-subtitle-2"},[e._v(e._s(t.header3))]),e._v(" | "),a("span",{staticClass:"blue--text"},[e._v(e._s(t.header4))])]):e._e()]),i?a("a",[t.sorting?a("span",[a("v-icon",{attrs:{small:""},domProps:{textContent:e._s(e.pagination.descending?"mdi-arrow-up":"mdi-arrow-down")}})],1):e._e()]):e._e()])}}],null,!0)})],1)})),0)])]}},{key:"item",fn:function(t){return[a("tr",[a("td",{staticClass:"text-center"},[a("v-responsive",{attrs:{width:"200"}},[a("vue-user",{attrs:{user:t.item.user}})],1)],1),a("td",{staticClass:"text-center"},[a("v-responsive",{attrs:{width:"65"}},[a("span",{domProps:{textContent:e._s(t.item.holidays)}})])],1),a("td",{staticClass:"text-center"},[a("v-responsive",{attrs:{width:"90"}},[a("span",{domProps:{textContent:e._s(t.item.working_days)}})])],1),a("td",{staticClass:"text-center"},[a("v-responsive",{attrs:{width:"90"}},[a("span",{domProps:{textContent:e._s(t.item.off_days)}})])],1),a("td",{staticClass:"text-center"},[a("v-responsive",{attrs:{width:"65"}},[a("span",[e._v(e._s(t.item.total_leave))])])],1),a("td",{staticClass:"text-center"},[a("v-responsive",{attrs:{width:"85"}},[a("span",[e._v(e._s(t.item.present_days))])])],1),e._l(t.item.leave_types,(function(t,n){return a("td",{key:n,staticClass:"text-center"},[a("v-responsive",{attrs:{width:"80"}},[a("span",{staticClass:"red--text text-subtitle-2"},[e._v(e._s(t.used))]),e._v(" | "),a("span",{staticClass:"blue--text"},[e._v(e._s(t.balance))])])],1)})),a("td",{staticClass:"text-center"},[a("v-responsive",{attrs:{width:"85"}},[a("span",[e._v(e._s(t.item.absent_days))])])],1),a("td",{staticClass:"text-center"},[a("v-responsive",{attrs:{width:"105"}},[a("span",[e._v(e._s(t.item.total_lost))])])],1),a("td",{staticClass:"text-center"},[a("v-responsive",{attrs:{width:"135"}},[a("span",[e._v(e._s(t.item.confirmed_overtime))])])],1)],2)]}}])},[a("template",{slot:"no-data"},[a("data-table-no-data",{attrs:{loading:e.loading}})],1)],2)],1)],1)},r=[],o=a("2909"),l=a("1da1"),c=a("5530"),d=(a("96cf"),a("d3b7"),a("d81d"),a("b0c0"),a("7db0"),a("a434"),a("99af"),a("a15b"),a("ac1f"),a("841c"),a("17cc")),u=a("02cb"),p=a("ac94"),h=a("a51f"),f=a("5660"),m=a("1229"),v=a("4980"),g=a("03df"),y=a("2f62"),b={components:{VueAutoComplete:f["default"],DataTableNoData:h["default"],DateFilterMenu:p["a"],VueUser:u["default"],ExportReport:g["a"]},mixins:[d["a"]],props:{title:{type:String,default:""},subTitle:{type:String,default:""}},data:function(){return{loading:!1,showFilters:!0,dateFilter:{start_date:"",end_date:""},pastEmployee:!1,headers:[{header1:"Employee",header2:"Name",value:"full_name",align:"left",sorting:!0},{header1:"Holidays",value:"holidays",sorting:!0},{header1:"Working",header2:"Days",value:"working_days",sorting:!0},{header1:"Off",header2:"Days",value:"off_days",sorting:!0},{header1:"Total",header2:"Leave",value:""},{header1:"Present",header2:"Days",value:"present_days",sorting:!0},{header1:"Absent",header2:"Days",value:"absent_days",sorting:!0},{header1:"Total Lost",header2:"Hours",value:"total_lost",sorting:!0},{header1:"Overtime",header2:"Confirmed",value:"confirmed_time",sorting:!0}],exportUrl:v["a"].getAttendanceLeaveReport(this.$route.params.slug)+"export/",activeHeaders:[],leaveTypes:[],selectedLeaveTypes:[],currentDivision:"",divisionEndpoint:"",totalNoOfDays:"",search:"",exportGeneration:{url:null,created_on:""},exportGenerated:!1}},created:function(){this.divisionEndpoint=m["a"].getDivision(this.getOrganizationSlug)},methods:Object(c["a"])(Object(c["a"])({},Object(y["d"])({setSnackBar:"common/setSnackBar"})),{},{fetchDataTable:function(){var e=this;return Object(l["a"])(regeneratorRuntime.mark((function t(){var a,n;return regeneratorRuntime.wrap((function(t){while(1)switch(t.prev=t.next){case 0:return e.loading=!0,t.next=3,e.$http.get(v["a"].getAttendanceLeaveReport(e.getOrganizationSlug)+"?send_leave_types=true&hourly=false",{params:e.fullParams}).then((function(t){e.loadDataTable(t),t.leave_type&&(e.leaveTypes=t.leave_type),e.totalNoOfDays=t.no_of_days})).catch((function(t){"Network Error"===t.message&&(e.setSnackBar({text:"Request could not be completed. Please try again later.",color:"red"}),e.fetchedResults=[])})).finally((function(){e.loading=!1}));case 3:n=[],e.fetchedResults.length>=1&&(n=e.fetchedResults[0].leave_types.map((function(t){return{header1:e.leaveTypes.find((function(e){return e.id===t.leave_type_id})).name,header3:"Taken",header4:"Balance"}}))),e.activeHeaders=[],e.activeHeaders=Object(o["a"])(e.headers),(a=e.activeHeaders).splice.apply(a,[5,0].concat(Object(o["a"])(n)));case 8:case"end":return t.stop()}}),t)})))()},searchResult:function(){this.DataTableFilter=Object(c["a"])(Object(c["a"])({},this.dateFilter),{},{leave_types:this.selectedLeaveTypes.join(","),division:this.currentDivision,user_status:this.pastEmployee?"past":"",search:this.search}),this.loadDataTableChange()},changeSort:function(e){e&&(this.pagination.sortBy===e?this.pagination.descending=!this.pagination.descending:(this.pagination.sortBy=e,this.pagination.descending=!1))}})},x=b,_=a("2877"),w=a("6544"),D=a.n(w),S=a("c6a6"),T=a("8336"),k=a("b0af"),C=a("99d9"),O=a("ac7c"),L=a("62ad"),P=a("8fea"),j=a("ce7e"),B=a("ce87"),R=a("132d"),V=a("6b53"),E=a("0fd9b"),$=a("0789"),A=a("8654"),F=Object(_["a"])(x,s,r,!1,null,null,null),I=F.exports;D()(F,{VAutocomplete:S["a"],VBtn:T["a"],VCard:k["a"],VCardText:C["c"],VCheckbox:O["a"],VCol:L["a"],VDataTable:P["a"],VDivider:j["a"],VHover:B["a"],VIcon:R["a"],VResponsive:V["a"],VRow:E["a"],VSlideYTransition:$["g"],VTextField:A["a"]});var G=a("0549"),M={components:{AttendanceLeave:I,VuePageWrapper:G["default"]},data:function(){return{htmlTitle:"Attendance & Leave Report | Generalized Report | Master Report | Admin",breadCrumbItems:[{text:"Reports",disabled:!0},{text:"Generalized",disabled:!1,to:{name:"admin-slug-master-report-generalized",params:{slug:this.$route.params.slug}}},{text:"Attendance and Leave",disabled:!0}]}}},N=M,U=Object(_["a"])(N,n,i,!1,null,null,null);t["default"]=U.exports},3129:function(e,t,a){"use strict";var n=a("3835"),i=a("5530"),s=(a("ac1f"),a("1276"),a("d81d"),a("a630"),a("3ca3"),a("5319"),a("1f09"),a("c995")),r=a("24b2"),o=a("7560"),l=a("58df"),c=a("80d2");t["a"]=Object(l["a"])(s["a"],r["a"],o["a"]).extend({name:"VSkeletonLoader",props:{boilerplate:Boolean,loading:Boolean,tile:Boolean,transition:String,type:String,types:{type:Object,default:function(){return{}}}},computed:{attrs:function(){return this.isLoading?this.boilerplate?{}:Object(i["a"])({"aria-busy":!0,"aria-live":"polite",role:"alert"},this.$attrs):this.$attrs},classes:function(){return Object(i["a"])(Object(i["a"])({"v-skeleton-loader--boilerplate":this.boilerplate,"v-skeleton-loader--is-loading":this.isLoading,"v-skeleton-loader--tile":this.tile},this.themeClasses),this.elevationClasses)},isLoading:function(){return!("default"in this.$scopedSlots)||this.loading},rootTypes:function(){return Object(i["a"])({actions:"button@2",article:"heading, paragraph",avatar:"avatar",button:"button",card:"image, card-heading","card-avatar":"image, list-item-avatar","card-heading":"heading",chip:"chip","date-picker":"list-item, card-heading, divider, date-picker-options, date-picker-days, actions","date-picker-options":"text, avatar@2","date-picker-days":"avatar@28",heading:"heading",image:"image","list-item":"text","list-item-avatar":"avatar, text","list-item-two-line":"sentences","list-item-avatar-two-line":"avatar, sentences","list-item-three-line":"paragraph","list-item-avatar-three-line":"avatar, paragraph",paragraph:"text@3",sentences:"text@2",table:"table-heading, table-thead, table-tbody, table-tfoot","table-heading":"heading, text","table-thead":"heading@6","table-tbody":"table-row-divider@6","table-row-divider":"table-row, divider","table-row":"table-cell@6","table-cell":"text","table-tfoot":"text@2, avatar@2",text:"text"},this.types)}},methods:{genBone:function(e,t){return this.$createElement("div",{staticClass:"v-skeleton-loader__".concat(e," v-skeleton-loader__bone")},t)},genBones:function(e){var t=this,a=e.split("@"),i=Object(n["a"])(a,2),s=i[0],r=i[1],o=function(){return t.genStructure(s)};return Array.from({length:r}).map(o)},genStructure:function(e){var t=[];e=e||this.type||"";var a=this.rootTypes[e]||"";if(e===a);else{if(e.indexOf(",")>-1)return this.mapBones(e);if(e.indexOf("@")>-1)return this.genBones(e);a.indexOf(",")>-1?t=this.mapBones(a):a.indexOf("@")>-1?t=this.genBones(a):a&&t.push(this.genStructure(a))}return[this.genBone(e,t)]},genSkeleton:function(){var e=[];return this.isLoading?e.push(this.genStructure()):e.push(Object(c["s"])(this)),this.transition?this.$createElement("transition",{props:{name:this.transition},on:{afterEnter:this.resetStyles,beforeEnter:this.onBeforeEnter,beforeLeave:this.onBeforeLeave,leaveCancelled:this.resetStyles}},e):e},mapBones:function(e){return e.replace(/\s/g,"").split(",").map(this.genStructure)},onBeforeEnter:function(e){this.resetStyles(e),this.isLoading&&(e._initialStyle={display:e.style.display,transition:e.style.transition},e.style.setProperty("transition","none","important"))},onBeforeLeave:function(e){e.style.setProperty("display","none","important")},resetStyles:function(e){e._initialStyle&&(e.style.display=e._initialStyle.display||"",e.style.transition=e._initialStyle.transition,delete e._initialStyle)}},render:function(e){return e("div",{staticClass:"v-skeleton-loader",attrs:this.attrs,on:this.$listeners,class:this.classes,style:this.isLoading?this.measurableStyles:void 0},[this.genSkeleton()])}})},4980:function(e,t,a){"use strict";t["a"]={getAppList:"/builder/",getReportList:"/builder/report/",generateReport:function(e){return"/builder/report/".concat(e,"/generate/")},getBuilderConstant:"/builder/constants/",getAttendanceLeaveReport:function(e){return"/builder/".concat(e,"/attendance-and-leave/")}}},5660:function(e,t,a){"use strict";a.r(t);var n=function(){var e=this,t=e.$createElement,a=e._self._c||t;return a("div",{staticClass:"d-flex space-between"},[a("v-autocomplete",{key:e.componentKey,ref:"autoComplete",class:e.appliedClass,attrs:{id:e.id,items:e.itemsSorted,"search-input":e.search,loading:e.isLoading,multiple:e.multiple,label:e.label,error:e.errorMessages.length>0,"error-messages":e.errorMessages,disabled:e.disabled,readonly:e.readonly,"data-cy":"autocomplete-"+e.dataCyVariable,"prepend-inner-icon":e.prependInnerIcon,clearable:e.clearable&&!e.readonly,"hide-details":e.hideDetails,"item-text":e.itemText,"item-value":e.itemValue,"small-chips":e.multiple||e.chips,"deletable-chips":e.multiple,hint:e.hint,"persistent-hint":e.persistentHint,chips:e.chips,solo:e.solo,flat:e.flat,"cache-items":e.cacheItems,placeholder:e.placeholder,dense:e.dense,"hide-selected":"","hide-no-data":""},on:{"update:searchInput":function(t){e.search=t},"update:search-input":function(t){e.search=t},focus:e.populateOnFocus,keydown:function(t){return!t.type.indexOf("key")&&e._k(t.keyCode,"enter",13,t.key,"Enter")?null:(t.preventDefault(),e.searchText())},change:e.updateState,blur:function(t){return e.$emit("blur")}},scopedSlots:e._u([{key:"selection",fn:function(t){return[e._t("selection",(function(){return[e.itemText&&t.item?a("div",[e.multiple||e.chips?a("v-chip",{attrs:{close:(e.clearable||!e.clearable&&!e.multiple)&&!e.readonly,small:""},on:{"click:close":function(a){return e.remove(t.item)}}},[t.item[e.itemText]?a("div",[t.item[e.itemText].length>40?a("v-tooltip",{attrs:{top:""},scopedSlots:e._u([{key:"activator",fn:function(n){var i=n.on;return[a("span",e._g({},i),[e._v(" "+e._s(e._f("truncate")(t.item[e.itemText],40)))])]}}],null,!0)},[a("span",[e._v(e._s(t.item[e.itemText]))])]):a("span",[e._v(e._s(t.item[e.itemText]))])],1):a("div",[a("span",[e._v(e._s(t.item))])])]):a("div",[t.item[e.itemText]?a("div",[t.item[e.itemText].length>40?a("v-tooltip",{attrs:{top:""},scopedSlots:e._u([{key:"activator",fn:function(n){var i=n.on;return[a("span",e._g({},i),[e._v(" "+e._s(e._f("truncate")(t.item[e.itemText],40)))])]}}],null,!0)},[a("span",[e._v(e._s(t.item[e.itemText]))])]):a("span",[e._v(e._s(t.item[e.itemText]))])],1):a("div",[a("span",[e._v(e._s(t.item))])])])],1):e._e()]}),{props:t})]}},{key:"item",fn:function(t){return[a("v-list-item-content",[a("v-list-item-title",[e._t("item",(function(){return[e.itemText&&t.item?a("div",[t.item[e.itemText]?a("div",[t.item[e.itemText].length>40?a("v-tooltip",{attrs:{top:""},scopedSlots:e._u([{key:"activator",fn:function(n){var i=n.on;return[a("span",e._g({},i),[e._v(" "+e._s(e._f("truncate")(t.item[e.itemText],40)))])]}}],null,!0)},[a("span",[e._v(e._s(t.item[e.itemText]))])]):a("span",[e._v(e._s(t.item[e.itemText]))])],1):a("div",[a("span",[e._v(e._s(t.item))])])]):e._e()]}),{props:t})],2)],1)]}},{key:"append-item",fn:function(){return[!e.fullyLoaded&&e.showMoreIcon?a("div",[a("v-list-item-content",{staticClass:"px-4 pointer primary--text font-weight-bold"},[a("v-list-item-title",{on:{click:function(t){return e.fetchData()}}},[e._v(" Load More Items ... ")])],1)],1):e._e()]},proxy:!0}],null,!0),model:{value:e.selectedData,callback:function(t){e.selectedData=t},expression:"selectedData"}}),e._t("default")],2)},i=[],s=a("2909"),r=a("5530"),o=a("53ca"),l=a("1da1"),c=(a("96cf"),a("a9e3"),a("ac1f"),a("841c"),a("7db0"),a("d81d"),a("159b"),a("4de4"),a("4e827"),a("2ca0"),a("d3b7"),a("c740"),a("a434"),a("3ca3"),a("ddb0"),a("2b3d"),a("caad"),a("2532"),a("63ea")),d=a.n(c),u={props:{value:{type:[Number,String,Array,Object],default:void 0},id:{type:String,default:""},dataCyVariable:{type:String,default:""},endpoint:{type:String,default:""},itemText:{type:String,required:!0},itemValue:{type:String,required:!0},params:{type:Object,required:!1,default:function(){return{}}},itemsToExclude:{type:[Array,Number],default:null},forceFetch:{type:Boolean,default:!1},staticItems:{type:Array,default:function(){return[]}},errorMessages:{type:[String,Array],default:function(){return[]}},label:{type:String,default:""},disabled:{type:Boolean,default:!1},readonly:{type:Boolean,default:!1},hint:{type:String,default:void 0},persistentHint:{type:Boolean,required:!1,default:!1},multiple:{type:Boolean,required:!1,default:!1},clearable:{type:Boolean,default:!0},hideDetails:{type:Boolean,default:!1},solo:{type:Boolean,default:!1},flat:{type:Boolean,default:!1},chips:{type:Boolean,default:!1},prependInnerIcon:{type:String,default:void 0},cacheItems:{type:Boolean,default:!1},appliedClass:{type:String,default:""},placeholder:{type:String,default:""},dense:{type:Boolean,default:!1}},data:function(){return{componentKey:0,items:[],selectedData:null,search:null,initialFetchStarted:!1,nextLimit:null,nextOffset:null,showMoreIcon:!1,fullyLoaded:!1,isLoading:!1}},computed:{itemsSorted:function(){return this.sortBySearch(this.items,this.search?this.search.toLowerCase():"")}},watch:{value:{handler:function(){var e=Object(l["a"])(regeneratorRuntime.mark((function e(t){var a,n,i,s,r=this;return regeneratorRuntime.wrap((function(e){while(1)switch(e.prev=e.next){case 0:if(!t){e.next=10;break}if(!this.forceFetch||this.initialFetchStarted){e.next=6;break}return this.initialFetchStarted=!0,e.next=5,this.fetchData();case 5:this.removeDuplicateItem();case 6:Array.isArray(t)?(i=[],"object"===Object(o["a"])(t[0])?(this.selectedData=t.map((function(e){return e[r.itemValue]})),t.forEach((function(e){var t=r.items.find((function(t){return t===e}));t||i.push(e)}))):(t.forEach((function(e){var t=r.items.find((function(t){return t[r.itemValue]===e}));t||i.push(e)})),this.selectedData=t),i.length>0&&(s=this.items).push.apply(s,i)):"object"===Object(o["a"])(t)?(this.selectedData=t[this.itemValue],a=this.items.find((function(e){return e[r.itemValue]===t})),a||this.items.push(t)):(this.selectedData=t,n=this.items.find((function(e){return e===t})),n||this.items.push(t)),this.updateData(this.selectedData),e.next=11;break;case 10:t||(this.selectedData=null);case 11:case"end":return e.stop()}}),e,this)})));function t(t){return e.apply(this,arguments)}return t}(),immediate:!0},selectedData:function(e){this.updateData(e)},params:{handler:function(e,t){d()(e,t)||(this.fullyLoaded=!1,this.initialFetchStarted=!1,this.items=[],this.componentKey+=1)},deep:!0}},methods:{sortBySearch:function(e,t){var a=this.itemText,n=e.filter((function(e){return"object"===Object(o["a"])(e)}));return n.sort((function(e,n){return e[a].toLowerCase().startsWith(t)&&n[a].toLowerCase().startsWith(t)?e[a].toLowerCase().localeCompare(n[a].toLowerCase()):e[a].toLowerCase().startsWith(t)?-1:n[a].toLowerCase().startsWith(t)?1:e[a].toLowerCase().localeCompare(n[a].toLowerCase())}))},populateOnFocus:function(){var e=this;return Object(l["a"])(regeneratorRuntime.mark((function t(){return regeneratorRuntime.wrap((function(t){while(1)switch(t.prev=t.next){case 0:if(!e.initialFetchStarted){t.next=2;break}return t.abrupt("return");case 2:return e.initialFetchStarted=!0,t.next=5,e.fetchData();case 5:e.removeDuplicateItem();case 6:case"end":return t.stop()}}),t)})))()},fetchData:function(){var e=this;return Object(l["a"])(regeneratorRuntime.mark((function t(){var a,n;return regeneratorRuntime.wrap((function(t){while(1)switch(t.prev=t.next){case 0:if(!(e.staticItems.length>0)){t.next=3;break}return e.items=e.staticItems,t.abrupt("return");case 3:return a=e.nextLimit,n=e.nextOffset,e.search&&(a=null,n=null),e.isLoading=!0,t.next=9,e.$http.get(e.endpoint,{params:Object(r["a"])(Object(r["a"])({},e.params),{},{search:e.search,limit:a,offset:n})}).then((function(t){var a;t.results||(t.results=t),t.next?(e.showMoreIcon=!0,e.extractLimitOffset(t.next)):(e.showMoreIcon=!1,e.search||(e.fullyLoaded=!0)),e.itemsToExclude&&(t.results=e.excludeRecord(t.results)),(a=e.items).push.apply(a,Object(s["a"])(t.results))})).finally((function(){e.isLoading=!1}));case 9:case"end":return t.stop()}}),t)})))()},removeDuplicateItem:function(){var e=this,t=this.items.indexOf(this.selectedData);if(t>=0){var a=this.items.findIndex((function(t){return t[e.itemValue]===e.selectedData}));a>=0&&(this.items.splice(t,1),this.componentKey+=1)}},updateData:function(e){var t=this,a=[];e instanceof Array?e.forEach((function(e){a.unshift(t.items.find((function(a){return a[t.itemValue]===e})))})):a=this.items.find((function(a){return a[t.itemValue]===e})),this.$emit("input",e),this.$emit("update:selectedFullData",a)},searchText:function(){0!==this.$refs.autoComplete.filteredItems.length||this.fullyLoaded||this.fetchData()},extractLimitOffset:function(e){var t=new URL(e);this.nextLimit=t.searchParams.get("limit"),this.nextOffset=t.searchParams.get("offset")},excludeRecord:function(e){var t=this,a=[];return"number"===typeof this.itemsToExclude?a.push(this.itemsToExclude):a=this.itemsToExclude,e.filter((function(e){if(e[t.itemValue])return!a.includes(e[t.itemValue])}))},remove:function(e){if(this.selectedData instanceof Object){var t=this.selectedData.indexOf(e[this.itemValue]);t>=0&&this.selectedData.splice(t,1)}else this.selectedData=null},updateState:function(){this.search="",this.nextLimit&&(this.showMoreIcon=!0)}}},p=u,h=a("2877"),f=a("6544"),m=a.n(f),v=a("c6a6"),g=a("cc20"),y=a("5d23"),b=a("3a2f"),x=Object(h["a"])(p,n,i,!1,null,null,null);t["default"]=x.exports;m()(x,{VAutocomplete:v["a"],VChip:g["a"],VListItemContent:y["a"],VListItemTitle:y["c"],VTooltip:b["a"]})},a51f:function(e,t,a){"use strict";a.r(t);var n=function(){var e=this,t=e.$createElement,a=e._self._c||t;return a("div",[e.search.length>0?a("span",[e._v(' Your search for "'+e._s(e.search)+'" found no results. ')]):e.loading?a("v-skeleton-loader",{attrs:{type:"table",height:e.skeletonLoaderHeight}}):a("no-data-found",{attrs:{text:e.text,height:e.height}},[e._t("default")],2)],1)},i=[],s=(a("a9e3"),a("e585")),r={components:{NoDataFound:s["default"]},props:{search:{type:String,default:""},loading:{type:Boolean,required:!0},text:{type:String,default:"No data available at the moment"},height:{type:[String,Number],default:200},skeletonLoaderHeight:{type:[String,Number],default:void 0}}},o=r,l=a("2877"),c=a("6544"),d=a.n(c),u=a("3129"),p=Object(l["a"])(o,n,i,!1,null,null,null);t["default"]=p.exports;d()(p,{VSkeletonLoader:u["a"]})},ce87:function(e,t,a){"use strict";var n=a("16b7"),i=a("f2e7"),s=a("58df"),r=a("d9bd");t["a"]=Object(s["a"])(n["a"],i["a"]).extend({name:"v-hover",props:{disabled:{type:Boolean,default:!1},value:{type:Boolean,default:void 0}},methods:{onMouseEnter:function(){this.runDelay("open")},onMouseLeave:function(){this.runDelay("close")}},render:function(){return this.$scopedSlots.default||void 0!==this.value?(this.$scopedSlots.default&&(e=this.$scopedSlots.default({hover:this.isActive})),Array.isArray(e)&&1===e.length&&(e=e[0]),e&&!Array.isArray(e)&&e.tag?(this.disabled||(e.data=e.data||{},this._g(e.data,{mouseenter:this.onMouseEnter,mouseleave:this.onMouseLeave})),e):(Object(r["c"])("v-hover should only contain a single element",this),e)):(Object(r["c"])("v-hover is missing a default scopedSlot or bound value",this),null);var e}})}}]);