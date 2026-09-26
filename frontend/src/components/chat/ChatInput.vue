<script setup lang="ts">
import { onMounted, ref } from "vue"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { ArrowUpCircleIcon } from "lucide-vue-next"
import { categoriesApi } from "@/api/categories"
import { watchDeep } from "@vueuse/core"
defineProps<{
  isLoading: boolean
  locale: "RU" | "RO",
  categoryId: number | null,
  isFirstMessage: {
    type: boolean,
    default: true
  };
}>()
const categories = ref([])
const emit = defineEmits<{
  send: [message: string]
}>()


const input = ref("")
const selectedCategory = ref("all")


watchDeep(selectedCategory, (newCategory) => {
  emit("update:categoryId", newCategory === "all" ? null : newCategory)
})
function send() {
  const value = input.value.trim()

  if (!value) return

  emit("send", value)
  input.value = ""
}

function handleKeydown(event: KeyboardEvent) {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault()
    send()
  }
}

onMounted(async () => {
  try {
    const response = await categoriesApi.list()
    categories.value = response
  } catch (error) {
    console.error("Error fetching categories:", error)
  }
})
</script>

<template>
  <footer class="sticky bottom-0 border-t bg-background p-4">
    <div class="mx-auto max-w-3xl">

      <!-- Categories -->
      <div
        class="mb-3 flex gap-2 overflow-x-auto pb-1 scrollbar-none"
      >
       <button
        v-if="categories.length == 0"
         
        
          class="shrink-0 rounded-full border px-3 py-1.5 text-xs font-medium transition-colors transparent"
         
        >
   
          -
        </button>
        <button
        v-if="isFirstMessage"
          v-for="category in categories"
          :key="category.id"
          type="button"
          class="shrink-0 rounded-full border px-3 py-1.5 text-xs font-medium transition-colors"
          :class="
            selectedCategory === category.id
              ? 'border-primary bg-primary text-primary-foreground'
              : 'bg-background text-muted-foreground hover:bg-muted hover:text-foreground'
          "
          @click="selectedCategory = category.id"
        >
   
         {{ locale === "RU" ? category.name.ru : locale === "RO" ? category.name.ro : category.name.en }}
        </button>
      </div>

      <!-- Input -->
      <div class="relative">
        <Textarea
          v-model="input"
          :placeholder="
            locale === 'RU'
              ? 'Напишите свой вопрос...'
              : locale === 'RO'
                ? 'Scrie întrebarea ta...'
                : 'Write your question...'
          "
          class="min-h-[56px] max-h-20 resize-none overflow-y-auto pr-20"
          @keydown="handleKeydown"
        />

        <Button
          class="absolute bottom-2 right-2"
          size="sm"
          :disabled="!input.trim() || isLoading"
          @click="send"
        >
        <ArrowUpCircleIcon></ArrowUpCircleIcon>
          <span class="mobile-hide">
  {{ locale === "RU" ? "Отправить" : locale === "RO" ? "Trimite" : "Send"  }}
          </span>
        </Button>
      </div>

      <p class="mt-2 text-center text-xs text-muted-foreground">
        
        {{
          locale === "RU"
            ? "AI может допускать ошибки. Проверяйте важную информацию."
            : locale === "RO"
              ? "AI poate face greșeli. Verifică informațiile importante."
              : "AI can make mistakes. Please verify important information."
        }}
      </p>
    </div>
  </footer>
</template>