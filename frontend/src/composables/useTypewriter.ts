import { ref } from "vue"

export function useTypewriter(speed = 30) {
  const text = ref("")
  const isTyping = ref(false)

  async function type(value: string) {
    text.value = ""
    isTyping.value = true

    for (const char of value) {
      text.value += char

      await new Promise((resolve) => {
        setTimeout(resolve, speed)
      })
    }

    isTyping.value = false
  }

  return {
    text,
    isTyping,
    type,
  }
}