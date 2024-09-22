(window["webpackJsonp"]=window["webpackJsonp"]||[]).push([["pages/external-user/salarynegotiation","chunk-6441e173","chunk-2d22d378","chunk-2d213000"],{"0798":function(e,t,a){"use strict";var n=a("5530"),r=a("ade3"),i=(a("caad"),a("0c18"),a("10d2")),o=a("afdd"),s=a("9d26"),l=a("f2e7"),c=a("7560"),d=a("f40d"),u=a("58df"),m=a("d9bd");t["a"]=Object(u["a"])(i["a"],l["a"],d["a"]).extend({name:"v-alert",props:{border:{type:String,validator:function(e){return["top","right","bottom","left"].includes(e)}},closeLabel:{type:String,default:"$vuetify.close"},coloredBorder:Boolean,dense:Boolean,dismissible:Boolean,closeIcon:{type:String,default:"$cancel"},icon:{default:"",type:[Boolean,String],validator:function(e){return"string"===typeof e||!1===e}},outlined:Boolean,prominent:Boolean,text:Boolean,type:{type:String,validator:function(e){return["info","error","success","warning"].includes(e)}},value:{type:Boolean,default:!0}},computed:{__cachedBorder:function(){if(!this.border)return null;var e={staticClass:"v-alert__border",class:Object(r["a"])({},"v-alert__border--".concat(this.border),!0)};return this.coloredBorder&&(e=this.setBackgroundColor(this.computedColor,e),e.class["v-alert__border--has-color"]=!0),this.$createElement("div",e)},__cachedDismissible:function(){var e=this;if(!this.dismissible)return null;var t=this.iconColor;return this.$createElement(o["a"],{staticClass:"v-alert__dismissible",props:{color:t,icon:!0,small:!0},attrs:{"aria-label":this.$vuetify.lang.t(this.closeLabel)},on:{click:function(){return e.isActive=!1}}},[this.$createElement(s["a"],{props:{color:t}},this.closeIcon)])},__cachedIcon:function(){return this.computedIcon?this.$createElement(s["a"],{staticClass:"v-alert__icon",props:{color:this.iconColor}},this.computedIcon):null},classes:function(){var e=Object(n["a"])(Object(n["a"])({},i["a"].options.computed.classes.call(this)),{},{"v-alert--border":Boolean(this.border),"v-alert--dense":this.dense,"v-alert--outlined":this.outlined,"v-alert--prominent":this.prominent,"v-alert--text":this.text});return this.border&&(e["v-alert--border-".concat(this.border)]=!0),e},computedColor:function(){return this.color||this.type},computedIcon:function(){return!1!==this.icon&&("string"===typeof this.icon&&this.icon?this.icon:!!["error","info","success","warning"].includes(this.type)&&"$".concat(this.type))},hasColoredIcon:function(){return this.hasText||Boolean(this.border)&&this.coloredBorder},hasText:function(){return this.text||this.outlined},iconColor:function(){return this.hasColoredIcon?this.computedColor:void 0},isDark:function(){return!(!this.type||this.coloredBorder||this.outlined)||c["a"].options.computed.isDark.call(this)}},created:function(){this.$attrs.hasOwnProperty("outline")&&Object(m["a"])("outline","outlined",this)},methods:{genWrapper:function(){var e=[this.$slots.prepend||this.__cachedIcon,this.genContent(),this.__cachedBorder,this.$slots.append,this.$scopedSlots.close?this.$scopedSlots.close({toggle:this.toggle}):this.__cachedDismissible],t={staticClass:"v-alert__wrapper"};return this.$createElement("div",t,e)},genContent:function(){return this.$createElement("div",{staticClass:"v-alert__content"},this.$slots.default)},genAlert:function(){var e={staticClass:"v-alert",attrs:{role:"alert"},on:this.listeners$,class:this.classes,style:this.styles,directives:[{name:"show",value:this.isActive}]};if(!this.coloredBorder){var t=this.hasText?this.setTextColor:this.setBackgroundColor;e=t(this.computedColor,e)}return this.$createElement("div",e,[this.genWrapper()])},toggle:function(){this.isActive=!this.isActive}},render:function(e){var t=this.genAlert();return this.transition?e("transition",{props:{name:this.transition,origin:this.origin,mode:this.mode}},[t]):t}})},"0962":function(e,t,a){"use strict";a.r(t);var n=function(){var e=this,t=e.$createElement,a=e._self._c||t;return a("v-row",{staticClass:"mx-3",attrs:{align:"center",justify:"center"}},[a("v-col",{attrs:{md:"9",cols:"12"}},[a("candidate-response-form",{attrs:{mode:"editable","candidate-id":e.candidateId,"negotiation-id":e.negotiationId}})],1)],1)},r=[],i=a("598e"),o={components:{CandidateResponseForm:i["a"]},data:function(){return{candidateId:"",negotiationId:""}},created:function(){document.title="Salary Declaration Form | RealHRsoft | Complete HR Intelligence",this.candidateId=this.$route.params.candidateId,this.negotiationId=this.$route.params.negotiationId}},s=o,l=a("2877"),c=a("6544"),d=a.n(c),u=a("62ad"),m=a("0fd9b"),f=Object(l["a"])(s,n,r,!1,null,null,null);t["default"]=f.exports;d()(f,{VCol:u["a"],VRow:m["a"]})},"0c18":function(e,t,a){},"598e":function(e,t,a){"use strict";var n=function(){var e=this,t=e.$createElement,a=e._self._c||t;return a("div",[e.getPageError?a("v-main",[a("v-container",[a("page-not-found")],1)],1):a("v-card",[a("vue-card-title",{attrs:{icon:"mdi-calendar",title:"Salary Declaration ",subtitle:"readOnly"===e.mode?"View response from Candidate.":"Please fill up the form below."}},[a("template",{slot:"actions"},["readOnly"===e.mode?a("v-icon",{domProps:{textContent:e._s("mdi-close-circle")},on:{click:function(t){return e.$emit("create")}}}):e._e()],1)],2),a("v-divider"),e.sent?a("v-card-text",[a("v-alert",{attrs:{type:"success"}},[e._v("Form submitted successfully.")])],1):a("v-card-text",{staticClass:"scrollbar-md"},[a("v-row",[e.nonFieldErrors.length?a("v-col",{attrs:{cols:"12"}},[a("non-field-form-errors",{attrs:{"non-field-errors":e.nonFieldErrors}})],1):e._e(),a("v-col",{attrs:{md:"12",cols:"12"}},["readOnly"!==e.mode?a("v-text-field",e._b({directives:[{name:"validate",rawName:"v-validate",value:"required",expression:"'required'"}],staticClass:"py-0",attrs:{type:"number",min:"0",max:"100"},model:{value:e.formValues.salary,callback:function(t){e.$set(e.formValues,"salary",e._n(t))},expression:"formValues.salary"}},"v-text-field",e.veeValidate("salary","Salary *"),!1)):a("div",[a("span",[e._v(" Salary * ")]),a("div",{domProps:{textContent:e._s(e.actionData.salary)}})])],1),a("v-col",{attrs:{md:"12",cols:"12"}},["readOnly"!==e.mode?a("v-textarea",e._b({directives:[{name:"validate",rawName:"v-validate",value:"required|max:600",expression:"'required|max:600'"}],attrs:{counter:600,"prepend-inner-icon":"mdi-file-document-outline",rows:"2"},model:{value:e.formValues.candidate_remarks,callback:function(t){e.$set(e.formValues,"candidate_remarks",t)},expression:"formValues.candidate_remarks"}},"v-textarea",e.veeValidate("candidate_remarks","Remarks: *"),!1)):a("div",[a("span",[e._v(" Remarks * ")]),a("div",{domProps:{textContent:e._s(e.actionData.candidate_remarks||"N/A")}})])],1),"readOnly"!==e.mode?a("v-col",{attrs:{md:"12",cols:"12"}},[a("v-row",{attrs:{"no-gutters":""}},[a("v-icon",{attrs:{size:"16"},domProps:{textContent:e._s("mdi-file-upload-outline")}}),a("div",{staticClass:"mx-1"},[e._v("Documents *")])],1),a("v-row",{attrs:{"no-gutters":"",align:"baseline"}},[a("v-col",{staticClass:"text-left",attrs:{cols:"10"}},[a("file-upload",e._b({directives:[{name:"validate",rawName:"v-validate",value:"required",expression:"'required'"}],attrs:{"hide-details":""},model:{value:e.attachment,callback:function(t){e.attachment=t},expression:"attachment"}},"file-upload",e.veeValidate("attachment","*"),!1)),a("span",{staticClass:"danger--text mt-1"},[e._v(" "+e._s(e.errors.first("attachment"))+" ")])],1)],1)],1):e._e(),"readOnly"!==e.mode?a("v-col",{attrs:{md:"12",cols:"12"}},[a("div",e._l(e.attachments,(function(t,n){return a("ul",{key:n},[a("v-hover",{scopedSlots:e._u([{key:"default",fn:function(r){var i=r.hover;return a("li",{},[a("span",[e._v(" "+e._s(t.file.name)+" "),i?a("a",{on:{click:function(t){return e.attachments.splice(n,1)}}},[a("v-icon",{attrs:{color:"danger",small:""}},[e._v("mdi-close")])],1):e._e()])])}}],null,!0)})],1)})),0)]):a("v-col",{attrs:{md:"12",cols:"12"}},[a("span",[e._v(" Documents * ")]),a("ul",e._l(e.actionData.attachments,(function(t,n){return a("li",{key:n},[a("a",{on:{click:function(a){return e.viewAttachment(t.attachment)}}},[e._v(" "+e._s(t.name))])])})),0)])],1)],1),a("v-divider"),"readOnly"!==e.mode?a("v-card-actions",[a("v-spacer"),e.sent?e._e():a("v-btn",{attrs:{color:"primary",small:""},on:{click:function(t){return e.updateSalaryDeclaration()}}},[e._v(" Send ")])],1):e._e()],1),a("vue-notify")],1)},r=[],i=a("5530"),o=(a("99af"),a("f82f")),s=a("f0d5"),l=a("f70a"),c=a("c44a"),d=a("ab8a"),u=a("2f62"),m=a("9134"),f={components:{FileUpload:o["a"],NonFieldFormErrors:d["default"],PageNotFound:m["default"]},mixins:[c["a"],s["a"],l["a"]],props:{actionData:{type:Object,default:null},mode:{type:String,required:!0},candidateId:{type:String,default:""},negotiationId:{type:String,default:""}},data:function(){return{sent:!1,attachment:"",attachments:[],formValues:{},mapErrorCode:{"Permission Denied":"error403","Page Not Found":"error404","Internal Server Error":"error500"}}},computed:Object(i["a"])({},Object(u["c"])({getPageError:"common/getPageError"})),created:function(){this.setSnackBar({display:!1})},methods:Object(i["a"])(Object(i["a"])({},Object(u["d"])({setSnackBar:"common/setSnackBar"})),{},{getFormValues:function(){var e=new FormData;return e.append("candidate_remarks",this.formValues.candidate_remarks),e.append("status","Progress"),e.append("salary",this.formValues.salary),e.append("attachment[0]",this.attachment),e},viewAttachment:function(e){var t=e;window.open(t,"_blank")},appendFiles:function(){this.attachment?(this.attachments.unshift({file:this.attachment}),this.attachment=null):this.setSnackBar({text:"Please add attachment",color:"red"})},updateSalaryDeclaration:function(){var e=this;this.patchData("/recruitment/salary-declaration/".concat(this.candidateId,"/").concat(this.negotiationId,"/?organization=").concat(this.getOrganizationSlug),this.getFormValues()).then((function(){e.sent=!0,setTimeout((function(){e.notifyUser("Form submitted successfully.","success")}),500)}))}})},h=f,p=a("2877"),v=a("6544"),g=a.n(v),y=a("0798"),b=a("8336"),_=a("b0af"),x=a("99d9"),k=a("62ad"),C=a("a523"),S=a("ce7e"),$=a("ce87"),F=a("132d"),w=a("f6c4"),V=a("0fd9b"),B=a("2fa4"),E=a("8654"),O=a("a844"),D=Object(p["a"])(h,n,r,!1,null,null,null);t["a"]=D.exports;g()(D,{VAlert:y["a"],VBtn:b["a"],VCard:_["a"],VCardActions:x["a"],VCardText:x["c"],VCol:k["a"],VContainer:C["a"],VDivider:S["a"],VHover:$["a"],VIcon:F["a"],VMain:w["a"],VRow:V["a"],VSpacer:B["a"],VTextField:E["a"],VTextarea:O["a"]})},ab8a:function(e,t,a){"use strict";a.r(t);var n=function(){var e=this,t=e.$createElement,a=e._self._c||t;return a("div",[e.changeType&&0!==e.nonFieldErrors.length?a("div",e._l(e.nonFieldErrors,(function(t,n){return a("v-col",{key:n},e._l(t,(function(t,n){return a("div",{key:n},[a("span",{domProps:{textContent:e._s(e.key)}}),a("span",{domProps:{textContent:e._s(t.toString())}})])})),0)})),1):e._e(),e.changeType||0===e.nonFieldErrors.length?e._e():a("v-alert",{staticClass:"ma-3",attrs:{outlined:"",dense:"",tile:"",dismissible:"",color:"danger"}},[a("span",{domProps:{textContent:e._s("There are some errors")}}),e._l(e.nonFieldErrors,(function(t,n){return a("div",{key:n},e._l(t,(function(t,n){return a("div",{key:n},[a("ul",[a("li",[a("span",{domProps:{textContent:e._s(e.key)}}),a("span",{domProps:{textContent:e._s(t.toString())}})])])])})),0)}))],2)],1)},r=[],i={props:{nonFieldErrors:{type:Array,required:!0},changeType:{type:Boolean,default:!1}},data:function(){return{key:""}}},o=i,s=a("2877"),l=a("6544"),c=a.n(l),d=a("0798"),u=a("62ad"),m=Object(s["a"])(o,n,r,!1,null,null,null);t["default"]=m.exports;c()(m,{VAlert:d["a"],VCol:u["a"]})},ce87:function(e,t,a){"use strict";var n=a("16b7"),r=a("f2e7"),i=a("58df"),o=a("d9bd");t["a"]=Object(i["a"])(n["a"],r["a"]).extend({name:"v-hover",props:{disabled:{type:Boolean,default:!1},value:{type:Boolean,default:void 0}},methods:{onMouseEnter:function(){this.runDelay("open")},onMouseLeave:function(){this.runDelay("close")}},render:function(){return this.$scopedSlots.default||void 0!==this.value?(this.$scopedSlots.default&&(e=this.$scopedSlots.default({hover:this.isActive})),Array.isArray(e)&&1===e.length&&(e=e[0]),e&&!Array.isArray(e)&&e.tag?(this.disabled||(e.data=e.data||{},this._g(e.data,{mouseenter:this.onMouseEnter,mouseleave:this.onMouseLeave})),e):(Object(o["c"])("v-hover should only contain a single element",this),e)):(Object(o["c"])("v-hover is missing a default scopedSlot or bound value",this),null);var e}})},f0d5:function(e,t,a){"use strict";a("d3b7"),a("3ca3"),a("ddb0");var n=a("c44a");t["a"]={components:{NonFieldFormErrors:function(){return a.e("chunk-6441e173").then(a.bind(null,"ab8a"))}},mixins:[n["a"]],data:function(){return{crud:{name:"record",message:"",addAnother:!1},formValues:{},loading:!1}}}},f70a:function(e,t,a){"use strict";a("d3b7"),a("caad");t["a"]={methods:{insertData:function(e,t){var a=this,n=arguments.length>2&&void 0!==arguments[2]?arguments[2]:{},r=n.validate,i=void 0===r||r,o=n.clearForm,s=void 0===o||o,l=arguments.length>3?arguments[3]:void 0;return new Promise((function(n,r){!a.loading&&e&&(a.clearErrors(),a.$validator.validateAll().then((function(o){i||(o=!0),o&&(a.loading=!0,a.$http.post(e,t,l||{}).then((function(e){a.clearErrors(),s&&(a.formValues={}),a.crud.addAnother||a.$emit("create"),a.crud.message&&setTimeout((function(){a.notifyUser(a.crud.message)}),1e3),n(e),a.loading=!1})).catch((function(e){a.pushErrors(e),a.notifyInvalidFormResponse(),r(e),a.loading=!1})))})))}))},patchData:function(e,t){var a=this,n=arguments.length>2&&void 0!==arguments[2]?arguments[2]:{},r=n.validate,i=void 0===r||r,o=n.clearForm,s=void 0===o||o,l=arguments.length>3?arguments[3]:void 0;return new Promise((function(n,r){a.updateData(e,t,{validate:i,clearForm:s},"patch",l).then((function(e){n(e)})).catch((function(e){r(e)}))}))},putData:function(e,t){var a=this,n=arguments.length>2&&void 0!==arguments[2]?arguments[2]:{},r=n.validate,i=void 0===r||r,o=n.clearForm,s=void 0===o||o,l=arguments.length>3?arguments[3]:void 0;return new Promise((function(n,r){a.updateData(e,t,{validate:i,clearForm:s},"put",l).then((function(e){n(e)})).catch((function(e){r(e)}))}))},updateData:function(e,t){var a=this,n=arguments.length>2&&void 0!==arguments[2]?arguments[2]:{},r=n.validate,i=void 0===r||r,o=n.clearForm,s=void 0===o||o,l=arguments.length>3?arguments[3]:void 0,c=arguments.length>4?arguments[4]:void 0;return new Promise((function(n,r){!a.loading&&e&&["put","patch"].includes(l)&&(a.clearErrors(),a.$validator.validateAll().then((function(o){i||(o=!0),o&&(a.loading=!0,a.$http[l](e,t,c||{}).then((function(e){a.$emit("update"),a.clearErrors(),s&&(a.formValues={}),a.crud.message&&setTimeout((function(){a.notifyUser(a.crud.message)}),1e3),n(e),a.loading=!1})).catch((function(e){a.pushErrors(e),a.notifyInvalidFormResponse(),r(e),a.loading=!1})))})))}))},clearErrors:function(){this.clearNonFieldErrors(),this.$validator.errors.clear()}}}},f82f:function(e,t,a){"use strict";var n=function(){var e=this,t=e.$createElement,a=e._self._c||t;return a("div",[a("v-text-field",{class:e.appliedClass,attrs:{id:e.id,label:e.label,"data-cy":"input-file-upload",error:e.errorMessages.length>0,"error-messages":e.errorMessages,"hide-details":e.hideDetails,hint:e.hint,"persistent-hint":!!e.hint,disabled:e.disabled,readonly:"","prepend-inner-icon":"mdi-attachment","append-icon":"mdi-close"},on:{"click:prepend":e.pickFile,"click:append":function(t){return e.clear()},click:e.pickFile,blur:function(t){return e.$emit("blur")}},model:{value:e.fileName,callback:function(t){e.fileName=t},expression:"fileName"}}),a("input",{ref:"upload",staticClass:"d-none",attrs:{id:"fileUpload",type:"file",multiple:"multiple"},on:{change:e.upload}})],1)},r=[],i=a("1da1"),o=a("5530"),s=(a("96cf"),a("a9e3"),a("ac1f"),a("1276"),a("b0c0"),a("2f62")),l={props:{value:{type:[String,File,Object],default:void 0},default:{type:[String,File],default:void 0},text:{type:String,default:void 0},id:{type:String,default:""},label:{type:String,default:"Browse file from here"},hint:{type:String,default:void 0},errorMessages:{type:[String,Array],default:function(){return[]}},hideDetails:{type:Boolean,default:!1},disabled:{type:Boolean,default:!1},appliedClass:{type:String,default:""},returnObject:{type:Boolean,default:!1},maxSize:{type:Number,default:5}},data:function(){return{fileName:null}},watch:{default:{handler:function(e){!e||e instanceof File||(this.fileName=e)},immediate:!0},value:function(e){e||(this.fileName=""),document.getElementById("fileUpload").value=null}},methods:Object(o["a"])(Object(o["a"])({},Object(s["d"])({setSnackBar:"common/setSnackBar"})),{},{pickFile:function(){this.$refs.upload.click()},upload:function(e){var t=this;return Object(i["a"])(regeneratorRuntime.mark((function a(){var n,r;return regeneratorRuntime.wrap((function(a){while(1)switch(a.prev=a.next){case 0:n=new FileReader,n.readAsDataURL(e.target.files[0]),r="",1===e.target.files[0].name.split(".").length?r="Please upload known file type.":e.target.files[0].size>1024*t.maxSize*1024?r="File size cannot be greater than ".concat(t.maxSize,"MB."):"svg"===e.target.files[0].name.split(".").pop()&&(r="SVG image not allowed here."),r?t.setSnackBar({text:r,color:"red"}):n.onload=function(){t.returnObject?t.$emit("input",{file_name:e.target.files[0].name,file_content:e.target.files[0]}):t.$emit("input",e.target.files[0]),t.$emit("blur"),t.$emit("update",n.result),t.fileName=e.target.files[0].name};case 5:case"end":return a.stop()}}),a)})))()},clear:function(){this.fileName=null,this.returnObject?this.$emit("input",{file_name:"",file_content:""}):this.$emit("input",this.fileName)}})},c=l,d=a("2877"),u=a("6544"),m=a.n(u),f=a("8654"),h=Object(d["a"])(c,n,r,!1,null,null,null);t["a"]=h.exports;m()(h,{VTextField:f["a"]})}}]);