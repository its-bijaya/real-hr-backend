(window["webpackJsonp"]=window["webpackJsonp"]||[]).push([["chunk-017b8c30"],{"19e1":function(t,e,i){"use strict";i.r(e);var a=function(){var t=this,e=t.$createElement,i=t._self._c||e;return i("v-form",{staticClass:"overflow-y-hidden",on:{submit:function(e){return e.preventDefault(),t.getFormAction.apply(null,arguments)}}},[i("v-card",[t.showTitle?i("vue-card-title",{attrs:{title:t.formAction+" Letter / Email Template",subtitle:"",icon:"mdi-file-document-outline",closable:""},on:{close:function(e){return t.$emit("close")}}}):t._e(),i("v-divider"),i("v-card-text",{staticClass:"scrollbar-md"},[t.nonFieldErrors?i("non-field-form-errors",{attrs:{"non-field-errors":t.nonFieldErrors}}):t._e(),t.viewMode?i("v-row",{staticClass:"ma-3"},[i("v-col",{attrs:{md:"6",cols:"12"}},[i("div",{staticClass:"text-subtitle-2 blueGrey--text"},[i("v-icon",{attrs:{size:"18",color:"blueGrey"},domProps:{textContent:t._s("mdi-file-document-outline")}}),t._v(" Name ")],1),i("div",{staticClass:"pl-5",domProps:{textContent:t._s(t.formValues.name)}})]),i("v-col",{attrs:{md:"6",cols:"12"}},[i("div",{staticClass:"blueGrey--text"},[i("v-icon",{attrs:{size:"18",color:"blueGrey"},domProps:{textContent:t._s("mdi-calendar-check-outline")}}),t._v(" Type ")],1),i("div",{staticClass:"pl-5",domProps:{textContent:t._s(t.hintChoices.find((function(e){return e.value===t.formValues.type})).text)}})]),i("v-col",{attrs:{md:"12",cols:"12"}},[i("v-icon",{attrs:{size:"18",color:"blueGrey"},domProps:{textContent:t._s("mdi-help-circle-outline")}}),i("span",{staticClass:"mx-1 blueGrey--text",domProps:{textContent:t._s("Hints")}})],1),t._l(Object.keys(t.hintsList),(function(e,a){return i("v-col",{key:a,staticClass:"px-2 py-1",attrs:{md:"2",cols:"6"},on:{click:function(e){t.appendHints(Object.keys(t.hintsList)[a])}}},[i("v-tooltip",{attrs:{bottom:""},scopedSlots:t._u([{key:"activator",fn:function(a){var s=a.on;return[i("v-btn",t._g({staticClass:"blueGrey white--text",attrs:{small:"",block:""}},s),[t._v(" "+t._s(e)+" ")])]}}],null,!0)},[i("span",[t._v(" "+t._s(Object.values(t.hintsList)[a])+" ")])])],1)})),i("v-col",{attrs:{md:"12"}},[i("div",{staticClass:"my-2 blueGrey--text"},[i("v-icon",{attrs:{size:"18",color:"blueGrey"},domProps:{textContent:t._s("mdi-email-outline")}}),t._v(" Message ")],1),t.viewMode?i("div",{staticClass:"pl-5",domProps:{innerHTML:t._s(t.highlightText)}}):t._e()])],2):i("v-row",{staticClass:"ma-3"},[i("v-col",{staticClass:"px-1",attrs:{md:"6"}},[i("v-text-field",t._b({directives:[{name:"validate",rawName:"v-validate",value:"required",expression:"'required'"}],attrs:{readonly:t.viewMode,counter:"150","prepend-inner-icon":"mdi-file-document-outline"},model:{value:t.formValues.name,callback:function(e){t.$set(t.formValues,"name",e)},expression:"formValues.name"}},"v-text-field",t.veeValidate("name","Name *"),!1)),i("div",{staticClass:"mt-2"},[i("v-icon",{attrs:{size:"18"},domProps:{textContent:t._s("mdi-email-outline")}}),t._v(" Message ")],1),i("vue-trumbowyg",t._b({directives:[{name:"validate",rawName:"v-validate",value:"",expression:"''"}],ref:"trumbowyg",attrs:{id:"trumbowyg",placeholder:"Write a message for template."},model:{value:t.formValues.content,callback:function(e){t.$set(t.formValues,"content",e)},expression:"formValues.content"}},"vue-trumbowyg",t.veeValidate("content","Message *"),!1))],1),i("v-col",{attrs:{md:"6"}},[i("v-select",t._b({directives:[{name:"validate",rawName:"v-validate",value:"required",expression:"'required'"}],attrs:{items:t.hintChoices,"prepend-icon":"mdi-calendar-check-outline"},model:{value:t.formValues.type,callback:function(e){t.$set(t.formValues,"type",e)},expression:"formValues.type"}},"v-select",t.veeValidate("type","Type"),!1)),i("div",{staticClass:"mt-1"},[i("v-icon",{attrs:{size:"18"},domProps:{textContent:t._s("mdi-help-circle-outline")}}),i("span",{staticClass:"mx-1",domProps:{textContent:t._s("Hints")}}),t.hintsList?i("v-row",{staticClass:"pl-5 pt-2"},t._l(Object.keys(t.hintsList),(function(e,a){return i("v-col",{key:a,staticClass:"px-1",attrs:{cols:"4"},on:{click:function(e){t.appendHints(Object.keys(t.hintsList)[a])}}},[i("v-tooltip",{attrs:{bottom:""},scopedSlots:t._u([{key:"activator",fn:function(a){var s=a.on;return[i("v-btn",t._g({staticClass:"blueGrey white--text",attrs:{small:"",block:""}},s),[t._v(" "+t._s(e)+" ")])]}}],null,!0)},[i("span",[t._v(" "+t._s(Object.values(t.hintsList)[a])+" ")])])],1)})),1):t._e()],1)],1)],1)],1),i("v-divider"),t.viewMode?t._e():i("v-card-actions",[i("v-row",{attrs:{"no-gutters":""}},[i("v-col",{staticClass:"text-right"},[i("v-btn",{attrs:{outlined:"",color:"primary"},on:{click:t.clearForm}},[t._v(" Clear ")]),i("v-btn",{attrs:{color:"primary",depressed:"",type:"submit"}},[i("v-icon",{staticClass:"mr-1",attrs:{size:"14"}},[t._v(" mdi-content-save-outline ")]),t._v(" Save ")],1)],1)],1)],1)],1)],1)},s=[],n=i("ade3"),r=i("1da1"),o=(i("96cf"),i("ac1f"),i("5319"),i("4d63"),i("25f0"),i("caad"),i("b0c0"),i("f12b")),l=i("1467"),c=i("38ef"),u=i("50e3"),m=i("23fe"),d={components:{VueTrumbowyg:l["default"]},mixins:[o["a"]],props:{actionData:{type:Object,required:!0},viewMode:{type:Boolean,default:!1},hintChoices:{type:Array,required:!0},templateType:{type:String,required:!0,validator:function(t){return-1!==["email","letter","pre-employment","recruitment"].indexOf(t)}},showTitle:{type:Boolean,default:!1}},data:function(){return{formAction:"Create",formValues:{},hintsList:{},createApi:"",updateApi:"",hintApi:"",hintParams:""}},computed:{highlightText:function(){var t=this.$sanitize(this.formValues.message||this.formValues.content||"");return t.replace(new RegExp("{{.*?}}","gi"),(function(t){return t.replace("{{","").replace("}}",""),"<span class='blueGrey white--text px-1 mx-1' style='border-radius: 4px;'><span style='text-indent: 0;'>"+t.replace("{{","").replace("}}","")+"</span></span>"}))}},watch:{"formValues.type":function(){this.formValues.type&&this.getHints()}},created:function(){this.initializeFormValues(),this.initializeApi(),this.actionData.slug&&(this.formAction="Update",this.getHints()),this.viewMode&&(this.formAction="View")},methods:{initializeApi:function(){"email"===this.templateType?(this.createApi=c["a"].postTemplate,this.updateApi=c["a"].updateTemplate(this.actionData.slug),this.hintApi=c["a"].getTemplateHints,this.hintParams="type"):"letter"===this.templateType?(this.createApi=u["a"].postLetterTemplate(this.getOrganizationSlug),this.updateApi=u["a"].updateLetterTemplate(this.getOrganizationSlug,this.actionData.slug),this.hintApi=u["a"].getHints(this.getOrganizationSlug),this.hintParams="letter_type"):"recruitment"===this.templateType&&(this.createApi=m["a"].postLetterTemplate+"?organization=".concat(this.getOrganizationSlug,"&as=hr"),this.updateApi=m["a"].updateLetterTemplate(this.actionData.slug)+"?organization=".concat(this.getOrganizationSlug,"&as=hr"),this.hintApi=m["a"].getHints+"?organization=".concat(this.getOrganizationSlug,"&as=hr"),this.hintParams="template_type")},initializeFormValues:function(){this.formValues=this.deepCopy(this.actionData),["letter","recruitment"].includes(this.templateType)&&(this.formValues.name=this.actionData.title,this.formValues.content=this.actionData.message,delete this.formValues.title,delete this.formValues.message)},cancelForm:function(){this.viewMode=!1,this.$emit("dismiss-form")},appendHints:function(t){this.viewMode||this.insertTextAtCursor(t)},getFormAction:function(){var t=this.deepCopy(this.formValues);return["letter","recruitment"].includes(this.templateType)&&(t.title=this.formValues.name,t.message=this.formValues.content,delete t.name,delete t.content),this.formValues.slug?this.updateSMSTemplate(t):this.createSMSTemplate(t)},createSMSTemplate:function(t){var e=this;return Object(r["a"])(regeneratorRuntime.mark((function i(){return regeneratorRuntime.wrap((function(i){while(1)switch(i.prev=i.next){case 0:e.crud.message="Successfully created Template",e.insertData(e.createApi,t).then((function(t){e.$emit("dismiss-form",t,"template_letter"),e.$emit("dismissForm")}));case 2:case"end":return i.stop()}}),i)})))()},updateSMSTemplate:function(t){var e=this;return Object(r["a"])(regeneratorRuntime.mark((function i(){return regeneratorRuntime.wrap((function(i){while(1)switch(i.prev=i.next){case 0:e.validateAllFields(),e.crud.message="Successfully updated Email Template.",e.putData(e.updateApi,t).then((function(){e.$emit("dismissForm")}));case 3:case"end":return i.stop()}}),i)})))()},clearForm:function(){this.$validator.errors.clear(),this.clearNonFieldErrors(),this.formValues={},this.hintsList=[]},getHints:function(){var t=this;this.getData(this.hintApi,Object(n["a"])({},this.hintParams,this.formValues.type)).then((function(e){t.hintsList=e}))},insertTextAtCursor:function(t){var e,i,a;if(window.getSelection){if(e=window.getSelection(),!e.anchorNode.isContentEditable&&!e.anchorNode.parentNode.isContentEditable)return void this.notifyUser("Please place the cursor at desired location in text editor.","red");this.notifyUser("","",!1),e.getRangeAt&&e.rangeCount&&(i=e.getRangeAt(0),i.deleteContents(),a=document.createTextNode(t),i.insertNode(a))}"trumbowyg-editor"===a.parentNode.className?this.formValues.content=a.parentNode.innerHTML:this.formValues.content=a.parentNode.parentNode.innerHTML}}},p=d,h=(i("dc4d"),i("2877")),f=i("6544"),v=i.n(f),g=i("8336"),y=i("b0af"),b=i("99d9"),x=i("62ad"),C=i("ce7e"),V=i("4bd4"),w=i("132d"),_=i("0fd9b"),T=i("b974"),A=i("8654"),k=i("3a2f"),S=Object(h["a"])(p,a,s,!1,null,"7544d6a6",null);e["default"]=S.exports;v()(S,{VBtn:g["a"],VCard:y["a"],VCardActions:b["a"],VCardText:b["c"],VCol:x["a"],VDivider:C["a"],VForm:V["a"],VIcon:w["a"],VRow:_["a"],VSelect:T["a"],VTextField:A["a"],VTooltip:k["a"]})},"23fe":function(t,e,i){"use strict";e["a"]={getLetterTemplate:"/recruitment/template/",postLetterTemplate:"/recruitment/template/",updateLetterTemplate:function(t){return"/recruitment/template/".concat(t,"/")},deleteLetterTemplate:function(t){return"/recruitment/template/".concat(t,"/")},getHints:"/recruitment/template/hints/"}},6447:function(t,e,i){},dc4d:function(t,e,i){"use strict";i("6447")}}]);