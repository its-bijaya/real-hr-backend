(window["webpackJsonp"]=window["webpackJsonp"]||[]).push([["pages/user/employee-directory/_id/profile-detail","chunk-31f8a6e6"],{"0549":function(t,e,i){"use strict";i.r(e);var s=function(){var t=this,e=t.$createElement,i=t._self._c||e;return i("div",[i("v-row",{staticClass:"mb-3",attrs:{"no-gutters":""}},[t.breadCrumbs?i("v-col",{attrs:{cols:"12"}},[i("v-card",{attrs:{flat:""}},[i("v-breadcrumbs",{staticClass:"text-body-1 pa-2",class:{"text-caption pa-1":t.$vuetify.breakpoint.xs},attrs:{items:t.breadCrumbs},scopedSlots:t._u([{key:"item",fn:function(e){return[i("span",{class:e.item.disabled?"grey--text":"baseColor--text text--accent-2 pointer",domProps:{textContent:t._s(e.item.text)},on:{click:function(i){return t.$router.push(e.item.to)}}})]}}],null,!1,1670153796)},[i("v-icon",{attrs:{slot:"divider"},slot:"divider"},[t._v("mdi-chevron-right")])],1)],1)],1):t._e()],1),i("v-row",{attrs:{"no-gutters":""}},[i("v-col",{attrs:{cols:"12"}},[t._t("default")],2)],1)],1)},a=[],r=i("5530"),o=(i("ac1f"),i("1276"),i("b0c0"),i("2f62")),n={props:{title:{type:String,required:!0},breadCrumbs:{type:Array,default:function(){return[]}}},computed:Object(r["a"])({},Object(o["c"])({getOrganizationName:"organization/getOrganizationName",getSupervisorSwitchedOrganization:"supervisor/getSwitchedOrganization"})),mounted:function(){document.title="".concat(this.title," | RealHRsoft");var t=this.$route.params.slug?"admin-slug-dashboard":"root",e=this.$route.name.split("-"),i=this.getOrganizationName;this.getSupervisorSwitchedOrganization&&"user"===e[0]&&"supervisor"===e[1]&&(i=this.getSupervisorSwitchedOrganization.name),this.breadCrumbs.unshift({text:i,disabled:!1,to:{name:t,params:{slug:this.$route.params.slug}}})}},l=n,m=i("2877"),c=i("6544"),u=i.n(c),d=i("2bc5"),v=i("b0af"),p=i("62ad"),b=i("132d"),f=i("0fd9b"),h=Object(m["a"])(l,s,a,!1,null,null,null);e["default"]=h.exports;u()(h,{VBreadcrumbs:d["a"],VCard:v["a"],VCol:p["a"],VIcon:b["a"],VRow:f["a"]})},"28fd":function(t,e,i){"use strict";var s=function(){var t=this,e=t.$createElement,i=t._self._c||e;return t.text&&t.text.length>t.count?i("v-tooltip",{attrs:{top:""},scopedSlots:t._u([{key:"activator",fn:function(e){var s=e.on;return[i("span",t._g({domProps:{innerHTML:t._f("truncate")(t.$sanitize(t.text),t.count)}},s))]}}],null,!1,1348744266)},[i("span",{domProps:{innerHTML:t._s(t.$sanitize(t.text))}})]):i("span",{domProps:{innerHTML:t._f("truncate")(t.$sanitize(t.text||t.defaultText),t.count)}})},a=[],r=(i("a9e3"),{props:{text:{required:!0,validator:function(t){return"string"===typeof t||null===t||void 0===t}},count:{type:Number,required:!0},defaultText:{type:String,default:"N/A"}}}),o=r,n=i("2877"),l=i("6544"),m=i.n(l),c=i("3a2f"),u=Object(n["a"])(o,s,a,!1,null,null,null);e["a"]=u.exports;m()(u,{VTooltip:c["a"]})},"2bc5":function(t,e,i){"use strict";var s=i("5530"),a=(i("a15b"),i("abd3"),i("ade3")),r=i("1c87"),o=i("58df"),n=Object(o["a"])(r["a"]).extend({name:"v-breadcrumbs-item",props:{activeClass:{type:String,default:"v-breadcrumbs__item--disabled"},ripple:{type:[Boolean,Object],default:!1}},computed:{classes:function(){return Object(a["a"])({"v-breadcrumbs__item":!0},this.activeClass,this.disabled)}},render:function(t){var e=this.generateRouteLink(),i=e.tag,a=e.data;return t("li",[t(i,Object(s["a"])(Object(s["a"])({},a),{},{attrs:Object(s["a"])(Object(s["a"])({},a.attrs),{},{"aria-current":this.isActive&&this.isLink?"page":void 0})}),this.$slots.default)])}}),l=i("80d2"),m=Object(l["i"])("v-breadcrumbs__divider","li"),c=i("7560");e["a"]=Object(o["a"])(c["a"]).extend({name:"v-breadcrumbs",props:{divider:{type:String,default:"/"},items:{type:Array,default:function(){return[]}},large:Boolean},computed:{classes:function(){return Object(s["a"])({"v-breadcrumbs--large":this.large},this.themeClasses)}},methods:{genDivider:function(){return this.$createElement(m,this.$slots.divider?this.$slots.divider:this.divider)},genItems:function(){for(var t=[],e=!!this.$scopedSlots.item,i=[],s=0;s<this.items.length;s++){var a=this.items[s];i.push(a.text),e?t.push(this.$scopedSlots.item({item:a})):t.push(this.$createElement(n,{key:i.join("."),props:a},[a.text])),s<this.items.length-1&&t.push(this.genDivider())}return t}},render:function(t){var e=this.$slots.default||this.genItems();return t("ul",{staticClass:"v-breadcrumbs",class:this.classes},e)}})},"42f8":function(t,e,i){"use strict";i("6ec5")},4335:function(t,e,i){"use strict";e["a"]={getEmployeeDirectory:"/hris/employee-directory/",getEmployeeDetails:function(t){return"/hris/employee-directory/".concat(t,"/")}}},"6ec5":function(t,e,i){},abd3:function(t,e,i){},dd56:function(t,e,i){"use strict";i.r(e);var s=function(){var t=this,e=t.$createElement,i=t._self._c||e;return i("vue-page-wrapper",{attrs:{title:t.htmlTitle,"bread-crumbs":t.breadCrumbItems}},[t.fetched?i("div",[i("div",[i("v-img",{attrs:{src:t.userDetail.user.cover_picture||"/images//help/lazy.jpeg","aspect-ratio":"4"}})],1),i("v-row",[i("v-col",{attrs:{md:"3",sm:"12"}},[i("v-card",{attrs:{align:"center"}},[i("div",[i("v-avatar",{staticClass:"mt-n10",attrs:{size:"120"}},[i("v-img",{attrs:{src:t.userDetail.user.profile_picture,"lazy-src":"/images//help/lazy.jpeg"}})],1)],1),i("div",[i("div",[i("p",{staticClass:"my-1"},[t._v(" "+t._s(t.userDetail.user.full_name)+" ")]),i("strong",{staticClass:"my-1"},[t._v(" "+t._s(t.get(t.userDetail.user,"organization.name"))+" ")]),i("div",{staticClass:"my-1"},[t._v(" "+t._s(t.get(t.userDetail.user,"email"))+" ")]),i("div",{staticClass:"my-1"},[t._v(" "+t._s(t.get(t.userDetail,"code"))+" ")]),t.get(t.userDetail,"eid_no")?i("div",{staticClass:"my-1"},[t._v(" EID No. : "+t._s(t.get(t.userDetail,"eid_no"))+" ")]):t._e(),i("v-chip",{staticClass:"my-1",attrs:{label:"",small:""}},[t._v(" "+t._s(t.get(t.userDetail.user,"employee_level"))+" ")])],1),i("v-col")],1)])],1),i("v-col",{attrs:{md:"9",sm:"12"}},[i("v-card",[i("vue-card-title",{attrs:{title:"Employee Profile Detail",subtitle:"Refer the following information for employee profile detail.",icon:"mdi-badge-account-horizontal-outline"}}),i("v-divider"),i("v-card-text",[i("v-row",[i("v-col",{attrs:{sm:"6"}},[i("v-list-item",[i("v-list-item-avatar",{staticClass:"mr-0"},[i("v-icon",{attrs:{small:""},domProps:{textContent:t._s("mdi-domain")}})],1),i("v-list-item-content",[i("v-list-item-title",{domProps:{textContent:t._s("Organization")}}),i("v-list-item-subtitle",[i("truncate-tooltip",{attrs:{count:40,text:t.get(t.userDetail.user,"organization.name")}})],1)],1)],1),i("v-list-item",[i("v-list-item-avatar",{staticClass:"mr-0"},[i("v-icon",{attrs:{small:""},domProps:{textContent:t._s("mdi-account-outline")}})],1),i("v-list-item-content",[i("v-list-item-title",{domProps:{textContent:t._s("Full Name")}}),i("v-list-item-subtitle",[i("truncate-tooltip",{attrs:{count:40,text:t.userDetail.user.full_name}})],1)],1)],1),i("v-list-item",[i("v-list-item-avatar",{staticClass:"mr-0"},[i("v-icon",{attrs:{small:""},domProps:{textContent:t._s("mdi-phone-outline")}})],1),i("v-list-item-content",[i("v-list-item-title",{domProps:{textContent:t._s("Extension Number")}}),i("v-list-item-subtitle",{domProps:{textContent:t._s(t.get(t.userDetail,"extension_number")||"N/A")}})],1)],1),i("v-list-item",[i("v-list-item-avatar",{staticClass:"mr-0"},[i("v-icon",{attrs:{small:""},domProps:{textContent:t._s("mdi-phone-outline")}})],1),i("v-list-item-content",[i("v-list-item-title",{domProps:{textContent:t._s("Phone Number")}}),i("v-list-item-subtitle",{domProps:{textContent:t._s(t.userDetail.phone_number||"N/A")}})],1)],1),i("v-list-item",[i("v-list-item-avatar",{staticClass:"mr-0"},[i("v-icon",{attrs:{small:""},domProps:{textContent:t._s("mdi-email-outline")}})],1),i("v-list-item-content",[i("v-list-item-title",{domProps:{textContent:t._s("Email")}}),i("v-list-item-subtitle",[i("truncate-tooltip",{attrs:{count:40,text:t.userDetail.user.email}})],1)],1)],1),i("v-list-item",[i("v-list-item-avatar",{staticClass:"mr-0"},[i("v-icon",{attrs:{small:""},domProps:{textContent:t._s("mdi-target")}})],1),i("v-list-item-content",[i("v-list-item-title",{domProps:{textContent:t._s("Address")}}),i("v-list-item-subtitle",[i("truncate-tooltip",{attrs:{count:40,text:t.userDetail.address}})],1)],1)],1)],1),i("v-col",{attrs:{sm:"6"}},[i("v-list-item",[i("v-list-item-avatar",{staticClass:"mr-0"},[i("v-icon",{attrs:{small:""},domProps:{textContent:t._s("mdi-calendar-month-outline")}})],1),i("v-list-item-content",[i("v-list-item-title",{domProps:{textContent:t._s("Joined Date")}}),i("v-list-item-subtitle",{domProps:{textContent:t._s(t.userDetail.joined_date||"N/A")}})],1)],1),i("v-list-item",[i("v-list-item-avatar",{staticClass:"mr-0"},[i("v-icon",{attrs:{small:""},domProps:{textContent:t._s("mdi-domain")}})],1),i("v-list-item-content",[i("v-list-item-title",{domProps:{textContent:t._s("Department")}}),i("v-list-item-subtitle",[i("truncate-tooltip",{attrs:{count:40,text:t.get(t.userDetail.user,"division.name")}})],1)],1)],1),i("v-list-item",[i("v-list-item-avatar",{staticClass:"mr-0"},[i("v-icon",{attrs:{small:""},domProps:{textContent:t._s("mdi-account-outline")}})],1),i("v-list-item-content",[i("v-list-item-title",{domProps:{textContent:t._s("Job Title")}}),i("v-list-item-subtitle",[i("truncate-tooltip",{attrs:{count:40,text:t.userDetail.user.job_title}})],1)],1)],1),i("v-list-item",[i("v-list-item-avatar",{staticClass:"mr-0"},[i("v-icon",{attrs:{small:""},domProps:{textContent:t._s("mdi-account-outline")}})],1),i("v-list-item-content",[i("v-list-item-title",{domProps:{textContent:t._s("Supervisor Name")}}),i("v-list-item-subtitle",[i("truncate-tooltip",{attrs:{count:40,text:t.get(t.userDetail.supervisor,"full_name")}})],1)],1)],1),i("v-list-item",[i("v-list-item-avatar",{staticClass:"mr-0"},[i("v-icon",{attrs:{small:""},domProps:{textContent:t._s("mdi-source-branch")}})],1),i("v-list-item-content",[i("v-list-item-title",{domProps:{textContent:t._s("Branch")}}),i("v-list-item-subtitle",[i("truncate-tooltip",{attrs:{count:40,text:t.get(t.userDetail.branch,"name")}})],1)],1)],1),i("v-list-item",[i("v-list-item-avatar",{staticClass:"mr-0"},[i("v-icon",{attrs:{small:""},domProps:{textContent:t._s("mdi-gender-male-female")}})],1),i("v-list-item-content",[i("v-list-item-title",{domProps:{textContent:t._s("Gender")}}),i("v-list-item-subtitle",{domProps:{textContent:t._s(t.userDetail.gender||"N/A")}})],1)],1)],1)],1)],1)],1)],1)],1)],1):t._e()])},a=[],r=i("0549"),o=i("4335"),n=i("28fd"),l={components:{TruncateTooltip:n["a"],VuePageWrapper:r["default"]},validate:function(t){var e=t.params;return/^\d+$/.test(e.id)},data:function(){return{htmlTitle:"Employee Directory | Profile Detail",breadCrumbItems:[{text:"Employee Directory",disabled:!1,to:{name:"user-employee-directory"}},{text:"Profile Detail",disabled:!0}],fetched:!1,userDetail:{}}},created:function(){var t=this.$route.params.id;this.fetchUserDetail(t)},methods:{fetchUserDetail:function(t){var e=this;this.$http.get(o["a"].getEmployeeDetails(t)).then((function(t){e.userDetail=t,e.fetched=!0}))}}},m=l,c=(i("42f8"),i("2877")),u=i("6544"),d=i.n(u),v=i("8212"),p=i("b0af"),b=i("99d9"),f=i("cc20"),h=i("62ad"),g=i("ce7e"),_=i("132d"),C=i("adda"),x=i("da13"),y=i("8270"),D=i("5d23"),P=i("0fd9b"),O=Object(c["a"])(m,s,a,!1,null,"b349aac8",null);e["default"]=O.exports;d()(O,{VAvatar:v["a"],VCard:p["a"],VCardText:b["c"],VChip:f["a"],VCol:h["a"],VDivider:g["a"],VIcon:_["a"],VImg:C["a"],VListItem:x["a"],VListItemAvatar:y["a"],VListItemContent:D["a"],VListItemSubtitle:D["b"],VListItemTitle:D["c"],VRow:P["a"]})}}]);