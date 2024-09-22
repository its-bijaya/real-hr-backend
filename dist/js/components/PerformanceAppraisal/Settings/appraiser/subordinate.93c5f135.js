(window["webpackJsonp"]=window["webpackJsonp"]||[]).push([["/components/PerformanceAppraisal/Settings/appraiser/subordinate"],{"8cd3":function(e,t,n){"use strict";var i=n("5530"),a=(n("d3b7"),n("f0d5"));t["a"]={mixins:[a["a"]],data:function(){return{dataTableEndpoint:"",fetchedResults:[],response:null,footerProps:{itemsPerPageOptions:[10,20,30,40,50,100]},pagination:{sortBy:["modified_at"],descending:!1,totalItems:0,page:1,rowsPerPage:10,pageCount:0},loadTableOnInit:!0}},computed:{filterParams:function(){var e=Object(i["a"])(Object(i["a"])({},this.dataTableFilter),{},{offset:(this.pagination.page-1)*this.pagination.rowsPerPage,limit:this.pagination.rowsPerPage,ordering:this.pagination.descending?this.pagination.sortBy:"-"+this.pagination.sortBy});return this.convertToURLSearchParams(e,!1)}},watch:{filterParams:function(){var e=this;this.$nextTick((function(){e.fetchDataTable()}))},dataTableFilter:function(){this.pagination.page=1}},created:function(){var e=this;setTimeout((function(){e.loadTableOnInit&&e.fetchDataTable()}),0)},methods:{fetchDataTable:function(e,t){var n=this;return new Promise((function(i,a){!e&&!n.dataTableEndpoint||n.loading||(n.loadTableOnInit=!1,n.loading=!0,n.fetchedResults=[],n.$http.get(e||n.dataTableEndpoint,t||{params:n.filterParams}).then((function(e){n.response=e,n.fetchedResults=e.results,n.pagination.totalItems=e.count,n.processAfterTableLoad(e),i(e),n.loading=!1})).catch((function(e){n.pushErrors(e),n.notifyInvalidFormResponse(),a(e),n.loading=!1})))}))},processAfterTableLoad:function(){}}}},ac59:function(e,t,n){"use strict";n.r(t);var i=function(){var e=this,t=e.$createElement,n=e._self._c||t;return n("v-card",[n("vue-card-title",{attrs:{title:"Subordinates Appraisal",subtitle:"Here you can view/edit subordinates appraisal",icon:"mdi-account-check-outline"}},[n("template",{slot:"actions"},[n("v-btn",{attrs:{small:"",depressed:"",color:"primary"},on:{click:function(t){e.displayBulkForm=!0}}},[e._v(" Bulk Assign ")]),n("v-btn",{attrs:{icon:""},on:{click:function(t){e.showFilter=!e.showFilter}}},[n("v-icon",{attrs:{small:""},domProps:{textContent:e._s("mdi-filter-variant")}})],1)],1)],2),n("v-divider"),n("v-slide-y-transition",[n("div",{directives:[{name:"show",rawName:"v-show",value:e.showFilter,expression:"showFilter"}]},[n("pa-filters",{on:{filter:function(t){e.paFilter=t}}})],1)]),e.showFilter?n("v-divider"):e._e(),n("v-data-table",{attrs:{headers:e.heading,items:e.fetchedResults,"sort-desc":e.pagination.descending,"sort-by":e.pagination.sortBy,page:e.pagination.page,"items-per-page":e.pagination.rowsPerPage,"footer-props":e.footerProps,"server-items-length":e.pagination.totalItems,"mobile-breakpoint":0,"single-expand":"","must-sort":""},on:{"update:sortDesc":function(t){return e.$set(e.pagination,"descending",t)},"update:sort-desc":function(t){return e.$set(e.pagination,"descending",t)},"update:sortBy":function(t){return e.$set(e.pagination,"sortBy",t)},"update:sort-by":function(t){return e.$set(e.pagination,"sortBy",t)},"update:page":function(t){return e.$set(e.pagination,"page",t)},"update:itemsPerPage":function(t){return e.$set(e.pagination,"rowsPerPage",t)},"update:items-per-page":function(t){return e.$set(e.pagination,"rowsPerPage",t)}},scopedSlots:e._u([{key:"item",fn:function(t){return[n("tr",[n("td",[n("vue-user",{attrs:{user:t.item}})],1),n("td",[n("div",{on:{click:function(n){e.selectedUser=t.item.subordinates.first_level.users,e.showUsersList=!0}}},[n("thumbnail-users",{attrs:{users:t.item.subordinates.first_level.users,"total-users":t.item.subordinates.first_level.total_selected_users}})],1)]),n("td",[n("div",{on:{click:function(n){e.selectedUser=t.item.subordinates.second_level.users,e.showUsersList=!0}}},[n("thumbnail-users",{attrs:{users:t.item.subordinates.second_level.users,"total-users":t.item.subordinates.second_level.total_selected_users}})],1)]),n("td",[n("div",{on:{click:function(n){e.selectedUser=t.item.subordinates.third_level.users,e.showUsersList=!0}}},[n("thumbnail-users",{attrs:{users:t.item.subordinates.third_level.users,"total-users":t.item.subordinates.third_level.total_selected_users}})],1)]),n("td",{attrs:{align:"center"}},[n("vue-context-menu",{attrs:{"context-list":[{name:"Edit 1st Level Subordinates",icon:"mdi-pencil-outline",color:"info"},{name:"Edit 2nd Level Subordinates",icon:"mdi-pencil-outline",color:"info"},{name:"Edit 3rd Level Subordinates",icon:"mdi-pencil-outline",color:"info"}]},on:{click0:function(n){return e.editSubordinates(t.item,"1")},click1:function(n){return e.editSubordinates(t.item,"2")},click2:function(n){return e.editSubordinates(t.item,"3")}}})],1)])]}}])},[n("template",{slot:"no-data"},[n("data-table-no-data",{attrs:{loading:e.loading}})],1)],2),e.displayForm?n("v-dialog",{attrs:{width:"960",scrollable:"",presistent:""},on:{keydown:function(t){if(!t.type.indexOf("key")&&e._k(t.keyCode,"esc",27,t.key,["Esc","Escape"]))return null;e.displayForm=!1}},model:{value:e.displayForm,callback:function(t){e.displayForm=t},expression:"displayForm"}},[e.displayForm?n("edit-subordinates-form",{attrs:{"action-data":e.actionData,level:e.level,"appraisal-id":e.appraisalId},on:{create:function(t){e.displayForm=!1,e.fetchDataTable()},close:function(t){e.displayForm=!1}}}):e._e()],1):e._e(),e.displayBulkForm?n("v-dialog",{attrs:{width:"720",scrollable:"",presistent:""},on:{keydown:function(t){if(!t.type.indexOf("key")&&e._k(t.keyCode,"esc",27,t.key,["Esc","Escape"]))return null;e.displayBulkForm=!1}},model:{value:e.displayBulkForm,callback:function(t){e.displayBulkForm=t},expression:"displayBulkForm"}},[e.displayBulkForm?n("bulk-assign-form",{attrs:{"appraisal-id":e.appraisalId,type:"Subordinate",params:e.filterParams},on:{close:function(t){e.displayBulkForm=!1,e.fetchDataTable()}}}):e._e()],1):e._e(),n("user-list-dialog",{attrs:{users:e.selectedUser,title:"All Subordinates"},on:{close:function(t){e.showUsersList=!1}},model:{value:e.showUsersList,callback:function(t){e.showUsersList=t},expression:"showUsersList"}})],1)},a=[],s=n("5530"),r=(n("d3b7"),n("3ca3"),n("ddb0"),n("a9e3"),n("8cd3")),o=n("a1b8"),l={components:{DataTableNoData:function(){return n.e("chunk-26c51c79").then(n.bind(null,"a51f"))},VueUser:function(){return Promise.resolve().then(n.bind(null,"02cb"))},UserListDialog:function(){return n.e("chunk-2d0e6279").then(n.bind(null,"9815"))},VueContextMenu:function(){return n.e("chunk-2d2259e9").then(n.bind(null,"e4bf"))},ThumbnailUsers:function(){return n.e("chunk-1b4245df").then(n.bind(null,"cde3"))},BulkAssignForm:function(){return n.e("chunk-ce775f50").then(n.bind(null,"8fbe"))},PaFilters:function(){return n.e("chunk-936ddf1a").then(n.bind(null,"8113"))},EditSubordinatesForm:function(){return n.e("chunk-45dc08da").then(n.bind(null,"90fd"))}},mixins:[r["a"]],props:{appraisalId:{type:[String,Number],required:!0}},data:function(){return{displayForm:!1,displayBulkForm:!1,actionData:{},showFilter:!1,paFilter:{},selectedUser:[],showUsersList:!1,heading:[{text:"Supervisor Name",value:"full_name"},{text:"1st Level Subordinates",sortable:!1},{text:"2nd Level Subordinates",sortable:!1},{text:"3rd Level Subordinates",sortable:!1},{text:"Actions",align:"center",sortable:!1}],level:""}},computed:{dataTableFilter:function(){return Object(s["a"])({},this.paFilter)}},created:function(){this.dataTableEndpoint=o["a"].getSubordinateAppraisalSettings(this.getOrganizationSlug,this.appraisalId)},methods:{editSubordinates:function(e,t){this.displayForm=!0,this.actionData=e,this.level=t}}},d=l,u=n("2877"),c=n("6544"),p=n.n(c),f=n("8336"),m=n("b0af"),b=n("8fea"),h=n("169a"),g=n("ce7e"),v=n("132d"),k=n("0789"),y=Object(u["a"])(d,i,a,!1,null,null,null);t["default"]=y.exports;p()(y,{VBtn:f["a"],VCard:m["a"],VDataTable:b["a"],VDialog:h["a"],VDivider:g["a"],VIcon:v["a"],VSlideYTransition:k["g"]})}}]);