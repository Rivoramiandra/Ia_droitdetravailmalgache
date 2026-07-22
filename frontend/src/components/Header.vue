<script setup>
import { RouterLink } from 'vue-router'
import {
    Menu,
    Scale,
    Home,
    MessageCircle,
    Info,
    User,
    LogIn,
    Sparkles
} from 'lucide-vue-next'

const emit = defineEmits([
    'toggle-sidebar'
])

const links = [
    {
        to: '/',
        label: 'Accueil',
        icon: Home,
        description: "Page d'accueil"
    },
    {
        to: '/chat',
        label: 'Chatbot',
        icon: MessageCircle,
        description: 'Assistant IA'
    },
    {
        to: '/about',
        label: 'À propos',
        icon: Info,
        description: 'En savoir plus'
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
                aria-label="Menu"
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
                    <span class="nav-icon-wrapper">
                        <component
                            :is="link.icon"
                            size="18"
                        />
                    </span>
                    <span class="nav-label">
                        {{ link.label }}
                    </span>
                </RouterLink>
            </nav>

            <!-- Espace et actions -->
            <div class="header-actions">
                <!-- Bouton Connexion -->
                <button class="action-btn" aria-label="Se connecter">
                    <LogIn size="18"/>
                    <span>Connexion</span>
                </button>

                <!-- Bouton S'inscrire -->
                <button class="action-btn primary" aria-label="S'inscrire">
                    <User size="18"/>
                    <span>S'inscrire</span>
                </button>
            </div>
        </div>
    </header>
</template>

<style scoped>
.app-header {
    position: sticky;
    top: 0;
    z-index: 100;
    height: 70px;
    background: rgba(15, 23, 42, 0.92);
    backdrop-filter: blur(16px);
    border-bottom: 1px solid rgba(255, 255, 255, 0.06);
    box-shadow: 0 4px 30px rgba(0, 0, 0, 0.3);
}

.header-inner {
    height: 70px;
    padding: 0 32px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    max-width: 1400px;
    margin: 0 auto;
}

/* =====================
   HAMBURGER
===================== */
.hamburger {
    width: 42px;
    height: 42px;
    display: none;
    align-items: center;
    justify-content: center;
    border: none;
    border-radius: 12px;
    background: rgba(56, 189, 248, 0.1);
    color: #38bdf8;
    cursor: pointer;
    transition: all 0.25s ease;
}

.hamburger:hover {
    background: rgba(56, 189, 248, 0.2);
    transform: scale(1.05);
}

/* =====================
   BRAND / LOGO
===================== */
.brand {
    display: flex;
    align-items: center;
    gap: 10px;
    color: white;
    text-decoration: none;
    font-size: 22px;
    font-weight: 700;
    letter-spacing: -0.5px;
    position: relative;
    padding: 6px 0;
}

.brand-icon {
    color: #38bdf8;
    display: flex;
    align-items: center;
    transition: transform 0.3s ease;
}

.brand:hover .brand-icon {
    transform: rotate(-8deg) scale(1.05);
}

.brand-name {
    background: linear-gradient(135deg, #ffffff 0%, #94a3b8 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

.brand-badge {
    font-size: 10px;
    font-weight: 600;
    padding: 2px 8px;
    border-radius: 20px;
    background: rgba(56, 189, 248, 0.15);
    color: #38bdf8;
    letter-spacing: 0.5px;
    -webkit-text-fill-color: #38bdf8;
    text-transform: uppercase;
}

/* =====================
   NAVIGATION
===================== */
nav {
    display: flex;
    align-items: center;
    gap: 6px;
    background: rgba(255, 255, 255, 0.04);
    padding: 4px;
    border-radius: 16px;
    border: 1px solid rgba(255, 255, 255, 0.05);
}

.nav-link {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 8px 18px;
    border-radius: 12px;
    color: #94a3b8;
    text-decoration: none;
    font-size: 14px;
    font-weight: 500;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    position: relative;
}

.nav-icon-wrapper {
    display: flex;
    align-items: center;
    transition: transform 0.3s ease;
}

.nav-link:hover .nav-icon-wrapper {
    transform: translateY(-2px) scale(1.1);
}

.nav-link:hover {
    color: #e2e8f0;
    background: rgba(255, 255, 255, 0.06);
    transform: translateY(-1px);
}

.nav-link.active {
    color: #082f49;
    background: linear-gradient(135deg, #38bdf8, #0ea5e9);
    box-shadow: 0 4px 15px rgba(56, 189, 248, 0.3);
}

.nav-link.active .nav-icon-wrapper {
    color: #082f49;
}

/* =====================
   HEADER ACTIONS
===================== */
.header-actions {
    display: flex;
    align-items: center;
    gap: 10px;
}

.action-btn {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 8px 16px;
    border: none;
    border-radius: 10px;
    background: rgba(255, 255, 255, 0.05);
    color: #94a3b8;
    cursor: pointer;
    font-size: 14px;
    font-weight: 500;
    transition: all 0.25s ease;
}

.action-btn:hover {
    background: rgba(255, 255, 255, 0.1);
    color: #e2e8f0;
    transform: translateY(-2px);
}

.action-btn.primary {
    background: linear-gradient(135deg, #38bdf8, #0ea5e9);
    color: #082f49;
    font-weight: 600;
    box-shadow: 0 4px 15px rgba(56, 189, 248, 0.25);
}

.action-btn.primary:hover {
    transform: translateY(-2px) scale(1.02);
    box-shadow: 0 6px 25px rgba(56, 189, 248, 0.4);
    background: linear-gradient(135deg, #0ea5e9, #0284c7);
}

/* =====================
   RESPONSIVE
===================== */

/* Tablette */
@media (max-width: 900px) {
    .header-inner {
        padding: 0 20px;
    }

    nav {
        gap: 4px;
        padding: 3px;
    }

    .nav-link {
        padding: 6px 14px;
        font-size: 13px;
    }

    .nav-label {
        display: none;
    }

    .nav-link .nav-icon-wrapper {
        margin: 0;
    }

    .action-btn span {
        display: none;
    }

    .action-btn {
        padding: 8px 12px;
    }

    .brand-badge {
        display: none;
    }
}

/* Mobile */
@media (max-width: 700px) {
    .app-header {
        height: 64px;
    }

    .header-inner {
        height: 64px;
        padding: 0 16px;
    }

    .hamburger {
        display: flex;
    }

    nav {
        display: none;
    }

    .header-actions {
        gap: 8px;
    }

    .action-btn {
        padding: 8px 12px;
        border-radius: 10px;
    }

    .action-btn.primary {
        padding: 8px 16px;
    }

    .action-btn span {
        display: none;
    }

    .brand {
        font-size: 18px;
        gap: 8px;
        margin-left: 8px;
    }

    .brand-name {
        font-size: 18px;
    }

    .brand-badge {
        display: none;
    }
}

/* Très petit mobile */
@media (max-width: 380px) {
    .brand-name {
        display: none;
    }

    .brand-icon {
        margin: 0;
    }

    .header-actions .action-btn:not(.primary) {
        display: none;
    }

    .action-btn.primary {
        padding: 8px 12px;
    }
}
</style>