(window["webpackJsonp"]=window["webpackJsonp"]||[]).push([["/components/PerformanceAppraisal/Settings/KeyFormSettings","chunk-2d0c8a11","chunk-da62e0c8","chunk-2d22d378"],{"05d7":function(t,e,a){"use strict";a.r(e);var n=function(){var t=this,e=t.$createElement,a=t._self._c||e;return a("v-card",[a("vue-card-title",{attrs:{title:"Key Form settings",subtitle:"This page contains Key Form settings.",icon:"mdi-format-float-right",closable:""},on:{close:function(e){return t.$emit("close")}}}),a("v-divider"),a("v-card-text",{staticClass:"scrollbar-md"},[t.nonFieldErrors?a("non-field-form-errors",{attrs:{"non-field-errors":t.nonFieldErrors}}):t._e(),t.loading?t._e():a("v-row",{attrs:{dense:"",align:"center"}},[a("v-col",{staticClass:"blueGrey--text font-weight-medium",attrs:{cols:"12"}},[a("span",[t._v("Instructions for Appraiser :")])]),a("v-col",{attrs:{cols:"12"}},[a("vue-trumbowyg",{staticClass:"vue",model:{value:t.formValues.instruction_for_evaluator,callback:function(e){t.$set(t.formValues,"instruction_for_evaluator",e)},expression:"formValues.instruction_for_evaluator"}})],1),a("v-col",{attrs:{cols:"12"}},[a("v-switch",{staticClass:"pa-0 ma-0",attrs:{color:"teal lighten-2",ripple:!1,label:"Include KSA as Rating Questions",dense:"","hide-details":""},model:{value:t.formValues.include_ksa,callback:function(e){t.$set(t.formValues,"include_ksa",e)},expression:"formValues.include_ksa"}})],1),t.formValues.include_ksa?[a("v-col",{attrs:{cols:"12"}},[a("v-text-field",t._b({directives:[{name:"validate",rawName:"v-validate",value:"max:255",expression:"'max:255'"}],attrs:{counter:255,placeholder:"Enter caption for KSA Question",dense:""},model:{value:t.formValues.caption_for_ksa,callback:function(e){t.$set(t.formValues,"caption_for_ksa",e)},expression:"formValues.caption_for_ksa"}},"v-text-field",t.veeValidate("caption_for_ksa","Caption For KSA"),!1))],1),a("v-col",{staticClass:"blueGrey--text font-weight-medium",attrs:{cols:"12"}},[a("span",[t._v("Select answer fields for all KSA questions :")])]),t._l(t.formValues.kaar_answer_types.filter((function(t){return"ksa"===t.question_type})),(function(e,n){return a("v-row",{key:"ksa-"+n,attrs:{align:"center",dense:""}},[a("v-col",{attrs:{cols:"2"}},[a("span",[t._v(t._s(t.scaleMap[e.answer_type]))])]),a("v-col",{attrs:{cols:"7"}},[a("v-text-field",t._b({directives:[{name:"validate",rawName:"v-validate",value:"max:600",expression:"'max:600'"}],attrs:{counter:600,label:"Description",dense:""},model:{value:e.description,callback:function(a){t.$set(e,"description",a)},expression:"item.description"}},"v-text-field",t.veeValidate("ksa-description-"+n,"Description"),!1))],1),a("v-col",{attrs:{cols:"3"}},[a("v-switch",{staticClass:"pa-0 ma-0",attrs:{color:"teal lighten-2",ripple:!1,label:"Mandatory Field",dense:"","hide-details":""},model:{value:e.is_mandatory,callback:function(a){t.$set(e,"is_mandatory",a)},expression:"item.is_mandatory"}})],1)],1)}))]:t._e(),a("v-col",{attrs:{cols:"12"}},[a("v-switch",{staticClass:"pa-0 ma-0",attrs:{color:"teal lighten-2",ripple:!1,label:"Include KPI as Rating Questions",dense:"","hide-details":""},model:{value:t.formValues.include_kpi,callback:function(e){t.$set(t.formValues,"include_kpi",e)},expression:"formValues.include_kpi"}})],1),t.formValues.include_kpi?[a("v-col",{attrs:{cols:"12"}},[a("v-text-field",t._b({directives:[{name:"validate",rawName:"v-validate",value:"max:255",expression:"'max:255'"}],attrs:{counter:255,placeholder:"Enter caption for KPI Question",dense:""},model:{value:t.formValues.caption_for_kpi,callback:function(e){t.$set(t.formValues,"caption_for_kpi",e)},expression:"formValues.caption_for_kpi"}},"v-text-field",t.veeValidate("caption_for_kpi","Caption For KPI"),!1))],1),a("v-col",{staticClass:"blueGrey--text font-weight-medium",attrs:{cols:"12"}},[a("span",[t._v("Select answer fields for all KPI questions :")])]),t._l(t.formValues.kaar_answer_types.filter((function(t){return"kpi"===t.question_type})),(function(e,n){return a("v-row",{key:"kpi-"+n,attrs:{align:"center",dense:""}},[a("v-col",{attrs:{cols:"2"}},[a("span",[t._v(t._s(t.scales[e.answer_type]))])]),a("v-col",{attrs:{cols:"7"}},[a("v-text-field",t._b({directives:[{name:"validate",rawName:"v-validate",value:"max:600",expression:"'max:600'"}],attrs:{counter:600,label:"Description",dense:""},model:{value:e.description,callback:function(a){t.$set(e,"description",a)},expression:"item.description"}},"v-text-field",t.veeValidate("kpi-description-"+n,"Description"),!1))],1),a("v-col",{attrs:{cols:"3"}},[a("v-switch",{staticClass:"pa-0 ma-0",attrs:{color:"teal lighten-2",ripple:!1,label:"Mandatory Field",dense:"","hide-details":""},model:{value:e.is_mandatory,callback:function(a){t.$set(e,"is_mandatory",a)},expression:"item.is_mandatory"}})],1)],1)}))]:t._e(),a("v-col",{attrs:{cols:"12"}},[a("v-switch",{staticClass:"pa-0 ma-0",attrs:{color:"teal lighten-2",ripple:!1,label:"Include question set for appraisee",dense:"","hide-details":""},model:{value:t.formValues.add_feedback,callback:function(e){t.$set(t.formValues,"add_feedback",e)},expression:"formValues.add_feedback"}})],1),t.formValues.add_feedback?[a("v-col",{attrs:{cols:"6"}},[a("vue-auto-complete",t._b({directives:[{name:"validate",rawName:"v-validate",value:"required",expression:"'required'"}],attrs:{endpoint:t.questionSetApi,"item-text":"name","prepend-inner-icon":"mdi-calendar-question","item-value":"id","force-fetch":""},model:{value:t.formValues.generic_question_set,callback:function(e){t.$set(t.formValues,"generic_question_set",e)},expression:"formValues.generic_question_set"}},"vue-auto-complete",t.veeValidate("question_set","Select Question Set for Appraisee *"),!1))],1)]:t._e()],2)],1),a("v-divider"),a("v-card-actions",[a("v-row",{attrs:{"no-gutters":""}},[a("v-col",{staticClass:"text-right"},[a("v-btn",{attrs:{small:"",text:""},on:{click:function(e){return t.$emit("close")}}},[t._v("Close")]),a("v-btn",{attrs:{color:"primary",small:"",disabled:t.loading},on:{click:t.submitData}},[t._v(" Save ")])],1)],1)],1)],1)},i=[],s=(a("a9e3"),a("b0c0"),a("159b"),a("a4d3"),a("e01a"),a("f12b")),r=a("1f4c"),o=a("931c"),c=a("5660"),l=a("1467"),u={components:{VueAutoComplete:c["default"],VueTrumbowyg:l["default"]},mixins:[s["a"]],props:{appraisalId:{type:[String,Number],required:!0},performanceAppraisalType:{type:String,required:!0}},data:function(){return{questionSetApi:"",scaleMap:{"rating-scale":"Rating Scale","long-text":"Long Text"},scales:{"rating-scale":"Rating Scale","long-text":"Key Achievement"},fetchedResults:[],formValues:{instruction_for_evaluator:"",add_feedback:!1,include_ksa:!1,include_kpi:!1,caption_for_ksa:"",caption_for_kpi:"",generic_question_set:null,kaar_answer_types:[{question_type:"ksa",answer_type:"rating-scale",description:"",is_mandatory:!1},{question_type:"ksa",answer_type:"long-text",description:"",is_mandatory:!1},{question_type:"kpi",answer_type:"rating-scale",description:"",is_mandatory:!1},{question_type:"kpi",answer_type:"long-text",description:"",is_mandatory:!1}]}}},created:function(){var t=this;this.questionSetApi=r["a"].getQuestionSet(this.getOrganizationSlug),this.crud.name="Key Form Settings",this.getData(o["a"].KaarFormSettings(this.getOrganizationSlug,this.appraisalId)).then((function(e){t.fetchedResults=e.results,t.getAppraisalData()}))},methods:{getAppraisalData:function(){this.clearNonFieldErrors(),this.$validator.errors.clear(),1==this.fetchedResults.length&&(this.formValues=this.fetchedResults[0])},submitData:function(){this.crud.message="Key Form Settings saved successfully.",this.insertData(o["a"].KaarFormSettings(this.getOrganizationSlug,this.appraisalId),this.formValues,{clearForm:!1})},getFormValues:function(){return this.formValues.include_ksa||(this.formValues.caption_for_ksa="",this.formValues.kaar_answer_types.forEach((function(t){"ksa"===t.question_type&&(t.description="",t.is_mandatory=!1)}))),this.formValues.include_kpi||(this.formValues.caption_for_kpi="",this.formValues.kaar_answer_types.forEach((function(t){"kpi"===t.question_type&&(t.description="",t.is_mandatory=!1)}))),this.formValues}}},p=u,d=(a("7068"),a("2877")),f=a("6544"),m=a.n(f),h=a("8336"),v=a("b0af"),g=a("99d9"),y=a("62ad"),_=a("ce7e"),b=a("0fd9b"),x=a("b73d"),k=a("8654"),w=Object(d["a"])(p,n,i,!1,null,null,null);e["default"]=w.exports;m()(w,{VBtn:h["a"],VCard:v["a"],VCardActions:g["a"],VCardText:g["c"],VCol:y["a"],VDivider:_["a"],VRow:b["a"],VSwitch:x["a"],VTextField:k["a"]})},"1f4c":function(t,e,a){"use strict";a("99af");e["a"]={getQuestionSet:function(t){return"/appraisal/".concat(t,"/question-set/")},createQuestionSet:function(t){return"/appraisal/".concat(t,"/question-set/")},getQuestionSetDetail:function(t,e){return"appraisal/".concat(t,"/question-set/").concat(e,"/")},updateQuestionSet:function(t,e){return"/appraisal/".concat(t,"/question-set/").concat(e,"/")},deleteQuestionSet:function(t,e){return"/appraisal/".concat(t,"/question-set/").concat(e,"/")},deleteQuestion:function(t,e,a){return"/appraisal/".concat(t,"/question-set/").concat(e,"/question/").concat(a,"/")},getQuestionSetUserType:function(t,e,a){return"/appraisal/".concat(t,"/question-set/").concat(e,"/question/").concat(a,"/user-type/")},copyQuestionSet:function(t,e){return"/appraisal/".concat(t,"/year/slot/").concat(e,"/question-set/copy/")},getQuestionsBySection:function(t,e,a){return"appraisal/".concat(t,"/question-set/").concat(e,"/section/").concat(a,"/question/")},postQuestionsInSection:function(t,e,a){return"appraisal/".concat(t,"/question-set/").concat(e,"/section/").concat(a,"/question/")},removeQuestionSet:function(t,e){return"/appraisal/".concat(t,"/question-set/").concat(e,"/")},updateQuestionSection:function(t,e,a){return"/appraisal/".concat(t,"/question-set/").concat(e,"/section/").concat(a,"/")},removeQuestionSection:function(t,e,a){return"/appraisal/".concat(t,"/question-set/").concat(e,"/section/").concat(a,"/")},removeQuestionFromSection:function(t,e,a,n){return"/appraisal/".concat(t,"/question-set/").concat(e,"/section/").concat(a,"/question/").concat(n,"/")},getQuestionsOnQuestionSet:function(t,e){return"/appraisal/".concat(t,"/question-set/").concat(e,"/questions/")},createQuestionSection:function(t,e){return"/appraisal/".concat(t,"/question-set/").concat(e,"/section/")}}},5660:function(t,e,a){"use strict";a.r(e);var n=function(){var t=this,e=t.$createElement,a=t._self._c||e;return a("div",{staticClass:"d-flex space-between"},[a("v-autocomplete",{key:t.componentKey,ref:"autoComplete",class:t.appliedClass,attrs:{id:t.id,items:t.itemsSorted,"search-input":t.search,loading:t.isLoading,multiple:t.multiple,label:t.label,error:t.errorMessages.length>0,"error-messages":t.errorMessages,disabled:t.disabled,readonly:t.readonly,"data-cy":"autocomplete-"+t.dataCyVariable,"prepend-inner-icon":t.prependInnerIcon,clearable:t.clearable&&!t.readonly,"hide-details":t.hideDetails,"item-text":t.itemText,"item-value":t.itemValue,"small-chips":t.multiple||t.chips,"deletable-chips":t.multiple,hint:t.hint,"persistent-hint":t.persistentHint,chips:t.chips,solo:t.solo,flat:t.flat,"cache-items":t.cacheItems,placeholder:t.placeholder,dense:t.dense,"hide-selected":"","hide-no-data":""},on:{"update:searchInput":function(e){t.search=e},"update:search-input":function(e){t.search=e},focus:t.populateOnFocus,keydown:function(e){return!e.type.indexOf("key")&&t._k(e.keyCode,"enter",13,e.key,"Enter")?null:(e.preventDefault(),t.searchText())},change:t.updateState,blur:function(e){return t.$emit("blur")}},scopedSlots:t._u([{key:"selection",fn:function(e){return[t._t("selection",(function(){return[t.itemText&&e.item?a("div",[t.multiple||t.chips?a("v-chip",{attrs:{close:(t.clearable||!t.clearable&&!t.multiple)&&!t.readonly,small:""},on:{"click:close":function(a){return t.remove(e.item)}}},[e.item[t.itemText]?a("div",[e.item[t.itemText].length>40?a("v-tooltip",{attrs:{top:""},scopedSlots:t._u([{key:"activator",fn:function(n){var i=n.on;return[a("span",t._g({},i),[t._v(" "+t._s(t._f("truncate")(e.item[t.itemText],40)))])]}}],null,!0)},[a("span",[t._v(t._s(e.item[t.itemText]))])]):a("span",[t._v(t._s(e.item[t.itemText]))])],1):a("div",[a("span",[t._v(t._s(e.item))])])]):a("div",[e.item[t.itemText]?a("div",[e.item[t.itemText].length>40?a("v-tooltip",{attrs:{top:""},scopedSlots:t._u([{key:"activator",fn:function(n){var i=n.on;return[a("span",t._g({},i),[t._v(" "+t._s(t._f("truncate")(e.item[t.itemText],40)))])]}}],null,!0)},[a("span",[t._v(t._s(e.item[t.itemText]))])]):a("span",[t._v(t._s(e.item[t.itemText]))])],1):a("div",[a("span",[t._v(t._s(e.item))])])])],1):t._e()]}),{props:e})]}},{key:"item",fn:function(e){return[a("v-list-item-content",[a("v-list-item-title",[t._t("item",(function(){return[t.itemText&&e.item?a("div",[e.item[t.itemText]?a("div",[e.item[t.itemText].length>40?a("v-tooltip",{attrs:{top:""},scopedSlots:t._u([{key:"activator",fn:function(n){var i=n.on;return[a("span",t._g({},i),[t._v(" "+t._s(t._f("truncate")(e.item[t.itemText],40)))])]}}],null,!0)},[a("span",[t._v(t._s(e.item[t.itemText]))])]):a("span",[t._v(t._s(e.item[t.itemText]))])],1):a("div",[a("span",[t._v(t._s(e.item))])])]):t._e()]}),{props:e})],2)],1)]}},{key:"append-item",fn:function(){return[!t.fullyLoaded&&t.showMoreIcon?a("div",[a("v-list-item-content",{staticClass:"px-4 pointer primary--text font-weight-bold"},[a("v-list-item-title",{on:{click:function(e){return t.fetchData()}}},[t._v(" Load More Items ... ")])],1)],1):t._e()]},proxy:!0}],null,!0),model:{value:t.selectedData,callback:function(e){t.selectedData=e},expression:"selectedData"}}),t._t("default")],2)},i=[],s=a("2909"),r=a("5530"),o=a("53ca"),c=a("1da1"),l=(a("96cf"),a("a9e3"),a("ac1f"),a("841c"),a("7db0"),a("d81d"),a("159b"),a("4de4"),a("4e827"),a("2ca0"),a("d3b7"),a("c740"),a("a434"),a("3ca3"),a("ddb0"),a("2b3d"),a("caad"),a("2532"),a("63ea")),u=a.n(l),p={props:{value:{type:[Number,String,Array,Object],default:void 0},id:{type:String,default:""},dataCyVariable:{type:String,default:""},endpoint:{type:String,default:""},itemText:{type:String,required:!0},itemValue:{type:String,required:!0},params:{type:Object,required:!1,default:function(){return{}}},itemsToExclude:{type:[Array,Number],default:null},forceFetch:{type:Boolean,default:!1},staticItems:{type:Array,default:function(){return[]}},errorMessages:{type:[String,Array],default:function(){return[]}},label:{type:String,default:""},disabled:{type:Boolean,default:!1},readonly:{type:Boolean,default:!1},hint:{type:String,default:void 0},persistentHint:{type:Boolean,required:!1,default:!1},multiple:{type:Boolean,required:!1,default:!1},clearable:{type:Boolean,default:!0},hideDetails:{type:Boolean,default:!1},solo:{type:Boolean,default:!1},flat:{type:Boolean,default:!1},chips:{type:Boolean,default:!1},prependInnerIcon:{type:String,default:void 0},cacheItems:{type:Boolean,default:!1},appliedClass:{type:String,default:""},placeholder:{type:String,default:""},dense:{type:Boolean,default:!1}},data:function(){return{componentKey:0,items:[],selectedData:null,search:null,initialFetchStarted:!1,nextLimit:null,nextOffset:null,showMoreIcon:!1,fullyLoaded:!1,isLoading:!1}},computed:{itemsSorted:function(){return this.sortBySearch(this.items,this.search?this.search.toLowerCase():"")}},watch:{value:{handler:function(){var t=Object(c["a"])(regeneratorRuntime.mark((function t(e){var a,n,i,s,r=this;return regeneratorRuntime.wrap((function(t){while(1)switch(t.prev=t.next){case 0:if(!e){t.next=10;break}if(!this.forceFetch||this.initialFetchStarted){t.next=6;break}return this.initialFetchStarted=!0,t.next=5,this.fetchData();case 5:this.removeDuplicateItem();case 6:Array.isArray(e)?(i=[],"object"===Object(o["a"])(e[0])?(this.selectedData=e.map((function(t){return t[r.itemValue]})),e.forEach((function(t){var e=r.items.find((function(e){return e===t}));e||i.push(t)}))):(e.forEach((function(t){var e=r.items.find((function(e){return e[r.itemValue]===t}));e||i.push(t)})),this.selectedData=e),i.length>0&&(s=this.items).push.apply(s,i)):"object"===Object(o["a"])(e)?(this.selectedData=e[this.itemValue],a=this.items.find((function(t){return t[r.itemValue]===e})),a||this.items.push(e)):(this.selectedData=e,n=this.items.find((function(t){return t===e})),n||this.items.push(e)),this.updateData(this.selectedData),t.next=11;break;case 10:e||(this.selectedData=null);case 11:case"end":return t.stop()}}),t,this)})));function e(e){return t.apply(this,arguments)}return e}(),immediate:!0},selectedData:function(t){this.updateData(t)},params:{handler:function(t,e){u()(t,e)||(this.fullyLoaded=!1,this.initialFetchStarted=!1,this.items=[],this.componentKey+=1)},deep:!0}},methods:{sortBySearch:function(t,e){var a=this.itemText,n=t.filter((function(t){return"object"===Object(o["a"])(t)}));return n.sort((function(t,n){return t[a].toLowerCase().startsWith(e)&&n[a].toLowerCase().startsWith(e)?t[a].toLowerCase().localeCompare(n[a].toLowerCase()):t[a].toLowerCase().startsWith(e)?-1:n[a].toLowerCase().startsWith(e)?1:t[a].toLowerCase().localeCompare(n[a].toLowerCase())}))},populateOnFocus:function(){var t=this;return Object(c["a"])(regeneratorRuntime.mark((function e(){return regeneratorRuntime.wrap((function(e){while(1)switch(e.prev=e.next){case 0:if(!t.initialFetchStarted){e.next=2;break}return e.abrupt("return");case 2:return t.initialFetchStarted=!0,e.next=5,t.fetchData();case 5:t.removeDuplicateItem();case 6:case"end":return e.stop()}}),e)})))()},fetchData:function(){var t=this;return Object(c["a"])(regeneratorRuntime.mark((function e(){var a,n;return regeneratorRuntime.wrap((function(e){while(1)switch(e.prev=e.next){case 0:if(!(t.staticItems.length>0)){e.next=3;break}return t.items=t.staticItems,e.abrupt("return");case 3:return a=t.nextLimit,n=t.nextOffset,t.search&&(a=null,n=null),t.isLoading=!0,e.next=9,t.$http.get(t.endpoint,{params:Object(r["a"])(Object(r["a"])({},t.params),{},{search:t.search,limit:a,offset:n})}).then((function(e){var a;e.results||(e.results=e),e.next?(t.showMoreIcon=!0,t.extractLimitOffset(e.next)):(t.showMoreIcon=!1,t.search||(t.fullyLoaded=!0)),t.itemsToExclude&&(e.results=t.excludeRecord(e.results)),(a=t.items).push.apply(a,Object(s["a"])(e.results))})).finally((function(){t.isLoading=!1}));case 9:case"end":return e.stop()}}),e)})))()},removeDuplicateItem:function(){var t=this,e=this.items.indexOf(this.selectedData);if(e>=0){var a=this.items.findIndex((function(e){return e[t.itemValue]===t.selectedData}));a>=0&&(this.items.splice(e,1),this.componentKey+=1)}},updateData:function(t){var e=this,a=[];t instanceof Array?t.forEach((function(t){a.unshift(e.items.find((function(a){return a[e.itemValue]===t})))})):a=this.items.find((function(a){return a[e.itemValue]===t})),this.$emit("input",t),this.$emit("update:selectedFullData",a)},searchText:function(){0!==this.$refs.autoComplete.filteredItems.length||this.fullyLoaded||this.fetchData()},extractLimitOffset:function(t){var e=new URL(t);this.nextLimit=e.searchParams.get("limit"),this.nextOffset=e.searchParams.get("offset")},excludeRecord:function(t){var e=this,a=[];return"number"===typeof this.itemsToExclude?a.push(this.itemsToExclude):a=this.itemsToExclude,t.filter((function(t){if(t[e.itemValue])return!a.includes(t[e.itemValue])}))},remove:function(t){if(this.selectedData instanceof Object){var e=this.selectedData.indexOf(t[this.itemValue]);e>=0&&this.selectedData.splice(e,1)}else this.selectedData=null},updateState:function(){this.search="",this.nextLimit&&(this.showMoreIcon=!0)}}},d=p,f=a("2877"),m=a("6544"),h=a.n(m),v=a("c6a6"),g=a("cc20"),y=a("5d23"),_=a("3a2f"),b=Object(f["a"])(d,n,i,!1,null,null,null);e["default"]=b.exports;h()(b,{VAutocomplete:v["a"],VChip:g["a"],VListItemContent:y["a"],VListItemTitle:y["c"],VTooltip:_["a"]})},"6c6f":function(t,e,a){"use strict";a("d3b7");e["a"]={data:function(){return{deleteNotification:{dialog:!1,heading:"Confirm Delete",text:"Are you sure you want to delete ?"}}},methods:{deleteData:function(t,e){var a=this;return new Promise((function(n,i){!a.loading&&t&&(a.loading=!0,a.$http.delete(t,e||{}).then((function(t){a.crud.message&&setTimeout((function(){a.notifyUser(a.crud.message)}),1e3),n(t),a.loading=!1})).catch((function(t){a.pushErrors(t),a.notifyInvalidFormResponse(),i(t),a.loading=!1})).finally((function(){a.deleteNotification.dialog=!1})))}))}}}},7068:function(t,e,a){"use strict";a("fe86")},"931c":function(t,e,a){"use strict";a("99af");e["a"]={getFormSettings:function(t,e){return"/appraisal/".concat(t,"/year/slot/").concat(e,"/form-design/")},postFormSettings:function(t,e){return"/appraisal/".concat(t,"/year/slot/").concat(e,"/form-design/")},generateAppraiseeForms:function(t,e){return"/appraisal/".concat(t,"/year/slot/").concat(e,"/form-design/generate/question-set/")},getAppraiseeForms:function(t,e){return"appraisal/".concat(t,"/year/slot/").concat(e,"/question-set/count/")},getAppraiseeFormsById:function(t,e,a){return"appraisal/".concat(t,"/year/slot/").concat(e,"/appraisee/").concat(a,"/appraiser/")},getAppraiserFormsById:function(t,e,a){return"appraisal/".concat(t,"/year/slot/").concat(e,"/appraiser/").concat(a,"/appraisee/")},postAppraisedForm:function(t,e,a,n){return"appraisal/".concat(t,"/year/slot/").concat(e,"/appraiser/").concat(a,"/appraisee/").concat(n,"/answer/")},approveAppraisedForm:function(t,e,a,n){return"appraisal/".concat(t,"/year/slot/").concat(e,"/appraisee/").concat(a,"/appraiser/").concat(n,"/approve/")},resendAppraisedForm:function(t,e,a,n){return"appraisal/".concat(t,"/year/slot/").concat(e,"/appraisee/").concat(a,"/appraiser/").concat(n,"/resend/")},getAppraiseeFormDetailForAppraiser:function(t,e,a,n){return"appraisal/".concat(t,"/year/slot/").concat(e,"/appraisee/").concat(a,"/appraiser/").concat(n,"/question-set/")},getFormSubmissionStatus:function(t,e){return"/appraisal/".concat(t,"/year/slot/").concat(e,"/question-set/statistics/")},getFormSubmissionList:function(t,e,a){return"/appraisal/".concat(t,"/year/slot/").concat(e,"/appraisee/").concat(a,"/appraiser/")},getFormApprovalStatus:function(t,e){return"/appraisal/".concat(t,"/year/slot/").concat(e,"/question-set/approval/")},updateAppraisalFormDates:function(t,e){return"/appraisal/".concat(t,"/year/slot/").concat(e,"/mode/update/date-parameters/")},sendAppraisalForms:function(t,e){return"appraisal/".concat(t,"/year/slot/").concat(e,"/form-design/send/question-set/")},getKaarFormSubmissionList:function(t,e){return"appraisal/".concat(t,"/year/slot/").concat(e,"/kaar-appraiser")},KaarFormSettings:function(t,e){return"/appraisal/".concat(t,"/year/slot/").concat(e,"/kaar-form-design/")},generateKaarAppraiseeForms:function(t,e){return"/appraisal/".concat(t,"/year/slot/").concat(e,"/kaar-form-design/generate/question-set/")},getKaarAppraiseeFormsCount:function(t,e){return"appraisal/".concat(t,"/year/slot/").concat(e,"/kaar-question-set/count/")},getKaarAppraiserConfig:function(t,e,a){return"appraisal/".concat(t,"/year/slot/").concat(e,"/kaar-appraiser/").concat(a,"/")},getKaarFormSubmissionStatus:function(t,e){return"/appraisal/".concat(t,"/year/slot/").concat(e,"/kaar-question-set/statistics/")},sendKaarAppraisalForms:function(t,e){return"appraisal/".concat(t,"/year/slot/").concat(e,"/kaar-form-design/send/question-set/")},postKaarAppraisedForm:function(t,e,a){return"appraisal/".concat(t,"/year/slot/").concat(e,"/kaar-appraiser/").concat(a,"/submit-answer/")},assignKaarScoreSetting:function(t,e){return"appraisal/".concat(t,"/year/slot/").concat(e,"/setting/kaar-scaling-setting/")},updateKaarScoreSetting:function(t,e,a){return"appraisal/".concat(t,"/year/slot/").concat(e,"/setting/kaar-scaling-setting/").concat(a)},supervisorEvaluation:function(t,e){return"appraisal/".concat(t,"/year/slot/").concat(e,"/supervisor-evaluation")},reviewerEvaluation:function(t,e){return"appraisal/".concat(t,"/year/slot/").concat(e,"/reviewer-evaluation")},updateReviewerEvaluation:function(t,e,a){return"appraisal/".concat(t,"/year/slot/").concat(e,"/reviewer-evaluation/").concat(a)},exportPaStatusReport:function(t,e){return"appraisal/".concat(t,"/year/slot/").concat(e,"/kaar-question-set/statistics/export")}}},"983c":function(t,e,a){"use strict";a("d3b7");e["a"]={methods:{getData:function(t,e,a){var n=this,i=arguments.length>3&&void 0!==arguments[3]&&arguments[3];return new Promise((function(s,r){!n.loading&&t&&(n.clearNonFieldErrors(),n.$validator.errors.clear(),n.loading=i,n.$http.get(t,a||{params:e||{}}).then((function(t){s(t),n.loading=!1})).catch((function(t){n.pushErrors(t),n.notifyInvalidFormResponse(),r(t),n.loading=!1})))}))},getBlockingData:function(t,e,a){var n=this;return new Promise((function(i,s){n.getData(t,e,a,!0).then((function(t){i(t)})).catch((function(t){s(t)}))}))}}}},"9d01":function(t,e,a){},b73d:function(t,e,a){"use strict";var n=a("5530"),i=(a("0481"),a("ec29"),a("9d01"),a("fe09")),s=a("c37a"),r=a("c3f0"),o=a("0789"),c=a("490a"),l=a("80d2");e["a"]=i["a"].extend({name:"v-switch",directives:{Touch:r["a"]},props:{inset:Boolean,loading:{type:[Boolean,String],default:!1},flat:{type:Boolean,default:!1}},computed:{classes:function(){return Object(n["a"])(Object(n["a"])({},s["a"].options.computed.classes.call(this)),{},{"v-input--selection-controls v-input--switch":!0,"v-input--switch--flat":this.flat,"v-input--switch--inset":this.inset})},attrs:function(){return{"aria-checked":String(this.isActive),"aria-disabled":String(this.isDisabled),role:"switch"}},validationState:function(){return this.hasError&&this.shouldValidate?"error":this.hasSuccess?"success":null!==this.hasColor?this.computedColor:void 0},switchData:function(){return this.setTextColor(this.loading?void 0:this.validationState,{class:this.themeClasses})}},methods:{genDefaultSlot:function(){return[this.genSwitch(),this.genLabel()]},genSwitch:function(){return this.$createElement("div",{staticClass:"v-input--selection-controls__input"},[this.genInput("checkbox",Object(n["a"])(Object(n["a"])({},this.attrs),this.attrs$)),this.genRipple(this.setTextColor(this.validationState,{directives:[{name:"touch",value:{left:this.onSwipeLeft,right:this.onSwipeRight}}]})),this.$createElement("div",Object(n["a"])({staticClass:"v-input--switch__track"},this.switchData)),this.$createElement("div",Object(n["a"])({staticClass:"v-input--switch__thumb"},this.switchData),[this.genProgress()])])},genProgress:function(){return this.$createElement(o["c"],{},[!1===this.loading?null:this.$slots.progress||this.$createElement(c["a"],{props:{color:!0===this.loading||""===this.loading?this.color||"primary":this.loading,size:16,width:2,indeterminate:!0}})])},onSwipeLeft:function(){this.isActive&&this.onChange()},onSwipeRight:function(){this.isActive||this.onChange()},onKeydown:function(t){(t.keyCode===l["y"].left&&this.isActive||t.keyCode===l["y"].right&&!this.isActive)&&this.onChange()}}})},f12b:function(t,e,a){"use strict";var n=a("f0d5"),i=a("983c"),s=a("f70a"),r=a("6c6f");e["a"]={mixins:[n["a"],i["a"],s["a"],r["a"]]}},f70a:function(t,e,a){"use strict";a("d3b7"),a("caad");e["a"]={methods:{insertData:function(t,e){var a=this,n=arguments.length>2&&void 0!==arguments[2]?arguments[2]:{},i=n.validate,s=void 0===i||i,r=n.clearForm,o=void 0===r||r,c=arguments.length>3?arguments[3]:void 0;return new Promise((function(n,i){!a.loading&&t&&(a.clearErrors(),a.$validator.validateAll().then((function(r){s||(r=!0),r&&(a.loading=!0,a.$http.post(t,e,c||{}).then((function(t){a.clearErrors(),o&&(a.formValues={}),a.crud.addAnother||a.$emit("create"),a.crud.message&&setTimeout((function(){a.notifyUser(a.crud.message)}),1e3),n(t),a.loading=!1})).catch((function(t){a.pushErrors(t),a.notifyInvalidFormResponse(),i(t),a.loading=!1})))})))}))},patchData:function(t,e){var a=this,n=arguments.length>2&&void 0!==arguments[2]?arguments[2]:{},i=n.validate,s=void 0===i||i,r=n.clearForm,o=void 0===r||r,c=arguments.length>3?arguments[3]:void 0;return new Promise((function(n,i){a.updateData(t,e,{validate:s,clearForm:o},"patch",c).then((function(t){n(t)})).catch((function(t){i(t)}))}))},putData:function(t,e){var a=this,n=arguments.length>2&&void 0!==arguments[2]?arguments[2]:{},i=n.validate,s=void 0===i||i,r=n.clearForm,o=void 0===r||r,c=arguments.length>3?arguments[3]:void 0;return new Promise((function(n,i){a.updateData(t,e,{validate:s,clearForm:o},"put",c).then((function(t){n(t)})).catch((function(t){i(t)}))}))},updateData:function(t,e){var a=this,n=arguments.length>2&&void 0!==arguments[2]?arguments[2]:{},i=n.validate,s=void 0===i||i,r=n.clearForm,o=void 0===r||r,c=arguments.length>3?arguments[3]:void 0,l=arguments.length>4?arguments[4]:void 0;return new Promise((function(n,i){!a.loading&&t&&["put","patch"].includes(c)&&(a.clearErrors(),a.$validator.validateAll().then((function(r){s||(r=!0),r&&(a.loading=!0,a.$http[c](t,e,l||{}).then((function(t){a.$emit("update"),a.clearErrors(),o&&(a.formValues={}),a.crud.message&&setTimeout((function(){a.notifyUser(a.crud.message)}),1e3),n(t),a.loading=!1})).catch((function(t){a.pushErrors(t),a.notifyInvalidFormResponse(),i(t),a.loading=!1})))})))}))},clearErrors:function(){this.clearNonFieldErrors(),this.$validator.errors.clear()}}}},fe86:function(t,e,a){}}]);