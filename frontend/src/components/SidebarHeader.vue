<script setup>

import {
    Home,
    MessageCircle,
    Info,
    X
} from '@lucide/vue'


import { RouterLink } from 'vue-router'


defineProps({

    show:{
        type:Boolean,
        default:false
    }

})


const emit = defineEmits([
    "close"
])


const links = [

    {
        to:"/",
        label:"Accueil",
        icon:Home
    },

    {
        to:"/chat",
        label:"Chatbot",
        icon:MessageCircle
    },

    {
        to:"/about",
        label:"À propos",
        icon:Info
    }

]


</script>



<template>


<aside
    class="sidebar"
    :class="{open:show}"
>



    <div class="sidebar-header">


        <h2>
            LegalAI
        </h2>



        <button
            class="close"
            @click="emit('close')"
        >

            <X size="20"/>

        </button>


    </div>





    <nav>


        <RouterLink
            v-for="link in links"
            :key="link.to"
            :to="link.to"
            class="side-link"
            @click="emit('close')"
        >


            <component
                :is="link.icon"
                size="20"
            />


            <span>
                {{link.label}}
            </span>


        </RouterLink>


    </nav>



</aside>



</template>





<style scoped>


.sidebar{

    position:fixed;

    top:65px;

    left:0;


    width:260px;

    height:calc(100vh - 65px);


    background:#0f172a;


    border-right:1px solid rgba(255,255,255,.1);


    padding:20px;


    z-index:200;


    transform:translateX(-100%);


    transition:.3s ease;


}



/* ouverture mobile */

.sidebar.open{

    transform:translateX(0);

}





.sidebar-header{

    display:flex;

    justify-content:space-between;

    align-items:center;

    margin-bottom:30px;

}



.sidebar-header h2{

    color:white;

    font-size:20px;

}





.close{


    width:35px;

    height:35px;


    border:none;


    border-radius:50%;


    display:flex;


    justify-content:center;


    align-items:center;


    background:#1e293b;


    color:white;


    cursor:pointer;


}





nav{


    display:flex;


    flex-direction:column;


    gap:10px;


}





.side-link{


    display:flex;


    align-items:center;


    gap:12px;


    padding:12px;


    border-radius:10px;


    color:#cbd5e1;


    text-decoration:none;


}





.side-link:hover,
.router-link-active{


    background:#38bdf8;


    color:#082f49;


}






/* GRAND ECRAN */

@media(min-width:901px){


.sidebar{


    display:none;


}



}





/* MOBILE */

@media(max-width:900px){


.sidebar{


    display:block;


}



}

</style>