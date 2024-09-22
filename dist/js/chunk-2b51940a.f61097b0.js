(window["webpackJsonp"]=window["webpackJsonp"]||[]).push([["chunk-2b51940a","chunk-63c80d7a"],{"0798":function(t,e,n){"use strict";var r=n("5530"),o=n("ade3"),a=(n("caad"),n("0c18"),n("10d2")),s=n("afdd"),i=n("9d26"),c=n("f2e7"),l=n("7560"),d=n("f40d"),u=n("58df"),h=n("d9bd");e["a"]=Object(u["a"])(a["a"],c["a"],d["a"]).extend({name:"v-alert",props:{border:{type:String,validator:function(t){return["top","right","bottom","left"].includes(t)}},closeLabel:{type:String,default:"$vuetify.close"},coloredBorder:Boolean,dense:Boolean,dismissible:Boolean,closeIcon:{type:String,default:"$cancel"},icon:{default:"",type:[Boolean,String],validator:function(t){return"string"===typeof t||!1===t}},outlined:Boolean,prominent:Boolean,text:Boolean,type:{type:String,validator:function(t){return["info","error","success","warning"].includes(t)}},value:{type:Boolean,default:!0}},computed:{__cachedBorder:function(){if(!this.border)return null;var t={staticClass:"v-alert__border",class:Object(o["a"])({},"v-alert__border--".concat(this.border),!0)};return this.coloredBorder&&(t=this.setBackgroundColor(this.computedColor,t),t.class["v-alert__border--has-color"]=!0),this.$createElement("div",t)},__cachedDismissible:function(){var t=this;if(!this.dismissible)return null;var e=this.iconColor;return this.$createElement(s["a"],{staticClass:"v-alert__dismissible",props:{color:e,icon:!0,small:!0},attrs:{"aria-label":this.$vuetify.lang.t(this.closeLabel)},on:{click:function(){return t.isActive=!1}}},[this.$createElement(i["a"],{props:{color:e}},this.closeIcon)])},__cachedIcon:function(){return this.computedIcon?this.$createElement(i["a"],{staticClass:"v-alert__icon",props:{color:this.iconColor}},this.computedIcon):null},classes:function(){var t=Object(r["a"])(Object(r["a"])({},a["a"].options.computed.classes.call(this)),{},{"v-alert--border":Boolean(this.border),"v-alert--dense":this.dense,"v-alert--outlined":this.outlined,"v-alert--prominent":this.prominent,"v-alert--text":this.text});return this.border&&(t["v-alert--border-".concat(this.border)]=!0),t},computedColor:function(){return this.color||this.type},computedIcon:function(){return!1!==this.icon&&("string"===typeof this.icon&&this.icon?this.icon:!!["error","info","success","warning"].includes(this.type)&&"$".concat(this.type))},hasColoredIcon:function(){return this.hasText||Boolean(this.border)&&this.coloredBorder},hasText:function(){return this.text||this.outlined},iconColor:function(){return this.hasColoredIcon?this.computedColor:void 0},isDark:function(){return!(!this.type||this.coloredBorder||this.outlined)||l["a"].options.computed.isDark.call(this)}},created:function(){this.$attrs.hasOwnProperty("outline")&&Object(h["a"])("outline","outlined",this)},methods:{genWrapper:function(){var t=[this.$slots.prepend||this.__cachedIcon,this.genContent(),this.__cachedBorder,this.$slots.append,this.$scopedSlots.close?this.$scopedSlots.close({toggle:this.toggle}):this.__cachedDismissible],e={staticClass:"v-alert__wrapper"};return this.$createElement("div",e,t)},genContent:function(){return this.$createElement("div",{staticClass:"v-alert__content"},this.$slots.default)},genAlert:function(){var t={staticClass:"v-alert",attrs:{role:"alert"},on:this.listeners$,class:this.classes,style:this.styles,directives:[{name:"show",value:this.isActive}]};if(!this.coloredBorder){var e=this.hasText?this.setTextColor:this.setBackgroundColor;t=e(this.computedColor,t)}return this.$createElement("div",t,[this.genWrapper()])},toggle:function(){this.isActive=!this.isActive}},render:function(t){var e=this.genAlert();return this.transition?t("transition",{props:{name:this.transition,origin:this.origin,mode:this.mode}},[e]):e}})},"0c18":function(t,e,n){},1491:function(t,e,n){"use strict";n.r(e);var r=function(){var t=this,e=t.$createElement,n=t._self._c||e;return n("div",[n("v-card",[n("vue-card-title",{attrs:{title:"Yearly Payslip Report",subtitle:"This is yearly payslip report "+("hr"===t.as?"of individual employee":""),icon:"mdi-cash"}},[n("template",{slot:"actions"},[t.response&&t.response.report_rows.length>0&&!t.loading?n("v-btn",{attrs:{small:"",depressed:"",color:"primary"},on:{click:function(e){return t.generateExcel("yearlyReport","Yearly Payslip Report","ms-excel")}}},[t._v(" Download Excel Report ")]):t._e(),n("v-btn",{attrs:{"data-cy":"btn-filter",icon:""},on:{click:function(e){t.showFilter=!t.showFilter}}},[n("v-icon",{attrs:{small:""},domProps:{textContent:t._s("mdi-filter-variant")}})],1)],1)],2),n("v-divider"),n("v-slide-y-transition",[n("div",{directives:[{name:"show",rawName:"v-show",value:t.showFilter,expression:"showFilter"}]},[n("v-row",{staticClass:"mx-3"},["hr"===t.as?n("v-col",{attrs:{cols:"12",sm:"4"}},[n("vue-users-auto-complete",{attrs:{params:{organization:t.getOrganizationSlug,is_active:"all",is_blocked:"all"},"applied-class":"pa-0 ma-0",placeholder:"Select Employee","hide-details":"",disabled:!t.selectedFiscalYear,label:""},model:{value:t.selectedUser,callback:function(e){t.selectedUser=e},expression:"selectedUser"}})],1):t._e(),n("v-col",{attrs:{cols:"12",sm:"4"}},[n("v-select",{staticClass:"py-0 pr-4 ma-0",attrs:{items:t.fiscalYearList,label:"","prepend-inner-icon":"mdi-calendar-month-outline",placeholder:"Fiscal Year","item-text":"name","item-value":"id","hide-details":""},model:{value:t.selectedFiscalYear,callback:function(e){t.selectedFiscalYear=e},expression:"selectedFiscalYear"}})],1),n("v-col",{staticClass:"py-0",attrs:{cols:"12",sm:"4"}},[n("v-switch",{attrs:{label:"Addons Detail"},model:{value:t.displayAddonsDetail,callback:function(e){t.displayAddonsDetail=e},expression:"displayAddonsDetail"}})],1)],1),n("v-divider")],1)]),n("v-divider"),n("v-row",[t.nonFieldErrors.length>0?n("v-col",{attrs:{cols:"12"}},[t.nonFieldErrors?n("non-field-form-errors",{attrs:{"non-field-errors":t.nonFieldErrors}}):t._e()],1):t._e()],1),t.selectedUser?t._e():n("v-alert",{staticClass:"text-body-1",attrs:{dense:"",text:"",type:"info",icon:"mdi-alert-outline"}},[t._v("Select employee to load data. ")]),t.response?n("div",{ref:"yearlyPayslip",staticClass:"pa-5",attrs:{id:"yearlyReport"}},[n("v-row",{staticClass:"\n          blue\n          lighten-5\n          no-gutters\n          text-subtitle-2\n          font-weight-regular\n          pa-2\n        ",staticStyle:{margin:"4px 2px 12px 2px"}},[n("v-col",{staticClass:"excel-hidden",attrs:{cols:"3"}},[n("div",[t._v("Name")]),n("div",[t._v("Username")]),n("div",[t._v("Branch")]),n("div",[t._v("Last Payroll Paid Date")]),n("div",[t._v("Contract Expiry Date")])]),n("v-col",{staticClass:"blueGrey--text font-weight-medium excel-hidden",attrs:{cols:"3"}},[n("div",[t._v(" : "),n("span",{staticClass:"font-weight-bold"},[t._v(t._s(t.get(t.response.employee,"full_name")||"N/A"))])]),n("div",[t._v(": "+t._s(t.get(t.response.employee,"username")||"N/A"))]),n("div",[t._v(": "+t._s(t.get(t.response.employee,"branch")||"N/A"))]),n("div",[t._v(": "+t._s(t.get(t.response,"last_paid")||"N/A"))]),n("div",[t._v(": "+t._s(t.get(t.response,"dismiss_date")||"N/A"))])]),n("v-col",{staticClass:"excel-hidden",attrs:{cols:"3"}},[n("div",[t._v("Job Title")]),n("div",[t._v("Marital status")]),n("div",[t._v("Division")]),n("div",[t._v("Organization")]),n("div",[t._v("Date of Join")])]),n("v-col",{staticClass:"blueGrey--text font-weight-medium excel-hidden",attrs:{cols:"3"}},[n("div",[t._v(": "+t._s(t.get(t.response.employee,"job_title")||"N/A"))]),n("div",[t._v(": "+t._s(t.get(t.response.employee,"marital_status")||"N/A"))]),n("div",[t._v(": "+t._s(t.get(t.response.employee,"division.name")||"N/A"))]),n("div",[t._v(" : "+t._s(t.get(t.response.employee,"organization.name")||"N/A")+" ")]),n("div",[t._v(": "+t._s(t.get(t.response.employee,"joined_date")||"N/A"))])]),n("v-col",{staticClass:"excel-only"},[n("table",[n("tr",[n("td",[n("strong",[t._v("Name")])]),n("td",[n("span",{staticClass:"font-weight-bold"},[t._v(" "+t._s(t.get(t.response.employee,"full_name")||"N/A")+" ")])]),n("td",[n("strong",[t._v("Username")])]),n("td",[t._v(t._s(t.get(t.response.employee,"username")||"N/A"))]),n("td",[n("strong",[t._v("Branch")])]),n("td",[t._v(t._s(t.get(t.response.employee,"branch")||"N/A"))]),n("td",[n("strong",[t._v("Last Payroll Paid Date")])]),n("td",[t._v(t._s(t.get(t.response,"last_paid")||"N/A"))]),n("td",[n("strong",[t._v("Contract Expiry Date")])]),n("td",[t._v(t._s(t.get(t.response,"dismiss_date")||"N/A"))])]),n("tr",[n("td",[n("strong",[t._v("Job Title")])]),n("td",[t._v(" "+t._s(t.get(t.response.employee,"job_title")||"N/A")+" ")]),n("td",[n("strong",[t._v("Marital status")])]),n("td",[t._v(" "+t._s(t.get(t.response.employee,"marital_status")||"N/A")+" ")]),n("td",[n("strong",[t._v("Division")])]),n("td",[t._v(" "+t._s(t.get(t.response.employee,"division.name")||"N/A")+" ")]),n("td",[n("strong",[t._v("Organization")])]),n("td",[t._v(" "+t._s(t.get(t.response.employee,"organization.name")||"N/A")+" ")]),n("td",[n("strong",[t._v("Date of Join")])]),n("td",[t._v(t._s(t.get(t.response.employee,"joined_date")||"N/A"))])])])])],1),t.response.report_rows.length>0?n("div",{staticClass:"horizontal-scrollbar",staticStyle:{display:"block","white-space":"nowrap"}},[n("table",{staticClass:"custom-yearly-layout",staticStyle:{width:"100%"}},[n("thead",{staticClass:"white--text text-subtitle-2"},[n("tr",[n("th",{staticStyle:{"min-width":"150px"}},[t._v("Salary Title")]),t._l(t.response.month_slots,(function(e,r){return[n("v-tooltip",{key:r,attrs:{top:""},scopedSlots:t._u([{key:"activator",fn:function(r){var o=r.on;return[n("th",t._g({},o),[t._v(t._s(e.display_name))])]}}],null,!0)},[n("span",[t._v(t._s(e.from_date+"--"+e.to_date))])])]})),t.displayAddonsDetail?t._l(t.response.addons_rows,(function(e,r){return n("th",{key:"addons"+r,staticStyle:{"min-width":"100px"}},[t._v(" "+t._s(e.title)+" ")])})):n("th",[t._v("Addons")]),n("th",{staticStyle:{"min-width":"150px"}},[t._v("Sum")])],2)]),n("tbody",{staticClass:"grey--text text--darken-2 text-center"},[n("tr",{staticClass:"blue lighten-5 font-weight-medium"},[n("td",[t._v("Description")]),n("td",{attrs:{colspan:t.response.month_slots.length+t.response.addons_rows.length+1}},[t._v(" Earnings ")])]),t._l(t.earning_rows,(function(e,r){return[n("tr",{key:"earning"+r,staticClass:"very-light-blue"},[n("td",[t._v(t._s(e.heading))]),t._l(e.payment_months,(function(e,r){return[n("td",{key:"earning-amount"+r},[t._v(" "+t._s(t.formatCurrency(e.amount)||"-")+" ")])]})),t.displayAddonsDetail?t._l(t.response.addons_rows,(function(r,o){return n("td",{key:"addons-earning"+o},[t._v(" "+t._s(t.formatCurrency(t.getIncentiveAmount(e,r))||"-")+" ")])})):n("td",[t._v(t._s(t.formatCurrency(t.getAddonsAmount(e))))]),n("td",[t._v(t._s(t.formatCurrency(t.sum_row_earning[r])||"-"))])],2)]})),n("tr",{staticClass:"very-light-blue font-weight-bold"},[n("td",[t._v("Total Earning")]),t._l(t.total_earning,(function(e,r){return n("td",{key:r},[t._v(" "+t._s(t.formatCurrency(e.amount)||"-")+" ")])})),t.displayAddonsDetail?t._l(t.sumAddonsAmount("addition"),(function(e,r){return n("td",{key:"addons-total-earning"+r},[t._v(" "+t._s(t.formatCurrency(e)||"-")+" ")])})):n("td",[t._v(" "+t._s(t.formatCurrency(t.totalAddonsAmount("addition")))+" ")]),n("td",[t._v(t._s(t.formatCurrency(t.sum_row_total_earning)||"-"))])],2),n("tr",{staticClass:"blue lighten-5 font-weight-medium"},[n("td",[t._v("Description")]),n("td",{attrs:{colspan:t.response.month_slots.length+t.response.addons_rows.length+1}},[t._v(" Deductions ")])]),t._l(t.deduction_rows,(function(e,r){return[n("tr",{key:"deduction"+r,staticClass:"very-light-blue"},[n("td",[t._v(t._s(e.heading))]),t._l(e.payment_months,(function(e,r){return[n("td",{key:"deduction-amount"+r},[t._v(" "+t._s(t.formatCurrency(e.amount)||"-")+" ")])]})),t.displayAddonsDetail?t._l(t.response.addons_rows,(function(r,o){return n("td",{key:"addons-deduction"+o},[t._v(" "+t._s(t.formatCurrency(t.getIncentiveAmount(e,r))||"-")+" ")])})):n("td",[t._v(t._s(t.formatCurrency(t.getAddonsAmount(e))))]),n("td",[t._v(t._s(t.formatCurrency(t.sum_row_deduction[r])||"-"))])],2)]})),n("tr",{staticClass:"very-light-blue font-weight-bold"},[n("td",[t._v("Total Deduction")]),t._l(t.total_deduction,(function(e,r){return n("td",{key:r},[t._v(" "+t._s(t.formatCurrency(e.amount)||"-")+" ")])})),t.displayAddonsDetail?t._l(t.sumAddonsAmount("deduction"),(function(e,r){return n("td",{key:"addons-total-deduction"+r},[t._v(" "+t._s(t.formatCurrency(e)||"-")+" ")])})):n("td",[t._v(" "+t._s(t.formatCurrency(t.totalAddonsAmount("deduction")))+" ")]),n("td",[t._v(t._s(t.formatCurrency(t.sum_row_total_deduction)||"-"))])],2),n("tr",{staticClass:"blue lighten-5 font-weight-bold"},[n("td",[t._v("Net Pay")]),t._l(t.net_pay,(function(e,r){return n("td",{key:r},[t._v(" "+t._s(t.formatCurrency(e.amount)||"-")+" ")])})),t.displayAddonsDetail?t._l(t.getNetPayOfAddons(),(function(e,r){return n("td",{key:"addons-net-pay"+r},[t._v(" "+t._s(t.formatCurrency(e)||"--")+" ")])})):n("td",[t._v(t._s(t.formatCurrency(t.totalNetPayOfAddons())))]),n("td",[t._v(t._s(t.formatCurrency(t.sum_row_total_net_pay)||""))])],2),n("tr")],2)])]):n("vue-no-data")],1):t.selectedUser&&!t.downloading&&t.loading?n("default-svg-loader"):t._e()],1)],1)},o=[],a=n("3835"),s=n("b85c"),i=(n("d3b7"),n("3ca3"),n("ddb0"),n("159b"),n("4e827"),n("a434"),n("99af"),n("7db0"),n("d81d"),n("4de4"),n("caad"),n("2532"),n("8b61")),c=n("cfa3"),l=n("d242"),d={getYearlyPayslipByUser:function(t,e){return"payroll/".concat(t,"/reports/yearly-payslip/").concat(e,"/")}},u=n("51d8"),h=n("cf45"),f=n("9dc8"),p={components:{VueUsersAutoComplete:function(){return n.e("chunk-aee42bec").then(n.bind(null,"ef8c"))},VueNoData:function(){return Promise.resolve().then(n.bind(null,"e585"))},DefaultSvgLoader:function(){return n.e("chunk-2d2160c2").then(n.bind(null,"c197"))},NonFieldFormErrors:function(){return n.e("chunk-2d213000").then(n.bind(null,"ab8a"))}},mixins:[l["a"],i["a"],c["a"],f["a"]],props:{as:{type:String,required:!0}},data:function(){return{htmlTitle:"Yearly Report | Payslip | Admin",breadCrumbItems:[{text:"Payroll",to:{name:"admin-slug-payroll-overview",params:{slug:this.$route.params.slug}},disabled:!1},{text:"Report",disabled:!1,to:{name:"admin-slug-payroll-reports",params:{slug:this.$route.params.slug}}},{text:"Payslip Yearly Report",disabled:!0}],headers:[{text:"Fiscal Year",value:"fiscal_year"},{text:"Action",align:"center",sortable:!1}],showFilter:!0,fiscalYearEndpoint:"",fiscalYearList:[],selectedUser:"",selectedFiscalYear:null,displayAddonsDetail:!1,displayDetail:!1}},computed:{default_row_for_total:function(){var t=this.deepCopy(this.response.month_slots);return t.forEach((function(t){t.amount=0})),t},sum_row_total_earning:function(){var t=0;this.total_earning.forEach((function(e){t+=e.amount}));var e=this.sumAddonsAmount("addition");return e.length&&(t+=e.reduce((function(t,e){return t+e}))),t},sum_row_total_deduction:function(){var t=0;this.total_deduction.forEach((function(e){t+=e.amount}));var e=this.sumAddonsAmount("deduction");return e.length&&(t+=e.reduce((function(t,e){return t+e}))),t},sum_row_total_net_pay:function(){var t=0;this.net_pay.forEach((function(e){t+=e.amount}));var e=this.getNetPayOfAddons();return e.length&&(t+=e.reduce((function(t,e){return t+e}))),t},sum_row_earning:function(){var t=this,e=[];return this.earning_rows.forEach((function(n,r){var o=t.getAddonsAmount(n);n.payment_months.forEach((function(t){t.amount&&(o+=t.amount)})),e[r]=o})),e},sum_row_deduction:function(){var t=this,e=[];return this.deduction_rows.forEach((function(n,r){var o=t.getAddonsAmount(n);n.payment_months.forEach((function(t){t.amount&&(o+=t.amount)})),e[r]=o})),e},earning_rows:function(){var t,e=this.response.earning_rows,n=this.deepCopy(this.default_row_for_total),r=Object(s["a"])(e);try{for(r.s();!(t=r.n()).done;){var o,i=t.value,c=Object(s["a"])(n.entries());try{for(c.s();!(o=c.n()).done;){var l,d=Object(a["a"])(o.value,2),u=d[0],h=d[1],f=!1,p=Object(s["a"])(i.payment_months);try{for(p.s();!(l=p.n()).done;){var m=l.value;if(h.from_date===m.from_date&&h.to_date===m.to_date){f=!0;break}}}catch(g){p.e(g)}finally{p.f()}!1===f&&i.payment_months.splice(u,0,{from_date:h.from_date,to_date:h.from_date,amount:null})}}catch(g){c.e(g)}finally{c.f()}}}catch(g){r.e(g)}finally{r.f()}return e.sort((function(t,e){return t.order-e.order}))},deduction_rows:function(){var t,e=this.response.deduction_rows,n=this.deepCopy(this.default_row_for_total),r=Object(s["a"])(e);try{for(r.s();!(t=r.n()).done;){var o,i=t.value,c=Object(s["a"])(n.entries());try{for(c.s();!(o=c.n()).done;){var l,d=Object(a["a"])(o.value,2),u=d[0],h=d[1],f=!1,p=Object(s["a"])(i.payment_months);try{for(p.s();!(l=p.n()).done;){var m=l.value;if(h.from_date===m.from_date&&h.to_date===m.to_date){f=!0;break}}}catch(g){p.e(g)}finally{p.f()}!1===f&&i.payment_months.splice(u,0,{from_date:h.from_date,to_date:h.from_date,amount:null})}}catch(g){c.e(g)}finally{c.f()}}}catch(g){r.e(g)}finally{r.f()}return e.sort((function(t,e){return t.order-e.order}))},total_earning:function(){var t=this.deepCopy(this.default_row_for_total);return this.earning_rows.forEach((function(e){e.payment_months.forEach((function(e){t.forEach((function(t){e.from_date===t.from_date&&e.to_date===t.to_date&&(t.amount+=e.amount)}))}))})),t},total_deduction:function(){var t=this.deepCopy(this.default_row_for_total);return this.deduction_rows.forEach((function(e){e.payment_months.forEach((function(e){t.forEach((function(t){e.from_date===t.from_date&&e.to_date===t.to_date&&(t.amount+=e.amount)}))}))})),t},net_pay:function(){var t=this,e=this.deepCopy(this.default_row_for_total);return this.total_earning.forEach((function(n){t.total_deduction.forEach((function(t){n.from_date===t.from_date&&n.to_date===t.to_date&&e.forEach((function(e){t.from_date===e.from_date&&t.to_date===e.to_date&&(e.amount=n.amount-t.amount)}))}))})),e}},watch:{selectedUser:function(t){this.response=null,t&&(this.crud.endpoint.common=d.getYearlyPayslipByUser(this.getOrganizationSlug,t)+"?as=".concat(this.as,"&fiscal_year=").concat(this.selectedFiscalYear),this.getData())},selectedFiscalYear:function(t){this.response=null,this.selectedUser&&(this.crud.endpoint.common=d.getYearlyPayslipByUser(this.getOrganizationSlug,this.selectedUser)+"?as=".concat(this.as,"&fiscal_year=").concat(t),this.getData())}},created:function(){var t=this;"user"===this.as&&(this.selectedUser=this.getAuthStateUserId),this.$http.get(u["a"].getFiscalYear(this.getOrganizationSlug)+"?category=global").then((function(e){t.fiscalYearList=e.results,t.selectedFiscalYear=t.fiscalYearList.find((function(t){return t.id===e.current_fiscal})).id})),null===this.selectedFiscalYear&&(this.selectedFiscalYear="")},methods:{formatCurrency:h["d"],getIncentiveAmount:function(t,e){if(!e.headings.length)return null;var n=null;return e.headings.map((function(e){t.heading===e.heading&&(n=e.amount)})),n},getAddonsAmount:function(t){var e=this;if(!this.response.addons_rows.length)return 0;var n=0;return this.response.addons_rows.forEach((function(r){n+=e.getIncentiveAmount(t,r)||0})),n},getNetPayOfAddons:function(){if(!this.response.addons_rows.length)return 0;var t=[];return this.response.addons_rows.forEach((function(e){var n=e.headings.filter((function(t){return"Type2Cnst"===t["heading_type"]}));t.push(n.length?n[0].amount:0)})),t},totalNetPayOfAddons:function(){var t=this.getNetPayOfAddons();return t.length?t.reduce((function(t,e){return t+e})):0},sumAddonsAmount:function(t){if(!this.response.addons_rows.length)return 0;var e={addition:["Addition","Extra Addition"],deduction:["Deduction","Extra Deduction","Tax Deduction"]}[t],n=[];return this.response.addons_rows.forEach((function(t){var r=t.headings.filter((function(t){return e.includes(t["heading_type"])})),o=r.reduce((function(t,e){var n=e.amount||0;return t+n}),0);n.push(o)})),n},totalAddonsAmount:function(t){var e=this.sumAddonsAmount(t);return e.length?e.reduce((function(t,e){return t+e})):0}}},m=p,g=(n("4118"),n("2877")),_=n("6544"),v=n.n(_),y=n("0798"),b=n("8336"),w=n("b0af"),x=n("62ad"),C=n("ce7e"),A=n("132d"),k=n("0fd9b"),O=n("b974"),S=n("0789"),E=n("b73d"),D=n("3a2f"),j=Object(g["a"])(m,r,o,!1,null,"6c911891",null);e["default"]=j.exports;v()(j,{VAlert:y["a"],VBtn:b["a"],VCard:w["a"],VCol:x["a"],VDivider:C["a"],VIcon:A["a"],VRow:k["a"],VSelect:O["a"],VSlideYTransition:S["g"],VSwitch:E["a"],VTooltip:D["a"]})},"1f04":function(t,e,n){"use strict";n.d(e,"b",(function(){return o})),n.d(e,"a",(function(){return c}));var r=n("1da1");n("d3b7"),n("3ca3"),n("ddb0"),n("96cf");function o(t){return a.apply(this,arguments)}function a(){return a=Object(r["a"])(regeneratorRuntime.mark((function t(e){var n,r;return regeneratorRuntime.wrap((function(t){while(1)switch(t.prev=t.next){case 0:return t.next=2,s(e);case 2:return n=t.sent,t.next=5,c([n]);case 5:return r=t.sent,t.abrupt("return",r[0]);case 7:case"end":return t.stop()}}),t)}))),a.apply(this,arguments)}function s(t){return i.apply(this,arguments)}function i(){return i=Object(r["a"])(regeneratorRuntime.mark((function t(e){var n;return regeneratorRuntime.wrap((function(t){while(1)switch(t.prev=t.next){case 0:return t.next=2,fetch(e);case 2:return n=t.sent,t.next=5,n.blob();case 5:return t.abrupt("return",t.sent);case 6:case"end":return t.stop()}}),t)}))),i.apply(this,arguments)}function c(t){return l.apply(this,arguments)}function l(){return l=Object(r["a"])(regeneratorRuntime.mark((function t(e){var n,r,o;return regeneratorRuntime.wrap((function(t){while(1)switch(t.prev=t.next){case 0:for(n=function(t){var e=new FileReader;return new Promise((function(n){e.readAsDataURL(t),e.onloadend=function(){n(e.result)}}))},r=[],o=0;o<e.length;o++)r.push(n(e[o]));return t.next=5,Promise.all(r);case 5:return t.abrupt("return",t.sent);case 6:case"end":return t.stop()}}),t)}))),l.apply(this,arguments)}},4118:function(t,e,n){"use strict";n("7b42")},"51d8":function(t,e,n){"use strict";n("99af");e["a"]={getFiscalYear:function(t){return"/org/".concat(t,"/fiscal-year/")},postFiscalYear:function(t){return"/org/".concat(t,"/fiscal-year/")},getFiscalYearDetails:function(t,e){return"/org/".concat(t,"/fiscal-year/").concat(e,"/")},updateFiscalYear:function(t,e){return"/org/".concat(t,"/fiscal-year/").concat(e,"/")},deleteFiscalYear:function(t,e){return"/org/".concat(t,"/fiscal-year/").concat(e,"/")},exportRebate:function(t){return"/payroll/".concat(t,"/user-voluntary-rebates/export/")}}},"7b42":function(t,e,n){},"9d01":function(t,e,n){},"9dc8":function(t,e,n){"use strict";var r=n("1da1"),o=n("5530"),a=(n("96cf"),n("7db0"),n("ac1f"),n("5319"),n("2f62")),s=n("1157"),i=n.n(s);e["a"]={data:function(){return{downloading:!1}},methods:Object(o["a"])(Object(o["a"])({},Object(a["d"])({setSnackBar:"common/setSnackBar"})),{},{generateExcel:function(t){var e=arguments,n=this;return Object(r["a"])(regeneratorRuntime.mark((function r(){var o,a,s,c,l,d,u,h,f;return regeneratorRuntime.wrap((function(r){while(1)switch(r.prev=r.next){case 0:if(o=e.length>1&&void 0!==e[1]?e[1]:"",a=e.length>2?e[2]:void 0,s={"ms-word":".doc","ms-excel":".xls"},l="application/vdn.".concat(a),n.setSnackBar({text:"Your excel file will be downloaded shortly.",color:"info",persist:!1}),d=document.getElementById(t),u=d.cloneNode(!0),i()(u).find(".excel-hidden").remove(),h=u.outerHTML.replace(/ /g,"%20"),o=o?o+s[a]:"excel_data".concat(s[a]),c=document.createElement("a"),document.body.appendChild(c),navigator.msSaveOrOpenBlob)f=new Blob(["\ufeff",h],{type:l}),navigator.msSaveOrOpenBlob(f,o);else{c.href="data:"+l+", "+h,c.download=o;try{c.click()}catch(p){n.setSnackBar({text:"Your request was not successful.",color:"red"}),n.downloading=!1}}case 13:case"end":return r.stop()}}),r)})))()}})}},b73d:function(t,e,n){"use strict";var r=n("5530"),o=(n("0481"),n("ec29"),n("9d01"),n("fe09")),a=n("c37a"),s=n("c3f0"),i=n("0789"),c=n("490a"),l=n("80d2");e["a"]=o["a"].extend({name:"v-switch",directives:{Touch:s["a"]},props:{inset:Boolean,loading:{type:[Boolean,String],default:!1},flat:{type:Boolean,default:!1}},computed:{classes:function(){return Object(r["a"])(Object(r["a"])({},a["a"].options.computed.classes.call(this)),{},{"v-input--selection-controls v-input--switch":!0,"v-input--switch--flat":this.flat,"v-input--switch--inset":this.inset})},attrs:function(){return{"aria-checked":String(this.isActive),"aria-disabled":String(this.isDisabled),role:"switch"}},validationState:function(){return this.hasError&&this.shouldValidate?"error":this.hasSuccess?"success":null!==this.hasColor?this.computedColor:void 0},switchData:function(){return this.setTextColor(this.loading?void 0:this.validationState,{class:this.themeClasses})}},methods:{genDefaultSlot:function(){return[this.genSwitch(),this.genLabel()]},genSwitch:function(){return this.$createElement("div",{staticClass:"v-input--selection-controls__input"},[this.genInput("checkbox",Object(r["a"])(Object(r["a"])({},this.attrs),this.attrs$)),this.genRipple(this.setTextColor(this.validationState,{directives:[{name:"touch",value:{left:this.onSwipeLeft,right:this.onSwipeRight}}]})),this.$createElement("div",Object(r["a"])({staticClass:"v-input--switch__track"},this.switchData)),this.$createElement("div",Object(r["a"])({staticClass:"v-input--switch__thumb"},this.switchData),[this.genProgress()])])},genProgress:function(){return this.$createElement(i["c"],{},[!1===this.loading?null:this.$slots.progress||this.$createElement(c["a"],{props:{color:!0===this.loading||""===this.loading?this.color||"primary":this.loading,size:16,width:2,indeterminate:!0}})])},onSwipeLeft:function(){this.isActive&&this.onChange()},onSwipeRight:function(){this.isActive||this.onChange()},onKeydown:function(t){(t.keyCode===l["y"].left&&this.isActive||t.keyCode===l["y"].right&&!this.isActive)&&this.onChange()}}})},d242:function(t,e,n){"use strict";var r=n("1da1"),o=n("5530"),a=(n("96cf"),n("d3b7"),n("3ca3"),n("ddb0"),n("caad"),n("159b"),n("99af"),n("b0c0"),n("7db0"),n("fb6a"),n("2f62")),s=n("f1d0"),i=n("1f04"),c=n("cf45");e["a"]={data:function(){return{orgInfo:null,serverTime:null,downloading:!1}},methods:Object(o["a"])(Object(o["a"])({},Object(a["d"])({setSnackBar:"common/setSnackBar"})),{},{downloadPdf:function(t){var e=arguments,o=this;return Object(r["a"])(regeneratorRuntime.mark((function a(){var s,l,d,u,h,f,p;return regeneratorRuntime.wrap((function(a){while(1)switch(a.prev=a.next){case 0:if(s=e.length>1&&void 0!==e[1]?e[1]:"p",l=e.length>2?e[2]:void 0,d=e.length>3&&void 0!==e[3]?e[3]:35,u=e.length>4&&void 0!==e[4]?e[4]:1245,h=e.length>5&&void 0!==e[5]?e[5]:1475,t.$el&&(t=t.$el),!o.loading){a.next=8;break}return a.abrupt("return");case 8:return scroll(0,0),a.prev=9,o.loading=!0,o.downloading=!0,o.setSnackBar({text:"File Downloading. Please wait...",color:"info",persist:!0}),a.next=15,o.loadOrganizationInfo();case 15:f=0,p=0,"l"===s&&(f=805,p=86),setTimeout(Object(r["a"])(regeneratorRuntime.mark((function e(){var a,m,g,_,v,y;return regeneratorRuntime.wrap((function(e){while(1)switch(e.prev=e.next){case 0:return a=t.getBoundingClientRect().top,m=t.getBoundingClientRect().left,g=t.offsetHeight+parseInt(getComputedStyle(t).marginTop),_=[],v=document.getElementsByClassName("download-only"),y=document.getElementsByClassName("download-hidden"),e.next=8,n.e("chunk-2d216257").then(n.t.bind(null,"c0e9",7)).then(function(){var e=Object(r["a"])(regeneratorRuntime.mark((function e(n){var o,s,i,c,l;return regeneratorRuntime.wrap((function(e){while(1)switch(e.prev=e.next){case 0:o=n.default;case 1:if(!(g>=40)){e.next=8;break}for(s=0;s<v.length;s++)v[s].style.display="block";for(i=0;i<y.length;i++)y[i].style.display="none";return e.next=6,o(t,{x:m-d,y:a,width:u,height:h-f,type:"dataURL",scale:2,useCORS:!0,windowWidth:1300}).then(function(){var t=Object(r["a"])(regeneratorRuntime.mark((function t(e){return regeneratorRuntime.wrap((function(t){while(1)switch(t.prev=t.next){case 0:_.push(e.toDataURL("image/png")),g-=h-f,a+=h-f;case 3:case"end":return t.stop()}}),t)})));return function(e){return t.apply(this,arguments)}}());case 6:e.next=1;break;case 8:for(c=0;c<v.length;c++)v[c].style.display="none";for(l=0;l<y.length;l++)y[l].style.display="";case 10:case"end":return e.stop()}}),e)})));return function(t){return e.apply(this,arguments)}}());case 8:n.e("chunk-e0378ed4").then(n.bind(null,"8baf")).then(function(){var t=Object(r["a"])(regeneratorRuntime.mark((function t(e){var n,r,a,d,u;return regeneratorRuntime.wrap((function(t){while(1)switch(t.prev=t.next){case 0:if(n=e.default,r=new n(s,"mm"),!["manualtesting","development"].includes(Object(c["f"])("VUE_APP_ENV"))){t.next=8;break}return t.next=5,Object(i["b"])("https://i.imgur.com/fHyEMsl.jpg");case 5:a=t.sent,t.next=11;break;case 8:return t.next=10,Object(i["b"])(o.orgInfo.logo);case 10:a=t.sent;case 11:d=210+p,u=32,_.forEach((function(t,e){e>0&&r.addPage(),r.addImage(t,"PNG",0,u,d,0,void 0,"FAST"),o.setHeaderAndFooter(e,r,a,_.length,s)})),r.save(l||"file.pdf"),o.loading=!1,o.setSnackBar({text:"",color:"",display:!1,error:!1});case 17:case"end":return t.stop()}}),t)})));return function(e){return t.apply(this,arguments)}}());case 9:case"end":return e.stop()}}),e)}))),500),a.next=27;break;case 21:a.prev=21,a.t0=a["catch"](9),console.error("Error while downloading pdf",a.t0),o.setSnackBar({text:"Your request was not successful.",color:"red"}),o.loading=!1,o.downloading=!1;case 27:case"end":return a.stop()}}),a,null,[[9,21]])})))()},setHeaderAndFooter:function(t,e,n,r,o){var a=0,s=0;"l"===o&&(a=2.5,s=84);var i=t+1,c=e.internal.pageSize.getWidth(),l=e.internal.pageSize.getHeight(),d=this.serverTime,u="Page ".concat(i," of ").concat(r);e.setPage(i),e.setFont("Helvetica","normal"),e.setLineWidth(.2),e.setDrawColor(150),e.line(7.5+a,27,203+s,27),e.line(7.5+a,l-12,203+s,l-12),e.setTextColor(150),e.setFontSize(8),e.text(u,7.5+a,l-7),e.text(d,c-8-a,l-7,{align:"right"});var h=this.orgInfo.address?this.orgInfo.address+",":"",f=this.orgInfo.phone_no?"Tel: ".concat(this.orgInfo.phone_no):"";e.text("".concat(h," ").concat(f),c-8-a,17,{align:"right"});var p=this.orgInfo.email?this.orgInfo.email+",":"",m=this.orgInfo.website||"";e.text("".concat(p," ").concat(m),c-8-a,21,{align:"right"}),e.setTextColor(100),e.setFontSize(14),e.setFont("Helvetica","bold"),e.text("".concat(this.orgInfo.name),c-8-a,13,{align:"right"}),e.addImage(n,"JPEG",7.5+a,7,18,18,void 0,"FAST")},loadOrganizationInfo:function(){var t=this;return Object(r["a"])(regeneratorRuntime.mark((function e(){var n,r;return regeneratorRuntime.wrap((function(e){while(1)switch(e.prev=e.next){case 0:if(n=t.getOrganizationSlug,r=JSON.parse(localStorage.getItem("org-info"))||[],!(r.length>0&&r.some((function(t){return t.slug===n})))){e.next=6;break}t.orgInfo=r.find((function(t){return t.slug===n})),e.next=8;break;case 6:return e.next=8,t.$http.get(s["a"].getOrganization(n)).then((function(e){var n=e.name,o=e.slug,a=e.appearance.logo,s=e.address?e.address.address:"",i=e.email,c=e.contacts.Phone,l=e.website,d={name:n,slug:o,logo:a,address:s,email:i,phone_no:c,website:l};r.push(d),localStorage.setItem("org-info",JSON.stringify(r)),t.orgInfo=d}));case 8:return e.next=10,t.$http.get("server-info/?fields=server_time").then((function(e){var n=e.server_time;n=n.slice(0,-6),t.serverTime=t.$dayjs(n).format("YYYY-MM-DD HH:mm:ss A")}));case 10:case"end":return e.stop()}}),e)})))()}})}},f1d0:function(t,e,n){"use strict";e["a"]={getOrganizationList:"/org/",getOrganization:function(t){return"/org/".concat(t,"/")},updateOrganization:function(t){return"/org/".concat(t,"/")},getOrgEmployeeData:function(t){return"/org/".concat(t,"/employee-data/")}}}}]);