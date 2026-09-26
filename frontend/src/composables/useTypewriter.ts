import { ref } from "vue"

export function useTypewriter(speed = 20) {
  const text = ref("")
  const isTyping = ref(false)

  async function type(value: string) {
    text.value = ""
    isTyping.value = true

    for (let i = 0; i < value.length; i++) {
      text.value += value[i]

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