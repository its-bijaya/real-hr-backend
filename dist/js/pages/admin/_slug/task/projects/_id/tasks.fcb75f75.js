(window["webpackJsonp"]=window["webpackJsonp"]||[]).push([["pages/admin/_slug/task/projects/_id/tasks","chunk-26c51c79","chunk-31f8a6e6","chunk-1b4245df","chunk-2d0e6279"],{"0549":function(t,e,a){"use strict";a.r(e);var s=function(){var t=this,e=t.$createElement,a=t._self._c||e;return a("div",[a("v-row",{staticClass:"mb-3",attrs:{"no-gutters":""}},[t.breadCrumbs?a("v-col",{attrs:{cols:"12"}},[a("v-card",{attrs:{flat:""}},[a("v-breadcrumbs",{staticClass:"text-body-1 pa-2",class:{"text-caption pa-1":t.$vuetify.breakpoint.xs},attrs:{items:t.breadCrumbs},scopedSlots:t._u([{key:"item",fn:function(e){return[a("span",{class:e.item.disabled?"grey--text":"baseColor--text text--accent-2 pointer",domProps:{textContent:t._s(e.item.text)},on:{click:function(a){return t.$router.push(e.item.to)}}})]}}],null,!1,1670153796)},[a("v-icon",{attrs:{slot:"divider"},slot:"divider"},[t._v("mdi-chevron-right")])],1)],1)],1):t._e()],1),a("v-row",{attrs:{"no-gutters":""}},[a("v-col",{attrs:{cols:"12"}},[t._t("default")],2)],1)],1)},i=[],n=a("5530"),r=(a("ac1f"),a("1276"),a("b0c0"),a("2f62")),o={props:{title:{type:String,required:!0},breadCrumbs:{type:Array,default:function(){return[]}}},computed:Object(n["a"])({},Object(r["c"])({getOrganizationName:"organization/getOrganizationName",getSupervisorSwitchedOrganization:"supervisor/getSwitchedOrganization"})),mounted:function(){document.title="".concat(this.title," | RealHRsoft");var t=this.$route.params.slug?"admin-slug-dashboard":"root",e=this.$route.name.split("-"),a=this.getOrganizationName;this.getSupervisorSwitchedOrganization&&"user"===e[0]&&"supervisor"===e[1]&&(a=this.getSupervisorSwitchedOrganization.name),this.breadCrumbs.unshift({text:a,disabled:!1,to:{name:t,params:{slug:this.$route.params.slug}}})}},l=o,d=a("2877"),u=a("6544"),c=a.n(u),p=a("2bc5"),h=a("b0af"),f=a("62ad"),g=a("132d"),m=a("0fd9b"),v=Object(d["a"])(l,s,i,!1,null,null,null);e["default"]=v.exports;c()(v,{VBreadcrumbs:p["a"],VCard:h["a"],VCol:f["a"],VIcon:g["a"],VRow:m["a"]})},"17cc":function(t,e,a){"use strict";var s=a("b85c"),i=a("1da1"),n=a("5530");a("96cf"),a("ac1f"),a("841c"),a("d3b7"),a("3ca3"),a("ddb0"),a("2b3d"),a("b64b");e["a"]={data:function(){return{fetchedResults:[],response:{},extra_data:"",appliedFilters:{},footerProps:{itemsPerPageOptions:[10,20,30,40,50,100]},pagination:{sortBy:["modified_at"],descending:!1,totalItems:0,page:1,rowsPerPage:10,pageCount:0},triggerDataTable:!0,fullParams:""}},created:function(){this.getParams(this.DataTableFilter)},methods:{getParams:function(t){var e=Object(n["a"])(Object(n["a"])({},t),{},{offset:(this.pagination.page-1)*this.pagination.rowsPerPage,limit:this.pagination.rowsPerPage,ordering:this.pagination.descending?this.pagination.sortBy:"-"+this.pagination.sortBy});this.fullParams=this.convertToURLSearchParams(e)},loadDataTable:function(t){this.response=t,this.fetchedResults=t.results,this.pagination.totalItems=t.count,this.extra_data=t.extra_data,this.triggerDataTable=!0},fetchData:function(t){var e=this;return Object(i["a"])(regeneratorRuntime.mark((function a(){var s,i;return regeneratorRuntime.wrap((function(a){while(1)switch(a.prev=a.next){case 0:return console.warn("DatatableMixin: fetchData has been deprecated. Please use the function in page itself."),s=Object(n["a"])(Object(n["a"])(Object(n["a"])({},t),e.appliedFilters),{},{search:e.search,offset:(e.pagination.page-1)*e.pagination.rowsPerPage,limit:e.pagination.rowsPerPage,ordering:e.pagination.descending?e.pagination.sortBy:"-"+e.pagination.sortBy}),i=e.convertToURLSearchParams(s),e.loading=!0,a.next=6,e.$http.get(e.endpoint,{params:i}).then((function(t){e.response=t,e.fetchedResults=t.results,e.pagination.totalItems=t.count})).finally((function(){e.loading=!1}));case 6:case"end":return a.stop()}}),a)})))()},applyFilters:function(t){this.appliedFilters=t,this.fetchData(t)},convertToURLSearchParams:function(t){for(var e=new URLSearchParams,a=0,i=Object.keys(t);a<i.length;a++){var n=i[a],r=t[n];if(void 0===r&&(r=""),Array.isArray(r)){var o,l=Object(s["a"])(r);try{for(l.s();!(o=l.n()).done;){var d=o.value;e.append(n,d)}}catch(u){l.e(u)}finally{l.f()}}else e.append(n,r)}return e},loadDataTableChange:function(){var t=this;this.triggerDataTable&&(this.getParams(this.DataTableFilter),this.$nextTick((function(){t.fetchDataTable()})))}},watch:{DataTableFilter:function(t){this.fetchedResults=[],this.getParams(t),this.fetchDataTable(),this.pagination.page=1},"pagination.sortBy":function(){this.fetchedResults=[],this.loadDataTableChange()},"pagination.descending":function(){this.fetchedResults=[],this.loadDataTableChange()},"pagination.page":function(){this.fetchedResults=[],this.loadDataTableChange()},"pagination.rowsPerPage":function(){this.fetchedResults=[],this.loadDataTableChange()}}}},"1f09":function(t,e,a){},"2ab5":function(t,e,a){"use strict";a("9d1c")},"2bc5":function(t,e,a){"use strict";var s=a("5530"),i=(a("a15b"),a("abd3"),a("ade3")),n=a("1c87"),r=a("58df"),o=Object(r["a"])(n["a"]).extend({name:"v-breadcrumbs-item",props:{activeClass:{type:String,default:"v-breadcrumbs__item--disabled"},ripple:{type:[Boolean,Object],default:!1}},computed:{classes:function(){return Object(i["a"])({"v-breadcrumbs__item":!0},this.activeClass,this.disabled)}},render:function(t){var e=this.generateRouteLink(),a=e.tag,i=e.data;return t("li",[t(a,Object(s["a"])(Object(s["a"])({},i),{},{attrs:Object(s["a"])(Object(s["a"])({},i.attrs),{},{"aria-current":this.isActive&&this.isLink?"page":void 0})}),this.$slots.default)])}}),l=a("80d2"),d=Object(l["i"])("v-breadcrumbs__divider","li"),u=a("7560");e["a"]=Object(r["a"])(u["a"]).extend({name:"v-breadcrumbs",props:{divider:{type:String,default:"/"},items:{type:Array,default:function(){return[]}},large:Boolean},computed:{classes:function(){return Object(s["a"])({"v-breadcrumbs--large":this.large},this.themeClasses)}},methods:{genDivider:function(){return this.$createElement(d,this.$slots.divider?this.$slots.divider:this.divider)},genItems:function(){for(var t=[],e=!!this.$scopedSlots.item,a=[],s=0;s<this.items.length;s++){var i=this.items[s];a.push(i.text),e?t.push(this.$scopedSlots.item({item:i})):t.push(this.$createElement(o,{key:a.join("."),props:i},[i.text])),s<this.items.length-1&&t.push(this.genDivider())}return t}},render:function(t){var e=this.$slots.default||this.genItems();return t("ul",{staticClass:"v-breadcrumbs",class:this.classes},e)}})},3129:function(t,e,a){"use strict";var s=a("3835"),i=a("5530"),n=(a("ac1f"),a("1276"),a("d81d"),a("a630"),a("3ca3"),a("5319"),a("1f09"),a("c995")),r=a("24b2"),o=a("7560"),l=a("58df"),d=a("80d2");e["a"]=Object(l["a"])(n["a"],r["a"],o["a"]).extend({name:"VSkeletonLoader",props:{boilerplate:Boolean,loading:Boolean,tile:Boolean,transition:String,type:String,types:{type:Object,default:function(){return{}}}},computed:{attrs:function(){return this.isLoading?this.boilerplate?{}:Object(i["a"])({"aria-busy":!0,"aria-live":"polite",role:"alert"},this.$attrs):this.$attrs},classes:function(){return Object(i["a"])(Object(i["a"])({"v-skeleton-loader--boilerplate":this.boilerplate,"v-skeleton-loader--is-loading":this.isLoading,"v-skeleton-loader--tile":this.tile},this.themeClasses),this.elevationClasses)},isLoading:function(){return!("default"in this.$scopedSlots)||this.loading},rootTypes:function(){return Object(i["a"])({actions:"button@2",article:"heading, paragraph",avatar:"avatar",button:"button",card:"image, card-heading","card-avatar":"image, list-item-avatar","card-heading":"heading",chip:"chip","date-picker":"list-item, card-heading, divider, date-picker-options, date-picker-days, actions","date-picker-options":"text, avatar@2","date-picker-days":"avatar@28",heading:"heading",image:"image","list-item":"text","list-item-avatar":"avatar, text","list-item-two-line":"sentences","list-item-avatar-two-line":"avatar, sentences","list-item-three-line":"paragraph","list-item-avatar-three-line":"avatar, paragraph",paragraph:"text@3",sentences:"text@2",table:"table-heading, table-thead, table-tbody, table-tfoot","table-heading":"heading, text","table-thead":"heading@6","table-tbody":"table-row-divider@6","table-row-divider":"table-row, divider","table-row":"table-cell@6","table-cell":"text","table-tfoot":"text@2, avatar@2",text:"text"},this.types)}},methods:{genBone:function(t,e){return this.$createElement("div",{staticClass:"v-skeleton-loader__".concat(t," v-skeleton-loader__bone")},e)},genBones:function(t){var e=this,a=t.split("@"),i=Object(s["a"])(a,2),n=i[0],r=i[1],o=function(){return e.genStructure(n)};return Array.from({length:r}).map(o)},genStructure:function(t){var e=[];t=t||this.type||"";var a=this.rootTypes[t]||"";if(t===a);else{if(t.indexOf(",")>-1)return this.mapBones(t);if(t.indexOf("@")>-1)return this.genBones(t);a.indexOf(",")>-1?e=this.mapBones(a):a.indexOf("@")>-1?e=this.genBones(a):a&&e.push(this.genStructure(a))}return[this.genBone(t,e)]},genSkeleton:function(){var t=[];return this.isLoading?t.push(this.genStructure()):t.push(Object(d["s"])(this)),this.transition?this.$createElement("transition",{props:{name:this.transition},on:{afterEnter:this.resetStyles,beforeEnter:this.onBeforeEnter,beforeLeave:this.onBeforeLeave,leaveCancelled:this.resetStyles}},t):t},mapBones:function(t){return t.replace(/\s/g,"").split(",").map(this.genStructure)},onBeforeEnter:function(t){this.resetStyles(t),this.isLoading&&(t._initialStyle={display:t.style.display,transition:t.style.transition},t.style.setProperty("transition","none","important"))},onBeforeLeave:function(t){t.style.setProperty("display","none","important")},resetStyles:function(t){t._initialStyle&&(t.style.display=t._initialStyle.display||"",t.style.transition=t._initialStyle.transition,delete t._initialStyle)}},render:function(t){return t("div",{staticClass:"v-skeleton-loader",attrs:this.attrs,on:this.$listeners,class:this.classes,style:this.isLoading?this.measurableStyles:void 0},[this.genSkeleton()])}})},"5a06":function(t,e,a){"use strict";a.r(e);var s=function(){var t=this,e=t.$createElement,a=t._self._c||e;return a("vue-page-wrapper",{attrs:{title:t.htmlTitle,"bread-crumbs":t.breadCrumbItems}},[t.fetched?a("v-card",[a("vue-card-title",{attrs:{title:"Task of Project "+t.projectDetail.name,subtitle:"List of tasks related to the project",icon:"mdi-file-document-outline"}}),a("task-data-table",{attrs:{"task-endpoint":t.taskEndpoint}})],1):t._e()],1)},i=[],n=a("0549"),r=a("6df2"),o={components:{TaskDataTable:r["a"],VuePageWrapper:n["default"]},validate:function(t){var e=t.params;return/^\d+$/.test(e.id)},data:function(){return{htmlTitle:"Task Project | Tasks",breadCrumbItems:[{text:"Task Projects",disabled:!0},{text:"Tasks",disabled:!0}],taskEndpoint:"/task/projects/"+this.$route.params.id+"/tasks/?as=HR",fetched:!1,projectDetail:null}},created:function(){var t=this.$route.params.id;this.fetchProjectDetail(t)},methods:{fetchProjectDetail:function(t){var e=this,a="/task/projects/"+t+"/?as=HR";this.$http.get(a).then((function(t){e.projectDetail=t,e.fetched=!0}))}}},l=o,d=a("2877"),u=a("6544"),c=a.n(u),p=a("b0af"),h=Object(d["a"])(l,s,i,!1,null,null,null);e["default"]=h.exports;c()(h,{VCard:p["a"]})},"6df2":function(t,e,a){"use strict";var s=function(){var t=this,e=t.$createElement,a=t._self._c||e;return a("div",[a("v-data-table",{attrs:{headers:t.headers,items:t.fetchedResults,"sort-desc":t.pagination.descending,"sort-by":t.pagination.sortBy,page:t.pagination.page,"items-per-page":t.pagination.rowsPerPage,"footer-props":t.overview||t.dashboard?{itemsPerPageOptions:[10]}:t.footerProps,"server-items-length":t.pagination.totalItems,"mobile-breakpoint":0,"must-sort":"","single-expand":""},on:{"update:sortDesc":function(e){return t.$set(t.pagination,"descending",e)},"update:sort-desc":function(e){return t.$set(t.pagination,"descending",e)},"update:sortBy":function(e){return t.$set(t.pagination,"sortBy",e)},"update:sort-by":function(e){return t.$set(t.pagination,"sortBy",e)},"update:page":function(e){return t.$set(t.pagination,"page",e)},"update:itemsPerPage":function(e){return t.$set(t.pagination,"rowsPerPage",e)},"update:items-per-page":function(e){return t.$set(t.pagination,"rowsPerPage",e)}},scopedSlots:t._u([{key:"item",fn:function(e){return[a("tr",[a("td",[a("v-tooltip",{attrs:{right:""},scopedSlots:t._u([{key:"activator",fn:function(s){var i=s.on;return[a("a",t._g({on:{click:function(a){return t.viewTaskDetails(e.item.id)}}},i),[t._v(" "+t._s(e.item.id)+": "+t._s(t._f("truncate")(e.item.title,30))+" ")])]}}],null,!0)},[a("span",{domProps:{textContent:t._s(e.item.title)}})]),e.item.parent&&e.item.can_view_parent_task?a("div",{on:{click:function(a){return t.viewTaskDetails(e.item.parent.id)}}},[a("span",{domProps:{textContent:t._s("Parent task: ")}}),a("v-tooltip",{attrs:{right:""},scopedSlots:t._u([{key:"activator",fn:function(s){var i=s.on;return[a("span",t._g({on:{click:function(a){return t.viewTaskDetails(e.item.parent.id)}}},i),[t._v(t._s(t._f("truncate")(e.item.parent.title,35,"...")))])]}}],null,!0)},[a("span",{domProps:{textContent:t._s(e.item.parent.title)}})])],1):t._e(),t.recurring?a("v-icon",{domProps:{textContent:t._s(e.expanded?"mdi-menu-up":"mdi-menu-down")},on:{click:function(t){return e.expand(!e.isExpanded)}}}):t._e()],1),a("td",[a("div",[t._v(" "+t._s(t._f("dayjs")(e.item.deadline,"YYYY-MM-DD"))+" ")]),a("div",[t._v(" "+t._s(t._f("dayjs")(e.item.deadline,"h:mm a"))+" ")])]),t.overview?t._e():a("td",[a("vue-user",{attrs:{user:e.item.created_by,size:"25"}})],1),t.overview?t._e():a("td",[a("user-thumbnails",{attrs:{users:e.item.responsible_persons.map((function(t){return t.user})),"total-users":e.item.responsible_persons.length},on:{showMore:function(a){t.responsiblePerson.data=e.item.responsible_persons,t.responsiblePerson.dialog=!0}}})],1),a("td",{staticClass:"text-center"},[a("v-chip",{attrs:{color:e.item.is_delayed?"red":t.taskStatus(e.item.status-1).color,outlined:"",small:""}},[a("span",[t._v(" "+t._s(t.taskStatus(e.item.status-1).text)+" ")])])],1),t.overview?t._e():a("td",{staticClass:"text-center"},[a("span",{class:{"red--text":"CRITICAL"===e.item.priority},domProps:{textContent:t._s(e.item.priority)}})])])]}},{key:"expanded-item",fn:function(e){var s=e.item,i=e.headers;return[a("td",{attrs:{colspan:i.length}},[a("v-card",{attrs:{flat:""}},t._l(s.recurring_task_queue,(function(e,s){return a("ul",{key:s},[e.created_task?a("li",[a("v-tooltip",{attrs:{right:""},scopedSlots:t._u([{key:"activator",fn:function(s){var i=s.on;return[a("a",t._g({on:{click:function(a){return t.viewTaskDetails(e.created_task.id)}}},i),[t._v(" "+t._s(e.created_task.id)+": "+t._s(e.created_task.title)+" ")])]}}],null,!0)},[a("span",{domProps:{textContent:t._s(e.created_task.title)}})]),a("v-col",[a("div",[t._v(" Deadline: "),a("span",[t._v(t._s(e.created_task.deadline))])]),a("div",[t._v(" Priority: "),a("span",[t._v(t._s(e.created_task.priority))])]),a("div",[t._v(" Status: "),a("span",[t._v(t._s(t.taskStatusMap[e.created_task.status-1]))])])])],1):a("li",[t._v(" A new task will be created at "+t._s(t.humanizeDate(e.timestamp))+" ")])])})),0)],1)]}}])},[a("template",{slot:"no-data"},[a("data-table-no-data",{attrs:{loading:t.loading}})],1)],2),t.responsiblePerson.dialog?a("user-list-dialog",{attrs:{users:t.responsiblePerson.data.map((function(t){return t.user}))},on:{close:function(e){t.responsiblePerson.dialog=!1}},model:{value:t.responsiblePerson.dialog,callback:function(e){t.$set(t.responsiblePerson,"dialog",e)},expression:"responsiblePerson.dialog"}}):t._e()],1)},i=[],n=(a("d3b7"),a("17cc")),r=a("cde3"),o=a("02cb"),l=a("a51f"),d=a("9815"),u={components:{DataTableNoData:l["default"],UserThumbnails:r["default"],VueUser:o["default"],UserListDialog:d["default"]},mixins:[n["a"]],props:{taskEndpoint:{type:String,required:!0},taskSearch:{type:String,required:!1,default:function(){return""}},taskSummary:{type:Object,required:!1,default:function(){return{}}},overview:{type:Boolean,default:!1},dashboard:{type:Boolean,default:!1},recurring:{type:Boolean,default:!1}},data:function(){return{loading:!1,fullHeaders:[{text:"Title",align:"left",sortable:!1},{text:"Deadline",align:"left",sortable:!0,value:"deadline"},{text:"Assigned BY",align:"left",sortable:!1},{text:"Assigned TO",align:"left",sortable:!1},{text:"Status",align:"center",sortable:!1},{text:"Priority",align:"left",sortable:!1}],taskStatusMap:["Pending","In Progress","On Hold","Completed","Closed"],overviewHeaders:[{text:"Title",align:"left",sortable:!1},{text:"Deadline",align:"left",sortable:!0,value:"deadline"},{text:"Status",align:"center",sortable:!1}],headers:[],search:"",showAllResponsiblePerson:!1,responsiblePerson:{dialog:!1,data:[]}}},watch:{taskEndpoint:function(t){t&&this.refreshDataTable(t)}},created:function(){this.headers=this.overview?this.overviewHeaders:this.fullHeaders,this.loadDataTableChange()},methods:{fetchDataTable:function(){var t=this;this.loading=!0,this.$http.get(this.taskEndpoint,{params:this.fullParams}).then((function(e){t.loadDataTable(e),t.$emit("update:taskSummary",e.summary)})).finally((function(){t.loading=!1}))},viewTaskDetails:function(t){var e=this.get(this.$route.params,"slug");this.$router.push({name:e?"admin-slug-task-id-detail":"user-task-my-id-detail",params:{id:t,slug:e||""}})},refreshDataTable:function(){this.fetchDataTable()},taskStatus:function(t){var e=[{text:"Pending",color:"amber"},{text:"In Progress",color:"blue"},{text:"On Hold",color:"pink accent-1"},{text:"Completed",color:"green"},{text:"Closed",color:"purple"}];return e[t]},humanizeDate:function(t){return this.$dayjs(t).format("YYYY-MM-DD")}}},c=u,p=(a("e076"),a("2877")),h=a("6544"),f=a.n(h),g=a("b0af"),m=a("cc20"),v=a("62ad"),b=a("8fea"),y=a("132d"),_=a("3a2f"),k=Object(p["a"])(c,s,i,!1,null,null,null);e["a"]=k.exports;f()(k,{VCard:g["a"],VChip:m["a"],VCol:v["a"],VDataTable:b["a"],VIcon:y["a"],VTooltip:_["a"]})},"8df9":function(t,e,a){},9815:function(t,e,a){"use strict";a.r(e);var s=function(){var t=this,e=t.$createElement,a=t._self._c||e;return a("v-dialog",{attrs:{width:"500",persistent:"",scrollable:""},on:{keydown:function(e){return!e.type.indexOf("key")&&t._k(e.keyCode,"esc",27,e.key,["Esc","Escape"])?null:t.$emit("input",!1)}},model:{value:t.dialog,callback:function(e){t.dialog=e},expression:"dialog"}},[a("v-card",[a("vue-card-title",{attrs:{title:t.title,subtitle:"List of Employees",icon:"mdi-account-group-outline",dark:"",closable:""},on:{close:function(e){return t.$emit("input",!1)}}}),a("v-divider"),t.headerInfo?a("v-list",{staticClass:"primaryLight pl-9 pr-5 py-0"},[a("v-list-item",[a("v-list-item-content",{staticClass:"text-body-1",attrs:{md:"5"}},[t._v(" Name ")]),a("v-list-item-action",{staticClass:"text-body-1 text-center"},[t._v(" "+t._s(t.headerInfo)+" ")])],1)],1):t._e(),a("v-divider"),a("v-card-text",{staticClass:"pb-0"},[t.endpoint||0!==t.users.length?t._e():a("div",[a("vue-no-data")],1),t.userInstance&&t.userInstance.length?a("v-list",t._l(t.userInstance,(function(e){return a("v-list-item",{key:e.id},[a("v-list-item-content",[a("vue-user",{attrs:{user:e.liked_by||e.user||e}})],1),t._l(t.infoList,(function(s,i){return[a("v-list-item-action",{key:i},[a("span",[i>0?a("span",[a("span",[t._v("|")])]):t._e(),t._v(" "+t._s(e[s])+" ")])])]})),a("v-list-item-action",[t._t("info",null,{user:e})],2)],2)})),1):t._e(),t.dialog&&t.endpoint?a("div",[a("infinite-loading-base",{attrs:{endpoint:t.endpoint,"response-key":t.responseKey},on:{setInfiniteResponse:t.setInfiniteResponse}})],1):t._e()],1)],1)],1)},i=[],n=a("2909"),r=(a("99af"),a("e585")),o=a("02cb"),l=a("cdd1"),d={components:{VueUser:o["default"],VueNoData:r["default"],InfiniteLoadingBase:l["a"]},extends:l["a"],props:{value:{type:Boolean,default:!1},users:{type:Array,default:function(){return[]}},title:{type:String,default:"List Of Employees"},infoList:{type:Array,default:function(){return[]}},endpoint:{type:String,default:""},headerInfo:{type:String,default:""},responseKey:{type:String,default:"results"}},data:function(){return{userInstance:[],dialog:this.value,fetched:!this.endpoint}},watch:{value:function(t){this.dialog=t,this.userInstance=this.users}},created:function(){this.userInstance=Object(n["a"])(this.users)},methods:{setInfiniteResponse:function(t){this.userInstance=this.userInstance.concat(t[this.responseKey])}}},u=d,c=a("2877"),p=a("6544"),h=a.n(p),f=a("b0af"),g=a("99d9"),m=a("169a"),v=a("ce7e"),b=a("8860"),y=a("da13"),_=a("1800"),k=a("5d23"),x=Object(c["a"])(u,s,i,!1,null,null,null);e["default"]=x.exports;h()(x,{VCard:f["a"],VCardText:g["c"],VDialog:m["a"],VDivider:v["a"],VList:b["a"],VListItem:y["a"],VListItemAction:_["a"],VListItemContent:k["a"]})},"9d1c":function(t,e,a){},a51f:function(t,e,a){"use strict";a.r(e);var s=function(){var t=this,e=t.$createElement,a=t._self._c||e;return a("div",[t.search.length>0?a("span",[t._v(' Your search for "'+t._s(t.search)+'" found no results. ')]):t.loading?a("v-skeleton-loader",{attrs:{type:"table",height:t.skeletonLoaderHeight}}):a("no-data-found",{attrs:{text:t.text,height:t.height}},[t._t("default")],2)],1)},i=[],n=(a("a9e3"),a("e585")),r={components:{NoDataFound:n["default"]},props:{search:{type:String,default:""},loading:{type:Boolean,required:!0},text:{type:String,default:"No data available at the moment"},height:{type:[String,Number],default:200},skeletonLoaderHeight:{type:[String,Number],default:void 0}}},o=r,l=a("2877"),d=a("6544"),u=a.n(d),c=a("3129"),p=Object(l["a"])(o,s,i,!1,null,null,null);e["default"]=p.exports;u()(p,{VSkeletonLoader:c["a"]})},abd3:function(t,e,a){},cde3:function(t,e,a){"use strict";a.r(e);var s=function(){var t=this,e=t.$createElement,a=t._self._c||e;return a("div",[a("div",{staticClass:"download-only"},t._l(t.users,(function(e,s){return a("v-chip",{key:s,staticClass:"ma-1",attrs:{small:"",label:""}},[t._v(" "+t._s(e.full_name)+" ")])})),1),a("v-row",{staticClass:"download-hidden",attrs:{"no-gutters":""}},[t.users&&!t.users.length?a("div",[a("v-col",{staticClass:"ma-0 pa-0"},[a("v-avatar",{staticClass:"mr-1",attrs:{size:"20"}},[a("v-img",{attrs:{src:"/images/info/user-default.png"}})],1),a("span",{staticClass:"grey--text text-caption"},[t._v("No Employee")])],1)],1):t._l(t.users.slice(0,3),(function(e,s){return a("div",{key:s,staticClass:"text-left"},[a("v-badge",{attrs:{dot:"",right:"",bottom:"",overlap:"","offset-y":"5",color:e.user&&e.user.is_online?"green":"transparent"}},[a("v-tooltip",{attrs:{top:""},scopedSlots:t._u([{key:"activator",fn:function(s){var i=s.on;return[a("a",[a("v-avatar",t._g({staticClass:"mr-n1",attrs:{size:t.imgSize}},i),[a("v-img",{attrs:{height:t.imgSize,width:t.imgSize,src:e.profile_picture||e.user.profile_picture},on:{click:t.showMore}})],1)],1)]}}],null,!0)},[a("span",{domProps:{textContent:t._s(e.full_name||e.user.full_name)}}),e[t.type]?a("span",[t._v(" : "),a("span",{domProps:{textContent:t._s(e[t.type])}})]):t._e()])],1)],1)})),t.users&&t.users.length&&t.totalUsers>3?a("div",[a("v-col",{staticClass:"pl-2 py-0 text-subtitle-1"},[a("a",{on:{click:t.showMore}},[t._v(" +"+t._s(parseInt(t.totalUsers)-3)+" ")])])],1):t._e()],2)],1)},i=[],n=(a("a9e3"),{name:"ThumbnailUsers",props:{users:{type:Array,default:function(){return[]}},totalUsers:{type:Number,required:!0},type:{type:String,default:""},imgSize:{type:[String,Number],default:22}},watch:{users:function(t){this.users=t}},methods:{showMore:function(){this.users&&0===this.users.length||this.$emit("showMore")}}}),r=n,o=(a("2ab5"),a("2877")),l=a("6544"),d=a.n(l),u=a("8212"),c=a("4ca6"),p=a("cc20"),h=a("62ad"),f=a("adda"),g=a("0fd9b"),m=a("3a2f"),v=Object(o["a"])(r,s,i,!1,null,"51021d54",null);e["default"]=v.exports;d()(v,{VAvatar:u["a"],VBadge:c["a"],VChip:p["a"],VCol:h["a"],VImg:f["a"],VRow:g["a"],VTooltip:m["a"]})},e076:function(t,e,a){"use strict";a("8df9")}}]);