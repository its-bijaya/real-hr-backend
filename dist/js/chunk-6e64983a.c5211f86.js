(window["webpackJsonp"]=window["webpackJsonp"]||[]).push([["chunk-6e64983a","chunk-2d22d378"],{4276:function(e,t,n){"use strict";t["a"]={getDocumentCategory:"/commons/document-category/",postDocumentCategory:"/commons/document-category/",updateDocumentCategory:function(e){return"/commons/document-category/".concat(e,"/")},deleteDocumentCategory:function(e){return"/commons/document-category/".concat(e,"/")}}},"6c6f":function(e,t,n){"use strict";n("d3b7");t["a"]={data:function(){return{deleteNotification:{dialog:!1,heading:"Confirm Delete",text:"Are you sure you want to delete ?"}}},methods:{deleteData:function(e,t){var n=this;return new Promise((function(a,o){!n.loading&&e&&(n.loading=!0,n.$http.delete(e,t||{}).then((function(e){n.crud.message&&setTimeout((function(){n.notifyUser(n.crud.message)}),1e3),a(e),n.loading=!1})).catch((function(e){n.pushErrors(e),n.notifyInvalidFormResponse(),o(e),n.loading=!1})).finally((function(){n.deleteNotification.dialog=!1})))}))}}}},"8cd3":function(e,t,n){"use strict";var a=n("5530"),o=(n("d3b7"),n("f0d5"));t["a"]={mixins:[o["a"]],data:function(){return{dataTableEndpoint:"",fetchedResults:[],response:null,footerProps:{itemsPerPageOptions:[10,20,30,40,50,100]},pagination:{sortBy:["modified_at"],descending:!1,totalItems:0,page:1,rowsPerPage:10,pageCount:0},loadTableOnInit:!0}},computed:{filterParams:function(){var e=Object(a["a"])(Object(a["a"])({},this.dataTableFilter),{},{offset:(this.pagination.page-1)*this.pagination.rowsPerPage,limit:this.pagination.rowsPerPage,ordering:this.pagination.descending?this.pagination.sortBy:"-"+this.pagination.sortBy});return this.convertToURLSearchParams(e,!1)}},watch:{filterParams:function(){var e=this;this.$nextTick((function(){e.fetchDataTable()}))},dataTableFilter:function(){this.pagination.page=1}},created:function(){var e=this;setTimeout((function(){e.loadTableOnInit&&e.fetchDataTable()}),0)},methods:{fetchDataTable:function(e,t){var n=this;return new Promise((function(a,o){!e&&!n.dataTableEndpoint||n.loading||(n.loadTableOnInit=!1,n.loading=!0,n.fetchedResults=[],n.$http.get(e||n.dataTableEndpoint,t||{params:n.filterParams}).then((function(e){n.response=e,n.fetchedResults=e.results,n.pagination.totalItems=e.count,n.processAfterTableLoad(e),a(e),n.loading=!1})).catch((function(e){n.pushErrors(e),n.notifyInvalidFormResponse(),o(e),n.loading=!1})))}))},processAfterTableLoad:function(){}}}},a79c:function(e,t,n){"use strict";n.d(t,"b",(function(){return o})),n.d(t,"a",(function(){return i}));var a=n("53ca");n("b0c0");function o(e,t,n){var r,s,l=t||new FormData;for(var c in e)if(Object.prototype.hasOwnProperty.call(e,c))if(r=n?n+"."+c:c,s=e[c],"boolean"===typeof s||"number"===typeof s)l.append(r,s);else if(Array.isArray(s))for(var d=0;d<s.length;d++)l.append(r,s[d]);else"object"!==Object(a["a"])(s)||i(s)?i(s)?l.append(r,s,s.name):s?l.append(r,s):s||"undefined"!==typeof s&&l.append(r,""):o(s,l,c);return l}function i(e){return e instanceof File||e instanceof Blob}},ad9de:function(e,t,n){"use strict";n.r(t);var a=function(){var e=this,t=e.$createElement,n=e._self._c||t;return n("div",[n("v-card",[n("vue-card-title",{attrs:{title:"Document Details",subtitle:e.cardText+e.userName,icon:"mdi-file-document-outline"}},[n("template",{slot:"actions"},[e.showForm||e.getAuthStateUserId!==parseInt(e.$route.params.id)&&!e.verifyPermission(e.allPermissions.CAN_CREATE_UPDATE_USER_PROFILE)||"supervisor"===e.as||e.loading?e._e():n("v-btn",{attrs:{small:"",color:"primary",depressed:""},on:{click:function(t){return e.openForm()}}},[e._v("Create New")]),e.showForm?n("v-btn",{attrs:{small:"","data-cy":"btn-filter",color:"primary",outlined:""},on:{click:e.dismissForm}},[e._v(" Cancel ")]):e._e()],1)],2),n("v-divider"),!e.showForm&&e.fetchedResults.length?n("v-data-table",{attrs:{headers:e.headers,items:e.fetchedResults,loading:e.loading,"sort-desc":e.pagination.descending,"sort-by":e.pagination.sortBy,page:e.pagination.page,"items-per-page":e.pagination.rowsPerPage,"footer-props":e.footerProps,"server-items-length":e.pagination.totalItems,"must-sort":""},on:{"update:sortDesc":function(t){return e.$set(e.pagination,"descending",t)},"update:sort-desc":function(t){return e.$set(e.pagination,"descending",t)},"update:sortBy":function(t){return e.$set(e.pagination,"sortBy",t)},"update:sort-by":function(t){return e.$set(e.pagination,"sortBy",t)},"update:page":function(t){return e.$set(e.pagination,"page",t)},"update:itemsPerPage":function(t){return e.$set(e.pagination,"rowsPerPage",t)},"update:items-per-page":function(t){return e.$set(e.pagination,"rowsPerPage",t)}},scopedSlots:e._u([{key:"item",fn:function(t){return[n("tr",[n("td",[n("v-tooltip",{attrs:{top:""},scopedSlots:e._u([{key:"activator",fn:function(a){var o=a.on;return[n("span",e._g({},o),[e._v(" "+e._s(e._f("truncate")(t.item.title,50))+" ")])]}}],null,!0)},[n("span",{domProps:{textContent:e._s(t.item.title)}})])],1),n("td",[e._v(" "+e._s(e.get(t.item,"document_type.name","N/A"))+" ")]),n("td",[n("vue-user",{attrs:{user:t.item.uploaded_by}})],1),n("td",[n("vue-context-menu",{attrs:{"context-list":[{name:"View Document",icon:"mdi-eye-outline",color:"blue"},{name:"Download Document",icon:"mdi-file-download-outline",color:"blue"},{name:"Delete Document",hide:"supervisor"===e.as,icon:"mdi-trash-can-outline",color:"red"}]},on:{click0:function(n){return e.viewAttachment(t.item.file)},click1:function(n){return e.downloadAttachment(t.item)},click2:function(n){e.form.actionData=t.item,e.deleteNotification.dialog=!0}}})],1)])]}}],null,!1,294881241)},[n("template",{slot:"no-data"},[n("data-table-no-data",{attrs:{text:e.userName+" hasn't added any documents yet",loading:e.loading}})],1)],2):e._e(),e.showForm||e.fetchedResults.length?e._e():n("vue-no-data"),e.showForm?n("document-form",{attrs:{as:e.as},on:{"close-form":e.dismissForm}}):e._e()],1),n("vue-dialog",{attrs:{notify:e.deleteNotification},on:{agree:e.deleteDocument,close:function(t){e.deleteNotification.dialog=!1}},model:{value:e.deleteNotification.dialog,callback:function(t){e.$set(e.deleteNotification,"dialog",t)},expression:"deleteNotification.dialog"}})],1)},o=[],i=n("db09"),r=function(){var e=this,t=e.$createElement,n=e._self._c||t;return n("v-form",{ref:"employeeDocumentForm"},[n("v-container",{staticClass:"px-12"},[e.nonFieldErrors?n("non-field-form-errors",{attrs:{"non-field-errors":e.nonFieldErrors}}):e._e(),n("v-row",[n("v-col",{attrs:{md:"6",sm:"12"}},[n("v-text-field",e._b({directives:[{name:"validate",rawName:"v-validate",value:"required|max:150",expression:"'required|max:150'"}],attrs:{counter:150,"prepend-inner-icon":"mdi-folder-outline"},model:{value:e.formValues.title,callback:function(t){e.$set(e.formValues,"title",t)},expression:"formValues.title"}},"v-text-field",e.veeValidate("title","Document Title *"),!1))],1),n("v-col",{attrs:{md:"6",sm:"12"}},[n("vue-auto-complete",e._b({directives:[{name:"validate",rawName:"v-validate",value:"required",expression:"'required'"}],attrs:{endpoint:e.documentCategoryEndpoint,"prepend-inner-icon":"mdi-text-box-outline","item-text":"name","item-value":"slug"},model:{value:e.formValues.document_type,callback:function(t){e.$set(e.formValues,"document_type",t)},expression:"formValues.document_type"}},"vue-auto-complete",e.veeValidate("document_type","Document Type *"),!1))],1),n("v-col",{attrs:{md:"6",sm:"12"}},[n("file-upload",e._b({directives:[{name:"validate",rawName:"v-validate",value:"required",expression:"'required'"}],attrs:{default:e.formValues.file},model:{value:e.formValues.file,callback:function(t){e.$set(e.formValues,"file",t)},expression:"formValues.file"}},"file-upload",e.veeValidate("file","Attachment *"),!1))],1)],1)],1),n("v-divider"),n("v-card-actions",[n("v-spacer"),n("v-btn",{attrs:{disabled:e.errors.any(),depressed:"","data-cy":"btn-save-and-add-another",color:"primary"},on:{click:e.addAnother}},[e._v(" Save and Add Another ")]),n("v-btn",{attrs:{disabled:e.errors.any(),depressed:"","data-cy":"btn-save",color:"primary"},on:{click:e.createDocument}},[e._v(" Save ")]),n("v-btn",{on:{click:e.clearForm}},[e._v(" Clear ")])],1)],1)},s=[],l=(n("d3b7"),n("f0d5")),c=n("f70a"),d=n("f82f"),u=n("5660"),f=n("a79c"),m=(n("99af"),{getUserDocuments:function(e){return"/users/".concat(e,"/documents/")},postUserDocument:function(e){return"/users/".concat(e,"/documents/")},getDocumentDetail:function(e,t){return"/users/".concat(e,"/documents/").concat(t,"/")},updateDocumentDetail:function(e,t){return"/users/".concat(e,"/documents/").concat(t,"/")},deleteUserDocument:function(e,t){return"/users/".concat(e,"/documents/").concat(t,"/")}}),p=n("4276"),h={components:{FileUpload:d["a"],VueAutoComplete:u["default"]},mixins:[l["a"],c["a"]],props:{as:{type:String,default:""}},data:function(){return{formValues:{},documentCategoryEndpoint:"",saveAndAddAnother:!1}},created:function(){this.documentCategoryEndpoint=p["a"].getDocumentCategory+"?for=Employee"},methods:{createDocument:function(){var e=this;this.insertData(m.postUserDocument(this.$route.params.id)+"?as=".concat(this.as),Object(f["b"])(this.formValues)).then((function(){e.verifyPermission(e.allPermissions.CAN_CREATE_UPDATE_USER_PROFILE)&&e.$route.params.slug?(e.notifyUser("Successfully added Document","green"),e.saveAndAddAnother?e.clearForm():e.$emit("close-form")):(e.notifyUser("Profile Change request has been sent","green"),e.saveAndAddAnother?e.clearForm():e.$router.push({name:"user-profile-change-request"}))})).finally((function(){e.saveAndAddAnother=!1}))},addAnother:function(){this.saveAndAddAnother=!0,this.createDocument()},clearForm:function(){this.errors.clear(),this.$refs.employeeDocumentForm.reset(),this.clearNonFieldErrors()}}},g=h,v=n("2877"),b=n("6544"),y=n.n(b),D=n("8336"),_=n("99d9"),w=n("62ad"),F=n("a523"),A=n("ce7e"),x=n("4bd4"),P=n("0fd9b"),E=n("2fa4"),$=n("8654"),T=Object(v["a"])(g,r,s,!1,null,null,null),V=T.exports;y()(T,{VBtn:D["a"],VCardActions:_["a"],VCol:w["a"],VContainer:F["a"],VDivider:A["a"],VForm:x["a"],VRow:P["a"],VSpacer:E["a"],VTextField:$["a"]});var N=n("02cb"),k=n("a51f"),C=n("e585"),S=n("e4bf"),U={components:{VueContextMenu:S["default"],DocumentForm:V,VueUser:N["default"],DataTableNoData:k["default"],VueNoData:C["default"]},mixins:[i["a"]],props:{userInfo:{type:Object,default:function(){return{}}},as:{type:String,default:""}},data:function(){return{headers:[{text:"Document Name",align:"left",sortable:!0,value:"title"},{text:"Document Type",align:"left",sortable:!0,value:"document_type"},{text:"Uploaded By",align:"left",sortable:!0,value:"uploaded_by"},{text:"Action",align:"",sortable:!1}],cardText:"List of Documents of ",deleteNotification:{dialog:!1,heading:"Confirm Delete",text:"Are you sure you want to delete this document?"},showForm:!1,form:{actionData:void 0}}},computed:{userName:function(){return this.userInfo.user.first_name+" "+this.userInfo.user.middle_name+" "+this.userInfo.user.last_name}},created:function(){this.dataTableEndpoint=m.getUserDocuments(this.$route.params.id)+"?as=".concat(this.as)},methods:{openForm:function(){this.cardText="Create Document of ",this.showForm=!0},viewAttachment:function(e){var t="https://docs.google.com/viewerng/viewer?url=".concat(e);window.open(t,"_blank")},downloadAttachment:function(e){window.open(e.file,"_blank")},dismissForm:function(){this.fetchDataTable(),this.form.actionData=void 0,this.deleteNotification.dialog=!1,this.showForm=!1,this.cardText="List of Documents of "},deleteDocument:function(){var e=this,t=this.verifyPermission(this.allPermissions.CAN_CREATE_UPDATE_USER_PROFILE)&&this.$route.params.slug;this.crud.message=t?"Successfully deleted Document":"Profile Change request has been sent",this.deleteData(m.deleteUserDocument(this.$route.params.id,this.form.actionData.slug)+"?as=".concat(this.as)).then((function(){t?e.dismissForm():e.$router.push({name:"user-profile-change-request"})})).catch((function(){var t=e.nonFieldErrors[0]["non field errors"];e.notifyUser(t,"red"),e.dismissForm()}))}}},O=U,R=n("b0af"),B=n("8fea"),I=n("3a2f"),j=Object(v["a"])(O,a,o,!1,null,null,null);t["default"]=j.exports;y()(j,{VBtn:D["a"],VCard:R["a"],VDataTable:B["a"],VDivider:A["a"],VTooltip:I["a"]})},db09:function(e,t,n){"use strict";var a=n("6c6f"),o=n("8cd3");t["a"]={mixins:[a["a"],o["a"]]}},f0d5:function(e,t,n){"use strict";n("d3b7"),n("3ca3"),n("ddb0");var a=n("c44a");t["a"]={components:{NonFieldFormErrors:function(){return n.e("chunk-6441e173").then(n.bind(null,"ab8a"))}},mixins:[a["a"]],data:function(){return{crud:{name:"record",message:"",addAnother:!1},formValues:{},loading:!1}}}},f70a:function(e,t,n){"use strict";n("d3b7"),n("caad");t["a"]={methods:{insertData:function(e,t){var n=this,a=arguments.length>2&&void 0!==arguments[2]?arguments[2]:{},o=a.validate,i=void 0===o||o,r=a.clearForm,s=void 0===r||r,l=arguments.length>3?arguments[3]:void 0;return new Promise((function(a,o){!n.loading&&e&&(n.clearErrors(),n.$validator.validateAll().then((function(r){i||(r=!0),r&&(n.loading=!0,n.$http.post(e,t,l||{}).then((function(e){n.clearErrors(),s&&(n.formValues={}),n.crud.addAnother||n.$emit("create"),n.crud.message&&setTimeout((function(){n.notifyUser(n.crud.message)}),1e3),a(e),n.loading=!1})).catch((function(e){n.pushErrors(e),n.notifyInvalidFormResponse(),o(e),n.loading=!1})))})))}))},patchData:function(e,t){var n=this,a=arguments.length>2&&void 0!==arguments[2]?arguments[2]:{},o=a.validate,i=void 0===o||o,r=a.clearForm,s=void 0===r||r,l=arguments.length>3?arguments[3]:void 0;return new Promise((function(a,o){n.updateData(e,t,{validate:i,clearForm:s},"patch",l).then((function(e){a(e)})).catch((function(e){o(e)}))}))},putData:function(e,t){var n=this,a=arguments.length>2&&void 0!==arguments[2]?arguments[2]:{},o=a.validate,i=void 0===o||o,r=a.clearForm,s=void 0===r||r,l=arguments.length>3?arguments[3]:void 0;return new Promise((function(a,o){n.updateData(e,t,{validate:i,clearForm:s},"put",l).then((function(e){a(e)})).catch((function(e){o(e)}))}))},updateData:function(e,t){var n=this,a=arguments.length>2&&void 0!==arguments[2]?arguments[2]:{},o=a.validate,i=void 0===o||o,r=a.clearForm,s=void 0===r||r,l=arguments.length>3?arguments[3]:void 0,c=arguments.length>4?arguments[4]:void 0;return new Promise((function(a,o){!n.loading&&e&&["put","patch"].includes(l)&&(n.clearErrors(),n.$validator.validateAll().then((function(r){i||(r=!0),r&&(n.loading=!0,n.$http[l](e,t,c||{}).then((function(e){n.$emit("update"),n.clearErrors(),s&&(n.formValues={}),n.crud.message&&setTimeout((function(){n.notifyUser(n.crud.message)}),1e3),a(e),n.loading=!1})).catch((function(e){n.pushErrors(e),n.notifyInvalidFormResponse(),o(e),n.loading=!1})))})))}))},clearErrors:function(){this.clearNonFieldErrors(),this.$validator.errors.clear()}}}},f82f:function(e,t,n){"use strict";var a=function(){var e=this,t=e.$createElement,n=e._self._c||t;return n("div",[n("v-text-field",{class:e.appliedClass,attrs:{id:e.id,label:e.label,"data-cy":"input-file-upload",error:e.errorMessages.length>0,"error-messages":e.errorMessages,"hide-details":e.hideDetails,hint:e.hint,"persistent-hint":!!e.hint,disabled:e.disabled,readonly:"","prepend-inner-icon":"mdi-attachment","append-icon":"mdi-close"},on:{"click:prepend":e.pickFile,"click:append":function(t){return e.clear()},click:e.pickFile,blur:function(t){return e.$emit("blur")}},model:{value:e.fileName,callback:function(t){e.fileName=t},expression:"fileName"}}),n("input",{ref:"upload",staticClass:"d-none",attrs:{id:"fileUpload",type:"file",multiple:"multiple"},on:{change:e.upload}})],1)},o=[],i=n("1da1"),r=n("5530"),s=(n("96cf"),n("a9e3"),n("ac1f"),n("1276"),n("b0c0"),n("2f62")),l={props:{value:{type:[String,File,Object],default:void 0},default:{type:[String,File],default:void 0},text:{type:String,default:void 0},id:{type:String,default:""},label:{type:String,default:"Browse file from here"},hint:{type:String,default:void 0},errorMessages:{type:[String,Array],default:function(){return[]}},hideDetails:{type:Boolean,default:!1},disabled:{type:Boolean,default:!1},appliedClass:{type:String,default:""},returnObject:{type:Boolean,default:!1},maxSize:{type:Number,default:5}},data:function(){return{fileName:null}},watch:{default:{handler:function(e){!e||e instanceof File||(this.fileName=e)},immediate:!0},value:function(e){e||(this.fileName=""),document.getElementById("fileUpload").value=null}},methods:Object(r["a"])(Object(r["a"])({},Object(s["d"])({setSnackBar:"common/setSnackBar"})),{},{pickFile:function(){this.$refs.upload.click()},upload:function(e){var t=this;return Object(i["a"])(regeneratorRuntime.mark((function n(){var a,o;return regeneratorRuntime.wrap((function(n){while(1)switch(n.prev=n.next){case 0:a=new FileReader,a.readAsDataURL(e.target.files[0]),o="",1===e.target.files[0].name.split(".").length?o="Please upload known file type.":e.target.files[0].size>1024*t.maxSize*1024?o="File size cannot be greater than ".concat(t.maxSize,"MB."):"svg"===e.target.files[0].name.split(".").pop()&&(o="SVG image not allowed here."),o?t.setSnackBar({text:o,color:"red"}):a.onload=function(){t.returnObject?t.$emit("input",{file_name:e.target.files[0].name,file_content:e.target.files[0]}):t.$emit("input",e.target.files[0]),t.$emit("blur"),t.$emit("update",a.result),t.fileName=e.target.files[0].name};case 5:case"end":return n.stop()}}),n)})))()},clear:function(){this.fileName=null,this.returnObject?this.$emit("input",{file_name:"",file_content:""}):this.$emit("input",this.fileName)}})},c=l,d=n("2877"),u=n("6544"),f=n.n(u),m=n("8654"),p=Object(d["a"])(c,a,o,!1,null,null,null);t["a"]=p.exports;f()(p,{VTextField:m["a"]})}}]);