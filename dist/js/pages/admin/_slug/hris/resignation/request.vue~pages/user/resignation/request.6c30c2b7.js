(window["webpackJsonp"]=window["webpackJsonp"]||[]).push([["pages/admin/_slug/hris/resignation/request.vue~pages/user/resignation/request","chunk-31f8a6e6","chunk-2d0c8a11"],{"0549":function(t,e,a){"use strict";a.r(e);var s=function(){var t=this,e=t.$createElement,a=t._self._c||e;return a("div",[a("v-row",{staticClass:"mb-3",attrs:{"no-gutters":""}},[t.breadCrumbs?a("v-col",{attrs:{cols:"12"}},[a("v-card",{attrs:{flat:""}},[a("v-breadcrumbs",{staticClass:"text-body-1 pa-2",class:{"text-caption pa-1":t.$vuetify.breakpoint.xs},attrs:{items:t.breadCrumbs},scopedSlots:t._u([{key:"item",fn:function(e){return[a("span",{class:e.item.disabled?"grey--text":"baseColor--text text--accent-2 pointer",domProps:{textContent:t._s(e.item.text)},on:{click:function(a){return t.$router.push(e.item.to)}}})]}}],null,!1,1670153796)},[a("v-icon",{attrs:{slot:"divider"},slot:"divider"},[t._v("mdi-chevron-right")])],1)],1)],1):t._e()],1),a("v-row",{attrs:{"no-gutters":""}},[a("v-col",{attrs:{cols:"12"}},[t._t("default")],2)],1)],1)},i=[],n=a("5530"),r=(a("ac1f"),a("1276"),a("b0c0"),a("2f62")),o={props:{title:{type:String,required:!0},breadCrumbs:{type:Array,default:function(){return[]}}},computed:Object(n["a"])({},Object(r["c"])({getOrganizationName:"organization/getOrganizationName",getSupervisorSwitchedOrganization:"supervisor/getSwitchedOrganization"})),mounted:function(){document.title="".concat(this.title," | RealHRsoft");var t=this.$route.params.slug?"admin-slug-dashboard":"root",e=this.$route.name.split("-"),a=this.getOrganizationName;this.getSupervisorSwitchedOrganization&&"user"===e[0]&&"supervisor"===e[1]&&(a=this.getSupervisorSwitchedOrganization.name),this.breadCrumbs.unshift({text:a,disabled:!1,to:{name:t,params:{slug:this.$route.params.slug}}})}},c=o,l=a("2877"),u=a("6544"),d=a.n(u),p=a("2bc5"),m=a("b0af"),h=a("62ad"),f=a("132d"),v=a("0fd9b"),g=Object(l["a"])(c,s,i,!1,null,null,null);e["default"]=g.exports;d()(g,{VBreadcrumbs:p["a"],VCard:m["a"],VCol:h["a"],VIcon:f["a"],VRow:v["a"]})},1806:function(t,e,a){"use strict";var s=a("1da1"),i=(a("96cf"),a("d3b7"),a("b0c0"),a("99af"),a("c44a")),n=a("17cc");e["a"]={mixins:[i["a"],n["a"]],data:function(){return{crud:{name:"operation",endpoint:{common:"",get:"",post:"",put:"",patch:"",delete:""},id:"id",dataTableFetch:void 0},loading:!1,rowsPerPageItems:[10,20,30,40,50],formValues:this.deepCopy(this.actionData||{}),deleteNotification:{dialog:!1,heading:"Confirm Delete",text:"Are you sure you want to delete ?"}}},created:function(){this.crud.dataTableFetch&&this.loadDataTableChange()},methods:{submit:function(){this.formValues&&this.formValues.id?this.updateData():this.insertData()},fetchDataTable:function(){var t=this;this.loading||(this.loading=!0,this.$http.get(this.crud.endpoint.common||this.crud.endpoint.get,{params:this.fullParams}).then((function(e){t.loadDataTable(e),t.processAfterTableLoad()})).catch((function(e){t.pushErrors(e),t.notifyInvalidFormResponse()})).finally((function(){t.loading=!1})))},insertData:function(){var t=this;return Object(s["a"])(regeneratorRuntime.mark((function e(){var a;return regeneratorRuntime.wrap((function(e){while(1)switch(e.prev=e.next){case 0:if(!t.loading){e.next=2;break}return e.abrupt("return");case 2:return e.next=4,t.validateAllFields();case 4:if(!e.sent){e.next=8;break}t.loading=!0,a="".concat(t.crud.endpoint.post||t.crud.endpoint.common),t.$http.post(a,t.getFormValues()).then((function(){t.$emit("create"),t.processAfterInsert(),t.notifyUser("Successfully created ".concat(t.crud.name))})).catch((function(e){t.pushErrors(e),t.notifyInvalidFormResponse()})).finally((function(){t.loading=!1}));case 8:case"end":return e.stop()}}),e)})))()},updateData:function(){var t=this;return Object(s["a"])(regeneratorRuntime.mark((function e(){var a,s,i;return regeneratorRuntime.wrap((function(e){while(1)switch(e.prev=e.next){case 0:if(!t.loading){e.next=2;break}return e.abrupt("return");case 2:return e.next=4,t.validateAllFields();case 4:if(!e.sent){e.next=10;break}t.loading=!0,a=t.crud.endpoint.patch||t.crud.endpoint.put||"".concat(t.crud.endpoint.common).concat(t.actionData[t.crud.id],"/"),s=t.getFormValues(),i=t.crud.endpoint.patch?"patch":"put",t.$http[i](a,s).then((function(){t.$emit("update"),t.processAfterUpdate(),t.notifyUser("Successfully Updated ".concat(t.crud.name))})).catch((function(e){t.pushErrors(e),t.notifyInvalidFormResponse()})).finally((function(){t.loading=!1}));case 10:case"end":return e.stop()}}),e)})))()},deleteData:function(){var t=this;if(!this.loading){var e=this.actionData?this.actionData[this.crud.id]:"",a="".concat(this.crud.endpoint.delete," || ").concat(this.crud.endpoint.common,"/").concat(e,"/");this.loading=!0,this.$http.delete(a).then((function(){t.notifyUser("Successfully Deleted ".concat(t.crud.name)),t.deleteNotification.dialog=!1,t.actionData={},"undefined"!==t.dataTableFetch&&t.loadDataTableChange(),t.processAfterDelete()})).catch((function(e){t.pushErrors(e),t.notifyInvalidFormResponse()})).finally((function(){t.loading=!1}))}},getFormValues:function(){return this.formValues},processAfterTableLoad:function(){return null},processAfterInsert:function(){return null},processAfterUpdate:function(){return null},processAfterDelete:function(){return null}}}},"2bc5":function(t,e,a){"use strict";var s=a("5530"),i=(a("a15b"),a("abd3"),a("ade3")),n=a("1c87"),r=a("58df"),o=Object(r["a"])(n["a"]).extend({name:"v-breadcrumbs-item",props:{activeClass:{type:String,default:"v-breadcrumbs__item--disabled"},ripple:{type:[Boolean,Object],default:!1}},computed:{classes:function(){return Object(i["a"])({"v-breadcrumbs__item":!0},this.activeClass,this.disabled)}},render:function(t){var e=this.generateRouteLink(),a=e.tag,i=e.data;return t("li",[t(a,Object(s["a"])(Object(s["a"])({},i),{},{attrs:Object(s["a"])(Object(s["a"])({},i.attrs),{},{"aria-current":this.isActive&&this.isLink?"page":void 0})}),this.$slots.default)])}}),c=a("80d2"),l=Object(c["i"])("v-breadcrumbs__divider","li"),u=a("7560");e["a"]=Object(r["a"])(u["a"]).extend({name:"v-breadcrumbs",props:{divider:{type:String,default:"/"},items:{type:Array,default:function(){return[]}},large:Boolean},computed:{classes:function(){return Object(s["a"])({"v-breadcrumbs--large":this.large},this.themeClasses)}},methods:{genDivider:function(){return this.$createElement(l,this.$slots.divider?this.$slots.divider:this.divider)},genItems:function(){for(var t=[],e=!!this.$scopedSlots.item,a=[],s=0;s<this.items.length;s++){var i=this.items[s];a.push(i.text),e?t.push(this.$scopedSlots.item({item:i})):t.push(this.$createElement(o,{key:a.join("."),props:i},[i.text])),s<this.items.length-1&&t.push(this.genDivider())}return t}},render:function(t){var e=this.$slots.default||this.genItems();return t("ul",{staticClass:"v-breadcrumbs",class:this.classes},e)}})},3296:function(t,e,a){"use strict";var s=function(){var t=this,e=t.$createElement,a=t._self._c||e;return a("div",[a("v-card",[a("vue-card-title",{attrs:{title:"Resignation/Termination of contract requests",subtitle:"Resignation/Termination of contract requests by employees",icon:"mdi-account-off-outline"}},[a("template",{slot:"actions"},[a("v-btn",{attrs:{icon:""},on:{click:function(e){t.filter.show=!t.filter.show}}},[a("v-icon",{attrs:{small:""},domProps:{textContent:t._s("mdi-filter-variant")}})],1)],1)],2),t.filter.show?a("v-divider"):t._e(),a("v-slide-y-transition",[a("v-row",{directives:[{name:"show",rawName:"v-show",value:t.filter.show,expression:"filter.show"}],attrs:{"no-gutters":""}},[a("v-col",{staticClass:"px-2",attrs:{cols:"6",md:"3"}},[a("vue-search",{attrs:{search:t.filter.search},on:{"update:search":function(e){return t.$set(t.filter,"search",e)}},model:{value:t.filter.search,callback:function(e){t.$set(t.filter,"search",e)},expression:"filter.search"}})],1)],1)],1),a("v-divider"),a("v-tabs",{attrs:{"show-arrows":"","slider-color":"blue"},model:{value:t.activeTab,callback:function(e){t.activeTab=e},expression:"activeTab"}},t._l(Object.keys(t.$options.tabs),(function(e){return a("v-tab",{key:e,attrs:{ripple:"",disabled:t.loading},on:{click:function(a){t.status=e}}},[a("span",{staticClass:"text-capitalize mr-2",domProps:{textContent:t._s(e)}}),a("v-chip",{staticClass:"white--text",attrs:{color:t.$options.tabs[e],small:""},domProps:{textContent:t._s(t.response.stats?t.response.stats[e]:"")}})],1)})),1),a("v-divider"),a("v-data-table",{attrs:{headers:t.headers,items:t.fetchedResults,"sort-desc":t.pagination.descending,"sort-by":t.pagination.sortBy,page:t.pagination.page,"items-per-page":t.pagination.rowsPerPage,"footer-props":t.footerProps,"server-items-length":t.pagination.totalItems,"mobile-breakpoint":0,"must-sort":""},on:{"update:sortDesc":function(e){return t.$set(t.pagination,"descending",e)},"update:sort-desc":function(e){return t.$set(t.pagination,"descending",e)},"update:sortBy":function(e){return t.$set(t.pagination,"sortBy",e)},"update:sort-by":function(e){return t.$set(t.pagination,"sortBy",e)},"update:page":function(e){return t.$set(t.pagination,"page",e)},"update:itemsPerPage":function(e){return t.$set(t.pagination,"rowsPerPage",e)},"update:items-per-page":function(e){return t.$set(t.pagination,"rowsPerPage",e)}},scopedSlots:t._u([{key:"item",fn:function(e){return[a("tr",[a("td",[a("vue-user",{attrs:{user:e.item.employee}})],1),a("td",{},[a("div",[t._v(" "+t._s(e.item.created_at.substring(0,10))+" ")]),a("div",{staticClass:"grey--text"},[t._v(" "+t._s(t.getTime(e.item.created_at))+" ")])]),a("td",{staticClass:"text-center"},["Requested"===e.item.status?a("approval-chip",{attrs:{"user-detail":e.item.recipient,status:e.item.status}}):"hr"===t.as&&"Approved"===e.item.status&&e.item.hr_approval&&Object.keys(e.item.hr_approval).length?a("v-chip",{attrs:{color:"purple",outlined:"",small:""}},[t._v(" Proceeded to Offboarding ")]):a("v-chip",{attrs:{color:t.$options.tabs[e.item.status],outlined:"",small:""}},[t._v(" "+t._s(e.item.status)+" ")])],1),a("td",[a("vue-context-menu",{attrs:{"context-list":[{name:"View Details",icon:"mdi-eye-outline",color:"blue"}]},on:{click0:function(a){t.requestDetails=e.item,t.openRequestDetail=!0}}})],1)])]}}])},[a("template",{slot:"no-data"},[a("data-table-no-data",{attrs:{loading:t.loading,search:t.search}})],1)],2)],1),a("v-bottom-sheet",{attrs:{scrollable:"",persistent:""},on:{keypress:function(e){if(!e.type.indexOf("key")&&t._k(e.keyCode,"esc",27,e.key,["Esc","Escape"]))return null;t.openRequestDetail=!1}},model:{value:t.openRequestDetail,callback:function(e){t.openRequestDetail=e},expression:"openRequestDetail"}},[t.openRequestDetail?a("view-resignation-details",{attrs:{as:t.as,details:t.requestDetails},on:{success:function(e){return t.loadDataTableChange()},close:function(e){t.openRequestDetail=!1}}}):t._e()],1)],1)},i=[],n=(a("ac1f"),a("841c"),a("4de4"),a("847b")),r=a("a51f"),o=a("e4bf"),c=a("bab2"),l=a("02cb"),u=a("e88d"),d=a("1806"),p={components:{ApprovalChip:u["a"],VueContextMenu:o["default"],DataTableNoData:r["default"],VueUser:l["default"],ViewResignationDetails:c["a"]},mixins:[d["a"]],props:{as:{type:String,default:""},endpoint:{type:String,default:null}},tabs:{Requested:"orange",Approved:"green",Denied:"red",Canceled:"grey",All:"cyan"},data:function(){return{requestDetails:{},filter:{search:"",show:!1},search:"",openRequestDetail:!1,crud:{name:"Resignation Request",endpoint:{common:"",get:"",post:"",put:"",patch:"",delete:""},dataTableFetch:!0},dateFilter:{},headers:[{text:"Requested By",align:"left",value:"employee"},{text:"Requested Date",align:"",value:"created_at"},{text:"Status",align:"center",sortable:!1},{text:"Action",align:"",sortable:!1}],rowsPerPageItems:[10,20,30,40,50],activeTab:0,loading:!1,status:"Requested"}},computed:{DataTableFilter:function(){return{status:"All"===this.status?"":this.status,search:this.filter.search||""}}},created:function(){this.crud.endpoint.common=this.endpoint||n["a"].getResignationRequest(this.getOrganizationSlug)+"?as=".concat(this.as)},methods:{getTime:function(t){return this.$dayjs(t).format("hh:mm:ss")}}},m=p,h=a("2877"),f=a("6544"),v=a.n(f),g=a("288c"),b=a("8336"),y=a("b0af"),x=a("cc20"),_=a("62ad"),D=a("8fea"),w=a("ce7e"),C=a("132d"),k=a("0fd9b"),S=a("0789"),V=a("71a3"),T=a("fe57"),q=Object(h["a"])(m,s,i,!1,null,null,null);e["a"]=q.exports;v()(q,{VBottomSheet:g["a"],VBtn:b["a"],VCard:y["a"],VChip:x["a"],VCol:_["a"],VDataTable:D["a"],VDivider:w["a"],VIcon:C["a"],VRow:k["a"],VSlideYTransition:S["g"],VTab:V["a"],VTabs:T["a"]})},5660:function(t,e,a){"use strict";a.r(e);var s=function(){var t=this,e=t.$createElement,a=t._self._c||e;return a("div",{staticClass:"d-flex space-between"},[a("v-autocomplete",{key:t.componentKey,ref:"autoComplete",class:t.appliedClass,attrs:{id:t.id,items:t.itemsSorted,"search-input":t.search,loading:t.isLoading,multiple:t.multiple,label:t.label,error:t.errorMessages.length>0,"error-messages":t.errorMessages,disabled:t.disabled,readonly:t.readonly,"data-cy":"autocomplete-"+t.dataCyVariable,"prepend-inner-icon":t.prependInnerIcon,clearable:t.clearable&&!t.readonly,"hide-details":t.hideDetails,"item-text":t.itemText,"item-value":t.itemValue,"small-chips":t.multiple||t.chips,"deletable-chips":t.multiple,hint:t.hint,"persistent-hint":t.persistentHint,chips:t.chips,solo:t.solo,flat:t.flat,"cache-items":t.cacheItems,placeholder:t.placeholder,dense:t.dense,"hide-selected":"","hide-no-data":""},on:{"update:searchInput":function(e){t.search=e},"update:search-input":function(e){t.search=e},focus:t.populateOnFocus,keydown:function(e){return!e.type.indexOf("key")&&t._k(e.keyCode,"enter",13,e.key,"Enter")?null:(e.preventDefault(),t.searchText())},change:t.updateState,blur:function(e){return t.$emit("blur")}},scopedSlots:t._u([{key:"selection",fn:function(e){return[t._t("selection",(function(){return[t.itemText&&e.item?a("div",[t.multiple||t.chips?a("v-chip",{attrs:{close:(t.clearable||!t.clearable&&!t.multiple)&&!t.readonly,small:""},on:{"click:close":function(a){return t.remove(e.item)}}},[e.item[t.itemText]?a("div",[e.item[t.itemText].length>40?a("v-tooltip",{attrs:{top:""},scopedSlots:t._u([{key:"activator",fn:function(s){var i=s.on;return[a("span",t._g({},i),[t._v(" "+t._s(t._f("truncate")(e.item[t.itemText],40)))])]}}],null,!0)},[a("span",[t._v(t._s(e.item[t.itemText]))])]):a("span",[t._v(t._s(e.item[t.itemText]))])],1):a("div",[a("span",[t._v(t._s(e.item))])])]):a("div",[e.item[t.itemText]?a("div",[e.item[t.itemText].length>40?a("v-tooltip",{attrs:{top:""},scopedSlots:t._u([{key:"activator",fn:function(s){var i=s.on;return[a("span",t._g({},i),[t._v(" "+t._s(t._f("truncate")(e.item[t.itemText],40)))])]}}],null,!0)},[a("span",[t._v(t._s(e.item[t.itemText]))])]):a("span",[t._v(t._s(e.item[t.itemText]))])],1):a("div",[a("span",[t._v(t._s(e.item))])])])],1):t._e()]}),{props:e})]}},{key:"item",fn:function(e){return[a("v-list-item-content",[a("v-list-item-title",[t._t("item",(function(){return[t.itemText&&e.item?a("div",[e.item[t.itemText]?a("div",[e.item[t.itemText].length>40?a("v-tooltip",{attrs:{top:""},scopedSlots:t._u([{key:"activator",fn:function(s){var i=s.on;return[a("span",t._g({},i),[t._v(" "+t._s(t._f("truncate")(e.item[t.itemText],40)))])]}}],null,!0)},[a("span",[t._v(t._s(e.item[t.itemText]))])]):a("span",[t._v(t._s(e.item[t.itemText]))])],1):a("div",[a("span",[t._v(t._s(e.item))])])]):t._e()]}),{props:e})],2)],1)]}},{key:"append-item",fn:function(){return[!t.fullyLoaded&&t.showMoreIcon?a("div",[a("v-list-item-content",{staticClass:"px-4 pointer primary--text font-weight-bold"},[a("v-list-item-title",{on:{click:function(e){return t.fetchData()}}},[t._v(" Load More Items ... ")])],1)],1):t._e()]},proxy:!0}],null,!0),model:{value:t.selectedData,callback:function(e){t.selectedData=e},expression:"selectedData"}}),t._t("default")],2)},i=[],n=a("2909"),r=a("5530"),o=a("53ca"),c=a("1da1"),l=(a("96cf"),a("a9e3"),a("ac1f"),a("841c"),a("7db0"),a("d81d"),a("159b"),a("4de4"),a("4e827"),a("2ca0"),a("d3b7"),a("c740"),a("a434"),a("3ca3"),a("ddb0"),a("2b3d"),a("caad"),a("2532"),a("63ea")),u=a.n(l),d={props:{value:{type:[Number,String,Array,Object],default:void 0},id:{type:String,default:""},dataCyVariable:{type:String,default:""},endpoint:{type:String,default:""},itemText:{type:String,required:!0},itemValue:{type:String,required:!0},params:{type:Object,required:!1,default:function(){return{}}},itemsToExclude:{type:[Array,Number],default:null},forceFetch:{type:Boolean,default:!1},staticItems:{type:Array,default:function(){return[]}},errorMessages:{type:[String,Array],default:function(){return[]}},label:{type:String,default:""},disabled:{type:Boolean,default:!1},readonly:{type:Boolean,default:!1},hint:{type:String,default:void 0},persistentHint:{type:Boolean,required:!1,default:!1},multiple:{type:Boolean,required:!1,default:!1},clearable:{type:Boolean,default:!0},hideDetails:{type:Boolean,default:!1},solo:{type:Boolean,default:!1},flat:{type:Boolean,default:!1},chips:{type:Boolean,default:!1},prependInnerIcon:{type:String,default:void 0},cacheItems:{type:Boolean,default:!1},appliedClass:{type:String,default:""},placeholder:{type:String,default:""},dense:{type:Boolean,default:!1}},data:function(){return{componentKey:0,items:[],selectedData:null,search:null,initialFetchStarted:!1,nextLimit:null,nextOffset:null,showMoreIcon:!1,fullyLoaded:!1,isLoading:!1}},computed:{itemsSorted:function(){return this.sortBySearch(this.items,this.search?this.search.toLowerCase():"")}},watch:{value:{handler:function(){var t=Object(c["a"])(regeneratorRuntime.mark((function t(e){var a,s,i,n,r=this;return regeneratorRuntime.wrap((function(t){while(1)switch(t.prev=t.next){case 0:if(!e){t.next=10;break}if(!this.forceFetch||this.initialFetchStarted){t.next=6;break}return this.initialFetchStarted=!0,t.next=5,this.fetchData();case 5:this.removeDuplicateItem();case 6:Array.isArray(e)?(i=[],"object"===Object(o["a"])(e[0])?(this.selectedData=e.map((function(t){return t[r.itemValue]})),e.forEach((function(t){var e=r.items.find((function(e){return e===t}));e||i.push(t)}))):(e.forEach((function(t){var e=r.items.find((function(e){return e[r.itemValue]===t}));e||i.push(t)})),this.selectedData=e),i.length>0&&(n=this.items).push.apply(n,i)):"object"===Object(o["a"])(e)?(this.selectedData=e[this.itemValue],a=this.items.find((function(t){return t[r.itemValue]===e})),a||this.items.push(e)):(this.selectedData=e,s=this.items.find((function(t){return t===e})),s||this.items.push(e)),this.updateData(this.selectedData),t.next=11;break;case 10:e||(this.selectedData=null);case 11:case"end":return t.stop()}}),t,this)})));function e(e){return t.apply(this,arguments)}return e}(),immediate:!0},selectedData:function(t){this.updateData(t)},params:{handler:function(t,e){u()(t,e)||(this.fullyLoaded=!1,this.initialFetchStarted=!1,this.items=[],this.componentKey+=1)},deep:!0}},methods:{sortBySearch:function(t,e){var a=this.itemText,s=t.filter((function(t){return"object"===Object(o["a"])(t)}));return s.sort((function(t,s){return t[a].toLowerCase().startsWith(e)&&s[a].toLowerCase().startsWith(e)?t[a].toLowerCase().localeCompare(s[a].toLowerCase()):t[a].toLowerCase().startsWith(e)?-1:s[a].toLowerCase().startsWith(e)?1:t[a].toLowerCase().localeCompare(s[a].toLowerCase())}))},populateOnFocus:function(){var t=this;return Object(c["a"])(regeneratorRuntime.mark((function e(){return regeneratorRuntime.wrap((function(e){while(1)switch(e.prev=e.next){case 0:if(!t.initialFetchStarted){e.next=2;break}return e.abrupt("return");case 2:return t.initialFetchStarted=!0,e.next=5,t.fetchData();case 5:t.removeDuplicateItem();case 6:case"end":return e.stop()}}),e)})))()},fetchData:function(){var t=this;return Object(c["a"])(regeneratorRuntime.mark((function e(){var a,s;return regeneratorRuntime.wrap((function(e){while(1)switch(e.prev=e.next){case 0:if(!(t.staticItems.length>0)){e.next=3;break}return t.items=t.staticItems,e.abrupt("return");case 3:return a=t.nextLimit,s=t.nextOffset,t.search&&(a=null,s=null),t.isLoading=!0,e.next=9,t.$http.get(t.endpoint,{params:Object(r["a"])(Object(r["a"])({},t.params),{},{search:t.search,limit:a,offset:s})}).then((function(e){var a;e.results||(e.results=e),e.next?(t.showMoreIcon=!0,t.extractLimitOffset(e.next)):(t.showMoreIcon=!1,t.search||(t.fullyLoaded=!0)),t.itemsToExclude&&(e.results=t.excludeRecord(e.results)),(a=t.items).push.apply(a,Object(n["a"])(e.results))})).finally((function(){t.isLoading=!1}));case 9:case"end":return e.stop()}}),e)})))()},removeDuplicateItem:function(){var t=this,e=this.items.indexOf(this.selectedData);if(e>=0){var a=this.items.findIndex((function(e){return e[t.itemValue]===t.selectedData}));a>=0&&(this.items.splice(e,1),this.componentKey+=1)}},updateData:function(t){var e=this,a=[];t instanceof Array?t.forEach((function(t){a.unshift(e.items.find((function(a){return a[e.itemValue]===t})))})):a=this.items.find((function(a){return a[e.itemValue]===t})),this.$emit("input",t),this.$emit("update:selectedFullData",a)},searchText:function(){0!==this.$refs.autoComplete.filteredItems.length||this.fullyLoaded||this.fetchData()},extractLimitOffset:function(t){var e=new URL(t);this.nextLimit=e.searchParams.get("limit"),this.nextOffset=e.searchParams.get("offset")},excludeRecord:function(t){var e=this,a=[];return"number"===typeof this.itemsToExclude?a.push(this.itemsToExclude):a=this.itemsToExclude,t.filter((function(t){if(t[e.itemValue])return!a.includes(t[e.itemValue])}))},remove:function(t){if(this.selectedData instanceof Object){var e=this.selectedData.indexOf(t[this.itemValue]);e>=0&&this.selectedData.splice(e,1)}else this.selectedData=null},updateState:function(){this.search="",this.nextLimit&&(this.showMoreIcon=!0)}}},p=d,m=a("2877"),h=a("6544"),f=a.n(h),v=a("c6a6"),g=a("cc20"),b=a("5d23"),y=a("3a2f"),x=Object(m["a"])(p,s,i,!1,null,null,null);e["default"]=x.exports;f()(x,{VAutocomplete:v["a"],VChip:g["a"],VListItemContent:b["a"],VListItemTitle:b["c"],VTooltip:y["a"]})},"847b":function(t,e,a){"use strict";a("99af");e["a"]={getResignationRequest:function(t){return"/hris/".concat(t,"/resignation/")},resignationApproval:function(t){return"/hris/".concat(t,"/resignation/setting/")},statusChange:function(t,e,a){return"/hris/".concat(t,"/resignation/").concat(e,"/").concat(a,"/")},createResignation:function(t){return"/hris/".concat(t,"/resignation/")}}},abd3:function(t,e,a){},bab2:function(t,e,a){"use strict";var s=function(){var t=this,e=t.$createElement,a=t._self._c||e;return a("v-card",[a("vue-card-title",{attrs:{title:"View Resignation Request Details",subtitle:"Here you can view resignation request details",icon:"mdi-eye-outline",closable:""},on:{close:function(e){return t.$emit("close")}}}),a("v-divider"),a("v-card-text",{staticClass:"scrollbar-md"},[a("v-row",{staticClass:"mx-1"},[["approver","hr"].includes(t.as)?a("v-col",{attrs:{md:"4",cols:"6"}},[a("div",{staticClass:"font-weight-medium"},[a("v-icon",{attrs:{small:""},domProps:{textContent:t._s("mdi-account")}}),t._v(" Requested By ")],1),a("vue-user",{staticClass:"mx-5",attrs:{user:t.requestDetails.employee}})],1):t._e(),t.requestDetails.created_at?a("v-col",{attrs:{md:"4",cols:"6"}},[a("div",{staticClass:"font-weight-medium"},[a("v-icon",{attrs:{small:""},domProps:{textContent:t._s("mdi-calendar")}}),t._v(" Requested Date ")],1),a("div",{staticClass:"mx-5 black--text"},[t._v(" "+t._s(t.requestDetails.created_at.substring(0,10))+" ")]),a("div",{staticClass:"mx-5 text-caption grey--text"},[t._v(" "+t._s(t.$dayjs(t.requestDetails.created_at).format("hh:mm:ss a"))+" ")])]):t._e(),a("v-col",{attrs:{md:"4",cols:"6"}},[a("div",{staticClass:"font-weight-medium"},[a("v-icon",{attrs:{small:""},domProps:{textContent:t._s("mdi-calendar")}}),t._v(" Last Date of Service ")],1),a("div",{staticClass:"mx-5 black--text"},[t._v(" "+t._s(t.requestDetails.release_date)+" ")])]),a("v-col",{attrs:{cols:"12"}},[a("div",{staticClass:"font-weight-medium"},[a("v-icon",{attrs:{small:""},domProps:{textContent:t._s("mdi-file-document-outline")}}),t._v(" Reason For Resignation ")],1),a("div",{staticClass:"mx-5 black--text"},[t._v(" "+t._s(t.requestDetails.reason)+" ")])]),a("v-col",{attrs:{cols:"12"}},[a("div",{staticClass:"font-weight-medium"},[a("v-icon",{attrs:{small:""},domProps:{textContent:t._s("mdi-file-document-outline")}}),t._v(" Remarks ")],1),a("div",{staticClass:"mx-5 black--text",domProps:{textContent:t._s(t.requestDetails.remarks)}})]),t.requestDetails.history&&t.requestDetails.history.length?a("v-col",{attrs:{cols:"12"}},[a("supervisor-level-detail",{attrs:{"approvals-detail":t.requestDetails.approvals}})],1):t._e(),t.requestDetails.history&&t.requestDetails.history.length?a("v-col",{staticClass:"blue-grey lighten-5 text-left",attrs:{cols:"12"}},[a("timeline-history",{attrs:{"history-detail":t.requestDetails.history,feature:"resignation"}})],1):t._e(),t.hrShow?a("v-col",{attrs:{cols:"4"}},[a("vue-auto-complete",t._b({directives:[{name:"validate",rawName:"v-validate",value:"",expression:"''"}],attrs:{endpoint:t.separationEndpoint,"item-text":"title","item-value":"id"},model:{value:t.formValues.separation_type,callback:function(e){t.$set(t.formValues,"separation_type",e)},expression:"formValues.separation_type"}},"vue-auto-complete",t.veeValidate("separation_type","Separation Type *"),!1))],1):t._e(),t.approverShow||["hr"].includes(t.as)&&"Requested"===t.requestDetails.status||t.hrShow?a("v-col",{attrs:{cols:"12"}},[a("v-textarea",t._b({directives:[{name:"validate",rawName:"v-validate",value:"required|max:600",expression:"'required|max:600'"}],attrs:{rows:"2","prepend-inner-icon":"mdi-information-outline",counter:"600"},model:{value:t.formValues.remarks,callback:function(e){t.$set(t.formValues,"remarks",e)},expression:"formValues.remarks"}},"v-textarea",t.veeValidate("remarks","Remarks *"),!1))],1):t._e()],1)],1),a("v-card-actions",[a("v-spacer"),a("v-btn",{staticClass:"black--text",attrs:{text:""},on:{click:function(e){return t.$emit("close")}}},[t._v(" Cancel ")]),t.approverShow||["hr"].includes(t.as)&&"Requested"===t.requestDetails.status||t.hrShow?a("v-btn",{staticClass:"white--text",attrs:{depressed:"",color:"danger"},on:{click:function(e){return t.changeStatus("deny")}}},[t._v(" Deny ")]):t._e(),t.approverShow?a("v-btn",{staticClass:"white--text",attrs:{depressed:"",color:"success"},on:{click:function(e){return t.changeStatus("approve")}}},[t._v(" Approve ")]):t._e(),t.hrShow?a("v-btn",{staticClass:"white--text",attrs:{depressed:"",color:"success"},on:{click:function(e){return t.changeStatus("approve")}}},[t._v(" Proceed To Offboarding ")]):t._e()],1)],1)},i=[],n=a("1da1"),r=(a("96cf"),a("caad"),a("b64b"),a("99af"),a("c44a")),o=a("847b"),c=a("6a79"),l=a("4c75"),u=a("f7ee"),d=a("02cb"),p=a("5660"),m={components:{TimelineHistory:c["a"],SupervisorLevelDetail:l["a"],VueUser:d["default"],VueAutoComplete:p["default"]},mixins:[r["a"]],props:{as:{type:String,default:""},details:{type:Object,required:!0,default:function(){return{}}}},data:function(){return{loading:!1,requestDetails:{},endpoint:"",dataToPost:{},separationEndpoint:u["a"].getSeparationType(this.$route.params.slug)+"?category=Resigned",formValues:{remarks:""}}},computed:{hrShow:function(){return["hr"].includes(this.as)&&"Approved"===this.requestDetails.status&&!this.requestDetails.hr_approval||this.requestDetails.hr_approval&&!Object.keys(this.requestDetails.hr_approval).length},approverShow:function(){return["approver"].includes(this.as)&&"Requested"===this.requestDetails.status&&this.requestDetails.recipient&&this.requestDetails.recipient.id===this.getAuthStateUserId}},mounted:function(){this.details.id&&this.getDetails()},methods:{changeStatus:function(t){var e=this;return Object(n["a"])(regeneratorRuntime.mark((function a(){return regeneratorRuntime.wrap((function(a){while(1)switch(a.prev=a.next){case 0:return"hr"===e.as&&"approve"===t?(e.endpoint=o["a"].statusChange(e.getOrganizationSlug,e.details.id,t)+"final/?as=hr",e.dataToPost={separation_type:e.formValues.separation_type,remarks:e.formValues.remarks}):(e.endpoint=o["a"].statusChange(e.getOrganizationSlug,e.details.id,t)+"?as=".concat(e.as),e.dataToPost={remarks:e.formValues.remarks}),a.next=3,e.validateAllFields();case 3:if(!a.sent){a.next=5;break}e.$http.post(e.endpoint,e.dataToPost).then((function(){"hr"===e.as&&"approve"===t?e.$router.push({name:"admin-slug-hris-employees-employee-separation-offboarding",params:{slug:e.getOrganizationSlug}}):(e.$emit("close"),e.$emit("success")),e.notifyUser("Successfully ".concat(t," request"))})).catch((function(t){e.pushErrors(t),e.notifyInvalidFormResponse()}));case 5:case"end":return a.stop()}}),a)})))()},getDetails:function(){var t=this;this.$http.get("hris/".concat(this.getOrganizationSlug,"/resignation/").concat(this.details.id)+"?as=".concat(this.as)).then((function(e){t.requestDetails=e})).catch((function(e){t.pushErrors(e),t.notifyInvalidFormResponse()}))}}},h=m,f=a("2877"),v=a("6544"),g=a.n(v),b=a("8336"),y=a("b0af"),x=a("99d9"),_=a("62ad"),D=a("ce7e"),w=a("132d"),C=a("0fd9b"),k=a("2fa4"),S=a("a844"),V=Object(f["a"])(h,s,i,!1,null,null,null);e["a"]=V.exports;g()(V,{VBtn:b["a"],VCard:y["a"],VCardActions:x["a"],VCardText:x["c"],VCol:_["a"],VDivider:D["a"],VIcon:w["a"],VRow:C["a"],VSpacer:k["a"],VTextarea:S["a"]})},f7ee:function(t,e,a){"use strict";a("99af");e["a"]={getSeparationType:function(t){return"/hris/".concat(t,"/employment/separation-type/")},postSeparationType:function(t){return"/hris/".concat(t,"/employment/separation-type/")},updateSeparationType:function(t,e){return"/hris/".concat(t,"/employment/separation-type/").concat(e,"/")},deleteSeparationType:function(t,e){return"/hris/".concat(t,"/employment/separation-type/").concat(e,"/")}}}}]);