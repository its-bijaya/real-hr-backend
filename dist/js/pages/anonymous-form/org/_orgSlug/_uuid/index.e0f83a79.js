(window["webpackJsonp"]=window["webpackJsonp"]||[]).push([["/pages/anonymous-form/org/_orgSlug/_uuid/index","chunk-da62e0c8","chunk-2d22d378"],{"1f04":function(t,e,n){"use strict";n.d(e,"b",(function(){return a})),n.d(e,"a",(function(){return u}));var r=n("1da1");n("d3b7"),n("3ca3"),n("ddb0"),n("96cf");function a(t){return o.apply(this,arguments)}function o(){return o=Object(r["a"])(regeneratorRuntime.mark((function t(e){var n,r;return regeneratorRuntime.wrap((function(t){while(1)switch(t.prev=t.next){case 0:return t.next=2,i(e);case 2:return n=t.sent,t.next=5,u([n]);case 5:return r=t.sent,t.abrupt("return",r[0]);case 7:case"end":return t.stop()}}),t)}))),o.apply(this,arguments)}function i(t){return s.apply(this,arguments)}function s(){return s=Object(r["a"])(regeneratorRuntime.mark((function t(e){var n;return regeneratorRuntime.wrap((function(t){while(1)switch(t.prev=t.next){case 0:return t.next=2,fetch(e);case 2:return n=t.sent,t.next=5,n.blob();case 5:return t.abrupt("return",t.sent);case 6:case"end":return t.stop()}}),t)}))),s.apply(this,arguments)}function u(t){return c.apply(this,arguments)}function c(){return c=Object(r["a"])(regeneratorRuntime.mark((function t(e){var n,r,a;return regeneratorRuntime.wrap((function(t){while(1)switch(t.prev=t.next){case 0:for(n=function(t){var e=new FileReader;return new Promise((function(n){e.readAsDataURL(t),e.onloadend=function(){n(e.result)}}))},r=[],a=0;a<e.length;a++)r.push(n(e[a]));return t.next=5,Promise.all(r);case 5:return t.abrupt("return",t.sent);case 6:case"end":return t.stop()}}),t)}))),c.apply(this,arguments)}},2940:function(t,e,n){"use strict";n.r(e);var r=function(){var t=this,e=t.$createElement,n=t._self._c||e;return n("v-container",{staticClass:"very-light-blue"},[n("v-row",[n("v-col",[n("v-card",{attrs:{flat:""}},[n("vue-card-title",{attrs:{title:t.formData.name||"Anonymous Survey & Forms",subtitle:"Please respond to below survey & forms",icon:"mdi-incognito",dark:""}}),n("v-card-text",[t.nonFieldErrors?n("non-field-form-errors",{attrs:{"non-field-errors":t.nonFieldErrors}}):t._e(),t.formData.description?n("v-row",[n("div",{domProps:{innerHTML:t._s(t.$sanitize(t.formData.description))}})]):t._e(),!t.formData.question_set||t.isObjectEmpty(t.formData.question_set)||t.submitted?t._e():n("questions-list",{attrs:{"question-details":t.formData.question_set,"updated-list":t.updatedQuestions},on:{"update:updatedList":function(e){t.updatedQuestions=e},"update:updated-list":function(e){t.updatedQuestions=e}}}),t.formData.disclaimer_text&&!t.submitted?n("v-row",[n("v-col",[n("span",{staticClass:"blueGrey--text"},[t._v(" Disclaimer : "+t._s(t.formData.disclaimer_text)+" ")])])],1):t._e(),t.submitted?n("div",[n("v-alert",{staticClass:"text-body-2 my-0 mt-2 py-1",attrs:{dense:"",text:"",type:"info"}},[t._v(" Successfully submitted survey & forms. Thank you for your response. ")])],1):t._e()],1),n("v-divider"),!t.formData.question_set||t.isObjectEmpty(t.formData.question_set)||t.submitted?t._e():n("v-card-actions",[n("v-spacer"),n("v-btn",{staticClass:"green white--text",attrs:{small:""},domProps:{textContent:t._s("Submit")},on:{click:t.submitForm}})],1)],1)],1)],1)],1)},a=[],o=(n("99af"),n("fb6e")),i=n("f0d5"),s=n("983c"),u=n("f70a"),c={components:{QuestionsList:o["default"]},mixins:[i["a"],s["a"],u["a"]],data:function(){return{formData:{},updatedQuestions:{},submitted:!1}},created:function(){var t=this;this.getData("forms/".concat(this.$route.params.orgSlug,"/anonymous/").concat(this.$route.params.uuid,"/")).then((function(e){t.formData=e}))},methods:{submitForm:function(){var t=this;this.insertData("/forms/".concat(this.$route.params.orgSlug,"/anonymous/").concat(this.$route.params.uuid,"/submit/"),{question:this.updatedQuestions}).then((function(){t.submitted=!0}))}}},d=c,l=n("2877"),f=n("6544"),m=n.n(f),p=n("0798"),h=n("8336"),v=n("b0af"),g=n("99d9"),b=n("62ad"),w=n("a523"),y=n("ce7e"),D=n("0fd9b"),_=n("2fa4"),x=Object(l["a"])(d,r,a,!1,null,null,null);e["default"]=x.exports;m()(x,{VAlert:p["a"],VBtn:h["a"],VCard:v["a"],VCardActions:g["a"],VCardText:g["c"],VCol:b["a"],VContainer:w["a"],VDivider:y["a"],VRow:D["a"],VSpacer:_["a"]})},"983c":function(t,e,n){"use strict";n("d3b7");e["a"]={methods:{getData:function(t,e,n){var r=this,a=arguments.length>3&&void 0!==arguments[3]&&arguments[3];return new Promise((function(o,i){!r.loading&&t&&(r.clearNonFieldErrors(),r.$validator.errors.clear(),r.loading=a,r.$http.get(t,n||{params:e||{}}).then((function(t){o(t),r.loading=!1})).catch((function(t){r.pushErrors(t),r.notifyInvalidFormResponse(),i(t),r.loading=!1})))}))},getBlockingData:function(t,e,n){var r=this;return new Promise((function(a,o){r.getData(t,e,n,!0).then((function(t){a(t)})).catch((function(t){o(t)}))}))}}}},f0d5:function(t,e,n){"use strict";n("d3b7"),n("3ca3"),n("ddb0");var r=n("c44a");e["a"]={components:{NonFieldFormErrors:function(){return n.e("chunk-6441e173").then(n.bind(null,"ab8a"))}},mixins:[r["a"]],data:function(){return{crud:{name:"record",message:"",addAnother:!1},formValues:{},loading:!1}}}},f70a:function(t,e,n){"use strict";n("d3b7"),n("caad");e["a"]={methods:{insertData:function(t,e){var n=this,r=arguments.length>2&&void 0!==arguments[2]?arguments[2]:{},a=r.validate,o=void 0===a||a,i=r.clearForm,s=void 0===i||i,u=arguments.length>3?arguments[3]:void 0;return new Promise((function(r,a){!n.loading&&t&&(n.clearErrors(),n.$validator.validateAll().then((function(i){o||(i=!0),i&&(n.loading=!0,n.$http.post(t,e,u||{}).then((function(t){n.clearErrors(),s&&(n.formValues={}),n.crud.addAnother||n.$emit("create"),n.crud.message&&setTimeout((function(){n.notifyUser(n.crud.message)}),1e3),r(t),n.loading=!1})).catch((function(t){n.pushErrors(t),n.notifyInvalidFormResponse(),a(t),n.loading=!1})))})))}))},patchData:function(t,e){var n=this,r=arguments.length>2&&void 0!==arguments[2]?arguments[2]:{},a=r.validate,o=void 0===a||a,i=r.clearForm,s=void 0===i||i,u=arguments.length>3?arguments[3]:void 0;return new Promise((function(r,a){n.updateData(t,e,{validate:o,clearForm:s},"patch",u).then((function(t){r(t)})).catch((function(t){a(t)}))}))},putData:function(t,e){var n=this,r=arguments.length>2&&void 0!==arguments[2]?arguments[2]:{},a=r.validate,o=void 0===a||a,i=r.clearForm,s=void 0===i||i,u=arguments.length>3?arguments[3]:void 0;return new Promise((function(r,a){n.updateData(t,e,{validate:o,clearForm:s},"put",u).then((function(t){r(t)})).catch((function(t){a(t)}))}))},updateData:function(t,e){var n=this,r=arguments.length>2&&void 0!==arguments[2]?arguments[2]:{},a=r.validate,o=void 0===a||a,i=r.clearForm,s=void 0===i||i,u=arguments.length>3?arguments[3]:void 0,c=arguments.length>4?arguments[4]:void 0;return new Promise((function(r,a){!n.loading&&t&&["put","patch"].includes(u)&&(n.clearErrors(),n.$validator.validateAll().then((function(i){o||(i=!0),i&&(n.loading=!0,n.$http[u](t,e,c||{}).then((function(t){n.$emit("update"),n.clearErrors(),s&&(n.formValues={}),n.crud.message&&setTimeout((function(){n.notifyUser(n.crud.message)}),1e3),r(t),n.loading=!1})).catch((function(t){n.pushErrors(t),n.notifyInvalidFormResponse(),a(t),n.loading=!1})))})))}))},clearErrors:function(){this.clearNonFieldErrors(),this.$validator.errors.clear()}}}}}]);