(window["webpackJsonp"]=window["webpackJsonp"]||[]).push([["pages/admin/_slug/hris/employees/employee-documents","chunk-26c51c79","chunk-31f8a6e6","chunk-2d0c8a11","chunk-2d2259e9"],{"0549":function(t,e,a){"use strict";a.r(e);var i=function(){var t=this,e=t.$createElement,a=t._self._c||e;return a("div",[a("v-row",{staticClass:"mb-3",attrs:{"no-gutters":""}},[t.breadCrumbs?a("v-col",{attrs:{cols:"12"}},[a("v-card",{attrs:{flat:""}},[a("v-breadcrumbs",{staticClass:"text-body-1 pa-2",class:{"text-caption pa-1":t.$vuetify.breakpoint.xs},attrs:{items:t.breadCrumbs},scopedSlots:t._u([{key:"item",fn:function(e){return[a("span",{class:e.item.disabled?"grey--text":"baseColor--text text--accent-2 pointer",domProps:{textContent:t._s(e.item.text)},on:{click:function(a){return t.$router.push(e.item.to)}}})]}}],null,!1,1670153796)},[a("v-icon",{attrs:{slot:"divider"},slot:"divider"},[t._v("mdi-chevron-right")])],1)],1)],1):t._e()],1),a("v-row",{attrs:{"no-gutters":""}},[a("v-col",{attrs:{cols:"12"}},[t._t("default")],2)],1)],1)},n=[],r=a("5530"),o=(a("ac1f"),a("1276"),a("b0c0"),a("2f62")),s={props:{title:{type:String,required:!0},breadCrumbs:{type:Array,default:function(){return[]}}},computed:Object(r["a"])({},Object(o["c"])({getOrganizationName:"organization/getOrganizationName",getSupervisorSwitchedOrganization:"supervisor/getSwitchedOrganization"})),mounted:function(){document.title="".concat(this.title," | RealHRsoft");var t=this.$route.params.slug?"admin-slug-dashboard":"root",e=this.$route.name.split("-"),a=this.getOrganizationName;this.getSupervisorSwitchedOrganization&&"user"===e[0]&&"supervisor"===e[1]&&(a=this.getSupervisorSwitchedOrganization.name),this.breadCrumbs.unshift({text:a,disabled:!1,to:{name:t,params:{slug:this.$route.params.slug}}})}},l=s,c=a("2877"),u=a("6544"),d=a.n(u),m=a("2bc5"),p=a("b0af"),f=a("62ad"),h=a("132d"),g=a("0fd9b"),v=Object(c["a"])(l,i,n,!1,null,null,null);e["default"]=v.exports;d()(v,{VBreadcrumbs:m["a"],VCard:p["a"],VCol:f["a"],VIcon:h["a"],VRow:g["a"]})},1229:function(t,e,a){"use strict";a("99af");e["a"]={getDivision:function(t){return"/org/".concat(t,"/division/")},postDivision:function(t){return"/org/".concat(t,"/division/")},getDivisionDetails:function(t,e){return"/org/".concat(t,"/division/").concat(e,"/")},putDivision:function(t,e){return"/org/".concat(t,"/division/").concat(e,"/")},deleteDivision:function(t,e){return"/org/".concat(t,"/division/").concat(e,"/")},importDivision:function(t){return"/org/".concat(t,"/division/import/")},downloadSampleDivision:function(t){return"/org/".concat(t,"/division/import/sample")}}},"17cc":function(t,e,a){"use strict";var i=a("b85c"),n=a("1da1"),r=a("5530");a("96cf"),a("ac1f"),a("841c"),a("d3b7"),a("3ca3"),a("ddb0"),a("2b3d"),a("b64b");e["a"]={data:function(){return{fetchedResults:[],response:{},extra_data:"",appliedFilters:{},footerProps:{itemsPerPageOptions:[10,20,30,40,50,100]},pagination:{sortBy:["modified_at"],descending:!1,totalItems:0,page:1,rowsPerPage:10,pageCount:0},triggerDataTable:!0,fullParams:""}},created:function(){this.getParams(this.DataTableFilter)},methods:{getParams:function(t){var e=Object(r["a"])(Object(r["a"])({},t),{},{offset:(this.pagination.page-1)*this.pagination.rowsPerPage,limit:this.pagination.rowsPerPage,ordering:this.pagination.descending?this.pagination.sortBy:"-"+this.pagination.sortBy});this.fullParams=this.convertToURLSearchParams(e)},loadDataTable:function(t){this.response=t,this.fetchedResults=t.results,this.pagination.totalItems=t.count,this.extra_data=t.extra_data,this.triggerDataTable=!0},fetchData:function(t){var e=this;return Object(n["a"])(regeneratorRuntime.mark((function a(){var i,n;return regeneratorRuntime.wrap((function(a){while(1)switch(a.prev=a.next){case 0:return console.warn("DatatableMixin: fetchData has been deprecated. Please use the function in page itself."),i=Object(r["a"])(Object(r["a"])(Object(r["a"])({},t),e.appliedFilters),{},{search:e.search,offset:(e.pagination.page-1)*e.pagination.rowsPerPage,limit:e.pagination.rowsPerPage,ordering:e.pagination.descending?e.pagination.sortBy:"-"+e.pagination.sortBy}),n=e.convertToURLSearchParams(i),e.loading=!0,a.next=6,e.$http.get(e.endpoint,{params:n}).then((function(t){e.response=t,e.fetchedResults=t.results,e.pagination.totalItems=t.count})).finally((function(){e.loading=!1}));case 6:case"end":return a.stop()}}),a)})))()},applyFilters:function(t){this.appliedFilters=t,this.fetchData(t)},convertToURLSearchParams:function(t){for(var e=new URLSearchParams,a=0,n=Object.keys(t);a<n.length;a++){var r=n[a],o=t[r];if(void 0===o&&(o=""),Array.isArray(o)){var s,l=Object(i["a"])(o);try{for(l.s();!(s=l.n()).done;){var c=s.value;e.append(r,c)}}catch(u){l.e(u)}finally{l.f()}}else e.append(r,o)}return e},loadDataTableChange:function(){var t=this;this.triggerDataTable&&(this.getParams(this.DataTableFilter),this.$nextTick((function(){t.fetchDataTable()})))}},watch:{DataTableFilter:function(t){this.fetchedResults=[],this.getParams(t),this.fetchDataTable(),this.pagination.page=1},"pagination.sortBy":function(){this.fetchedResults=[],this.loadDataTableChange()},"pagination.descending":function(){this.fetchedResults=[],this.loadDataTableChange()},"pagination.page":function(){this.fetchedResults=[],this.loadDataTableChange()},"pagination.rowsPerPage":function(){this.fetchedResults=[],this.loadDataTableChange()}}}},"1f09":function(t,e,a){},"2bc5":function(t,e,a){"use strict";var i=a("5530"),n=(a("a15b"),a("abd3"),a("ade3")),r=a("1c87"),o=a("58df"),s=Object(o["a"])(r["a"]).extend({name:"v-breadcrumbs-item",props:{activeClass:{type:String,default:"v-breadcrumbs__item--disabled"},ripple:{type:[Boolean,Object],default:!1}},computed:{classes:function(){return Object(n["a"])({"v-breadcrumbs__item":!0},this.activeClass,this.disabled)}},render:function(t){var e=this.generateRouteLink(),a=e.tag,n=e.data;return t("li",[t(a,Object(i["a"])(Object(i["a"])({},n),{},{attrs:Object(i["a"])(Object(i["a"])({},n.attrs),{},{"aria-current":this.isActive&&this.isLink?"page":void 0})}),this.$slots.default)])}}),l=a("80d2"),c=Object(l["i"])("v-breadcrumbs__divider","li"),u=a("7560");e["a"]=Object(o["a"])(u["a"]).extend({name:"v-breadcrumbs",props:{divider:{type:String,default:"/"},items:{type:Array,default:function(){return[]}},large:Boolean},computed:{classes:function(){return Object(i["a"])({"v-breadcrumbs--large":this.large},this.themeClasses)}},methods:{genDivider:function(){return this.$createElement(c,this.$slots.divider?this.$slots.divider:this.divider)},genItems:function(){for(var t=[],e=!!this.$scopedSlots.item,a=[],i=0;i<this.items.length;i++){var n=this.items[i];a.push(n.text),e?t.push(this.$scopedSlots.item({item:n})):t.push(this.$createElement(s,{key:a.join("."),props:n},[n.text])),i<this.items.length-1&&t.push(this.genDivider())}return t}},render:function(t){var e=this.$slots.default||this.genItems();return t("ul",{staticClass:"v-breadcrumbs",class:this.classes},e)}})},"2c2a":function(t,e,a){"use strict";a("99af");e["a"]={getEmploymentLevel:function(t){return"/org/".concat(t,"/employment/level/")},postEmploymentLevel:function(t){return"/org/".concat(t,"/employment/level/")},getEmploymentLevelDetail:function(t,e){return"/org/".concat(t,"/employment/level/").concat(e,"/")},updateEmploymentLevel:function(t,e){return"/org/".concat(t,"/employment/level/").concat(e,"/")},deleteEmploymentLevel:function(t,e){return"/org/".concat(t,"/employment/level/").concat(e,"/")},importEmploymentLevel:function(t){return"/org/".concat(t,"/employment/level/import/")},downloadSampleEmploymentLevel:function(t){return"/org/".concat(t,"/employment/level/import/sample")}}},3129:function(t,e,a){"use strict";var i=a("3835"),n=a("5530"),r=(a("ac1f"),a("1276"),a("d81d"),a("a630"),a("3ca3"),a("5319"),a("1f09"),a("c995")),o=a("24b2"),s=a("7560"),l=a("58df"),c=a("80d2");e["a"]=Object(l["a"])(r["a"],o["a"],s["a"]).extend({name:"VSkeletonLoader",props:{boilerplate:Boolean,loading:Boolean,tile:Boolean,transition:String,type:String,types:{type:Object,default:function(){return{}}}},computed:{attrs:function(){return this.isLoading?this.boilerplate?{}:Object(n["a"])({"aria-busy":!0,"aria-live":"polite",role:"alert"},this.$attrs):this.$attrs},classes:function(){return Object(n["a"])(Object(n["a"])({"v-skeleton-loader--boilerplate":this.boilerplate,"v-skeleton-loader--is-loading":this.isLoading,"v-skeleton-loader--tile":this.tile},this.themeClasses),this.elevationClasses)},isLoading:function(){return!("default"in this.$scopedSlots)||this.loading},rootTypes:function(){return Object(n["a"])({actions:"button@2",article:"heading, paragraph",avatar:"avatar",button:"button",card:"image, card-heading","card-avatar":"image, list-item-avatar","card-heading":"heading",chip:"chip","date-picker":"list-item, card-heading, divider, date-picker-options, date-picker-days, actions","date-picker-options":"text, avatar@2","date-picker-days":"avatar@28",heading:"heading",image:"image","list-item":"text","list-item-avatar":"avatar, text","list-item-two-line":"sentences","list-item-avatar-two-line":"avatar, sentences","list-item-three-line":"paragraph","list-item-avatar-three-line":"avatar, paragraph",paragraph:"text@3",sentences:"text@2",table:"table-heading, table-thead, table-tbody, table-tfoot","table-heading":"heading, text","table-thead":"heading@6","table-tbody":"table-row-divider@6","table-row-divider":"table-row, divider","table-row":"table-cell@6","table-cell":"text","table-tfoot":"text@2, avatar@2",text:"text"},this.types)}},methods:{genBone:function(t,e){return this.$createElement("div",{staticClass:"v-skeleton-loader__".concat(t," v-skeleton-loader__bone")},e)},genBones:function(t){var e=this,a=t.split("@"),n=Object(i["a"])(a,2),r=n[0],o=n[1],s=function(){return e.genStructure(r)};return Array.from({length:o}).map(s)},genStructure:function(t){var e=[];t=t||this.type||"";var a=this.rootTypes[t]||"";if(t===a);else{if(t.indexOf(",")>-1)return this.mapBones(t);if(t.indexOf("@")>-1)return this.genBones(t);a.indexOf(",")>-1?e=this.mapBones(a):a.indexOf("@")>-1?e=this.genBones(a):a&&e.push(this.genStructure(a))}return[this.genBone(t,e)]},genSkeleton:function(){var t=[];return this.isLoading?t.push(this.genStructure()):t.push(Object(c["s"])(this)),this.transition?this.$createElement("transition",{props:{name:this.transition},on:{afterEnter:this.resetStyles,beforeEnter:this.onBeforeEnter,beforeLeave:this.onBeforeLeave,leaveCancelled:this.resetStyles}},t):t},mapBones:function(t){return t.replace(/\s/g,"").split(",").map(this.genStructure)},onBeforeEnter:function(t){this.resetStyles(t),this.isLoading&&(t._initialStyle={display:t.style.display,transition:t.style.transition},t.style.setProperty("transition","none","important"))},onBeforeLeave:function(t){t.style.setProperty("display","none","important")},resetStyles:function(t){t._initialStyle&&(t.style.display=t._initialStyle.display||"",t.style.transition=t._initialStyle.transition,delete t._initialStyle)}},render:function(t){return t("div",{staticClass:"v-skeleton-loader",attrs:this.attrs,on:this.$listeners,class:this.classes,style:this.isLoading?this.measurableStyles:void 0},[this.genSkeleton()])}})},5660:function(t,e,a){"use strict";a.r(e);var i=function(){var t=this,e=t.$createElement,a=t._self._c||e;return a("div",{staticClass:"d-flex space-between"},[a("v-autocomplete",{key:t.componentKey,ref:"autoComplete",class:t.appliedClass,attrs:{id:t.id,items:t.itemsSorted,"search-input":t.search,loading:t.isLoading,multiple:t.multiple,label:t.label,error:t.errorMessages.length>0,"error-messages":t.errorMessages,disabled:t.disabled,readonly:t.readonly,"data-cy":"autocomplete-"+t.dataCyVariable,"prepend-inner-icon":t.prependInnerIcon,clearable:t.clearable&&!t.readonly,"hide-details":t.hideDetails,"item-text":t.itemText,"item-value":t.itemValue,"small-chips":t.multiple||t.chips,"deletable-chips":t.multiple,hint:t.hint,"persistent-hint":t.persistentHint,chips:t.chips,solo:t.solo,flat:t.flat,"cache-items":t.cacheItems,placeholder:t.placeholder,dense:t.dense,"hide-selected":"","hide-no-data":""},on:{"update:searchInput":function(e){t.search=e},"update:search-input":function(e){t.search=e},focus:t.populateOnFocus,keydown:function(e){return!e.type.indexOf("key")&&t._k(e.keyCode,"enter",13,e.key,"Enter")?null:(e.preventDefault(),t.searchText())},change:t.updateState,blur:function(e){return t.$emit("blur")}},scopedSlots:t._u([{key:"selection",fn:function(e){return[t._t("selection",(function(){return[t.itemText&&e.item?a("div",[t.multiple||t.chips?a("v-chip",{attrs:{close:(t.clearable||!t.clearable&&!t.multiple)&&!t.readonly,small:""},on:{"click:close":function(a){return t.remove(e.item)}}},[e.item[t.itemText]?a("div",[e.item[t.itemText].length>40?a("v-tooltip",{attrs:{top:""},scopedSlots:t._u([{key:"activator",fn:function(i){var n=i.on;return[a("span",t._g({},n),[t._v(" "+t._s(t._f("truncate")(e.item[t.itemText],40)))])]}}],null,!0)},[a("span",[t._v(t._s(e.item[t.itemText]))])]):a("span",[t._v(t._s(e.item[t.itemText]))])],1):a("div",[a("span",[t._v(t._s(e.item))])])]):a("div",[e.item[t.itemText]?a("div",[e.item[t.itemText].length>40?a("v-tooltip",{attrs:{top:""},scopedSlots:t._u([{key:"activator",fn:function(i){var n=i.on;return[a("span",t._g({},n),[t._v(" "+t._s(t._f("truncate")(e.item[t.itemText],40)))])]}}],null,!0)},[a("span",[t._v(t._s(e.item[t.itemText]))])]):a("span",[t._v(t._s(e.item[t.itemText]))])],1):a("div",[a("span",[t._v(t._s(e.item))])])])],1):t._e()]}),{props:e})]}},{key:"item",fn:function(e){return[a("v-list-item-content",[a("v-list-item-title",[t._t("item",(function(){return[t.itemText&&e.item?a("div",[e.item[t.itemText]?a("div",[e.item[t.itemText].length>40?a("v-tooltip",{attrs:{top:""},scopedSlots:t._u([{key:"activator",fn:function(i){var n=i.on;return[a("span",t._g({},n),[t._v(" "+t._s(t._f("truncate")(e.item[t.itemText],40)))])]}}],null,!0)},[a("span",[t._v(t._s(e.item[t.itemText]))])]):a("span",[t._v(t._s(e.item[t.itemText]))])],1):a("div",[a("span",[t._v(t._s(e.item))])])]):t._e()]}),{props:e})],2)],1)]}},{key:"append-item",fn:function(){return[!t.fullyLoaded&&t.showMoreIcon?a("div",[a("v-list-item-content",{staticClass:"px-4 pointer primary--text font-weight-bold"},[a("v-list-item-title",{on:{click:function(e){return t.fetchData()}}},[t._v(" Load More Items ... ")])],1)],1):t._e()]},proxy:!0}],null,!0),model:{value:t.selectedData,callback:function(e){t.selectedData=e},expression:"selectedData"}}),t._t("default")],2)},n=[],r=a("2909"),o=a("5530"),s=a("53ca"),l=a("1da1"),c=(a("96cf"),a("a9e3"),a("ac1f"),a("841c"),a("7db0"),a("d81d"),a("159b"),a("4de4"),a("4e827"),a("2ca0"),a("d3b7"),a("c740"),a("a434"),a("3ca3"),a("ddb0"),a("2b3d"),a("caad"),a("2532"),a("63ea")),u=a.n(c),d={props:{value:{type:[Number,String,Array,Object],default:void 0},id:{type:String,default:""},dataCyVariable:{type:String,default:""},endpoint:{type:String,default:""},itemText:{type:String,required:!0},itemValue:{type:String,required:!0},params:{type:Object,required:!1,default:function(){return{}}},itemsToExclude:{type:[Array,Number],default:null},forceFetch:{type:Boolean,default:!1},staticItems:{type:Array,default:function(){return[]}},errorMessages:{type:[String,Array],default:function(){return[]}},label:{type:String,default:""},disabled:{type:Boolean,default:!1},readonly:{type:Boolean,default:!1},hint:{type:String,default:void 0},persistentHint:{type:Boolean,required:!1,default:!1},multiple:{type:Boolean,required:!1,default:!1},clearable:{type:Boolean,default:!0},hideDetails:{type:Boolean,default:!1},solo:{type:Boolean,default:!1},flat:{type:Boolean,default:!1},chips:{type:Boolean,default:!1},prependInnerIcon:{type:String,default:void 0},cacheItems:{type:Boolean,default:!1},appliedClass:{type:String,default:""},placeholder:{type:String,default:""},dense:{type:Boolean,default:!1}},data:function(){return{componentKey:0,items:[],selectedData:null,search:null,initialFetchStarted:!1,nextLimit:null,nextOffset:null,showMoreIcon:!1,fullyLoaded:!1,isLoading:!1}},computed:{itemsSorted:function(){return this.sortBySearch(this.items,this.search?this.search.toLowerCase():"")}},watch:{value:{handler:function(){var t=Object(l["a"])(regeneratorRuntime.mark((function t(e){var a,i,n,r,o=this;return regeneratorRuntime.wrap((function(t){while(1)switch(t.prev=t.next){case 0:if(!e){t.next=10;break}if(!this.forceFetch||this.initialFetchStarted){t.next=6;break}return this.initialFetchStarted=!0,t.next=5,this.fetchData();case 5:this.removeDuplicateItem();case 6:Array.isArray(e)?(n=[],"object"===Object(s["a"])(e[0])?(this.selectedData=e.map((function(t){return t[o.itemValue]})),e.forEach((function(t){var e=o.items.find((function(e){return e===t}));e||n.push(t)}))):(e.forEach((function(t){var e=o.items.find((function(e){return e[o.itemValue]===t}));e||n.push(t)})),this.selectedData=e),n.length>0&&(r=this.items).push.apply(r,n)):"object"===Object(s["a"])(e)?(this.selectedData=e[this.itemValue],a=this.items.find((function(t){return t[o.itemValue]===e})),a||this.items.push(e)):(this.selectedData=e,i=this.items.find((function(t){return t===e})),i||this.items.push(e)),this.updateData(this.selectedData),t.next=11;break;case 10:e||(this.selectedData=null);case 11:case"end":return t.stop()}}),t,this)})));function e(e){return t.apply(this,arguments)}return e}(),immediate:!0},selectedData:function(t){this.updateData(t)},params:{handler:function(t,e){u()(t,e)||(this.fullyLoaded=!1,this.initialFetchStarted=!1,this.items=[],this.componentKey+=1)},deep:!0}},methods:{sortBySearch:function(t,e){var a=this.itemText,i=t.filter((function(t){return"object"===Object(s["a"])(t)}));return i.sort((function(t,i){return t[a].toLowerCase().startsWith(e)&&i[a].toLowerCase().startsWith(e)?t[a].toLowerCase().localeCompare(i[a].toLowerCase()):t[a].toLowerCase().startsWith(e)?-1:i[a].toLowerCase().startsWith(e)?1:t[a].toLowerCase().localeCompare(i[a].toLowerCase())}))},populateOnFocus:function(){var t=this;return Object(l["a"])(regeneratorRuntime.mark((function e(){return regeneratorRuntime.wrap((function(e){while(1)switch(e.prev=e.next){case 0:if(!t.initialFetchStarted){e.next=2;break}return e.abrupt("return");case 2:return t.initialFetchStarted=!0,e.next=5,t.fetchData();case 5:t.removeDuplicateItem();case 6:case"end":return e.stop()}}),e)})))()},fetchData:function(){var t=this;return Object(l["a"])(regeneratorRuntime.mark((function e(){var a,i;return regeneratorRuntime.wrap((function(e){while(1)switch(e.prev=e.next){case 0:if(!(t.staticItems.length>0)){e.next=3;break}return t.items=t.staticItems,e.abrupt("return");case 3:return a=t.nextLimit,i=t.nextOffset,t.search&&(a=null,i=null),t.isLoading=!0,e.next=9,t.$http.get(t.endpoint,{params:Object(o["a"])(Object(o["a"])({},t.params),{},{search:t.search,limit:a,offset:i})}).then((function(e){var a;e.results||(e.results=e),e.next?(t.showMoreIcon=!0,t.extractLimitOffset(e.next)):(t.showMoreIcon=!1,t.search||(t.fullyLoaded=!0)),t.itemsToExclude&&(e.results=t.excludeRecord(e.results)),(a=t.items).push.apply(a,Object(r["a"])(e.results))})).finally((function(){t.isLoading=!1}));case 9:case"end":return e.stop()}}),e)})))()},removeDuplicateItem:function(){var t=this,e=this.items.indexOf(this.selectedData);if(e>=0){var a=this.items.findIndex((function(e){return e[t.itemValue]===t.selectedData}));a>=0&&(this.items.splice(e,1),this.componentKey+=1)}},updateData:function(t){var e=this,a=[];t instanceof Array?t.forEach((function(t){a.unshift(e.items.find((function(a){return a[e.itemValue]===t})))})):a=this.items.find((function(a){return a[e.itemValue]===t})),this.$emit("input",t),this.$emit("update:selectedFullData",a)},searchText:function(){0!==this.$refs.autoComplete.filteredItems.length||this.fullyLoaded||this.fetchData()},extractLimitOffset:function(t){var e=new URL(t);this.nextLimit=e.searchParams.get("limit"),this.nextOffset=e.searchParams.get("offset")},excludeRecord:function(t){var e=this,a=[];return"number"===typeof this.itemsToExclude?a.push(this.itemsToExclude):a=this.itemsToExclude,t.filter((function(t){if(t[e.itemValue])return!a.includes(t[e.itemValue])}))},remove:function(t){if(this.selectedData instanceof Object){var e=this.selectedData.indexOf(t[this.itemValue]);e>=0&&this.selectedData.splice(e,1)}else this.selectedData=null},updateState:function(){this.search="",this.nextLimit&&(this.showMoreIcon=!0)}}},m=d,p=a("2877"),f=a("6544"),h=a.n(f),g=a("c6a6"),v=a("cc20"),b=a("5d23"),y=a("3a2f"),x=Object(p["a"])(m,i,n,!1,null,null,null);e["default"]=x.exports;h()(x,{VAutocomplete:g["a"],VChip:v["a"],VListItemContent:b["a"],VListItemTitle:b["c"],VTooltip:y["a"]})},"7c2b":function(t,e,a){"use strict";a.r(e);var i=function(){var t=this,e=t.$createElement,a=t._self._c||e;return a("vue-page-wrapper",{attrs:{"bread-crumbs":t.breadCrumbItems,title:t.htmlTitle}},[a("v-card",[a("vue-card-title",{attrs:{title:"Employee Documents Library",subtitle:t.cardText,icon:"mdi-file-document-outline"}},[a("template",{slot:"actions"},[a("v-btn",{attrs:{icon:""},on:{click:function(e){t.showFilters=!t.showFilters}}},[a("v-icon",{attrs:{small:""},domProps:{textContent:t._s("mdi-filter-variant")}})],1)],1)],2),a("v-divider"),a("v-slide-y-transition",[t.showFilters?a("v-row",{staticClass:"px-3"},[a("v-col",{attrs:{md:"3",cols:"6"}},[a("vue-search",{attrs:{search:t.search},on:{"update:search":function(e){t.search=e}},model:{value:t.search,callback:function(e){t.search=e},expression:"search"}})],1),a("v-col",{attrs:{md:"3",cols:"6"}},[a("vue-auto-complete",{attrs:{endpoint:t.jobTitleEndpoint,label:"Search By Job Title","item-text":"title","item-value":"slug"},model:{value:t.searchFilters.job_title,callback:function(e){t.$set(t.searchFilters,"job_title",e)},expression:"searchFilters.job_title"}})],1),a("v-col",{attrs:{md:"3",cols:"6"}},[a("vue-auto-complete",{attrs:{endpoint:t.employeeLevelEndpoint,params:{is_archived:"false"},label:"Search By Employment Level","item-text":"title","item-value":"slug"},model:{value:t.searchFilters.employment_level,callback:function(e){t.$set(t.searchFilters,"employment_level",e)},expression:"searchFilters.employment_level"}})],1),a("v-col",{attrs:{md:"3",cols:"6"}},[a("vue-auto-complete",{attrs:{endpoint:t.divisionEndpoint,params:{is_archived:"false"},label:"Search By Division","item-text":"name","item-value":"slug"},model:{value:t.searchFilters.division,callback:function(e){t.$set(t.searchFilters,"division",e)},expression:"searchFilters.division"}})],1),a("v-divider")],1):t._e()],1),t.form.display?t._e():a("v-data-table",{attrs:{headers:t.headers,items:t.fetchedResults,"sort-desc":t.pagination.descending,"sort-by":t.pagination.sortBy,page:t.pagination.page,"items-per-page":t.pagination.rowsPerPage,"footer-props":t.footerProps,"server-items-length":t.pagination.totalItems,"mobile-breakpoint":0,"must-sort":""},on:{"update:sortDesc":function(e){return t.$set(t.pagination,"descending",e)},"update:sort-desc":function(e){return t.$set(t.pagination,"descending",e)},"update:sortBy":function(e){return t.$set(t.pagination,"sortBy",e)},"update:sort-by":function(e){return t.$set(t.pagination,"sortBy",e)},"update:page":function(e){return t.$set(t.pagination,"page",e)},"update:itemsPerPage":function(e){return t.$set(t.pagination,"rowsPerPage",e)},"update:items-per-page":function(e){return t.$set(t.pagination,"rowsPerPage",e)}},scopedSlots:t._u([{key:"item",fn:function(e){return[a("tr",[a("td",[a("vue-user",{attrs:{user:e.item.user}})],1),a("td",[a("a",{domProps:{textContent:t._s(e.item.title)},on:{click:function(a){return t.performAction("View Document",e.item)}}})]),a("td",[e.item.document_type?a("div",[t._v(" "+t._s(e.item.document_type.name)+" ")]):a("div",{domProps:{textContent:t._s("N/A")}})]),a("td",[a("vue-user",{attrs:{user:e.item.uploaded_by}})],1),a("td",[a("vue-context-menu",{attrs:{"context-list":[{name:"View Document",icon:"mdi-eye-outline",color:"blue",disabled:!t.verifyPermission(t.allPermissions.ORGANIZATION_DOCUMENTS_PERMISSION),disable_message:"No Permission"},{name:"Download Document",icon:"mdi-file-download-outline",color:"",disabled:!t.verifyPermission(t.allPermissions.ORGANIZATION_DOCUMENTS_PERMISSION),disable_message:"No Permission"},{name:"Delete Document",icon:"mdi-delete",color:"blue",disabled:!t.verifyPermission(t.allPermissions.ORGANIZATION_DOCUMENTS_PERMISSION),disable_message:"No Permission"}]},on:{click0:function(a){return t.performAction("View Document",e.item)},click1:function(a){return t.performAction("Download Document",e.item)},click2:function(a){return t.performAction("Delete Document",e.item)}}})],1)])]}}],null,!1,3866445701)},[a("template",{slot:"no-data"},[a("data-table-no-data",{attrs:{loading:t.loading}})],1)],2),t.form.display||t.deleteDocument?a("employee-document-form",{attrs:{"action-data":t.form.actionData,"delete-document":t.deleteDocument},on:{closeForm:t.dismissForm}}):t._e()],1),a("vue-dialog",{attrs:{notify:t.deleteNotification},on:{agree:function(e){return t.triggerForm("delete",t.form.actionData)},close:function(e){t.deleteNotification.dialog=!1}}})],1)},n=[],r=a("1da1"),o=a("5530"),s=(a("96cf"),a("ac1f"),a("841c"),a("d3b7"),a("17cc")),l=a("0549"),c=a("2f62"),u=a("5660"),d=function(){var t=this,e=t.$createElement,a=t._self._c||e;return t.deleteDocument?t._e():a("v-form",{ref:"employeeDocumentForm",on:{submit:function(e){return e.preventDefault(),t.getFormAction.apply(null,arguments)}}},[a("form-submit",{attrs:{"form-errors":t.errors.any()},on:{clearForm:t.clearForm,submit:t.getFormAction}})],1)},m=[],p=(a("99af"),a("c44a")),f=a("878b"),h={components:{FormSubmit:f["a"]},mixins:[p["a"]],props:{actionData:{type:Object,default:function(){return{title:"",document_type:"",file:"",user:void 0}}},deleteDocument:{type:Boolean,default:!1}},data:function(){return{formValues:this.actionData}},computed:Object(o["a"])({},Object(c["c"])({orgSlug:"organization/getOrganizationSlug"})),created:function(){this.deleteDocument&&this.getFormAction()},methods:{getFormAction:function(){var t=this;return Object(r["a"])(regeneratorRuntime.mark((function e(){return regeneratorRuntime.wrap((function(e){while(1)switch(e.prev=e.next){case 0:return e.abrupt("return",t.deleteDocumentItem());case 1:case"end":return e.stop()}}),e)})))()},clearForm:function(){this.errors.clear(),this.$refs.employeeDocumentForm.reset(),this.clearNonFieldErrors()},deleteDocumentItem:function(){var t=this;return Object(r["a"])(regeneratorRuntime.mark((function e(){var a;return regeneratorRuntime.wrap((function(e){while(1)switch(e.prev=e.next){case 0:return a="/hris/".concat(t.orgSlug,"/document-library/").concat(t.actionData.slug,"/"),e.next=3,t.$http.delete(a);case 3:t.notifyUser("Successfully Deleted Document","success"),t.$emit("closeForm");case 5:case"end":return e.stop()}}),e)})))()}}},g=h,v=a("2877"),b=a("6544"),y=a.n(b),x=a("4bd4"),_=Object(v["a"])(g,d,m,!1,null,null,null),D=_.exports;y()(_,{VForm:x["a"]});var S=a("02cb"),w=a("a51f"),O={getDocumentLibrary:function(t){return"/hris/".concat(t,"/document-library/")},getDocumentLibraryDetails:function(t,e){return"/hris/".concat(t,"/document-library/").concat(e)},deleteDocumentLibrary:function(t,e){return"/hris/".concat(t,"/document-library/").concat(e)}},C=a("86eb"),k=a("1229"),T=a("e4bf"),j=a("2c2a"),L={components:{VueAutoComplete:u["default"],VuePageWrapper:l["default"],EmployeeDocumentForm:D,VueUser:S["default"],DataTableNoData:w["default"],VueContextMenu:T["default"]},mixins:[s["a"]],data:function(){return{htmlTitle:"Employee Documents | Employees | HRIS | Admin",breadCrumbItems:[{text:"HRIS",disabled:!1,to:{name:"admin-slug-hris-overview",params:{slug:this.$route.params.slug}}},{text:"Employees",disabled:!1,to:{name:"admin-slug-hris-employees",params:{slug:this.$route.params.slug}}},{text:"Documents",disabled:!0}],showFilters:!1,loading:!1,headers:[{text:"Name",align:"left",sortable:!0,value:"full_name"},{text:"Document Name",align:"left",width:"",sortable:!0,value:"title"},{text:"Document Type",align:"left",sortable:!0,value:"document_type"},{text:"Created By",align:"left",sortable:!0,value:"uploaded_by"},{text:"Action",align:"",sortable:!1}],rowsPerPageItems:[10,20,30,40,50],deleteDocument:!1,search:"",cardText:"List of employee Documents",searchFilters:{job_title:"",employment_level:"",division:""},deleteNotification:{dialog:!1,heading:"Confirm Delete",text:"Are you sure you want to delete this document?"},form:{display:!1,actionData:void 0}}},computed:Object(o["a"])(Object(o["a"])({},Object(c["c"])({orgSlug:"organization/getOrganizationSlug"})),{},{DataTableFilter:function(){return{search:this.search,job_title:this.searchFilters.job_title||"",employee_level:this.searchFilters.employment_level||"",division:this.searchFilters.division||""}}}),created:function(){this.initializeDynamicUrls(),this.loadDataTableChange()},methods:{fetchDataTable:function(){var t=this;return Object(r["a"])(regeneratorRuntime.mark((function e(){return regeneratorRuntime.wrap((function(e){while(1)switch(e.prev=e.next){case 0:t.loading=!0,t.$http.get(O.getDocumentLibrary(t.orgSlug),{params:t.fullParams}).then((function(e){t.loadDataTable(e)})).finally((function(){t.loading=!1}));case 2:case"end":return e.stop()}}),e)})))()},triggerForm:function(t,e){var a={create:"Create Document",delete:"Delete Document"};this.cardText=a[t],this.form.display=!0,this.form.actionData=e||void 0,this.deleteDocument="delete"===t},performAction:function(t,e){"View Document"===t||"Download Document"===t?window.open(e.file,"_blank"):(this.form.actionData=e,this.deleteNotification.dialog=!0)},initializeDynamicUrls:function(){var t=this.$route.params.slug;this.jobTitleEndpoint=C["a"].getJobTitle(t),this.divisionEndpoint=k["a"].getDivision(t),this.employeeLevelEndpoint=j["a"].getEmploymentLevel(t)},dismissForm:function(){this.fetchDataTable(),this.form.actionData=void 0,this.deleteDocument=!1,this.deleteNotification.dialog=!1,this.form.display=!1,this.cardText="List of employee Documents"}}},P=L,I=a("8336"),B=a("b0af"),V=a("62ad"),F=a("8fea"),$=a("ce7e"),E=a("132d"),R=a("0fd9b"),A=a("0789"),N=Object(v["a"])(P,i,n,!1,null,null,null);e["default"]=N.exports;y()(N,{VBtn:I["a"],VCard:B["a"],VCol:V["a"],VDataTable:F["a"],VDivider:$["a"],VIcon:E["a"],VRow:R["a"],VSlideYTransition:A["g"]})},"86eb":function(t,e,a){"use strict";a("99af");e["a"]={getJobTitle:function(t){return"/org/".concat(t,"/employment/job-title/")},postJobTitle:function(t){return"/org/".concat(t,"/employment/job-title/")},getJobTitleDetail:function(t,e){return"/org/".concat(t,"/employment/job-title/").concat(e,"/")},updateJobTitle:function(t,e){return"/org/".concat(t,"/employment/job-title/").concat(e,"/")},deleteJobTitle:function(t,e){return"/org/".concat(t,"/employment/job-title/").concat(e,"/")},importJobTitle:function(t){return"/org/".concat(t,"/employment/job-title/import/")},downloadSampleJobTitle:function(t){return"/org/".concat(t,"/employment/job-title/import/sample")}}},"878b":function(t,e,a){"use strict";var i=function(){var t=this,e=t.$createElement,a=t._self._c||e;return a("div",[a("v-card-actions",[a("v-spacer"),t.hideClear?t._e():a("v-btn",{attrs:{text:"",small:""},domProps:{textContent:t._s("Clear")},on:{click:function(e){return t.$emit("clearForm")}}}),a("v-btn",{attrs:{disabled:t.formErrors||t.disabled,color:t.deleteInstance?"red":"primary",depressed:"",small:"",loading:t.loading,type:"submit"}},[a("v-icon",{staticClass:"mr-1",attrs:{size:"14"}},[t._v(" mdi-content-save-outline ")]),t._v(" "+t._s(t.deleteInstance?"Delete":"Save")+" ")],1)],1)],1)},n=[],r={props:{hideClear:{type:Boolean,default:!1},formErrors:{type:Boolean,required:!0},disabled:{type:Boolean,default:!1},deleteInstance:{type:Boolean,required:!1,default:!1},loading:{type:Boolean,default:!1}}},o=r,s=a("2877"),l=a("6544"),c=a.n(l),u=a("8336"),d=a("99d9"),m=a("132d"),p=a("2fa4"),f=Object(s["a"])(o,i,n,!1,null,null,null);e["a"]=f.exports;c()(f,{VBtn:u["a"],VCardActions:d["a"],VIcon:m["a"],VSpacer:p["a"]})},a51f:function(t,e,a){"use strict";a.r(e);var i=function(){var t=this,e=t.$createElement,a=t._self._c||e;return a("div",[t.search.length>0?a("span",[t._v(' Your search for "'+t._s(t.search)+'" found no results. ')]):t.loading?a("v-skeleton-loader",{attrs:{type:"table",height:t.skeletonLoaderHeight}}):a("no-data-found",{attrs:{text:t.text,height:t.height}},[t._t("default")],2)],1)},n=[],r=(a("a9e3"),a("e585")),o={components:{NoDataFound:r["default"]},props:{search:{type:String,default:""},loading:{type:Boolean,required:!0},text:{type:String,default:"No data available at the moment"},height:{type:[String,Number],default:200},skeletonLoaderHeight:{type:[String,Number],default:void 0}}},s=o,l=a("2877"),c=a("6544"),u=a.n(c),d=a("3129"),m=Object(l["a"])(s,i,n,!1,null,null,null);e["default"]=m.exports;u()(m,{VSkeletonLoader:d["a"]})},abd3:function(t,e,a){},e4bf:function(t,e,a){"use strict";a.r(e);var i=function(){var t=this,e=t.$createElement,a=t._self._c||e;return a("div",[t.contextList.filter((function(t){return!t.hide})).length<3&&!t.hideIcons||t.showIcons?a("div",t._l(t.contextList,(function(e,i){return a("span",{key:i},[e.hide?t._e():a("v-tooltip",{attrs:{disabled:t.$vuetify.breakpoint.xs,top:""},scopedSlots:t._u([{key:"activator",fn:function(n){var r=n.on;return[a("v-btn",t._g({staticClass:"mx-0",attrs:{text:"",width:t.small?"18":"22",depressed:"",icon:""}},r),[a("v-icon",{attrs:{disabled:e.disabled,color:e.color,"data-cy":t.dataCyVariable+"btn-dropdown-menu-item-"+(i+1),dark:!e.disabled,small:t.small,size:"20",dense:""},domProps:{textContent:t._s(e.icon)},on:{click:function(e){return t.$emit("click"+i)}}})],1)]}}],null,!0)},[a("span",{domProps:{textContent:t._s(e.disabled&&e.disable_message||e.name)}})])],1)})),0):a("v-menu",{attrs:{"offset-y":"",left:"",transition:"slide-y-transition"},scopedSlots:t._u([{key:"activator",fn:function(e){var i=e.on;return[a("v-btn",t._g({attrs:{small:"",text:"",icon:""}},i),[a("v-icon",{attrs:{"data-cy":"btn-dropdown-menu"},domProps:{textContent:t._s("mdi-dots-vertical")}})],1)]}}])},t._l(t.contextList,(function(e,i){return a("v-list",{key:i,staticClass:"pa-0",attrs:{dense:""}},[e.hide?t._e():a("div",[e.disabled?a("v-list-item",{attrs:{"data-cy":"btn-dropdown-menu-item"}},[a("v-tooltip",{attrs:{top:""},scopedSlots:t._u([{key:"activator",fn:function(i){var n=i.on;return[a("v-list-item-title",t._g({},n),[a("v-icon",{attrs:{disabled:"",small:"",color:e.color},domProps:{textContent:t._s(e.icon)}}),a("span",{staticClass:"ml-1 grey--text",domProps:{textContent:t._s(e.name)}})],1)]}}],null,!0)},[a("span",{domProps:{textContent:t._s(e.disabled&&e.disable_message||e.name)}})])],1):a("v-list-item",{attrs:{"data-cy":"btn-dropdown-menu-item"},on:{click:function(e){return t.$emit("click"+i)}}},[a("v-list-item-title",[a("v-icon",{attrs:{color:e.color,small:"",dense:""},domProps:{textContent:t._s(e.icon)}}),a("span",{staticClass:"ml-1",class:e.text_color,domProps:{textContent:t._s(e.name)}})],1)],1)],1)])})),1)],1)},n=[],r={name:"VueContextMenu",props:{contextList:{type:Array,default:function(){return[]}},dataCyVariable:{type:String,default:""},showIcons:{type:Boolean,default:!1},hideIcons:{type:Boolean,default:!1},small:{type:Boolean,default:!1}}},o=r,s=a("2877"),l=a("6544"),c=a.n(l),u=a("8336"),d=a("132d"),m=a("8860"),p=a("da13"),f=a("5d23"),h=a("e449"),g=a("3a2f"),v=Object(s["a"])(o,i,n,!1,null,"71ee785c",null);e["default"]=v.exports;c()(v,{VBtn:u["a"],VIcon:d["a"],VList:m["a"],VListItem:p["a"],VListItemTitle:f["c"],VMenu:h["a"],VTooltip:g["a"]})}}]);