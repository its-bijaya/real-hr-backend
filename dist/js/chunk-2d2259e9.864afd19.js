(window["webpackJsonp"]=window["webpackJsonp"]||[]).push([["chunk-2d2259e9"],{e4bf:function(t,e,n){"use strict";n.r(e);var o=function(){var t=this,e=t.$createElement,n=t._self._c||e;return n("div",[t.contextList.filter((function(t){return!t.hide})).length<3&&!t.hideIcons||t.showIcons?n("div",t._l(t.contextList,(function(e,o){return n("span",{key:o},[e.hide?t._e():n("v-tooltip",{attrs:{disabled:t.$vuetify.breakpoint.xs,top:""},scopedSlots:t._u([{key:"activator",fn:function(s){var a=s.on;return[n("v-btn",t._g({staticClass:"mx-0",attrs:{text:"",width:t.small?"18":"22",depressed:"",icon:""}},a),[n("v-icon",{attrs:{disabled:e.disabled,color:e.color,"data-cy":t.dataCyVariable+"btn-dropdown-menu-item-"+(o+1),dark:!e.disabled,small:t.small,size:"20",dense:""},domProps:{textContent:t._s(e.icon)},on:{click:function(e){return t.$emit("click"+o)}}})],1)]}}],null,!0)},[n("span",{domProps:{textContent:t._s(e.disabled&&e.disable_message||e.name)}})])],1)})),0):n("v-menu",{attrs:{"offset-y":"",left:"",transition:"slide-y-transition"},scopedSlots:t._u([{key:"activator",fn:function(e){var o=e.on;return[n("v-btn",t._g({attrs:{small:"",text:"",icon:""}},o),[n("v-icon",{attrs:{"data-cy":"btn-dropdown-menu"},domProps:{textContent:t._s("mdi-dots-vertical")}})],1)]}}])},t._l(t.contextList,(function(e,o){return n("v-list",{key:o,staticClass:"pa-0",attrs:{dense:""}},[e.hide?t._e():n("div",[e.disabled?n("v-list-item",{attrs:{"data-cy":"btn-dropdown-menu-item"}},[n("v-tooltip",{attrs:{top:""},scopedSlots:t._u([{key:"activator",fn:function(o){var s=o.on;return[n("v-list-item-title",t._g({},s),[n("v-icon",{attrs:{disabled:"",small:"",color:e.color},domProps:{textContent:t._s(e.icon)}}),n("span",{staticClass:"ml-1 grey--text",domProps:{textContent:t._s(e.name)}})],1)]}}],null,!0)},[n("span",{domProps:{textContent:t._s(e.disabled&&e.disable_message||e.name)}})])],1):n("v-list-item",{attrs:{"data-cy":"btn-dropdown-menu-item"},on:{click:function(e){return t.$emit("click"+o)}}},[n("v-list-item-title",[n("v-icon",{attrs:{color:e.color,small:"",dense:""},domProps:{textContent:t._s(e.icon)}}),n("span",{staticClass:"ml-1",class:e.text_color,domProps:{textContent:t._s(e.name)}})],1)],1)],1)])})),1)],1)},s=[],a={name:"VueContextMenu",props:{contextList:{type:Array,default:function(){return[]}},dataCyVariable:{type:String,default:""},showIcons:{type:Boolean,default:!1},hideIcons:{type:Boolean,default:!1},small:{type:Boolean,default:!1}}},i=a,l=n("2877"),r=n("6544"),d=n.n(r),c=n("8336"),u=n("132d"),m=n("8860"),p=n("da13"),f=n("5d23"),v=n("e449"),b=n("3a2f"),_=Object(l["a"])(i,o,s,!1,null,"71ee785c",null);e["default"]=_.exports;d()(_,{VBtn:c["a"],VIcon:u["a"],VList:m["a"],VListItem:p["a"],VListItemTitle:f["c"],VMenu:v["a"],VTooltip:b["a"]})}}]);