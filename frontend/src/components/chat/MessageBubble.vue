<script setup lang="ts">
import Badge from "@/components/ui/badge/Badge.vue"
import { Link, FileText } from "lucide-vue-next"

interface Source {
  url: string
}

const props = defineProps<{
  role: "user" | "assistant"
  content: string
  sources: Source[]
}>()

interface Part {
  type: "text" | "bold" | "link" | "source"
  text: string
  url?: string
}

const parts: Part[] = []

// Сначала разбираем ссылки и [source]
const tokens = props.content.split(
  /(\[[^\]]+\]\([^)]+\)|\[[^\]]+\])/g
)

for (const token of tokens) {
  // [text](url)
  const linkMatch = token.match(/^\[([^\]]+)\]\(([^)]+)\)$/)

  if (linkMatch) {
    parts.push({
      type: "link",
      text: linkMatch[1],
      url: linkMatch[2],
    })
    continue
  }

  // [source]
  const sourceMatch = token.match(/^\[([^\]]+)\]$/)

  if (sourceMatch) {
    parts.push({
      type: "source",
      text: sourceMatch[1],
    })
    continue
  }

  // Разбираем **bold**
  const boldParts = token.split(/(\*\*[^*]+\*\*)/g)

  for (const part of boldParts) {
    if (!part) continue

    const boldMatch = part.match(/^\*\*(.+)\*\*$/)

    if (boldMatch) {
      parts.push({
        type: "bold",
        text: boldMatch[1],
      })
    } else {
      parts.push({
        type: "text",
        text: part,
      })
    }
  }
}
</script>

<template>
  <div
    class="flex"
    :class="role === 'user' ? 'justify-end' : 'justify-start'"
  >
    <div
      class="max-w-[80%] rounded-2xl px-4 py-3 text-sm"
      :class="
        role === 'user'
          ? 'bg-primary text-primary-foreground'
          : 'bg-muted'
      "
    >
      <template
        v-for="(part, index) in parts"
        :key="index"
      >
        <!-- Обычный текст -->
        <span v-if="part.type === 'text'">
          {{ part.text }}
        </span>

        <!-- **Жирный текст** -->
        <strong
          v-else-if="part.type === 'bold'"
          class="font-semibold"
        >
          {{ part.text }}
        </strong>

        <!-- [text](url) -->
        <Badge
          v-else-if="part.type === 'link'"
          variant="outline"
          class="mx-0.5 inline-flex bg-white text-blue-500"
        >
          <Link class="mr-1 h-3.5 w-3.5" />

          <a
            :href="part.url"
            target="_blank"
            rel="noopener noreferrer"
            class="hover:underline"
          >
            <strong
              v-if="
                part.text.startsWith('**') &&
                part.text.endsWith('**')
              "
            >
              {{ part.text.slice(2, -2) }}
            </strong>

            <span v-else>
              {{ part.text }}
            </span>
          </a>
        </Badge>

        <!-- [source] -->
        <Badge
          v-else-if="part.type === 'source'"
          variant="outline"
          class="mx-0.5 inline-flex bg-white text-black"
        >
          <FileText class="mr-1 h-3.5 w-3.5" />

          <span>
            {{ part.text }}
          </span>
        </Badge>
      </template>
    </div>
  </div>
</template>