(window["webpackJsonp"]=window["webpackJsonp"]||[]).push([["pages/admin/_slug/hris/noticeboard-approval/request.vue","chunk-26c51c79","chunk-31f8a6e6","chunk-2d2259e9"],{"0549":function(t,e,a){"use strict";a.r(e);var i=function(){var t=this,e=t.$createElement,a=t._self._c||e;return a("div",[a("v-row",{staticClass:"mb-3",attrs:{"no-gutters":""}},[t.breadCrumbs?a("v-col",{attrs:{cols:"12"}},[a("v-card",{attrs:{flat:""}},[a("v-breadcrumbs",{staticClass:"text-body-1 pa-2",class:{"text-caption pa-1":t.$vuetify.breakpoint.xs},attrs:{items:t.breadCrumbs},scopedSlots:t._u([{key:"item",fn:function(e){return[a("span",{class:e.item.disabled?"grey--text":"baseColor--text text--accent-2 pointer",domProps:{textContent:t._s(e.item.text)},on:{click:function(a){return t.$router.push(e.item.to)}}})]}}],null,!1,1670153796)},[a("v-icon",{attrs:{slot:"divider"},slot:"divider"},[t._v("mdi-chevron-right")])],1)],1)],1):t._e()],1),a("v-row",{attrs:{"no-gutters":""}},[a("v-col",{attrs:{cols:"12"}},[t._t("default")],2)],1)],1)},s=[],n=a("5530"),r=(a("ac1f"),a("1276"),a("b0c0"),a("2f62")),o={props:{title:{type:String,required:!0},breadCrumbs:{type:Array,default:function(){return[]}}},computed:Object(n["a"])({},Object(r["c"])({getOrganizationName:"organization/getOrganizationName",getSupervisorSwitchedOrganization:"supervisor/getSwitchedOrganization"})),mounted:function(){document.title="".concat(this.title," | RealHRsoft");var t=this.$route.params.slug?"admin-slug-dashboard":"root",e=this.$route.name.split("-"),a=this.getOrganizationName;this.getSupervisorSwitchedOrganization&&"user"===e[0]&&"supervisor"===e[1]&&(a=this.getSupervisorSwitchedOrganization.name),this.breadCrumbs.unshift({text:a,disabled:!1,to:{name:t,params:{slug:this.$route.params.slug}}})}},l=o,c=a("2877"),d=a("6544"),u=a.n(d),h=a("2bc5"),p=a("b0af"),m=a("62ad"),f=a("132d"),g=a("0fd9b"),v=Object(c["a"])(l,i,s,!1,null,null,null);e["default"]=v.exports;u()(v,{VBreadcrumbs:h["a"],VCard:p["a"],VCol:m["a"],VIcon:f["a"],VRow:g["a"]})},"17cc":function(t,e,a){"use strict";var i=a("b85c"),s=a("1da1"),n=a("5530");a("96cf"),a("ac1f"),a("841c"),a("d3b7"),a("3ca3"),a("ddb0"),a("2b3d"),a("b64b");e["a"]={data:function(){return{fetchedResults:[],response:{},extra_data:"",appliedFilters:{},footerProps:{itemsPerPageOptions:[10,20,30,40,50,100]},pagination:{sortBy:["modified_at"],descending:!1,totalItems:0,page:1,rowsPerPage:10,pageCount:0},triggerDataTable:!0,fullParams:""}},created:function(){this.getParams(this.DataTableFilter)},methods:{getParams:function(t){var e=Object(n["a"])(Object(n["a"])({},t),{},{offset:(this.pagination.page-1)*this.pagination.rowsPerPage,limit:this.pagination.rowsPerPage,ordering:this.pagination.descending?this.pagination.sortBy:"-"+this.pagination.sortBy});this.fullParams=this.convertToURLSearchParams(e)},loadDataTable:function(t){this.response=t,this.fetchedResults=t.results,this.pagination.totalItems=t.count,this.extra_data=t.extra_data,this.triggerDataTable=!0},fetchData:function(t){var e=this;return Object(s["a"])(regeneratorRuntime.mark((function a(){var i,s;return regeneratorRuntime.wrap((function(a){while(1)switch(a.prev=a.next){case 0:return console.warn("DatatableMixin: fetchData has been deprecated. Please use the function in page itself."),i=Object(n["a"])(Object(n["a"])(Object(n["a"])({},t),e.appliedFilters),{},{search:e.search,offset:(e.pagination.page-1)*e.pagination.rowsPerPage,limit:e.pagination.rowsPerPage,ordering:e.pagination.descending?e.pagination.sortBy:"-"+e.pagination.sortBy}),s=e.convertToURLSearchParams(i),e.loading=!0,a.next=6,e.$http.get(e.endpoint,{params:s}).then((function(t){e.response=t,e.fetchedResults=t.results,e.pagination.totalItems=t.count})).finally((function(){e.loading=!1}));case 6:case"end":return a.stop()}}),a)})))()},applyFilters:function(t){this.appliedFilters=t,this.fetchData(t)},convertToURLSearchParams:function(t){for(var e=new URLSearchParams,a=0,s=Object.keys(t);a<s.length;a++){var n=s[a],r=t[n];if(void 0===r&&(r=""),Array.isArray(r)){var o,l=Object(i["a"])(r);try{for(l.s();!(o=l.n()).done;){var c=o.value;e.append(n,c)}}catch(d){l.e(d)}finally{l.f()}}else e.append(n,r)}return e},loadDataTableChange:function(){var t=this;this.triggerDataTable&&(this.getParams(this.DataTableFilter),this.$nextTick((function(){t.fetchDataTable()})))}},watch:{DataTableFilter:function(t){this.fetchedResults=[],this.getParams(t),this.fetchDataTable(),this.pagination.page=1},"pagination.sortBy":function(){this.fetchedResults=[],this.loadDataTableChange()},"pagination.descending":function(){this.fetchedResults=[],this.loadDataTableChange()},"pagination.page":function(){this.fetchedResults=[],this.loadDataTableChange()},"pagination.rowsPerPage":function(){this.fetchedResults=[],this.loadDataTableChange()}}}},1806:function(t,e,a){"use strict";var i=a("1da1"),s=(a("96cf"),a("d3b7"),a("b0c0"),a("99af"),a("c44a")),n=a("17cc");e["a"]={mixins:[s["a"],n["a"]],data:function(){return{crud:{name:"operation",endpoint:{common:"",get:"",post:"",put:"",patch:"",delete:""},id:"id",dataTableFetch:void 0},loading:!1,rowsPerPageItems:[10,20,30,40,50],formValues:this.deepCopy(this.actionData||{}),deleteNotification:{dialog:!1,heading:"Confirm Delete",text:"Are you sure you want to delete ?"}}},created:function(){this.crud.dataTableFetch&&this.loadDataTableChange()},methods:{submit:function(){this.formValues&&this.formValues.id?this.updateData():this.insertData()},fetchDataTable:function(){var t=this;this.loading||(this.loading=!0,this.$http.get(this.crud.endpoint.common||this.crud.endpoint.get,{params:this.fullParams}).then((function(e){t.loadDataTable(e),t.processAfterTableLoad()})).catch((function(e){t.pushErrors(e),t.notifyInvalidFormResponse()})).finally((function(){t.loading=!1})))},insertData:function(){var t=this;return Object(i["a"])(regeneratorRuntime.mark((function e(){var a;return regeneratorRuntime.wrap((function(e){while(1)switch(e.prev=e.next){case 0:if(!t.loading){e.next=2;break}return e.abrupt("return");case 2:return e.next=4,t.validateAllFields();case 4:if(!e.sent){e.next=8;break}t.loading=!0,a="".concat(t.crud.endpoint.post||t.crud.endpoint.common),t.$http.post(a,t.getFormValues()).then((function(){t.$emit("create"),t.processAfterInsert(),t.notifyUser("Successfully created ".concat(t.crud.name))})).catch((function(e){t.pushErrors(e),t.notifyInvalidFormResponse()})).finally((function(){t.loading=!1}));case 8:case"end":return e.stop()}}),e)})))()},updateData:function(){var t=this;return Object(i["a"])(regeneratorRuntime.mark((function e(){var a,i,s;return regeneratorRuntime.wrap((function(e){while(1)switch(e.prev=e.next){case 0:if(!t.loading){e.next=2;break}return e.abrupt("return");case 2:return e.next=4,t.validateAllFields();case 4:if(!e.sent){e.next=10;break}t.loading=!0,a=t.crud.endpoint.patch||t.crud.endpoint.put||"".concat(t.crud.endpoint.common).concat(t.actionData[t.crud.id],"/"),i=t.getFormValues(),s=t.crud.endpoint.patch?"patch":"put",t.$http[s](a,i).then((function(){t.$emit("update"),t.processAfterUpdate(),t.notifyUser("Successfully Updated ".concat(t.crud.name))})).catch((function(e){t.pushErrors(e),t.notifyInvalidFormResponse()})).finally((function(){t.loading=!1}));case 10:case"end":return e.stop()}}),e)})))()},deleteData:function(){var t=this;if(!this.loading){var e=this.actionData?this.actionData[this.crud.id]:"",a="".concat(this.crud.endpoint.delete," || ").concat(this.crud.endpoint.common,"/").concat(e,"/");this.loading=!0,this.$http.delete(a).then((function(){t.notifyUser("Successfully Deleted ".concat(t.crud.name)),t.deleteNotification.dialog=!1,t.actionData={},"undefined"!==t.dataTableFetch&&t.loadDataTableChange(),t.processAfterDelete()})).catch((function(e){t.pushErrors(e),t.notifyInvalidFormResponse()})).finally((function(){t.loading=!1}))}},getFormValues:function(){return this.formValues},processAfterTableLoad:function(){return null},processAfterInsert:function(){return null},processAfterUpdate:function(){return null},processAfterDelete:function(){return null}}}},"1e6c":function(t,e,a){"use strict";var i=a("9d65"),s=a("4e82"),n=a("c3f0"),r=a("80d2"),o=a("58df"),l=Object(o["a"])(i["a"],Object(s["a"])("windowGroup","v-window-item","v-window"));e["a"]=l.extend().extend().extend({name:"v-window-item",directives:{Touch:n["a"]},props:{disabled:Boolean,reverseTransition:{type:[Boolean,String],default:void 0},transition:{type:[Boolean,String],default:void 0},value:{required:!1}},data:function(){return{isActive:!1,inTransition:!1}},computed:{classes:function(){return this.groupClasses},computedTransition:function(){return this.windowGroup.internalReverse?"undefined"!==typeof this.reverseTransition?this.reverseTransition||"":this.windowGroup.computedTransition:"undefined"!==typeof this.transition?this.transition||"":this.windowGroup.computedTransition}},methods:{genDefaultSlot:function(){return this.$slots.default},genWindowItem:function(){return this.$createElement("div",{staticClass:"v-window-item",class:this.classes,directives:[{name:"show",value:this.isActive}],on:this.$listeners},this.genDefaultSlot())},onAfterTransition:function(){this.inTransition&&(this.inTransition=!1,this.windowGroup.transitionCount>0&&(this.windowGroup.transitionCount--,0===this.windowGroup.transitionCount&&(this.windowGroup.transitionHeight=void 0)))},onBeforeTransition:function(){this.inTransition||(this.inTransition=!0,0===this.windowGroup.transitionCount&&(this.windowGroup.transitionHeight=Object(r["g"])(this.windowGroup.$el.clientHeight)),this.windowGroup.transitionCount++)},onTransitionCancelled:function(){this.onAfterTransition()},onEnter:function(t){var e=this;this.inTransition&&this.$nextTick((function(){e.computedTransition&&e.inTransition&&(e.windowGroup.transitionHeight=Object(r["g"])(t.clientHeight))}))}},render:function(t){var e=this;return t("transition",{props:{name:this.computedTransition},on:{beforeEnter:this.onBeforeTransition,afterEnter:this.onAfterTransition,enterCancelled:this.onTransitionCancelled,beforeLeave:this.onBeforeTransition,afterLeave:this.onAfterTransition,leaveCancelled:this.onTransitionCancelled,enter:this.onEnter}},this.showLazyContent((function(){return[e.genWindowItem()]})))}})},"1f09":function(t,e,a){},"2bc5":function(t,e,a){"use strict";var i=a("5530"),s=(a("a15b"),a("abd3"),a("ade3")),n=a("1c87"),r=a("58df"),o=Object(r["a"])(n["a"]).extend({name:"v-breadcrumbs-item",props:{activeClass:{type:String,default:"v-breadcrumbs__item--disabled"},ripple:{type:[Boolean,Object],default:!1}},computed:{classes:function(){return Object(s["a"])({"v-breadcrumbs__item":!0},this.activeClass,this.disabled)}},render:function(t){var e=this.generateRouteLink(),a=e.tag,s=e.data;return t("li",[t(a,Object(i["a"])(Object(i["a"])({},s),{},{attrs:Object(i["a"])(Object(i["a"])({},s.attrs),{},{"aria-current":this.isActive&&this.isLink?"page":void 0})}),this.$slots.default)])}}),l=a("80d2"),c=Object(l["i"])("v-breadcrumbs__divider","li"),d=a("7560");e["a"]=Object(r["a"])(d["a"]).extend({name:"v-breadcrumbs",props:{divider:{type:String,default:"/"},items:{type:Array,default:function(){return[]}},large:Boolean},computed:{classes:function(){return Object(i["a"])({"v-breadcrumbs--large":this.large},this.themeClasses)}},methods:{genDivider:function(){return this.$createElement(c,this.$slots.divider?this.$slots.divider:this.divider)},genItems:function(){for(var t=[],e=!!this.$scopedSlots.item,a=[],i=0;i<this.items.length;i++){var s=this.items[i];a.push(s.text),e?t.push(this.$scopedSlots.item({item:s})):t.push(this.$createElement(o,{key:a.join("."),props:s},[s.text])),i<this.items.length-1&&t.push(this.genDivider())}return t}},render:function(t){var e=this.$slots.default||this.genItems();return t("ul",{staticClass:"v-breadcrumbs",class:this.classes},e)}})},3129:function(t,e,a){"use strict";var i=a("3835"),s=a("5530"),n=(a("ac1f"),a("1276"),a("d81d"),a("a630"),a("3ca3"),a("5319"),a("1f09"),a("c995")),r=a("24b2"),o=a("7560"),l=a("58df"),c=a("80d2");e["a"]=Object(l["a"])(n["a"],r["a"],o["a"]).extend({name:"VSkeletonLoader",props:{boilerplate:Boolean,loading:Boolean,tile:Boolean,transition:String,type:String,types:{type:Object,default:function(){return{}}}},computed:{attrs:function(){return this.isLoading?this.boilerplate?{}:Object(s["a"])({"aria-busy":!0,"aria-live":"polite",role:"alert"},this.$attrs):this.$attrs},classes:function(){return Object(s["a"])(Object(s["a"])({"v-skeleton-loader--boilerplate":this.boilerplate,"v-skeleton-loader--is-loading":this.isLoading,"v-skeleton-loader--tile":this.tile},this.themeClasses),this.elevationClasses)},isLoading:function(){return!("default"in this.$scopedSlots)||this.loading},rootTypes:function(){return Object(s["a"])({actions:"button@2",article:"heading, paragraph",avatar:"avatar",button:"button",card:"image, card-heading","card-avatar":"image, list-item-avatar","card-heading":"heading",chip:"chip","date-picker":"list-item, card-heading, divider, date-picker-options, date-picker-days, actions","date-picker-options":"text, avatar@2","date-picker-days":"avatar@28",heading:"heading",image:"image","list-item":"text","list-item-avatar":"avatar, text","list-item-two-line":"sentences","list-item-avatar-two-line":"avatar, sentences","list-item-three-line":"paragraph","list-item-avatar-three-line":"avatar, paragraph",paragraph:"text@3",sentences:"text@2",table:"table-heading, table-thead, table-tbody, table-tfoot","table-heading":"heading, text","table-thead":"heading@6","table-tbody":"table-row-divider@6","table-row-divider":"table-row, divider","table-row":"table-cell@6","table-cell":"text","table-tfoot":"text@2, avatar@2",text:"text"},this.types)}},methods:{genBone:function(t,e){return this.$createElement("div",{staticClass:"v-skeleton-loader__".concat(t," v-skeleton-loader__bone")},e)},genBones:function(t){var e=this,a=t.split("@"),s=Object(i["a"])(a,2),n=s[0],r=s[1],o=function(){return e.genStructure(n)};return Array.from({length:r}).map(o)},genStructure:function(t){var e=[];t=t||this.type||"";var a=this.rootTypes[t]||"";if(t===a);else{if(t.indexOf(",")>-1)return this.mapBones(t);if(t.indexOf("@")>-1)return this.genBones(t);a.indexOf(",")>-1?e=this.mapBones(a):a.indexOf("@")>-1?e=this.genBones(a):a&&e.push(this.genStructure(a))}return[this.genBone(t,e)]},genSkeleton:function(){var t=[];return this.isLoading?t.push(this.genStructure()):t.push(Object(c["s"])(this)),this.transition?this.$createElement("transition",{props:{name:this.transition},on:{afterEnter:this.resetStyles,beforeEnter:this.onBeforeEnter,beforeLeave:this.onBeforeLeave,leaveCancelled:this.resetStyles}},t):t},mapBones:function(t){return t.replace(/\s/g,"").split(",").map(this.genStructure)},onBeforeEnter:function(t){this.resetStyles(t),this.isLoading&&(t._initialStyle={display:t.style.display,transition:t.style.transition},t.style.setProperty("transition","none","important"))},onBeforeLeave:function(t){t.style.setProperty("display","none","important")},resetStyles:function(t){t._initialStyle&&(t.style.display=t._initialStyle.display||"",t.style.transition=t._initialStyle.transition,delete t._initialStyle)}},render:function(t){return t("div",{staticClass:"v-skeleton-loader",attrs:this.attrs,on:this.$listeners,class:this.classes,style:this.isLoading?this.measurableStyles:void 0},[this.genSkeleton()])}})},3860:function(t,e,a){"use strict";var i=a("604c");e["a"]=i["a"].extend({name:"button-group",provide:function(){return{btnToggle:this}},computed:{classes:function(){return i["a"].options.computed.classes.call(this)}},methods:{genData:i["a"].options.methods.genData}})},"3e35":function(t,e,a){"use strict";var i=a("5530"),s=a("1e6c"),n=a("adda"),r=a("58df"),o=a("80d2"),l=a("1c87"),c=Object(r["a"])(s["a"],l["a"]);e["a"]=c.extend({name:"v-carousel-item",inheritAttrs:!1,methods:{genDefaultSlot:function(){return[this.$createElement(n["a"],{staticClass:"v-carousel__item",props:Object(i["a"])(Object(i["a"])({},this.$attrs),{},{height:this.windowGroup.internalHeight}),on:this.$listeners,scopedSlots:{placeholder:this.$scopedSlots.placeholder}},Object(o["s"])(this))]},genWindowItem:function(){var t=this.generateRouteLink(),e=t.tag,a=t.data;return a.staticClass="v-window-item",a.directives.push({name:"show",value:this.isActive}),this.$createElement(e,a,this.genDefaultSlot())}}})},"5e66":function(t,e,a){"use strict";var i=a("5530"),s=(a("a9e3"),a("63b7"),a("f665")),n=a("afdd"),r=a("9d26"),o=a("37c6"),l=a("3860"),c=a("80d2"),d=a("d9bd");e["a"]=s["a"].extend({name:"v-carousel",props:{continuous:{type:Boolean,default:!0},cycle:Boolean,delimiterIcon:{type:String,default:"$delimiter"},height:{type:[Number,String],default:500},hideDelimiters:Boolean,hideDelimiterBackground:Boolean,interval:{type:[Number,String],default:6e3,validator:function(t){return t>0}},mandatory:{type:Boolean,default:!0},progress:Boolean,progressColor:String,showArrows:{type:Boolean,default:!0},verticalDelimiters:{type:String,default:void 0}},data:function(){return{internalHeight:this.height,slideTimeout:void 0}},computed:{classes:function(){return Object(i["a"])(Object(i["a"])({},s["a"].options.computed.classes.call(this)),{},{"v-carousel":!0,"v-carousel--hide-delimiter-background":this.hideDelimiterBackground,"v-carousel--vertical-delimiters":this.isVertical})},isDark:function(){return this.dark||!this.light},isVertical:function(){return null!=this.verticalDelimiters}},watch:{internalValue:"restartTimeout",interval:"restartTimeout",height:function(t,e){t!==e&&t&&(this.internalHeight=t)},cycle:function(t){t?this.restartTimeout():(clearTimeout(this.slideTimeout),this.slideTimeout=void 0)}},created:function(){this.$attrs.hasOwnProperty("hide-controls")&&Object(d["a"])("hide-controls",':show-arrows="false"',this)},mounted:function(){this.startTimeout()},methods:{genControlIcons:function(){return this.isVertical?null:s["a"].options.methods.genControlIcons.call(this)},genDelimiters:function(){return this.$createElement("div",{staticClass:"v-carousel__controls",style:{left:"left"===this.verticalDelimiters&&this.isVertical?0:"auto",right:"right"===this.verticalDelimiters?0:"auto"}},[this.genItems()])},genItems:function(){for(var t=this,e=this.items.length,a=[],i=0;i<e;i++){var s=this.$createElement(n["a"],{staticClass:"v-carousel__controls__item",attrs:{"aria-label":this.$vuetify.lang.t("$vuetify.carousel.ariaLabel.delimiter",i+1,e)},props:{icon:!0,small:!0,value:this.getValue(this.items[i],i)}},[this.$createElement(r["a"],{props:{size:18}},this.delimiterIcon)]);a.push(s)}return this.$createElement(l["a"],{props:{value:this.internalValue,mandatory:this.mandatory},on:{change:function(e){t.internalValue=e}}},a)},genProgress:function(){return this.$createElement(o["a"],{staticClass:"v-carousel__progress",props:{color:this.progressColor,value:(this.internalIndex+1)/this.items.length*100}})},restartTimeout:function(){this.slideTimeout&&clearTimeout(this.slideTimeout),this.slideTimeout=void 0,window.requestAnimationFrame(this.startTimeout)},startTimeout:function(){this.cycle&&(this.slideTimeout=window.setTimeout(this.next,+this.interval>0?+this.interval:6e3))}},render:function(t){var e=s["a"].options.render.call(this,t);return e.data.style="height: ".concat(Object(c["g"])(this.height),";"),this.hideDelimiters||e.children.push(this.genDelimiters()),(this.progress||this.progressColor)&&e.children.push(this.genProgress()),e}})},"63b7":function(t,e,a){},"6d1c":function(t,e,a){"use strict";e["a"]={getPost:"/noticeboard/posts/",submitPost:"/noticeboard/posts/",patchPost:function(t){return"/noticeboard/posts/".concat(t,"/")},getLikedPostById:function(t){return"/noticeboard/post/like/".concat(t,"/")},likePostById:function(t){return"/noticeboard/post/like/".concat(t,"/")},getLikedCommentById:function(t){return"/noticeboard/post/comment/like/".concat(t,"/")},deletePostById:function(t){return"/noticeboard/posts/".concat(t,"/")},commentPostById:function(t){return"/noticeboard/post/comment/".concat(t,"/")},getCommentByPostId:function(t){return"/noticeboard/post/comment/".concat(t,"/")},getTrendingPost:"/noticeboard/posts/trending/",approveRequest:function(t){return"/noticeboard/posts/".concat(t,"/approve/")},denyRequest:function(t){return"/noticeboard/posts/".concat(t,"/deny/")}}},8448:function(t,e,a){"use strict";var i=function(){var t=this,e=t.$createElement,a=t._self._c||e;return a("v-dialog",{attrs:{"hide-overlay":!1,width:"80%",persistent:""},on:{keydown:function(e){return!e.type.indexOf("key")&&t._k(e.keyCode,"esc",27,e.key,["Esc","Escape"])?null:t.$emit("close")}},model:{value:t.slideShow,callback:function(e){t.slideShow=e},expression:"slideShow"}},[a("v-row",{staticClass:"black ml-0"},[a("v-col",[a("v-carousel",{attrs:{cycle:!1,value:t.startFrom,"hide-delimiters":"","show-arrows":1!==t.items.length}},t._l(t.items,(function(e,i){return a("v-carousel-item",{key:i,attrs:{"lazy-src":e.image_thumb_1,src:e.image,contain:""}},[a("v-btn",{staticClass:"float-right mx-2",attrs:{fab:"",primary:"","x-small":""},on:{click:function(e){return t.$emit("close")}}},[a("v-icon",{attrs:{size:22},domProps:{textContent:t._s("mdi-close")}})],1),a("v-btn",{staticClass:"float-right mx-2",attrs:{fab:"",primary:"","x-small":""},on:{click:function(a){return t.downloadImage(e.image)}}},[a("v-icon",{attrs:{size:22},domProps:{textContent:t._s("mdi-download-outline")}})],1)],1)})),1)],1)],1)],1)},s=[],n=(a("a9e3"),{name:"ImageViewer",props:{items:{type:Array,default:function(){return[]}},slideShow:{type:Boolean,default:!0},postContent:{type:String,default:""},startFrom:{type:Number,default:0}},methods:{performClose:function(){this.$emit("close")},downloadImage:function(t){window.open(t,"_blank")}}}),r=n,o=a("2877"),l=a("6544"),c=a.n(l),d=a("8336"),u=a("5e66"),h=a("3e35"),p=a("62ad"),m=a("169a"),f=a("132d"),g=a("0fd9b"),v=Object(o["a"])(r,i,s,!1,null,null,null);e["a"]=v.exports;c()(v,{VBtn:d["a"],VCarousel:u["a"],VCarouselItem:h["a"],VCol:p["a"],VDialog:m["a"],VIcon:f["a"],VRow:g["a"]})},a51f:function(t,e,a){"use strict";a.r(e);var i=function(){var t=this,e=t.$createElement,a=t._self._c||e;return a("div",[t.search.length>0?a("span",[t._v(' Your search for "'+t._s(t.search)+'" found no results. ')]):t.loading?a("v-skeleton-loader",{attrs:{type:"table",height:t.skeletonLoaderHeight}}):a("no-data-found",{attrs:{text:t.text,height:t.height}},[t._t("default")],2)],1)},s=[],n=(a("a9e3"),a("e585")),r={components:{NoDataFound:n["default"]},props:{search:{type:String,default:""},loading:{type:Boolean,required:!0},text:{type:String,default:"No data available at the moment"},height:{type:[String,Number],default:200},skeletonLoaderHeight:{type:[String,Number],default:void 0}}},o=r,l=a("2877"),c=a("6544"),d=a.n(c),u=a("3129"),h=Object(l["a"])(o,i,s,!1,null,null,null);e["default"]=h.exports;d()(h,{VSkeletonLoader:u["a"]})},abd3:function(t,e,a){},de76:function(t,e,a){"use strict";a.r(e);var i=function(){var t=this,e=t.$createElement,a=t._self._c||e;return a("approval-request-list",{attrs:{"bread-crumbs":t.breadCrumbItems,"html-title":"Noticeboard Approval Request List","hr-admin":""}})},s=[],n=function(){var t=this,e=t.$createElement,a=t._self._c||e;return a("vue-page-wrapper",{attrs:{title:t.htmlTitle,"bread-crumbs":t.breadCrumbItems}},[a("v-card",[a("vue-card-title",{attrs:{title:"Noticeboard Approval Request List",subtitle:"The list below contains the noticeboard post approval requests.",icon:"mdi-post-outline"}},[a("template",{slot:"actions"},[a("v-btn",{attrs:{icon:""},on:{click:function(e){t.filter.show=!t.filter.show}}},[a("v-icon",{attrs:{small:""},domProps:{textContent:t._s("mdi-filter-variant")}})],1)],1)],2),a("v-divider"),a("v-slide-y-transition",[a("v-row",{directives:[{name:"show",rawName:"v-show",value:t.filter.show,expression:"filter.show"}],attrs:{"no-gutters":""}},[a("v-col",{staticClass:"px-2",attrs:{cols:"6",md:"3"}},[a("vue-search",{attrs:{search:t.filter.search},on:{"update:search":function(e){return t.$set(t.filter,"search",e)}},model:{value:t.filter.search,callback:function(e){t.$set(t.filter,"search",e)},expression:"filter.search"}})],1)],1)],1),t.filter.show?a("v-divider"):t._e(),a("v-tabs",{attrs:{"show-arrows":"","slider-color":"blue"},model:{value:t.activeTab,callback:function(e){t.activeTab=e},expression:"activeTab"}},t._l(Object.keys(t.$options.tabs),(function(e){return a("v-tab",{key:e,attrs:{ripple:"",disabled:t.loading},on:{click:function(a){t.status=e}}},[a("span",{staticClass:"text-capitalize mr-2",domProps:{textContent:t._s(e)}}),a("v-chip",{staticClass:"white--text",attrs:{color:t.$options.tabs[e],small:""},domProps:{textContent:t._s(t.response.stats?t.response.stats[e]:"")}})],1)})),1),a("v-divider"),a("v-data-table",{attrs:{headers:t.headers,items:t.fetchedResults,"sort-desc":t.pagination.descending,"sort-by":t.pagination.sortBy,page:t.pagination.page,"items-per-page":t.pagination.rowsPerPage,"footer-props":t.footerProps,"server-items-length":t.pagination.totalItems,"mobile-breakpoint":0,"must-sort":""},on:{"update:sortDesc":function(e){return t.$set(t.pagination,"descending",e)},"update:sort-desc":function(e){return t.$set(t.pagination,"descending",e)},"update:sortBy":function(e){return t.$set(t.pagination,"sortBy",e)},"update:sort-by":function(e){return t.$set(t.pagination,"sortBy",e)},"update:page":function(e){return t.$set(t.pagination,"page",e)},"update:itemsPerPage":function(e){return t.$set(t.pagination,"rowsPerPage",e)},"update:items-per-page":function(e){return t.$set(t.pagination,"rowsPerPage",e)}},scopedSlots:t._u([{key:"item",fn:function(e){return[a("tr",[a("td",[a("vue-user",{attrs:{user:e.item.posted_by}})],1),a("td",[t._v(" "+t._s(t.get(e.item,"category"))+" ")]),a("td",{},[a("div",[t._v(" "+t._s(e.item.modified_at.substring(0,10))+" ")]),a("div",{staticClass:"grey--text"},[t._v(" "+t._s(t.getTime(e.item.modified_at))+" ")])]),a("td",{staticClass:"text-center"},[a("v-chip",{attrs:{color:t.tabsColors[e.item.status],outlined:""}},[t._v(" "+t._s(e.item.status)+" ")])],1),a("td",[a("vue-context-menu",{attrs:{"context-list":[{name:"View Details",icon:"mdi-eye",color:"blue"}]},on:{click0:function(a){return t.viewDetail(e.item)}}})],1)])]}}])},[a("template",{slot:"no-data"},[a("data-table-no-data",{attrs:{loading:t.loading}})],1)],2),a("v-dialog",{attrs:{scrollable:"",width:"900",persistent:""},on:{close:function(e){t.viewRequestDetail=!1},keypress:function(e){if(!e.type.indexOf("key")&&t._k(e.keyCode,"esc",27,e.key,["Esc","Escape"]))return null;t.viewRequestDetail=!1}},model:{value:t.viewRequestDetail,callback:function(e){t.viewRequestDetail=e},expression:"viewRequestDetail"}},[t.viewRequestDetail?a("request-detail",{attrs:{"request-details":t.requestInfo},on:{close:function(e){t.viewRequestDetail=!1},success:function(e){t.viewRequestDetail=!1,t.loadDataTableChange()}}}):t._e()],1)],1)],1)},r=[],o=(a("ac1f"),a("841c"),a("4de4"),a("a51f")),l=a("02cb"),c=a("6d1c"),d=function(){var t=this,e=t.$createElement,a=t._self._c||e;return a("v-card",[a("vue-card-title",{attrs:{title:"Approval Request Detail",subtitle:"Here you can view approval request details and approve or reject the post",icon:"mdi-eye",closable:""},on:{close:function(e){return t.$emit("close")}}}),a("v-divider"),a("v-card-text",{staticClass:"scrollbar-md"},[a("v-row",{staticClass:"mx-1"},[a("v-col",{attrs:{md:"4",cols:"6"}},[a("div",{staticClass:"font-weight-medium"},[a("v-icon",{attrs:{small:""},domProps:{textContent:t._s("mdi-account")}}),t._v(" Requested By ")],1),a("vue-user",{staticClass:"mx-5",attrs:{user:t.requestDetails.posted_by}})],1),a("v-col",{attrs:{md:"4",cols:"6"}},[a("div",{staticClass:"font-weight-medium"},[a("v-icon",{attrs:{small:""},domProps:{textContent:t._s("mdi-information-outline")}}),t._v(" Category ")],1),a("div",{staticClass:"mx-5 black--text"},[t._v(" "+t._s(t.requestDetails.category)+" ")])]),t.requestDetails.modified_at?a("v-col",{attrs:{md:"4",cols:"6"}},[a("div",{staticClass:"font-weight-medium"},[a("v-icon",{attrs:{small:""},domProps:{textContent:t._s("mdi-calendar")}}),t._v(" Requested Date ")],1),a("div",{staticClass:"mx-5 black--text"},[t._v(" "+t._s(t.requestDetails.modified_at.substring(0,10))+" ")]),a("div",{staticClass:"mx-5 text-caption grey--text"},[t._v(" "+t._s(t.$dayjs(t.requestDetails.modified_at).format("hh:mm:ss a"))+" ")])]):t._e(),a("v-col",{attrs:{md:"12"}},[a("div",{staticClass:"user-content",staticStyle:{"white-space":"pre-wrap"},domProps:{innerHTML:t._s(t.requestDetails.post_content)}}),a("attachment-view",{attrs:{attachments:t.requestDetails.attachments}})],1)],1)],1),a("v-card-actions",[a("v-spacer"),a("v-btn",{staticClass:"black--text",attrs:{text:""},on:{click:function(e){return t.$emit("close")}}},[t._v(" Cancel ")]),"Pending"===t.requestDetails.status?a("v-btn",{staticClass:"white--text",attrs:{depressed:"",color:"danger"},on:{click:function(e){return t.changeStatus("deny")}}},[t._v(" Deny ")]):t._e(),"Approved"!==t.requestDetails.status?a("v-btn",{staticClass:"white--text",attrs:{depressed:"",color:"success"},on:{click:function(e){return t.changeStatus("approve")}}},[t._v(" Approve ")]):t._e()],1)],1)},u=[],h=a("facf"),p={components:{AttachmentView:h["a"],VueUser:l["default"]},props:{requestDetails:{type:Object,required:!0,default:function(){return{}}}},methods:{changeStatus:function(t){var e=this;this.$http.post("approve"===t?c["a"].approveRequest(this.requestDetails.id)+"?as=hr":c["a"].denyRequest(this.requestDetails.id)+"?as=hr").then((function(){e.$emit("success"),e.notifyUser("Successfully ".concat(t," request"))}))}}},m=p,f=a("2877"),g=a("6544"),v=a.n(g),b=a("8336"),y=a("b0af"),w=a("99d9"),_=a("62ad"),x=a("ce7e"),C=a("132d"),k=a("0fd9b"),D=a("2fa4"),T=Object(f["a"])(m,d,u,!1,null,null,null),V=T.exports;v()(T,{VBtn:b["a"],VCard:y["a"],VCardActions:w["a"],VCardText:w["c"],VCol:_["a"],VDivider:x["a"],VIcon:C["a"],VRow:k["a"],VSpacer:D["a"]});var S=a("0549"),P=a("e4bf"),$=a("1806"),O={components:{VueContextMenu:P["default"],VuePageWrapper:S["default"],DataTableNoData:o["default"],VueUser:l["default"],RequestDetail:V},mixins:[$["a"]],props:{breadCrumbs:{type:Array,required:!0},htmlTitle:{type:String,required:!0}},tabs:{Pending:"orange",Approved:"green",Denied:"red",All:"cyan"},data:function(){return{loading:!1,breadCrumbItems:[{text:"Noticeboard Approval",disabled:!0},{text:"Request List",disabled:!0}],headers:[{text:"Requested By",value:"full_name"},{text:"Category",value:"category"},{text:"Requested Date",value:"modified_at"},{text:"Status",align:"center",value:"status"},{text:"Action",align:"left",sortable:!1}],tabs:[{tabName:"All",value:"",count:"0",color:"blue"},{tabName:"Pending",value:"Pending",count:"0",color:"orange"},{tabName:"Approved",value:"Approved",count:"0",color:"cyan"},{tabName:"Denied",value:"Denied",count:"0",color:"red"}],tabsColors:{Pending:"orange",Approved:"green",Denied:"red"},counts:{},selectedTab:"",requestInfo:{},filter:{search:"",show:!1},crud:{name:"Resignation Request",endpoint:{common:"",get:"",post:"",put:"",patch:"",delete:""},dataTableFetch:!0},dateFilter:{},search:"",status:"Pending",viewRequestDetail:!1,rowsPerPageItems:[10,20,30,40,50]}},computed:{DataTableFilter:function(){return{status:"All"===this.status?"":this.status,search:this.filter.search||""}}},created:function(){this.crud.endpoint.common=c["a"].getPost+"?as=hr"},methods:{viewDetail:function(t){this.requestInfo=t,this.viewRequestDetail=!0},getTime:function(t){return this.$dayjs(t).format("hh:mm:ss")}}},B=O,R=a("cc20"),j=a("8fea"),q=a("169a"),I=a("0789"),A=a("71a3"),L=a("fe57"),F=Object(f["a"])(B,n,r,!1,null,null,null),E=F.exports;v()(F,{VBtn:b["a"],VCard:y["a"],VChip:R["a"],VCol:_["a"],VDataTable:j["a"],VDialog:q["a"],VDivider:x["a"],VIcon:C["a"],VRow:k["a"],VSlideYTransition:I["g"],VTab:A["a"],VTabs:L["a"]});var N={components:{ApprovalRequestList:E},data:function(){return{breadCrumbItems:[{text:"Noticeboard Approval",disabled:!0},{text:"Request List",disabled:!0}]}}},z=N,G=Object(f["a"])(z,i,s,!1,null,null,null);e["default"]=G.exports},e4bf:function(t,e,a){"use strict";a.r(e);var i=function(){var t=this,e=t.$createElement,a=t._self._c||e;return a("div",[t.contextList.filter((function(t){return!t.hide})).length<3&&!t.hideIcons||t.showIcons?a("div",t._l(t.contextList,(function(e,i){return a("span",{key:i},[e.hide?t._e():a("v-tooltip",{attrs:{disabled:t.$vuetify.breakpoint.xs,top:""},scopedSlots:t._u([{key:"activator",fn:function(s){var n=s.on;return[a("v-btn",t._g({staticClass:"mx-0",attrs:{text:"",width:t.small?"18":"22",depressed:"",icon:""}},n),[a("v-icon",{attrs:{disabled:e.disabled,color:e.color,"data-cy":t.dataCyVariable+"btn-dropdown-menu-item-"+(i+1),dark:!e.disabled,small:t.small,size:"20",dense:""},domProps:{textContent:t._s(e.icon)},on:{click:function(e){return t.$emit("click"+i)}}})],1)]}}],null,!0)},[a("span",{domProps:{textContent:t._s(e.disabled&&e.disable_message||e.name)}})])],1)})),0):a("v-menu",{attrs:{"offset-y":"",left:"",transition:"slide-y-transition"},scopedSlots:t._u([{key:"activator",fn:function(e){var i=e.on;return[a("v-btn",t._g({attrs:{small:"",text:"",icon:""}},i),[a("v-icon",{attrs:{"data-cy":"btn-dropdown-menu"},domProps:{textContent:t._s("mdi-dots-vertical")}})],1)]}}])},t._l(t.contextList,(function(e,i){return a("v-list",{key:i,staticClass:"pa-0",attrs:{dense:""}},[e.hide?t._e():a("div",[e.disabled?a("v-list-item",{attrs:{"data-cy":"btn-dropdown-menu-item"}},[a("v-tooltip",{attrs:{top:""},scopedSlots:t._u([{key:"activator",fn:function(i){var s=i.on;return[a("v-list-item-title",t._g({},s),[a("v-icon",{attrs:{disabled:"",small:"",color:e.color},domProps:{textContent:t._s(e.icon)}}),a("span",{staticClass:"ml-1 grey--text",domProps:{textContent:t._s(e.name)}})],1)]}}],null,!0)},[a("span",{domProps:{textContent:t._s(e.disabled&&e.disable_message||e.name)}})])],1):a("v-list-item",{attrs:{"data-cy":"btn-dropdown-menu-item"},on:{click:function(e){return t.$emit("click"+i)}}},[a("v-list-item-title",[a("v-icon",{attrs:{color:e.color,small:"",dense:""},domProps:{textContent:t._s(e.icon)}}),a("span",{staticClass:"ml-1",class:e.text_color,domProps:{textContent:t._s(e.name)}})],1)],1)],1)])})),1)],1)},s=[],n={name:"VueContextMenu",props:{contextList:{type:Array,default:function(){return[]}},dataCyVariable:{type:String,default:""},showIcons:{type:Boolean,default:!1},hideIcons:{type:Boolean,default:!1},small:{type:Boolean,default:!1}}},r=n,o=a("2877"),l=a("6544"),c=a.n(l),d=a("8336"),u=a("132d"),h=a("8860"),p=a("da13"),m=a("5d23"),f=a("e449"),g=a("3a2f"),v=Object(o["a"])(r,i,s,!1,null,"71ee785c",null);e["default"]=v.exports;c()(v,{VBtn:d["a"],VIcon:u["a"],VList:h["a"],VListItem:p["a"],VListItemTitle:m["c"],VMenu:f["a"],VTooltip:g["a"]})},facf:function(t,e,a){"use strict";var i=function(){var t=this,e=t.$createElement,a=t._self._c||e;return a("div",[t.attachments.length<3?a("div",[a("v-row",{attrs:{dense:""}},t._l(t.attachments,(function(e,i){return a("v-col",{key:"attachmentLarge"+i,attrs:{md:"12",cols:"12"}},[a("v-img",{staticClass:"pointer",staticStyle:{border:"1px solid #efefef"},attrs:{src:e.image_thumb_1,"aspect-ratio":"2"},on:{click:function(e){t.imageViewer.display=!0,t.imageViewer.startFrom=i}}})],1)})),1)],1):3===t.attachments.length?a("v-row",{attrs:{dense:""}},[a("v-col",{attrs:{cols:"12"}},[a("v-img",{staticClass:"pointer",staticStyle:{border:"1px solid #efefef"},attrs:{src:t.attachments[0].image_thumb_1,"aspect-ratio":"2"},on:{click:function(e){t.imageViewer.display=!0,t.imageViewer.startFrom=0}}})],1),a("v-col",{attrs:{cols:"12"}},[a("v-row",{attrs:{dense:""}},[a("v-col",{attrs:{cols:"6"}},[a("v-img",{staticClass:"pointer",staticStyle:{border:"1px solid #efefef"},attrs:{src:t.attachments[1].image_thumb_1,"aspect-ratio":"2"},on:{click:function(e){t.imageViewer.display=!0,t.imageViewer.startFrom=1}}})],1),a("v-col",{attrs:{cols:"6"}},[a("v-img",{staticClass:"pointer",staticStyle:{border:"1px solid #efefef"},attrs:{src:t.attachments[2].image_thumb_1,"aspect-ratio":"2"},on:{click:function(e){t.imageViewer.display=!0,t.imageViewer.startFrom=2}}})],1)],1)],1)],1):4===t.attachments.length?a("v-row",{attrs:{dense:""}},[a("v-col",{attrs:{cols:"6"}},[a("v-row",{attrs:{dense:""}},[a("v-col",{attrs:{cols:"12"}},[a("v-img",{staticClass:"pointer",staticStyle:{border:"1px solid #efefef"},attrs:{src:t.attachments[0].image_thumb_1,"aspect-ratio":"2"},on:{click:function(e){t.imageViewer.display=!0,t.imageViewer.startFrom=0}}})],1),a("v-col",{attrs:{cols:"12"}},[a("v-img",{staticClass:"pointer",staticStyle:{border:"1px solid #efefef"},attrs:{src:t.attachments[1].image_thumb_1,"aspect-ratio":"2"},on:{click:function(e){t.imageViewer.display=!0,t.imageViewer.startFrom=1}}})],1)],1)],1),a("v-col",{attrs:{cols:"6"}},[a("v-row",{attrs:{dense:""}},[a("v-col",{attrs:{cols:"12"}},[a("v-img",{staticClass:"pointer",staticStyle:{border:"1px solid #efefef"},attrs:{src:t.attachments[2].image_thumb_2,"aspect-ratio":"2"},on:{click:function(e){t.imageViewer.display=!0,t.imageViewer.startFrom=2}}})],1),a("v-col",{attrs:{cols:"12"}},[a("v-img",{staticClass:"pointer",staticStyle:{border:"1px solid #efefef"},attrs:{src:t.attachments[3].image_thumb_2,"aspect-ratio":"2"},on:{click:function(e){t.imageViewer.display=!0,t.imageViewer.startFrom=3}}})],1)],1)],1)],1):a("v-row",{attrs:{dense:""}},[t._l(t.attachments,(function(e,i){return[0===i?a("v-col",{key:"attachmentLarge"+i,attrs:{md:"12",cols:"12"}},[a("v-img",{staticClass:"pointer",staticStyle:{border:"1px solid #efefef"},attrs:{src:e.image_thumb_1,"aspect-ratio":"2"},on:{click:function(e){t.imageViewer.display=!0,t.imageViewer.startFrom=i}}})],1):t._e()]})),t._l(t.attachments,(function(e,i){return[i>0&&i<=4?a("v-col",{key:"attachmentSmall"+i,attrs:{md:"3",cols:"12"}},[a("v-img",{staticClass:"pointer",staticStyle:{border:"1px solid #efefef"},attrs:{src:e.image_thumb_2,"aspect-ratio":"1"},on:{click:function(e){t.imageViewer.display=!0,t.imageViewer.startFrom=i}}},[t.images.length-5>0&&4===i?a("v-overlay",{attrs:{value:!0,"z-index":"-1",opacity:"0.5",absolute:""}}):t._e(),t.images.length-5>0&&4===i?a("v-row",{staticClass:"fill-height",attrs:{align:"center"}},[a("v-col",[a("p",{staticClass:"text-h3 ma-auto white--text text-center",staticStyle:{"text-shadow":"2px 2px #5f5f5f"},domProps:{textContent:t._s("+ "+(t.images.length-5))}})])],1):t._e()],1)],1):t._e()]}))],2),t.imageViewer.display?a("image-viewer",{attrs:{items:t.attachments,"start-from":t.imageViewer.startFrom},on:{close:function(e){t.imageViewer.display=!1}}}):t._e()],1)},s=[],n=a("8448"),r={components:{ImageViewer:n["a"]},props:{attachments:{type:[Object,Array],default:void 0}},data:function(){return{imageViewer:{display:!1,startFrom:0},images:this.deepCopy(this.attachments)}}},o=r,l=a("2877"),c=a("6544"),d=a.n(c),u=a("62ad"),h=a("adda"),p=a("a797"),m=a("0fd9b"),f=Object(l["a"])(o,i,s,!1,null,null,null);e["a"]=f.exports;d()(f,{VCol:u["a"],VImg:h["a"],VOverlay:p["a"],VRow:m["a"]})}}]);