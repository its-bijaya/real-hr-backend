(window["webpackJsonp"]=window["webpackJsonp"]||[]).push([["pages/admin/_slug/pa/settings/appraisal/_id/kaar-forms","chunk-26c51c79","chunk-31f8a6e6"],{"0549":function(e,t,a){"use strict";a.r(t);var i=function(){var e=this,t=e.$createElement,a=e._self._c||t;return a("div",[a("v-row",{staticClass:"mb-3",attrs:{"no-gutters":""}},[e.breadCrumbs?a("v-col",{attrs:{cols:"12"}},[a("v-card",{attrs:{flat:""}},[a("v-breadcrumbs",{staticClass:"text-body-1 pa-2",class:{"text-caption pa-1":e.$vuetify.breakpoint.xs},attrs:{items:e.breadCrumbs},scopedSlots:e._u([{key:"item",fn:function(t){return[a("span",{class:t.item.disabled?"grey--text":"baseColor--text text--accent-2 pointer",domProps:{textContent:e._s(t.item.text)},on:{click:function(a){return e.$router.push(t.item.to)}}})]}}],null,!1,1670153796)},[a("v-icon",{attrs:{slot:"divider"},slot:"divider"},[e._v("mdi-chevron-right")])],1)],1)],1):e._e()],1),a("v-row",{attrs:{"no-gutters":""}},[a("v-col",{attrs:{cols:"12"}},[e._t("default")],2)],1)],1)},r=[],n=a("5530"),s=(a("ac1f"),a("1276"),a("b0c0"),a("2f62")),o={props:{title:{type:String,required:!0},breadCrumbs:{type:Array,default:function(){return[]}}},computed:Object(n["a"])({},Object(s["c"])({getOrganizationName:"organization/getOrganizationName",getSupervisorSwitchedOrganization:"supervisor/getSwitchedOrganization"})),mounted:function(){document.title="".concat(this.title," | RealHRsoft");var e=this.$route.params.slug?"admin-slug-dashboard":"root",t=this.$route.name.split("-"),a=this.getOrganizationName;this.getSupervisorSwitchedOrganization&&"user"===t[0]&&"supervisor"===t[1]&&(a=this.getSupervisorSwitchedOrganization.name),this.breadCrumbs.unshift({text:a,disabled:!1,to:{name:e,params:{slug:this.$route.params.slug}}})}},l=o,d=a("2877"),c=a("6544"),u=a.n(c),p=a("2bc5"),m=a("b0af"),h=a("62ad"),f=a("132d"),v=a("0fd9b"),g=Object(d["a"])(l,i,r,!1,null,null,null);t["default"]=g.exports;u()(g,{VBreadcrumbs:p["a"],VCard:m["a"],VCol:h["a"],VIcon:f["a"],VRow:v["a"]})},"1f09":function(e,t,a){},"2bc5":function(e,t,a){"use strict";var i=a("5530"),r=(a("a15b"),a("abd3"),a("ade3")),n=a("1c87"),s=a("58df"),o=Object(s["a"])(n["a"]).extend({name:"v-breadcrumbs-item",props:{activeClass:{type:String,default:"v-breadcrumbs__item--disabled"},ripple:{type:[Boolean,Object],default:!1}},computed:{classes:function(){return Object(r["a"])({"v-breadcrumbs__item":!0},this.activeClass,this.disabled)}},render:function(e){var t=this.generateRouteLink(),a=t.tag,r=t.data;return e("li",[e(a,Object(i["a"])(Object(i["a"])({},r),{},{attrs:Object(i["a"])(Object(i["a"])({},r.attrs),{},{"aria-current":this.isActive&&this.isLink?"page":void 0})}),this.$slots.default)])}}),l=a("80d2"),d=Object(l["i"])("v-breadcrumbs__divider","li"),c=a("7560");t["a"]=Object(s["a"])(c["a"]).extend({name:"v-breadcrumbs",props:{divider:{type:String,default:"/"},items:{type:Array,default:function(){return[]}},large:Boolean},computed:{classes:function(){return Object(i["a"])({"v-breadcrumbs--large":this.large},this.themeClasses)}},methods:{genDivider:function(){return this.$createElement(d,this.$slots.divider?this.$slots.divider:this.divider)},genItems:function(){for(var e=[],t=!!this.$scopedSlots.item,a=[],i=0;i<this.items.length;i++){var r=this.items[i];a.push(r.text),t?e.push(this.$scopedSlots.item({item:r})):e.push(this.$createElement(o,{key:a.join("."),props:r},[r.text])),i<this.items.length-1&&e.push(this.genDivider())}return e}},render:function(e){var t=this.$slots.default||this.genItems();return e("ul",{staticClass:"v-breadcrumbs",class:this.classes},t)}})},3129:function(e,t,a){"use strict";var i=a("3835"),r=a("5530"),n=(a("ac1f"),a("1276"),a("d81d"),a("a630"),a("3ca3"),a("5319"),a("1f09"),a("c995")),s=a("24b2"),o=a("7560"),l=a("58df"),d=a("80d2");t["a"]=Object(l["a"])(n["a"],s["a"],o["a"]).extend({name:"VSkeletonLoader",props:{boilerplate:Boolean,loading:Boolean,tile:Boolean,transition:String,type:String,types:{type:Object,default:function(){return{}}}},computed:{attrs:function(){return this.isLoading?this.boilerplate?{}:Object(r["a"])({"aria-busy":!0,"aria-live":"polite",role:"alert"},this.$attrs):this.$attrs},classes:function(){return Object(r["a"])(Object(r["a"])({"v-skeleton-loader--boilerplate":this.boilerplate,"v-skeleton-loader--is-loading":this.isLoading,"v-skeleton-loader--tile":this.tile},this.themeClasses),this.elevationClasses)},isLoading:function(){return!("default"in this.$scopedSlots)||this.loading},rootTypes:function(){return Object(r["a"])({actions:"button@2",article:"heading, paragraph",avatar:"avatar",button:"button",card:"image, card-heading","card-avatar":"image, list-item-avatar","card-heading":"heading",chip:"chip","date-picker":"list-item, card-heading, divider, date-picker-options, date-picker-days, actions","date-picker-options":"text, avatar@2","date-picker-days":"avatar@28",heading:"heading",image:"image","list-item":"text","list-item-avatar":"avatar, text","list-item-two-line":"sentences","list-item-avatar-two-line":"avatar, sentences","list-item-three-line":"paragraph","list-item-avatar-three-line":"avatar, paragraph",paragraph:"text@3",sentences:"text@2",table:"table-heading, table-thead, table-tbody, table-tfoot","table-heading":"heading, text","table-thead":"heading@6","table-tbody":"table-row-divider@6","table-row-divider":"table-row, divider","table-row":"table-cell@6","table-cell":"text","table-tfoot":"text@2, avatar@2",text:"text"},this.types)}},methods:{genBone:function(e,t){return this.$createElement("div",{staticClass:"v-skeleton-loader__".concat(e," v-skeleton-loader__bone")},t)},genBones:function(e){var t=this,a=e.split("@"),r=Object(i["a"])(a,2),n=r[0],s=r[1],o=function(){return t.genStructure(n)};return Array.from({length:s}).map(o)},genStructure:function(e){var t=[];e=e||this.type||"";var a=this.rootTypes[e]||"";if(e===a);else{if(e.indexOf(",")>-1)return this.mapBones(e);if(e.indexOf("@")>-1)return this.genBones(e);a.indexOf(",")>-1?t=this.mapBones(a):a.indexOf("@")>-1?t=this.genBones(a):a&&t.push(this.genStructure(a))}return[this.genBone(e,t)]},genSkeleton:function(){var e=[];return this.isLoading?e.push(this.genStructure()):e.push(Object(d["s"])(this)),this.transition?this.$createElement("transition",{props:{name:this.transition},on:{afterEnter:this.resetStyles,beforeEnter:this.onBeforeEnter,beforeLeave:this.onBeforeLeave,leaveCancelled:this.resetStyles}},e):e},mapBones:function(e){return e.replace(/\s/g,"").split(",").map(this.genStructure)},onBeforeEnter:function(e){this.resetStyles(e),this.isLoading&&(e._initialStyle={display:e.style.display,transition:e.style.transition},e.style.setProperty("transition","none","important"))},onBeforeLeave:function(e){e.style.setProperty("display","none","important")},resetStyles:function(e){e._initialStyle&&(e.style.display=e._initialStyle.display||"",e.style.transition=e._initialStyle.transition,delete e._initialStyle)}},render:function(e){return e("div",{staticClass:"v-skeleton-loader",attrs:this.attrs,on:this.$listeners,class:this.classes,style:this.isLoading?this.measurableStyles:void 0},[this.genSkeleton()])}})},8113:function(e,t,a){"use strict";a.r(t);var i=function(){var e=this,t=e.$createElement,a=e._self._c||t;return a("v-row",[a("v-col",{attrs:{md:"12",cols:"12"}},[a("vue-search",{staticClass:"px-2",attrs:{search:e.filter.search},on:{"update:search":function(t){return e.$set(e.filter,"search",t)}},model:{value:e.filter.search,callback:function(t){e.$set(e.filter,"search",t)},expression:"filter.search"}})],1),a("v-col",{attrs:{md:"3",cols:"12"}},[a("vue-auto-complete",e._b({staticClass:"px-2",attrs:{endpoint:e.branchEndpoint,"static-items":e.filterData.branches,"item-text":"name","item-value":"slug","prepend-inner-icon":"mdi-map-marker-outline"},model:{value:e.filter.branch,callback:function(t){e.$set(e.filter,"branch",t)},expression:"filter.branch"}},"vue-auto-complete",e.veeValidate("branches","Branch"),!1))],1),a("v-col",{attrs:{md:"3",cols:"12"}},[a("vue-auto-complete",e._b({staticClass:"px-2",attrs:{endpoint:e.divisionEndpoint,"static-items":e.filterData.divisions,"item-text":"name","item-value":"slug","prepend-inner-icon":"mdi-source-branch"},model:{value:e.filter.division,callback:function(t){e.$set(e.filter,"division",t)},expression:"filter.division"}},"vue-auto-complete",e.veeValidate("divisions","Division"),!1))],1),a("v-col",{attrs:{md:"3",cols:"12"}},[a("vue-auto-complete",e._b({staticClass:"px-2",attrs:{endpoint:e.employmentTypeEndpoint,"static-items":e.filterData.employment_types,"item-text":"title","item-value":"slug","prepend-inner-icon":"mdi-briefcase-account-outline"},model:{value:e.filter.employment_type,callback:function(t){e.$set(e.filter,"employment_type",t)},expression:"filter.employment_type"}},"vue-auto-complete",e.veeValidate("employment_types","Employment Type"),!1))],1),a("v-col",{attrs:{md:"3",cols:"12"}},[a("vue-auto-complete",e._b({staticClass:"px-2",attrs:{endpoint:e.employmentLevelEndpoint,"static-items":e.filterData.employment_levels,"item-text":"title","item-value":"slug","prepend-inner-icon":"mdi-family-tree"},model:{value:e.filter.employment_level,callback:function(t){e.$set(e.filter,"employment_level",t)},expression:"filter.employment_level"}},"vue-auto-complete",e.veeValidate("employment_levels","Employment Level"),!1))],1)],1)},r=[],n=(a("d3b7"),a("3ca3"),a("ddb0"),a("f0d5")),s=a("983c"),o=a("e59e"),l=a("1229"),d=a("2c2a"),c=a("7e77"),u=a("a1b8"),p={components:{VueAutoComplete:function(){return a.e("chunk-2d0c8a11").then(a.bind(null,"5660"))}},mixins:[n["a"],s["a"]],props:{reportFilter:{type:Boolean,default:!1}},data:function(){return{filterData:{branches:[],divisions:[],employment_types:[],employment_levels:[]},filter:{search:"",branch:"",division:"",employment_type:"",employment_level:""},branchEndpoint:"",divisionEndpoint:"",employmentLevelEndpoint:"",employmentTypeEndpoint:""}},watch:{filter:{handler:function(e){this.$emit("filter",e)},deep:!0}},created:function(){this.initializeEndpoints(),this.reportFilter||this.getFilterData()},methods:{initializeEndpoints:function(){this.branchEndpoint=o["a"].getBranch(this.getOrganizationSlug)+"?is_archived=false",this.divisionEndpoint=l["a"].getDivision(this.getOrganizationSlug)+"?is_archived=false",this.employmentLevelEndpoint=d["a"].getEmploymentLevel(this.getOrganizationSlug)+"?is_archived=false",this.employmentTypeEndpoint=c["a"].getEmploymentType(this.getOrganizationSlug)+"?is_archived=false"},getFilterData:function(){var e=this;this.getData(u["a"].getAppraiseeSettings(this.getOrganizationSlug,this.$route.params.id)).then((function(t){t.results.length>0&&(e.filterData=t.results[0])}))}}},m=p,h=a("2877"),f=a("6544"),v=a.n(f),g=a("62ad"),b=a("0fd9b"),y=Object(h["a"])(m,i,r,!1,null,null,null);t["default"]=y.exports;v()(y,{VCol:g["a"],VRow:b["a"]})},a51f:function(e,t,a){"use strict";a.r(t);var i=function(){var e=this,t=e.$createElement,a=e._self._c||t;return a("div",[e.search.length>0?a("span",[e._v(' Your search for "'+e._s(e.search)+'" found no results. ')]):e.loading?a("v-skeleton-loader",{attrs:{type:"table",height:e.skeletonLoaderHeight}}):a("no-data-found",{attrs:{text:e.text,height:e.height}},[e._t("default")],2)],1)},r=[],n=(a("a9e3"),a("e585")),s={components:{NoDataFound:n["default"]},props:{search:{type:String,default:""},loading:{type:Boolean,required:!0},text:{type:String,default:"No data available at the moment"},height:{type:[String,Number],default:200},skeletonLoaderHeight:{type:[String,Number],default:void 0}}},o=s,l=a("2877"),d=a("6544"),c=a.n(d),u=a("3129"),p=Object(l["a"])(o,i,r,!1,null,null,null);t["default"]=p.exports;c()(p,{VSkeletonLoader:u["a"]})},abd3:function(e,t,a){},c6d0:function(e,t,a){"use strict";a.r(t);var i=function(){var e=this,t=e.$createElement,a=e._self._c||t;return a("vue-page-wrapper",{attrs:{"bread-crumbs":e.breadCrumbItems,title:e.htmlTitle}},[a("v-card",[a("vue-card-title",{attrs:{title:"Key Achievement And Rating Forms",subtitle:"Here you can generate and view list of forms of all employee.",icon:"mdi-account-check-outline"}},[a("template",{slot:"actions"},[e.generateForm?e._e():a("v-btn",{attrs:{depressed:"",color:"primary"},on:{click:function(t){e.sendForm=!0}}},[e._v(" Send ")]),a("v-btn",{attrs:{depressed:"",color:"primary",outlined:!e.generateForm},on:{click:function(t){e.generateForm?e.confirmGenerate.dialog=!0:e.confirmReGenerate.dialog=!0}}},[e._v(" "+e._s(e.generateForm?"Generate":"Re-Generate")+" ")]),a("v-btn",{attrs:{icon:""},on:{click:function(t){e.showFilter=!e.showFilter}}},[a("v-icon",{attrs:{small:""},domProps:{textContent:e._s("mdi-filter-variant")}})],1)],1)],2),a("v-divider"),a("v-slide-y-transition",[e.showFilter?a("div",[a("pa-filters",{on:{filter:function(t){e.paFilter=t}}})],1):e._e()]),e.showFilter?a("v-divider"):e._e(),e.nonFieldErrors?a("non-field-form-errors",{attrs:{"non-field-errors":e.nonFieldErrors}}):e._e(),a("v-data-table",{attrs:{headers:e.heading,items:e.fetchedResults,"sort-desc":e.pagination.descending,"sort-by":e.pagination.sortBy,page:e.pagination.page,"items-per-page":e.pagination.rowsPerPage,"footer-props":e.footerProps,"server-items-length":e.pagination.totalItems,"mobile-breakpoint":0,"must-sort":""},on:{"update:sortDesc":function(t){return e.$set(e.pagination,"descending",t)},"update:sort-desc":function(t){return e.$set(e.pagination,"descending",t)},"update:sortBy":function(t){return e.$set(e.pagination,"sortBy",t)},"update:sort-by":function(t){return e.$set(e.pagination,"sortBy",t)},"update:page":function(t){return e.$set(e.pagination,"page",t)},"update:itemsPerPage":function(t){return e.$set(e.pagination,"rowsPerPage",t)},"update:items-per-page":function(t){return e.$set(e.pagination,"rowsPerPage",t)}},scopedSlots:e._u([{key:"item",fn:function(t){return[a("tr",[a("td",[a("vue-user",{attrs:{user:t.item.appraisee}})],1),a("td",{staticClass:"text-center"},[a("div",{staticClass:"font-weight-bold text-h6 green--text pointer",on:{click:function(a){e.viewQuestionSet(e.showIndividualForm,t.item.question_set_count["Self Appraisal"]),e.selectedAppraiserType="Self Appraisal"}}},[e._v(" "+e._s(t.item.question_set_count["Self Appraisal"].count)+" ")])]),a("td",{staticClass:"text-center"},[a("div",{staticClass:"font-weight-bold text-h6 cyan--text pointer",on:{click:function(a){e.viewQuestionSet(e.showIndividualForm,t.item.question_set_count["Supervisor Appraisal"]),e.selectedAppraiserType="Supervisor Appraisal"}}},[e._v(" "+e._s(t.item.question_set_count["Supervisor Appraisal"].count)+" ")])]),a("td",{staticClass:"text-center"},[a("div",{staticClass:"font-weight-bold text-h6 purple--text pointer",on:{click:function(a){e.viewQuestionSet(e.showIndividualForm,t.item.question_set_count["Reviewer Evaluation"]),e.selectedAppraiserType="Reviewer Evaluation"}}},[e._v(" "+e._s(t.item.question_set_count["Reviewer Evaluation"].count)+" ")])])])]}}])},[a("template",{slot:"no-data"},[a("data-table-no-data",{attrs:{loading:e.loading}})],1)],2),a("vue-dialog",{attrs:{notify:e.generateForm?e.confirmGenerate:e.confirmReGenerate},on:{close:function(t){e.generateForm?e.confirmGenerate.dialog=!1:e.confirmReGenerate.dialog=!1},agree:e.reGenerate}}),e.showIndividualForm?a("v-dialog",{attrs:{scrollable:"",persistent:"",fullscreen:""},model:{value:e.showIndividualForm,callback:function(t){e.showIndividualForm=t},expression:"showIndividualForm"}},[a("kaar-appraisal-forms",{attrs:{"appraiser-config-id":e.appraiserConfigId,"appraisal-id":this.$route.params.id,as:"hr","read-only":""},on:{close:function(t){e.showIndividualForm=!1},refresh:e.refresh}})],1):e._e(),e.sendForm?a("v-dialog",{attrs:{width:"960",scrollable:"",persistent:""},on:{keydown:function(t){if(!t.type.indexOf("key")&&e._k(t.keyCode,"esc",27,t.key,["Esc","Escape"]))return null;e.sendForm=!1}},model:{value:e.sendForm,callback:function(t){e.sendForm=t},expression:"sendForm"}},[e.sendForm?a("send-kaar-appraisal-form",{attrs:{as:"hr","appraisal-id":e.$route.params.id},on:{close:function(t){e.sendForm=!1},refresh:function(t){e.sendForm=!1,e.fetchDataTable()}}}):e._e()],1):e._e()],1)],1)},r=[],n=a("5530"),s=(a("d3b7"),a("8cd3")),o=a("f70a"),l=a("931c"),d=a("1239"),c=function(){var e=this,t=e.$createElement,a=e._self._c||t;return a("v-card",[a("vue-card-title",{attrs:{title:"Send Key Achievement And Rating Appraisal Form",subtitle:"Here you can send key achievement and rating appraisal forms",icon:"mdi-playlist-check",closable:""},on:{close:function(t){return e.$emit("close")}}}),a("v-divider"),a("v-card-text",{staticClass:"scrollbar-md"},[e.nonFieldErrors?a("non-field-form-errors",{attrs:{"non-field-errors":e.nonFieldErrors}}):e._e(),e._l(e.appraisal_mode,(function(t,i){return a("v-row",{key:i,staticClass:"pl-2",attrs:{"no-gutters":"",align:"center"}},[a("v-col",{attrs:{md:"auto"}},[a("v-checkbox",{attrs:{value:t.appraisal_type},model:{value:e.selectedData,callback:function(t){e.selectedData=t},expression:"selectedData"}})],1),a("v-col",{attrs:{md:"5"}},[a("v-row",{attrs:{"no-gutters":""}},[a("strong",[e._v(e._s(t.appraisal_type))])]),a("v-row",{attrs:{"no-gutters":""}},[a("span",[e._v(e._s(t.subtitle))])])],1),a("v-col",{staticClass:"text-right",attrs:{md:"3",cols:"12"}},[e.selectedData.includes(t.appraisal_type)?a("vue-date-time-picker",e._b({directives:[{name:"validate",rawName:"v-validate",value:"required",expression:"'required'"}],attrs:{"prepend-inner-icon":"mdi-calendar"},model:{value:t.start_date,callback:function(a){e.$set(t,"start_date",a)},expression:"item.start_date"}},"vue-date-time-picker",e.veeValidate("start_date"+i,"Start Date *"),!1)):e._e()],1),a("v-col",{staticClass:"text-right mx-2",attrs:{md:"3",cols:"12"}},[e.selectedData.includes(t.appraisal_type)?a("vue-date-time-picker",e._b({directives:[{name:"validate",rawName:"v-validate",value:"required",expression:"'required'"}],attrs:{"prepend-inner-icon":"mdi-calendar"},model:{value:t.deadline,callback:function(a){e.$set(t,"deadline",a)},expression:"item.deadline"}},"vue-date-time-picker",e.veeValidate("deadline"+i,"Deadline *"),!1)):e._e()],1)],1)}))],2),a("v-divider"),a("v-card-actions",[a("v-row",{attrs:{"no-gutters":""}},[a("v-col",{staticClass:"text-right"},[a("v-btn",{attrs:{small:"",text:""},on:{click:function(t){return e.$emit("close")}}},[e._v("Close")]),a("v-btn",{attrs:{color:"primary",small:""},on:{click:function(t){return e.submitForm()}}},[e._v("Send")])],1)],1)],1)],1)},u=[],p=a("1da1"),m=(a("96cf"),a("a9e3"),a("b0c0"),a("159b"),a("caad"),a("2532"),a("f12b")),h=a("a1b8"),f={mixins:[m["a"]],props:{appraisalId:{type:[String,Number],required:!0},as:{type:String,default:""}},data:function(){return{formValues:[],selectedData:[],currentDate:(new Date).toISOString(),appraisal_mode:[]}},created:function(){var e=this;this.crud.name="Send Appraisal Forms",this.getData(h["a"].getModeOfAppraisal(this.getOrganizationSlug,this.appraisalId)+"?as=".concat(this.as)).then((function(t){t.results.length>0&&t.results.forEach((function(t){t.appraisal_type==="".concat(t.appraisal_type)&&(t.deadline&&e.selectedData.push(t.appraisal_type),e.appraisal_mode.push({subtitle:"Select to assign weightage for ".concat(t.appraisal_type),appraisal_type:"".concat(t.appraisal_type),deadline:t.deadline,start_date:t.start_date||e.currentDate,id:t.id}))}))}))},methods:{submitForm:function(){var e=this;return Object(p["a"])(regeneratorRuntime.mark((function t(){var a;return regeneratorRuntime.wrap((function(t){while(1)switch(t.prev=t.next){case 0:a=[],e.appraisal_mode.forEach((function(t){e.selectedData.includes(t.appraisal_type)&&a.push({appraisal_type:t.appraisal_type,start_date:t.start_date,deadline:t.deadline})})),e.insertData(l["a"].updateAppraisalFormDates(e.getOrganizationSlug,e.appraisalId),a).then((function(){e.sendForm()}));case 3:case"end":return t.stop()}}),t)})))()},sendForm:function(){var e=this;this.crud.message="Successfully sent appraisal form",this.insertData(l["a"].sendKaarAppraisalForms(this.getOrganizationSlug,this.appraisalId)).then((function(){e.$emit("refresh")}))}}},v=f,g=a("2877"),b=a("6544"),y=a.n(b),_=a("8336"),x=a("b0af"),S=a("99d9"),w=a("ac7c"),k=a("62ad"),F=a("ce7e"),C=a("0fd9b"),O=Object(g["a"])(v,c,u,!1,null,null,null),$=O.exports;y()(O,{VBtn:_["a"],VCard:x["a"],VCardActions:S["a"],VCardText:S["c"],VCheckbox:w["a"],VCol:k["a"],VDivider:F["a"],VRow:C["a"]});var E=a("02cb"),D=a("0549"),A=a("a51f"),V=a("8113"),j={components:{SendKaarAppraisalForm:$,KaarAppraisalForms:d["a"],VueUser:E["default"],VuePageWrapper:D["default"],DataTableNoData:A["default"],PaFilters:V["default"]},mixins:[s["a"],o["a"]],data:function(){return{htmlTitle:"Forms | Frequency and Mode | Settings | Key Achievement And Rating | Admin",breadCrumbItems:[{text:"Key Achievement And Rating",disabled:!1,to:{name:"admin-slug-pa-overview",params:{slug:this.$route.params.slug}}},{text:"Settings",disabled:!1,to:{name:"admin-slug-pa-settings",params:{slug:this.$route.params.slug}}},{text:"Frequency and Mode",disabled:!1,to:{name:"admin-slug-pa-settings-frequency-and-mode",params:{slug:this.$route.params.slug}}},{text:"Forms",disabled:!0}],showFilter:!1,paFilter:{},heading:[{text:"Name",value:"name"},{text:"Self Appraisal",value:"",sortable:!1,align:"center"},{text:"Supervisor Appraisal",value:"",sortable:!1,align:"center"},{text:"Reviewer Evaluation",value:"",sortable:!1,align:"center"}],confirmReGenerate:{dialog:!1,heading:"Confirm ReGenerate",subheading:"You are about to regenerate the forms. Confirm your action.",text:"Are you sure you want to regenerate the forms ?"},confirmGenerate:{dialog:!1,heading:"Confirm Generate",subheading:"You are about to generate the forms. Confirm your action.",text:"Are you sure you want to generate the forms ?"},showIndividualForm:!1,sendForm:!1,appraiserConfigId:"",selectedAppraiserType:""}},computed:{dataTableFilter:function(){return Object(n["a"])({},this.paFilter)},generateForm:function(){return!!this.response&&"not_generated"==this.response.question_status}},created:function(){this.dataTableEndpoint=l["a"].getKaarAppraiseeFormsCount(this.getOrganizationSlug,this.$route.params.id)},methods:{reGenerate:function(){var e=this;this.crud.message="Successfully ".concat(this.generateForm?"Generated":"Re-Generated"," forms."),this.insertData(l["a"].generateKaarAppraiseeForms(this.getOrganizationSlug,this.$route.params.id)).then((function(){e.fetchDataTable()})).finally((function(){e.generateForm?e.confirmGenerate.dialog=!1:e.confirmReGenerate.dialog=!1}))},viewQuestionSet:function(e,t){0!=t.count&&t.appraiser_config_id&&(this.showIndividualForm=!e,this.appraiserConfigId=t.appraiser_config_id)},refresh:function(){this.showIndividualForm=!1,this.fetchDataTable()}}},B=j,I=a("8fea"),R=a("169a"),T=a("132d"),z=a("0789"),L=Object(g["a"])(B,i,r,!1,null,null,null);t["default"]=L.exports;y()(L,{VBtn:_["a"],VCard:x["a"],VDataTable:I["a"],VDialog:R["a"],VDivider:F["a"],VIcon:T["a"],VSlideYTransition:z["g"]})}}]);