(window["webpackJsonp"]=window["webpackJsonp"]||[]).push([["pages/admin/_slug/dignity/settings/_id/formDesign","chunk-26c51c79","chunk-31f8a6e6","chunk-2d0c8a11"],{"0393":function(e,t,n){"use strict";var a=n("5530"),i=(n("0481"),n("210b"),n("604c")),s=n("d9bd");t["a"]=i["a"].extend({name:"v-expansion-panels",provide:function(){return{expansionPanels:this}},props:{accordion:Boolean,disabled:Boolean,flat:Boolean,hover:Boolean,focusable:Boolean,inset:Boolean,popout:Boolean,readonly:Boolean,tile:Boolean},computed:{classes:function(){return Object(a["a"])(Object(a["a"])({},i["a"].options.computed.classes.call(this)),{},{"v-expansion-panels":!0,"v-expansion-panels--accordion":this.accordion,"v-expansion-panels--flat":this.flat,"v-expansion-panels--hover":this.hover,"v-expansion-panels--focusable":this.focusable,"v-expansion-panels--inset":this.inset,"v-expansion-panels--popout":this.popout,"v-expansion-panels--tile":this.tile})}},created:function(){this.$attrs.hasOwnProperty("expand")&&Object(s["a"])("expand","multiple",this),Array.isArray(this.value)&&this.value.length>0&&"boolean"===typeof this.value[0]&&Object(s["a"])(':value="[true, false, true]"',':value="[0, 2]"',this)},methods:{updateItem:function(e,t){var n=this.getValue(e,t),a=this.getValue(e,t+1);e.isActive=this.toggleMethod(n),e.nextIsActive=this.toggleMethod(a)}}})},"0549":function(e,t,n){"use strict";n.r(t);var a=function(){var e=this,t=e.$createElement,n=e._self._c||t;return n("div",[n("v-row",{staticClass:"mb-3",attrs:{"no-gutters":""}},[e.breadCrumbs?n("v-col",{attrs:{cols:"12"}},[n("v-card",{attrs:{flat:""}},[n("v-breadcrumbs",{staticClass:"text-body-1 pa-2",class:{"text-caption pa-1":e.$vuetify.breakpoint.xs},attrs:{items:e.breadCrumbs},scopedSlots:e._u([{key:"item",fn:function(t){return[n("span",{class:t.item.disabled?"grey--text":"baseColor--text text--accent-2 pointer",domProps:{textContent:e._s(t.item.text)},on:{click:function(n){return e.$router.push(t.item.to)}}})]}}],null,!1,1670153796)},[n("v-icon",{attrs:{slot:"divider"},slot:"divider"},[e._v("mdi-chevron-right")])],1)],1)],1):e._e()],1),n("v-row",{attrs:{"no-gutters":""}},[n("v-col",{attrs:{cols:"12"}},[e._t("default")],2)],1)],1)},i=[],s=n("5530"),r=(n("ac1f"),n("1276"),n("b0c0"),n("2f62")),o={props:{title:{type:String,required:!0},breadCrumbs:{type:Array,default:function(){return[]}}},computed:Object(s["a"])({},Object(r["c"])({getOrganizationName:"organization/getOrganizationName",getSupervisorSwitchedOrganization:"supervisor/getSwitchedOrganization"})),mounted:function(){document.title="".concat(this.title," | RealHRsoft");var e=this.$route.params.slug?"admin-slug-dashboard":"root",t=this.$route.name.split("-"),n=this.getOrganizationName;this.getSupervisorSwitchedOrganization&&"user"===t[0]&&"supervisor"===t[1]&&(n=this.getSupervisorSwitchedOrganization.name),this.breadCrumbs.unshift({text:n,disabled:!1,to:{name:e,params:{slug:this.$route.params.slug}}})}},l=o,c=n("2877"),u=n("6544"),d=n.n(u),p=n("2bc5"),h=n("b0af"),m=n("62ad"),f=n("132d"),v=n("0fd9b"),g=Object(c["a"])(l,a,i,!1,null,null,null);t["default"]=g.exports;d()(g,{VBreadcrumbs:p["a"],VCard:h["a"],VCol:m["a"],VIcon:f["a"],VRow:v["a"]})},1229:function(e,t,n){"use strict";n("99af");t["a"]={getDivision:function(e){return"/org/".concat(e,"/division/")},postDivision:function(e){return"/org/".concat(e,"/division/")},getDivisionDetails:function(e,t){return"/org/".concat(e,"/division/").concat(t,"/")},putDivision:function(e,t){return"/org/".concat(e,"/division/").concat(t,"/")},deleteDivision:function(e,t){return"/org/".concat(e,"/division/").concat(t,"/")},importDivision:function(e){return"/org/".concat(e,"/division/import/")},downloadSampleDivision:function(e){return"/org/".concat(e,"/division/import/sample")}}},"1f09":function(e,t,n){},"210b":function(e,t,n){},"2bc5":function(e,t,n){"use strict";var a=n("5530"),i=(n("a15b"),n("abd3"),n("ade3")),s=n("1c87"),r=n("58df"),o=Object(r["a"])(s["a"]).extend({name:"v-breadcrumbs-item",props:{activeClass:{type:String,default:"v-breadcrumbs__item--disabled"},ripple:{type:[Boolean,Object],default:!1}},computed:{classes:function(){return Object(i["a"])({"v-breadcrumbs__item":!0},this.activeClass,this.disabled)}},render:function(e){var t=this.generateRouteLink(),n=t.tag,i=t.data;return e("li",[e(n,Object(a["a"])(Object(a["a"])({},i),{},{attrs:Object(a["a"])(Object(a["a"])({},i.attrs),{},{"aria-current":this.isActive&&this.isLink?"page":void 0})}),this.$slots.default)])}}),l=n("80d2"),c=Object(l["i"])("v-breadcrumbs__divider","li"),u=n("7560");t["a"]=Object(r["a"])(u["a"]).extend({name:"v-breadcrumbs",props:{divider:{type:String,default:"/"},items:{type:Array,default:function(){return[]}},large:Boolean},computed:{classes:function(){return Object(a["a"])({"v-breadcrumbs--large":this.large},this.themeClasses)}},methods:{genDivider:function(){return this.$createElement(c,this.$slots.divider?this.$slots.divider:this.divider)},genItems:function(){for(var e=[],t=!!this.$scopedSlots.item,n=[],a=0;a<this.items.length;a++){var i=this.items[a];n.push(i.text),t?e.push(this.$scopedSlots.item({item:i})):e.push(this.$createElement(o,{key:n.join("."),props:i},[i.text])),a<this.items.length-1&&e.push(this.genDivider())}return e}},render:function(e){var t=this.$slots.default||this.genItems();return e("ul",{staticClass:"v-breadcrumbs",class:this.classes},t)}})},"2c2a":function(e,t,n){"use strict";n("99af");t["a"]={getEmploymentLevel:function(e){return"/org/".concat(e,"/employment/level/")},postEmploymentLevel:function(e){return"/org/".concat(e,"/employment/level/")},getEmploymentLevelDetail:function(e,t){return"/org/".concat(e,"/employment/level/").concat(t,"/")},updateEmploymentLevel:function(e,t){return"/org/".concat(e,"/employment/level/").concat(t,"/")},deleteEmploymentLevel:function(e,t){return"/org/".concat(e,"/employment/level/").concat(t,"/")},importEmploymentLevel:function(e){return"/org/".concat(e,"/employment/level/import/")},downloadSampleEmploymentLevel:function(e){return"/org/".concat(e,"/employment/level/import/sample")}}},3129:function(e,t,n){"use strict";var a=n("3835"),i=n("5530"),s=(n("ac1f"),n("1276"),n("d81d"),n("a630"),n("3ca3"),n("5319"),n("1f09"),n("c995")),r=n("24b2"),o=n("7560"),l=n("58df"),c=n("80d2");t["a"]=Object(l["a"])(s["a"],r["a"],o["a"]).extend({name:"VSkeletonLoader",props:{boilerplate:Boolean,loading:Boolean,tile:Boolean,transition:String,type:String,types:{type:Object,default:function(){return{}}}},computed:{attrs:function(){return this.isLoading?this.boilerplate?{}:Object(i["a"])({"aria-busy":!0,"aria-live":"polite",role:"alert"},this.$attrs):this.$attrs},classes:function(){return Object(i["a"])(Object(i["a"])({"v-skeleton-loader--boilerplate":this.boilerplate,"v-skeleton-loader--is-loading":this.isLoading,"v-skeleton-loader--tile":this.tile},this.themeClasses),this.elevationClasses)},isLoading:function(){return!("default"in this.$scopedSlots)||this.loading},rootTypes:function(){return Object(i["a"])({actions:"button@2",article:"heading, paragraph",avatar:"avatar",button:"button",card:"image, card-heading","card-avatar":"image, list-item-avatar","card-heading":"heading",chip:"chip","date-picker":"list-item, card-heading, divider, date-picker-options, date-picker-days, actions","date-picker-options":"text, avatar@2","date-picker-days":"avatar@28",heading:"heading",image:"image","list-item":"text","list-item-avatar":"avatar, text","list-item-two-line":"sentences","list-item-avatar-two-line":"avatar, sentences","list-item-three-line":"paragraph","list-item-avatar-three-line":"avatar, paragraph",paragraph:"text@3",sentences:"text@2",table:"table-heading, table-thead, table-tbody, table-tfoot","table-heading":"heading, text","table-thead":"heading@6","table-tbody":"table-row-divider@6","table-row-divider":"table-row, divider","table-row":"table-cell@6","table-cell":"text","table-tfoot":"text@2, avatar@2",text:"text"},this.types)}},methods:{genBone:function(e,t){return this.$createElement("div",{staticClass:"v-skeleton-loader__".concat(e," v-skeleton-loader__bone")},t)},genBones:function(e){var t=this,n=e.split("@"),i=Object(a["a"])(n,2),s=i[0],r=i[1],o=function(){return t.genStructure(s)};return Array.from({length:r}).map(o)},genStructure:function(e){var t=[];e=e||this.type||"";var n=this.rootTypes[e]||"";if(e===n);else{if(e.indexOf(",")>-1)return this.mapBones(e);if(e.indexOf("@")>-1)return this.genBones(e);n.indexOf(",")>-1?t=this.mapBones(n):n.indexOf("@")>-1?t=this.genBones(n):n&&t.push(this.genStructure(n))}return[this.genBone(e,t)]},genSkeleton:function(){var e=[];return this.isLoading?e.push(this.genStructure()):e.push(Object(c["s"])(this)),this.transition?this.$createElement("transition",{props:{name:this.transition},on:{afterEnter:this.resetStyles,beforeEnter:this.onBeforeEnter,beforeLeave:this.onBeforeLeave,leaveCancelled:this.resetStyles}},e):e},mapBones:function(e){return e.replace(/\s/g,"").split(",").map(this.genStructure)},onBeforeEnter:function(e){this.resetStyles(e),this.isLoading&&(e._initialStyle={display:e.style.display,transition:e.style.transition},e.style.setProperty("transition","none","important"))},onBeforeLeave:function(e){e.style.setProperty("display","none","important")},resetStyles:function(e){e._initialStyle&&(e.style.display=e._initialStyle.display||"",e.style.transition=e._initialStyle.transition,delete e._initialStyle)}},render:function(e){return e("div",{staticClass:"v-skeleton-loader",attrs:this.attrs,on:this.$listeners,class:this.classes,style:this.isLoading?this.measurableStyles:void 0},[this.genSkeleton()])}})},"49e2":function(e,t,n){"use strict";var a=n("0789"),i=n("9d65"),s=n("a9ad"),r=n("3206"),o=n("80d2"),l=n("58df"),c=Object(l["a"])(i["a"],s["a"],Object(r["a"])("expansionPanel","v-expansion-panel-content","v-expansion-panel"));t["a"]=c.extend().extend({name:"v-expansion-panel-content",computed:{isActive:function(){return this.expansionPanel.isActive}},created:function(){this.expansionPanel.registerContent(this)},beforeDestroy:function(){this.expansionPanel.unregisterContent()},render:function(e){var t=this;return e(a["a"],this.showLazyContent((function(){return[e("div",t.setBackgroundColor(t.color,{staticClass:"v-expansion-panel-content",directives:[{name:"show",value:t.isActive}]}),[e("div",{class:"v-expansion-panel-content__wrap"},Object(o["s"])(t))])]})))}})},"4f4a":function(e,t,n){"use strict";var a=n("8b61"),i=n("cfa3"),s=n("a09e"),r=n("c13e");t["a"]={mixins:[a["a"],i["a"],s["a"],r["a"]]}},5660:function(e,t,n){"use strict";n.r(t);var a=function(){var e=this,t=e.$createElement,n=e._self._c||t;return n("div",{staticClass:"d-flex space-between"},[n("v-autocomplete",{key:e.componentKey,ref:"autoComplete",class:e.appliedClass,attrs:{id:e.id,items:e.itemsSorted,"search-input":e.search,loading:e.isLoading,multiple:e.multiple,label:e.label,error:e.errorMessages.length>0,"error-messages":e.errorMessages,disabled:e.disabled,readonly:e.readonly,"data-cy":"autocomplete-"+e.dataCyVariable,"prepend-inner-icon":e.prependInnerIcon,clearable:e.clearable&&!e.readonly,"hide-details":e.hideDetails,"item-text":e.itemText,"item-value":e.itemValue,"small-chips":e.multiple||e.chips,"deletable-chips":e.multiple,hint:e.hint,"persistent-hint":e.persistentHint,chips:e.chips,solo:e.solo,flat:e.flat,"cache-items":e.cacheItems,placeholder:e.placeholder,dense:e.dense,"hide-selected":"","hide-no-data":""},on:{"update:searchInput":function(t){e.search=t},"update:search-input":function(t){e.search=t},focus:e.populateOnFocus,keydown:function(t){return!t.type.indexOf("key")&&e._k(t.keyCode,"enter",13,t.key,"Enter")?null:(t.preventDefault(),e.searchText())},change:e.updateState,blur:function(t){return e.$emit("blur")}},scopedSlots:e._u([{key:"selection",fn:function(t){return[e._t("selection",(function(){return[e.itemText&&t.item?n("div",[e.multiple||e.chips?n("v-chip",{attrs:{close:(e.clearable||!e.clearable&&!e.multiple)&&!e.readonly,small:""},on:{"click:close":function(n){return e.remove(t.item)}}},[t.item[e.itemText]?n("div",[t.item[e.itemText].length>40?n("v-tooltip",{attrs:{top:""},scopedSlots:e._u([{key:"activator",fn:function(a){var i=a.on;return[n("span",e._g({},i),[e._v(" "+e._s(e._f("truncate")(t.item[e.itemText],40)))])]}}],null,!0)},[n("span",[e._v(e._s(t.item[e.itemText]))])]):n("span",[e._v(e._s(t.item[e.itemText]))])],1):n("div",[n("span",[e._v(e._s(t.item))])])]):n("div",[t.item[e.itemText]?n("div",[t.item[e.itemText].length>40?n("v-tooltip",{attrs:{top:""},scopedSlots:e._u([{key:"activator",fn:function(a){var i=a.on;return[n("span",e._g({},i),[e._v(" "+e._s(e._f("truncate")(t.item[e.itemText],40)))])]}}],null,!0)},[n("span",[e._v(e._s(t.item[e.itemText]))])]):n("span",[e._v(e._s(t.item[e.itemText]))])],1):n("div",[n("span",[e._v(e._s(t.item))])])])],1):e._e()]}),{props:t})]}},{key:"item",fn:function(t){return[n("v-list-item-content",[n("v-list-item-title",[e._t("item",(function(){return[e.itemText&&t.item?n("div",[t.item[e.itemText]?n("div",[t.item[e.itemText].length>40?n("v-tooltip",{attrs:{top:""},scopedSlots:e._u([{key:"activator",fn:function(a){var i=a.on;return[n("span",e._g({},i),[e._v(" "+e._s(e._f("truncate")(t.item[e.itemText],40)))])]}}],null,!0)},[n("span",[e._v(e._s(t.item[e.itemText]))])]):n("span",[e._v(e._s(t.item[e.itemText]))])],1):n("div",[n("span",[e._v(e._s(t.item))])])]):e._e()]}),{props:t})],2)],1)]}},{key:"append-item",fn:function(){return[!e.fullyLoaded&&e.showMoreIcon?n("div",[n("v-list-item-content",{staticClass:"px-4 pointer primary--text font-weight-bold"},[n("v-list-item-title",{on:{click:function(t){return e.fetchData()}}},[e._v(" Load More Items ... ")])],1)],1):e._e()]},proxy:!0}],null,!0),model:{value:e.selectedData,callback:function(t){e.selectedData=t},expression:"selectedData"}}),e._t("default")],2)},i=[],s=n("2909"),r=n("5530"),o=n("53ca"),l=n("1da1"),c=(n("96cf"),n("a9e3"),n("ac1f"),n("841c"),n("7db0"),n("d81d"),n("159b"),n("4de4"),n("4e827"),n("2ca0"),n("d3b7"),n("c740"),n("a434"),n("3ca3"),n("ddb0"),n("2b3d"),n("caad"),n("2532"),n("63ea")),u=n.n(c),d={props:{value:{type:[Number,String,Array,Object],default:void 0},id:{type:String,default:""},dataCyVariable:{type:String,default:""},endpoint:{type:String,default:""},itemText:{type:String,required:!0},itemValue:{type:String,required:!0},params:{type:Object,required:!1,default:function(){return{}}},itemsToExclude:{type:[Array,Number],default:null},forceFetch:{type:Boolean,default:!1},staticItems:{type:Array,default:function(){return[]}},errorMessages:{type:[String,Array],default:function(){return[]}},label:{type:String,default:""},disabled:{type:Boolean,default:!1},readonly:{type:Boolean,default:!1},hint:{type:String,default:void 0},persistentHint:{type:Boolean,required:!1,default:!1},multiple:{type:Boolean,required:!1,default:!1},clearable:{type:Boolean,default:!0},hideDetails:{type:Boolean,default:!1},solo:{type:Boolean,default:!1},flat:{type:Boolean,default:!1},chips:{type:Boolean,default:!1},prependInnerIcon:{type:String,default:void 0},cacheItems:{type:Boolean,default:!1},appliedClass:{type:String,default:""},placeholder:{type:String,default:""},dense:{type:Boolean,default:!1}},data:function(){return{componentKey:0,items:[],selectedData:null,search:null,initialFetchStarted:!1,nextLimit:null,nextOffset:null,showMoreIcon:!1,fullyLoaded:!1,isLoading:!1}},computed:{itemsSorted:function(){return this.sortBySearch(this.items,this.search?this.search.toLowerCase():"")}},watch:{value:{handler:function(){var e=Object(l["a"])(regeneratorRuntime.mark((function e(t){var n,a,i,s,r=this;return regeneratorRuntime.wrap((function(e){while(1)switch(e.prev=e.next){case 0:if(!t){e.next=10;break}if(!this.forceFetch||this.initialFetchStarted){e.next=6;break}return this.initialFetchStarted=!0,e.next=5,this.fetchData();case 5:this.removeDuplicateItem();case 6:Array.isArray(t)?(i=[],"object"===Object(o["a"])(t[0])?(this.selectedData=t.map((function(e){return e[r.itemValue]})),t.forEach((function(e){var t=r.items.find((function(t){return t===e}));t||i.push(e)}))):(t.forEach((function(e){var t=r.items.find((function(t){return t[r.itemValue]===e}));t||i.push(e)})),this.selectedData=t),i.length>0&&(s=this.items).push.apply(s,i)):"object"===Object(o["a"])(t)?(this.selectedData=t[this.itemValue],n=this.items.find((function(e){return e[r.itemValue]===t})),n||this.items.push(t)):(this.selectedData=t,a=this.items.find((function(e){return e===t})),a||this.items.push(t)),this.updateData(this.selectedData),e.next=11;break;case 10:t||(this.selectedData=null);case 11:case"end":return e.stop()}}),e,this)})));function t(t){return e.apply(this,arguments)}return t}(),immediate:!0},selectedData:function(e){this.updateData(e)},params:{handler:function(e,t){u()(e,t)||(this.fullyLoaded=!1,this.initialFetchStarted=!1,this.items=[],this.componentKey+=1)},deep:!0}},methods:{sortBySearch:function(e,t){var n=this.itemText,a=e.filter((function(e){return"object"===Object(o["a"])(e)}));return a.sort((function(e,a){return e[n].toLowerCase().startsWith(t)&&a[n].toLowerCase().startsWith(t)?e[n].toLowerCase().localeCompare(a[n].toLowerCase()):e[n].toLowerCase().startsWith(t)?-1:a[n].toLowerCase().startsWith(t)?1:e[n].toLowerCase().localeCompare(a[n].toLowerCase())}))},populateOnFocus:function(){var e=this;return Object(l["a"])(regeneratorRuntime.mark((function t(){return regeneratorRuntime.wrap((function(t){while(1)switch(t.prev=t.next){case 0:if(!e.initialFetchStarted){t.next=2;break}return t.abrupt("return");case 2:return e.initialFetchStarted=!0,t.next=5,e.fetchData();case 5:e.removeDuplicateItem();case 6:case"end":return t.stop()}}),t)})))()},fetchData:function(){var e=this;return Object(l["a"])(regeneratorRuntime.mark((function t(){var n,a;return regeneratorRuntime.wrap((function(t){while(1)switch(t.prev=t.next){case 0:if(!(e.staticItems.length>0)){t.next=3;break}return e.items=e.staticItems,t.abrupt("return");case 3:return n=e.nextLimit,a=e.nextOffset,e.search&&(n=null,a=null),e.isLoading=!0,t.next=9,e.$http.get(e.endpoint,{params:Object(r["a"])(Object(r["a"])({},e.params),{},{search:e.search,limit:n,offset:a})}).then((function(t){var n;t.results||(t.results=t),t.next?(e.showMoreIcon=!0,e.extractLimitOffset(t.next)):(e.showMoreIcon=!1,e.search||(e.fullyLoaded=!0)),e.itemsToExclude&&(t.results=e.excludeRecord(t.results)),(n=e.items).push.apply(n,Object(s["a"])(t.results))})).finally((function(){e.isLoading=!1}));case 9:case"end":return t.stop()}}),t)})))()},removeDuplicateItem:function(){var e=this,t=this.items.indexOf(this.selectedData);if(t>=0){var n=this.items.findIndex((function(t){return t[e.itemValue]===e.selectedData}));n>=0&&(this.items.splice(t,1),this.componentKey+=1)}},updateData:function(e){var t=this,n=[];e instanceof Array?e.forEach((function(e){n.unshift(t.items.find((function(n){return n[t.itemValue]===e})))})):n=this.items.find((function(n){return n[t.itemValue]===e})),this.$emit("input",e),this.$emit("update:selectedFullData",n)},searchText:function(){0!==this.$refs.autoComplete.filteredItems.length||this.fullyLoaded||this.fetchData()},extractLimitOffset:function(e){var t=new URL(e);this.nextLimit=t.searchParams.get("limit"),this.nextOffset=t.searchParams.get("offset")},excludeRecord:function(e){var t=this,n=[];return"number"===typeof this.itemsToExclude?n.push(this.itemsToExclude):n=this.itemsToExclude,e.filter((function(e){if(e[t.itemValue])return!n.includes(e[t.itemValue])}))},remove:function(e){if(this.selectedData instanceof Object){var t=this.selectedData.indexOf(e[this.itemValue]);t>=0&&this.selectedData.splice(t,1)}else this.selectedData=null},updateState:function(){this.search="",this.nextLimit&&(this.showMoreIcon=!0)}}},p=d,h=n("2877"),m=n("6544"),f=n.n(m),v=n("c6a6"),g=n("cc20"),b=n("5d23"),y=n("3a2f"),x=Object(h["a"])(p,a,i,!1,null,null,null);t["default"]=x.exports;f()(x,{VAutocomplete:v["a"],VChip:g["a"],VListItemContent:b["a"],VListItemTitle:b["c"],VTooltip:y["a"]})},"86eb":function(e,t,n){"use strict";n("99af");t["a"]={getJobTitle:function(e){return"/org/".concat(e,"/employment/job-title/")},postJobTitle:function(e){return"/org/".concat(e,"/employment/job-title/")},getJobTitleDetail:function(e,t){return"/org/".concat(e,"/employment/job-title/").concat(t,"/")},updateJobTitle:function(e,t){return"/org/".concat(e,"/employment/job-title/").concat(t,"/")},deleteJobTitle:function(e,t){return"/org/".concat(e,"/employment/job-title/").concat(t,"/")},importJobTitle:function(e){return"/org/".concat(e,"/employment/job-title/import/")},downloadSampleJobTitle:function(e){return"/org/".concat(e,"/employment/job-title/import/sample")}}},a51f:function(e,t,n){"use strict";n.r(t);var a=function(){var e=this,t=e.$createElement,n=e._self._c||t;return n("div",[e.search.length>0?n("span",[e._v(' Your search for "'+e._s(e.search)+'" found no results. ')]):e.loading?n("v-skeleton-loader",{attrs:{type:"table",height:e.skeletonLoaderHeight}}):n("no-data-found",{attrs:{text:e.text,height:e.height}},[e._t("default")],2)],1)},i=[],s=(n("a9e3"),n("e585")),r={components:{NoDataFound:s["default"]},props:{search:{type:String,default:""},loading:{type:Boolean,required:!0},text:{type:String,default:"No data available at the moment"},height:{type:[String,Number],default:200},skeletonLoaderHeight:{type:[String,Number],default:void 0}}},o=r,l=n("2877"),c=n("6544"),u=n.n(c),d=n("3129"),p=Object(l["a"])(o,a,i,!1,null,null,null);t["default"]=p.exports;u()(p,{VSkeletonLoader:d["a"]})},abd3:function(e,t,n){},c13e:function(e,t,n){"use strict";n("99af"),n("d3b7"),n("b0c0");t["a"]={data:function(){return{deleteNotification:{dialog:!1,heading:"Confirm Delete",text:"Are you sure you want to delete ?"}}},methods:{deleteData:function(e){var t=this;if(!this.loading){var n=this.actionData?this.actionData[this.crud.id]:"",a=e||this.crud.endpoint.delete||"".concat(this.crud.endpoint.common).concat(n,"/");return this.loading=!0,new Promise((function(e,n){t.$http.delete(a,{params:t.crud.urlParams}).then((function(n){e(n),setTimeout((function(){t.notifyUser(t.crud.message||"Successfully Deleted ".concat(t.crud.name))}),1e3),t.deleteNotification.dialog=!1,t.loading=!1,"undefined"!==typeof t.dataTableFetch&&t.loadDataTableChange(),t.actionData={},t.processAfterDeleteSuccess()})).catch((function(e){n(e),t.pushErrors(e),t.processOnDeleteError(e),t.notifyInvalidFormResponse()})).finally((function(){t.loading=!1,t.processAfterDelete()}))}))}},processAfterDelete:function(){},processAfterDeleteSuccess:function(){},processOnDeleteError:function(){}}}},c865:function(e,t,n){"use strict";var a=n("5530"),i=n("0789"),s=n("9d26"),r=n("a9ad"),o=n("3206"),l=n("5607"),c=n("80d2"),u=n("58df"),d=Object(u["a"])(r["a"],Object(o["a"])("expansionPanel","v-expansion-panel-header","v-expansion-panel"));t["a"]=d.extend().extend({name:"v-expansion-panel-header",directives:{ripple:l["a"]},props:{disableIconRotate:Boolean,expandIcon:{type:String,default:"$expand"},hideActions:Boolean,ripple:{type:[Boolean,Object],default:!1}},data:function(){return{hasMousedown:!1}},computed:{classes:function(){return{"v-expansion-panel-header--active":this.isActive,"v-expansion-panel-header--mousedown":this.hasMousedown}},isActive:function(){return this.expansionPanel.isActive},isDisabled:function(){return this.expansionPanel.isDisabled},isReadonly:function(){return this.expansionPanel.isReadonly}},created:function(){this.expansionPanel.registerHeader(this)},beforeDestroy:function(){this.expansionPanel.unregisterHeader()},methods:{onClick:function(e){this.$emit("click",e)},genIcon:function(){var e=Object(c["s"])(this,"actions")||[this.$createElement(s["a"],this.expandIcon)];return this.$createElement(i["d"],[this.$createElement("div",{staticClass:"v-expansion-panel-header__icon",class:{"v-expansion-panel-header__icon--disable-rotate":this.disableIconRotate},directives:[{name:"show",value:!this.isDisabled}]},e)])}},render:function(e){var t=this;return e("button",this.setBackgroundColor(this.color,{staticClass:"v-expansion-panel-header",class:this.classes,attrs:{tabindex:this.isDisabled?-1:null,type:"button"},directives:[{name:"ripple",value:this.ripple}],on:Object(a["a"])(Object(a["a"])({},this.$listeners),{},{click:this.onClick,mousedown:function(){return t.hasMousedown=!0},mouseup:function(){return t.hasMousedown=!1}})}),[Object(c["s"])(this,"default",{open:this.isActive},!0),this.hideActions||this.genIcon()])}})},cba0:function(e,t,n){"use strict";n.r(t);var a=function(){var e=this,t=e.$createElement,n=e._self._c||t;return n("vue-page-wrapper",{attrs:{title:e.htmlTitle,"bread-crumbs":e.breadCrumbItems}},[n("v-card",{attrs:{height:"auto"}},[n("vue-card-title",{attrs:{title:"Peer To Peer Evaluation Form",subtitle:"Here you can view/edit/generate peer to peer evaluation form",icon:"mdi-account-check-outline"}},[n("template",{slot:"actions"},[n("v-btn",{attrs:{small:"",color:"primary",depressed:""},on:{click:function(t){e.sendForm=!0}}},[e._v(" Send ")]),n("v-btn",{attrs:{icon:""},on:{click:function(t){e.showFilters=!e.showFilters}}},[n("v-icon",{attrs:{small:""},domProps:{textContent:e._s("mdi-filter-variant")}})],1)],1)],2),n("v-divider"),e.showFilters?n("v-slide-y-transition",[n("v-row",{staticClass:"px-3"},[n("v-col",{attrs:{md:"4",cols:"6"}},[n("vue-search",{attrs:{search:e.search},on:{"update:search":function(t){e.search=t}},model:{value:e.search,callback:function(t){e.search=t},expression:"search"}})],1),n("v-col",{attrs:{md:"4",cols:"6"}},[n("vue-auto-complete",{attrs:{"data-cy-variable":"branch",endpoint:e.branchesEndpoint,params:{is_archived:!1},label:"Select Branch","item-text":"name","hide-details":"","item-value":"slug"},model:{value:e.searchFilters.branch,callback:function(t){e.$set(e.searchFilters,"branch",t)},expression:"searchFilters.branch"}})],1),n("v-col",{attrs:{md:"4",cols:"6"}},[n("vue-auto-complete",{attrs:{"data-cy-variable":"division",endpoint:e.divisionEndpoint,params:{is_archived:!1},label:"Select Division","item-text":"name","item-value":"slug"},model:{value:e.searchFilters.division,callback:function(t){e.$set(e.searchFilters,"division",t)},expression:"searchFilters.division"}})],1),n("v-col",{attrs:{md:"4",cols:"6"}},[n("vue-auto-complete",{attrs:{"data-cy-variable":"job-title",endpoint:e.jobTitleEndpoint,label:"Select Job Title","item-text":"title","item-value":"slug"},model:{value:e.searchFilters.job_title,callback:function(t){e.$set(e.searchFilters,"job_title",t)},expression:"searchFilters.job_title"}})],1),n("v-col",{attrs:{md:"4",cols:"6"}},[n("vue-auto-complete",{attrs:{"data-cy-variable":"employment-level",endpoint:e.employeeLevelEndpoint,params:{is_archived:"false"},label:"Select Employment Level","item-text":"title","item-value":"slug"},model:{value:e.searchFilters.employment_level,callback:function(t){e.$set(e.searchFilters,"employment_level",t)},expression:"searchFilters.employment_level"}})],1)],1)],1):e._e(),e.showFilters?n("v-divider"):e._e(),n("v-data-table",{attrs:{headers:e.headers,items:e.fetchedResults,"footer-props":e.footerProps,"sort-desc":e.pagination.descending,"sort-by":e.pagination.sortBy,page:e.pagination.page,"items-per-page":e.pagination.rowsPerPage,"server-items-length":e.pagination.totalItems,"must-sort":"","mobile-breakpoint":0},on:{"update:sortDesc":function(t){return e.$set(e.pagination,"descending",t)},"update:sort-desc":function(t){return e.$set(e.pagination,"descending",t)},"update:sortBy":function(t){return e.$set(e.pagination,"sortBy",t)},"update:sort-by":function(t){return e.$set(e.pagination,"sortBy",t)},"update:page":function(t){return e.$set(e.pagination,"page",t)},"update:itemsPerPage":function(t){return e.$set(e.pagination,"rowsPerPage",t)},"update:items-per-page":function(t){return e.$set(e.pagination,"rowsPerPage",t)}},scopedSlots:e._u([{key:"item",fn:function(t){return[n("tr",[n("td",[n("div",[e._v(e._s(t.item.appraisee.full_name))])]),n("td",[n("v-chip",{staticClass:"pointer",on:{click:function(n){t.item.appraiser_counts.internal_appraiser&&e.openListDialog(t.item,"Internal")}}},[e._v(e._s(t.item.appraiser_counts.internal_appraiser||0))])],1),n("td",[n("v-chip",{staticClass:"pointer",on:{click:function(n){t.item.appraiser_counts.external_appraiser&&e.openListDialog(t.item,"External")}}},[e._v(e._s(t.item.appraiser_counts.external_appraiser||0))])],1)])]}}])},[n("template",{slot:"no-data"},[n("no-data-found",{attrs:{loading:e.loading}})],1)],2),n("v-dialog",{key:e.userType,attrs:{width:"500",scrollable:"",persistent:""},model:{value:e.showList,callback:function(t){e.showList=t},expression:"showList"}},[e.showList?n("show-form-list-dialog",{key:e.showList,attrs:{"individual-appraisal":e.selectedItem,as:"hr","user-type":e.userType},on:{close:function(t){e.showList=!1}}}):e._e()],1),e.sendForm?n("v-dialog",{attrs:{width:"450",scrollable:"",presistent:""},on:{keydown:function(t){if(!t.type.indexOf("key")&&e._k(t.keyCode,"esc",27,t.key,["Esc","Escape"]))return null;e.sendForm=!1}},model:{value:e.sendForm,callback:function(t){e.sendForm=t},expression:"sendForm"}},[n("v-card",[n("vue-card-title",{attrs:{title:"Send Peer To Peer Form",subtitle:"Here you can send peer to peer form",icon:"mdi-playlist-check",closable:""},on:{close:function(t){e.sendForm=!1}}}),n("v-divider"),n("v-card-text",{staticClass:"align-center"},[n("h4",[e._v("Are you sure you want to send the question set?")])]),n("v-divider"),n("v-card-actions",[n("v-row",{attrs:{"no-gutters":""}},[n("v-col",{staticClass:"text-right"},[n("v-btn",{attrs:{small:"",text:""},on:{click:function(t){e.sendForm=!1}}},[e._v("Close")]),n("v-btn",{attrs:{color:"primary",small:""},on:{click:e.sendEvaluatorForm,close:function(t){e.sendForm=!1}}},[e._v("Send")])],1)],1)],1)],1)],1):e._e()],1)],1)},i=[],s=n("5530"),r=(n("ac1f"),n("841c"),n("d3b7"),n("0549")),o=n("a51f"),l=n("17cc"),c=function(){var e=this,t=e.$createElement,n=e._self._c||t;return n("v-card",[n("vue-card-title",{attrs:{title:e.userType+" Evaluators",subtitle:e.userType+" evaluators",icon:"mdi-account-group-outline",dark:"",closable:""},on:{close:function(t){return e.$emit("close")}}}),n("v-divider"),n("non-field-form-errors",{attrs:{"non-field-errors":e.nonFieldErrors}}),n("v-card-text",[e.individualAppraisers.length?e._e():n("div",[n("vue-no-data")],1),"Internal"===e.userType?n("v-list",e._l(e.individualAppraisers,(function(t,a){return n("v-list-item-content",{key:a},[n("vue-user",{staticClass:"mx-5",attrs:{user:t.internal_user}}),n("v-row",{attrs:{"no-gutters":""}},[n("v-col",{staticClass:"text-right"},[n("v-btn",{attrs:{small:"",color:"primary",depressed:""},on:{click:function(n){return e.openQuestionDialog(t)}}},[e._v("View Question Set")])],1)],1)],1)})),1):n("v-expansion-panels",{attrs:{accordion:""}},e._l(e.individualAppraisers,(function(t,a){return n("v-expansion-panel",{key:a},[n("v-expansion-panel-header",[n("div",[n("v-icon",{attrs:{small:""}},[e._v(" mdi-account")]),e._v(e._s(t.external_user.name)+" ")],1),n("v-row",{attrs:{"no-gutters":""}},[n("v-col",{staticClass:"text-right"},[n("v-btn",{attrs:{small:"",color:"primary",depressed:""},on:{click:function(n){return e.openQuestionDialog(t)}}},[e._v("View Question Set")])],1)],1)],1),n("v-expansion-panel-content",[n("v-row",[n("v-col",{attrs:{md:"10"}},[n("a",{attrs:{id:"external-url",href:t.external_link,target:"_blank"}},[e._v(" "+e._s(t.external_link)+" ")])]),n("v-col",{attrs:{md:"2"}},[n("v-btn",{attrs:{icon:"",color:"primary"},on:{click:function(t){return e.copyText()}}},[n("v-icon",{attrs:{small:""},domProps:{textContent:e._s("mdi-content-copy")}})],1)],1)],1)],1)],1)})),1),n("v-dialog",{attrs:{width:"1000"},model:{value:e.viewQuestionSheet,callback:function(t){e.viewQuestionSheet=t},expression:"viewQuestionSheet"}},[e.viewQuestionSheet?n("view-question",{key:e.viewQuestionSheet,attrs:{as:e.as,"selected-appraiser":e.selectedItem},on:{close:function(t){e.viewQuestionSheet=!1,e.loadData()}}}):e._e()],1)],1)],1)},u=[],d=n("e585"),p=n("3241"),h=n("dd34"),m=n("02cb"),f=n("ab8a"),v=n("f12b"),g={components:{NonFieldFormErrors:f["default"],VueUser:m["default"],VueNoData:d["default"],viewQuestion:p["a"]},mixins:[v["a"]],name:"ShowListDialog",props:{individualAppraisal:{type:Object,required:!0},userType:{type:String,required:!0},as:{type:String,default:"user"}},data:function(){return{viewQuestionSheet:!1,individualAppraisers:[],selectedItem:{}}},created:function(){this.loadData()},methods:{openQuestionDialog:function(e){this.viewQuestionSheet=!0,this.selectedItem=e,this.$emit("closeList")},copyText:function(){var e=document.getElementById("external-url"),t=window.getSelection(),n=document.createRange();n.selectNodeContents(e),t.removeAllRanges(),t.addRange(n),document.execCommand("Copy"),t.empty(),this.notifyUser("Url copied to clipboard","blue")},loadData:function(){var e=this;this.$http.get(h["a"].getAppraiser(this.getOrganizationSlug,this.$route.params.id),{params:{as:this.as,individual_appraisal:this.individualAppraisal.id,user_type:this.userType}}).then((function(t){e.individualAppraisers=t.results}))}}},b=g,y=n("2877"),x=n("6544"),_=n.n(x),S=n("8336"),w=n("b0af"),k=n("99d9"),D=n("62ad"),O=n("169a"),C=n("ce7e"),j=n("cd55"),T=n("49e2"),L=n("c865"),B=n("0393"),E=n("132d"),$=n("8860"),F=n("5d23"),V=n("0fd9b"),I=Object(y["a"])(b,c,u,!1,null,null,null),A=I.exports;_()(I,{VBtn:S["a"],VCard:w["a"],VCardText:k["c"],VCol:D["a"],VDialog:O["a"],VDivider:C["a"],VExpansionPanel:j["a"],VExpansionPanelContent:T["a"],VExpansionPanelHeader:L["a"],VExpansionPanels:B["a"],VIcon:E["a"],VList:$["a"],VListItemContent:F["a"],VRow:V["a"]});var P=n("e59e"),R=n("1229"),z=n("5660"),N=n("86eb"),M=n("2c2a"),Q=n("4f4a"),H=n("2f62"),q={components:{VueAutoComplete:z["default"],showFormListDialog:A,VuePageWrapper:r["default"],NoDataFound:o["default"]},props:{as:{type:String,default:""}},mixins:[l["a"],Q["a"]],data:function(){return{showFilters:!1,jobTitleEndpoint:"",divisionEndpoint:"",employeeLevelEndpoint:"",branchesEndpoint:"",searchFilters:{job_title:"",employment_level:"",division:"",branch:""},search:"",sendForm:!1,generateEvaluator:!1,showList:!1,userType:"",selectedItem:{},displayForm:!1,actionData:{},isHrAdmin:!0,htmlTitle:"Forms | Appraisal Settings | Settings | Dignity | Admin",breadCrumbItems:[{text:"Settings",disabled:!1,to:{name:"admin-slug-dignity-settings",params:{slug:this.$route.params.slug}}},{text:"Appraisal Settings",disabled:!1,to:{name:"admin-slug-dignity-appraisal-setting",params:{slug:this.$route.params.slug}}},{text:"Forms",disabled:!0}],loading:!1,headers:[{text:"Evaluatee Name",value:"name"},{text:"No. of Internal Evaluator",value:"internal"},{text:"No. of External Evaluator",value:"external"}]}},computed:{DataTableFilter:function(){return{as:"hr",search:this.search,branch:this.searchFilters.branch||"",division:this.searchFilters.division||"",job_title:this.searchFilters.job_title||"",employment_level:this.searchFilters.employment_level||""}}},created:function(){this.initializeDynamicUrls(),this.fetchDataTable()},methods:Object(s["a"])(Object(s["a"])({},Object(H["d"])({setSnackBar:"common/setSnackBar"})),{},{initializeDynamicUrls:function(){this.jobTitleEndpoint=N["a"].getJobTitle(this.getOrganizationSlug),this.divisionEndpoint=R["a"].getDivision(this.getOrganizationSlug),this.employeeLevelEndpoint=M["a"].getEmploymentLevel(this.getOrganizationSlug),this.branchesEndpoint=P["a"].getBranch(this.getOrganizationSlug)},fetchDataTable:function(){var e=this;this.loading||(this.loading=!0,this.$http.get(h["a"].getEvaluatee(this.getOrganizationSlug,this.$route.params.id),{params:this.fullParams}).then((function(t){e.loadDataTable(t)})).finally((function(){e.loading=!1})))},openListDialog:function(e,t){this.selectedItem=e,this.userType=t,this.showList=!0},sendEvaluatorForm:function(){var e=this;this.$http.post(h["a"].sendEvaluationForm(this.getOrganizationSlug,this.$route.params.id),["this array has nothing to do with backend, its just data params for post method."],{params:{as:"hr"}}).then((function(){return e.sendForm=!1}),this.fetchDataTable),this.setSnackBar({text:"Successfully sent question form.",color:"green"})}})},J=q,U=n("cc20"),W=n("8fea"),K=n("0789"),Y=Object(y["a"])(J,a,i,!1,null,null,null);t["default"]=Y.exports;_()(Y,{VBtn:S["a"],VCard:w["a"],VCardActions:k["a"],VCardText:k["c"],VChip:U["a"],VCol:D["a"],VDataTable:W["a"],VDialog:O["a"],VDivider:C["a"],VIcon:E["a"],VRow:V["a"],VSlideYTransition:K["g"]})},cd55:function(e,t,n){"use strict";var a=n("5530"),i=n("4e82"),s=n("3206"),r=n("80d2"),o=n("58df");t["a"]=Object(o["a"])(Object(i["a"])("expansionPanels","v-expansion-panel","v-expansion-panels"),Object(s["b"])("expansionPanel",!0)).extend({name:"v-expansion-panel",props:{disabled:Boolean,readonly:Boolean},data:function(){return{content:null,header:null,nextIsActive:!1}},computed:{classes:function(){return Object(a["a"])({"v-expansion-panel--active":this.isActive,"v-expansion-panel--next-active":this.nextIsActive,"v-expansion-panel--disabled":this.isDisabled},this.groupClasses)},isDisabled:function(){return this.expansionPanels.disabled||this.disabled},isReadonly:function(){return this.expansionPanels.readonly||this.readonly}},methods:{registerContent:function(e){this.content=e},unregisterContent:function(){this.content=null},registerHeader:function(e){this.header=e,e.$on("click",this.onClick)},unregisterHeader:function(){this.header=null},onClick:function(e){e.detail&&this.header.$el.blur(),this.$emit("click",e),this.isReadonly||this.isDisabled||this.toggle()},toggle:function(){var e=this;this.content&&(this.content.isBooted=!0),this.$nextTick((function(){return e.$emit("change")}))}},render:function(e){return e("div",{staticClass:"v-expansion-panel",class:this.classes,attrs:{"aria-expanded":String(this.isActive)}},Object(r["s"])(this))}})},e59e:function(e,t,n){"use strict";n("99af");t["a"]={getBranch:function(e){return"/org/".concat(e,"/branch/")},postBranch:function(e){return"/org/".concat(e,"/branch/")},getBranchDetail:function(e,t){return"/org/".concat(e,"/branch/").concat(t,"/")},updateBranch:function(e,t){return"/org/".concat(e,"/branch/").concat(t,"/")},deleteBranch:function(e,t){return"/org/".concat(e,"/branch/").concat(t,"/")},importBranch:function(e){return"/org/".concat(e,"/branch/import/")},downloadSampleBranch:function(e){return"/org/".concat(e,"/branch/import/sample")},exportBranch:function(e){return"/org/".concat(e,"/branch/export")},branchType:function(e){return"/org/".concat(e,"/branch-type")},branchTypeDetail:function(e,t){return"org/".concat(e,"/branch-type/").concat(t)}}}}]);