(window["webpackJsonp"]=window["webpackJsonp"]||[]).push([["pages/admin/_slug/payroll/response/index~pages/user/payroll/payslip/index","chunk-26c51c79","chunk-2d2259e9","chunk-6441e173","chunk-aee42bec","chunk-2d213000"],{"0798":function(t,e,a){"use strict";var n=a("5530"),i=a("ade3"),s=(a("caad"),a("0c18"),a("10d2")),r=a("afdd"),o=a("9d26"),l=a("f2e7"),c=a("7560"),d=a("f40d"),u=a("58df"),h=a("d9bd");e["a"]=Object(u["a"])(s["a"],l["a"],d["a"]).extend({name:"v-alert",props:{border:{type:String,validator:function(t){return["top","right","bottom","left"].includes(t)}},closeLabel:{type:String,default:"$vuetify.close"},coloredBorder:Boolean,dense:Boolean,dismissible:Boolean,closeIcon:{type:String,default:"$cancel"},icon:{default:"",type:[Boolean,String],validator:function(t){return"string"===typeof t||!1===t}},outlined:Boolean,prominent:Boolean,text:Boolean,type:{type:String,validator:function(t){return["info","error","success","warning"].includes(t)}},value:{type:Boolean,default:!0}},computed:{__cachedBorder:function(){if(!this.border)return null;var t={staticClass:"v-alert__border",class:Object(i["a"])({},"v-alert__border--".concat(this.border),!0)};return this.coloredBorder&&(t=this.setBackgroundColor(this.computedColor,t),t.class["v-alert__border--has-color"]=!0),this.$createElement("div",t)},__cachedDismissible:function(){var t=this;if(!this.dismissible)return null;var e=this.iconColor;return this.$createElement(r["a"],{staticClass:"v-alert__dismissible",props:{color:e,icon:!0,small:!0},attrs:{"aria-label":this.$vuetify.lang.t(this.closeLabel)},on:{click:function(){return t.isActive=!1}}},[this.$createElement(o["a"],{props:{color:e}},this.closeIcon)])},__cachedIcon:function(){return this.computedIcon?this.$createElement(o["a"],{staticClass:"v-alert__icon",props:{color:this.iconColor}},this.computedIcon):null},classes:function(){var t=Object(n["a"])(Object(n["a"])({},s["a"].options.computed.classes.call(this)),{},{"v-alert--border":Boolean(this.border),"v-alert--dense":this.dense,"v-alert--outlined":this.outlined,"v-alert--prominent":this.prominent,"v-alert--text":this.text});return this.border&&(t["v-alert--border-".concat(this.border)]=!0),t},computedColor:function(){return this.color||this.type},computedIcon:function(){return!1!==this.icon&&("string"===typeof this.icon&&this.icon?this.icon:!!["error","info","success","warning"].includes(this.type)&&"$".concat(this.type))},hasColoredIcon:function(){return this.hasText||Boolean(this.border)&&this.coloredBorder},hasText:function(){return this.text||this.outlined},iconColor:function(){return this.hasColoredIcon?this.computedColor:void 0},isDark:function(){return!(!this.type||this.coloredBorder||this.outlined)||c["a"].options.computed.isDark.call(this)}},created:function(){this.$attrs.hasOwnProperty("outline")&&Object(h["a"])("outline","outlined",this)},methods:{genWrapper:function(){var t=[this.$slots.prepend||this.__cachedIcon,this.genContent(),this.__cachedBorder,this.$slots.append,this.$scopedSlots.close?this.$scopedSlots.close({toggle:this.toggle}):this.__cachedDismissible],e={staticClass:"v-alert__wrapper"};return this.$createElement("div",e,t)},genContent:function(){return this.$createElement("div",{staticClass:"v-alert__content"},this.$slots.default)},genAlert:function(){var t={staticClass:"v-alert",attrs:{role:"alert"},on:this.listeners$,class:this.classes,style:this.styles,directives:[{name:"show",value:this.isActive}]};if(!this.coloredBorder){var e=this.hasText?this.setTextColor:this.setBackgroundColor;t=e(this.computedColor,t)}return this.$createElement("div",t,[this.genWrapper()])},toggle:function(){this.isActive=!this.isActive}},render:function(t){var e=this.genAlert();return this.transition?t("transition",{props:{name:this.transition,origin:this.origin,mode:this.mode}},[e]):e}})},"0c18":function(t,e,a){},"17cc":function(t,e,a){"use strict";var n=a("b85c"),i=a("1da1"),s=a("5530");a("96cf"),a("ac1f"),a("841c"),a("d3b7"),a("3ca3"),a("ddb0"),a("2b3d"),a("b64b");e["a"]={data:function(){return{fetchedResults:[],response:{},extra_data:"",appliedFilters:{},footerProps:{itemsPerPageOptions:[10,20,30,40,50,100]},pagination:{sortBy:["modified_at"],descending:!1,totalItems:0,page:1,rowsPerPage:10,pageCount:0},triggerDataTable:!0,fullParams:""}},created:function(){this.getParams(this.DataTableFilter)},methods:{getParams:function(t){var e=Object(s["a"])(Object(s["a"])({},t),{},{offset:(this.pagination.page-1)*this.pagination.rowsPerPage,limit:this.pagination.rowsPerPage,ordering:this.pagination.descending?this.pagination.sortBy:"-"+this.pagination.sortBy});this.fullParams=this.convertToURLSearchParams(e)},loadDataTable:function(t){this.response=t,this.fetchedResults=t.results,this.pagination.totalItems=t.count,this.extra_data=t.extra_data,this.triggerDataTable=!0},fetchData:function(t){var e=this;return Object(i["a"])(regeneratorRuntime.mark((function a(){var n,i;return regeneratorRuntime.wrap((function(a){while(1)switch(a.prev=a.next){case 0:return console.warn("DatatableMixin: fetchData has been deprecated. Please use the function in page itself."),n=Object(s["a"])(Object(s["a"])(Object(s["a"])({},t),e.appliedFilters),{},{search:e.search,offset:(e.pagination.page-1)*e.pagination.rowsPerPage,limit:e.pagination.rowsPerPage,ordering:e.pagination.descending?e.pagination.sortBy:"-"+e.pagination.sortBy}),i=e.convertToURLSearchParams(n),e.loading=!0,a.next=6,e.$http.get(e.endpoint,{params:i}).then((function(t){e.response=t,e.fetchedResults=t.results,e.pagination.totalItems=t.count})).finally((function(){e.loading=!1}));case 6:case"end":return a.stop()}}),a)})))()},applyFilters:function(t){this.appliedFilters=t,this.fetchData(t)},convertToURLSearchParams:function(t){for(var e=new URLSearchParams,a=0,i=Object.keys(t);a<i.length;a++){var s=i[a],r=t[s];if(void 0===r&&(r=""),Array.isArray(r)){var o,l=Object(n["a"])(r);try{for(l.s();!(o=l.n()).done;){var c=o.value;e.append(s,c)}}catch(d){l.e(d)}finally{l.f()}}else e.append(s,r)}return e},loadDataTableChange:function(){var t=this;this.triggerDataTable&&(this.getParams(this.DataTableFilter),this.$nextTick((function(){t.fetchDataTable()})))}},watch:{DataTableFilter:function(t){this.fetchedResults=[],this.getParams(t),this.fetchDataTable(),this.pagination.page=1},"pagination.sortBy":function(){this.fetchedResults=[],this.loadDataTableChange()},"pagination.descending":function(){this.fetchedResults=[],this.loadDataTableChange()},"pagination.page":function(){this.fetchedResults=[],this.loadDataTableChange()},"pagination.rowsPerPage":function(){this.fetchedResults=[],this.loadDataTableChange()}}}},1806:function(t,e,a){"use strict";var n=a("1da1"),i=(a("96cf"),a("d3b7"),a("b0c0"),a("99af"),a("c44a")),s=a("17cc");e["a"]={mixins:[i["a"],s["a"]],data:function(){return{crud:{name:"operation",endpoint:{common:"",get:"",post:"",put:"",patch:"",delete:""},id:"id",dataTableFetch:void 0},loading:!1,rowsPerPageItems:[10,20,30,40,50],formValues:this.deepCopy(this.actionData||{}),deleteNotification:{dialog:!1,heading:"Confirm Delete",text:"Are you sure you want to delete ?"}}},created:function(){this.crud.dataTableFetch&&this.loadDataTableChange()},methods:{submit:function(){this.formValues&&this.formValues.id?this.updateData():this.insertData()},fetchDataTable:function(){var t=this;this.loading||(this.loading=!0,this.$http.get(this.crud.endpoint.common||this.crud.endpoint.get,{params:this.fullParams}).then((function(e){t.loadDataTable(e),t.processAfterTableLoad()})).catch((function(e){t.pushErrors(e),t.notifyInvalidFormResponse()})).finally((function(){t.loading=!1})))},insertData:function(){var t=this;return Object(n["a"])(regeneratorRuntime.mark((function e(){var a;return regeneratorRuntime.wrap((function(e){while(1)switch(e.prev=e.next){case 0:if(!t.loading){e.next=2;break}return e.abrupt("return");case 2:return e.next=4,t.validateAllFields();case 4:if(!e.sent){e.next=8;break}t.loading=!0,a="".concat(t.crud.endpoint.post||t.crud.endpoint.common),t.$http.post(a,t.getFormValues()).then((function(){t.$emit("create"),t.processAfterInsert(),t.notifyUser("Successfully created ".concat(t.crud.name))})).catch((function(e){t.pushErrors(e),t.notifyInvalidFormResponse()})).finally((function(){t.loading=!1}));case 8:case"end":return e.stop()}}),e)})))()},updateData:function(){var t=this;return Object(n["a"])(regeneratorRuntime.mark((function e(){var a,n,i;return regeneratorRuntime.wrap((function(e){while(1)switch(e.prev=e.next){case 0:if(!t.loading){e.next=2;break}return e.abrupt("return");case 2:return e.next=4,t.validateAllFields();case 4:if(!e.sent){e.next=10;break}t.loading=!0,a=t.crud.endpoint.patch||t.crud.endpoint.put||"".concat(t.crud.endpoint.common).concat(t.actionData[t.crud.id],"/"),n=t.getFormValues(),i=t.crud.endpoint.patch?"patch":"put",t.$http[i](a,n).then((function(){t.$emit("update"),t.processAfterUpdate(),t.notifyUser("Successfully Updated ".concat(t.crud.name))})).catch((function(e){t.pushErrors(e),t.notifyInvalidFormResponse()})).finally((function(){t.loading=!1}));case 10:case"end":return e.stop()}}),e)})))()},deleteData:function(){var t=this;if(!this.loading){var e=this.actionData?this.actionData[this.crud.id]:"",a="".concat(this.crud.endpoint.delete," || ").concat(this.crud.endpoint.common,"/").concat(e,"/");this.loading=!0,this.$http.delete(a).then((function(){t.notifyUser("Successfully Deleted ".concat(t.crud.name)),t.deleteNotification.dialog=!1,t.actionData={},"undefined"!==t.dataTableFetch&&t.loadDataTableChange(),t.processAfterDelete()})).catch((function(e){t.pushErrors(e),t.notifyInvalidFormResponse()})).finally((function(){t.loading=!1}))}},getFormValues:function(){return this.formValues},processAfterTableLoad:function(){return null},processAfterInsert:function(){return null},processAfterUpdate:function(){return null},processAfterDelete:function(){return null}}}},"1f09":function(t,e,a){},3129:function(t,e,a){"use strict";var n=a("3835"),i=a("5530"),s=(a("ac1f"),a("1276"),a("d81d"),a("a630"),a("3ca3"),a("5319"),a("1f09"),a("c995")),r=a("24b2"),o=a("7560"),l=a("58df"),c=a("80d2");e["a"]=Object(l["a"])(s["a"],r["a"],o["a"]).extend({name:"VSkeletonLoader",props:{boilerplate:Boolean,loading:Boolean,tile:Boolean,transition:String,type:String,types:{type:Object,default:function(){return{}}}},computed:{attrs:function(){return this.isLoading?this.boilerplate?{}:Object(i["a"])({"aria-busy":!0,"aria-live":"polite",role:"alert"},this.$attrs):this.$attrs},classes:function(){return Object(i["a"])(Object(i["a"])({"v-skeleton-loader--boilerplate":this.boilerplate,"v-skeleton-loader--is-loading":this.isLoading,"v-skeleton-loader--tile":this.tile},this.themeClasses),this.elevationClasses)},isLoading:function(){return!("default"in this.$scopedSlots)||this.loading},rootTypes:function(){return Object(i["a"])({actions:"button@2",article:"heading, paragraph",avatar:"avatar",button:"button",card:"image, card-heading","card-avatar":"image, list-item-avatar","card-heading":"heading",chip:"chip","date-picker":"list-item, card-heading, divider, date-picker-options, date-picker-days, actions","date-picker-options":"text, avatar@2","date-picker-days":"avatar@28",heading:"heading",image:"image","list-item":"text","list-item-avatar":"avatar, text","list-item-two-line":"sentences","list-item-avatar-two-line":"avatar, sentences","list-item-three-line":"paragraph","list-item-avatar-three-line":"avatar, paragraph",paragraph:"text@3",sentences:"text@2",table:"table-heading, table-thead, table-tbody, table-tfoot","table-heading":"heading, text","table-thead":"heading@6","table-tbody":"table-row-divider@6","table-row-divider":"table-row, divider","table-row":"table-cell@6","table-cell":"text","table-tfoot":"text@2, avatar@2",text:"text"},this.types)}},methods:{genBone:function(t,e){return this.$createElement("div",{staticClass:"v-skeleton-loader__".concat(t," v-skeleton-loader__bone")},e)},genBones:function(t){var e=this,a=t.split("@"),i=Object(n["a"])(a,2),s=i[0],r=i[1],o=function(){return e.genStructure(s)};return Array.from({length:r}).map(o)},genStructure:function(t){var e=[];t=t||this.type||"";var a=this.rootTypes[t]||"";if(t===a);else{if(t.indexOf(",")>-1)return this.mapBones(t);if(t.indexOf("@")>-1)return this.genBones(t);a.indexOf(",")>-1?e=this.mapBones(a):a.indexOf("@")>-1?e=this.genBones(a):a&&e.push(this.genStructure(a))}return[this.genBone(t,e)]},genSkeleton:function(){var t=[];return this.isLoading?t.push(this.genStructure()):t.push(Object(c["s"])(this)),this.transition?this.$createElement("transition",{props:{name:this.transition},on:{afterEnter:this.resetStyles,beforeEnter:this.onBeforeEnter,beforeLeave:this.onBeforeLeave,leaveCancelled:this.resetStyles}},t):t},mapBones:function(t){return t.replace(/\s/g,"").split(",").map(this.genStructure)},onBeforeEnter:function(t){this.resetStyles(t),this.isLoading&&(t._initialStyle={display:t.style.display,transition:t.style.transition},t.style.setProperty("transition","none","important"))},onBeforeLeave:function(t){t.style.setProperty("display","none","important")},resetStyles:function(t){t._initialStyle&&(t.style.display=t._initialStyle.display||"",t.style.transition=t._initialStyle.transition,delete t._initialStyle)}},render:function(t){return t("div",{staticClass:"v-skeleton-loader",attrs:this.attrs,on:this.$listeners,class:this.classes,style:this.isLoading?this.measurableStyles:void 0},[this.genSkeleton()])}})},"3da5":function(t,e,a){"use strict";e["a"]={showGeneratedPayslip:function(t){return"/payroll/".concat(t,"/show-generated-payslip/")}}},"8cd3":function(t,e,a){"use strict";var n=a("5530"),i=(a("d3b7"),a("f0d5"));e["a"]={mixins:[i["a"]],data:function(){return{dataTableEndpoint:"",fetchedResults:[],response:null,footerProps:{itemsPerPageOptions:[10,20,30,40,50,100]},pagination:{sortBy:["modified_at"],descending:!1,totalItems:0,page:1,rowsPerPage:10,pageCount:0},loadTableOnInit:!0}},computed:{filterParams:function(){var t=Object(n["a"])(Object(n["a"])({},this.dataTableFilter),{},{offset:(this.pagination.page-1)*this.pagination.rowsPerPage,limit:this.pagination.rowsPerPage,ordering:this.pagination.descending?this.pagination.sortBy:"-"+this.pagination.sortBy});return this.convertToURLSearchParams(t,!1)}},watch:{filterParams:function(){var t=this;this.$nextTick((function(){t.fetchDataTable()}))},dataTableFilter:function(){this.pagination.page=1}},created:function(){var t=this;setTimeout((function(){t.loadTableOnInit&&t.fetchDataTable()}),0)},methods:{fetchDataTable:function(t,e){var a=this;return new Promise((function(n,i){!t&&!a.dataTableEndpoint||a.loading||(a.loadTableOnInit=!1,a.loading=!0,a.fetchedResults=[],a.$http.get(t||a.dataTableEndpoint,e||{params:a.filterParams}).then((function(t){a.response=t,a.fetchedResults=t.results,a.pagination.totalItems=t.count,a.processAfterTableLoad(t),n(t),a.loading=!1})).catch((function(t){a.pushErrors(t),a.notifyInvalidFormResponse(),i(t),a.loading=!1})))}))},processAfterTableLoad:function(){}}}},a51f:function(t,e,a){"use strict";a.r(e);var n=function(){var t=this,e=t.$createElement,a=t._self._c||e;return a("div",[t.search.length>0?a("span",[t._v(' Your search for "'+t._s(t.search)+'" found no results. ')]):t.loading?a("v-skeleton-loader",{attrs:{type:"table",height:t.skeletonLoaderHeight}}):a("no-data-found",{attrs:{text:t.text,height:t.height}},[t._t("default")],2)],1)},i=[],s=(a("a9e3"),a("e585")),r={components:{NoDataFound:s["default"]},props:{search:{type:String,default:""},loading:{type:Boolean,required:!0},text:{type:String,default:"No data available at the moment"},height:{type:[String,Number],default:200},skeletonLoaderHeight:{type:[String,Number],default:void 0}}},o=r,l=a("2877"),c=a("6544"),d=a.n(c),u=a("3129"),h=Object(l["a"])(o,n,i,!1,null,null,null);e["default"]=h.exports;d()(h,{VSkeletonLoader:u["a"]})},ab8a:function(t,e,a){"use strict";a.r(e);var n=function(){var t=this,e=t.$createElement,a=t._self._c||e;return a("div",[t.changeType&&0!==t.nonFieldErrors.length?a("div",t._l(t.nonFieldErrors,(function(e,n){return a("v-col",{key:n},t._l(e,(function(e,n){return a("div",{key:n},[a("span",{domProps:{textContent:t._s(t.key)}}),a("span",{domProps:{textContent:t._s(e.toString())}})])})),0)})),1):t._e(),t.changeType||0===t.nonFieldErrors.length?t._e():a("v-alert",{staticClass:"ma-3",attrs:{outlined:"",dense:"",tile:"",dismissible:"",color:"danger"}},[a("span",{domProps:{textContent:t._s("There are some errors")}}),t._l(t.nonFieldErrors,(function(e,n){return a("div",{key:n},t._l(e,(function(e,n){return a("div",{key:n},[a("ul",[a("li",[a("span",{domProps:{textContent:t._s(t.key)}}),a("span",{domProps:{textContent:t._s(e.toString())}})])])])})),0)}))],2)],1)},i=[],s={props:{nonFieldErrors:{type:Array,required:!0},changeType:{type:Boolean,default:!1}},data:function(){return{key:""}}},r=s,o=a("2877"),l=a("6544"),c=a.n(l),d=a("0798"),u=a("62ad"),h=Object(o["a"])(r,n,i,!1,null,null,null);e["default"]=h.exports;c()(h,{VAlert:d["a"],VCol:u["a"]})},cd2d:function(t,e,a){"use strict";var n=function(){var t=this,e=t.$createElement,a=t._self._c||e;return a("v-card",[a("vue-card-title",{attrs:{title:"Payslip Comments",subtitle:"View Or Send Payslip Comments",icon:"mdi-comment-text-outline",closable:""},on:{close:function(e){return t.$emit("close")}}}),a("v-divider"),a("v-card-text",{staticClass:"px-0"},[t.nonFieldErrors?a("non-field-form-errors",{attrs:{"non-field-errors":t.nonFieldErrors}}):t._e(),a("v-row",{attrs:{"no-gutters":""}},[t.fetchedResults.length>0?a("v-col",{staticClass:"py-2",attrs:{md:"12",cols:"12"}},[a("timeline-component",{attrs:{"action-data":t.fetchedResults,"timeline-for":"Comments"}})],1):t._e(),a("v-col",{staticClass:"px-8",attrs:{md:"12",cols:"12"}},[a("v-textarea",t._b({directives:[{name:"validate",rawName:"v-validate",value:"required|max:600",expression:"'required|max:600'"}],attrs:{rows:"2",counter:600,"prepend-inner-icon":"mdi-information-outline"},model:{value:t.formValues.remarks,callback:function(e){t.$set(t.formValues,"remarks",e)},expression:"formValues.remarks"}},"v-textarea",t.veeValidate("remarks","Comment *"),!1))],1)],1)],1),a("v-divider"),a("v-card-actions",[a("v-row",{attrs:{"no-gutters":""}},[a("v-col",{staticClass:"text-right"},[a("v-btn",{attrs:{small:"",text:""},on:{click:function(e){return t.$emit("close")}}},[t._v("Cancel")]),a("v-btn",{attrs:{color:"primary",small:""},on:{click:t.insertData}},[t._v("Send")])],1)],1)],1)],1)},i=[],s=(a("a9e3"),a("99af"),a("ab8a")),r=a("1806"),o=function(){var t=this,e=t.$createElement,a=t._self._c||e;return a("v-timeline",{staticClass:"scrollbar-sm pt-0",attrs:{dense:"",clipped:""}},t._l(t.actionData,(function(e,n){return a("v-timeline-item",{key:n,staticClass:"py-1",attrs:{color:"green",icon:"mdi-check",small:"",dense:""}},[a("v-row",{staticClass:"text-body-2",attrs:{align:"center"}},[a("v-col",{staticClass:"py-0",attrs:{cols:"2"}},[a("div",{staticClass:"font-weight-bold",domProps:{textContent:t._s(t.humanizeDate(e.created_at))}}),a("div",{domProps:{textContent:t._s(t.humanizeTime(e.created_at))}})]),a("v-col",{staticClass:"py-0",attrs:{cols:"3"}},[a("vue-user",{attrs:{user:e.commented_by}})],1),a("v-col",{staticClass:"py-0",attrs:{cols:"7"}},[a("div",{staticClass:"font-weight-medium"},[t._v(t._s(t.timelineFor)+":")]),a("div",[a("span",{domProps:{textContent:t._s(e.remarks||"N/A")}})])])],1)],1)})),1)},l=[],c=a("02cb"),d={components:{VueUser:c["default"]},props:{actionData:{type:Array,default:void 0},timelineFor:{type:String,default:"Remarks"}},methods:{humanizeDate:function(t){return this.$dayjs(t).format("MMM-D, YYYY")},humanizeTime:function(t){var e=this.$dayjs(t).format("h:mm:ss a");return"Invalid date"===e?"N/A":e}}},u=d,h=a("2877"),p=a("6544"),f=a.n(p),m=a("62ad"),g=a("0fd9b"),v=a("8414"),b=a("1e06"),y=Object(h["a"])(u,o,l,!1,null,null,null),_=y.exports;f()(y,{VCol:m["a"],VRow:g["a"],VTimeline:v["a"],VTimelineItem:b["a"]});var x={components:{NonFieldFormErrors:s["default"],TimelineComponent:_},mixins:[r["a"]],props:{payrollId:{type:[Number,String],required:!0}},data:function(){return{formValues:{},crud:{name:"Payslip Comments",endpoint:{common:""},dataTableFetch:!0}}},created:function(){this.crud.endpoint.common="payroll/employee-payrolls/".concat(this.payrollId,"/comments/?as=hr&organization__slug=").concat(this.getOrganizationSlug)}},C=x,k=a("8336"),w=a("b0af"),D=a("99d9"),T=a("ce7e"),P=a("a844"),S=Object(h["a"])(C,n,i,!1,null,null,null);e["a"]=S.exports;f()(S,{VBtn:k["a"],VCard:w["a"],VCardActions:D["a"],VCardText:D["c"],VCol:m["a"],VDivider:T["a"],VRow:g["a"],VTextarea:P["a"]})},e4bf:function(t,e,a){"use strict";a.r(e);var n=function(){var t=this,e=t.$createElement,a=t._self._c||e;return a("div",[t.contextList.filter((function(t){return!t.hide})).length<3&&!t.hideIcons||t.showIcons?a("div",t._l(t.contextList,(function(e,n){return a("span",{key:n},[e.hide?t._e():a("v-tooltip",{attrs:{disabled:t.$vuetify.breakpoint.xs,top:""},scopedSlots:t._u([{key:"activator",fn:function(i){var s=i.on;return[a("v-btn",t._g({staticClass:"mx-0",attrs:{text:"",width:t.small?"18":"22",depressed:"",icon:""}},s),[a("v-icon",{attrs:{disabled:e.disabled,color:e.color,"data-cy":t.dataCyVariable+"btn-dropdown-menu-item-"+(n+1),dark:!e.disabled,small:t.small,size:"20",dense:""},domProps:{textContent:t._s(e.icon)},on:{click:function(e){return t.$emit("click"+n)}}})],1)]}}],null,!0)},[a("span",{domProps:{textContent:t._s(e.disabled&&e.disable_message||e.name)}})])],1)})),0):a("v-menu",{attrs:{"offset-y":"",left:"",transition:"slide-y-transition"},scopedSlots:t._u([{key:"activator",fn:function(e){var n=e.on;return[a("v-btn",t._g({attrs:{small:"",text:"",icon:""}},n),[a("v-icon",{attrs:{"data-cy":"btn-dropdown-menu"},domProps:{textContent:t._s("mdi-dots-vertical")}})],1)]}}])},t._l(t.contextList,(function(e,n){return a("v-list",{key:n,staticClass:"pa-0",attrs:{dense:""}},[e.hide?t._e():a("div",[e.disabled?a("v-list-item",{attrs:{"data-cy":"btn-dropdown-menu-item"}},[a("v-tooltip",{attrs:{top:""},scopedSlots:t._u([{key:"activator",fn:function(n){var i=n.on;return[a("v-list-item-title",t._g({},i),[a("v-icon",{attrs:{disabled:"",small:"",color:e.color},domProps:{textContent:t._s(e.icon)}}),a("span",{staticClass:"ml-1 grey--text",domProps:{textContent:t._s(e.name)}})],1)]}}],null,!0)},[a("span",{domProps:{textContent:t._s(e.disabled&&e.disable_message||e.name)}})])],1):a("v-list-item",{attrs:{"data-cy":"btn-dropdown-menu-item"},on:{click:function(e){return t.$emit("click"+n)}}},[a("v-list-item-title",[a("v-icon",{attrs:{color:e.color,small:"",dense:""},domProps:{textContent:t._s(e.icon)}}),a("span",{staticClass:"ml-1",class:e.text_color,domProps:{textContent:t._s(e.name)}})],1)],1)],1)])})),1)],1)},i=[],s={name:"VueContextMenu",props:{contextList:{type:Array,default:function(){return[]}},dataCyVariable:{type:String,default:""},showIcons:{type:Boolean,default:!1},hideIcons:{type:Boolean,default:!1},small:{type:Boolean,default:!1}}},r=s,o=a("2877"),l=a("6544"),c=a.n(l),d=a("8336"),u=a("132d"),h=a("8860"),p=a("da13"),f=a("5d23"),m=a("e449"),g=a("3a2f"),v=Object(o["a"])(r,n,i,!1,null,"71ee785c",null);e["default"]=v.exports;c()(v,{VBtn:d["a"],VIcon:u["a"],VList:h["a"],VListItem:p["a"],VListItemTitle:f["c"],VMenu:m["a"],VTooltip:g["a"]})},ef8c:function(t,e,a){"use strict";a.r(e);var n=function(){var t=this,e=t.$createElement,a=t._self._c||e;return a("div",[a("v-autocomplete",{class:t.appliedClass,attrs:{items:t.itemsSorted,loading:t.isLoading,"search-input":t.search,multiple:t.multiple,label:t.label,error:t.errorMessages.length>0,"error-messages":t.errorMessages,disabled:t.disabled,"prepend-inner-icon":t.prependInnerIcon,clearable:t.clearable&&!t.readonly,readonly:!!t.readonly,"hide-details":t.hideDetails,"data-cy":"input-user-autocomplete-"+t.dataCyVariable,placeholder:t.placeholder,"hide-selected":"","hide-no-data":"","item-text":"full_name","item-value":"id"},on:{"update:searchInput":function(e){t.search=e},"update:search-input":function(e){t.search=e},blur:function(e){return t.$emit("blur")}},scopedSlots:t._u([{key:"selection",fn:function(e){return[a("v-chip",{attrs:{"input-value":e.selected,close:(t.clearable||!t.clearable&&!t.multiple)&&!t.readonly,small:""},on:{"click:close":function(a){return t.remove(e.item)}}},[a("v-avatar",{attrs:{left:""}},[a("v-img",{attrs:{src:e.item.profile_picture,cover:""}})],1),t._v(" "+t._s(t._f("truncate")(e.item.full_name,t.truncate))+" ")],1)]}},{key:"item",fn:function(e){var n=e.item;return[a("v-list-item-avatar",[a("v-avatar",{attrs:{size:"30"}},[a("v-img",{attrs:{src:n.profile_picture,cover:""}})],1)],1),a("v-list-item-content",[a("v-list-item-title",[t._v(" "+t._s(t._f("truncate")(n.full_name,20))+" "),n.employee_code?a("span",[t._v("("+t._s(n.employee_code)+")")]):t._e()]),n.division?a("v-list-item-subtitle",{domProps:{textContent:t._s(n.division)}}):t._e()],1)]}}]),model:{value:t.selectedData,callback:function(e){t.selectedData=e},expression:"selectedData"}})],1)},i=[],s=a("53ca"),r=(a("a9e3"),a("ac1f"),a("841c"),a("4e827"),a("2ca0"),a("d81d"),a("a434"),a("d3b7"),a("159b"),a("7db0"),a("4de4"),a("caad"),a("2532"),a("fab2")),o=a("63ea"),l=a.n(o),c={props:{value:{type:[Number,String,Array,Object],required:!1,default:function(){return null}},dataCyVariable:{type:String,default:""},userObject:{type:[Object,Array],required:!1,default:function(){return{}}},params:{type:[Object,Array],required:!1,default:function(){return{}}},multiple:{type:Boolean,required:!1,default:!1},disabled:{type:Boolean,required:!1,default:!1},errorMessages:{type:[String,Array],default:function(){return[]}},label:{type:String,default:"Select Employee"},prependInnerIcon:{type:String,default:"mdi-account-plus-outline"},itemsToExclude:{type:[Array,Number],default:null},itemsToInclude:{type:[Array,Number],default:null},clearable:{type:Boolean,default:!0},readonly:{type:Boolean,default:!1},hideDetails:{type:Boolean,default:!1},appliedClass:{type:String,default:""},truncate:{type:Number,default:10},placeholder:{type:String,default:""}},data:function(){return{isLoading:!1,items:[],allUsers:[],selectedData:null,search:null}},computed:{itemsSorted:function(){return this.sortBySearch(this.items,this.search?this.search.toLowerCase():"")}},watch:{value:{handler:function(t,e){!t&&e&&(this.selectedData="",this.populateInitialUsers()),!e&&t&&this.populateInitialUsers()},immediate:!0},search:function(t){!t||this.items.length>0||this.fetchUsers()},selectedData:function(t){this.search="",this.syncUserData(t),this.$emit("input",t)},itemsToExclude:function(){this.items=this.excludeRecord(this.allUsers)},itemsToInclude:function(){this.items=this.includeRecord(this.allUsers)},params:{handler:function(t,e){l()(t,e)||this.fetchUsers()},deep:!0}},methods:{sortBySearch:function(t,e){return t.sort((function(t,a){return t.full_name.toLowerCase().startsWith(e)&&a.full_name.toLowerCase().startsWith(e)?t.full_name.toLowerCase().localeCompare(a.full_name.toLowerCase()):t.full_name.toLowerCase().startsWith(e)?-1:a.full_name.toLowerCase().startsWith(e)?1:t.full_name.toLowerCase().localeCompare(a.full_name.toLowerCase())}))},populateInitialUsers:function(){this.fetchUsers(this.value),Array.isArray(this.value)?"object"===Object(s["a"])(this.value[0])?this.selectedData=this.value.map((function(t){return t.user.id})):this.selectedData=this.value:null===this.value?this.selectedData="":"object"===Object(s["a"])(this.value)?this.selectedData=this.value.id:this.selectedData=this.value,this.$emit("input",this.selectedData)},remove:function(t){if(this.selectedData instanceof Object){var e=this.selectedData.indexOf(t.id);e>=0&&this.selectedData.splice(e,1),this.$emit("remove",t)}else this.selectedData=""},fetchUsers:function(t){var e=this;this.isLoading||(this.isLoading=!0,this.$http.get(r["a"].autocomplete,{params:this.params}).then((function(a){e.allUsers=a,e.itemsToExclude&&(a=e.excludeRecord(a)),e.itemsToInclude&&(a=e.includeRecord(a)),e.items=a,t&&e.syncUserData(t)})).finally((function(){return e.isLoading=!1})))},syncUserData:function(t){var e=this;if(t instanceof Array){var a=[];t.forEach((function(t){a.unshift(e.items.find((function(e){return e.id===t})))})),this.$emit("update:userObject",a)}else{var n=this.items.find((function(e){return e.id===t}));this.$emit("update:userObject",n)}},excludeRecord:function(t){var e=[];return"number"===typeof this.itemsToExclude?e.push(this.itemsToExclude):e=this.itemsToExclude,t.filter((function(t){return!e.includes(t.id)}))},includeRecord:function(t){var e=this;return t.filter((function(t){return e.itemsToInclude.includes(t.id)}))}}},d=c,u=a("2877"),h=a("6544"),p=a.n(h),f=a("c6a6"),m=a("8212"),g=a("cc20"),v=a("adda"),b=a("8270"),y=a("5d23"),_=Object(u["a"])(d,n,i,!1,null,null,null);e["default"]=_.exports;p()(_,{VAutocomplete:f["a"],VAvatar:m["a"],VChip:g["a"],VImg:v["a"],VListItemAvatar:b["a"],VListItemContent:y["a"],VListItemSubtitle:y["b"],VListItemTitle:y["c"]})},f0d5:function(t,e,a){"use strict";a("d3b7"),a("3ca3"),a("ddb0");var n=a("c44a");e["a"]={components:{NonFieldFormErrors:function(){return a.e("chunk-6441e173").then(a.bind(null,"ab8a"))}},mixins:[n["a"]],data:function(){return{crud:{name:"record",message:"",addAnother:!1},formValues:{},loading:!1}}}},fab2:function(t,e,a){"use strict";e["a"]={getUserList:"/users/",postUser:"/users/",autocomplete:"/users/autocomplete/",postImportUser:"/users/import/",downloadUserImportSample:function(t){return"/users/import/sample/?organization=".concat(t)},getUserDetail:function(t){return"/users/".concat(t,"/")},getInternalUserDetail:function(t){return"/users/".concat(t,"/internal-detail")},deleteUser:function(t){return"/users/".concat(t,"/")},updateUser:function(t){return"/users/".concat(t,"/")},changePassword:function(t){return"/users/".concat(t,"/change-password/")},getUserCV:function(t){return"/users/".concat(t,"/cv/")},getProfileCompleteness:function(t){return"users/".concat(t,"/profile-completeness/")}}}}]);