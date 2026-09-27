<script setup lang="ts">
import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { SquarePen, ChevronDown } from "lucide-vue-next"

defineProps<{
  locale: "RU" | "RO" | "EN",
  showNewChatButton: {
    type: boolean,
    default: false
  }
}>()

const emit = defineEmits<{
  "update:locale": [value: "RU" | "RO" | "EN"]
}>()
</script>

<template>
  <header class="flex h-16 items-center justify-between border-b px-6">
    <a href="/" class="flex gap-2">
      <img
        src="/assets/img/logo-rec.png"
        alt=""
        class="h-8 w-fit"
      />

      <div class="flex flex-col mobile-hide">
        <h1 class="font-semibold">Smart City AI</h1>
<p class="text-xs text-muted-foreground">
  {{
    locale === "RU"
      ? "Ваш помощник по городу"
      : locale === "RO"
        ? "Asistentul tău pentru oraș"
        : "Your city assistant"
  }}
</p>
      </div>
    </a>

    <div class="flex items-center gap-2">
      <!-- Language -->
      <DropdownMenu>
        <DropdownMenuTrigger as-child>
          <Button
            variant="ghost"
            size="sm"
            class="gap-1"
          >
            {{ locale }}
            <ChevronDown class="h-4 w-4" />
          </Button>
        </DropdownMenuTrigger>

        <DropdownMenuContent align="end">
          <DropdownMenuItem
            @click="emit('update:locale', 'RU')"
          >
            Русский
          </DropdownMenuItem>

          <DropdownMenuItem
            @click="emit('update:locale', 'RO')"
          >
            Română
          </DropdownMenuItem>

          <DropdownMenuItem
            @click="emit('update:locale', 'EN')"
          >
            English
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>

      <!-- New chat -->
      <Button
        variant="outline"
        size="sm"
        class="flex items-center gap-1"
        v-if="showNewChatButton"
        @click="$router.push('/')"
      >
        <SquarePen class="h-4 w-4" />
        <span class="mobile-hide">
{{ locale === "RU" ? "Новый чат" : locale === "RO" ? "Chat nou" : "New chat" }}
        </span>
      </Button>
    </div>
  </header>
</template>