(window["webpackJsonp"]=window["webpackJsonp"]||[]).push([["chunk-2d21ee9e"],{d81e:function(e,t,i){"use strict";i.r(t);var a=function(){var e=this,t=e.$createElement,i=e._self._c||t;return i("v-form",{ref:"jobTitleForm"},[i("v-card",[e.showTitle?i("vue-card-title",{attrs:{title:e.isEdit?"Update ":"Create Job Title",subtitle:"You can "+(e.isEdit?"Update":"Create")+" job title here",icon:e.isEdit?"mdi-pencil-outline":"mdi-account-outline",closable:""},on:{close:function(t){return e.$emit("dismiss-form")}}}):e._e(),i("v-card-text",[i("v-container",[i("v-row",[e.nonFieldErrors.length>0?i("v-col",{attrs:{cols:"12"}},[i("non-field-form-errors",{attrs:{"non-field-errors":e.nonFieldErrors}})],1):e._e(),i("v-col",{attrs:{cols:"12"}},[i("v-text-field",e._b({directives:[{name:"validate",rawName:"v-validate",value:"required|max:150",expression:"'required|max:150'"}],attrs:{counter:150,"prepend-inner-icon":"mdi-file-document-outline"},model:{value:e.formValues.title,callback:function(t){e.$set(e.formValues,"title",t)},expression:"formValues.title"}},"v-text-field",e.veeValidate("title","Title *"),!1)),i("v-textarea",e._b({directives:[{name:"validate",rawName:"v-validate",value:"max:600",expression:"'max:600'"}],attrs:{counter:600,rows:"3","prepend-inner-icon":"mdi-information-outline"},model:{value:e.formValues.description,callback:function(t){e.$set(e.formValues,"description",t)},expression:"formValues.description"}},"v-textarea",e.veeValidate("description","Description"),!1))],1)],1),i("v-divider"),i("div",[i("v-card-actions",[i("v-spacer"),i("v-btn",{attrs:{text:""},domProps:{textContent:e._s("Clear")},on:{click:e.clearForm}}),i("v-btn",{attrs:{color:"primary",depressed:"",loading:e.loading},on:{click:e.submitJobTitle}},[i("v-icon",{staticClass:"mr-1",attrs:{size:"14"}},[e._v(" mdi-content-save-outline ")]),e._v(" Save ")],1)],1)],1)],1)],1)],1)],1)},r=[],o=i("f0d5"),s=i("f70a"),n=i("86eb"),l={mixins:[s["a"],o["a"]],props:{showTitle:{type:Boolean,default:!1},activeAutoCompleteFormName:{type:String,default:""},actionData:{type:Object,required:!1,default:function(){return{title:"",description:""}}},orgSlug:{type:String,required:!0},isEdit:{type:Boolean,default:!1}},data:function(){return{formValues:this.actionData}},computed:{},created:function(){},methods:{submitJobTitle:function(){var e=this;this.isEdit?(this.crud.message="Successfully updated Job Title",this.patchData(n["a"].updateJobTitle(this.orgSlug,this.actionData.slug),this.formValues).then((function(){e.$emit("dismiss-form")}))):(this.crud.message="Successfully created Job Title",this.insertData(n["a"].postJobTitle(this.orgSlug),this.formValues).then((function(t){e.$emit("dismiss-form",t,"job_title")})))},clearForm:function(){this.errors.clear(),this.$refs.jobTitleForm.reset(),this.clearNonFieldErrors()}}},c=l,d=i("2877"),u=i("6544"),m=i.n(u),f=i("8336"),v=i("b0af"),p=i("99d9"),b=i("62ad"),h=i("a523"),V=i("ce7e"),x=i("4bd4"),T=i("132d"),g=i("0fd9b"),w=i("2fa4"),C=i("8654"),F=i("a844"),_=Object(d["a"])(c,a,r,!1,null,null,null);t["default"]=_.exports;m()(_,{VBtn:f["a"],VCard:v["a"],VCardActions:p["a"],VCardText:p["c"],VCol:b["a"],VContainer:h["a"],VDivider:V["a"],VForm:x["a"],VIcon:T["a"],VRow:g["a"],VSpacer:w["a"],VTextField:C["a"],VTextarea:F["a"]})}}]);