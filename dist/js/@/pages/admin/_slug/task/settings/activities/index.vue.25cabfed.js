(window["webpackJsonp"]=window["webpackJsonp"]||[]).push([["@/pages/admin/_slug/task/settings/activities/index.vue","chunk-26c51c79","chunk-31f8a6e6","chunk-2d2259e9","chunk-2d22d378"],{"0549":function(t,e,a){"use strict";a.r(e);var i=function(){var t=this,e=t.$createElement,a=t._self._c||e;return a("div",[a("v-row",{staticClass:"mb-3",attrs:{"no-gutters":""}},[t.breadCrumbs?a("v-col",{attrs:{cols:"12"}},[a("v-card",{attrs:{flat:""}},[a("v-breadcrumbs",{staticClass:"text-body-1 pa-2",class:{"text-caption pa-1":t.$vuetify.breakpoint.xs},attrs:{items:t.breadCrumbs},scopedSlots:t._u([{key:"item",fn:function(e){return[a("span",{class:e.item.disabled?"grey--text":"baseColor--text text--accent-2 pointer",domProps:{textContent:t._s(e.item.text)},on:{click:function(a){return t.$router.push(e.item.to)}}})]}}],null,!1,1670153796)},[a("v-icon",{attrs:{slot:"divider"},slot:"divider"},[t._v("mdi-chevron-right")])],1)],1)],1):t._e()],1),a("v-row",{attrs:{"no-gutters":""}},[a("v-col",{attrs:{cols:"12"}},[t._t("default")],2)],1)],1)},n=[],s=a("5530"),r=(a("ac1f"),a("1276"),a("b0c0"),a("2f62")),o={props:{title:{type:String,required:!0},breadCrumbs:{type:Array,default:function(){return[]}}},computed:Object(s["a"])({},Object(r["c"])({getOrganizationName:"organization/getOrganizationName",getSupervisorSwitchedOrganization:"supervisor/getSwitchedOrganization"})),mounted:function(){document.title="".concat(this.title," | RealHRsoft");var t=this.$route.params.slug?"admin-slug-dashboard":"root",e=this.$route.name.split("-"),a=this.getOrganizationName;this.getSupervisorSwitchedOrganization&&"user"===e[0]&&"supervisor"===e[1]&&(a=this.getSupervisorSwitchedOrganization.name),this.breadCrumbs.unshift({text:a,disabled:!1,to:{name:t,params:{slug:this.$route.params.slug}}})}},l=o,c=a("2877"),d=a("6544"),u=a.n(d),m=a("2bc5"),p=a("b0af"),f=a("62ad"),v=a("132d"),h=a("0fd9b"),g=Object(c["a"])(l,i,n,!1,null,null,null);e["default"]=g.exports;u()(g,{VBreadcrumbs:m["a"],VCard:p["a"],VCol:f["a"],VIcon:v["a"],VRow:h["a"]})},"1f09":function(t,e,a){},2926:function(t,e,a){"use strict";a.r(e);var i=function(){var t=this,e=t.$createElement,a=t._self._c||e;return a("vue-page-wrapper",{attrs:{title:t.htmlTitle,"bread-crumbs":t.breadCrumbItems}},[a("v-card",[a("vue-card-title",{attrs:{title:"Activities",subtitle:"Here you can view the list of activities.",icon:"mdi-file-table-box-multiple-outline","data-cy-variable":"task-projects"}},[a("template",{slot:"actions"},[a("v-btn",{attrs:{small:"","data-cy":"btn-create-task-project",color:"primary",depressed:""},on:{click:function(e){return t.triggerForm("create")}}},[t._v(" Create Activity ")]),a("v-btn",{attrs:{"data-cy":"btn-filter",icon:""},on:{click:function(e){t.showFilters=!t.showFilters}}},[a("v-icon",{attrs:{small:""},domProps:{textContent:t._s("mdi-filter-variant")}})],1)],1)],2),a("v-divider"),a("v-slide-y-transition",[t.showFilters?a("div",[a("v-row",{staticClass:"px-3"},[a("v-col",[a("vue-search",{staticClass:"pa-0",attrs:{search:t.search},on:{"update:search":function(e){t.search=e}},model:{value:t.search,callback:function(e){t.search=e},expression:"search"}})],1)],1)],1):t._e()]),a("v-data-table",{attrs:{headers:t.headers,items:t.fetchedResults,loading:t.loading,"sort-desc":t.pagination.descending,"sort-by":t.pagination.sortBy,page:t.pagination.page,"items-per-page":t.pagination.rowsPerPage,"footer-props":t.footerProps,"server-items-length":t.pagination.totalItems,"mobile-breakpoint":"0","must-sort":""},on:{"update:sortDesc":function(e){return t.$set(t.pagination,"descending",e)},"update:sort-desc":function(e){return t.$set(t.pagination,"descending",e)},"update:sortBy":function(e){return t.$set(t.pagination,"sortBy",e)},"update:sort-by":function(e){return t.$set(t.pagination,"sortBy",e)},"update:page":function(e){return t.$set(t.pagination,"page",e)},"update:itemsPerPage":function(e){return t.$set(t.pagination,"rowsPerPage",e)},"update:items-per-page":function(e){return t.$set(t.pagination,"rowsPerPage",e)}},scopedSlots:t._u([{key:"item",fn:function(e){return[a("tr",[a("td",[a("v-tooltip",{attrs:{"max-width":"300",top:""},scopedSlots:t._u([{key:"activator",fn:function(i){var n=i.on,s=i.attrs;return[a("span",t._g(t._b({},"span",s,!1),n),[t._v(" "+t._s(t._f("truncate")(e.item.name,150))+" ")])]}}],null,!0)},[a("span",[t._v(t._s(e.item.name))])])],1),a("td",{staticClass:"text-center text-capitalize"},[t._v(" "+t._s(e.item.unit||"N/A")+" ")]),a("td",{staticClass:"text-center"},[t._v(t._s(e.item.employee_rate))]),a("td",{staticClass:"text-center"},[t._v(t._s(e.item.client_rate))]),a("td",[a("vue-context-menu",{attrs:{"context-list":[{name:"View Details",icon:"mdi-eye",color:"gray"},{name:"Update Details",icon:"mdi-pencil-outline",color:"blue"},{name:"Delete Details",icon:"mdi-delete-outline",color:"danger"}]},on:{click0:function(a){return t.triggerForm("view",e.item)},click1:function(a){return t.triggerForm("update",e.item)},click2:function(a){return t.triggerForm("delete",e.item)}}})],1)])]}}])},[a("template",{slot:"no-data"},[a("data-table-no-data",{attrs:{loading:t.loading}})],1)],2),a("v-dialog",{attrs:{persistent:"",width:"960"},on:{keydown:function(e){if(!e.type.indexOf("key")&&t._k(e.keyCode,"esc",27,e.key,["Esc","Escape"]))return null;t.displayForm=!1}},model:{value:t.displayForm,callback:function(e){t.displayForm=e},expression:"displayForm"}},[t.displayForm?a("activity-form",{attrs:{"action-data":t.actionData,"update-form":t.updateForm},on:{"dismiss-form":t.dismissForm}}):t._e()],1),a("v-dialog",{attrs:{persistent:"",width:"960"},on:{keydown:function(e){if(!e.type.indexOf("key")&&t._k(e.keyCode,"esc",27,e.key,["Esc","Escape"]))return null;t.displayViewDetails=!1}},model:{value:t.displayViewDetails,callback:function(e){t.displayViewDetails=e},expression:"displayViewDetails"}},[t.displayViewDetails?a("activity-view",{attrs:{"action-data":t.actionData},on:{"dismiss-form":t.dismissForm}}):t._e()],1),a("vue-dialog",{attrs:{notify:t.deleteNotification},on:{close:function(e){t.deleteNotification.dialog=!1},agree:t.deleteDataItem}})],1)],1)},n=[],s=(a("ac1f"),a("841c"),function(){var t=this,e=t.$createElement,a=t._self._c||e;return a("v-card",[a("vue-card-title",{attrs:{title:"Activity",subtitle:(t.updateForm?"Update":"Create")+" Activity",icon:"mdi-file-table-box-multiple-outline",closable:""},on:{close:function(e){return t.$emit("dismiss-form")}}}),a("v-divider"),t.nonFieldErrors?a("non-field-form-errors",{attrs:{"non-field-errors":t.nonFieldErrors}}):t._e(),a("v-card-text",{ref:"assignActivityForm"},[a("v-row",[a("v-col",{attrs:{md:"6",cols:"12"}},[a("v-text-field",t._b({directives:[{name:"validate",rawName:"v-validate",value:"required|max:255",expression:"'required|max:255'"}],attrs:{counter:255},model:{value:t.formValues.name,callback:function(e){t.$set(t.formValues,"name",e)},expression:"formValues.name"}},"v-text-field",t.veeValidate("name","Activity Name *"),!1))],1),a("v-col",{attrs:{md:"6",cols:"12"}},[a("v-select",t._b({directives:[{name:"validate",rawName:"v-validate",value:"required",expression:"'required'"}],attrs:{items:t.measuringUnit},model:{value:t.formValues.unit,callback:function(e){t.$set(t.formValues,"unit",e)},expression:"formValues.unit"}},"v-select",t.veeValidate("unit","Measuring Unit *"),!1))],1),a("v-col",{attrs:{md:"6",cols:"12"}},[a("v-text-field",t._b({directives:[{name:"validate",rawName:"v-validate",value:"required",expression:"'required'"}],attrs:{type:"number"},model:{value:t.formValues.employee_rate,callback:function(e){t.$set(t.formValues,"employee_rate",e)},expression:"formValues.employee_rate"}},"v-text-field",t.veeValidate("employee_rate","Employee Default Rate *"),!1))],1),a("v-col",{attrs:{md:"6",cols:"12"}},[a("v-text-field",t._b({directives:[{name:"validate",rawName:"v-validate",value:"required",expression:"'required'"}],attrs:{type:"number"},model:{value:t.formValues.client_rate,callback:function(e){t.$set(t.formValues,"client_rate",e)},expression:"formValues.client_rate"}},"v-text-field",t.veeValidate("client_rate","Client Default Rate *"),!1))],1),a("v-col",{attrs:{md:"6",cols:"12"}},[a("v-textarea",t._b({directives:[{name:"validate",rawName:"v-validate",value:"max:600",expression:"'max:600'"}],attrs:{counter:"600",rows:"3"},model:{value:t.formValues.description,callback:function(e){t.$set(t.formValues,"description",e)},expression:"formValues.description"}},"v-textarea",t.veeValidate("description","Activity Description"),!1))],1)],1)],1),a("v-divider"),a("v-card-actions",[a("v-spacer"),a("v-btn",{attrs:{text:"",type:"reset"},on:{click:function(e){return t.$emit("dismiss-form")}}},[t._v(" Cancel ")]),a("v-btn",{attrs:{depressed:"",color:"primary"},on:{click:t.submitForm}},[a("v-icon",{staticClass:"mr-1",attrs:{size:"14"}},[t._v(" mdi-content-save-outline ")]),t._v(" Save ")],1)],1)],1)}),r=[],o=a("f0d5"),l=a("f70a"),c={getActivity:"/task/activities/",postActivity:"/task/activities/",putActivity:function(t){return"/task/activities/".concat(t,"/")},deleteActivity:function(t){return"/task/activities/".concat(t,"/")}},d={components:{},mixins:[o["a"],l["a"]],props:{actionData:{type:Object,required:!1,default:function(){return{name:"",description:"",members:null}}},updateForm:{type:Boolean,default:!1}},data:function(){return{formValues:this.actionData,measuringUnit:[{text:"Hour",value:"hour"},{text:"Day",value:"day"},{text:"Piece",value:"piece"}]}},methods:{clearFormData:function(){this.errors.clear(),this.$refs.assignProjectForm.reset()},submitForm:function(){var t=this;this.updateForm?(this.crud.message="Successfully updated activity.",this.putData(c.putActivity(this.formValues.id)+"?as=hr",this.formValues).then((function(){t.$emit("dismiss-form")}))):(this.crud.message="Successfully created activity.",this.insertData(c.postActivity+"?as=hr",this.formValues).then((function(){t.$emit("dismiss-form")})))}}},u=d,m=a("2877"),p=a("6544"),f=a.n(p),v=a("8336"),h=a("b0af"),g=a("99d9"),b=a("62ad"),y=a("ce7e"),x=a("132d"),_=a("0fd9b"),w=a("b974"),V=a("2fa4"),k=a("8654"),C=a("a844"),D=Object(m["a"])(u,s,r,!1,null,null,null),$=D.exports;f()(D,{VBtn:v["a"],VCard:h["a"],VCardActions:g["a"],VCardText:g["c"],VCol:b["a"],VDivider:y["a"],VIcon:x["a"],VRow:_["a"],VSelect:w["a"],VSpacer:V["a"],VTextField:k["a"],VTextarea:C["a"]});var S=a("e4bf"),F=a("a51f"),O=a("8cd3"),P=a("6c6f"),A=a("0549"),T=function(){var t=this,e=t.$createElement,a=t._self._c||e;return a("v-card",[a("vue-card-title",{attrs:{title:"View Activity",subtitle:"Here you can view activity",icon:"mdi-file-table-box-multiple-outline",closable:""},on:{close:function(e){return t.$emit("dismiss-form")}}}),a("v-divider"),a("v-card-text",{ref:"assignActivityForm"},[a("v-row",[a("v-col",{attrs:{md:"6",cols:"12"}},[a("span",{staticClass:"font-weight-medium text-subtitle-1"},[t._v("Name ")]),t._v(" "),a("br"),t._v(" "+t._s(t.actionData.name)+" ")]),a("v-col",{attrs:{cols:"12",md:"6"}},[a("span",{staticClass:"font-weight-medium text-subtitle-1"},[t._v(" Unit")]),a("br"),a("span",{staticClass:"text-capitalize"},[t._v(" "+t._s(t.actionData.unit)+" ")])]),a("v-col",{attrs:{cols:"12",md:"6"}},[a("span",{staticClass:"font-weight-medium text-subtitle-1"},[t._v(" Employee Default Rate")]),a("br"),t._v(" "+t._s(t.actionData.employee_rate)+" ")]),a("v-col",{attrs:{cols:"12",md:"6"}},[a("span",{staticClass:"font-weight-medium text-subtitle-1"},[t._v(" Client Default Rate")]),a("br"),t._v(" "+t._s(t.actionData.client_rate)+" ")]),a("v-col",{attrs:{cols:"12",md:"6"}},[a("span",{staticClass:"font-weight-medium text-subtitle-1"},[t._v(" Description")]),a("br"),t._v(" "+t._s(t.actionData.description)+" ")])],1)],1),a("v-divider"),a("v-card-actions",[a("v-spacer"),a("v-btn",{attrs:{text:"",type:"reset"},on:{click:function(e){return t.$emit("dismiss-form")}}},[t._v(" Cancel ")])],1)],1)},E=[],B={props:{actionData:{type:Object,required:!1,default:function(){return{name:"",description:"",members:null}}}}},j=B,I=Object(m["a"])(j,T,E,!1,null,null,null),N=I.exports;f()(I,{VBtn:v["a"],VCard:h["a"],VCardActions:g["a"],VCardText:g["c"],VCol:b["a"],VDivider:y["a"],VRow:_["a"],VSpacer:V["a"]});var L={components:{ActivityView:N,VuePageWrapper:A["default"],ActivityForm:$,VueContextMenu:S["default"],DataTableNoData:F["default"]},mixins:[O["a"],P["a"]],props:{isHrAdmin:{type:Boolean,default:!1}},data:function(){return{htmlTitle:"Activities | Settings | Task | Admin",breadCrumbItems:[{text:"Task",disabled:!1,to:{name:"admin-slug-task-overview",params:{slug:this.$route.params.slug}}},{text:"Settings",disabled:!1,to:{name:"admin-slug-task-settings",params:{slug:this.$route.params.slug}}},{text:"Activites",disabled:!0}],deleteNotification:{heading:"Confirm Delete",text:"Are you sure you want to delete this activity?",dialog:!1},headers:[{text:"Name",value:"name",width:"40%"},{text:"Unit",value:"unit",width:"",align:"center"},{text:"Employee Default Rate",value:"employee_rate",width:"",align:"center"},{text:"Client Default Rate",value:"client_rate",sortable:!0,width:"",align:"center"},{text:"Actions",sortable:!1,width:""}],showFilters:!1,search:"",actionData:{},updateForm:!1,displayForm:!1,displayViewDetails:!1}},computed:{dataTableFilter:function(){return{search:this.search}}},created:function(){this.dataTableEndpoint=c.getActivity+"?as=hr"},methods:{triggerForm:function(t,e){"delete"===t?this.deleteNotification.dialog=!0:"update"===t?(this.updateForm=!0,this.displayForm=!0):"view"===t?this.displayViewDetails=!0:(this.updateForm=!1,this.displayForm=!0),this.actionData=e||void 0},deleteDataItem:function(){var t=this;this.crud.message="Successfully deleted activity",this.deleteData(c.deleteActivity(this.actionData.id)+"?as=hr").then((function(){t.deleteNotification.dialog=!1,t.fetchDataTable()}))},dismissForm:function(){this.actionData={},this.displayViewDetails=!1,this.displayForm=!1,this.fetchDataTable()}}},R=L,q=a("8fea"),z=a("169a"),U=a("0789"),H=a("3a2f"),M=Object(m["a"])(R,i,n,!1,null,null,null);e["default"]=M.exports;f()(M,{VBtn:v["a"],VCard:h["a"],VCol:b["a"],VDataTable:q["a"],VDialog:z["a"],VDivider:y["a"],VIcon:x["a"],VRow:_["a"],VSlideYTransition:U["g"],VTooltip:H["a"]})},"2bc5":function(t,e,a){"use strict";var i=a("5530"),n=(a("a15b"),a("abd3"),a("ade3")),s=a("1c87"),r=a("58df"),o=Object(r["a"])(s["a"]).extend({name:"v-breadcrumbs-item",props:{activeClass:{type:String,default:"v-breadcrumbs__item--disabled"},ripple:{type:[Boolean,Object],default:!1}},computed:{classes:function(){return Object(n["a"])({"v-breadcrumbs__item":!0},this.activeClass,this.disabled)}},render:function(t){var e=this.generateRouteLink(),a=e.tag,n=e.data;return t("li",[t(a,Object(i["a"])(Object(i["a"])({},n),{},{attrs:Object(i["a"])(Object(i["a"])({},n.attrs),{},{"aria-current":this.isActive&&this.isLink?"page":void 0})}),this.$slots.default)])}}),l=a("80d2"),c=Object(l["i"])("v-breadcrumbs__divider","li"),d=a("7560");e["a"]=Object(r["a"])(d["a"]).extend({name:"v-breadcrumbs",props:{divider:{type:String,default:"/"},items:{type:Array,default:function(){return[]}},large:Boolean},computed:{classes:function(){return Object(i["a"])({"v-breadcrumbs--large":this.large},this.themeClasses)}},methods:{genDivider:function(){return this.$createElement(c,this.$slots.divider?this.$slots.divider:this.divider)},genItems:function(){for(var t=[],e=!!this.$scopedSlots.item,a=[],i=0;i<this.items.length;i++){var n=this.items[i];a.push(n.text),e?t.push(this.$scopedSlots.item({item:n})):t.push(this.$createElement(o,{key:a.join("."),props:n},[n.text])),i<this.items.length-1&&t.push(this.genDivider())}return t}},render:function(t){var e=this.$slots.default||this.genItems();return t("ul",{staticClass:"v-breadcrumbs",class:this.classes},e)}})},3129:function(t,e,a){"use strict";var i=a("3835"),n=a("5530"),s=(a("ac1f"),a("1276"),a("d81d"),a("a630"),a("3ca3"),a("5319"),a("1f09"),a("c995")),r=a("24b2"),o=a("7560"),l=a("58df"),c=a("80d2");e["a"]=Object(l["a"])(s["a"],r["a"],o["a"]).extend({name:"VSkeletonLoader",props:{boilerplate:Boolean,loading:Boolean,tile:Boolean,transition:String,type:String,types:{type:Object,default:function(){return{}}}},computed:{attrs:function(){return this.isLoading?this.boilerplate?{}:Object(n["a"])({"aria-busy":!0,"aria-live":"polite",role:"alert"},this.$attrs):this.$attrs},classes:function(){return Object(n["a"])(Object(n["a"])({"v-skeleton-loader--boilerplate":this.boilerplate,"v-skeleton-loader--is-loading":this.isLoading,"v-skeleton-loader--tile":this.tile},this.themeClasses),this.elevationClasses)},isLoading:function(){return!("default"in this.$scopedSlots)||this.loading},rootTypes:function(){return Object(n["a"])({actions:"button@2",article:"heading, paragraph",avatar:"avatar",button:"button",card:"image, card-heading","card-avatar":"image, list-item-avatar","card-heading":"heading",chip:"chip","date-picker":"list-item, card-heading, divider, date-picker-options, date-picker-days, actions","date-picker-options":"text, avatar@2","date-picker-days":"avatar@28",heading:"heading",image:"image","list-item":"text","list-item-avatar":"avatar, text","list-item-two-line":"sentences","list-item-avatar-two-line":"avatar, sentences","list-item-three-line":"paragraph","list-item-avatar-three-line":"avatar, paragraph",paragraph:"text@3",sentences:"text@2",table:"table-heading, table-thead, table-tbody, table-tfoot","table-heading":"heading, text","table-thead":"heading@6","table-tbody":"table-row-divider@6","table-row-divider":"table-row, divider","table-row":"table-cell@6","table-cell":"text","table-tfoot":"text@2, avatar@2",text:"text"},this.types)}},methods:{genBone:function(t,e){return this.$createElement("div",{staticClass:"v-skeleton-loader__".concat(t," v-skeleton-loader__bone")},e)},genBones:function(t){var e=this,a=t.split("@"),n=Object(i["a"])(a,2),s=n[0],r=n[1],o=function(){return e.genStructure(s)};return Array.from({length:r}).map(o)},genStructure:function(t){var e=[];t=t||this.type||"";var a=this.rootTypes[t]||"";if(t===a);else{if(t.indexOf(",")>-1)return this.mapBones(t);if(t.indexOf("@")>-1)return this.genBones(t);a.indexOf(",")>-1?e=this.mapBones(a):a.indexOf("@")>-1?e=this.genBones(a):a&&e.push(this.genStructure(a))}return[this.genBone(t,e)]},genSkeleton:function(){var t=[];return this.isLoading?t.push(this.genStructure()):t.push(Object(c["s"])(this)),this.transition?this.$createElement("transition",{props:{name:this.transition},on:{afterEnter:this.resetStyles,beforeEnter:this.onBeforeEnter,beforeLeave:this.onBeforeLeave,leaveCancelled:this.resetStyles}},t):t},mapBones:function(t){return t.replace(/\s/g,"").split(",").map(this.genStructure)},onBeforeEnter:function(t){this.resetStyles(t),this.isLoading&&(t._initialStyle={display:t.style.display,transition:t.style.transition},t.style.setProperty("transition","none","important"))},onBeforeLeave:function(t){t.style.setProperty("display","none","important")},resetStyles:function(t){t._initialStyle&&(t.style.display=t._initialStyle.display||"",t.style.transition=t._initialStyle.transition,delete t._initialStyle)}},render:function(t){return t("div",{staticClass:"v-skeleton-loader",attrs:this.attrs,on:this.$listeners,class:this.classes,style:this.isLoading?this.measurableStyles:void 0},[this.genSkeleton()])}})},"6c6f":function(t,e,a){"use strict";a("d3b7");e["a"]={data:function(){return{deleteNotification:{dialog:!1,heading:"Confirm Delete",text:"Are you sure you want to delete ?"}}},methods:{deleteData:function(t,e){var a=this;return new Promise((function(i,n){!a.loading&&t&&(a.loading=!0,a.$http.delete(t,e||{}).then((function(t){a.crud.message&&setTimeout((function(){a.notifyUser(a.crud.message)}),1e3),i(t),a.loading=!1})).catch((function(t){a.pushErrors(t),a.notifyInvalidFormResponse(),n(t),a.loading=!1})).finally((function(){a.deleteNotification.dialog=!1})))}))}}}},"8cd3":function(t,e,a){"use strict";var i=a("5530"),n=(a("d3b7"),a("f0d5"));e["a"]={mixins:[n["a"]],data:function(){return{dataTableEndpoint:"",fetchedResults:[],response:null,footerProps:{itemsPerPageOptions:[10,20,30,40,50,100]},pagination:{sortBy:["modified_at"],descending:!1,totalItems:0,page:1,rowsPerPage:10,pageCount:0},loadTableOnInit:!0}},computed:{filterParams:function(){var t=Object(i["a"])(Object(i["a"])({},this.dataTableFilter),{},{offset:(this.pagination.page-1)*this.pagination.rowsPerPage,limit:this.pagination.rowsPerPage,ordering:this.pagination.descending?this.pagination.sortBy:"-"+this.pagination.sortBy});return this.convertToURLSearchParams(t,!1)}},watch:{filterParams:function(){var t=this;this.$nextTick((function(){t.fetchDataTable()}))},dataTableFilter:function(){this.pagination.page=1}},created:function(){var t=this;setTimeout((function(){t.loadTableOnInit&&t.fetchDataTable()}),0)},methods:{fetchDataTable:function(t,e){var a=this;return new Promise((function(i,n){!t&&!a.dataTableEndpoint||a.loading||(a.loadTableOnInit=!1,a.loading=!0,a.fetchedResults=[],a.$http.get(t||a.dataTableEndpoint,e||{params:a.filterParams}).then((function(t){a.response=t,a.fetchedResults=t.results,a.pagination.totalItems=t.count,a.processAfterTableLoad(t),i(t),a.loading=!1})).catch((function(t){a.pushErrors(t),a.notifyInvalidFormResponse(),n(t),a.loading=!1})))}))},processAfterTableLoad:function(){}}}},a51f:function(t,e,a){"use strict";a.r(e);var i=function(){var t=this,e=t.$createElement,a=t._self._c||e;return a("div",[t.search.length>0?a("span",[t._v(' Your search for "'+t._s(t.search)+'" found no results. ')]):t.loading?a("v-skeleton-loader",{attrs:{type:"table",height:t.skeletonLoaderHeight}}):a("no-data-found",{attrs:{text:t.text,height:t.height}},[t._t("default")],2)],1)},n=[],s=(a("a9e3"),a("e585")),r={components:{NoDataFound:s["default"]},props:{search:{type:String,default:""},loading:{type:Boolean,required:!0},text:{type:String,default:"No data available at the moment"},height:{type:[String,Number],default:200},skeletonLoaderHeight:{type:[String,Number],default:void 0}}},o=r,l=a("2877"),c=a("6544"),d=a.n(c),u=a("3129"),m=Object(l["a"])(o,i,n,!1,null,null,null);e["default"]=m.exports;d()(m,{VSkeletonLoader:u["a"]})},abd3:function(t,e,a){},e4bf:function(t,e,a){"use strict";a.r(e);var i=function(){var t=this,e=t.$createElement,a=t._self._c||e;return a("div",[t.contextList.filter((function(t){return!t.hide})).length<3&&!t.hideIcons||t.showIcons?a("div",t._l(t.contextList,(function(e,i){return a("span",{key:i},[e.hide?t._e():a("v-tooltip",{attrs:{disabled:t.$vuetify.breakpoint.xs,top:""},scopedSlots:t._u([{key:"activator",fn:function(n){var s=n.on;return[a("v-btn",t._g({staticClass:"mx-0",attrs:{text:"",width:t.small?"18":"22",depressed:"",icon:""}},s),[a("v-icon",{attrs:{disabled:e.disabled,color:e.color,"data-cy":t.dataCyVariable+"btn-dropdown-menu-item-"+(i+1),dark:!e.disabled,small:t.small,size:"20",dense:""},domProps:{textContent:t._s(e.icon)},on:{click:function(e){return t.$emit("click"+i)}}})],1)]}}],null,!0)},[a("span",{domProps:{textContent:t._s(e.disabled&&e.disable_message||e.name)}})])],1)})),0):a("v-menu",{attrs:{"offset-y":"",left:"",transition:"slide-y-transition"},scopedSlots:t._u([{key:"activator",fn:function(e){var i=e.on;return[a("v-btn",t._g({attrs:{small:"",text:"",icon:""}},i),[a("v-icon",{attrs:{"data-cy":"btn-dropdown-menu"},domProps:{textContent:t._s("mdi-dots-vertical")}})],1)]}}])},t._l(t.contextList,(function(e,i){return a("v-list",{key:i,staticClass:"pa-0",attrs:{dense:""}},[e.hide?t._e():a("div",[e.disabled?a("v-list-item",{attrs:{"data-cy":"btn-dropdown-menu-item"}},[a("v-tooltip",{attrs:{top:""},scopedSlots:t._u([{key:"activator",fn:function(i){var n=i.on;return[a("v-list-item-title",t._g({},n),[a("v-icon",{attrs:{disabled:"",small:"",color:e.color},domProps:{textContent:t._s(e.icon)}}),a("span",{staticClass:"ml-1 grey--text",domProps:{textContent:t._s(e.name)}})],1)]}}],null,!0)},[a("span",{domProps:{textContent:t._s(e.disabled&&e.disable_message||e.name)}})])],1):a("v-list-item",{attrs:{"data-cy":"btn-dropdown-menu-item"},on:{click:function(e){return t.$emit("click"+i)}}},[a("v-list-item-title",[a("v-icon",{attrs:{color:e.color,small:"",dense:""},domProps:{textContent:t._s(e.icon)}}),a("span",{staticClass:"ml-1",class:e.text_color,domProps:{textContent:t._s(e.name)}})],1)],1)],1)])})),1)],1)},n=[],s={name:"VueContextMenu",props:{contextList:{type:Array,default:function(){return[]}},dataCyVariable:{type:String,default:""},showIcons:{type:Boolean,default:!1},hideIcons:{type:Boolean,default:!1},small:{type:Boolean,default:!1}}},r=s,o=a("2877"),l=a("6544"),c=a.n(l),d=a("8336"),u=a("132d"),m=a("8860"),p=a("da13"),f=a("5d23"),v=a("e449"),h=a("3a2f"),g=Object(o["a"])(r,i,n,!1,null,"71ee785c",null);e["default"]=g.exports;c()(g,{VBtn:d["a"],VIcon:u["a"],VList:m["a"],VListItem:p["a"],VListItemTitle:f["c"],VMenu:v["a"],VTooltip:h["a"]})},f0d5:function(t,e,a){"use strict";a("d3b7"),a("3ca3"),a("ddb0");var i=a("c44a");e["a"]={components:{NonFieldFormErrors:function(){return a.e("chunk-6441e173").then(a.bind(null,"ab8a"))}},mixins:[i["a"]],data:function(){return{crud:{name:"record",message:"",addAnother:!1},formValues:{},loading:!1}}}},f70a:function(t,e,a){"use strict";a("d3b7"),a("caad");e["a"]={methods:{insertData:function(t,e){var a=this,i=arguments.length>2&&void 0!==arguments[2]?arguments[2]:{},n=i.validate,s=void 0===n||n,r=i.clearForm,o=void 0===r||r,l=arguments.length>3?arguments[3]:void 0;return new Promise((function(i,n){!a.loading&&t&&(a.clearErrors(),a.$validator.validateAll().then((function(r){s||(r=!0),r&&(a.loading=!0,a.$http.post(t,e,l||{}).then((function(t){a.clearErrors(),o&&(a.formValues={}),a.crud.addAnother||a.$emit("create"),a.crud.message&&setTimeout((function(){a.notifyUser(a.crud.message)}),1e3),i(t),a.loading=!1})).catch((function(t){a.pushErrors(t),a.notifyInvalidFormResponse(),n(t),a.loading=!1})))})))}))},patchData:function(t,e){var a=this,i=arguments.length>2&&void 0!==arguments[2]?arguments[2]:{},n=i.validate,s=void 0===n||n,r=i.clearForm,o=void 0===r||r,l=arguments.length>3?arguments[3]:void 0;return new Promise((function(i,n){a.updateData(t,e,{validate:s,clearForm:o},"patch",l).then((function(t){i(t)})).catch((function(t){n(t)}))}))},putData:function(t,e){var a=this,i=arguments.length>2&&void 0!==arguments[2]?arguments[2]:{},n=i.validate,s=void 0===n||n,r=i.clearForm,o=void 0===r||r,l=arguments.length>3?arguments[3]:void 0;return new Promise((function(i,n){a.updateData(t,e,{validate:s,clearForm:o},"put",l).then((function(t){i(t)})).catch((function(t){n(t)}))}))},updateData:function(t,e){var a=this,i=arguments.length>2&&void 0!==arguments[2]?arguments[2]:{},n=i.validate,s=void 0===n||n,r=i.clearForm,o=void 0===r||r,l=arguments.length>3?arguments[3]:void 0,c=arguments.length>4?arguments[4]:void 0;return new Promise((function(i,n){!a.loading&&t&&["put","patch"].includes(l)&&(a.clearErrors(),a.$validator.validateAll().then((function(r){s||(r=!0),r&&(a.loading=!0,a.$http[l](t,e,c||{}).then((function(t){a.$emit("update"),a.clearErrors(),o&&(a.formValues={}),a.crud.message&&setTimeout((function(){a.notifyUser(a.crud.message)}),1e3),i(t),a.loading=!1})).catch((function(t){a.pushErrors(t),a.notifyInvalidFormResponse(),n(t),a.loading=!1})))})))}))},clearErrors:function(){this.clearNonFieldErrors(),this.$validator.errors.clear()}}}}}]);