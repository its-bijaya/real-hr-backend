(window["webpackJsonp"]=window["webpackJsonp"]||[]).push([["chunk-3c35437d"],{1229:function(e,t,a){"use strict";a("99af");t["a"]={getDivision:function(e){return"/org/".concat(e,"/division/")},postDivision:function(e){return"/org/".concat(e,"/division/")},getDivisionDetails:function(e,t){return"/org/".concat(e,"/division/").concat(t,"/")},putDivision:function(e,t){return"/org/".concat(e,"/division/").concat(t,"/")},deleteDivision:function(e,t){return"/org/".concat(e,"/division/").concat(t,"/")},importDivision:function(e){return"/org/".concat(e,"/division/import/")},downloadSampleDivision:function(e){return"/org/".concat(e,"/division/import/sample")}}},"2c2a":function(e,t,a){"use strict";a("99af");t["a"]={getEmploymentLevel:function(e){return"/org/".concat(e,"/employment/level/")},postEmploymentLevel:function(e){return"/org/".concat(e,"/employment/level/")},getEmploymentLevelDetail:function(e,t){return"/org/".concat(e,"/employment/level/").concat(t,"/")},updateEmploymentLevel:function(e,t){return"/org/".concat(e,"/employment/level/").concat(t,"/")},deleteEmploymentLevel:function(e,t){return"/org/".concat(e,"/employment/level/").concat(t,"/")},importEmploymentLevel:function(e){return"/org/".concat(e,"/employment/level/import/")},downloadSampleEmploymentLevel:function(e){return"/org/".concat(e,"/employment/level/import/sample")}}},"41d3":function(e,t,a){"use strict";a.r(t);var i=function(){var e=this,t=e.$createElement,a=e._self._c||t;return a("div",[a("v-card-text",{staticClass:"scrollbar-thin px-8",staticStyle:{height:"calc(100vh - 250px)"}},[a("v-row",{staticClass:"column"},[e.nonFieldErrors.length?a("v-col",{attrs:{cols:"12"}},[a("non-field-errors",{attrs:{"non-field-errors":e.nonFieldErrors}})],1):e._e(),a("v-col",{staticClass:"pb-0",attrs:{md:"6",cols:"12"}},[a("vue-auto-complete",e._b({directives:[{name:"validate",rawName:"v-validate",value:"required",expression:"'required'"}],attrs:{endpoint:e.autocompleteAPI.jobTitleEndpoint,"prepend-inner-icon":"mdi-file","item-text":"title","item-value":"slug"},model:{value:e.formValues.title,callback:function(t){e.$set(e.formValues,"title",t)},expression:"formValues.title"}},"vue-auto-complete",e.veeValidate("title","Title *"),!1))],1),a("v-col",{staticClass:"pb-0",attrs:{md:"6",cols:"12"}},[a("v-text-field",e._b({directives:[{name:"validate",rawName:"v-validate",value:"required|max:255",expression:"'required|max:255'"}],attrs:{label:"Job Locations *",counter:"255","prepend-inner-icon":"mdi-map-marker"},model:{value:e.formValues.location,callback:function(t){e.$set(e.formValues,"location",t)},expression:"formValues.location"}},"v-text-field",e.veeValidate("location","Job Locations"),!1))],1),a("v-col",{attrs:{md:"6",cols:"12"}},[a("vue-auto-complete",e._b({directives:[{name:"validate",rawName:"v-validate",value:"",expression:"''"}],attrs:{endpoint:e.autocompleteAPI.branchEndpoint,params:{is_archived:"false"},"prepend-inner-icon":"mdi-source-branch","item-text":"name","item-value":"slug"},model:{value:e.formValues.branch,callback:function(t){e.$set(e.formValues,"branch",t)},expression:"formValues.branch"}},"vue-auto-complete",e.veeValidate("branch","Branch"),!1))],1),a("v-col",{attrs:{md:"6",cols:"12"}},[a("vue-auto-complete",e._b({directives:[{name:"validate",rawName:"v-validate",value:"required",expression:"'required'"}],attrs:{endpoint:e.autocompleteAPI.divisionEndpoint,params:{is_archived:"false"},"prepend-inner-icon":"mdi-source-branch","item-text":"name","item-value":"slug"},model:{value:e.formValues.division,callback:function(t){e.$set(e.formValues,"division",t)},expression:"formValues.division"}},"vue-auto-complete",e.veeValidate("division","Division *"),!1))],1),a("v-col",{attrs:{md:"6",cols:"12"}},[a("vue-auto-complete",e._b({directives:[{name:"validate",rawName:"v-validate",value:"required",expression:"'required'"}],attrs:{endpoint:e.autocompleteAPI.employmentLevelEndpoint,params:{is_archived:"false",organization:e.getOrganizationSlug},"prepend-inner-icon":"mdi-source-branch","item-text":"title","item-value":"slug"},model:{value:e.formValues.employment_level,callback:function(t){e.$set(e.formValues,"employment_level",t)},expression:"formValues.employment_level"}},"vue-auto-complete",e.veeValidate("employment_level","Employment Level *"),!1))],1),a("v-col",{staticClass:"pb-0",attrs:{md:"6",cols:"12"}},[a("vue-auto-complete",e._b({directives:[{name:"validate",rawName:"v-validate",value:"required",expression:"'required'"}],attrs:{endpoint:e.autocompleteAPI.employmentTypeEndpoint,params:{is_archived:"false"},"prepend-inner-icon":"mdi-source-branch","item-text":"title","item-value":"slug"},model:{value:e.formValues.employment_status,callback:function(t){e.$set(e.formValues,"employment_status",t)},expression:"formValues.employment_status"}},"vue-auto-complete",e.veeValidate("employment_type","Employment Type *"),!1))],1),a("v-col",{attrs:{md:"6",cols:"12"}},[a("vue-date-time-picker",e._b({directives:[{name:"validate",rawName:"v-validate",value:"required",expression:"'required'"}],attrs:{label:"Deadline *","hide-details":""},model:{value:e.formValues.deadline,callback:function(t){e.$set(e.formValues,"deadline",t)},expression:"formValues.deadline"}},"vue-date-time-picker",e.veeValidate("deadline","Deadline"),!1))],1),a("v-col",{attrs:{md:"6",cols:"12"}},[a("v-row",[a("v-icon",{attrs:{left:""},domProps:{textContent:e._s("mdi-account")}}),a("span",{domProps:{textContent:e._s("Required Number of Candidates *: ")}})],1),a("v-row",{attrs:{"no-gutters":""}},[a("v-col",{staticClass:"py-0",attrs:{md:"6",cols:"12"}},[a("v-switch",e._b({directives:[{name:"validate",rawName:"v-validate",value:"",expression:"''"}],model:{value:e.formValues.show_vacancy_number,callback:function(t){e.$set(e.formValues,"show_vacancy_number",t)},expression:"formValues.show_vacancy_number"}},"v-switch",e.veeValidate("show_vacancy_number","Show Vacancy no."),!1))],1)],1),e.addMoreEmployee?e._e():a("v-btn-toggle",{staticClass:"mb-3",model:{value:e.formValues.vacancies,callback:function(t){e.$set(e.formValues,"vacancies",t)},expression:"formValues.vacancies"}},[e._l(4,(function(t){return a("v-btn",{key:t,staticClass:"mx-0",class:t===e.formValues.vacancies?"indigo darken-4 white--text":"black--text",attrs:{value:t,small:""},domProps:{textContent:e._s(t)}})})),e.formValues.vacancies>4?a("v-btn",{staticClass:"indigo darken-2 white--text mx-0",attrs:{small:""}},[e._v(e._s(e.formValues.vacancies))]):e._e(),a("v-btn",{staticClass:"mx-0",attrs:{small:""},on:{click:function(t){e.addMoreEmployee=!e.addMoreEmployee}}},[e._v("More")])],2),e.addMoreEmployee?a("v-col",{staticClass:"py-0",attrs:{cols:"12"}},[a("v-text-field",e._b({directives:[{name:"validate",rawName:"v-validate",value:"",expression:"''"}],staticClass:"mt-0 pt-0 pl-6",attrs:{type:"number",placeholder:"Add Number"},model:{value:e.formValues.vacancies,callback:function(t){e.$set(e.formValues,"vacancies",t)},expression:"formValues.vacancies"}},"v-text-field",e.veeValidate("vacancies","Vacancies"),!1),[a("template",{slot:"append"},[a("v-btn",{attrs:{text:"",color:"indigo"},on:{click:function(t){e.addMoreEmployee=!e.addMoreEmployee}}},[e._v(" Show Less ")])],1)],2)],1):e._e()],1),a("v-col",{attrs:{md:"6",cols:"12"}},[a("v-row",[a("v-col",{staticClass:"pt-6",attrs:{cols:"1"}},[a("v-icon",{attrs:{left:""},domProps:{textContent:e._s("mdi-card-text-outline")}})],1),a("v-col",{staticClass:"pt-6",attrs:{cols:"11"}},[a("span",{domProps:{textContent:e._s("What is the salary for this job? ")}})])],1),a("v-row",[a("v-col",{staticClass:"pt-0 mt-0 ml-6",attrs:{cols:"12"}},[a("v-switch",{staticClass:"mt-0",attrs:{"v-bind":e.veeValidate("salary_visible_to_candidate","Salary visible to candidate"),label:"Salary visible to candidate","hide-details":""},model:{value:e.formValues.salary_visible_to_candidate,callback:function(t){e.$set(e.formValues,"salary_visible_to_candidate",t)},expression:"formValues.salary_visible_to_candidate"}})],1)],1),a("v-radio-group",{staticClass:"mx-6 mt-0 mb-2",attrs:{mandatory:!1,"hide-details":""},model:{value:e.isRange,callback:function(t){e.isRange=t},expression:"isRange"}},[a("v-row",[a("v-col",{staticClass:"py-0"},[a("v-radio",{attrs:{label:"Range",value:!0}},[a("template",{slot:"label"},[a("div",{staticClass:"text-caption"},[e._v("Range")])])],2)],1),a("v-col",{staticClass:"py-0"},[a("v-radio",{attrs:{label:"Fixed",value:!1}},[a("template",{slot:"label"},[a("div",{staticClass:"text-caption"},[e._v("Fixed")])])],2)],1)],1)],1),a("v-row",{staticClass:"mx-6"},[a("v-col",{staticClass:"py-0",attrs:{md:"6"}},[a("v-text-field",e._b({directives:[{name:"validate",rawName:"v-validate",value:"required",expression:"'required'"}],staticClass:"py-0",attrs:{type:"number",min:"0"},model:{value:e.formValues.offered_salary.minimum,callback:function(t){e.$set(e.formValues.offered_salary,"minimum",t)},expression:"formValues.offered_salary.minimum"}},"v-text-field",e.veeValidate("offered_salary",e.isRange?"Minimum Salary *":"Salary *"),!1))],1),e.isRange?a("v-col",{staticClass:"py-0",attrs:{md:"6"}},[a("v-text-field",{directives:[{name:"validate",rawName:"v-validate",value:"required",expression:"'required'"}],staticClass:"py-0",attrs:{placeholder:"Maximum Salary *",type:"number","hide-details":"",min:"0"},model:{value:e.formValues.offered_salary.maximum,callback:function(t){e.$set(e.formValues.offered_salary,"maximum",t)},expression:"formValues.offered_salary.maximum"}})],1):e._e(),a("v-col",{staticClass:"py-0",attrs:{md:"4"}},[a("v-select",{staticClass:"py-0",attrs:{placeholder:"Select Unit",items:e.unitChoices,"hide-details":""},model:{value:e.formValues.offered_salary.unit,callback:function(t){e.$set(e.formValues.offered_salary,"unit",t)},expression:"formValues.offered_salary.unit"}})],1)],1)],1),a("v-col",{attrs:{md:"6",cols:"12"}},[a("v-row",{staticClass:"pl-3"},[a("v-icon",{staticClass:"pt-5 pb-2",attrs:{left:""},domProps:{textContent:e._s("mdi-card-text-outline")}}),a("span",{staticClass:"pt-5 pb-2",domProps:{textContent:e._s("Shift : ")}})],1),a("v-btn-toggle",{staticClass:"my-1",attrs:{dense:""},model:{value:e.formValues.preferred_shift,callback:function(t){e.$set(e.formValues,"preferred_shift",t)},expression:"formValues.preferred_shift"}},e._l(e.shiftChoices,(function(t){return a("v-btn",{key:t.value,staticClass:"text-capitalize mx-0",class:t.value===e.formValues.preferred_shift?"indigo darken-4 white--text":"black--text",attrs:{value:t.value,depressed:"",small:"",medium:""},domProps:{textContent:e._s(t.text)}})})),1)],1),a("v-col",{attrs:{md:"6",cols:"12"}},[a("v-row",{staticClass:"pl-3"},[a("v-switch",e._b({directives:[{name:"validate",rawName:"v-validate",value:"",expression:"''"}],model:{value:e.formValues.expected_salary_required,callback:function(t){e.$set(e.formValues,"expected_salary_required",t)},expression:"formValues.expected_salary_required"}},"v-switch",e.veeValidate("expected_salary_required","Expected Salary Required"),!1))],1)],1),a("v-col",{attrs:{md:"6",cols:"12"}},[a("v-row",{staticClass:"pl-3"},[a("v-switch",e._b({directives:[{name:"validate",rawName:"v-validate",value:"",expression:"''"}],model:{value:e.formValues.is_internal,callback:function(t){e.$set(e.formValues,"is_internal",t)},expression:"formValues.is_internal"}},"v-switch",e.veeValidate("is_internal","Is Internal"),!1))],1)],1),a("v-col",{staticClass:"py-0",attrs:{md:"6",cols:"12"}},[a("v-row",{staticClass:"pl-3"},[a("v-switch",e._b({directives:[{name:"validate",rawName:"v-validate",value:"",expression:"''"}],model:{value:e.formValues.references_required,callback:function(t){e.$set(e.formValues,"references_required",t)},expression:"formValues.references_required"}},"v-switch",e.veeValidate("references_required","Make References mandatory"),!1))],1)],1),a("v-col",{staticClass:"py-0",attrs:{md:"6",cols:"12"}},[a("v-row",{staticClass:"pl-3"},[a("v-switch",e._b({directives:[{name:"validate",rawName:"v-validate",value:"",expression:"''"}],model:{value:e.formValues.curriculum_vitae_required,callback:function(t){e.$set(e.formValues,"curriculum_vitae_required",t)},expression:"formValues.curriculum_vitae_required"}},"v-switch",e.veeValidate("curriculum_vitae_required","Make Curriculum Vitae mandatory"),!1))],1)],1)],1)],1),a("v-divider"),a("v-card-actions",[a("v-col",{staticClass:"text-right py-0"},[a("v-btn",{staticClass:"text-capitalize",attrs:{text:""},on:{click:function(t){return e.$emit("close")}}},[e._v(" Cancel ")]),a("v-btn",{staticClass:"white--text text-capitalize",attrs:{depressed:"",color:"primary"},on:{click:e.createBasicInfo}},[e._v(" Save & Continue ")]),e.updateSlug?a("v-btn",{staticClass:"text-capitalize white--text mx-2",attrs:{color:"primary",outlined:""},on:{click:function(t){return e.$emit("switch",2)}}},[e._v(" Next ")]):e._e()],1)],1)],1)},o=[],n=a("1da1"),s=a("5530"),r=(a("96cf"),a("ac1f"),a("1276"),a("99af"),a("c44a")),l=a("d567"),c=a("f1d0"),u=a("e59e"),m=a("1229"),d=a("86eb"),p=a("2f62"),v=a("2c2a"),f=a("7e77"),h=a("3cd5"),g=a("08f6"),y=a("5660"),_=a("ab8a"),b={components:{NonFieldErrors:_["default"],VueAutoComplete:y["default"],VueDateTimePicker:l["a"]},mixins:[r["a"]],props:{updateSlug:{type:String,default:""},jobDetail:{type:Object,required:!0},as:{type:String,default:""}},data:function(){return{formValues:{title:"",tags:[],vacancies:1,deadline:"",available_for:"full_time",offered_salary:{currency:"NRs",operator:"Equals",minimum:null,maximum:null,unit:"Monthly"},job_level:"entry_level",preferred_shift:"Morning",expected_salary_required:!1,references_required:!1,curriculum_vitae_required:!1,salary_visible_to_candidate:!0,is_internal:!1,show_vacancy_number:!1},addMoreEmployee:!1,isRange:!1,autocompleteAPI:{divisionEndpoint:"",branchEndpoint:"",organizationApi:"",jobCategoryApi:"",jobLocationApi:"",jobTitleEndpoint:"",employmentLevelEndpoint:"",employmentTypeEndpoint:""},jobTypeChoices:[{name:"Full Time",value:"full_time"},{name:"Part Time",value:"part_time"},{name:"Contractual",value:"contractual"},{name:"Freelancing",value:"freelancing"},{name:"Internship",value:"internship"},{name:"Volunteer",value:"volunteer"},{name:"Temporary",value:"temporary"},{name:"Traineeship",value:"traineeship"}],jobTitleEndpoint:"",operatorChoices:[{value:"Above",display_name:"Above"},{value:"Below",display_name:"Below"},{value:"Equals",display_name:"Equals"}],unitChoices:[{value:"Hourly",text:"Hourly"},{value:"Daily",text:"Daily"},{value:"Weekly",text:"Weekly"},{value:"Monthly",text:"Monthly"},{value:"Yearly",text:"Yearly"}],jobLevelChoices:[{value:"top_level",text:"Top Level"},{value:"senior_level",text:"Senior Level"},{value:"mid_level",text:"Mid Level"},{value:"entry_level",text:"Entry Level"}],shiftChoices:[{value:"Morning",text:"Morning"},{value:"Day",text:"Day"},{value:"Night",text:"Night"},{value:"Evening",text:"Evening"},{value:"Anytime",text:"Anytime"}]}},computed:Object(s["a"])({},Object(p["c"])({getSupervisorOrganization:"supervisor/getOrganizationSlug"})),created:function(){this.initializeEndpoint(),this.updateSlug?this.populateFormValues(this.jobDetail):this.formValues.deadline=this.getDeadline()},methods:{initializeEndpoint:function(){this.autocompleteAPI.jobLocationApi=g["a"].getJobLocations,this.autocompleteAPI.organizationApi=c["a"].getOrganizationList,this.autocompleteAPI.divisionEndpoint=m["a"].getDivision(this.$route.params.slug?this.$route.params.slug:this.getSupervisorOrganization),this.autocompleteAPI.branchEndpoint=u["a"].getBranch(this.$route.params.slug?this.$route.params.slug:this.getSupervisorOrganization),this.autocompleteAPI.jobTitleEndpoint=d["a"].getJobTitle(this.$route.params.slug?this.$route.params.slug:this.getSupervisorOrganization),this.autocompleteAPI.employmentLevelEndpoint=v["a"].getEmploymentLevel(this.$route.params.slug?this.$route.params.slug:this.getSupervisorOrganization),this.autocompleteAPI.employmentTypeEndpoint=f["a"].getEmploymentType(this.$route.params.slug?this.$route.params.slug:this.getSupervisorOrganization)},getDeadline:function(){var e=new Date((new Date).getTime()+6048e5-6e4*(new Date).getTimezoneOffset()).toISOString().split(".")[0];return"true"===localStorage.useNepaliDate?this.ad2bs(e)+" "+e.split("T")[1]:e},populateFormValues:function(e){e&&(this.formValues=Object(s["a"])({},e),this.isRange=!!this.get(e,"offered_salary.maximum"),this.formValues.deadline=e.deadline)},createBasicInfo:function(){var e=this;return Object(n["a"])(regeneratorRuntime.mark((function t(){return regeneratorRuntime.wrap((function(t){while(1)switch(t.prev=t.next){case 0:return t.next=2,e.validateAllFields();case 2:if(!t.sent){t.next=9;break}if(!e.formValues.slug){t.next=7;break}e.$http.put(h["a"].putBasicInformation(e.formValues.slug)+"?organization=".concat(e.getOrganizationSlug,"&as=").concat(e.as),e.constructFormValues()).then((function(t){e.notifyUser("Successfully updated Basic Information"),e.$emit("createdSlug",t.slug),e.$emit("refresh"),e.$emit("switch",2)})).catch((function(t){e.pushErrors(t),e.notifyInvalidFormResponse("Review Field and try again.")})),t.next=9;break;case 7:return t.next=9,e.$http.post(h["a"].postBasicInformation+"?organization=".concat(e.getOrganizationSlug,"&as=").concat(e.as),e.constructFormValues()).then((function(t){e.$emit("createdSlug",t.slug),e.$emit("switch",2),e.$emit("refresh"),e.notifyUser("Successfully Added Basic Information.")})).catch((function(t){e.notifyInvalidFormResponse("Review Field and try again."),e.pushErrors(t),e.formValues.available_for="full_time"}));case 9:case"end":return t.stop()}}),t)})))()},constructFormValues:function(){return{organization:this.getOrganizationSlug,branch:this.formValues.branch,employment_status:this.formValues.employment_status,employment_level:this.formValues.employment_level,division:this.formValues.division,title:this.formValues.title,location:this.formValues.location,deadline:this.formValues.deadline,vacancies:this.formValues.vacancies,offered_salary:this.formValues.offered_salary,preferred_shift:this.formValues.preferred_shift,expected_salary_required:this.formValues.expected_salary_required,references_required:this.formValues.references_required,curriculum_vitae_required:this.formValues.curriculum_vitae_required,salary_visible_to_candidate:this.formValues.salary_visible_to_candidate,is_internal:this.formValues.is_internal,show_vacancy_number:this.formValues.show_vacancy_number}}}},x=b,V=a("2877"),w=a("6544"),C=a.n(w),E=a("8336"),S=a("a609"),k=a("99d9"),$=a("62ad"),q=a("ce7e"),T=a("132d"),D=a("67b6"),j=a("43a6"),A=a("0fd9b"),O=a("b974"),z=a("b73d"),L=a("8654"),I=Object(V["a"])(x,i,o,!1,null,null,null);t["default"]=I.exports;C()(I,{VBtn:E["a"],VBtnToggle:S["a"],VCardActions:k["a"],VCardText:k["c"],VCol:$["a"],VDivider:q["a"],VIcon:T["a"],VRadio:D["a"],VRadioGroup:j["a"],VRow:A["a"],VSelect:O["a"],VSwitch:z["a"],VTextField:L["a"]})},"7e77":function(e,t,a){"use strict";a("99af");t["a"]={getEmploymentType:function(e){return"/org/".concat(e,"/employment/status/")},postEmploymentType:function(e){return"/org/".concat(e,"/employment/status/")},getEmploymentStatusDetail:function(e,t){return"/org/".concat(e,"/employment/status/").concat(t,"/")},updateEmploymentType:function(e,t){return"/org/".concat(e,"/employment/status/").concat(t,"/")},deleteEmploymentType:function(e,t){return"/org/".concat(e,"/employment/status/").concat(t,"/")},downloadSampleEmploymentType:function(e){return"/org/".concat(e,"/employment/status/import/sample")},importEmploymentType:function(e){return"/org/".concat(e,"/employment/status/import/")}}},"86eb":function(e,t,a){"use strict";a("99af");t["a"]={getJobTitle:function(e){return"/org/".concat(e,"/employment/job-title/")},postJobTitle:function(e){return"/org/".concat(e,"/employment/job-title/")},getJobTitleDetail:function(e,t){return"/org/".concat(e,"/employment/job-title/").concat(t,"/")},updateJobTitle:function(e,t){return"/org/".concat(e,"/employment/job-title/").concat(t,"/")},deleteJobTitle:function(e,t){return"/org/".concat(e,"/employment/job-title/").concat(t,"/")},importJobTitle:function(e){return"/org/".concat(e,"/employment/job-title/import/")},downloadSampleJobTitle:function(e){return"/org/".concat(e,"/employment/job-title/import/sample")}}},"9d01":function(e,t,a){},b73d:function(e,t,a){"use strict";var i=a("5530"),o=(a("0481"),a("ec29"),a("9d01"),a("fe09")),n=a("c37a"),s=a("c3f0"),r=a("0789"),l=a("490a"),c=a("80d2");t["a"]=o["a"].extend({name:"v-switch",directives:{Touch:s["a"]},props:{inset:Boolean,loading:{type:[Boolean,String],default:!1},flat:{type:Boolean,default:!1}},computed:{classes:function(){return Object(i["a"])(Object(i["a"])({},n["a"].options.computed.classes.call(this)),{},{"v-input--selection-controls v-input--switch":!0,"v-input--switch--flat":this.flat,"v-input--switch--inset":this.inset})},attrs:function(){return{"aria-checked":String(this.isActive),"aria-disabled":String(this.isDisabled),role:"switch"}},validationState:function(){return this.hasError&&this.shouldValidate?"error":this.hasSuccess?"success":null!==this.hasColor?this.computedColor:void 0},switchData:function(){return this.setTextColor(this.loading?void 0:this.validationState,{class:this.themeClasses})}},methods:{genDefaultSlot:function(){return[this.genSwitch(),this.genLabel()]},genSwitch:function(){return this.$createElement("div",{staticClass:"v-input--selection-controls__input"},[this.genInput("checkbox",Object(i["a"])(Object(i["a"])({},this.attrs),this.attrs$)),this.genRipple(this.setTextColor(this.validationState,{directives:[{name:"touch",value:{left:this.onSwipeLeft,right:this.onSwipeRight}}]})),this.$createElement("div",Object(i["a"])({staticClass:"v-input--switch__track"},this.switchData)),this.$createElement("div",Object(i["a"])({staticClass:"v-input--switch__thumb"},this.switchData),[this.genProgress()])])},genProgress:function(){return this.$createElement(r["c"],{},[!1===this.loading?null:this.$slots.progress||this.$createElement(l["a"],{props:{color:!0===this.loading||""===this.loading?this.color||"primary":this.loading,size:16,width:2,indeterminate:!0}})])},onSwipeLeft:function(){this.isActive&&this.onChange()},onSwipeRight:function(){this.isActive||this.onChange()},onKeydown:function(e){(e.keyCode===c["y"].left&&this.isActive||e.keyCode===c["y"].right&&!this.isActive)&&this.onChange()}}})},e59e:function(e,t,a){"use strict";a("99af");t["a"]={getBranch:function(e){return"/org/".concat(e,"/branch/")},postBranch:function(e){return"/org/".concat(e,"/branch/")},getBranchDetail:function(e,t){return"/org/".concat(e,"/branch/").concat(t,"/")},updateBranch:function(e,t){return"/org/".concat(e,"/branch/").concat(t,"/")},deleteBranch:function(e,t){return"/org/".concat(e,"/branch/").concat(t,"/")},importBranch:function(e){return"/org/".concat(e,"/branch/import/")},downloadSampleBranch:function(e){return"/org/".concat(e,"/branch/import/sample")},exportBranch:function(e){return"/org/".concat(e,"/branch/export")},branchType:function(e){return"/org/".concat(e,"/branch-type")},branchTypeDetail:function(e,t){return"org/".concat(e,"/branch-type/").concat(t)}}},f1d0:function(e,t,a){"use strict";t["a"]={getOrganizationList:"/org/",getOrganization:function(e){return"/org/".concat(e,"/")},updateOrganization:function(e){return"/org/".concat(e,"/")},getOrgEmployeeData:function(e){return"/org/".concat(e,"/employee-data/")}}}}]);