(window["webpackJsonp"]=window["webpackJsonp"]||[]).push([["pages/external-user/prescreeninginterview"],{a687:function(e,t,n){"use strict";n.r(t);var i=function(){var e=this,t=e.$createElement,n=e._self._c||t;return n("v-card",[n("vue-card-title",{attrs:{title:"Preliminary Screening Interview Evaluation Form for "+e.jobTitle,subtitle:"Here you can evaluate candidate.",icon:"mdi-file-document-outline",dark:""}}),n("v-divider"),n("v-card-text",{staticClass:"pa-0"},[n("score-card",{attrs:{"score-mode":"",endpoint:e.questionEndpoint,"viewer-id":e.$route.params.interviewerId,"job-title":e.jobTitle,external:"","recruitment-stage":"prescreening interview"},on:{"update:jobTitle":function(t){e.jobTitle=t},"update:job-title":function(t){e.jobTitle=t}}})],1)],1)},r=[],a=(n("99af"),n("d5d7")),o={components:{ScoreCard:a["a"]},data:function(){return{questionEndpoint:"",jobTitle:""}},created:function(){this.questionEndpoint="/recruitment/pre-screening-interview/interviewer/".concat(this.$route.params.interviewerId,"/answer/").concat(this.$route.params.questionId,"/")}},c=o,d=n("2877"),s=n("6544"),u=n.n(s),l=n("b0af"),p=n("99d9"),v=n("ce7e"),w=Object(d["a"])(c,i,r,!1,null,null,null);t["default"]=w.exports;u()(w,{VCard:l["a"],VCardText:p["c"],VDivider:v["a"]})}}]);