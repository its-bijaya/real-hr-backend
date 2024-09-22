(window["webpackJsonp"]=window["webpackJsonp"]||[]).push([["chunk-5a1f7100","chunk-2d2160c2","chunk-2d2160c2","chunk-2d2160c2","chunk-2d2160c2","chunk-2d2160c2"],{"2c64":function(e,t,i){},"371f":function(e,t,i){"use strict";i.r(t);var s=function(){var e=this,t=e.$createElement,i=e._self._c||t;return i("v-form",{on:{submit:function(t){return t.preventDefault(),e.assignCoreTask.apply(null,arguments)}}},[i("v-container",[i("v-row",[i("v-col",{attrs:{md:"12"}},[i("h5",[e._v("Assign To")]),i("vue-user",{attrs:{user:e.selectedUserData}})],1),e.selectedUserData.division&&e.selectedUserData.experiences.length>0?i("v-col",{attrs:{md:"12"}},[e.fetched&&!e.loading?i("div",[i("v-row",[i("v-col",{attrs:{md:"8"}},[e.fetched&&e.fetchedData.length>0?i("div",[i("h5",[e._v(" Result Area and Core Tasks associated with "+e._s(e.divisionName||e.selectedUserData.division.name)+" ")]),i("v-divider"),e._l(e.fetchedData,(function(t,s){return i("div",{key:s},[t.core_tasks.length>0?i("div",[i("v-switch",{attrs:{label:t.title+(e.kra.includes(t.id)?" : Key Result Area":" : Result Area"),value:t.id},model:{value:e.kra,callback:function(t){e.kra=t},expression:"kra"}})],1):i("div",[e._v(" There are no added core tasks under result area "),i("strong",[e._v(e._s(t.title))]),e._v(". Please add core tasks to continue. ")]),e._l(t.core_tasks,(function(t,s){return i("v-row",{key:s},[i("div",{staticClass:"pl-12"},[i("v-checkbox",{attrs:{value:t.id,loading:!0,height:t.title.length>109?30:5},model:{value:e.selectedCoreTasks,callback:function(t){e.selectedCoreTasks=t},expression:"selectedCoreTasks"}},[i("template",{slot:"label"},[e._v(" "+e._s(t.order)+". "+e._s(t.title)+" ")])],2)],1)])}))],2)}))],2):i("div",[i("v-divider",{staticClass:"mt-5"}),i("no-data",{attrs:{text:(e.divisionName||e.selectedUserData.division.name)+" has no result areas associated. Please add to continue further. ",height:300}})],1)]),i("v-col",{attrs:{md:"4"}},[i("h5",[e._v("Select Employee Experience")]),i("v-divider"),i("v-radio-group",{model:{value:e.selectedUserExperienceID,callback:function(t){e.selectedUserExperienceID=t},expression:"selectedUserExperienceID"}},e._l(e.selectedUserData.experiences,(function(t,s){return i("v-radio",{key:s,attrs:{value:t.id}},[i("template",{slot:"label"},[e._v(" "+e._s(e.get(t,"job_title.title"))+" "),t.is_current?i("span",[e._v(" (Current)")]):e._e(),t.upcoming?i("span",[e._v(" (Upcoming)")]):e._e()])],2)})),1)],1)],1)],1):e._e(),e.loading?i("default-svg-loader"):e._e()],1):0===e.selectedUserData.experiences.length?i("v-col",{attrs:{md:"12"}},[i("v-divider"),i("no-data",{attrs:{text:e.selectedUserData.full_name+" has no user experiences .",height:300}})],1):i("v-col",{attrs:{md:"12"}},[i("v-divider"),i("no-data",{attrs:{text:e.selectedUserData.full_name+" is not assigned to any division. Please assign division to continue.",height:300}})],1)],1)],1),i("v-footer",{attrs:{height:"auto",fixed:""}},[i("v-spacer"),i("v-btn",{staticClass:"mx-2 my-1",attrs:{disabled:e.disableSave,depressed:"",color:"primary",type:"submit"},domProps:{textContent:e._s("Save")}})],1)],1)},a=[],n=i("1da1"),r=(i("96cf"),i("a9e3"),i("159b"),i("caad"),i("2532"),i("d81d"),i("4de4"),i("99af"),i("7db0"),i("b0c0"),i("f12b")),o=i("e585"),c=i("02cb"),l=i("c197"),u={components:{NoData:o["default"],VueUser:c["default"],DefaultSvgLoader:l["default"]},mixins:[r["a"]],props:{selectedUserData:{type:Object,required:!0},changeType:{type:Boolean,default:!1},changeId:{type:Number,default:null}},data:function(){return{orgSlug:this.$route.params.slug,kra:[],fetchedData:null,fetched:!1,selectedCoreTasks:[],loading:!1,divisionName:"",formValues:[],selectedUserExperienceID:null,disableSave:!1}},computed:{constructFormValues:function(){var e=this;return this.fetched&&(this.formValues.forEach((function(t){t.user_experience=e.selectedUserExperienceID,t.core_tasks=[],t.key_result_area=e.kra.includes(t.result_area)})),this.selectedCoreTasks.forEach((function(t){var i=e.fetchedData.map((function(e){return e.core_tasks.filter((function(e){return e.id===t}))})),s=[].concat.apply([],i);if(s.length){var a=e.formValues.find((function(e){return e.result_area===s[0].result_area}));a.result_area===s[0].result_area&&a.core_tasks.unshift(t)}}))),this.formValues}},watch:{selectedUserExperienceID:function(e){if(this.selectedUserData.experiences.find((function(t){return t.id===e})).division){this.divisionName=this.selectedUserData.experiences.find((function(t){return t.id===e})).division.name;var t=this.selectedUserData.experiences.find((function(t){return t.id===e})).division.slug;this.fetchDivisionResultAreas(t)}var i=this.selectedUserData.experiences.find((function(t){return t.id===e}));this.populateSelectedDataAndKRA(i.result_areas)}},mounted:function(){if(this.selectedUserData.experiences&&this.selectedUserData.division&&this.selectedUserData.experiences.length>0){var e=this.selectedUserData.division.slug;this.fetchDivisionResultAreas(e);var t=this.currentUserExperienceResultAreas(this.selectedUserData.experiences);this.populateSelectedDataAndKRA(t)}},methods:{fetchDivisionResultAreas:function(e){var t=this;return Object(n["a"])(regeneratorRuntime.mark((function i(){var s,a;return regeneratorRuntime.wrap((function(i){while(1)switch(i.prev=i.next){case 0:return t.fetchedData=[],s="/hris/".concat(t.$route.params.slug,"/result-area/"),a={division:e,limit:100},i.next=5,t.getData(s,a).then((function(e){t.fetchedData=e.results,t.fetchedData.forEach((function(e){t.formValues.unshift({user_experience:null,result_area:e.id,core_tasks:[],key_result_area:!1})})),t.fetched=!0}));case 5:case"end":return i.stop()}}),i)})))()},assignCoreTask:function(){var e=this;return Object(n["a"])(regeneratorRuntime.mark((function t(){var i,s;return regeneratorRuntime.wrap((function(t){while(1)switch(t.prev=t.next){case 0:return t.next=2,e.validateAllFields();case 2:if(!t.sent){t.next=4;break}e.changeType?(i="/hris/".concat(e.getOrganizationSlug,"/employment/employment-review/").concat(e.changeId,"/assign-core-task/"),e.insertData(i,e.constructFormValues).then((function(){e.$emit("formResponse")}))):(s="/hris/assign/user-result-areas/?organization_slug=".concat(e.getOrganizationSlug),e.insertData(s,e.constructFormValues).then((function(){e.$emit("formResponse")})));case 4:case"end":return t.stop()}}),t)})))()},currentUserExperienceResultAreas:function(e){var t=e.find((function(e){return e.is_current}));if(t)return this.setCurrentUserExperience(t.id),t.result_areas;var i=e[0].result_areas;return this.setCurrentUserExperience(i.id),e},populateSelectedDataAndKRA:function(e){var t=e.map((function(e){return e.core_tasks.map((function(e){return e.id}))}));this.selectedCoreTasks=[].concat.apply([],t),this.kra=e.filter((function(e){return e.key_result_area})).map((function(e){return e.result_area.id}))},setCurrentUserExperience:function(e){this.selectedUserExperienceID=e},disableFormSave:function(){this.disableSave=!0}}},d=u,h=i("2877"),p=i("6544"),f=i.n(p),v=i("8336"),m=i("ac7c"),g=i("62ad"),b=i("a523"),_=i("ce7e"),x=i("553a"),k=i("4bd4"),y=i("67b6"),D=i("43a6"),S=i("0fd9b"),C=i("2fa4"),w=i("b73d"),O=Object(h["a"])(d,s,a,!1,null,null,null);t["default"]=O.exports;f()(O,{VBtn:v["a"],VCheckbox:m["a"],VCol:g["a"],VContainer:b["a"],VDivider:_["a"],VFooter:x["a"],VForm:k["a"],VRadio:y["a"],VRadioGroup:D["a"],VRow:S["a"],VSpacer:C["a"],VSwitch:w["a"]})},"3d86":function(e,t,i){},"43a6":function(e,t,i){"use strict";var s=i("5530"),a=(i("a9e3"),i("ec29"),i("3d86"),i("c37a")),n=i("604c"),r=i("8547"),o=i("58df"),c=Object(o["a"])(r["a"],n["a"],a["a"]);t["a"]=c.extend({name:"v-radio-group",provide:function(){return{radioGroup:this}},props:{column:{type:Boolean,default:!0},height:{type:[Number,String],default:"auto"},name:String,row:Boolean,value:null},computed:{classes:function(){return Object(s["a"])(Object(s["a"])({},a["a"].options.computed.classes.call(this)),{},{"v-input--selection-controls v-input--radio-group":!0,"v-input--radio-group--column":this.column&&!this.row,"v-input--radio-group--row":this.row})}},methods:{genDefaultSlot:function(){return this.$createElement("div",{staticClass:"v-input--radio-group__input",attrs:{id:this.id,role:"radiogroup","aria-labelledby":this.computedId}},a["a"].options.methods.genDefaultSlot.call(this))},genInputSlot:function(){var e=a["a"].options.methods.genInputSlot.call(this);return delete e.data.on.click,e},genLabel:function(){var e=a["a"].options.methods.genLabel.call(this);return e?(e.data.attrs.id=this.computedId,delete e.data.attrs.for,e.tag="legend",e):null},onClick:n["a"].options.methods.onClick}})},"553a":function(e,t,i){"use strict";var s=i("5530"),a=(i("a9e3"),i("c7cd"),i("b5b6"),i("8dd9")),n=i("3a66"),r=i("d10f"),o=i("58df"),c=i("80d2");t["a"]=Object(o["a"])(a["a"],Object(n["a"])("footer",["height","inset"]),r["a"]).extend({name:"v-footer",props:{height:{default:"auto",type:[Number,String]},inset:Boolean,padless:Boolean,tag:{type:String,default:"footer"}},computed:{applicationProperty:function(){return this.inset?"insetFooter":"footer"},classes:function(){return Object(s["a"])(Object(s["a"])({},a["a"].options.computed.classes.call(this)),{},{"v-footer--absolute":this.absolute,"v-footer--fixed":!this.absolute&&(this.app||this.fixed),"v-footer--padless":this.padless,"v-footer--inset":this.inset})},computedBottom:function(){if(this.isPositioned)return this.app?this.$vuetify.application.bottom:0},computedLeft:function(){if(this.isPositioned)return this.app&&this.inset?this.$vuetify.application.left:0},computedRight:function(){if(this.isPositioned)return this.app&&this.inset?this.$vuetify.application.right:0},isPositioned:function(){return Boolean(this.absolute||this.fixed||this.app)},styles:function(){var e=parseInt(this.height);return Object(s["a"])(Object(s["a"])({},a["a"].options.computed.styles.call(this)),{},{height:isNaN(e)?e:Object(c["g"])(e),left:Object(c["g"])(this.computedLeft),right:Object(c["g"])(this.computedRight),bottom:Object(c["g"])(this.computedBottom)})}},methods:{updateApplication:function(){var e=parseInt(this.height);return isNaN(e)?this.$el?this.$el.clientHeight:0:e}},render:function(e){var t=this.setBackgroundColor(this.color,{staticClass:"v-footer",class:this.classes,style:this.styles});return e(this.tag,t,this.$slots.default)}})},"67b6":function(e,t,i){"use strict";var s=i("5530"),a=(i("b0c0"),i("2c64"),i("ba87")),n=i("9d26"),r=i("c37a"),o=i("7e2b"),c=i("a9ad"),l=i("4e82"),u=i("5311"),d=i("7560"),h=i("fe09"),p=i("80d2"),f=i("58df"),v=i("d9f7"),m=Object(f["a"])(o["a"],c["a"],u["a"],Object(l["a"])("radioGroup"),d["a"]);t["a"]=m.extend().extend({name:"v-radio",inheritAttrs:!1,props:{disabled:Boolean,id:String,label:String,name:String,offIcon:{type:String,default:"$radioOff"},onIcon:{type:String,default:"$radioOn"},readonly:Boolean,value:{default:null}},data:function(){return{isFocused:!1}},computed:{classes:function(){return Object(s["a"])(Object(s["a"])({"v-radio--is-disabled":this.isDisabled,"v-radio--is-focused":this.isFocused},this.themeClasses),this.groupClasses)},computedColor:function(){return h["a"].options.computed.computedColor.call(this)},computedIcon:function(){return this.isActive?this.onIcon:this.offIcon},computedId:function(){return r["a"].options.computed.computedId.call(this)},hasLabel:r["a"].options.computed.hasLabel,hasState:function(){return(this.radioGroup||{}).hasState},isDisabled:function(){return this.disabled||!!this.radioGroup&&this.radioGroup.isDisabled},isReadonly:function(){return this.readonly||!!this.radioGroup&&this.radioGroup.isReadonly},computedName:function(){return this.name||!this.radioGroup?this.name:this.radioGroup.name||"radio-".concat(this.radioGroup._uid)},rippleState:function(){return h["a"].options.computed.rippleState.call(this)},validationState:function(){return(this.radioGroup||{}).validationState||this.computedColor}},methods:{genInput:function(e){return h["a"].options.methods.genInput.call(this,"radio",e)},genLabel:function(){return this.hasLabel?this.$createElement(a["a"],{on:{click:h["b"]},attrs:{for:this.computedId},props:{color:this.validationState,focused:this.hasState}},Object(p["s"])(this,"label")||this.label):null},genRadio:function(){return this.$createElement("div",{staticClass:"v-input--selection-controls__input"},[this.$createElement(n["a"],this.setTextColor(this.validationState,{props:{dense:this.radioGroup&&this.radioGroup.dense}}),this.computedIcon),this.genInput(Object(s["a"])({name:this.computedName,value:this.value},this.attrs$)),this.genRipple(this.setTextColor(this.rippleState))])},onFocus:function(e){this.isFocused=!0,this.$emit("focus",e)},onBlur:function(e){this.isFocused=!1,this.$emit("blur",e)},onChange:function(){this.isDisabled||this.isReadonly||this.isActive||this.toggle()},onKeydown:function(){}},render:function(e){var t={staticClass:"v-radio",class:this.classes,on:Object(v["c"])({click:this.onChange},this.listeners$)};return e("div",t,[this.genRadio(),this.genLabel()])}})},"9d01":function(e,t,i){},b5b6:function(e,t,i){},b73d:function(e,t,i){"use strict";var s=i("5530"),a=(i("0481"),i("ec29"),i("9d01"),i("fe09")),n=i("c37a"),r=i("c3f0"),o=i("0789"),c=i("490a"),l=i("80d2");t["a"]=a["a"].extend({name:"v-switch",directives:{Touch:r["a"]},props:{inset:Boolean,loading:{type:[Boolean,String],default:!1},flat:{type:Boolean,default:!1}},computed:{classes:function(){return Object(s["a"])(Object(s["a"])({},n["a"].options.computed.classes.call(this)),{},{"v-input--selection-controls v-input--switch":!0,"v-input--switch--flat":this.flat,"v-input--switch--inset":this.inset})},attrs:function(){return{"aria-checked":String(this.isActive),"aria-disabled":String(this.isDisabled),role:"switch"}},validationState:function(){return this.hasError&&this.shouldValidate?"error":this.hasSuccess?"success":null!==this.hasColor?this.computedColor:void 0},switchData:function(){return this.setTextColor(this.loading?void 0:this.validationState,{class:this.themeClasses})}},methods:{genDefaultSlot:function(){return[this.genSwitch(),this.genLabel()]},genSwitch:function(){return this.$createElement("div",{staticClass:"v-input--selection-controls__input"},[this.genInput("checkbox",Object(s["a"])(Object(s["a"])({},this.attrs),this.attrs$)),this.genRipple(this.setTextColor(this.validationState,{directives:[{name:"touch",value:{left:this.onSwipeLeft,right:this.onSwipeRight}}]})),this.$createElement("div",Object(s["a"])({staticClass:"v-input--switch__track"},this.switchData)),this.$createElement("div",Object(s["a"])({staticClass:"v-input--switch__thumb"},this.switchData),[this.genProgress()])])},genProgress:function(){return this.$createElement(o["c"],{},[!1===this.loading?null:this.$slots.progress||this.$createElement(c["a"],{props:{color:!0===this.loading||""===this.loading?this.color||"primary":this.loading,size:16,width:2,indeterminate:!0}})])},onSwipeLeft:function(){this.isActive&&this.onChange()},onSwipeRight:function(){this.isActive||this.onChange()},onKeydown:function(e){(e.keyCode===l["y"].left&&this.isActive||e.keyCode===l["y"].right&&!this.isActive)&&this.onChange()}}})},c197:function(e,t,i){"use strict";i.r(t);var s=function(){var e=this,t=e.$createElement,i=e._self._c||t;return i("div",{class:e.divClass},[i("v-img",{class:e.imgClass,attrs:{src:"/svg/three-dots.svg",height:e.height,contain:""}}),i("h3",{staticClass:"text-center grey--text",domProps:{textContent:e._s(e.message)}})],1)},a=[],n={props:{message:{type:String,default:"Please wait. Fetching data just for you ..."},divClass:{type:String,default:"pa-12"},imgClass:{type:String,default:"my-6"},height:{type:String,default:"20"}},data:function(){return{}}},r=n,o=i("2877"),c=i("6544"),l=i.n(c),u=i("adda"),d=Object(o["a"])(r,s,a,!1,null,null,null);t["default"]=d.exports;l()(d,{VImg:u["a"]})}}]);