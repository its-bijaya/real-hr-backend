(window["webpackJsonp"]=window["webpackJsonp"]||[]).push([["pages/admin/_slug/task/settings/assign-task-setting","chunk-31f8a6e6","chunk-da62e0c8","chunk-2d22d378"],{"0549":function(t,e,i){"use strict";i.r(e);var a=function(){var t=this,e=t.$createElement,i=t._self._c||e;return i("div",[i("v-row",{staticClass:"mb-3",attrs:{"no-gutters":""}},[t.breadCrumbs?i("v-col",{attrs:{cols:"12"}},[i("v-card",{attrs:{flat:""}},[i("v-breadcrumbs",{staticClass:"text-body-1 pa-2",class:{"text-caption pa-1":t.$vuetify.breakpoint.xs},attrs:{items:t.breadCrumbs},scopedSlots:t._u([{key:"item",fn:function(e){return[i("span",{class:e.item.disabled?"grey--text":"baseColor--text text--accent-2 pointer",domProps:{textContent:t._s(e.item.text)},on:{click:function(i){return t.$router.push(e.item.to)}}})]}}],null,!1,1670153796)},[i("v-icon",{attrs:{slot:"divider"},slot:"divider"},[t._v("mdi-chevron-right")])],1)],1)],1):t._e()],1),i("v-row",{attrs:{"no-gutters":""}},[i("v-col",{attrs:{cols:"12"}},[t._t("default")],2)],1)],1)},s=[],n=i("5530"),r=(i("ac1f"),i("1276"),i("b0c0"),i("2f62")),o={props:{title:{type:String,required:!0},breadCrumbs:{type:Array,default:function(){return[]}}},computed:Object(n["a"])({},Object(r["c"])({getOrganizationName:"organization/getOrganizationName",getSupervisorSwitchedOrganization:"supervisor/getSwitchedOrganization"})),mounted:function(){document.title="".concat(this.title," | RealHRsoft");var t=this.$route.params.slug?"admin-slug-dashboard":"root",e=this.$route.name.split("-"),i=this.getOrganizationName;this.getSupervisorSwitchedOrganization&&"user"===e[0]&&"supervisor"===e[1]&&(i=this.getSupervisorSwitchedOrganization.name),this.breadCrumbs.unshift({text:i,disabled:!1,to:{name:t,params:{slug:this.$route.params.slug}}})}},c=o,l=i("2877"),u=i("6544"),d=i.n(u),h=i("2bc5"),m=i("b0af"),g=i("62ad"),f=i("132d"),v=i("0fd9b"),p=Object(l["a"])(c,a,s,!1,null,null,null);e["default"]=p.exports;d()(p,{VBreadcrumbs:h["a"],VCard:m["a"],VCol:g["a"],VIcon:f["a"],VRow:v["a"]})},"2bc5":function(t,e,i){"use strict";var a=i("5530"),s=(i("a15b"),i("abd3"),i("ade3")),n=i("1c87"),r=i("58df"),o=Object(r["a"])(n["a"]).extend({name:"v-breadcrumbs-item",props:{activeClass:{type:String,default:"v-breadcrumbs__item--disabled"},ripple:{type:[Boolean,Object],default:!1}},computed:{classes:function(){return Object(s["a"])({"v-breadcrumbs__item":!0},this.activeClass,this.disabled)}},render:function(t){var e=this.generateRouteLink(),i=e.tag,s=e.data;return t("li",[t(i,Object(a["a"])(Object(a["a"])({},s),{},{attrs:Object(a["a"])(Object(a["a"])({},s.attrs),{},{"aria-current":this.isActive&&this.isLink?"page":void 0})}),this.$slots.default)])}}),c=i("80d2"),l=Object(c["i"])("v-breadcrumbs__divider","li"),u=i("7560");e["a"]=Object(r["a"])(u["a"]).extend({name:"v-breadcrumbs",props:{divider:{type:String,default:"/"},items:{type:Array,default:function(){return[]}},large:Boolean},computed:{classes:function(){return Object(a["a"])({"v-breadcrumbs--large":this.large},this.themeClasses)}},methods:{genDivider:function(){return this.$createElement(l,this.$slots.divider?this.$slots.divider:this.divider)},genItems:function(){for(var t=[],e=!!this.$scopedSlots.item,i=[],a=0;a<this.items.length;a++){var s=this.items[a];i.push(s.text),e?t.push(this.$scopedSlots.item({item:s})):t.push(this.$createElement(o,{key:i.join("."),props:s},[s.text])),a<this.items.length-1&&t.push(this.genDivider())}return t}},render:function(t){var e=this.$slots.default||this.genItems();return t("ul",{staticClass:"v-breadcrumbs",class:this.classes},e)}})},"6c6f":function(t,e,i){"use strict";i("d3b7");e["a"]={data:function(){return{deleteNotification:{dialog:!1,heading:"Confirm Delete",text:"Are you sure you want to delete ?"}}},methods:{deleteData:function(t,e){var i=this;return new Promise((function(a,s){!i.loading&&t&&(i.loading=!0,i.$http.delete(t,e||{}).then((function(t){i.crud.message&&setTimeout((function(){i.notifyUser(i.crud.message)}),1e3),a(t),i.loading=!1})).catch((function(t){i.pushErrors(t),i.notifyInvalidFormResponse(),s(t),i.loading=!1})).finally((function(){i.deleteNotification.dialog=!1})))}))}}}},"983c":function(t,e,i){"use strict";i("d3b7");e["a"]={methods:{getData:function(t,e,i){var a=this,s=arguments.length>3&&void 0!==arguments[3]&&arguments[3];return new Promise((function(n,r){!a.loading&&t&&(a.clearNonFieldErrors(),a.$validator.errors.clear(),a.loading=s,a.$http.get(t,i||{params:e||{}}).then((function(t){n(t),a.loading=!1})).catch((function(t){a.pushErrors(t),a.notifyInvalidFormResponse(),r(t),a.loading=!1})))}))},getBlockingData:function(t,e,i){var a=this;return new Promise((function(s,n){a.getData(t,e,i,!0).then((function(t){s(t)})).catch((function(t){n(t)}))}))}}}},"9d01":function(t,e,i){},ab95:function(t,e,i){"use strict";i.r(e);var a=function(){var t=this,e=t.$createElement,i=t._self._c||e;return i("vue-page-wrapper",{attrs:{title:t.htmlTitle,"bread-crumbs":t.breadCrumbItems}},[i("v-card",[i("vue-card-title",{attrs:{title:"Assign Task Setting",subtitle:"Here you can set assign task settings.",icon:"mdi-format-list-checks"}}),i("v-divider"),i("v-card-text",{staticClass:"pb-0 mb-0 pt-5"},[i("v-row",{attrs:{dense:"","no-gutters":""}},[i("span",{staticClass:"py-0 mt-1"},[t._v("Can assign to higher employment level ? ")]),i("v-switch",{staticClass:"pl-4 my-0 py-0",attrs:{label:"","data-cy":"switch-apply-holiday",color:"success"},model:{value:t.formValues.can_assign_to_higher_employment_level,callback:function(e){t.$set(t.formValues,"can_assign_to_higher_employment_level",e)},expression:"formValues.can_assign_to_higher_employment_level"}}),i("div",[i("strong",[t._v("Note:")]),t._v(" When setting is enabled, employee with lower employment/hierarchy level will be able to assign task to employee with higher employment/hierarchy level. ")])],1)],1),i("v-divider"),i("v-card-actions",[i("v-spacer"),i("v-btn",{attrs:{depressed:"",color:"primary"},on:{click:t.saveTaskSettingRequest}},[i("v-icon",{staticClass:"mr-1",attrs:{size:"14"}},[t._v(" mdi-content-save-outline ")]),t._v(" Save ")],1)],1)],1)],1)},s=[],n=i("0549"),r=i("f12b"),o=i("f8a4"),c={components:{VuePageWrapper:n["default"]},mixins:[r["a"]],data:function(){return{htmlTitle:"Assign Task Setting | Settings | Task | Admin",breadCrumbItems:[{text:"Task",disabled:!1,to:{name:"admin-slug-task-overview",params:{slug:this.$route.params.slug}}},{text:"Settings",disabled:!1,to:{name:"admin-slug-task-settings",params:{slug:this.$route.params.slug}}},{text:"Assign Task Setting",disabled:!0}],formValues:{}}},mounted:function(){this.fetchTaskSettings()},methods:{fetchTaskSettings:function(){var t=this;this.getData(o["a"].getTaskSetting(this.getOrganizationSlug)).then((function(e){t.formValues=e}))},saveTaskSettingRequest:function(){var t=this;this.crud.message="Successfully saved Task settings.",this.putData(o["a"].putTaskSetting(this.getOrganizationSlug),this.formValues).then((function(){t.fetchTaskSettings()}))}}},l=c,u=i("2877"),d=i("6544"),h=i.n(d),m=i("8336"),g=i("b0af"),f=i("99d9"),v=i("ce7e"),p=i("132d"),b=i("0fd9b"),w=i("2fa4"),y=i("b73d"),S=Object(u["a"])(l,a,s,!1,null,null,null);e["default"]=S.exports;h()(S,{VBtn:m["a"],VCard:g["a"],VCardActions:f["a"],VCardText:f["c"],VDivider:v["a"],VIcon:p["a"],VRow:b["a"],VSpacer:w["a"],VSwitch:y["a"]})},abd3:function(t,e,i){},b73d:function(t,e,i){"use strict";var a=i("5530"),s=(i("0481"),i("ec29"),i("9d01"),i("fe09")),n=i("c37a"),r=i("c3f0"),o=i("0789"),c=i("490a"),l=i("80d2");e["a"]=s["a"].extend({name:"v-switch",directives:{Touch:r["a"]},props:{inset:Boolean,loading:{type:[Boolean,String],default:!1},flat:{type:Boolean,default:!1}},computed:{classes:function(){return Object(a["a"])(Object(a["a"])({},n["a"].options.computed.classes.call(this)),{},{"v-input--selection-controls v-input--switch":!0,"v-input--switch--flat":this.flat,"v-input--switch--inset":this.inset})},attrs:function(){return{"aria-checked":String(this.isActive),"aria-disabled":String(this.isDisabled),role:"switch"}},validationState:function(){return this.hasError&&this.shouldValidate?"error":this.hasSuccess?"success":null!==this.hasColor?this.computedColor:void 0},switchData:function(){return this.setTextColor(this.loading?void 0:this.validationState,{class:this.themeClasses})}},methods:{genDefaultSlot:function(){return[this.genSwitch(),this.genLabel()]},genSwitch:function(){return this.$createElement("div",{staticClass:"v-input--selection-controls__input"},[this.genInput("checkbox",Object(a["a"])(Object(a["a"])({},this.attrs),this.attrs$)),this.genRipple(this.setTextColor(this.validationState,{directives:[{name:"touch",value:{left:this.onSwipeLeft,right:this.onSwipeRight}}]})),this.$createElement("div",Object(a["a"])({staticClass:"v-input--switch__track"},this.switchData)),this.$createElement("div",Object(a["a"])({staticClass:"v-input--switch__thumb"},this.switchData),[this.genProgress()])])},genProgress:function(){return this.$createElement(o["c"],{},[!1===this.loading?null:this.$slots.progress||this.$createElement(c["a"],{props:{color:!0===this.loading||""===this.loading?this.color||"primary":this.loading,size:16,width:2,indeterminate:!0}})])},onSwipeLeft:function(){this.isActive&&this.onChange()},onSwipeRight:function(){this.isActive||this.onChange()},onKeydown:function(t){(t.keyCode===l["y"].left&&this.isActive||t.keyCode===l["y"].right&&!this.isActive)&&this.onChange()}}})},f0d5:function(t,e,i){"use strict";i("d3b7"),i("3ca3"),i("ddb0");var a=i("c44a");e["a"]={components:{NonFieldFormErrors:function(){return i.e("chunk-6441e173").then(i.bind(null,"ab8a"))}},mixins:[a["a"]],data:function(){return{crud:{name:"record",message:"",addAnother:!1},formValues:{},loading:!1}}}},f12b:function(t,e,i){"use strict";var a=i("f0d5"),s=i("983c"),n=i("f70a"),r=i("6c6f");e["a"]={mixins:[a["a"],s["a"],n["a"],r["a"]]}},f70a:function(t,e,i){"use strict";i("d3b7"),i("caad");e["a"]={methods:{insertData:function(t,e){var i=this,a=arguments.length>2&&void 0!==arguments[2]?arguments[2]:{},s=a.validate,n=void 0===s||s,r=a.clearForm,o=void 0===r||r,c=arguments.length>3?arguments[3]:void 0;return new Promise((function(a,s){!i.loading&&t&&(i.clearErrors(),i.$validator.validateAll().then((function(r){n||(r=!0),r&&(i.loading=!0,i.$http.post(t,e,c||{}).then((function(t){i.clearErrors(),o&&(i.formValues={}),i.crud.addAnother||i.$emit("create"),i.crud.message&&setTimeout((function(){i.notifyUser(i.crud.message)}),1e3),a(t),i.loading=!1})).catch((function(t){i.pushErrors(t),i.notifyInvalidFormResponse(),s(t),i.loading=!1})))})))}))},patchData:function(t,e){var i=this,a=arguments.length>2&&void 0!==arguments[2]?arguments[2]:{},s=a.validate,n=void 0===s||s,r=a.clearForm,o=void 0===r||r,c=arguments.length>3?arguments[3]:void 0;return new Promise((function(a,s){i.updateData(t,e,{validate:n,clearForm:o},"patch",c).then((function(t){a(t)})).catch((function(t){s(t)}))}))},putData:function(t,e){var i=this,a=arguments.length>2&&void 0!==arguments[2]?arguments[2]:{},s=a.validate,n=void 0===s||s,r=a.clearForm,o=void 0===r||r,c=arguments.length>3?arguments[3]:void 0;return new Promise((function(a,s){i.updateData(t,e,{validate:n,clearForm:o},"put",c).then((function(t){a(t)})).catch((function(t){s(t)}))}))},updateData:function(t,e){var i=this,a=arguments.length>2&&void 0!==arguments[2]?arguments[2]:{},s=a.validate,n=void 0===s||s,r=a.clearForm,o=void 0===r||r,c=arguments.length>3?arguments[3]:void 0,l=arguments.length>4?arguments[4]:void 0;return new Promise((function(a,s){!i.loading&&t&&["put","patch"].includes(c)&&(i.clearErrors(),i.$validator.validateAll().then((function(r){n||(r=!0),r&&(i.loading=!0,i.$http[c](t,e,l||{}).then((function(t){i.$emit("update"),i.clearErrors(),o&&(i.formValues={}),i.crud.message&&setTimeout((function(){i.notifyUser(i.crud.message)}),1e3),a(t),i.loading=!1})).catch((function(t){i.pushErrors(t),i.notifyInvalidFormResponse(),s(t),i.loading=!1})))})))}))},clearErrors:function(){this.clearNonFieldErrors(),this.$validator.errors.clear()}}}}}]);