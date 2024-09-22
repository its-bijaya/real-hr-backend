(window["webpackJsonp"]=window["webpackJsonp"]||[]).push([["pages/admin/_slug/pa/settings/assign-kpi~pages/user/pa/kpi/index~pages/user/supervisor/kpi/index","chunk-aee42bec"],{5102:function(e,t,i){"use strict";var a=function(){var e=this,t=e.$createElement,i=e._self._c||t;return i("v-card",[i("vue-card-title",{attrs:{title:"Assign Individual KPI",subtitle:"Here you can "+(e.editDialog?"update":"create")+" Individual KPI.",icon:"mdi-file-document-outline",dark:"",closable:""},on:{close:function(t){return e.$emit("close")}}}),i("v-divider"),i("v-card-text",{style:e.cardTextStyle},[e.nonFieldErrors?i("non-field-form-errors",{attrs:{"non-field-errors":e.nonFieldErrors}}):e._e(),i("v-row",{staticClass:"mx-3",attrs:{align:"center"}},[i("v-col",{attrs:{md:"3",cols:"12"}},[i("v-text-field",e._b({directives:[{name:"validate",rawName:"v-validate",value:"required",expression:"'required'"}],model:{value:e.formValues.title,callback:function(t){e.$set(e.formValues,"title",t)},expression:"formValues.title"}},"v-text-field",e.veeValidate("title","Title*"),!1))],1),i("v-col",{attrs:{md:"3",cols:"12"}},[i("vue-users-auto-complete",e._b({attrs:{params:e.getParams,disabled:e.disableVueUserAutoComplete,readonly:e.disableVueUserAutoComplete},model:{value:e.userId,callback:function(t){e.userId=t},expression:"userId"}},"vue-users-auto-complete",e.veeValidate("user","Employee Name*"),!1))],1),e.isNormalUser?e._e():i("v-col",{attrs:{md:"3",cols:"12"}},[i("VueDynamicUserFieldAutoComplete",e._b({attrs:{params:e.getParams,disabled:e.disableVueDynamicAutoComplete,readonly:e.disableVueDynamicAutoComplete,field:"username"},model:{value:e.username,callback:function(t){e.username=t},expression:"username"}},"VueDynamicUserFieldAutoComplete",e.veeValidate("username","Username"),!1))],1),i("v-col",{attrs:{md:"3",cols:"12"}},[i("vue-auto-complete",e._b({directives:[{name:"validate",rawName:"v-validate",value:"required",expression:"'required'"}],attrs:{endpoint:e.fiscalYearEndpoint,"item-value":"id","item-text":"name",disabled:e.isNormalUser,readonly:e.isNormalUser},model:{value:e.formValues.fiscal_year,callback:function(t){e.$set(e.formValues,"fiscal_year",t)},expression:"formValues.fiscal_year"}},"vue-auto-complete",e.veeValidate("fiscal_year","Fiscal Year*"),!1))],1),i("v-col",{attrs:{md:"3",cols:"12"}},[i("vue-auto-complete",{attrs:{endpoint:e.jobTitleEndpoint,label:"Filter KPI by Job Title","item-text":"title","item-value":"slug",disabled:!e.userId&&!e.username},model:{value:e.formValues.job_title,callback:function(t){e.$set(e.formValues,"job_title",t)},expression:"formValues.job_title"}})],1)],1),e.kpiTitles.length?e._l(e.kpiTitles,(function(t,a){return i("v-row",{key:a,staticClass:"px-3",attrs:{"no-gutters":""}},[i("v-col",{attrs:{md:"2",cols:"12"}},[i("v-checkbox",{attrs:{label:t.title},model:{value:t["add_kpi"],callback:function(i){e.$set(t,"add_kpi",i)},expression:"item['add_kpi']"}})],1),t.add_kpi?i("v-col",{attrs:{md:"8",cols:"12"}},[i("v-textarea",{attrs:{label:"Success Criteria",value:t.success_criteria,outlined:""},model:{value:t["success_criteria"],callback:function(i){e.$set(t,"success_criteria",i)},expression:"item['success_criteria']"}})],1):e._e(),t.add_kpi?i("v-col",{attrs:{md:"2",cols:"12"}},[i("v-row",{attrs:{justify:"end"}},[i("v-col",{attrs:{md:"8",cols:"12"}},[i("v-text-field",{attrs:{type:"number",label:"Weightage",min:0,max:100},model:{value:t["weightage"],callback:function(i){e.$set(t,"weightage",i)},expression:"item['weightage']"}})],1)],1)],1):e._e()],1)})):e._e(),i("v-card-actions",[i("v-row",{attrs:{"no-gutters":""}},[i("v-col",{staticClass:"text-right"},[i("v-btn",{staticClass:"black--text",attrs:{text:""},on:{click:function(t){return e.$emit("close")}}},[e._v("Cancel")]),e.editDialog?i("v-btn",{attrs:{small:"",depressed:"",color:"primary"},on:{click:function(t){return e.updateIndividualKpi()}}},[e._v(e._s(e.isNormalUser?"Submit":"Update"))]):i("v-btn",{attrs:{small:"",depressed:"",color:"primary"},on:{click:function(t){return e.CreateIndividualKpi()}}},[e._v(" "+e._s(e.isNormalUser?"Submit":"Save")+" ")])],1)],1)],1)],2)],1)},s=[],r=i("2909"),n=i("5530"),l=(i("caad"),i("b64b"),i("d81d"),i("4de4"),i("2532"),i("99af"),i("ef8c")),o=i("edc2"),u=i("8cd3"),c=i("5660"),d=i("51d8"),m=i("be30"),p=i("ab8a"),f=i("2f62"),h=i("86eb"),v={name:"individualKpi",components:{VueAutoComplete:c["default"],VueUsersAutoComplete:l["default"],VueDynamicUserFieldAutoComplete:o["a"],NonFieldFormErrors:p["default"]},mixins:[u["a"]],props:{IndividualKpiItem:{type:Object},editDialog:{type:Boolean},as:{type:String,default:""}},data:function(){return{formValues:{title:"",user:"",fiscal_year:"",other_kpi:[]},username:"",userId:"",fiscalYearEndpoint:"",kpiTitles:[],otherItems:[],disableDynamicAutoComplete:!1,disableUserAutoComplete:!1,jobTitleEndpoint:"",defaultKpis:[]}},computed:Object(n["a"])(Object(n["a"])({},Object(f["c"])({getSupervisorOrgSlug:"supervisor/getOrganizationSlug"})),{},{getParams:function(){var e={organization:"hr"===this.as?this.getOrganizationSlug:this.getSupervisorOrgSlug,user_status:"current"};return"supervisor"===this.as&&(e["supervisor"]=this.getAuthStateUserId,e["immediate_subordinates"]=!0),e},cardTextStyle:function(){return{maxHeight:"80vh",overflowY:"auto","@media (max-width: 767px)":{maxHeight:"60vh"},"@media (min-width: 768px)":{maxHeight:"80vh"}}},isNormalUser:function(){return"user"===this.as},getStatus:function(){return this.isNormalUser?"Submitted":"Pending"},disableVueUserAutoComplete:function(){return!(!["Submitted","Confirmed"].includes(this.formValues.status)&&!this.isNormalUser)||this.disableUserAutoComplete},disableVueDynamicAutoComplete:function(){return!!["Submitted","Confirmed"].includes(this.formValues.status)||this.disableDynamicAutoComplete}}),watch:{userId:function(e,t){t&&(this.kpiTitles=[],this.disableDynamicAutoComplete=!1),e&&(this.getKpiTitle(e),this.disableDynamicAutoComplete=!0)},username:function(e,t){t&&(this.kpiTitles=[],this.disableUserAutoComplete=!1),e&&(this.getKpiTitle(e),this.disableUserAutoComplete=!0)},"formValues.job_title":function(){this.formValues.job_title?this.getFilteredKpis():this.getOtherKpi()}},created:function(){this.fiscalYearEndpoint=d["a"].getFiscalYear(this.getOrganizationSlug),this.jobTitleEndpoint=h["a"].getJobTitle(this.getOrganizationSlug),this.editDialog||Object.keys(this.IndividualKpiItem).length?(this.formValues=this.deepCopy(this.IndividualKpiItem),this.userId=this.formValues.user):this.formValues={};var e=this.deepCopy(this.IndividualKpiItem);Object.keys(e).length&&(this.kpiTitles=e.extended_individual_kpis.map((function(e){return{id:e.kpi.id,extended_kpi_id:e.id,title:e.kpi.title,add_kpi:!0,weightage:e.weightage,success_criteria:e.success_criteria}})))},methods:{setOtherKpis:function(e){var t,i=this;this.formValues.other_kpi=e,this.otherItems=this.$refs.otherKpis.$data.items;var a=this.otherItems.filter((function(t){return e.includes(t.id)&&-1===i.kpiTitles.indexOf(t)}));(t=this.kpiTitles).push.apply(t,Object(r["a"])(a))},CreateIndividualKpi:function(){var e=this;if(this.validateAllFields()){this.formValues.status=this.getStatus;var t=this.kpiTitles.filter((function(e){return e.add_kpi})).map((function(e){return{kpi:e.id,weightage:e.weightage,success_criteria:e.success_criteria}}));this.$http.post(m["a"].bulkCreateIndividualKpi(this.getOrganizationSlug),{individual_kpi:this.formValues,extended_kpi:t}).then((function(){e.notifyUser("Successfully created individual KPI","green"),e.$emit("refresh"),e.$emit("close")})).catch((function(t){e.notifyInvalidFormResponse(),e.pushIndexedErrors(t,"weightage",!0,"")}))}},getKpiTitle:function(e){var t=this;this.formValues.user=e,this.$http.get(m["a"].getKPITitles(this.getOrganizationSlug,e)).then((function(e){if(t.kpiTitles.length){var i=t.kpiTitles.map((function(e){return e.id}));t.kpiTitles=t.kpiTitles.concat(e.results.filter((function(e){if(!i.includes(e.id))return e})))}else t.kpiTitles=e.results;t.defaultKpis=e.results.map((function(e){return e.id}))})).catch((function(e){t.notifyInvalidFormResponse(),t.pushErrors(e)}))},updateIndividualKpi:function(){var e=this;this.formValues.status=this.getStatus;var t=this.kpiTitles.filter((function(e){return e.add_kpi})).map((function(t){return{kpi:t.id,individual_kpi:e.IndividualKpiItem.id,extended_kpi_id:t.extended_kpi_id?t.extended_kpi_id:null,weightage:t.weightage,success_criteria:t.success_criteria}}));this.$http.put(m["a"].bulkUpdateIndividualKpi(this.getOrganizationSlug,this.IndividualKpiItem.id)+"?as=".concat(this.as),{individual_kpi:this.formValues,extended_kpi:t}).then((function(){e.notifyUser("Successfully updated individual KPI","green"),e.$emit("refresh"),e.$emit("close")})).catch((function(t){e.notifyInvalidFormResponse(),e.pushErrors(t)}))},getOtherKpi:function(){var e=this;this.kpiTitles=this.kpiTitles.filter((function(t){if(t.add_kpi||e.defaultKpis.includes(t.id))return t}))},getFilteredKpis:function(){var e=this,t=m["a"].getKPIs(this.getOrganizationSlug);this.$http.get(t,{params:{userIds:this.userId||this.username,as:this.as,job_title:this.formValues.job_title?"".concat(this.formValues.job_title):"",other_kpis:!0}}).then((function(t){if(e.kpiTitles.length){var i=e.kpiTitles.map((function(e){return e.id}));e.kpiTitles=e.kpiTitles.concat(t.results.filter((function(e){if(!i.includes(e.id))return e})))}else e.kpiTitles=t.results}))}}},g=v,b=i("2877"),y=i("6544"),_=i.n(y),x=i("8336"),C=i("b0af"),I=i("99d9"),k=i("ac7c"),V=i("62ad"),D=i("ce7e"),w=i("0fd9b"),S=i("8654"),T=i("a844"),U=Object(b["a"])(g,a,s,!1,null,"0abc28aa",null);t["a"]=U.exports;_()(U,{VBtn:x["a"],VCard:C["a"],VCardActions:I["a"],VCardText:I["c"],VCheckbox:k["a"],VCol:V["a"],VDivider:D["a"],VRow:w["a"],VTextField:S["a"],VTextarea:T["a"]})},"51d8":function(e,t,i){"use strict";i("99af");t["a"]={getFiscalYear:function(e){return"/org/".concat(e,"/fiscal-year/")},postFiscalYear:function(e){return"/org/".concat(e,"/fiscal-year/")},getFiscalYearDetails:function(e,t){return"/org/".concat(e,"/fiscal-year/").concat(t,"/")},updateFiscalYear:function(e,t){return"/org/".concat(e,"/fiscal-year/").concat(t,"/")},deleteFiscalYear:function(e,t){return"/org/".concat(e,"/fiscal-year/").concat(t,"/")},exportRebate:function(e){return"/payroll/".concat(e,"/user-voluntary-rebates/export/")}}},edc2:function(e,t,i){"use strict";var a=function(){var e=this,t=e.$createElement,i=e._self._c||t;return i("div",[i("v-autocomplete",{class:e.appliedClass,attrs:{items:e.itemsSorted,loading:e.isLoading,"search-input":e.search,multiple:e.multiple,label:e.label,error:e.errorMessages.length>0,"error-messages":e.errorMessages,disabled:e.disabled,"prepend-inner-icon":e.prependInnerIcon,clearable:e.clearable&&!e.readonly,readonly:!!e.readonly,"hide-details":e.hideDetails,"data-cy":"input-user-autocomplete-"+e.dataCyVariable,placeholder:e.placeholder,"hide-selected":"","hide-no-data":"","item-text":e.field,"item-value":"id"},on:{"update:searchInput":function(t){e.search=t},"update:search-input":function(t){e.search=t},blur:function(t){return e.$emit("blur")}},scopedSlots:e._u([{key:"selection",fn:function(t){return[i("v-chip",{attrs:{"input-value":t.selected,close:(e.clearable||!e.clearable&&!e.multiple)&&!e.readonly,small:""},on:{"click:close":function(i){return e.remove(t.item)}}},[i("v-avatar",{attrs:{left:""}},[i("v-img",{attrs:{src:t.item.profile_picture,cover:""}})],1),e._v(" "+e._s(e._f("truncate")(t.item[e.field],e.truncate))+" ")],1)]}},{key:"item",fn:function(t){var a=t.item;return[i("v-list-item-avatar",[i("v-avatar",{attrs:{size:"30"}},[i("v-img",{attrs:{src:a.profile_picture,cover:""}})],1)],1),i("v-list-item-content",[i("v-list-item-title",[e._v(" "+e._s(e._f("truncate")(a[e.field],20))+" "),a.employee_code?[e._v(" ("+e._s(a.employee_code)+") ")]:e._e()],2),a.division?i("v-list-item-subtitle",{domProps:{textContent:e._s(a.division)}}):e._e()],1)]}}]),model:{value:e.selectedData,callback:function(t){e.selectedData=t},expression:"selectedData"}})],1)},s=[],r=i("53ca"),n=(i("a9e3"),i("ac1f"),i("841c"),i("4e827"),i("2ca0"),i("d81d"),i("a434"),i("d3b7"),i("159b"),i("7db0"),i("4de4"),i("caad"),i("2532"),i("fab2")),l=i("63ea"),o=i.n(l),u={props:{value:{type:[Number,String,Array,Object],required:!1,default:function(){return null}},dataCyVariable:{type:String,default:""},userObject:{type:[Object,Array],required:!1,default:function(){return{}}},params:{type:[Object,Array],required:!1,default:function(){return{}}},multiple:{type:Boolean,required:!1,default:!1},disabled:{type:Boolean,required:!1,default:!1},errorMessages:{type:[String,Array],default:function(){return[]}},label:{type:String,default:"Select Employee"},prependInnerIcon:{type:String,default:"mdi-account-plus-outline"},itemsToExclude:{type:[Array,Number],default:null},itemsToInclude:{type:[Array,Number],default:null},clearable:{type:Boolean,default:!0},readonly:{type:Boolean,default:!1},hideDetails:{type:Boolean,default:!1},appliedClass:{type:String,default:""},truncate:{type:Number,default:10},placeholder:{type:String,default:""},field:{type:String,default:"full_name"}},data:function(){return{isLoading:!1,items:[],allUsers:[],selectedData:null,search:null}},computed:{itemsSorted:function(){return this.sortBySearch(this.items,this.search?this.search.toLowerCase():"")}},watch:{value:{handler:function(e,t){!e&&t&&(this.selectedData="",this.populateInitialUsers()),!t&&e&&this.populateInitialUsers()},immediate:!0},search:function(e){!e||this.items.length>0||this.fetchUsers()},selectedData:function(e){this.search="",this.syncUserData(e),this.$emit("input",e)},itemsToExclude:function(){this.items=this.excludeRecord(this.allUsers)},itemsToInclude:function(){this.items=this.includeRecord(this.allUsers)},params:{handler:function(e,t){o()(e,t)||this.fetchUsers()},deep:!0}},methods:{sortBySearch:function(e,t){var i=this.field;return e.sort((function(e,a){return e[i].toLowerCase().startsWith(t)&&a[i].toLowerCase().startsWith(t)?e[i].toLowerCase().localeCompare(a[i].toLowerCase()):e[i].toLowerCase().startsWith(t)?-1:a[i].toLowerCase().startsWith(t)?1:e[i].toLowerCase().localeCompare(a[i].toLowerCase())}))},populateInitialUsers:function(){this.fetchUsers(this.value),Array.isArray(this.value)?"object"===Object(r["a"])(this.value[0])?this.selectedData=this.value.map((function(e){return e.user.id})):this.selectedData=this.value:null===this.value?this.selectedData="":"object"===Object(r["a"])(this.value)?this.selectedData=this.value.id:this.selectedData=this.value,this.$emit("input",this.selectedData)},remove:function(e){if(this.selectedData instanceof Object){var t=this.selectedData.indexOf(e.id);t>=0&&this.selectedData.splice(t,1),this.$emit("remove",e)}else this.selectedData=""},fetchUsers:function(e){var t=this;this.isLoading||(this.isLoading=!0,this.$http.get(n["a"].autocomplete,{params:this.params}).then((function(i){t.allUsers=i,t.itemsToExclude&&(i=t.excludeRecord(i)),t.itemsToInclude&&(i=t.includeRecord(i)),t.items=i,e&&t.syncUserData(e)})).finally((function(){return t.isLoading=!1})))},syncUserData:function(e){var t=this;if(e instanceof Array){var i=[];e.forEach((function(e){i.unshift(t.items.find((function(t){return t.id===e})))})),this.$emit("update:userObject",i)}else{var a=this.items.find((function(t){return t.id===e}));this.$emit("update:userObject",a)}},excludeRecord:function(e){var t=[];return"number"===typeof this.itemsToExclude?t.push(this.itemsToExclude):t=this.itemsToExclude,e.filter((function(e){return!t.includes(e.id)}))},includeRecord:function(e){var t=this;return e.filter((function(e){return t.itemsToInclude.includes(e.id)}))}}},c=u,d=i("2877"),m=i("6544"),p=i.n(m),f=i("c6a6"),h=i("8212"),v=i("cc20"),g=i("adda"),b=i("8270"),y=i("5d23"),_=Object(d["a"])(c,a,s,!1,null,null,null);t["a"]=_.exports;p()(_,{VAutocomplete:f["a"],VAvatar:h["a"],VChip:v["a"],VImg:g["a"],VListItemAvatar:b["a"],VListItemContent:y["a"],VListItemSubtitle:y["b"],VListItemTitle:y["c"]})},ef8c:function(e,t,i){"use strict";i.r(t);var a=function(){var e=this,t=e.$createElement,i=e._self._c||t;return i("div",[i("v-autocomplete",{class:e.appliedClass,attrs:{items:e.itemsSorted,loading:e.isLoading,"search-input":e.search,multiple:e.multiple,label:e.label,error:e.errorMessages.length>0,"error-messages":e.errorMessages,disabled:e.disabled,"prepend-inner-icon":e.prependInnerIcon,clearable:e.clearable&&!e.readonly,readonly:!!e.readonly,"hide-details":e.hideDetails,"data-cy":"input-user-autocomplete-"+e.dataCyVariable,placeholder:e.placeholder,"hide-selected":"","hide-no-data":"","item-text":"full_name","item-value":"id"},on:{"update:searchInput":function(t){e.search=t},"update:search-input":function(t){e.search=t},blur:function(t){return e.$emit("blur")}},scopedSlots:e._u([{key:"selection",fn:function(t){return[i("v-chip",{attrs:{"input-value":t.selected,close:(e.clearable||!e.clearable&&!e.multiple)&&!e.readonly,small:""},on:{"click:close":function(i){return e.remove(t.item)}}},[i("v-avatar",{attrs:{left:""}},[i("v-img",{attrs:{src:t.item.profile_picture,cover:""}})],1),e._v(" "+e._s(e._f("truncate")(t.item.full_name,e.truncate))+" ")],1)]}},{key:"item",fn:function(t){var a=t.item;return[i("v-list-item-avatar",[i("v-avatar",{attrs:{size:"30"}},[i("v-img",{attrs:{src:a.profile_picture,cover:""}})],1)],1),i("v-list-item-content",[i("v-list-item-title",[e._v(" "+e._s(e._f("truncate")(a.full_name,20))+" "),a.employee_code?i("span",[e._v("("+e._s(a.employee_code)+")")]):e._e()]),a.division?i("v-list-item-subtitle",{domProps:{textContent:e._s(a.division)}}):e._e()],1)]}}]),model:{value:e.selectedData,callback:function(t){e.selectedData=t},expression:"selectedData"}})],1)},s=[],r=i("53ca"),n=(i("a9e3"),i("ac1f"),i("841c"),i("4e827"),i("2ca0"),i("d81d"),i("a434"),i("d3b7"),i("159b"),i("7db0"),i("4de4"),i("caad"),i("2532"),i("fab2")),l=i("63ea"),o=i.n(l),u={props:{value:{type:[Number,String,Array,Object],required:!1,default:function(){return null}},dataCyVariable:{type:String,default:""},userObject:{type:[Object,Array],required:!1,default:function(){return{}}},params:{type:[Object,Array],required:!1,default:function(){return{}}},multiple:{type:Boolean,required:!1,default:!1},disabled:{type:Boolean,required:!1,default:!1},errorMessages:{type:[String,Array],default:function(){return[]}},label:{type:String,default:"Select Employee"},prependInnerIcon:{type:String,default:"mdi-account-plus-outline"},itemsToExclude:{type:[Array,Number],default:null},itemsToInclude:{type:[Array,Number],default:null},clearable:{type:Boolean,default:!0},readonly:{type:Boolean,default:!1},hideDetails:{type:Boolean,default:!1},appliedClass:{type:String,default:""},truncate:{type:Number,default:10},placeholder:{type:String,default:""}},data:function(){return{isLoading:!1,items:[],allUsers:[],selectedData:null,search:null}},computed:{itemsSorted:function(){return this.sortBySearch(this.items,this.search?this.search.toLowerCase():"")}},watch:{value:{handler:function(e,t){!e&&t&&(this.selectedData="",this.populateInitialUsers()),!t&&e&&this.populateInitialUsers()},immediate:!0},search:function(e){!e||this.items.length>0||this.fetchUsers()},selectedData:function(e){this.search="",this.syncUserData(e),this.$emit("input",e)},itemsToExclude:function(){this.items=this.excludeRecord(this.allUsers)},itemsToInclude:function(){this.items=this.includeRecord(this.allUsers)},params:{handler:function(e,t){o()(e,t)||this.fetchUsers()},deep:!0}},methods:{sortBySearch:function(e,t){return e.sort((function(e,i){return e.full_name.toLowerCase().startsWith(t)&&i.full_name.toLowerCase().startsWith(t)?e.full_name.toLowerCase().localeCompare(i.full_name.toLowerCase()):e.full_name.toLowerCase().startsWith(t)?-1:i.full_name.toLowerCase().startsWith(t)?1:e.full_name.toLowerCase().localeCompare(i.full_name.toLowerCase())}))},populateInitialUsers:function(){this.fetchUsers(this.value),Array.isArray(this.value)?"object"===Object(r["a"])(this.value[0])?this.selectedData=this.value.map((function(e){return e.user.id})):this.selectedData=this.value:null===this.value?this.selectedData="":"object"===Object(r["a"])(this.value)?this.selectedData=this.value.id:this.selectedData=this.value,this.$emit("input",this.selectedData)},remove:function(e){if(this.selectedData instanceof Object){var t=this.selectedData.indexOf(e.id);t>=0&&this.selectedData.splice(t,1),this.$emit("remove",e)}else this.selectedData=""},fetchUsers:function(e){var t=this;this.isLoading||(this.isLoading=!0,this.$http.get(n["a"].autocomplete,{params:this.params}).then((function(i){t.allUsers=i,t.itemsToExclude&&(i=t.excludeRecord(i)),t.itemsToInclude&&(i=t.includeRecord(i)),t.items=i,e&&t.syncUserData(e)})).finally((function(){return t.isLoading=!1})))},syncUserData:function(e){var t=this;if(e instanceof Array){var i=[];e.forEach((function(e){i.unshift(t.items.find((function(t){return t.id===e})))})),this.$emit("update:userObject",i)}else{var a=this.items.find((function(t){return t.id===e}));this.$emit("update:userObject",a)}},excludeRecord:function(e){var t=[];return"number"===typeof this.itemsToExclude?t.push(this.itemsToExclude):t=this.itemsToExclude,e.filter((function(e){return!t.includes(e.id)}))},includeRecord:function(e){var t=this;return e.filter((function(e){return t.itemsToInclude.includes(e.id)}))}}},c=u,d=i("2877"),m=i("6544"),p=i.n(m),f=i("c6a6"),h=i("8212"),v=i("cc20"),g=i("adda"),b=i("8270"),y=i("5d23"),_=Object(d["a"])(c,a,s,!1,null,null,null);t["default"]=_.exports;p()(_,{VAutocomplete:f["a"],VAvatar:h["a"],VChip:v["a"],VImg:g["a"],VListItemAvatar:b["a"],VListItemContent:y["a"],VListItemSubtitle:y["b"],VListItemTitle:y["c"]})},f008:function(e,t,i){"use strict";var a=function(){var e=this,t=e.$createElement,i=e._self._c||t;return i("v-card",[i("vue-card-title",{attrs:{title:"View Individual KPI",subtitle:"Here you can view Individual KPI",icon:"mdi-eye-outline",dark:"",closable:""},on:{close:function(t){return e.$emit("close")}}}),i("v-card-text",{staticStyle:{"max-height":"90vh","overflow-y":"auto"}},[i("v-row",{staticClass:"py-3 px-3",attrs:{"no-gutters":""}},[i("v-col",{attrs:{md:"4",cols:"12"}},[i("v-card-text",[i("div",{staticClass:"font-weight-medium"},[i("v-icon",{attrs:{small:""},domProps:{textContent:e._s("mdi-file-document-outline")}}),e._v(" Individual KPI Title: ")],1),i("div",{staticClass:"pl-5"},[e._v(" "+e._s(e.individualKpiDetails.title||"N/A")+" ")])])],1),i("v-col",{attrs:{md:"4",cols:"12"}},[i("v-card-text",[i("div",{staticClass:"font-weight-medium"},[i("v-icon",{attrs:{small:""},domProps:{textContent:e._s("mdi-account-check-outline")}}),e._v(" Assign To: ")],1),i("vue-user",{attrs:{user:e.individualKpiDetails.user}})],1)],1),i("v-col",{attrs:{md:"4",cols:"12"}},[i("v-card-text",[i("div",{staticClass:"font-weight-medium"},[i("v-icon",{attrs:{small:""},domProps:{textContent:e._s("mdi-calendar-month-outline")}}),e._v(" Fiscal Year: ")],1),i("div",{staticClass:"pl-5"},[e._v(" "+e._s(e.individualKpiDetails.fiscal_year.name||"N/A")+" ")])])],1),i("v-data-table",{staticClass:"py-0",attrs:{headers:e.headers,items:e.individualKpiDetails.extended_individual_kpis,"items-per-page":e.individualKpiDetails.extended_individual_kpis.length,"hide-default-footer":""},scopedSlots:e._u([{key:"item",fn:function(t){return[i("tr",[i("td",[i("span",{domProps:{textContent:e._s(t.item.kpi.title)}})]),i("td",{staticClass:"pa-4"},[i("span",{domProps:{textContent:e._s(t.item.success_criteria)}})]),i("td",[i("span",{domProps:{textContent:e._s(t.item.weightage)}})])])]}}])})],1),i("v-divider"),i("v-row",{staticClass:"my-4",attrs:{dense:"","no-gutters":"",justify:"center"}},[i("v-col",{staticClass:"text-center text-sm font-weight-bold blue--text",attrs:{cols:"12"},domProps:{textContent:e._s("Individual KPI History")}}),i("v-timeline",{staticClass:"py-0 my-0"},e._l(e.individualKpiDetails.histories,(function(t,a){return i("v-timeline-item",{key:a,attrs:{right:!0,color:"green","show-dot":"",small:""}},[i("v-card-text",{staticClass:"font-weight-medium",domProps:{textContent:e._s(t.remarks)}}),i("template",{slot:"opposite"},[i("v-card-text",[i("vue-user",{attrs:{user:t.created_by,clickable:!1}}),i("div",{staticClass:"font-weight-bold",domProps:{textContent:e._s(e.humanizeDate(t.created_at))}}),i("div",{domProps:{textContent:e._s(e.humanizeTime(t.created_at))}})],1)],1)],2)})),1)],1),i("v-divider"),e.showButton?i("v-card-actions",[i("v-spacer"),i("v-btn",{attrs:{color:"primary",disabled:["Acknowledged","Archived","Confirmed"].includes(e.individualKpiDetails.status)},on:{click:function(t){return e.submitOrConfirmKpi()}}},[e._v(" "+e._s(e.buttonText)+" ")])],1):e._e()],1)],1)},s=[],r=(i("caad"),i("be30")),n=i("8cd3"),l=i("02cb"),o={name:"IndividualKpiDetails",components:{VueUser:l["default"]},mixins:[n["a"]],props:{individualKpiDetails:{type:Object},showButton:{type:Boolean,default:!1},status:{type:String,default:"Submitted"},buttonText:{type:String,default:"Submit"},as:{type:String,default:""}},data:function(){return{headers:[{text:"KPI Title",value:"kpi.title",width:"30%"},{text:"Success Criteria",value:"success_criteria",width:"50%"},{text:"Weightage(%)",value:"weightage",width:"20%"}]}},methods:{submitOrConfirmKpi:function(){var e=this;["Pending","Submitted"].includes(this.individualKpiDetails.status)&&this.$http.patch(r["a"].updateIndividualKpi(this.getOrganizationSlug,this.individualKpiDetails.id)+"?as=".concat(this.as),{status:this.status}).then((function(){e.notifyUser("Successfully ".concat(e.status),"green"),e.$emit("close"),e.$emit("refresh")})).catch((function(t){e.notifyInvalidFormResponse(),e.pushErrors(t)}))},humanizeDate:function(e){return this.$dayjs(e).format("YYYY-MM-DD")},humanizeTime:function(e){var t=this.$dayjs(e).format("h:mm:ss a");return"Invalid date"===t?"N/A":t}}},u=o,c=i("2877"),d=i("6544"),m=i.n(d),p=i("8336"),f=i("b0af"),h=i("99d9"),v=i("62ad"),g=i("8fea"),b=i("ce7e"),y=i("132d"),_=i("0fd9b"),x=i("2fa4"),C=i("8414"),I=i("1e06"),k=Object(c["a"])(u,a,s,!1,null,"01240585",null);t["a"]=k.exports;m()(k,{VBtn:p["a"],VCard:f["a"],VCardActions:h["a"],VCardText:h["c"],VCol:v["a"],VDataTable:g["a"],VDivider:b["a"],VIcon:y["a"],VRow:_["a"],VSpacer:x["a"],VTimeline:C["a"],VTimelineItem:I["a"]})},fab2:function(e,t,i){"use strict";t["a"]={getUserList:"/users/",postUser:"/users/",autocomplete:"/users/autocomplete/",postImportUser:"/users/import/",downloadUserImportSample:function(e){return"/users/import/sample/?organization=".concat(e)},getUserDetail:function(e){return"/users/".concat(e,"/")},getInternalUserDetail:function(e){return"/users/".concat(e,"/internal-detail")},deleteUser:function(e){return"/users/".concat(e,"/")},updateUser:function(e){return"/users/".concat(e,"/")},changePassword:function(e){return"/users/".concat(e,"/change-password/")},getUserCV:function(e){return"/users/".concat(e,"/cv/")},getProfileCompleteness:function(e){return"users/".concat(e,"/profile-completeness/")}}}}]);