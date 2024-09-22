(window["webpackJsonp"]=window["webpackJsonp"]||[]).push([["chunk-c547037c"],{4479:function(e,t,r){"use strict";r.r(t);var n=function(){var e=this,t=e.$createElement,r=e._self._c||t;return e.deleteEmploymentType?e._e():r("v-form",{ref:"employmentTypeForm",on:{submit:function(t){return t.preventDefault(),e.getFormAction.apply(null,arguments)}}},[r("v-card",[e.showTitle?r("vue-card-title",{attrs:{title:e.info.title,subtitle:e.info.subtitle,icon:e.info.icon,closable:""},on:{close:function(t){return e.$emit("dismiss-form")}}}):e._e(),r("v-divider"),r("v-card-text",[r("v-row",{attrs:{align:"end"}},[e.nonFieldErrors?r("non-field-form-errors",{attrs:{"non-field-errors":e.nonFieldErrors}}):e._e(),r("v-col",{attrs:{md:"6",cols:"12"}},[r("v-text-field",e._b({directives:[{name:"validate",rawName:"v-validate",value:"required|max:150",expression:"'required|max:150'"}],attrs:{counter:150,"prepend-inner-icon":"mdi-file-document-outline"},model:{value:e.formValues.title,callback:function(t){e.$set(e.formValues,"title",t)},expression:"formValues.title"}},"v-text-field",e.veeValidate("title","Title *"),!1))],1),r("v-col",{attrs:{md:"6",cols:"12"}},[r("v-textarea",e._b({directives:[{name:"validate",rawName:"v-validate",value:"max:600",expression:"'max:600'"}],attrs:{counter:600,rows:"2","prepend-inner-icon":"mdi-information-outline"},model:{value:e.formValues.description,callback:function(t){e.$set(e.formValues,"description",t)},expression:"formValues.description"}},"v-textarea",e.veeValidate("description","Description"),!1))],1),r("v-col",{attrs:{md:"6",cols:"12"}},[r("v-checkbox",e._b({model:{value:e.formValues.is_archived,callback:function(t){e.$set(e.formValues,"is_archived",t)},expression:"formValues.is_archived"}},"v-checkbox",e.veeValidate("is_archived","Is Archived"),!1))],1),r("v-col",{attrs:{md:"6",cols:"12"}},[r("v-checkbox",e._b({model:{value:e.formValues.is_contract,callback:function(t){e.$set(e.formValues,"is_contract",t)},expression:"formValues.is_contract"}},"v-checkbox",e.veeValidate("is_contract","Is Contract"),!1))],1)],1)],1),r("v-divider"),r("form-submit",{attrs:{"form-errors":e.errors.any(),"delete-instance":e.deleteEmploymentType},on:{clearForm:e.clearForm}})],1)],1)},a=[],i=r("1da1"),o=(r("96cf"),r("f12b")),s=r("878b"),l=r("7e77"),c={components:{FormSubmit:s["a"]},mixins:[o["a"]],props:{actionData:{type:Object,required:!1,default:function(){return{title:"",description:"",is_contract:!1}}},orgSlug:{type:String,required:!0},deleteEmploymentType:{type:Boolean,default:!1},showTitle:{type:Boolean,default:!1}},data:function(){return{formValues:this.actionData,info:{title:"",subtitle:"",icon:""}}},computed:{deletionOf:function(){return{name:"Employment Type",instanceName:this.actionData.title}}},created:function(){this.deleteEmploymentType&&this.getFormAction()},mounted:function(){this.cardTitleDetail()},methods:{getFormAction:function(){var e=this;return Object(i["a"])(regeneratorRuntime.mark((function t(){return regeneratorRuntime.wrap((function(t){while(1)switch(t.prev=t.next){case 0:return t.next=2,e.validateAllFields();case 2:if(!t.sent){t.next=6;break}if(!e.deleteEmploymentType){t.next=5;break}return t.abrupt("return",e.removeEmploymentType());case 5:return t.abrupt("return",e.formValues.slug?e.editEmploymentType():e.createEmploymentType());case 6:case"end":return t.stop()}}),t)})))()},cancelForm:function(){this.$validator.errors.clear(),this.$emit("dismiss-form")},createEmploymentType:function(){var e=this;return Object(i["a"])(regeneratorRuntime.mark((function t(){return regeneratorRuntime.wrap((function(t){while(1)switch(t.prev=t.next){case 0:e.crud.message="Successfully created Employment Type",e.insertData(l["a"].postEmploymentType(e.orgSlug),e.formValues).then((function(t){e.$emit("dismiss-form",t,"employment_status")}));case 2:case"end":return t.stop()}}),t)})))()},editEmploymentType:function(){var e=this;return Object(i["a"])(regeneratorRuntime.mark((function t(){return regeneratorRuntime.wrap((function(t){while(1)switch(t.prev=t.next){case 0:e.crud.message="Successfully updated Employment Type",e.patchData(l["a"].updateEmploymentType(e.orgSlug,e.actionData.slug),e.formValues).then((function(){e.$emit("dismiss-form")}));case 2:case"end":return t.stop()}}),t)})))()},removeEmploymentType:function(){var e=this;return Object(i["a"])(regeneratorRuntime.mark((function t(){return regeneratorRuntime.wrap((function(t){while(1)switch(t.prev=t.next){case 0:e.crud.message="Successfully deleted Employment Type",e.deleteData(l["a"].deleteEmploymentType(e.orgSlug,e.actionData.slug)).then((function(){e.$emit("dismiss-form"),e.$emit("refresh")})).catch((function(t){var r=t.response.data.non_field_errors[0];e.notifyUser(r,"red"),e.$emit("dismiss-form")}));case 2:case"end":return t.stop()}}),t)})))()},clearForm:function(){this.errors.clear(),this.$refs.employmentTypeForm.reset(),this.clearNonFieldErrors()},cardTitleDetail:function(){this.actionData.title.length>0?(this.info.title="Update Details",this.info.subtitle="Here you can update organization employment type details",this.info.icon="mdi-pencil-outline"):(this.info.title="Create New",this.info.subtitle="Here you can create organization employment type",this.info.icon="mdi-file-edit-outline")}}},u=c,m=r("2877"),d=r("6544"),p=r.n(d),f=r("b0af"),v=r("99d9"),y=r("ac7c"),h=r("62ad"),b=r("ce7e"),x=r("4bd4"),g=r("0fd9b"),V=r("8654"),T=r("a844"),_=Object(m["a"])(u,n,a,!1,null,null,null);t["default"]=_.exports;p()(_,{VCard:f["a"],VCardText:v["c"],VCheckbox:y["a"],VCol:h["a"],VDivider:b["a"],VForm:x["a"],VRow:g["a"],VTextField:V["a"],VTextarea:T["a"]})},"878b":function(e,t,r){"use strict";var n=function(){var e=this,t=e.$createElement,r=e._self._c||t;return r("div",[r("v-card-actions",[r("v-spacer"),e.hideClear?e._e():r("v-btn",{attrs:{text:"",small:""},domProps:{textContent:e._s("Clear")},on:{click:function(t){return e.$emit("clearForm")}}}),r("v-btn",{attrs:{disabled:e.formErrors||e.disabled,color:e.deleteInstance?"red":"primary",depressed:"",small:"",loading:e.loading,type:"submit"}},[r("v-icon",{staticClass:"mr-1",attrs:{size:"14"}},[e._v(" mdi-content-save-outline ")]),e._v(" "+e._s(e.deleteInstance?"Delete":"Save")+" ")],1)],1)],1)},a=[],i={props:{hideClear:{type:Boolean,default:!1},formErrors:{type:Boolean,required:!0},disabled:{type:Boolean,default:!1},deleteInstance:{type:Boolean,required:!1,default:!1},loading:{type:Boolean,default:!1}}},o=i,s=r("2877"),l=r("6544"),c=r.n(l),u=r("8336"),m=r("99d9"),d=r("132d"),p=r("2fa4"),f=Object(s["a"])(o,n,a,!1,null,null,null);t["a"]=f.exports;c()(f,{VBtn:u["a"],VCardActions:m["a"],VIcon:d["a"],VSpacer:p["a"]})}}]);