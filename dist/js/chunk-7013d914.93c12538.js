(window["webpackJsonp"]=window["webpackJsonp"]||[]).push([["chunk-7013d914"],{c121:function(e,t,n){"use strict";n("99af");t["a"]={getUserLeaveBalanceHistory:function(e,t,n){return"/leave/".concat(e,"/user-balance/").concat(t,"/").concat(n,"/history/")},getIndividualBalance:function(e){return"/leave/".concat(e,"/reports/individual-leave-balance/")},exportIndividualBalance:function(e){return"/leave/".concat(e,"/reports/individual-leave-balance/export/")},getUserLeaveBalance:function(e){return"/leave/".concat(e,"/user-balance/")},postUserLeaveBalance:function(e,t){return"/leave/".concat(e,"/user-balance/").concat(t,"/edit/")},getUserLeaveBalanceDetails:function(e,t){return"/leave/".concat(e,"/user-balance/").concat(t,"/")}}},ce0c:function(e,t,n){"use strict";n.d(t,"b",(function(){return r})),n.d(t,"c",(function(){return c})),n.d(t,"a",(function(){return o}));var a=n("3835");n("d3b7"),n("25f0"),n("ac1f"),n("1276");function r(e,t){if(!e&&0!==e)return"N/A";var n=parseInt(e/3600),a=parseInt(e%3600/60);return i(n,a,t)}function i(e,t,n){var a=t.toString().length<2&&t<10?"0":"",r=e.toString().length<2&&e<10?"0":"",i=a+t,c=r+e;return":"===n?c+":"+i:0===e?i+" Minutes":c+" Hours "+i+" Minutes"}function c(e){if(!e)return"N/A";if("00:00:00"===e)return"N/A";var t=e.split(":"),n=Object(a["a"])(t,3),r=n[0],i=n[1],c=n[2];return"00"===r&&"00"===i?c+" Seconds":"00"===r?i+" Minutes":r+" Hours "+i+" Minutes"}function o(e){if(isNaN(parseInt(e)))return"-";var t=parseInt(e/60);t.toString().length<2&&(t="0"+t.toString());var n=parseInt(e%60);return n.toString().length<2&&(n="0"+n.toString()),t+":"+n}},ce59:function(e,t,n){"use strict";n.r(t);var a=function(){var e=this,t=e.$createElement,n=e._self._c||t;return n("v-card",{attrs:{height:"100%"}},[n("vue-card-title",{attrs:{title:"Leaves",subtitle:"Leave Balance Information",icon:"mdi-calendar-remove-outline"}}),n("v-divider"),n("v-card-text",{staticClass:"py-0 scrollbar-sm"},[e.loading?n("div",e._l(2,(function(e){return n("list-loader",{key:e,attrs:{width:200,height:100}})})),1):n("div",[n("v-list",{staticClass:"py-0"},[e._l(e.leaveTypeInfo,(function(t,a){return[n("v-list-item",{key:a},[n("v-list-item-content",[n("div",{domProps:{textContent:e._s(t.leave_type.name)}})]),n("v-list-item-action",[n("div",[n("strong",{class:t.balance>0?"primary--text pointer":"red--text",domProps:{textContent:e._s(e.getLeaveBalance(t))},on:{click:function(t){return e.$router.push({name:"user-leave-request"})}}})])])],1),a!==e.leaveTypeInfo.length-1?n("v-divider",{key:"D-"+a}):e._e()]}))],2)],1)])],1)},r=[],i=n("1da1"),c=(n("96cf"),n("d3b7"),n("caad"),n("c121")),o=n("e330"),u=n("ce0c"),s={components:{ListLoader:o["d"]},data:function(){return{loading:!0,LeaveTypeInfo:{}}},created:function(){this.getLeaveOverview()},methods:{getLeaveOverview:function(){var e=this;return Object(i["a"])(regeneratorRuntime.mark((function t(){return regeneratorRuntime.wrap((function(t){while(1)switch(t.prev=t.next){case 0:e.loading=!0,e.$http.get(c["a"].getUserLeaveBalanceDetails(e.getOrganizationSlug,e.getAuthStateUserId)).then((function(t){e.leaveTypeInfo=t.results})).finally((function(){e.loading=!1}));case 2:case"end":return t.stop()}}),t)})))()},getLeaveBalance:function(e){return["Time Off","Credit Hour"].includes(e.leave_type.category)?Object(u["a"])(e.usable_balance):e.usable_balance}}},l=s,v=n("2877"),d=n("6544"),f=n.n(d),g=n("b0af"),p=n("99d9"),b=n("ce7e"),h=n("8860"),m=n("da13"),L=n("1800"),y=n("5d23"),I=Object(v["a"])(l,a,r,!1,null,null,null);t["default"]=I.exports;f()(I,{VCard:g["a"],VCardText:p["c"],VDivider:b["a"],VList:h["a"],VListItem:m["a"],VListItemAction:L["a"],VListItemContent:y["a"]})}}]);