import axios from 'axios'


const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'


const client = axios.create({
  baseURL: BASE_URL,
  timeout: 60000,
  headers: {
    'Content-Type': 'application/json'
  }
})


export async function askQuestion(question) {

  try {

    const { data } = await client.post(
      '/chat',
      {
        question: question
      }
    )


    return data.answer


  } catch (error) {

    console.error(
      "Erreur API LegalAI :",
      error
    )


    throw error
  }
}


export default {
  askQuestion
}