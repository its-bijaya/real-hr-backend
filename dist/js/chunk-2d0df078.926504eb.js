(window["webpackJsonp"]=window["webpackJsonp"]||[]).push([["chunk-2d0df078"],{"87be":function(e,t,r){"use strict";r.r(t);var s=function(){var e=this,t=e.$createElement,r=e._self._c||t;return r("v-card",[r("vue-card-title",{attrs:{title:"Address",subtitle:"Address Information of "+e.userName,icon:"mdi-file-document-outline"}},[r("template",{slot:"actions"},[!e.showForm&&e.addressInfo.length<2&&(e.getAuthStateUserId===parseInt(e.$route.params.id)||e.verifyPermission(e.allPermissions.CAN_CREATE_UPDATE_USER_PROFILE))&&"supervisor"!==e.as&&!e.loading?r("v-btn",{attrs:{small:"",depressed:"",color:"primary"},on:{click:e.addAddress}},[e._v(" "+e._s(e.$t("createNew"))+" ")]):e._e(),e.showForm?r("v-btn",{attrs:{small:"",color:"primary",outlined:""},on:{click:e.cancelForm}},[e._v(" Cancel ")]):e._e()],1)],2),e.nonFieldErrors.length?[r("non-field-errors",{attrs:{"non-field-errors":e.nonFieldErrors}})]:e._e(),r("v-divider"),e.showForm?e._e():r("v-card-text",[e.loading?r("v-row",e._l(6,(function(e){return r("v-col",{key:e,attrs:{cols:"4"}},[r("bullet-list-loader",{attrs:{"primary-color":"#eee","secondary-color":"#d5d5d7"}})],1)})),1):e.addressInfo.length<1&&!e.showForm&&!e.loading?r("vue-no-data"):e._e(),e.showForm||e.loading?e._e():r("v-col",e._l(e.addressInfo,(function(t){return r("v-hover",{key:t.id,scopedSlots:e._u([{key:"default",fn:function(s){var o=s.hover;return r("v-row",{},[r("v-col",{attrs:{cols:"12"}},[r("strong",[e._v(" "+e._s(t.address_type)+" Address: ")]),o?r("span",[e.getAuthStateUserId!==parseInt(e.$route.params.id)&&!e.verifyPermission(e.allPermissions.CAN_CREATE_UPDATE_USER_PROFILE)||"supervisor"===e.as?e._e():r("v-icon",{staticClass:"float-right mx-2",attrs:{small:""},domProps:{textContent:e._s("mdi-pencil")},on:{click:function(r){return e.updateAddress(t)}}}),e.getAuthStateUserId!==parseInt(e.$route.params.id)&&!e.verifyPermission(e.allPermissions.CAN_CREATE_UPDATE_USER_PROFILE)||"supervisor"===e.as?e._e():r("v-icon",{staticClass:"float-right mx-2",attrs:{small:""},domProps:{textContent:e._s("mdi-delete")},on:{click:function(r){return e.deleteAddress(t)}}})],1):e._e()]),r("v-col",{attrs:{md:"6",sm:"12"}},[r("v-list-item",[r("v-list-item-avatar",{staticClass:"mr-0"},[r("v-icon",{attrs:{small:""},domProps:{textContent:e._s("mdi-web")}})],1),r("v-list-item-content",[r("v-list-item-title",{domProps:{textContent:e._s("Address")}}),r("v-list-item-subtitle",{domProps:{textContent:e._s(t.address||"N/A")}})],1)],1)],1),r("v-col",{attrs:{md:"6",sm:"12"}},[r("v-list-item",[r("v-list-item-avatar",{staticClass:"mr-0"},[r("v-icon",{attrs:{small:""},domProps:{textContent:e._s("mdi-flag-outline")}})],1),r("v-list-item-content",[r("v-list-item-title",{domProps:{textContent:e._s("Country")}}),r("v-list-item-subtitle",{domProps:{textContent:e._s(t.country.name||"N/A")}})],1)],1)],1),r("v-col",{attrs:{md:"6",sm:"12"}},[r("v-list-item",[r("v-list-item-avatar",{staticClass:"mr-0"},[r("v-icon",{attrs:{small:""},domProps:{textContent:e._s("mdi-flag-outline")}})],1),r("v-list-item-content",[r("v-list-item-title",{domProps:{textContent:e._s("Province")}}),r("v-list-item-subtitle",{domProps:{textContent:e._s(t.province?t.province.name:"N/A")}})],1)],1)],1),r("v-col",{attrs:{md:"6",sm:"12"}},[r("v-list-item",[r("v-list-item-avatar",{staticClass:"mr-0"},[r("v-icon",{attrs:{small:""},domProps:{textContent:e._s("mdi-flag-outline")}})],1),r("v-list-item-content",[r("v-list-item-title",{domProps:{textContent:e._s("District")}}),r("v-list-item-subtitle",{domProps:{textContent:e._s(t.district?t.district.name:"N/A")}})],1)],1)],1),r("v-col",{attrs:{md:"6",sm:"12"}},[r("v-list-item",[r("v-list-item-avatar",{staticClass:"mr-0"},[r("v-icon",{attrs:{small:""},domProps:{textContent:e._s("mdi-map-outline")}})],1),r("v-list-item-content",[r("v-list-item-title",{domProps:{textContent:e._s("Street")}}),r("v-list-item-subtitle",{domProps:{textContent:e._s(t.street||"N/A")}})],1)],1)],1),r("v-col",{attrs:{md:"6",sm:"12"}},[r("v-list-item",[r("v-list-item-avatar",{staticClass:"mr-0"},[r("v-icon",{attrs:{small:""},domProps:{textContent:e._s("mdi-city")}})],1),r("v-list-item-content",[r("v-list-item-title",{domProps:{textContent:e._s("City")}}),r("v-list-item-subtitle",{domProps:{textContent:e._s(t.city||"N/A")}})],1)],1)],1),r("v-col",{attrs:{md:"6",sm:"12"}},[r("v-list-item",[r("v-list-item-avatar",{staticClass:"mr-0"},[r("v-icon",{attrs:{small:""},domProps:{textContent:e._s("mdi-map-outline")}})],1),r("v-list-item-content",[r("v-list-item-title",{domProps:{textContent:e._s("Postal Code")}}),r("v-list-item-subtitle",{domProps:{textContent:e._s(t.postal_code||"N/A")}})],1)],1)],1)],1)}}],null,!0)})})),1)],1),e.showForm?r("address-form",{attrs:{"user-id":e.userInfo.user.id,"export-fields":e.selectedItem,as:e.as},on:{created:e.refresh,updated:e.refresh}}):e._e(),r("vue-dialog",{attrs:{notify:e.deleteDialog},on:{close:function(t){e.deleteDialog.dialog=!1},agree:e.deleteItem},model:{value:e.deleteDialog.dialog,callback:function(t){e.$set(e.deleteDialog,"dialog",t)},expression:"deleteDialog.dialog"}}),r("vue-notify",{attrs:{notify:e.notify}})],2)},o=[],i=r("1da1"),n=(r("96cf"),function(){var e=this,t=e.$createElement,r=e._self._c||t;return r("v-form",{on:{submit:function(t){return t.preventDefault(),e.getFormAction.apply(null,arguments)}}},[r("v-container",{staticClass:"px-12"},[e.nonFieldErrors?r("non-field-form-errors",{attrs:{"non-field-errors":e.nonFieldErrors}}):e._e(),r("v-row",[r("v-col",{attrs:{md:"6",sm:"12"}},[r("v-select",e._b({directives:[{name:"validate",rawName:"v-validate",value:"required",expression:"'required'"}],attrs:{items:e.addressTypeChoices,"item-text":"text","item-value":"value","prepend-inner-icon":"mdi-text-box-outline"},model:{value:e.form.address_type,callback:function(t){e.$set(e.form,"address_type",t)},expression:"form.address_type"}},"v-select",e.veeValidate("address_type","Address Type *"),!1))],1),r("v-col",{attrs:{md:"6",sm:"12"}},[r("v-text-field",e._b({directives:[{name:"validate",rawName:"v-validate",value:"required|max:255",expression:"'required|max:255'"}],attrs:{counter:255,"prepend-inner-icon":"mdi-web"},model:{value:e.form.address,callback:function(t){e.$set(e.form,"address",t)},expression:"form.address"}},"v-text-field",e.veeValidate("address","Address *"),!1))],1),r("v-col",{attrs:{md:"6",sm:"12"}},[r("vue-auto-complete",e._b({directives:[{name:"validate",rawName:"v-validate",value:"required",expression:"'required'"}],attrs:{endpoint:"recruitment/common/country/","item-text":"name","item-value":"id","selected-full-data":e.selectedCountryFullData,"force-fetch":"","prepend-inner-icon":"mdi-flag-outline"},on:{"update:selectedFullData":function(t){e.selectedCountryFullData=t},"update:selected-full-data":function(t){e.selectedCountryFullData=t}},model:{value:e.form.country,callback:function(t){e.$set(e.form,"country",t)},expression:"form.country"}},"vue-auto-complete",e.veeValidate("country","Country *"),!1))],1),e.selectedCountryFullData&&"Nepal"===e.selectedCountryFullData.name?r("v-col",{attrs:{md:"6",sm:"12"}},[r("vue-auto-complete",e._b({directives:[{name:"validate",rawName:"v-validate",value:"required",expression:"'required'"}],attrs:{endpoint:"/recruitment/common/country/"+e.getId(e.form.country)+"/provinces/","item-text":"name","item-value":"id","prepend-inner-icon":"mdi-map-marker-outline","force-fetch":""},model:{value:e.form.province,callback:function(t){e.$set(e.form,"province",t)},expression:"form.province"}},"vue-auto-complete",e.veeValidate("province","Province/State*"),!1))],1):e._e(),e.form.province?r("v-col",{attrs:{md:"6",sm:"12"}},[r("vue-auto-complete",e._b({directives:[{name:"validate",rawName:"v-validate",value:"required",expression:"'required'"}],key:e.districtAutoCompleteKey,attrs:{endpoint:"/recruitment/common/country/"+e.getId(e.form.country)+"/provinces/"+e.getId(e.form.province)+"/district","item-text":"name","item-value":"id","prepend-inner-icon":"mdi-map-marker-outline","force-fetch":""},model:{value:e.form.district,callback:function(t){e.$set(e.form,"district",t)},expression:"form.district"}},"vue-auto-complete",e.veeValidate("district","District*"),!1))],1):e._e(),r("v-col",{attrs:{md:"6",sm:"12"}},[r("v-text-field",e._b({directives:[{name:"validate",rawName:"v-validate",value:"max:100",expression:"'max:100'"}],attrs:{counter:100,"prepend-inner-icon":"mdi-city"},model:{value:e.form.city,callback:function(t){e.$set(e.form,"city",t)},expression:"form.city"}},"v-text-field",e.veeValidate("city","City"),!1))],1),r("v-col",{attrs:{md:"6",sm:"12"}},[r("v-text-field",e._b({directives:[{name:"validate",rawName:"v-validate",value:"max:255",expression:"'max:255'"}],attrs:{counter:255,"prepend-inner-icon":"mdi-map-outline"},model:{value:e.form.street,callback:function(t){e.$set(e.form,"street",t)},expression:"form.street"}},"v-text-field",e.veeValidate("street","Street"),!1))],1),r("v-col",{attrs:{md:"6",sm:"12"}},[r("v-text-field",e._b({directives:[{name:"validate",rawName:"v-validate",value:"max:10",expression:"'max:10'"}],attrs:{counter:10,"prepend-inner-icon":"mdi-city"},model:{value:e.form.postal_code,callback:function(t){e.$set(e.form,"postal_code",t)},expression:"form.postal_code"}},"v-text-field",e.veeValidate("postal_code","Postal code"),!1))],1)],1)],1),r("v-divider"),r("v-card-actions",[r("v-spacer"),r("v-btn",{attrs:{disabled:e.errors.any(),depressed:"",color:"primary",type:"submit"}},[e._v(" Save ")]),r("v-btn",{on:{click:e.clear}},[e._v(" Clear")])],1)],1)}),a=[],l=(r("a9e3"),r("b0c0"),r("c44a")),d=r("ab8a"),c=r("5660"),m=(r("99af"),{getUserAddresses:function(e){return"/users/".concat(e,"/address/")},postUserAddress:function(e){return"/users/".concat(e,"/address/")},getAddressDetail:function(e,t){return"/users/".concat(e,"/address/").concat(t,"/")},updateAddressDetail:function(e,t){return"/users/".concat(e,"/address/").concat(t,"/")},deleteUserAddress:function(e,t){return"/users/".concat(e,"/address/").concat(t,"/")}}),u={components:{NonFieldFormErrors:d["default"],VueAutoComplete:c["default"]},mixins:[l["a"]],props:{userId:{type:Number,required:!0},exportFields:{type:Object,required:!0},as:{type:String,default:""}},data:function(){return{fromMenu:!1,toMenu:!1,form:this.exportFields,addressTypeChoices:[{value:"Permanent",text:"Permanent"},{value:"Temporary",text:"Temporary"}],selectedCountryFullData:this.exportFields.country,districtAutoCompleteKey:0}},watch:{selectedCountryFullData:{handler:function(e){e&&"Nepal"!==e.name&&(this.$set(this.form,"province",null),this.$set(this.form,"district",null))},deep:!0},"form.province":function(){this.districtAutoCompleteKey+=1},exportFields:function(e){this.form=e,this.$validator.errors.clear(),this.clearNonFieldErrors()}},methods:{clear:function(){this.$validator.errors.clear(),this.form={}},getFormAction:function(){return this.form.id?this.editItem():this.createItem()},createItem:function(){var e=this;return Object(i["a"])(regeneratorRuntime.mark((function t(){return regeneratorRuntime.wrap((function(t){while(1)switch(t.prev=t.next){case 0:return t.next=2,e.validateAllFields();case 2:if(!t.sent){t.next=4;break}e.$http.post(m.postUserAddress(e.userId)+"?as=".concat(e.as),e.form).then((function(t){e.verifyPermission(e.allPermissions.CAN_CREATE_UPDATE_USER_PROFILE)&&e.$route.params.slug?(e.notifyUser("Successfully created Address Information","green"),e.$emit("created",t)):(e.$router.push({name:"user-profile-change-request"}),setTimeout((function(){e.notifyUser("Profile Change request has been sent","green")}),1e3))})).catch((function(t){e.notifyInvalidFormResponse(),e.pushErrors(t)}));case 4:case"end":return t.stop()}}),t)})))()},editItem:function(){var e=this;return Object(i["a"])(regeneratorRuntime.mark((function t(){return regeneratorRuntime.wrap((function(t){while(1)switch(t.prev=t.next){case 0:return t.next=2,e.validateAllFields();case 2:if(!t.sent){t.next=4;break}e.$http.put(m.updateAddressDetail(e.userId,e.form.id)+"?as=".concat(e.as),e.form).then((function(){e.verifyPermission(e.allPermissions.CAN_CREATE_UPDATE_USER_PROFILE)&&e.$route.params.slug?(e.notifyUser("Successfully updated Address Information","green"),e.$emit("updated")):(e.notifyUser("Profile Change request has been sent","green"),e.$router.push({name:"user-profile-change-request"}))})).catch((function(t){e.notifyInvalidFormResponse(),e.pushErrors(t)}));case 4:case"end":return t.stop()}}),t)})))()},getId:function(e){return"number"===typeof e?e:e.id}}},v=u,f=r("2877"),p=r("6544"),h=r.n(p),_=r("8336"),x=r("99d9"),y=r("62ad"),g=r("a523"),C=r("ce7e"),A=r("4bd4"),b=r("0fd9b"),P=r("b974"),I=r("2fa4"),F=r("8654"),w=Object(f["a"])(v,n,a,!1,null,null,null),E=w.exports;h()(w,{VBtn:_["a"],VCardActions:x["a"],VCol:y["a"],VContainer:g["a"],VDivider:C["a"],VForm:A["a"],VRow:b["a"],VSelect:P["a"],VSpacer:I["a"],VTextField:F["a"]});var D=r("e585"),V=r("e330"),$={components:{NonFieldErrors:d["default"],AddressForm:E,BulletListLoader:V["a"],VueNoData:D["default"]},mixins:[l["a"]],props:{userInfo:{type:Object,required:!0},as:{type:String,default:""}},data:function(){return{notify:{},addressInfo:{},selectedItem:{},loading:!1,showForm:!1,deleteDialog:{dialog:!1,heading:"Confirm Delete",text:"Do you really want to delete this Address information ?"},idToDelete:-1}},computed:{userName:function(){return this.userInfo.user.first_name+" "+this.userInfo.user.middle_name+" "+this.userInfo.user.last_name}},mounted:function(){this.getUserAddress()},methods:{getUserAddress:function(){var e=this;return Object(i["a"])(regeneratorRuntime.mark((function t(){return regeneratorRuntime.wrap((function(t){while(1)switch(t.prev=t.next){case 0:e.loading=!0,e.$http.get(m.getUserAddresses(e.$route.params.id)+"?as=".concat(e.as)).then((function(t){e.addressInfo=t.results})),e.loading=!1;case 3:case"end":return t.stop()}}),t)})))()},refresh:function(){this.getUserAddress(),this.showForm=!1,this.deleteDialog.dialog=!1,this.idToDelete=""},cancelForm:function(){this.getUserAddress(),this.showForm=!1},addAddress:function(){this.selectedItem={},this.showForm=!0},updateAddress:function(e){this.selectedItem=e,this.showForm=!0},deleteAddress:function(e){this.selectedItem=e,this.deleteDialog.dialog=!0},deleteItem:function(){var e=this;return Object(i["a"])(regeneratorRuntime.mark((function t(){return regeneratorRuntime.wrap((function(t){while(1)switch(t.prev=t.next){case 0:e.idToDelete=e.selectedItem.id,e.$http.delete(m.deleteUserAddress(e.userInfo.user.id,e.idToDelete)+"?as=".concat(e.as)).then((function(){e.verifyPermission(e.allPermissions.CAN_CREATE_UPDATE_USER_PROFILE)&&e.$route.params.slug?(e.notifyUser("Successfully deleted Address Information","green"),e.refresh()):(e.notifyUser("Profile Change request has been sent","green"),e.$router.push({name:"user-profile-change-request"}))})).catch((function(t){e.deleteDialog.dialog=!1,e.pushErrors(t),e.notifyInvalidFormResponse()}));case 2:case"end":return t.stop()}}),t)})))()}}},N=$,R=r("b0af"),U=r("ce87"),k=r("132d"),T=r("da13"),S=r("8270"),q=r("5d23"),O=Object(f["a"])(N,s,o,!1,null,null,null);t["default"]=O.exports;h()(O,{VBtn:_["a"],VCard:R["a"],VCardText:x["c"],VCol:y["a"],VDivider:C["a"],VHover:U["a"],VIcon:k["a"],VListItem:T["a"],VListItemAvatar:S["a"],VListItemContent:q["a"],VListItemSubtitle:q["b"],VListItemTitle:q["c"],VRow:b["a"]})}}]);