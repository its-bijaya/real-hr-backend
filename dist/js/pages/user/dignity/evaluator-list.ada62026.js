(window["webpackJsonp"]=window["webpackJsonp"]||[]).push([["pages/user/dignity/evaluator-list"],{cd49:function(t,a,e){"use strict";e.r(a);var i=function(){var t=this,a=t.$createElement,e=t._self._c||a;return e("vue-page-wrapper",{attrs:{title:t.htmlTitle,"bread-crumbs":t.breadCrumbItems}},[e("v-card",{attrs:{height:"auto"}},[e("vue-card-title",{attrs:{title:"List of Evaluators",subtitle:"These are the list of evaluators.",icon:"mdi-format-list-bulleted"}},[e("template",{slot:"actions"},[e("v-btn",{attrs:{small:"",color:"primary",depressed:""},on:{click:function(a){t.addEvaluator=!0}}},[t._v(" Add new evaluator ")]),e("v-btn",{attrs:{icon:""},on:{click:function(a){t.filters.show=!t.filters.show}}},[e("v-icon",{attrs:{small:""},domProps:{textContent:t._s("mdi-filter-variant")}})],1)],1)],2),e("v-divider"),e("v-slide-y-transition",{directives:[{name:"show",rawName:"v-show",value:t.filters.show,expression:"filters.show"}]},[t.filters.show?e("v-row",{staticClass:"px-2 py-0"},[e("v-col",[e("v-text-field",{attrs:{value:t.filters.search,label:"Search","prepend-inner-icon":"mdi-magnify"},on:{change:function(a){t.filters.search=a}}})],1)],1):t._e()],1),t.filters.show?e("v-divider"):t._e(),e("v-data-table",{attrs:{headers:t.headers,items:t.fetchedResults,"sort-desc":t.pagination.descending,"sort-by":t.pagination.sortBy,page:t.pagination.page,"items-per-page":t.pagination.rowsPerPage,"footer-props":t.footerProps,"server-items-length":t.pagination.totalItems,"must-sort":"","mobile-breakpoint":0},on:{"update:sortDesc":function(a){return t.$set(t.pagination,"descending",a)},"update:sort-desc":function(a){return t.$set(t.pagination,"descending",a)},"update:sortBy":function(a){return t.$set(t.pagination,"sortBy",a)},"update:sort-by":function(a){return t.$set(t.pagination,"sortBy",a)},"update:page":function(a){return t.$set(t.pagination,"page",a)},"update:itemsPerPage":function(a){return t.$set(t.pagination,"rowsPerPage",a)},"update:items-per-page":function(a){return t.$set(t.pagination,"rowsPerPage",a)}},scopedSlots:t._u([{key:"item",fn:function(a){return[e("tr",[e("td",[e("div",{staticClass:"text--lighten-5"},[t._v(" "+t._s(t._f("truncate")(a.item.dignity_appraisal.title,25))+" ")])]),e("td",[e("v-chip",[t._v(" "+t._s(a.item.internal_users_count)+" ")])],1),e("td",[e("v-chip",[t._v(" "+t._s(a.item.external_users_count)+" ")])],1)])]}}])},[e("template",{slot:"no-data"},[e("no-data-found",{attrs:{loading:t.loading}})],1)],2)],1),t.addEvaluator?e("v-dialog",{attrs:{width:"960",scrollable:"",presistent:""},on:{keydown:function(a){if(!a.type.indexOf("key")&&t._k(a.keyCode,"esc",27,a.key,["Esc","Escape"]))return null;t.addEvaluator=!1}},model:{value:t.addEvaluator,callback:function(a){t.addEvaluator=a},expression:"addEvaluator"}},[t.addEvaluator?e("evaluator-form",{attrs:{"action-data":t.actionData},on:{close:function(a){t.addEvaluator=!1,t.actionData={},t.fetchDataTable()}}}):t._e()],1):t._e(),e("v-dialog",{attrs:{width:"500",scrollable:"",persistent:""},model:{value:t.showList,callback:function(a){t.showList=a},expression:"showList"}},[e("show-list-dialog",{attrs:{title:t.titleList,subtitle:t.subTitle,items:t.externalEvaluatorList,"header-name":t.headerName},on:{close:function(a){t.showList=a}}})],1),e("user-list-dialog",{attrs:{users:t.internalEvaluatorList,title:"Internal Evaluator"},on:{close:function(a){t.showUsersList=!1,t.internalEvaluatorList=[]}},model:{value:t.showUsersList,callback:function(a){t.showUsersList=a},expression:"showUsersList"}})],1)},s=[],r=(e("ac1f"),e("841c"),e("d3b7"),e("0549")),n=e("dac4"),o=e("17cc"),l=e("c44a"),d=e("a51f"),u=e("dd34"),c=e("9815"),p=e("68c3"),f={components:{showListDialog:p["a"],UserListDialog:c["default"],NoDataFound:d["default"],EvaluatorForm:n["a"],VuePageWrapper:r["default"]},mixins:[o["a"],l["a"]],data:function(){return{isHrAdmin:!0,htmlTitle:"Goal Period | Dignity | Admin",breadCrumbItems:[{text:"Evaluators",disabled:!0}],addEvaluator:!1,activeEvaluator:0,viewDetail:!1,loading:!1,filters:{show:!1,search:"",startDateFilter:{},finishDateFilter:{}},headers:[{text:"Appraisal Cycle",sortable:!0,value:"title"},{text:"Internal",sortable:!1},{text:"External",sortable:!1}],actionData:{},userDetail:"",statusColor:{Pending:"orange",Rejected:"red",Accepted:"purple",Confirmed:"blue"},internalEvaluatorList:[],showUsersList:!1,headerName:"",title:"",subtitle:"",externalEvaluatorList:[],showList:!1,subTitle:"",titleList:""}},computed:{DataTableFilter:function(){return{search:this.filters.search}}},watch:{params:function(){this.fetchDataTable()}},created:function(){this.loadDataTableChange()},methods:{editEvaluatorDetails:function(t){this.addEvaluator=!0,this.actionData=t},fetchDataTable:function(){var t=this;this.loading||(this.loading=!0,this.$http.get(u["a"].addEvaluator(this.getOrganizationSlug),{params:this.fullParams}).then((function(a){t.loadDataTable(a)})).finally((function(){t.loading=!1})))}}},h=f,v=e("2877"),g=e("6544"),m=e.n(g),b=e("8336"),w=e("b0af"),E=e("cc20"),D=e("62ad"),_=e("8fea"),y=e("169a"),x=e("ce7e"),L=e("132d"),k=e("0fd9b"),P=e("0789"),T=e("8654"),C=Object(v["a"])(h,i,s,!1,null,null,null);a["default"]=C.exports;m()(C,{VBtn:b["a"],VCard:w["a"],VChip:E["a"],VCol:D["a"],VDataTable:_["a"],VDialog:y["a"],VDivider:x["a"],VIcon:L["a"],VRow:k["a"],VSlideYTransition:P["g"],VTextField:T["a"]})}}]);