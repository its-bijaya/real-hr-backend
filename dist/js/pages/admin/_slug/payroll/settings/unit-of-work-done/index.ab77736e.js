(window["webpackJsonp"]=window["webpackJsonp"]||[]).push([["pages/admin/_slug/payroll/settings/unit-of-work-done/index","chunk-31f8a6e6"],{"0549":function(t,e,s){"use strict";s.r(e);var a=function(){var t=this,e=t.$createElement,s=t._self._c||e;return s("div",[s("v-row",{staticClass:"mb-3",attrs:{"no-gutters":""}},[t.breadCrumbs?s("v-col",{attrs:{cols:"12"}},[s("v-card",{attrs:{flat:""}},[s("v-breadcrumbs",{staticClass:"text-body-1 pa-2",class:{"text-caption pa-1":t.$vuetify.breakpoint.xs},attrs:{items:t.breadCrumbs},scopedSlots:t._u([{key:"item",fn:function(e){return[s("span",{class:e.item.disabled?"grey--text":"baseColor--text text--accent-2 pointer",domProps:{textContent:t._s(e.item.text)},on:{click:function(s){return t.$router.push(e.item.to)}}})]}}],null,!1,1670153796)},[s("v-icon",{attrs:{slot:"divider"},slot:"divider"},[t._v("mdi-chevron-right")])],1)],1)],1):t._e()],1),s("v-row",{attrs:{"no-gutters":""}},[s("v-col",{attrs:{cols:"12"}},[t._t("default")],2)],1)],1)},r=[],i=s("5530"),n=(s("ac1f"),s("1276"),s("b0c0"),s("2f62")),o={props:{title:{type:String,required:!0},breadCrumbs:{type:Array,default:function(){return[]}}},computed:Object(i["a"])({},Object(n["c"])({getOrganizationName:"organization/getOrganizationName",getSupervisorSwitchedOrganization:"supervisor/getSwitchedOrganization"})),mounted:function(){document.title="".concat(this.title," | RealHRsoft");var t=this.$route.params.slug?"admin-slug-dashboard":"root",e=this.$route.name.split("-"),s=this.getOrganizationName;this.getSupervisorSwitchedOrganization&&"user"===e[0]&&"supervisor"===e[1]&&(s=this.getSupervisorSwitchedOrganization.name),this.breadCrumbs.unshift({text:s,disabled:!1,to:{name:t,params:{slug:this.$route.params.slug}}})}},l=o,c=s("2877"),u=s("6544"),d=s.n(u),p=s("2bc5"),h=s("b0af"),m=s("62ad"),v=s("132d"),f=s("0fd9b"),g=Object(c["a"])(l,a,r,!1,null,null,null);e["default"]=g.exports;d()(g,{VBreadcrumbs:p["a"],VCard:h["a"],VCol:m["a"],VIcon:v["a"],VRow:f["a"]})},"0b75":function(t,e,s){"use strict";var a=function(){var t=this,e=t.$createElement,s=t._self._c||e;return s("v-card",{attrs:{height:"100%"}},[s("v-row",{attrs:{dense:""}},[s("v-col",{staticClass:"py-0 pt-2 px-5",attrs:{cols:"12"}},[s("v-text-field",{attrs:{placeholder:"Search","prepend-inner-icon":"mdi-magnify","hide-details":"",dense:""},model:{value:t.search,callback:function(e){t.search=e},expression:"search"}})],1)],1),s("v-card-text",[s("v-row",{staticClass:"text-center"},[0===t.searchedItems.length?s("v-col",{attrs:{cols:"12"}},[s("vue-no-data",{attrs:{text:t.noDataText}})],1):t._e(),t._l(t.searchedItems,(function(e,a){return[!t.verifyPermission(e.permission||"show",e.isCommon)||e.hide||t.hideMenu(t.parent,t.child,e.to.name.replace(t.textToReplace,""))?t._e():s("v-col",{key:a,attrs:{md:"4",sm:"6"}},[s("v-hover",{scopedSlots:t._u([{key:"default",fn:function(a){var r=a.hover;return s("v-card",{class:"elevation-"+(r?12:2),attrs:{to:e.to,"data-cy":"box-heading",height:"100%"}},[s("v-col",{staticClass:"primaryLight"},[s("v-icon",{attrs:{size:"40",color:"primary"}},[t._v(" "+t._s(e.icon)+" ")])],1),s("v-divider"),s("v-card-text",{staticClass:"white"},[s("div",{staticClass:"text-body-1"},[s("strong",[t._v(t._s(e.title))]),t.settingStatus?s("v-tooltip",{attrs:{top:""},scopedSlots:t._u([void 0===t.settingStatus[e.title]?{key:"activator",fn:function(e){var a=e.on;return[s("v-progress-circular",t._g({attrs:{indeterminate:"",size:"14",width:"2"}},a))]}}:{key:"activator",fn:function(a){var r=a.on;return[s("v-icon",t._g({attrs:{color:t.settingStatus[e.title]?"green":"red",size:"17"},domProps:{textContent:t._s(t.settingStatus[e.title]?"mdi-check-circle":"cancel")}},r))]}}],null,!0)},[s("span",{domProps:{textContent:t._s("Setting has "+(t.settingStatus[e.title]?"been configured.":"not been configured."))}})]):t._e()],1),s("p",{staticClass:"text-body-2 grey--text"},[t._v(" "+t._s(e.subtitle)+" ")])])],1)}}],null,!0)})],1)]}))],2)],1)],1)},r=[],i=(s("4de4"),s("caad"),s("2532"),s("ac1f"),s("841c"),s("a15b"),s("e585")),n={components:{VueNoData:i["default"]},props:{items:{type:Array,required:!0},noDataText:{type:String,default:"No Records Found."},settingStatus:{type:Object,default:void 0},parent:{type:String,default:void 0},child:{type:[String,Array],default:void 0}},data:function(){return{showFilters:!1,search:""}},computed:{searchedItems:function(){var t=this;return this.items.filter((function(e){return e.title.toLowerCase().includes(t.search.toLowerCase())}))},textToReplace:function(){return Array.isArray(this.child)?this.parent+"-"+this.child.join("-")+"-":this.parent+"-"+this.child+"-"}}},o=n,l=s("2877"),c=s("6544"),u=s.n(c),d=s("b0af"),p=s("99d9"),h=s("62ad"),m=s("ce7e"),v=s("ce87"),f=s("132d"),g=s("490a"),b=s("0fd9b"),y=s("8654"),x=s("3a2f"),_=Object(l["a"])(o,a,r,!1,null,null,null);e["a"]=_.exports;u()(_,{VCard:d["a"],VCardText:p["c"],VCol:h["a"],VDivider:m["a"],VHover:v["a"],VIcon:f["a"],VProgressCircular:g["a"],VRow:b["a"],VTextField:y["a"],VTooltip:x["a"]})},"2bc5":function(t,e,s){"use strict";var a=s("5530"),r=(s("a15b"),s("abd3"),s("ade3")),i=s("1c87"),n=s("58df"),o=Object(n["a"])(i["a"]).extend({name:"v-breadcrumbs-item",props:{activeClass:{type:String,default:"v-breadcrumbs__item--disabled"},ripple:{type:[Boolean,Object],default:!1}},computed:{classes:function(){return Object(r["a"])({"v-breadcrumbs__item":!0},this.activeClass,this.disabled)}},render:function(t){var e=this.generateRouteLink(),s=e.tag,r=e.data;return t("li",[t(s,Object(a["a"])(Object(a["a"])({},r),{},{attrs:Object(a["a"])(Object(a["a"])({},r.attrs),{},{"aria-current":this.isActive&&this.isLink?"page":void 0})}),this.$slots.default)])}}),l=s("80d2"),c=Object(l["i"])("v-breadcrumbs__divider","li"),u=s("7560");e["a"]=Object(n["a"])(u["a"]).extend({name:"v-breadcrumbs",props:{divider:{type:String,default:"/"},items:{type:Array,default:function(){return[]}},large:Boolean},computed:{classes:function(){return Object(a["a"])({"v-breadcrumbs--large":this.large},this.themeClasses)}},methods:{genDivider:function(){return this.$createElement(c,this.$slots.divider?this.$slots.divider:this.divider)},genItems:function(){for(var t=[],e=!!this.$scopedSlots.item,s=[],a=0;a<this.items.length;a++){var r=this.items[a];s.push(r.text),e?t.push(this.$scopedSlots.item({item:r})):t.push(this.$createElement(o,{key:s.join("."),props:r},[r.text])),a<this.items.length-1&&t.push(this.genDivider())}return t}},render:function(t){var e=this.$slots.default||this.genItems();return t("ul",{staticClass:"v-breadcrumbs",class:this.classes},e)}})},abd3:function(t,e,s){},ce87:function(t,e,s){"use strict";var a=s("16b7"),r=s("f2e7"),i=s("58df"),n=s("d9bd");e["a"]=Object(i["a"])(a["a"],r["a"]).extend({name:"v-hover",props:{disabled:{type:Boolean,default:!1},value:{type:Boolean,default:void 0}},methods:{onMouseEnter:function(){this.runDelay("open")},onMouseLeave:function(){this.runDelay("close")}},render:function(){return this.$scopedSlots.default||void 0!==this.value?(this.$scopedSlots.default&&(t=this.$scopedSlots.default({hover:this.isActive})),Array.isArray(t)&&1===t.length&&(t=t[0]),t&&!Array.isArray(t)&&t.tag?(this.disabled||(t.data=t.data||{},this._g(t.data,{mouseenter:this.onMouseEnter,mouseleave:this.onMouseLeave})),t):(Object(n["c"])("v-hover should only contain a single element",this),t)):(Object(n["c"])("v-hover is missing a default scopedSlot or bound value",this),null);var t}})},cfba:function(t,e,s){"use strict";s.r(e);var a=function(){var t=this,e=t.$createElement,s=t._self._c||e;return s("vue-page-wrapper",{attrs:{title:t.htmlTitle,"bread-crumbs":t.breadCrumbItems}},[s("menu-grid-list",{attrs:{items:t.reports,parent:"admin-slug-payroll",child:["settings","unit-of-work-done"]}})],1)},r=[],i=s("0549"),n=s("0b75"),o={components:{MenuGridList:n["a"],VuePageWrapper:i["default"]},data:function(){return{htmlTitle:"Unit of Work | Settings | Payroll | Admin",breadCrumbItems:[{text:"Payroll",disabled:!1,to:{name:"admin-slug-payroll-overview",params:{slug:this.$route.params.slug}}},{text:"Settings",disabled:!1,to:{name:"admin-slug-payroll-settings",params:{slug:this.$route.params.slug}}},{text:"Unit of Work Done",disabled:!0}],reports:[{title:"Operation/Project",subtitle:"This tab contains settings for operation/project.",icon:"mdi-information-outline",to:{name:"admin-slug-payroll-settings-unit-of-work-done-operation",params:{slug:this.$route.params.slug}}},{title:"Code/Task",subtitle:"This tab contains settings for code/task.",icon:"mdi-file-code-outline",to:{name:"admin-slug-payroll-settings-unit-of-work-done-code",params:{slug:this.$route.params.slug}}},{title:"Rate",subtitle:"This tab contains settings for rate.",icon:"mdi-file-percent-outline",to:{name:"admin-slug-payroll-settings-unit-of-work-done-rate",params:{slug:this.$route.params.slug}}}]}}},l=o,c=s("2877"),u=Object(c["a"])(l,a,r,!1,null,null,null);e["default"]=u.exports}}]);