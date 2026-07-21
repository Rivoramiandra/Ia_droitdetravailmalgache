<script setup>

import { ref } from 'vue'

import { RouterView } from 'vue-router'

import Header from './components/Header.vue'

import SidebarHeader from './components/SidebarHeader.vue'


const showSidebar = ref(false)


</script>



<template>


<div class="app-shell">


<Header
    @toggle-sidebar="showSidebar=true"
/>



<SidebarHeader

    :show="showSidebar"

    @close="showSidebar=false"

/>




<main class="app-main">


<RouterView />


</main>



</div>


</template>