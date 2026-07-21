<script setup>
import {
    Plus,
    MessageSquare,
    Trash2,
    X
} from '@lucide/vue'

defineProps({
    show:{
        type:Boolean,
        default:false
    }
})

const emit = defineEmits([
    "close",
    "new-chat"
])

const histories = [
    "Contrat de travail CDI",
    "Droit du salarié licencié",
    "Congés annuels Madagascar",
    "Salaire minimum légal"
]

// Fonction pour gérer le clic sur "Nouvelle discussion"
const handleNewChat = () => {
    emit('new-chat')
    // Fermer automatiquement le sidebar après avoir créé une nouvelle discussion
    emit('close')
}
</script>

<template>
    <aside 
        class="history"
        :class="{show:show}"
    >
        <!-- fermeture mobile -->
        <button 
            class="close-btn"
            @click="emit('close')"
        >
            <X size="20"/>
        </button>

        <!-- Nouvelle discussion -->
        <button 
            class="new-chat"
            @click="handleNewChat"
        >
            <Plus size="18"/>
            <span>
                Nouvelle discussion
            </span>
        </button>

        <h3>
            Historique
        </h3>

        <div class="history-list">
            <div
                v-for="(item,index) in histories"
                :key="index"
                class="history-item"
            >
                <MessageSquare size="16"/>
                <span>
                    {{item}}
                </span>
                <button class="delete">
                    <Trash2 size="14"/>
                </button>
            </div>
        </div>
    </aside>
</template>

<style scoped>
.history{
    width:260px;
    height:calc(100vh - 65px);
    position:sticky;
    top:65px;
    background:#0f172a;
    border-right:1px solid rgba(255,255,255,.1);
    padding:20px;
    overflow-y:auto;
    flex-shrink:0;
}

.new-chat{
    width:100%;
    height:44px;
    display:flex;
    align-items:center;
    justify-content:center;
    gap:8px;
    border-radius:10px;
    border:none;
    cursor:pointer;
    background:#38bdf8;
    color:#082f49;
    font-weight:600;
}

h3{
    margin-top:25px;
    color:#94a3b8;
    font-size:14px;
}

.history-item{
    display:flex;
    align-items:center;
    gap:10px;
    padding:10px;
    margin-bottom:8px;
    border-radius:10px;
    color:#cbd5e1;
    cursor:pointer;
}

.history-item:hover{
    background:#1e293b;
}

.history-item span{
    flex:1;
    overflow:hidden;
    white-space:nowrap;
    text-overflow:ellipsis;
}

.delete{
    background:none;
    border:none;
    color:#64748b;
    cursor:pointer;
}

.delete:hover{
    color:#ef4444;
}

.close-btn{
    display:none;
}

/* =====================
        MOBILE
===================== */
@media(max-width:900px){
    .history{
        position:fixed;
        top:65px;
        left:0;
        width:85vw;
        max-width:320px;
        height:calc(100vh - 65px);
        z-index:200;
        transform:translateX(-110%);
        transition:.3s ease;
        box-shadow: 10px 0 30px rgba(0,0,0,.4);
    }

    .history.show{
        transform:translateX(0);
    }

    .close-btn{
        display:flex;
        position:absolute;
        right:15px;
        top:15px;
        width:35px;
        height:35px;
        align-items:center;
        justify-content:center;
        border:none;
        border-radius:50%;
        background:#1e293b;
        color:white;
        cursor:pointer;
    }

    .new-chat{
        margin-top:45px;
    }
}
</style>