(window["webpackJsonp"]=window["webpackJsonp"]||[]).push([["pages/admin/_slug/attendance/attendance-import"],{f00a:function(t,e,a){"use strict";a.r(e);var n=function(){var t=this,e=t.$createElement,a=t._self._c||e;return a("vue-page-wrapper",{attrs:{title:t.htmlTitle,"bread-crumbs":t.breadCrumbItems}},[a("import-form",{attrs:{heading:t.heading,"sample-endpoint":t.sampleEndpoint,endpoint:t.endpoint,"redirect-to":t.redirectName,"refresh-route":"admin-slug-attendance-import-attendance"}})],1)},r=[],d=a("0549"),i=a("926d5"),s={components:{ImportForm:i["a"],VuePageWrapper:d["default"]},data:function(){return{htmlTitle:"Import | Attendance | Admin",breadCrumbItems:[{text:"Attendance",disabled:!1,to:{name:"admin-slug-attendance-overview",params:{slug:this.$route.params.slug}}},{text:"Import",disabled:!1,to:{name:"admin-slug-attendance-import",params:{slug:this.$route.params.slug}}},{text:"Import Attendance",disabled:!0}],heading:{title:"Import Attendance",subtitle:"Import bulk attendance for employee."},endpoint:"",sampleEndpoint:"",redirectName:"admin-slug-attendance-reports-individual"}},created:function(){this.endpoint="/attendance/".concat(this.$route.params.slug,"/import/"),this.sampleEndpoint="/attendance/".concat(this.$route.params.slug,"/import/sample/")}},o=s,p=a("2877"),m=Object(p["a"])(o,n,r,!1,null,null,null);e["default"]=m.exports}}]);