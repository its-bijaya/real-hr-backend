(window["webpackJsonp"]=window["webpackJsonp"]||[]).push([["pages/admin/_slug/organization/settings/application","chunk-26c51c79","chunk-31f8a6e6","chunk-2d2259e9","chunk-6441e173","chunk-2d213000"],{"0549":function(t,e,a){"use strict";a.r(e);var i=function(){var t=this,e=t.$createElement,a=t._self._c||e;return a("div",[a("v-row",{staticClass:"mb-3",attrs:{"no-gutters":""}},[t.breadCrumbs?a("v-col",{attrs:{cols:"12"}},[a("v-card",{attrs:{flat:""}},[a("v-breadcrumbs",{staticClass:"text-body-1 pa-2",class:{"text-caption pa-1":t.$vuetify.breakpoint.xs},attrs:{items:t.breadCrumbs},scopedSlots:t._u([{key:"item",fn:function(e){return[a("span",{class:e.item.disabled?"grey--text":"baseColor--text text--accent-2 pointer",domProps:{textContent:t._s(e.item.text)},on:{click:function(a){return t.$router.push(e.item.to)}}})]}}],null,!1,1670153796)},[a("v-icon",{attrs:{slot:"divider"},slot:"divider"},[t._v("mdi-chevron-right")])],1)],1)],1):t._e()],1),a("v-row",{attrs:{"no-gutters":""}},[a("v-col",{attrs:{cols:"12"}},[t._t("default")],2)],1)],1)},n=[],s=a("5530"),r=(a("ac1f"),a("1276"),a("b0c0"),a("2f62")),o={props:{title:{type:String,required:!0},breadCrumbs:{type:Array,default:function(){return[]}}},computed:Object(s["a"])({},Object(r["c"])({getOrganizationName:"organization/getOrganizationName",getSupervisorSwitchedOrganization:"supervisor/getSwitchedOrganization"})),mounted:function(){document.title="".concat(this.title," | RealHRsoft");var t=this.$route.params.slug?"admin-slug-dashboard":"root",e=this.$route.name.split("-"),a=this.getOrganizationName;this.getSupervisorSwitchedOrganization&&"user"===e[0]&&"supervisor"===e[1]&&(a=this.getSupervisorSwitchedOrganization.name),this.breadCrumbs.unshift({text:a,disabled:!1,to:{name:t,params:{slug:this.$route.params.slug}}})}},l=o,c=a("2877"),d=a("6544"),u=a.n(d),p=a("2bc5"),h=a("b0af"),f=a("62ad"),g=a("132d"),m=a("0fd9b"),b=Object(c["a"])(l,i,n,!1,null,null,null);e["default"]=b.exports;u()(b,{VBreadcrumbs:p["a"],VCard:h["a"],VCol:f["a"],VIcon:g["a"],VRow:m["a"]})},"0798":function(t,e,a){"use strict";var i=a("5530"),n=a("ade3"),s=(a("caad"),a("0c18"),a("10d2")),r=a("afdd"),o=a("9d26"),l=a("f2e7"),c=a("7560"),d=a("f40d"),u=a("58df"),p=a("d9bd");e["a"]=Object(u["a"])(s["a"],l["a"],d["a"]).extend({name:"v-alert",props:{border:{type:String,validator:function(t){return["top","right","bottom","left"].includes(t)}},closeLabel:{type:String,default:"$vuetify.close"},coloredBorder:Boolean,dense:Boolean,dismissible:Boolean,closeIcon:{type:String,default:"$cancel"},icon:{default:"",type:[Boolean,String],validator:function(t){return"string"===typeof t||!1===t}},outlined:Boolean,prominent:Boolean,text:Boolean,type:{type:String,validator:function(t){return["info","error","success","warning"].includes(t)}},value:{type:Boolean,default:!0}},computed:{__cachedBorder:function(){if(!this.border)return null;var t={staticClass:"v-alert__border",class:Object(n["a"])({},"v-alert__border--".concat(this.border),!0)};return this.coloredBorder&&(t=this.setBackgroundColor(this.computedColor,t),t.class["v-alert__border--has-color"]=!0),this.$createElement("div",t)},__cachedDismissible:function(){var t=this;if(!this.dismissible)return null;var e=this.iconColor;return this.$createElement(r["a"],{staticClass:"v-alert__dismissible",props:{color:e,icon:!0,small:!0},attrs:{"aria-label":this.$vuetify.lang.t(this.closeLabel)},on:{click:function(){return t.isActive=!1}}},[this.$createElement(o["a"],{props:{color:e}},this.closeIcon)])},__cachedIcon:function(){return this.computedIcon?this.$createElement(o["a"],{staticClass:"v-alert__icon",props:{color:this.iconColor}},this.computedIcon):null},classes:function(){var t=Object(i["a"])(Object(i["a"])({},s["a"].options.computed.classes.call(this)),{},{"v-alert--border":Boolean(this.border),"v-alert--dense":this.dense,"v-alert--outlined":this.outlined,"v-alert--prominent":this.prominent,"v-alert--text":this.text});return this.border&&(t["v-alert--border-".concat(this.border)]=!0),t},computedColor:function(){return this.color||this.type},computedIcon:function(){return!1!==this.icon&&("string"===typeof this.icon&&this.icon?this.icon:!!["error","info","success","warning"].includes(this.type)&&"$".concat(this.type))},hasColoredIcon:function(){return this.hasText||Boolean(this.border)&&this.coloredBorder},hasText:function(){return this.text||this.outlined},iconColor:function(){return this.hasColoredIcon?this.computedColor:void 0},isDark:function(){return!(!this.type||this.coloredBorder||this.outlined)||c["a"].options.computed.isDark.call(this)}},created:function(){this.$attrs.hasOwnProperty("outline")&&Object(p["a"])("outline","outlined",this)},methods:{genWrapper:function(){var t=[this.$slots.prepend||this.__cachedIcon,this.genContent(),this.__cachedBorder,this.$slots.append,this.$scopedSlots.close?this.$scopedSlots.close({toggle:this.toggle}):this.__cachedDismissible],e={staticClass:"v-alert__wrapper"};return this.$createElement("div",e,t)},genContent:function(){return this.$createElement("div",{staticClass:"v-alert__content"},this.$slots.default)},genAlert:function(){var t={staticClass:"v-alert",attrs:{role:"alert"},on:this.listeners$,class:this.classes,style:this.styles,directives:[{name:"show",value:this.isActive}]};if(!this.coloredBorder){var e=this.hasText?this.setTextColor:this.setBackgroundColor;t=e(this.computedColor,t)}return this.$createElement("div",t,[this.genWrapper()])},toggle:function(){this.isActive=!this.isActive}},render:function(t){var e=this.genAlert();return this.transition?t("transition",{props:{name:this.transition,origin:this.origin,mode:this.mode}},[e]):e}})},"0c18":function(t,e,a){},"17cc":function(t,e,a){"use strict";var i=a("b85c"),n=a("1da1"),s=a("5530");a("96cf"),a("ac1f"),a("841c"),a("d3b7"),a("3ca3"),a("ddb0"),a("2b3d"),a("b64b");e["a"]={data:function(){return{fetchedResults:[],response:{},extra_data:"",appliedFilters:{},footerProps:{itemsPerPageOptions:[10,20,30,40,50,100]},pagination:{sortBy:["modified_at"],descending:!1,totalItems:0,page:1,rowsPerPage:10,pageCount:0},triggerDataTable:!0,fullParams:""}},created:function(){this.getParams(this.DataTableFilter)},methods:{getParams:function(t){var e=Object(s["a"])(Object(s["a"])({},t),{},{offset:(this.pagination.page-1)*this.pagination.rowsPerPage,limit:this.pagination.rowsPerPage,ordering:this.pagination.descending?this.pagination.sortBy:"-"+this.pagination.sortBy});this.fullParams=this.convertToURLSearchParams(e)},loadDataTable:function(t){this.response=t,this.fetchedResults=t.results,this.pagination.totalItems=t.count,this.extra_data=t.extra_data,this.triggerDataTable=!0},fetchData:function(t){var e=this;return Object(n["a"])(regeneratorRuntime.mark((function a(){var i,n;return regeneratorRuntime.wrap((function(a){while(1)switch(a.prev=a.next){case 0:return console.warn("DatatableMixin: fetchData has been deprecated. Please use the function in page itself."),i=Object(s["a"])(Object(s["a"])(Object(s["a"])({},t),e.appliedFilters),{},{search:e.search,offset:(e.pagination.page-1)*e.pagination.rowsPerPage,limit:e.pagination.rowsPerPage,ordering:e.pagination.descending?e.pagination.sortBy:"-"+e.pagination.sortBy}),n=e.convertToURLSearchParams(i),e.loading=!0,a.next=6,e.$http.get(e.endpoint,{params:n}).then((function(t){e.response=t,e.fetchedResults=t.results,e.pagination.totalItems=t.count})).finally((function(){e.loading=!1}));case 6:case"end":return a.stop()}}),a)})))()},applyFilters:function(t){this.appliedFilters=t,this.fetchData(t)},convertToURLSearchParams:function(t){for(var e=new URLSearchParams,a=0,n=Object.keys(t);a<n.length;a++){var s=n[a],r=t[s];if(void 0===r&&(r=""),Array.isArray(r)){var o,l=Object(i["a"])(r);try{for(l.s();!(o=l.n()).done;){var c=o.value;e.append(s,c)}}catch(d){l.e(d)}finally{l.f()}}else e.append(s,r)}return e},loadDataTableChange:function(){var t=this;this.triggerDataTable&&(this.getParams(this.DataTableFilter),this.$nextTick((function(){t.fetchDataTable()})))}},watch:{DataTableFilter:function(t){this.fetchedResults=[],this.getParams(t),this.fetchDataTable(),this.pagination.page=1},"pagination.sortBy":function(){this.fetchedResults=[],this.loadDataTableChange()},"pagination.descending":function(){this.fetchedResults=[],this.loadDataTableChange()},"pagination.page":function(){this.fetchedResults=[],this.loadDataTableChange()},"pagination.rowsPerPage":function(){this.fetchedResults=[],this.loadDataTableChange()}}}},"1f09":function(t,e,a){},"2bc5":function(t,e,a){"use strict";var i=a("5530"),n=(a("a15b"),a("abd3"),a("ade3")),s=a("1c87"),r=a("58df"),o=Object(r["a"])(s["a"]).extend({name:"v-breadcrumbs-item",props:{activeClass:{type:String,default:"v-breadcrumbs__item--disabled"},ripple:{type:[Boolean,Object],default:!1}},computed:{classes:function(){return Object(n["a"])({"v-breadcrumbs__item":!0},this.activeClass,this.disabled)}},render:function(t){var e=this.generateRouteLink(),a=e.tag,n=e.data;return t("li",[t(a,Object(i["a"])(Object(i["a"])({},n),{},{attrs:Object(i["a"])(Object(i["a"])({},n.attrs),{},{"aria-current":this.isActive&&this.isLink?"page":void 0})}),this.$slots.default)])}}),l=a("80d2"),c=Object(l["i"])("v-breadcrumbs__divider","li"),d=a("7560");e["a"]=Object(r["a"])(d["a"]).extend({name:"v-breadcrumbs",props:{divider:{type:String,default:"/"},items:{type:Array,default:function(){return[]}},large:Boolean},computed:{classes:function(){return Object(i["a"])({"v-breadcrumbs--large":this.large},this.themeClasses)}},methods:{genDivider:function(){return this.$createElement(c,this.$slots.divider?this.$slots.divider:this.divider)},genItems:function(){for(var t=[],e=!!this.$scopedSlots.item,a=[],i=0;i<this.items.length;i++){var n=this.items[i];a.push(n.text),e?t.push(this.$scopedSlots.item({item:n})):t.push(this.$createElement(o,{key:a.join("."),props:n},[n.text])),i<this.items.length-1&&t.push(this.genDivider())}return t}},render:function(t){var e=this.$slots.default||this.genItems();return t("ul",{staticClass:"v-breadcrumbs",class:this.classes},e)}})},3129:function(t,e,a){"use strict";var i=a("3835"),n=a("5530"),s=(a("ac1f"),a("1276"),a("d81d"),a("a630"),a("3ca3"),a("5319"),a("1f09"),a("c995")),r=a("24b2"),o=a("7560"),l=a("58df"),c=a("80d2");e["a"]=Object(l["a"])(s["a"],r["a"],o["a"]).extend({name:"VSkeletonLoader",props:{boilerplate:Boolean,loading:Boolean,tile:Boolean,transition:String,type:String,types:{type:Object,default:function(){return{}}}},computed:{attrs:function(){return this.isLoading?this.boilerplate?{}:Object(n["a"])({"aria-busy":!0,"aria-live":"polite",role:"alert"},this.$attrs):this.$attrs},classes:function(){return Object(n["a"])(Object(n["a"])({"v-skeleton-loader--boilerplate":this.boilerplate,"v-skeleton-loader--is-loading":this.isLoading,"v-skeleton-loader--tile":this.tile},this.themeClasses),this.elevationClasses)},isLoading:function(){return!("default"in this.$scopedSlots)||this.loading},rootTypes:function(){return Object(n["a"])({actions:"button@2",article:"heading, paragraph",avatar:"avatar",button:"button",card:"image, card-heading","card-avatar":"image, list-item-avatar","card-heading":"heading",chip:"chip","date-picker":"list-item, card-heading, divider, date-picker-options, date-picker-days, actions","date-picker-options":"text, avatar@2","date-picker-days":"avatar@28",heading:"heading",image:"image","list-item":"text","list-item-avatar":"avatar, text","list-item-two-line":"sentences","list-item-avatar-two-line":"avatar, sentences","list-item-three-line":"paragraph","list-item-avatar-three-line":"avatar, paragraph",paragraph:"text@3",sentences:"text@2",table:"table-heading, table-thead, table-tbody, table-tfoot","table-heading":"heading, text","table-thead":"heading@6","table-tbody":"table-row-divider@6","table-row-divider":"table-row, divider","table-row":"table-cell@6","table-cell":"text","table-tfoot":"text@2, avatar@2",text:"text"},this.types)}},methods:{genBone:function(t,e){return this.$createElement("div",{staticClass:"v-skeleton-loader__".concat(t," v-skeleton-loader__bone")},e)},genBones:function(t){var e=this,a=t.split("@"),n=Object(i["a"])(a,2),s=n[0],r=n[1],o=function(){return e.genStructure(s)};return Array.from({length:r}).map(o)},genStructure:function(t){var e=[];t=t||this.type||"";var a=this.rootTypes[t]||"";if(t===a);else{if(t.indexOf(",")>-1)return this.mapBones(t);if(t.indexOf("@")>-1)return this.genBones(t);a.indexOf(",")>-1?e=this.mapBones(a):a.indexOf("@")>-1?e=this.genBones(a):a&&e.push(this.genStructure(a))}return[this.genBone(t,e)]},genSkeleton:function(){var t=[];return this.isLoading?t.push(this.genStructure()):t.push(Object(c["s"])(this)),this.transition?this.$createElement("transition",{props:{name:this.transition},on:{afterEnter:this.resetStyles,beforeEnter:this.onBeforeEnter,beforeLeave:this.onBeforeLeave,leaveCancelled:this.resetStyles}},t):t},mapBones:function(t){return t.replace(/\s/g,"").split(",").map(this.genStructure)},onBeforeEnter:function(t){this.resetStyles(t),this.isLoading&&(t._initialStyle={display:t.style.display,transition:t.style.transition},t.style.setProperty("transition","none","important"))},onBeforeLeave:function(t){t.style.setProperty("display","none","important")},resetStyles:function(t){t._initialStyle&&(t.style.display=t._initialStyle.display||"",t.style.transition=t._initialStyle.transition,delete t._initialStyle)}},render:function(t){return t("div",{staticClass:"v-skeleton-loader",attrs:this.attrs,on:this.$listeners,class:this.classes,style:this.isLoading?this.measurableStyles:void 0},[this.genSkeleton()])}})},"878b":function(t,e,a){"use strict";var i=function(){var t=this,e=t.$createElement,a=t._self._c||e;return a("div",[a("v-card-actions",[a("v-spacer"),t.hideClear?t._e():a("v-btn",{attrs:{text:"",small:""},domProps:{textContent:t._s("Clear")},on:{click:function(e){return t.$emit("clearForm")}}}),a("v-btn",{attrs:{disabled:t.formErrors||t.disabled,color:t.deleteInstance?"red":"primary",depressed:"",small:"",loading:t.loading,type:"submit"}},[a("v-icon",{staticClass:"mr-1",attrs:{size:"14"}},[t._v(" mdi-content-save-outline ")]),t._v(" "+t._s(t.deleteInstance?"Delete":"Save")+" ")],1)],1)],1)},n=[],s={props:{hideClear:{type:Boolean,default:!1},formErrors:{type:Boolean,required:!0},disabled:{type:Boolean,default:!1},deleteInstance:{type:Boolean,required:!1,default:!1},loading:{type:Boolean,default:!1}}},r=s,o=a("2877"),l=a("6544"),c=a.n(l),d=a("8336"),u=a("99d9"),p=a("132d"),h=a("2fa4"),f=Object(o["a"])(r,i,n,!1,null,null,null);e["a"]=f.exports;c()(f,{VBtn:d["a"],VCardActions:u["a"],VIcon:p["a"],VSpacer:h["a"]})},"9d01":function(t,e,a){},a51f:function(t,e,a){"use strict";a.r(e);var i=function(){var t=this,e=t.$createElement,a=t._self._c||e;return a("div",[t.search.length>0?a("span",[t._v(' Your search for "'+t._s(t.search)+'" found no results. ')]):t.loading?a("v-skeleton-loader",{attrs:{type:"table",height:t.skeletonLoaderHeight}}):a("no-data-found",{attrs:{text:t.text,height:t.height}},[t._t("default")],2)],1)},n=[],s=(a("a9e3"),a("e585")),r={components:{NoDataFound:s["default"]},props:{search:{type:String,default:""},loading:{type:Boolean,required:!0},text:{type:String,default:"No data available at the moment"},height:{type:[String,Number],default:200},skeletonLoaderHeight:{type:[String,Number],default:void 0}}},o=r,l=a("2877"),c=a("6544"),d=a.n(c),u=a("3129"),p=Object(l["a"])(o,i,n,!1,null,null,null);e["default"]=p.exports;d()(p,{VSkeletonLoader:u["a"]})},a79c:function(t,e,a){"use strict";a.d(e,"b",(function(){return n})),a.d(e,"a",(function(){return s}));var i=a("53ca");a("b0c0");function n(t,e,a){var r,o,l=e||new FormData;for(var c in t)if(Object.prototype.hasOwnProperty.call(t,c))if(r=a?a+"."+c:c,o=t[c],"boolean"===typeof o||"number"===typeof o)l.append(r,o);else if(Array.isArray(o))for(var d=0;d<o.length;d++)l.append(r,o[d]);else"object"!==Object(i["a"])(o)||s(o)?s(o)?l.append(r,o,o.name):o?l.append(r,o):o||"undefined"!==typeof o&&l.append(r,""):n(o,l,c);return l}function s(t){return t instanceof File||t instanceof Blob}},ab8a:function(t,e,a){"use strict";a.r(e);var i=function(){var t=this,e=t.$createElement,a=t._self._c||e;return a("div",[t.changeType&&0!==t.nonFieldErrors.length?a("div",t._l(t.nonFieldErrors,(function(e,i){return a("v-col",{key:i},t._l(e,(function(e,i){return a("div",{key:i},[a("span",{domProps:{textContent:t._s(t.key)}}),a("span",{domProps:{textContent:t._s(e.toString())}})])})),0)})),1):t._e(),t.changeType||0===t.nonFieldErrors.length?t._e():a("v-alert",{staticClass:"ma-3",attrs:{outlined:"",dense:"",tile:"",dismissible:"",color:"danger"}},[a("span",{domProps:{textContent:t._s("There are some errors")}}),t._l(t.nonFieldErrors,(function(e,i){return a("div",{key:i},t._l(e,(function(e,i){return a("div",{key:i},[a("ul",[a("li",[a("span",{domProps:{textContent:t._s(t.key)}}),a("span",{domProps:{textContent:t._s(e.toString())}})])])])})),0)}))],2)],1)},n=[],s={props:{nonFieldErrors:{type:Array,required:!0},changeType:{type:Boolean,default:!1}},data:function(){return{key:""}}},r=s,o=a("2877"),l=a("6544"),c=a.n(l),d=a("0798"),u=a("62ad"),p=Object(o["a"])(r,i,n,!1,null,null,null);e["default"]=p.exports;c()(p,{VAlert:d["a"],VCol:u["a"]})},abd3:function(t,e,a){},b73d:function(t,e,a){"use strict";var i=a("5530"),n=(a("0481"),a("ec29"),a("9d01"),a("fe09")),s=a("c37a"),r=a("c3f0"),o=a("0789"),l=a("490a"),c=a("80d2");e["a"]=n["a"].extend({name:"v-switch",directives:{Touch:r["a"]},props:{inset:Boolean,loading:{type:[Boolean,String],default:!1},flat:{type:Boolean,default:!1}},computed:{classes:function(){return Object(i["a"])(Object(i["a"])({},s["a"].options.computed.classes.call(this)),{},{"v-input--selection-controls v-input--switch":!0,"v-input--switch--flat":this.flat,"v-input--switch--inset":this.inset})},attrs:function(){return{"aria-checked":String(this.isActive),"aria-disabled":String(this.isDisabled),role:"switch"}},validationState:function(){return this.hasError&&this.shouldValidate?"error":this.hasSuccess?"success":null!==this.hasColor?this.computedColor:void 0},switchData:function(){return this.setTextColor(this.loading?void 0:this.validationState,{class:this.themeClasses})}},methods:{genDefaultSlot:function(){return[this.genSwitch(),this.genLabel()]},genSwitch:function(){return this.$createElement("div",{staticClass:"v-input--selection-controls__input"},[this.genInput("checkbox",Object(i["a"])(Object(i["a"])({},this.attrs),this.attrs$)),this.genRipple(this.setTextColor(this.validationState,{directives:[{name:"touch",value:{left:this.onSwipeLeft,right:this.onSwipeRight}}]})),this.$createElement("div",Object(i["a"])({staticClass:"v-input--switch__track"},this.switchData)),this.$createElement("div",Object(i["a"])({staticClass:"v-input--switch__thumb"},this.switchData),[this.genProgress()])])},genProgress:function(){return this.$createElement(o["c"],{},[!1===this.loading?null:this.$slots.progress||this.$createElement(l["a"],{props:{color:!0===this.loading||""===this.loading?this.color||"primary":this.loading,size:16,width:2,indeterminate:!0}})])},onSwipeLeft:function(){this.isActive&&this.onChange()},onSwipeRight:function(){this.isActive||this.onChange()},onKeydown:function(t){(t.keyCode===c["y"].left&&this.isActive||t.keyCode===c["y"].right&&!this.isActive)&&this.onChange()}}})},dff5:function(t,e,a){"use strict";a.r(e);var i=function(){var t=this,e=t.$createElement,a=t._self._c||e;return a("vue-page-wrapper",{attrs:{title:t.htmlTitle,"bread-crumbs":t.breadCrumbItems}},[a("v-card",[a("vue-card-title",{attrs:{title:"Disabled Applications",subtitle:"Here you can add applications that you want to disable.",icon:"mdi-cog-outline"}},[a("template",{slot:"actions"},[t.verifyPermission(t.allPermissions.APPLICATION_SETTING_PERMISSION)?a("v-btn",{attrs:{disabled:t.disableButton,small:"",color:"primary",depressed:""},on:{click:function(e){t.displayForm=!0}}},[t._v(" Add New ")]):t._e(),a("v-dialog",{attrs:{persistent:"",scrollable:"",width:"560"},on:{keydown:function(e){if(!e.type.indexOf("key")&&t._k(e.keyCode,"esc",27,e.key,["Esc","Escape"]))return null;t.displayForm=!1}},model:{value:t.displayForm,callback:function(e){t.displayForm=e},expression:"displayForm"}},[a("v-card",[a("vue-card-title",{attrs:{title:"Disable Application",subtitle:"Here you can disable applications",icon:"mdi-cog-outline",closable:""},on:{close:function(e){t.displayForm=!1}}}),a("v-divider"),t.displayForm?a("application-setting",{attrs:{"filtered-applications":t.filteredApplications},on:{refresh:function(e){t.displayForm=!1,t.fetchDataTable()}}}):t._e()],1)],1)],1)],2),a("v-divider"),a("v-data-table",{attrs:{headers:t.headers,items:t.fetchedResults,"sort-desc":t.pagination.descending,"sort-by":t.pagination.sortBy,page:t.pagination.page,"items-per-page":t.pagination.rowsPerPage,"footer-props":t.footerProps,"server-items-length":t.pagination.totalItems,"mobile-breakpoint":0,"must-sort":""},on:{"update:sortDesc":function(e){return t.$set(t.pagination,"descending",e)},"update:sort-desc":function(e){return t.$set(t.pagination,"descending",e)},"update:sortBy":function(e){return t.$set(t.pagination,"sortBy",e)},"update:sort-by":function(e){return t.$set(t.pagination,"sortBy",e)},"update:page":function(e){return t.$set(t.pagination,"page",e)},"update:itemsPerPage":function(e){return t.$set(t.pagination,"rowsPerPage",e)},"update:items-per-page":function(e){return t.$set(t.pagination,"rowsPerPage",e)}},scopedSlots:t._u([{key:"item",fn:function(e){return[a("tr",[a("td",{staticClass:"text-capitalize"},[a("span",{domProps:{textContent:t._s(e.item.application)}})]),a("td",[a("v-switch",{attrs:{disabled:["worklog","recruitment"].includes(e.item.application),color:"green"},on:{change:function(a){return t.updateForHr(e.item)}},model:{value:e.item.enabled,callback:function(a){t.$set(e.item,"enabled",a)},expression:"props.item.enabled"}})],1),a("td",{staticClass:"text-center"},[a("vue-context-menu",{attrs:{"context-list":[{name:"Enable Application",icon:"mdi-trash-can-outline",color:"danger",disabled:!t.verifyPermission(t.allPermissions.ORGANIZATION_DOCUMENTS_PERMISSION),disable_message:"No Permission"}]},on:{click0:function(a){t.deleteNotification.dialog=!0,t.deleteId=e.item.id}}})],1)])]}}])},[a("template",{slot:"no-data"},[a("data-table-no-data",{attrs:{loading:t.loading}})],1)],2)],1),a("vue-dialog",{attrs:{notify:t.deleteNotification},on:{close:function(e){t.deleteNotification.dialog=!1},agree:function(e){return t.deleteApplicationSetting()}}})],1)},n=[],s=a("1da1"),r=a("5530"),o=(a("96cf"),a("4de4"),a("caad"),a("2532"),a("d3b7"),a("d81d"),a("99af"),a("0549")),l=function(){var t=this,e=t.$createElement,a=t._self._c||e;return a("v-form",{ref:"applicationSettingForm",on:{submit:function(e){return e.preventDefault(),t.getFormAction.apply(null,arguments)}}},[a("v-row",{staticClass:"ma-4",attrs:{align:"end"}},[t.nonFieldErrors.length>0?a("v-col",{attrs:{cols:"12"}},[a("non-field-form-errors",{attrs:{"non-field-errors":t.nonFieldErrors}})],1):t._e(),a("v-col",{attrs:{md:"6",sm:"12"}},[a("v-select",t._b({directives:[{name:"validate",rawName:"v-validate",value:"required",expression:"'required'"}],attrs:{items:t.filteredApplications,"prepend-inner-icon":"mdi-apps","item-text":"title","item-value":"value"},model:{value:t.formValues.application,callback:function(e){t.$set(t.formValues,"application",e)},expression:"formValues.application"}},"v-select",t.veeValidate("application","Select Application To Disable *"),!1))],1)],1),a("v-divider"),a("form-submit",{attrs:{"form-errors":t.errors.any()},on:{clearForm:t.clearForm}})],1)},c=[],d=a("c44a"),u=a("ab8a"),p=a("878b"),h=a("a79c"),f={postApplicationSetting:function(t){return"/org/".concat(t,"/setting/applications/")},updateApplicationSetting:function(t,e){return"/org/".concat(t,"/setting/applications/").concat(e,"/")},getApplicationSetting:function(t){return"/org/".concat(t,"/setting/applications/")},deleteApplicationSetting:function(t,e){return"/org/".concat(t,"/setting/applications/").concat(e,"/")}},g={components:{NonFieldFormErrors:u["default"],FormSubmit:p["a"]},mixins:[d["a"]],props:{filteredApplications:{type:Array,required:!0}},data:function(){return{formValues:{application:"",enabled:!1}}},methods:{getFormAction:function(){var t=this;return Object(s["a"])(regeneratorRuntime.mark((function e(){return regeneratorRuntime.wrap((function(e){while(1)switch(e.prev=e.next){case 0:return e.next=2,t.validateAllFields();case 2:if(!e.sent){e.next=4;break}t.createApplicationSetting();case 4:case"end":return e.stop()}}),e)})))()},createApplicationSetting:function(){var t=this;return Object(s["a"])(regeneratorRuntime.mark((function e(){return regeneratorRuntime.wrap((function(e){while(1)switch(e.prev=e.next){case 0:t.$http.post(f.postApplicationSetting(t.getOrganizationSlug),Object(h["b"])(t.formValues)).then((function(){t.notifyUser("Successfully created Application Setting","green"),t.$emit("refresh")})).catch((function(e){t.pushErrors(e)}));case 1:case"end":return e.stop()}}),e)})))()},clearForm:function(){this.errors.clear(),this.clearNonFieldErrors(),this.$refs.applicationSettingForm.reset()}}},m=g,b=a("2877"),v=a("6544"),y=a.n(v),_=a("62ad"),S=a("ce7e"),x=a("4bd4"),C=a("0fd9b"),w=a("b974"),O=Object(b["a"])(m,l,c,!1,null,null,null),k=O.exports;y()(O,{VCol:_["a"],VDivider:S["a"],VForm:x["a"],VRow:C["a"],VSelect:w["a"]});var $=a("a51f"),A=a("ea98"),P=a("17cc"),B=a("8b61"),D=a("a09e"),j=a("e4bf"),T=a("2f62"),E={components:{VuePageWrapper:o["default"],VueDialog:A["a"],DataTableNoData:$["default"],ApplicationSetting:k,VueContextMenu:j["default"]},mixins:[P["a"],D["a"],B["a"]],data:function(){return{htmlTitle:"Disabled Applications | Settings | Organization | Admin",breadCrumbItems:[{text:"Organization",disabled:!1,to:{name:"admin-slug-organization-overview",params:{slug:this.$route.params.slug}}},{text:"Settings",disabled:!1,to:{name:"admin-slug-organization-settings",params:{slug:this.$route.params.slug}}},{text:"Application",disabled:!0}],loading:!1,headers:[{text:"Application Name",value:"name",width:""},{text:"Enabled For Hr Only",value:"enabled",width:""},{text:"Action",align:"center",sortable:!1,width:""}],applicationSettings:[{title:"Worklog",value:"worklog"},{title:"Payroll",value:"payroll"},{title:"Reimbursement",value:"reimbursement"},{title:"Assessment",value:"assessment"},{title:"Training",value:"training"}],deleteId:"",applicationsToDisable:[],displayForm:!1,disableApp:{organization:[]},deleteNotification:{dialog:!1,heading:"Confirm Enable",subheading:"You are about to enable this application. Confirm your action.",text:"Are you sure you want to enable this application?"}}},computed:{filteredApplications:function(){var t=this;return 0===this.applicationsToDisable.length?this.applicationSettings:this.applicationSettings.filter((function(e){return!t.applicationsToDisable.includes(e.value)}))},disableButton:function(){return this.applicationsToDisable.length===this.applicationSettings.length}},created:function(){this.loadDataTableChange()},methods:Object(r["a"])(Object(r["a"])({},Object(T["d"])({setDisableAppList:"auth/setDisableApplication",setOrgDisableApp:"organization/setOrgDisableApp"})),{},{fetchDataTable:function(){var t=this;return Object(s["a"])(regeneratorRuntime.mark((function e(){return regeneratorRuntime.wrap((function(e){while(1)switch(e.prev=e.next){case 0:t.loading=!0,t.$http.get(f.getApplicationSetting(t.getOrganizationSlug),{params:t.fullParams}).then((function(e){t.loadDataTable(e),t.applicationsToDisable=e.results.map((function(t){return t.application})),t.setOrgDisableApp(e.results.filter((function(t){return!t.enabled})).map((function(t){return t.application}))),t.setDisableAppList(t.applicationsToDisable)})).finally((function(){t.loading=!1}));case 2:case"end":return e.stop()}}),e)})))()},deleteApplicationSetting:function(){var t=this;return Object(s["a"])(regeneratorRuntime.mark((function e(){return regeneratorRuntime.wrap((function(e){while(1)switch(e.prev=e.next){case 0:t.$http.delete(f.deleteApplicationSetting(t.getOrganizationSlug,t.deleteId)).then((function(){t.deleteNotification.dialog=!1,t.notifyUser("Successfully deleted Application Setting","green"),t.loadDataTableChange()}));case 1:case"end":return e.stop()}}),e)})))()},updateForHr:function(t){var e=this;this.$http.patch(f.updateApplicationSetting(this.getOrganizationSlug,t.id),{enabled:t.enabled}).then((function(){e.notifyUser("Successfully ".concat(t.enabled?"enabled":"disabled"," ").concat(t.application," for HR"),"green"),e.loadDataTableChange()})).catch((function(t){e.pushErrors(t)}))}})},V=E,F=a("8336"),I=a("b0af"),R=a("8fea"),L=a("169a"),N=a("b73d"),z=Object(b["a"])(V,i,n,!1,null,null,null);e["default"]=z.exports;y()(z,{VBtn:F["a"],VCard:I["a"],VDataTable:R["a"],VDialog:L["a"],VDivider:S["a"],VSwitch:N["a"]})},e4bf:function(t,e,a){"use strict";a.r(e);var i=function(){var t=this,e=t.$createElement,a=t._self._c||e;return a("div",[t.contextList.filter((function(t){return!t.hide})).length<3&&!t.hideIcons||t.showIcons?a("div",t._l(t.contextList,(function(e,i){return a("span",{key:i},[e.hide?t._e():a("v-tooltip",{attrs:{disabled:t.$vuetify.breakpoint.xs,top:""},scopedSlots:t._u([{key:"activator",fn:function(n){var s=n.on;return[a("v-btn",t._g({staticClass:"mx-0",attrs:{text:"",width:t.small?"18":"22",depressed:"",icon:""}},s),[a("v-icon",{attrs:{disabled:e.disabled,color:e.color,"data-cy":t.dataCyVariable+"btn-dropdown-menu-item-"+(i+1),dark:!e.disabled,small:t.small,size:"20",dense:""},domProps:{textContent:t._s(e.icon)},on:{click:function(e){return t.$emit("click"+i)}}})],1)]}}],null,!0)},[a("span",{domProps:{textContent:t._s(e.disabled&&e.disable_message||e.name)}})])],1)})),0):a("v-menu",{attrs:{"offset-y":"",left:"",transition:"slide-y-transition"},scopedSlots:t._u([{key:"activator",fn:function(e){var i=e.on;return[a("v-btn",t._g({attrs:{small:"",text:"",icon:""}},i),[a("v-icon",{attrs:{"data-cy":"btn-dropdown-menu"},domProps:{textContent:t._s("mdi-dots-vertical")}})],1)]}}])},t._l(t.contextList,(function(e,i){return a("v-list",{key:i,staticClass:"pa-0",attrs:{dense:""}},[e.hide?t._e():a("div",[e.disabled?a("v-list-item",{attrs:{"data-cy":"btn-dropdown-menu-item"}},[a("v-tooltip",{attrs:{top:""},scopedSlots:t._u([{key:"activator",fn:function(i){var n=i.on;return[a("v-list-item-title",t._g({},n),[a("v-icon",{attrs:{disabled:"",small:"",color:e.color},domProps:{textContent:t._s(e.icon)}}),a("span",{staticClass:"ml-1 grey--text",domProps:{textContent:t._s(e.name)}})],1)]}}],null,!0)},[a("span",{domProps:{textContent:t._s(e.disabled&&e.disable_message||e.name)}})])],1):a("v-list-item",{attrs:{"data-cy":"btn-dropdown-menu-item"},on:{click:function(e){return t.$emit("click"+i)}}},[a("v-list-item-title",[a("v-icon",{attrs:{color:e.color,small:"",dense:""},domProps:{textContent:t._s(e.icon)}}),a("span",{staticClass:"ml-1",class:e.text_color,domProps:{textContent:t._s(e.name)}})],1)],1)],1)])})),1)],1)},n=[],s={name:"VueContextMenu",props:{contextList:{type:Array,default:function(){return[]}},dataCyVariable:{type:String,default:""},showIcons:{type:Boolean,default:!1},hideIcons:{type:Boolean,default:!1},small:{type:Boolean,default:!1}}},r=s,o=a("2877"),l=a("6544"),c=a.n(l),d=a("8336"),u=a("132d"),p=a("8860"),h=a("da13"),f=a("5d23"),g=a("e449"),m=a("3a2f"),b=Object(o["a"])(r,i,n,!1,null,"71ee785c",null);e["default"]=b.exports;c()(b,{VBtn:d["a"],VIcon:u["a"],VList:p["a"],VListItem:h["a"],VListItemTitle:f["c"],VMenu:g["a"],VTooltip:m["a"]})}}]);