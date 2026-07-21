<script setup>

import { RouterLink } from 'vue-router'

import {
    Menu,
    Scale,
    Home,
    MessageCircle,
    Info
} from 'lucide-vue-next'


const emit = defineEmits([
    'toggle-sidebar'
])


const links = [

    {
        to: '/',
        label: 'Accueil',
        icon: Home
    },

    {
        to: '/chat',
        label: 'Chatbot',
        icon: MessageCircle
    },

    {
        to: '/about',
        label: 'À propos',
        icon: Info
    }

]


</script>



<template>

<header class="app-header">


    <div class="header-inner">


        <!-- Hamburger -->

        <button
            class="hamburger"
            @click="emit('toggle-sidebar')"
        >

            <Menu size="22"/>

        </button>




        <!-- Logo -->

        <RouterLink
            to="/"
            class="brand"
        >

            <span class="brand-icon">

                <Scale size="26"/>

            </span>


            <span class="brand-name">

                LegalAI

            </span>


        </RouterLink>





        <!-- Navigation desktop -->

        <nav>


            <RouterLink
                v-for="link in links"
                :key="link.to"
                :to="link.to"
                class="nav-link"
                active-class="active"
            >


                <component
                    :is="link.icon"
                    size="18"
                />


                <span>
                    {{ link.label }}
                </span>


            </RouterLink>


        </nav>




        <div class="space"></div>



    </div>


</header>


</template>





<style scoped>


.app-header{


    position:sticky;


    top:0;


    z-index:100;


    height:65px;


    background:rgba(15,23,42,.9);


    backdrop-filter:blur(12px);


    border-bottom:1px solid rgba(255,255,255,.1);


}




.header-inner{


    height:65px;


    padding:0 20px;


    display:flex;


    align-items:center;


}





/* hamburger */


.hamburger{


    width:40px;


    height:40px;


    display:flex;


    align-items:center;


    justify-content:center;


    border:none;


    border-radius:10px;


    background:rgba(56,189,248,.15);


    color:#38bdf8;


    cursor:pointer;


}





/* logo */


.brand{


    display:flex;


    align-items:center;


    gap:8px;


    margin-left:15px;


    color:white;


    text-decoration:none;


    font-size:20px;


    font-weight:700;


}



.brand-icon{


    color:#38bdf8;


}





/* navigation */


nav{


    position:absolute;


    left:50%;


    transform:translateX(-50%);


    display:flex;


    align-items:center;


    gap:10px;


}





.nav-link{


    display:flex;


    align-items:center;


    gap:7px;


    padding:9px 15px;


    border-radius:20px;


    color:#cbd5e1;


    text-decoration:none;


    transition:.25s;


}




.nav-link:hover,
.active{


    background:#38bdf8;


    color:#082f49;


}





.space{


    flex:1;


}





/* tablette + mobile */


@media(max-width:700px){


nav{


    display:none;


}



.header-inner{


    padding:0 12px;


}


.brand-name{


    font-size:18px;


}



}




/* petit mobile */


@media(max-width:380px){


.brand-name{


    display:none;


}



}

</style>