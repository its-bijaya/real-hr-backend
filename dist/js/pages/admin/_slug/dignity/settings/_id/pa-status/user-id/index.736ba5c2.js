(window["webpackJsonp"]=window["webpackJsonp"]||[]).push([["pages/admin/_slug/dignity/settings/_id/pa-status/user-id/index"],{dda0:function(t,e,a){"use strict";a.r(e);var s=function(){var t=this,e=t.$createElement,a=t._self._c||e;return a("vue-page-wrapper",{attrs:{"bread-crumbs":t.breadCrumbItems,title:t.htmlTitle}},[a("v-card",[a("vue-card-title",{attrs:{title:"Form Submission Status of Appraiser",subtitle:"Here you can view forms of all employee.",icon:"mdi-account-check-outline"}},[a("template",{slot:"actions"},[a("v-btn",{attrs:{icon:""},on:{click:function(e){t.showFilter=!t.showFilter}}},[a("v-icon",{attrs:{small:""},domProps:{textContent:t._s("mdi-filter-variant")}})],1)],1)],2),a("v-divider"),a("v-slide-y-transition",[a("v-row",{directives:[{name:"show",rawName:"v-show",value:t.showFilter,expression:"showFilter"}],staticClass:"mx-3 py-0"},[a("v-col",{attrs:{md:"4",cols:"12"}},[a("vue-search",{attrs:{search:t.search},on:{"update:search":function(e){t.search=e}},model:{value:t.search,callback:function(e){t.search=e},expression:"search"}})],1)],1)],1),t.showFilter?a("v-divider"):t._e(),a("v-card-text",[a("vue-user",{attrs:{user:t.selectedAppraisee}})],1),a("v-divider"),a("v-tabs",{attrs:{"show-arrows":"","slider-color":"blue"},model:{value:t.activeStatus,callback:function(e){t.activeStatus=e},expression:"activeStatus"}},t._l(t.statusTabs,(function(e){return a("v-tab",{key:e.tabName,attrs:{ripple:"",disabled:t.loading}},[a("span",{staticClass:"pr-2 text-capitalize"},[t._v(" "+t._s(e.tabName)+" ")]),a("v-chip",{staticClass:"white--text",attrs:{color:e.color,small:""}},[t._v(" "+t._s(e.count)+" ")])],1)})),1),a("v-divider"),a("v-data-table",{attrs:{headers:t.heading,items:t.fetchedResults,"sort-desc":t.pagination.descending,"sort-by":t.pagination.sortBy,page:t.pagination.page,"items-per-page":t.pagination.rowsPerPage,"footer-props":t.footerProps,"server-items-length":t.pagination.totalItems,"mobile-breakpoint":0,"must-sort":""},on:{"update:sortDesc":function(e){return t.$set(t.pagination,"descending",e)},"update:sort-desc":function(e){return t.$set(t.pagination,"descending",e)},"update:sortBy":function(e){return t.$set(t.pagination,"sortBy",e)},"update:sort-by":function(e){return t.$set(t.pagination,"sortBy",e)},"update:page":function(e){return t.$set(t.pagination,"page",e)},"update:itemsPerPage":function(e){return t.$set(t.pagination,"rowsPerPage",e)},"update:items-per-page":function(e){return t.$set(t.pagination,"rowsPerPage",e)}},scopedSlots:t._u([{key:"item",fn:function(e){return[a("tr",[a("td",[a("vue-user",{attrs:{user:e.item.internal_user}})],1),a("td",{staticClass:"font-weight-bold blue--text",class:"Generated"!==e.item.form_status?"pointer":""},[a("div",[a("span",{on:{click:function(a){"Generated"!==e.item.form_status&&t.openQuestionDialog(e.item)}}},[t._v(" "+t._s(e.item.total_score||"N/A")+" ")])])])])]}}])},[a("template",{slot:"no-data"},[a("data-table-no-data",{attrs:{loading:t.loading}})],1)],2),a("v-dialog",{attrs:{width:"1000"},model:{value:t.viewQuestionSheet,callback:function(e){t.viewQuestionSheet=e},expression:"viewQuestionSheet"}},[t.viewQuestionSheet?a("view-question",{key:t.viewQuestionSheet,attrs:{as:"hr","selected-appraiser":t.selectedItem},on:{close:function(e){t.viewQuestionSheet=!1,t.fetchDataTable()}}}):t._e()],1)],1)],1)},i=[],n=(a("d3b7"),a("3ca3"),a("ddb0"),a("ac1f"),a("841c"),a("17cc")),r=a("a09e"),o=a("dd34"),u=a("3241"),l={components:{viewQuestion:u["a"],VueUser:function(){return Promise.resolve().then(a.bind(null,"02cb"))},VuePageWrapper:function(){return a.e("chunk-31f8a6e6").then(a.bind(null,"0549"))},DataTableNoData:function(){return a.e("chunk-26c51c79").then(a.bind(null,"a51f"))}},mixins:[r["a"],n["a"]],data:function(){return{htmlTitle:"Individual Status | Status | Appraisal Settings | Settings | Dignity | Admin",breadCrumbItems:[{text:"Settings",disabled:!1,to:{name:"admin-slug-dignity-settings",params:{slug:this.$route.params.slug}}},{text:"Appraisal Settings",disabled:!1,to:{name:"admin-slug-dignity-appraisal-setting",params:{slug:this.$route.params.slug}}},{text:"Status",disabled:!1,to:{name:"admin-slug-dignity-settings-id-formSubmissionStatus",params:{slug:this.$route.params.slug}}},{text:"Individual Status",disabled:!0}],mode:"",heading:[{text:"Appraiser",value:"appraiser"},{text:"Score",value:"obtained_score"}],selectedAppraisee:null,loading:!1,showFilter:!1,viewQuestionSheet:!1,selectedItem:{},individualAppraisers:[],search:"",actionData:{},activeStatus:0,activeAppraisalStatus:0,formStatus:"",statusTabs:[{tabName:"Generated",value:"Generated",count:"0",color:"orange",index:""},{tabName:"Sent",value:"Received",count:"0",color:"red",index:""},{tabName:"Completed",value:"Submitted",count:"0",color:"green",index:""},{tabName:"All",value:"",count:"0",color:"blue",index:""}]}},computed:{DataTableFilter:function(){return{as:"hr",search:this.search,form_status:this.statusTabs[this.activeStatus].value,user_type:"Internal",appraisee:this.$route.params.user_id}}},watch:{params:function(){this.fetchDataTable()}},created:function(){this.loadDataTableChange()},methods:{fetchDataTable:function(){var t=this;this.loading||(this.loading=!0,this.$http.get(o["a"].getAppraiser(this.getOrganizationSlug,this.$route.params.id)+"?as=hr&user_type=Internal",{params:this.fullParams}).then((function(e){t.loadDataTable(e),t.individualAppraisers=e.results,t.processAfterTableLoad(e)})).finally((function(){t.loading=!1})))},processAfterTableLoad:function(t){var e=t.stats;this.statusTabs[0].count=e["Generated"],this.statusTabs[1].count=e["Received"],this.statusTabs[2].count=e["Submitted"],this.statusTabs[3].count=e["All"],this.selectedAppraisee=this.fetchedResults.length?this.fetchedResults[0].individual_appraisal.appraisee:null},openQuestionDialog:function(t){this.viewQuestionSheet=!0,this.selectedItem=t,this.$emit("closeList")}}},d=l,c=a("2877"),p=a("6544"),h=a.n(p),m=a("8336"),g=a("b0af"),v=a("99d9"),b=a("cc20"),f=a("62ad"),w=a("8fea"),S=a("169a"),_=a("ce7e"),x=a("132d"),T=a("0fd9b"),y=a("0789"),A=a("71a3"),D=a("fe57"),V=Object(c["a"])(d,s,i,!1,null,null,null);e["default"]=V.exports;h()(V,{VBtn:m["a"],VCard:g["a"],VCardText:v["c"],VChip:b["a"],VCol:f["a"],VDataTable:w["a"],VDialog:S["a"],VDivider:_["a"],VIcon:x["a"],VRow:T["a"],VSlideYTransition:y["g"],VTab:A["a"],VTabs:D["a"]})}}]);