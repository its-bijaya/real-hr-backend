(window["webpackJsonp"]=window["webpackJsonp"]||[]).push([["pages/admin/_slug/task/projects/_id/assign-project","chunk-31f8a6e6","chunk-2d0c8a11","chunk-2d2259e9","chunk-aee42bec"],{"0549":function(e,t,a){"use strict";a.r(t);var i=function(){var e=this,t=e.$createElement,a=e._self._c||t;return a("div",[a("v-row",{staticClass:"mb-3",attrs:{"no-gutters":""}},[e.breadCrumbs?a("v-col",{attrs:{cols:"12"}},[a("v-card",{attrs:{flat:""}},[a("v-breadcrumbs",{staticClass:"text-body-1 pa-2",class:{"text-caption pa-1":e.$vuetify.breakpoint.xs},attrs:{items:e.breadCrumbs},scopedSlots:e._u([{key:"item",fn:function(t){return[a("span",{class:t.item.disabled?"grey--text":"baseColor--text text--accent-2 pointer",domProps:{textContent:e._s(t.item.text)},on:{click:function(a){return e.$router.push(t.item.to)}}})]}}],null,!1,1670153796)},[a("v-icon",{attrs:{slot:"divider"},slot:"divider"},[e._v("mdi-chevron-right")])],1)],1)],1):e._e()],1),a("v-row",{attrs:{"no-gutters":""}},[a("v-col",{attrs:{cols:"12"}},[e._t("default")],2)],1)],1)},s=[],r=a("5530"),n=(a("ac1f"),a("1276"),a("b0c0"),a("2f62")),o={props:{title:{type:String,required:!0},breadCrumbs:{type:Array,default:function(){return[]}}},computed:Object(r["a"])({},Object(n["c"])({getOrganizationName:"organization/getOrganizationName",getSupervisorSwitchedOrganization:"supervisor/getSwitchedOrganization"})),mounted:function(){document.title="".concat(this.title," | RealHRsoft");var e=this.$route.params.slug?"admin-slug-dashboard":"root",t=this.$route.name.split("-"),a=this.getOrganizationName;this.getSupervisorSwitchedOrganization&&"user"===t[0]&&"supervisor"===t[1]&&(a=this.getSupervisorSwitchedOrganization.name),this.breadCrumbs.unshift({text:a,disabled:!1,to:{name:e,params:{slug:this.$route.params.slug}}})}},l=o,c=a("2877"),u=a("6544"),d=a.n(u),m=a("2bc5"),p=a("b0af"),f=a("62ad"),h=a("132d"),v=a("0fd9b"),b=Object(c["a"])(l,i,s,!1,null,null,null);t["default"]=b.exports;d()(b,{VBreadcrumbs:m["a"],VCard:p["a"],VCol:f["a"],VIcon:h["a"],VRow:v["a"]})},"2bc5":function(e,t,a){"use strict";var i=a("5530"),s=(a("a15b"),a("abd3"),a("ade3")),r=a("1c87"),n=a("58df"),o=Object(n["a"])(r["a"]).extend({name:"v-breadcrumbs-item",props:{activeClass:{type:String,default:"v-breadcrumbs__item--disabled"},ripple:{type:[Boolean,Object],default:!1}},computed:{classes:function(){return Object(s["a"])({"v-breadcrumbs__item":!0},this.activeClass,this.disabled)}},render:function(e){var t=this.generateRouteLink(),a=t.tag,s=t.data;return e("li",[e(a,Object(i["a"])(Object(i["a"])({},s),{},{attrs:Object(i["a"])(Object(i["a"])({},s.attrs),{},{"aria-current":this.isActive&&this.isLink?"page":void 0})}),this.$slots.default)])}}),l=a("80d2"),c=Object(l["i"])("v-breadcrumbs__divider","li"),u=a("7560");t["a"]=Object(n["a"])(u["a"]).extend({name:"v-breadcrumbs",props:{divider:{type:String,default:"/"},items:{type:Array,default:function(){return[]}},large:Boolean},computed:{classes:function(){return Object(i["a"])({"v-breadcrumbs--large":this.large},this.themeClasses)}},methods:{genDivider:function(){return this.$createElement(c,this.$slots.divider?this.$slots.divider:this.divider)},genItems:function(){for(var e=[],t=!!this.$scopedSlots.item,a=[],i=0;i<this.items.length;i++){var s=this.items[i];a.push(s.text),t?e.push(this.$scopedSlots.item({item:s})):e.push(this.$createElement(o,{key:a.join("."),props:s},[s.text])),i<this.items.length-1&&e.push(this.genDivider())}return e}},render:function(e){var t=this.$slots.default||this.genItems();return e("ul",{staticClass:"v-breadcrumbs",class:this.classes},t)}})},5660:function(e,t,a){"use strict";a.r(t);var i=function(){var e=this,t=e.$createElement,a=e._self._c||t;return a("div",{staticClass:"d-flex space-between"},[a("v-autocomplete",{key:e.componentKey,ref:"autoComplete",class:e.appliedClass,attrs:{id:e.id,items:e.itemsSorted,"search-input":e.search,loading:e.isLoading,multiple:e.multiple,label:e.label,error:e.errorMessages.length>0,"error-messages":e.errorMessages,disabled:e.disabled,readonly:e.readonly,"data-cy":"autocomplete-"+e.dataCyVariable,"prepend-inner-icon":e.prependInnerIcon,clearable:e.clearable&&!e.readonly,"hide-details":e.hideDetails,"item-text":e.itemText,"item-value":e.itemValue,"small-chips":e.multiple||e.chips,"deletable-chips":e.multiple,hint:e.hint,"persistent-hint":e.persistentHint,chips:e.chips,solo:e.solo,flat:e.flat,"cache-items":e.cacheItems,placeholder:e.placeholder,dense:e.dense,"hide-selected":"","hide-no-data":""},on:{"update:searchInput":function(t){e.search=t},"update:search-input":function(t){e.search=t},focus:e.populateOnFocus,keydown:function(t){return!t.type.indexOf("key")&&e._k(t.keyCode,"enter",13,t.key,"Enter")?null:(t.preventDefault(),e.searchText())},change:e.updateState,blur:function(t){return e.$emit("blur")}},scopedSlots:e._u([{key:"selection",fn:function(t){return[e._t("selection",(function(){return[e.itemText&&t.item?a("div",[e.multiple||e.chips?a("v-chip",{attrs:{close:(e.clearable||!e.clearable&&!e.multiple)&&!e.readonly,small:""},on:{"click:close":function(a){return e.remove(t.item)}}},[t.item[e.itemText]?a("div",[t.item[e.itemText].length>40?a("v-tooltip",{attrs:{top:""},scopedSlots:e._u([{key:"activator",fn:function(i){var s=i.on;return[a("span",e._g({},s),[e._v(" "+e._s(e._f("truncate")(t.item[e.itemText],40)))])]}}],null,!0)},[a("span",[e._v(e._s(t.item[e.itemText]))])]):a("span",[e._v(e._s(t.item[e.itemText]))])],1):a("div",[a("span",[e._v(e._s(t.item))])])]):a("div",[t.item[e.itemText]?a("div",[t.item[e.itemText].length>40?a("v-tooltip",{attrs:{top:""},scopedSlots:e._u([{key:"activator",fn:function(i){var s=i.on;return[a("span",e._g({},s),[e._v(" "+e._s(e._f("truncate")(t.item[e.itemText],40)))])]}}],null,!0)},[a("span",[e._v(e._s(t.item[e.itemText]))])]):a("span",[e._v(e._s(t.item[e.itemText]))])],1):a("div",[a("span",[e._v(e._s(t.item))])])])],1):e._e()]}),{props:t})]}},{key:"item",fn:function(t){return[a("v-list-item-content",[a("v-list-item-title",[e._t("item",(function(){return[e.itemText&&t.item?a("div",[t.item[e.itemText]?a("div",[t.item[e.itemText].length>40?a("v-tooltip",{attrs:{top:""},scopedSlots:e._u([{key:"activator",fn:function(i){var s=i.on;return[a("span",e._g({},s),[e._v(" "+e._s(e._f("truncate")(t.item[e.itemText],40)))])]}}],null,!0)},[a("span",[e._v(e._s(t.item[e.itemText]))])]):a("span",[e._v(e._s(t.item[e.itemText]))])],1):a("div",[a("span",[e._v(e._s(t.item))])])]):e._e()]}),{props:t})],2)],1)]}},{key:"append-item",fn:function(){return[!e.fullyLoaded&&e.showMoreIcon?a("div",[a("v-list-item-content",{staticClass:"px-4 pointer primary--text font-weight-bold"},[a("v-list-item-title",{on:{click:function(t){return e.fetchData()}}},[e._v(" Load More Items ... ")])],1)],1):e._e()]},proxy:!0}],null,!0),model:{value:e.selectedData,callback:function(t){e.selectedData=t},expression:"selectedData"}}),e._t("default")],2)},s=[],r=a("2909"),n=a("5530"),o=a("53ca"),l=a("1da1"),c=(a("96cf"),a("a9e3"),a("ac1f"),a("841c"),a("7db0"),a("d81d"),a("159b"),a("4de4"),a("4e827"),a("2ca0"),a("d3b7"),a("c740"),a("a434"),a("3ca3"),a("ddb0"),a("2b3d"),a("caad"),a("2532"),a("63ea")),u=a.n(c),d={props:{value:{type:[Number,String,Array,Object],default:void 0},id:{type:String,default:""},dataCyVariable:{type:String,default:""},endpoint:{type:String,default:""},itemText:{type:String,required:!0},itemValue:{type:String,required:!0},params:{type:Object,required:!1,default:function(){return{}}},itemsToExclude:{type:[Array,Number],default:null},forceFetch:{type:Boolean,default:!1},staticItems:{type:Array,default:function(){return[]}},errorMessages:{type:[String,Array],default:function(){return[]}},label:{type:String,default:""},disabled:{type:Boolean,default:!1},readonly:{type:Boolean,default:!1},hint:{type:String,default:void 0},persistentHint:{type:Boolean,required:!1,default:!1},multiple:{type:Boolean,required:!1,default:!1},clearable:{type:Boolean,default:!0},hideDetails:{type:Boolean,default:!1},solo:{type:Boolean,default:!1},flat:{type:Boolean,default:!1},chips:{type:Boolean,default:!1},prependInnerIcon:{type:String,default:void 0},cacheItems:{type:Boolean,default:!1},appliedClass:{type:String,default:""},placeholder:{type:String,default:""},dense:{type:Boolean,default:!1}},data:function(){return{componentKey:0,items:[],selectedData:null,search:null,initialFetchStarted:!1,nextLimit:null,nextOffset:null,showMoreIcon:!1,fullyLoaded:!1,isLoading:!1}},computed:{itemsSorted:function(){return this.sortBySearch(this.items,this.search?this.search.toLowerCase():"")}},watch:{value:{handler:function(){var e=Object(l["a"])(regeneratorRuntime.mark((function e(t){var a,i,s,r,n=this;return regeneratorRuntime.wrap((function(e){while(1)switch(e.prev=e.next){case 0:if(!t){e.next=10;break}if(!this.forceFetch||this.initialFetchStarted){e.next=6;break}return this.initialFetchStarted=!0,e.next=5,this.fetchData();case 5:this.removeDuplicateItem();case 6:Array.isArray(t)?(s=[],"object"===Object(o["a"])(t[0])?(this.selectedData=t.map((function(e){return e[n.itemValue]})),t.forEach((function(e){var t=n.items.find((function(t){return t===e}));t||s.push(e)}))):(t.forEach((function(e){var t=n.items.find((function(t){return t[n.itemValue]===e}));t||s.push(e)})),this.selectedData=t),s.length>0&&(r=this.items).push.apply(r,s)):"object"===Object(o["a"])(t)?(this.selectedData=t[this.itemValue],a=this.items.find((function(e){return e[n.itemValue]===t})),a||this.items.push(t)):(this.selectedData=t,i=this.items.find((function(e){return e===t})),i||this.items.push(t)),this.updateData(this.selectedData),e.next=11;break;case 10:t||(this.selectedData=null);case 11:case"end":return e.stop()}}),e,this)})));function t(t){return e.apply(this,arguments)}return t}(),immediate:!0},selectedData:function(e){this.updateData(e)},params:{handler:function(e,t){u()(e,t)||(this.fullyLoaded=!1,this.initialFetchStarted=!1,this.items=[],this.componentKey+=1)},deep:!0}},methods:{sortBySearch:function(e,t){var a=this.itemText,i=e.filter((function(e){return"object"===Object(o["a"])(e)}));return i.sort((function(e,i){return e[a].toLowerCase().startsWith(t)&&i[a].toLowerCase().startsWith(t)?e[a].toLowerCase().localeCompare(i[a].toLowerCase()):e[a].toLowerCase().startsWith(t)?-1:i[a].toLowerCase().startsWith(t)?1:e[a].toLowerCase().localeCompare(i[a].toLowerCase())}))},populateOnFocus:function(){var e=this;return Object(l["a"])(regeneratorRuntime.mark((function t(){return regeneratorRuntime.wrap((function(t){while(1)switch(t.prev=t.next){case 0:if(!e.initialFetchStarted){t.next=2;break}return t.abrupt("return");case 2:return e.initialFetchStarted=!0,t.next=5,e.fetchData();case 5:e.removeDuplicateItem();case 6:case"end":return t.stop()}}),t)})))()},fetchData:function(){var e=this;return Object(l["a"])(regeneratorRuntime.mark((function t(){var a,i;return regeneratorRuntime.wrap((function(t){while(1)switch(t.prev=t.next){case 0:if(!(e.staticItems.length>0)){t.next=3;break}return e.items=e.staticItems,t.abrupt("return");case 3:return a=e.nextLimit,i=e.nextOffset,e.search&&(a=null,i=null),e.isLoading=!0,t.next=9,e.$http.get(e.endpoint,{params:Object(n["a"])(Object(n["a"])({},e.params),{},{search:e.search,limit:a,offset:i})}).then((function(t){var a;t.results||(t.results=t),t.next?(e.showMoreIcon=!0,e.extractLimitOffset(t.next)):(e.showMoreIcon=!1,e.search||(e.fullyLoaded=!0)),e.itemsToExclude&&(t.results=e.excludeRecord(t.results)),(a=e.items).push.apply(a,Object(r["a"])(t.results))})).finally((function(){e.isLoading=!1}));case 9:case"end":return t.stop()}}),t)})))()},removeDuplicateItem:function(){var e=this,t=this.items.indexOf(this.selectedData);if(t>=0){var a=this.items.findIndex((function(t){return t[e.itemValue]===e.selectedData}));a>=0&&(this.items.splice(t,1),this.componentKey+=1)}},updateData:function(e){var t=this,a=[];e instanceof Array?e.forEach((function(e){a.unshift(t.items.find((function(a){return a[t.itemValue]===e})))})):a=this.items.find((function(a){return a[t.itemValue]===e})),this.$emit("input",e),this.$emit("update:selectedFullData",a)},searchText:function(){0!==this.$refs.autoComplete.filteredItems.length||this.fullyLoaded||this.fetchData()},extractLimitOffset:function(e){var t=new URL(e);this.nextLimit=t.searchParams.get("limit"),this.nextOffset=t.searchParams.get("offset")},excludeRecord:function(e){var t=this,a=[];return"number"===typeof this.itemsToExclude?a.push(this.itemsToExclude):a=this.itemsToExclude,e.filter((function(e){if(e[t.itemValue])return!a.includes(e[t.itemValue])}))},remove:function(e){if(this.selectedData instanceof Object){var t=this.selectedData.indexOf(e[this.itemValue]);t>=0&&this.selectedData.splice(t,1)}else this.selectedData=null},updateState:function(){this.search="",this.nextLimit&&(this.showMoreIcon=!0)}}},m=d,p=a("2877"),f=a("6544"),h=a.n(f),v=a("c6a6"),b=a("cc20"),y=a("5d23"),g=a("3a2f"),_=Object(p["a"])(m,i,s,!1,null,null,null);t["default"]=_.exports;h()(_,{VAutocomplete:v["a"],VChip:b["a"],VListItemContent:y["a"],VListItemTitle:y["c"],VTooltip:g["a"]})},"6c6f":function(e,t,a){"use strict";a("d3b7");t["a"]={data:function(){return{deleteNotification:{dialog:!1,heading:"Confirm Delete",text:"Are you sure you want to delete ?"}}},methods:{deleteData:function(e,t){var a=this;return new Promise((function(i,s){!a.loading&&e&&(a.loading=!0,a.$http.delete(e,t||{}).then((function(e){a.crud.message&&setTimeout((function(){a.notifyUser(a.crud.message)}),1e3),i(e),a.loading=!1})).catch((function(e){a.pushErrors(e),a.notifyInvalidFormResponse(),s(e),a.loading=!1})).finally((function(){a.deleteNotification.dialog=!1})))}))}}}},"7ff0":function(e,t,a){"use strict";a.r(t);var i=function(){var e=this,t=e.$createElement,a=e._self._c||t;return a("vue-page-wrapper",{attrs:{title:e.htmlTitle,"bread-crumbs":e.breadCrumbItems}},[e.projectData.name?a("v-card",[a("vue-card-title",{attrs:{title:e.projectData.name,subtitle:"Here you can view member of project",icon:"mdi-account-edit"}},[a("template",{slot:"actions"},[a("v-btn",{attrs:{small:"","data-cy":"btn-create-task-project",color:"primary",depressed:""},on:{click:function(t){return e.triggerForm("create")}}},[e._v(" Assign Member ")]),a("v-btn",{attrs:{"data-cy":"btn-filter",icon:""},on:{click:function(t){e.filter.show=!e.filter.show}}},[a("v-icon",{attrs:{small:""},domProps:{textContent:e._s("mdi-filter-variant")}})],1)],1)],2),a("v-divider"),a("v-slide-y-transition",[a("v-row",{directives:[{name:"show",rawName:"v-show",value:e.filter.show,expression:"filter.show"}],staticClass:"mx-3 py-0"},[a("vue-search",{attrs:{search:e.search},on:{"update:search":function(t){e.search=t}},model:{value:e.search,callback:function(t){e.search=t},expression:"search"}})],1)],1),e.filter.show?a("v-divider"):e._e(),a("v-tabs",{attrs:{"show-arrows":"","slider-color":"blue"},model:{value:e.filter.activeStatus,callback:function(t){e.$set(e.filter,"activeStatus",t)},expression:"filter.activeStatus"}},e._l(e.tabs,(function(t){return a("v-tab",{key:t.tabName,attrs:{ripple:"",disabled:e.loading}},[a("span",{staticClass:"pr-2 text-capitalize"},[e._v(" "+e._s(t.tabName)+" ")]),a("v-chip",{staticClass:"white--text",attrs:{color:t.color,small:""}},[e._v(" "+e._s(t.count)+" ")])],1)})),1),a("v-divider"),a("v-data-table",{attrs:{headers:e.headers,items:e.fetchedResults,"sort-desc":e.pagination.descending,"sort-by":e.pagination.sortBy,page:e.pagination.page,"items-per-page":e.pagination.rowsPerPage,"server-items-length":e.pagination.totalItems,"mobile-breakpoint":0,"must-sort":""},on:{"update:sortDesc":function(t){return e.$set(e.pagination,"descending",t)},"update:sort-desc":function(t){return e.$set(e.pagination,"descending",t)},"update:sortBy":function(t){return e.$set(e.pagination,"sortBy",t)},"update:sort-by":function(t){return e.$set(e.pagination,"sortBy",t)},"update:page":function(t){return e.$set(e.pagination,"page",t)},"update:itemsPerPage":function(t){return e.$set(e.pagination,"rowsPerPage",t)},"update:items-per-page":function(t){return e.$set(e.pagination,"rowsPerPage",t)}},scopedSlots:e._u([{key:"item",fn:function(t){return[a("tr",[a("td",{staticClass:"text-center"},[a("vue-user",{attrs:{user:t.item.user}})],1),a("td",[a("v-tooltip",{attrs:{"max-width":"600",top:""},scopedSlots:e._u([{key:"activator",fn:function(i){var s=i.on,r=i.attrs;return[a("p",e._g(e._b({},"p",r,!1),s),[e._v(" "+e._s(e._f("truncate")(t.item.activity.name,70))+" ")])]}}],null,!0)},[a("span",[e._v(e._s(t.item.activity.name))])])],1),a("td",{staticClass:"text-center"},[e._v(" "+e._s(t.item.employee_rate)+" ")]),a("td",{staticClass:"text-center"},[e._v(" "+e._s(t.item.client_rate)+" ")]),a("td",{staticClass:"text-center"},[a("v-icon",{attrs:{color:t.item.is_billable?"green":"red"}},[e._v(" "+e._s(t.item.is_billable?"mdi-check":"mdi-close")+" ")])],1),a("td",{staticClass:"text-center",staticStyle:{width:"14%"}},[a("vue-context-menu",{attrs:{"context-list":[{name:"Edit",icon:"mdi-pencil-outline",color:"blue"},{name:"Delete",icon:"mdi-delete-outline",color:"red"}]},on:{click0:function(a){return e.triggerForm("update",t.item)},click1:function(a){return e.triggerForm("delete",t.item)}}})],1)])]}}],null,!1,4290872489)},[a("template",{slot:"no-data"},[a("data-table-no-data",{attrs:{loading:e.loading}})],1)],2),a("v-dialog",{attrs:{persistent:"",width:"960"},on:{keydown:function(t){if(!t.type.indexOf("key")&&e._k(t.keyCode,"esc",27,t.key,["Esc","Escape"]))return null;e.displayForm=!1}},model:{value:e.displayForm,callback:function(t){e.displayForm=t},expression:"displayForm"}},[e.displayForm?a("task-project-assign-form",{attrs:{"action-data":e.actionData,"update-form":e.updateForm,"project-data":e.projectData},on:{"dismiss-form":e.dismissForm}}):e._e()],1),a("vue-dialog",{attrs:{notify:e.deleteNotification},on:{close:function(t){e.deleteNotification.dialog=!1},agree:e.deleteDataItem}})],1):e._e()],1)},s=[],r=a("1da1"),n=(a("96cf"),a("ac1f"),a("841c"),a("0549")),o=a("8cd3"),l=a("02cb"),c=a("a51f"),u=a("e4bf"),d=function(){var e=this,t=e.$createElement,a=e._self._c||t;return a("v-card",[a("vue-card-title",{attrs:{title:"Assign Employee",subtitle:"Here you can assign employee.",icon:"mdi-account-edit",closable:""},on:{close:function(t){return e.$emit("dismiss-form")}}}),a("v-divider"),e.nonFieldErrors?a("non-field-form-errors",{attrs:{"non-field-errors":e.nonFieldErrors}}):e._e(),a("v-card-text",{ref:"assignProjectForm"},[a("v-row",[a("v-col",{attrs:{md:"6",cols:"12"}},[a("users-auto-complete",e._b({directives:[{name:"validate",rawName:"v-validate",value:"required",expression:"'required'"}],model:{value:e.formValues.user,callback:function(t){e.$set(e.formValues,"user",t)},expression:"formValues.user"}},"users-auto-complete",e.veeValidate("user","Project Members *"),!1))],1),a("v-col",{attrs:{md:"6",cols:"12"}},[a("vue-auto-complete",e._b({directives:[{name:"validate",rawName:"v-validate",value:"required",expression:"'required'"}],ref:"moreAutoComplete",attrs:{endpoint:e.activitiesEndpoint,label:"Activities *","item-text":"name","item-value":"id","prepend-inner-icon":"mdi-source-branch"},model:{value:e.formValues.activity,callback:function(t){e.$set(e.formValues,"activity",t)},expression:"formValues.activity"}},"vue-auto-complete",e.veeValidate("activity","Activities *"),!1))],1),a("v-col",{attrs:{md:"6",cols:"12"}},[a("v-text-field",e._b({directives:[{name:"validate",rawName:"v-validate",value:"",expression:"''"}],attrs:{type:"number",suffix:e.selectedActivity&&e.selectedActivity.unit?"per "+e.selectedActivity.unit:""},model:{value:e.formValues.employee_rate,callback:function(t){e.$set(e.formValues,"employee_rate",t)},expression:"formValues.employee_rate"}},"v-text-field",e.veeValidate("employee_rate","Employee Rate"),!1))],1),a("v-col",{attrs:{md:"6",cols:"12"}},[a("v-text-field",e._b({directives:[{name:"validate",rawName:"v-validate",value:"",expression:"''"}],attrs:{type:"number",suffix:e.selectedActivity.unit?"per "+e.selectedActivity.unit:""},model:{value:e.formValues.client_rate,callback:function(t){e.$set(e.formValues,"client_rate",t)},expression:"formValues.client_rate"}},"v-text-field",e.veeValidate("client_rate","Client Rate"),!1))],1),a("v-col",{attrs:{md:"6",cols:"12"}},[a("v-checkbox",e._b({directives:[{name:"validate",rawName:"v-validate",value:"",expression:"''"}],model:{value:e.formValues.is_billable,callback:function(t){e.$set(e.formValues,"is_billable",t)},expression:"formValues.is_billable"}},"v-checkbox",e.veeValidate("is_billable","Is Billable"),!1))],1)],1),a("v-divider"),a("v-card-actions",[a("v-spacer"),a("v-btn",{attrs:{text:"",type:"reset"},on:{click:function(t){return e.$emit("dismiss-form")}}},[e._v(" Cancel ")]),a("v-btn",{attrs:{depressed:"",color:"primary"},on:{click:e.submitForm}},[a("v-icon",{staticClass:"mr-1",attrs:{size:"14"}},[e._v(" mdi-content-save-outline ")]),e._v(" Save ")],1)],1)],1)],1)},m=[],p=(a("7db0"),a("f0d5")),f=a("f70a"),h=a("ef8c"),v=a("5660"),b=a("e590"),y={components:{UsersAutoComplete:h["default"],VueAutoComplete:v["default"]},mixins:[p["a"],f["a"]],props:{actionData:{type:Object,required:!1,default:function(){return{user:"",employee_rate:null,activity:null,client_rate:null,is_billable:null}}},updateForm:{type:Boolean,default:!1},projectData:{type:Object,default:function(){return{}}}},data:function(){return{formValues:this.deepCopy(this.actionData),activitiesEndpoint:"/task/activities/?as=hr",selectedActivity:{}}},watch:{"formValues.activity":function(e){if(e){var t=this.$refs.moreAutoComplete.items.find((function(t){var a=t.id;return a===e}));this.formValues.employee_rate=t.employee_rate||this.formValues.employee_rate,this.formValues.client_rate=t.client_rate||this.formValues.client_rate,this.selectedActivity=t}}},created:function(){this.updateForm||(this.formValues.is_billable=this.projectData.is_billable)},methods:{submitForm:function(){var e=this;this.updateForm?(this.crud.message="Successfully updated assigned employee.",this.putData(b["a"].putAssignProject(this.$route.params.id,this.formValues.id)+"?as=hr",this.formValues).then((function(){e.$emit("dismiss-form")}))):(this.crud.message="Successfully assigned employee.",this.insertData(b["a"].postAssignProject(this.$route.params.id)+"?as=hr",this.formValues).then((function(){e.$emit("dismiss-form")})))}}},g=y,_=a("2877"),x=a("6544"),C=a.n(x),w=a("8336"),V=a("b0af"),D=a("99d9"),k=a("ac7c"),j=a("62ad"),S=a("ce7e"),I=a("132d"),$=a("0fd9b"),O=a("2fa4"),T=a("8654"),L=Object(_["a"])(g,d,m,!1,null,null,null),A=L.exports;C()(L,{VBtn:w["a"],VCard:V["a"],VCardActions:D["a"],VCardText:D["c"],VCheckbox:k["a"],VCol:j["a"],VDivider:S["a"],VIcon:I["a"],VRow:$["a"],VSpacer:O["a"],VTextField:T["a"]});var F=a("6c6f"),E=a("983c"),P={components:{TaskProjectAssignForm:A,VuePageWrapper:n["default"],VueContextMenu:u["default"],DataTableNoData:c["default"],VueUser:l["default"]},mixins:[o["a"],F["a"],E["a"]],props:{},data:function(){return{htmlTitle:"Assign Project | Project | Tasks",breadCrumbItems:[{text:"Task",disabled:!1,to:{name:"admin-slug-task-overview",params:{slug:this.$route.params.slug}}},{text:"Projects",disabled:!1,to:{name:"admin-slug-task-projects",params:{slug:this.$route.params.slug}}},{text:"Assign Project",disabled:!0}],headers:[{text:"Employee Name",value:"user",width:"20%"},{text:"Activity",value:"activity"},{text:"Employee Rate",value:"employee_rate",align:"center",width:"15%"},{text:"Client Rate",sortable:!0,value:"client_rate",align:"center",width:"15%"},{text:"Billable",align:"center",value:"is_billable",sortable:!1},{text:"Action",align:"center",value:"action",sortable:!1}],tabs:[{tabName:"Activities",value:"",count:"0",color:"blue"}],filter:{dateFilter:{},activeStatus:0,currentCategory:"",show:!1},search:"",statusColor:{Pending:"orange",Approved:"green",Rejected:"red"},deleteNotification:{heading:"Confirm Delete",text:"Are you sure you want to delete this assign activity?",dialog:!1},actionData:{},updateForm:!1,displayForm:!1,projectData:{}}},computed:{dataTableFilter:function(){return{search:this.search}}},created:function(){var e=this;this.dataTableEndpoint=b["a"].getAssignProject(this.$route.params.id)+"?as=hr",this.getData("task/projects/".concat(this.$route.params.id,"/?as=hr")).then((function(t){e.projectData=t}))},methods:{processAfterTableLoad:function(){this.updateCounts(this.response.stats)},triggerForm:function(e,t){this.assignKey++,"delete"===e?this.deleteNotification.dialog=!0:"update"===e?(this.updateForm=!0,this.displayForm=!0):(this.updateForm=!1,this.displayForm=!0),this.actionData=t||void 0},updateCounts:function(e){this.tabs[0].count=e.activity},deleteDataItem:function(){var e=this;return Object(r["a"])(regeneratorRuntime.mark((function t(){return regeneratorRuntime.wrap((function(t){while(1)switch(t.prev=t.next){case 0:e.crud.message="Successfully unassigned employee.",e.deleteData(b["a"].deleteAssignProject(e.$route.params.id,e.actionData.id)+"?as=hr").then((function(){e.dismissForm()}));case 2:case"end":return t.stop()}}),t)})))()},refreshData:function(e){!0===e&&(this.countUpdated=!1,this.fetchDataTable()),this.showRequestDetails=!1},dismissForm:function(){this.displayForm=!1,this.fetchDataTable()}}},B=P,R=a("cc20"),U=a("8fea"),N=a("169a"),q=a("0789"),M=a("71a3"),z=a("fe57"),W=a("3a2f"),H=Object(_["a"])(B,i,s,!1,null,null,null);t["default"]=H.exports;C()(H,{VBtn:w["a"],VCard:V["a"],VChip:R["a"],VDataTable:U["a"],VDialog:N["a"],VDivider:S["a"],VIcon:I["a"],VRow:$["a"],VSlideYTransition:q["g"],VTab:M["a"],VTabs:z["a"],VTooltip:W["a"]})},"983c":function(e,t,a){"use strict";a("d3b7");t["a"]={methods:{getData:function(e,t,a){var i=this,s=arguments.length>3&&void 0!==arguments[3]&&arguments[3];return new Promise((function(r,n){!i.loading&&e&&(i.clearNonFieldErrors(),i.$validator.errors.clear(),i.loading=s,i.$http.get(e,a||{params:t||{}}).then((function(e){r(e),i.loading=!1})).catch((function(e){i.pushErrors(e),i.notifyInvalidFormResponse(),n(e),i.loading=!1})))}))},getBlockingData:function(e,t,a){var i=this;return new Promise((function(s,r){i.getData(e,t,a,!0).then((function(e){s(e)})).catch((function(e){r(e)}))}))}}}},abd3:function(e,t,a){},e4bf:function(e,t,a){"use strict";a.r(t);var i=function(){var e=this,t=e.$createElement,a=e._self._c||t;return a("div",[e.contextList.filter((function(e){return!e.hide})).length<3&&!e.hideIcons||e.showIcons?a("div",e._l(e.contextList,(function(t,i){return a("span",{key:i},[t.hide?e._e():a("v-tooltip",{attrs:{disabled:e.$vuetify.breakpoint.xs,top:""},scopedSlots:e._u([{key:"activator",fn:function(s){var r=s.on;return[a("v-btn",e._g({staticClass:"mx-0",attrs:{text:"",width:e.small?"18":"22",depressed:"",icon:""}},r),[a("v-icon",{attrs:{disabled:t.disabled,color:t.color,"data-cy":e.dataCyVariable+"btn-dropdown-menu-item-"+(i+1),dark:!t.disabled,small:e.small,size:"20",dense:""},domProps:{textContent:e._s(t.icon)},on:{click:function(t){return e.$emit("click"+i)}}})],1)]}}],null,!0)},[a("span",{domProps:{textContent:e._s(t.disabled&&t.disable_message||t.name)}})])],1)})),0):a("v-menu",{attrs:{"offset-y":"",left:"",transition:"slide-y-transition"},scopedSlots:e._u([{key:"activator",fn:function(t){var i=t.on;return[a("v-btn",e._g({attrs:{small:"",text:"",icon:""}},i),[a("v-icon",{attrs:{"data-cy":"btn-dropdown-menu"},domProps:{textContent:e._s("mdi-dots-vertical")}})],1)]}}])},e._l(e.contextList,(function(t,i){return a("v-list",{key:i,staticClass:"pa-0",attrs:{dense:""}},[t.hide?e._e():a("div",[t.disabled?a("v-list-item",{attrs:{"data-cy":"btn-dropdown-menu-item"}},[a("v-tooltip",{attrs:{top:""},scopedSlots:e._u([{key:"activator",fn:function(i){var s=i.on;return[a("v-list-item-title",e._g({},s),[a("v-icon",{attrs:{disabled:"",small:"",color:t.color},domProps:{textContent:e._s(t.icon)}}),a("span",{staticClass:"ml-1 grey--text",domProps:{textContent:e._s(t.name)}})],1)]}}],null,!0)},[a("span",{domProps:{textContent:e._s(t.disabled&&t.disable_message||t.name)}})])],1):a("v-list-item",{attrs:{"data-cy":"btn-dropdown-menu-item"},on:{click:function(t){return e.$emit("click"+i)}}},[a("v-list-item-title",[a("v-icon",{attrs:{color:t.color,small:"",dense:""},domProps:{textContent:e._s(t.icon)}}),a("span",{staticClass:"ml-1",class:t.text_color,domProps:{textContent:e._s(t.name)}})],1)],1)],1)])})),1)],1)},s=[],r={name:"VueContextMenu",props:{contextList:{type:Array,default:function(){return[]}},dataCyVariable:{type:String,default:""},showIcons:{type:Boolean,default:!1},hideIcons:{type:Boolean,default:!1},small:{type:Boolean,default:!1}}},n=r,o=a("2877"),l=a("6544"),c=a.n(l),u=a("8336"),d=a("132d"),m=a("8860"),p=a("da13"),f=a("5d23"),h=a("e449"),v=a("3a2f"),b=Object(o["a"])(n,i,s,!1,null,"71ee785c",null);t["default"]=b.exports;c()(b,{VBtn:u["a"],VIcon:d["a"],VList:m["a"],VListItem:p["a"],VListItemTitle:f["c"],VMenu:h["a"],VTooltip:v["a"]})},ef8c:function(e,t,a){"use strict";a.r(t);var i=function(){var e=this,t=e.$createElement,a=e._self._c||t;return a("div",[a("v-autocomplete",{class:e.appliedClass,attrs:{items:e.itemsSorted,loading:e.isLoading,"search-input":e.search,multiple:e.multiple,label:e.label,error:e.errorMessages.length>0,"error-messages":e.errorMessages,disabled:e.disabled,"prepend-inner-icon":e.prependInnerIcon,clearable:e.clearable&&!e.readonly,readonly:!!e.readonly,"hide-details":e.hideDetails,"data-cy":"input-user-autocomplete-"+e.dataCyVariable,placeholder:e.placeholder,"hide-selected":"","hide-no-data":"","item-text":"full_name","item-value":"id"},on:{"update:searchInput":function(t){e.search=t},"update:search-input":function(t){e.search=t},blur:function(t){return e.$emit("blur")}},scopedSlots:e._u([{key:"selection",fn:function(t){return[a("v-chip",{attrs:{"input-value":t.selected,close:(e.clearable||!e.clearable&&!e.multiple)&&!e.readonly,small:""},on:{"click:close":function(a){return e.remove(t.item)}}},[a("v-avatar",{attrs:{left:""}},[a("v-img",{attrs:{src:t.item.profile_picture,cover:""}})],1),e._v(" "+e._s(e._f("truncate")(t.item.full_name,e.truncate))+" ")],1)]}},{key:"item",fn:function(t){var i=t.item;return[a("v-list-item-avatar",[a("v-avatar",{attrs:{size:"30"}},[a("v-img",{attrs:{src:i.profile_picture,cover:""}})],1)],1),a("v-list-item-content",[a("v-list-item-title",[e._v(" "+e._s(e._f("truncate")(i.full_name,20))+" "),i.employee_code?a("span",[e._v("("+e._s(i.employee_code)+")")]):e._e()]),i.division?a("v-list-item-subtitle",{domProps:{textContent:e._s(i.division)}}):e._e()],1)]}}]),model:{value:e.selectedData,callback:function(t){e.selectedData=t},expression:"selectedData"}})],1)},s=[],r=a("53ca"),n=(a("a9e3"),a("ac1f"),a("841c"),a("4e827"),a("2ca0"),a("d81d"),a("a434"),a("d3b7"),a("159b"),a("7db0"),a("4de4"),a("caad"),a("2532"),a("fab2")),o=a("63ea"),l=a.n(o),c={props:{value:{type:[Number,String,Array,Object],required:!1,default:function(){return null}},dataCyVariable:{type:String,default:""},userObject:{type:[Object,Array],required:!1,default:function(){return{}}},params:{type:[Object,Array],required:!1,default:function(){return{}}},multiple:{type:Boolean,required:!1,default:!1},disabled:{type:Boolean,required:!1,default:!1},errorMessages:{type:[String,Array],default:function(){return[]}},label:{type:String,default:"Select Employee"},prependInnerIcon:{type:String,default:"mdi-account-plus-outline"},itemsToExclude:{type:[Array,Number],default:null},itemsToInclude:{type:[Array,Number],default:null},clearable:{type:Boolean,default:!0},readonly:{type:Boolean,default:!1},hideDetails:{type:Boolean,default:!1},appliedClass:{type:String,default:""},truncate:{type:Number,default:10},placeholder:{type:String,default:""}},data:function(){return{isLoading:!1,items:[],allUsers:[],selectedData:null,search:null}},computed:{itemsSorted:function(){return this.sortBySearch(this.items,this.search?this.search.toLowerCase():"")}},watch:{value:{handler:function(e,t){!e&&t&&(this.selectedData="",this.populateInitialUsers()),!t&&e&&this.populateInitialUsers()},immediate:!0},search:function(e){!e||this.items.length>0||this.fetchUsers()},selectedData:function(e){this.search="",this.syncUserData(e),this.$emit("input",e)},itemsToExclude:function(){this.items=this.excludeRecord(this.allUsers)},itemsToInclude:function(){this.items=this.includeRecord(this.allUsers)},params:{handler:function(e,t){l()(e,t)||this.fetchUsers()},deep:!0}},methods:{sortBySearch:function(e,t){return e.sort((function(e,a){return e.full_name.toLowerCase().startsWith(t)&&a.full_name.toLowerCase().startsWith(t)?e.full_name.toLowerCase().localeCompare(a.full_name.toLowerCase()):e.full_name.toLowerCase().startsWith(t)?-1:a.full_name.toLowerCase().startsWith(t)?1:e.full_name.toLowerCase().localeCompare(a.full_name.toLowerCase())}))},populateInitialUsers:function(){this.fetchUsers(this.value),Array.isArray(this.value)?"object"===Object(r["a"])(this.value[0])?this.selectedData=this.value.map((function(e){return e.user.id})):this.selectedData=this.value:null===this.value?this.selectedData="":"object"===Object(r["a"])(this.value)?this.selectedData=this.value.id:this.selectedData=this.value,this.$emit("input",this.selectedData)},remove:function(e){if(this.selectedData instanceof Object){var t=this.selectedData.indexOf(e.id);t>=0&&this.selectedData.splice(t,1),this.$emit("remove",e)}else this.selectedData=""},fetchUsers:function(e){var t=this;this.isLoading||(this.isLoading=!0,this.$http.get(n["a"].autocomplete,{params:this.params}).then((function(a){t.allUsers=a,t.itemsToExclude&&(a=t.excludeRecord(a)),t.itemsToInclude&&(a=t.includeRecord(a)),t.items=a,e&&t.syncUserData(e)})).finally((function(){return t.isLoading=!1})))},syncUserData:function(e){var t=this;if(e instanceof Array){var a=[];e.forEach((function(e){a.unshift(t.items.find((function(t){return t.id===e})))})),this.$emit("update:userObject",a)}else{var i=this.items.find((function(t){return t.id===e}));this.$emit("update:userObject",i)}},excludeRecord:function(e){var t=[];return"number"===typeof this.itemsToExclude?t.push(this.itemsToExclude):t=this.itemsToExclude,e.filter((function(e){return!t.includes(e.id)}))},includeRecord:function(e){var t=this;return e.filter((function(e){return t.itemsToInclude.includes(e.id)}))}}},u=c,d=a("2877"),m=a("6544"),p=a.n(m),f=a("c6a6"),h=a("8212"),v=a("cc20"),b=a("adda"),y=a("8270"),g=a("5d23"),_=Object(d["a"])(u,i,s,!1,null,null,null);t["default"]=_.exports;p()(_,{VAutocomplete:f["a"],VAvatar:h["a"],VChip:v["a"],VImg:b["a"],VListItemAvatar:y["a"],VListItemContent:g["a"],VListItemSubtitle:g["b"],VListItemTitle:g["c"]})},fab2:function(e,t,a){"use strict";t["a"]={getUserList:"/users/",postUser:"/users/",autocomplete:"/users/autocomplete/",postImportUser:"/users/import/",downloadUserImportSample:function(e){return"/users/import/sample/?organization=".concat(e)},getUserDetail:function(e){return"/users/".concat(e,"/")},getInternalUserDetail:function(e){return"/users/".concat(e,"/internal-detail")},deleteUser:function(e){return"/users/".concat(e,"/")},updateUser:function(e){return"/users/".concat(e,"/")},changePassword:function(e){return"/users/".concat(e,"/change-password/")},getUserCV:function(e){return"/users/".concat(e,"/cv/")},getProfileCompleteness:function(e){return"users/".concat(e,"/profile-completeness/")}}}}]);