<script setup>
import { ref } from 'vue'
import ChatContainer from '../components/ChatContainer.vue'
import ChatHistory from '../components/ChatHistory.vue'
import {
    Plus
} from '@lucide/vue'

const showHistory = ref(false)

// Ajout d'un ID de conversation
const conversationId = ref(0)

const createNewChat = () => {
    conversationId.value += 1  // Change l'ID pour déclencher la réinitialisation
}
</script>

<template>
    <section class="chat-page">
        <!-- Sidebar historique -->
        <ChatHistory
            :show="showHistory"
            @close="showHistory=false"
            @newChat="createNewChat"
        />

        <!-- Overlay mobile -->
        <div
            v-if="showHistory"
            class="overlay"
            @click="showHistory=false"
        ></div>

        <!-- Contenu Chat -->
        <main class="chat-main">
            <!-- bouton mobile -->
            <button
                class="mobile-new"
                @click="showHistory=true"
                title="Nouvelle discussion"
            >
                <Plus size="22"/>
            </button>

            <div class="page-head">
                <p>
                    Posez vos questions, l'assistant vous répond en temps réel.
                </p>
            </div>

            <!-- Passage de l'ID de conversation -->
            <ChatContainer :conversation-id="conversationId" />
        </main>
    </section>
</template>

<style scoped>
.chat-page{
    display:flex;
    height:calc(100vh - 65px);
    background:#020617;
    overflow:hidden;
}

.chat-main{
    flex:1;
    min-width:0;
    padding:2rem 1.5rem;
    overflow-y:auto;
}

.page-head{
    text-align:center;
    margin-bottom:20px;
}

.page-head p{
    color:#94a3b8;
}

/* bouton mobile + */
.mobile-new{
    display:none;
    width:42px;
    height:42px;
    border:none;
    border-radius:50%;
    align-items:center;
    justify-content:center;
    background:#38bdf8;
    color:#082f49;
    cursor:pointer;
    transition:.2s;
}

.mobile-new:hover{
    transform:scale(1.05);
}

/* overlay */
.overlay{
    display:none;
}

/* =====================
        MOBILE
===================== */
@media(max-width:900px){
    .chat-page{
        position:relative;
    }

    .chat-main{
        width:100%;
        padding:15px;
    }

    .mobile-new{
        display:flex;
        margin-bottom:15px;
    }

    .overlay{
        display:block;
        position:absolute;
        inset:0;
        background:rgba(0,0,0,.5);
        z-index:40;
    }
}
</style>