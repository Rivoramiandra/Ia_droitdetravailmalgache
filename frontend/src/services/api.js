import axios from 'axios'

const BASE_URL = import.meta.env.VITE_API_URL || '/api'

const client = axios.create({
  baseURL: BASE_URL,
  timeout: 15000,
  headers: { 'Content-Type': 'application/json' },
})

// Mock responses used when no FastAPI backend is reachable.
const MOCK_REPLIES = [
  "Bonne question ! Voici ce que je peux vous dire à ce sujet.",
  "Je suis un assistant de démonstration. Pouvez-vous préciser votre demande ?",
  "Intéressant. Laissez-moi reformuler : vous souhaitez en savoir plus sur ce point ?",
  "Voici une réponse synthétique basée sur votre question.",
  "Je n'ai pas toutes les informations, mais voici une piste de réflexion.",
]

function mockAnswer(question) {
  const seed = question.length % MOCK_REPLIES.length
  return MOCK_REPLIES[seed]
}

export async function askQuestion(question) {
  try {
    const { data } = await client.post('/ask', { question })
    return data.answer
  } catch (error) {
    // Fallback for the demo environment (no FastAPI backend running).
    return mockAnswer(question)
  }
}

export default { askQuestion }
