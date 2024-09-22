(window["webpackJsonp"]=window["webpackJsonp"]||[]).push([["chunk-c8e6bdda"],{"3b22":function(t,e,n){"use strict";e["a"]={getPostHiringMethod:"/recruitment/hiring-method/",updateDeleteHiringMethod:function(t){return"/recruitment/hiring-method/".concat(t)}}},8133:function(t,e,n){"use strict";n.r(e);var r=function(){var t=this,e=t.$createElement,n=t._self._c||e;return n("v-card",[n("vue-card-title",{attrs:{title:"Other Detail",subtitle:"Other Details of "+t.userName,icon:"mdi-file-document"}},[n("template",{slot:"actions"},["hr"===t.as?[t.showForm?n("v-btn",{attrs:{small:"",color:"primary",outlined:""},on:{click:function(e){return t.changeShowForm(!1)}}},[t._v("Cancel ")]):t._e(),t.showHiringForm?n("v-btn",{attrs:{small:"",color:"primary",outlined:""},on:{click:function(e){return t.changeHiringShowForm(!1)}}},[t._v("Cancel ")]):t._e()]:t._e()],2)],2),n("v-divider"),t.showForm?[n("EidInformationForm",{attrs:{userId:t.userId,"action-data":t.eid_no,as:t.as},on:{"refresh-data":t.refresh}})]:t.showHiringForm?[n("HiringMethodForm",{attrs:{userId:t.userId,"action-data":t.new_hiring_method,as:t.as},on:{"refresh-data":t.refresh}})]:[n("v-row",[n("v-col",{attrs:{cols:"4"}},[n("v-hover",{scopedSlots:t._u([{key:"default",fn:function(e){var r=e.hover;return n("v-col",{},[n("v-list-item",[n("v-list-item-avatar",{staticClass:"mr-0"},[n("v-icon",{attrs:{small:""},domProps:{textContent:t._s("mdi-file-document")}})],1),n("v-list-item-content",[n("v-list-item-title",[t._v("EID Number "),!t.showForm&&r?n("v-icon",{staticClass:"float-right mx-2",attrs:{small:""},domProps:{textContent:t._s("mdi-pencil")},on:{click:function(e){return t.changeShowForm(!0)}}}):t._e()],1),n("v-list-item-subtitle",[t._v(t._s(t.eid_no||"N/A")+" ")])],1)],1)],1)}}])}),"hr"===t.as||t.userId===t.getAuthStateUserId?n("v-hover",{scopedSlots:t._u([{key:"default",fn:function(e){var r=e.hover;return"hr"===t.as||t.userId===t.getAuthStateUserId?n("v-col",{},[n("v-list-item",[n("v-list-item-avatar",{staticClass:"mr-0"},[n("v-icon",{attrs:{small:""},domProps:{textContent:t._s("mdi-file-document")}})],1),n("v-list-item-content",[n("v-list-item-title",[t._v("Hiring Method "),!t.showHiringForm&&r&&"hr"===t.as?n("v-icon",{staticClass:"float-right mx-2",attrs:{small:""},domProps:{textContent:t._s("mdi-pencil")},on:{click:function(e){return t.changeHiringShowForm(!0)}}}):t._e()],1),n("v-list-item-subtitle",[t._v(t._s(t.hiring_method||"N/A")+" ")])],1)],1)],1):t._e()}}],null,!0)}):t._e()],1)],1)]],2)},i=[],a=n("1da1"),o=(n("96cf"),function(){var t=this,e=t.$createElement,n=t._self._c||e;return n("div",[n("v-form",{ref:"form",attrs:{"lazy-validation":""}},[n("v-row",[n("v-col",{attrs:{cols:"6"}},[n("v-list-item",[n("v-text-field",t._b({directives:[{name:"validate",rawName:"v-validate",value:"num_dash",expression:"'num_dash'"}],attrs:{"prepend-inner-icon":"mdi-file-document"},model:{value:t.form.eid_no,callback:function(e){t.$set(t.form,"eid_no",e)},expression:"form.eid_no"}},"v-text-field",t.veeValidate("eid_no","EID No"),!1))],1)],1)],1),n("v-divider"),n("v-card-actions",[n("v-spacer"),n("v-btn",{attrs:{depressed:"",color:"primary"},on:{click:t.addEditData}},[t._v(" Save ")]),n("v-btn",{attrs:{depressed:""},on:{click:function(e){return t.clear()}}},[t._v(" Clear ")])],1)],1)],1)}),s=[],c=(n("a9e3"),n("159b"),n("b64b"),n("fab2")),d=n("c44a"),l=n("7bb1");l["b"].Validator.extend("num_dash",{validate:function(t){return/^[a-zA-Z0-9-]+$/.test(t)},getMessage:function(t){return"".concat(t," should be valid alpha numeric")}});var u={mixins:[d["a"]],props:{userId:{type:Number,default:null},actionData:{type:String,default:null},as:{type:String,default:""}},data:function(){return{form:{eid_no:""}}},created:function(){null!=this.actionData&&(this.form.eid_no=this.actionData)},methods:{addEditData:function(){var t=this;return Object(a["a"])(regeneratorRuntime.mark((function e(){return regeneratorRuntime.wrap((function(e){while(1)switch(e.prev=e.next){case 0:return e.next=2,t.validateAllFields();case 2:if(!e.sent){e.next=4;break}t.$http.patch(c["a"].updateUser(t.userId)+"?as=".concat(t.as),{eid_no:0===t.form.eid_no.length?null:t.form.eid_no}).then((function(e){t.form.eid_no=e.eid_no,t.notifyUser("EID Number updated successfully","green"),t.$emit("refresh-data")})).catch((function(e){t.pushErrors(e)}));case 4:case"end":return e.stop()}}),e)})))()},clear:function(){var t=this;this.$validator.errors.clear(),this.clearNonFieldErrors(),Object.keys(this.form).forEach((function(e){t.form[e]=""}))}}},m=u,h=n("2877"),f=n("6544"),v=n.n(f),_=n("8336"),g=n("99d9"),p=n("62ad"),w=n("ce7e"),b=n("4bd4"),I=n("da13"),V=n("0fd9b"),F=n("2fa4"),x=n("8654"),E=Object(h["a"])(m,o,s,!1,null,null,null),k=E.exports;v()(E,{VBtn:_["a"],VCardActions:g["a"],VCol:p["a"],VDivider:w["a"],VForm:b["a"],VListItem:I["a"],VRow:V["a"],VSpacer:F["a"],VTextField:x["a"]});var y=function(){var t=this,e=t.$createElement,n=t._self._c||e;return n("div",[n("v-form",{ref:"form",attrs:{"lazy-validation":""}},[n("v-row",[n("v-col",{attrs:{cols:"6"}},[n("v-list-item",[n("vue-auto-complete",{attrs:{endpoint:t.hiringMethodEndPoint,label:"Hiring method","force-fetch":"","item-text":"name","item-value":"id","prepend-inner-icon":"mdi-file-document"},model:{value:t.form.new_hiring_method,callback:function(e){t.$set(t.form,"new_hiring_method",e)},expression:"form.new_hiring_method"}})],1)],1)],1),n("v-divider"),n("v-card-actions",[n("v-spacer"),n("v-btn",{attrs:{depressed:"",color:"primary"},on:{click:t.addEditData}},[t._v(" Save")]),n("v-btn",{attrs:{depressed:""},on:{click:function(e){return t.clear()}}},[t._v(" Clear")])],1)],1)],1)},S=[],C=n("5660"),D=n("3b22");l["b"].Validator.extend("num_dash",{validate:function(t){return/^[a-zA-Z0-9-]+$/.test(t)},getMessage:function(t){return"".concat(t," should be valid alpha numeric")}});var H={components:{VueAutoComplete:C["default"]},mixins:[d["a"]],props:{userId:{type:Number,default:null},actionData:{type:[String,Number],default:null},as:{type:String,default:""}},data:function(){return{form:{new_hiring_method:""},hiringMethodEndPoint:""}},created:function(){this.hiringMethodEndPoint=D["a"].getPostHiringMethod+"?organization=".concat(this.getOrganizationSlug),null!=this.actionData&&(this.form.new_hiring_method=this.actionData)},methods:{addEditData:function(){var t=this;return Object(a["a"])(regeneratorRuntime.mark((function e(){return regeneratorRuntime.wrap((function(e){while(1)switch(e.prev=e.next){case 0:return e.next=2,t.validateAllFields();case 2:if(!e.sent){e.next=4;break}t.$http.patch(c["a"].updateUser(t.userId)+"?as=".concat(t.as),{new_hiring_method:t.form.new_hiring_method?t.form.new_hiring_method:null}).then((function(e){t.form.new_hiring_method=e.new_hiring_method,t.notifyUser("Hiring method updated successfully","green"),t.$emit("refresh-data")})).catch((function(e){t.pushErrors(e)}));case 4:case"end":return e.stop()}}),e)})))()},clear:function(){var t=this;this.$validator.errors.clear(),this.clearNonFieldErrors(),Object.keys(this.form).forEach((function(e){t.form[e]=""}))}}},$=H,N=Object(h["a"])($,y,S,!1,null,null,null),A=N.exports;v()(N,{VBtn:_["a"],VCardActions:g["a"],VCol:p["a"],VDivider:w["a"],VForm:b["a"],VListItem:I["a"],VRow:V["a"],VSpacer:F["a"]});var O={components:{EidInformationForm:k,HiringMethodForm:A},props:{userInfo:{type:Object,default:function(){return{}}},as:{type:String,default:""}},data:function(){return{showForm:!1,showHiringForm:!1,loading:!1,eid_no:"",hiring_method:"",new_hiring_method:""}},computed:{userName:function(){return this.userInfo.user.first_name+" "+this.userInfo.user.middle_name+" "+this.userInfo.user.last_name},userId:function(){return this.userInfo.user.id}},created:function(){this.getEidInfo()},methods:{getEidInfo:function(){var t=this;return Object(a["a"])(regeneratorRuntime.mark((function e(){return regeneratorRuntime.wrap((function(e){while(1)switch(e.prev=e.next){case 0:t.loading=!0,t.$http.get(c["a"].getUserDetail(t.userId)+"?as=".concat(t.as)).then((function(e){t.eid_no=e.eid_no,t.hiring_method=e.hiring_method,t.new_hiring_method=e.new_hiring_method})),t.loading=!1;case 3:case"end":return e.stop()}}),e)})))()},changeShowForm:function(t){1==t?(this.showForm=!0,this.loading=!1):this.showForm=!1},changeHiringShowForm:function(t){t?(this.showHiringForm=!0,this.loading=!1):this.showHiringForm=!1},refresh:function(){this.showForm=!1,this.showHiringForm=!1,this.getEidInfo(),this.$emit("refresh")}}},M=O,j=n("b0af"),P=n("ce87"),R=n("132d"),L=n("8270"),U=n("5d23"),z=Object(h["a"])(M,r,i,!1,null,null,null);e["default"]=z.exports;v()(z,{VBtn:_["a"],VCard:j["a"],VCol:p["a"],VDivider:w["a"],VHover:P["a"],VIcon:R["a"],VListItem:I["a"],VListItemAvatar:L["a"],VListItemContent:U["a"],VListItemSubtitle:U["b"],VListItemTitle:U["c"],VRow:V["a"]})}}]);