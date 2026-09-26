<script setup lang="ts">
import { ref } from "vue"
import { Eye, EyeOff, LockKeyhole } from "lucide-vue-next"

import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"

const username = ref("")
const password = ref("")
const showPassword = ref(false)
const isLoading = ref(false)

async function login() {
  if (!username.value || !password.value) return

  isLoading.value = true

  // TODO: API login
  await new Promise((resolve) => setTimeout(resolve, 800))

  isLoading.value = false
}
</script>

<template>
  <main class="flex min-h-screen items-center justify-center bg-muted/30 px-4">
    <div class="w-full max-w-sm">

      <!-- Logo / heading -->
      <div class="mb-8 text-center">
        <div
          class="mx-auto mb-4 flex size-12 items-center justify-center rounded-xl bg-primary text-primary-foreground"
        >
          <LockKeyhole class="size-5" />
        </div>

        <h1 class="text-2xl font-semibold tracking-tight">
          Admin Panel
        </h1>

        <p class="mt-2 text-sm text-muted-foreground">
          Войдите в панель управления
        </p>
      </div>

      <!-- Form -->
      <div class="rounded-xl border bg-background p-6 shadow-sm">
        <form
          class="space-y-5"
          @submit.prevent="login"
        >
          <!-- Username -->
          <div class="space-y-2">
            <Label for="username">
              Логин
            </Label>

            <Input
              id="username"
              v-model="username"
              type="text"
              autocomplete="username"
              placeholder="admin"
              :disabled="isLoading"
            />
          </div>

          <!-- Password -->
          <div class="space-y-2">
            <div class="flex items-center justify-between">
              <Label for="password">
                Пароль
              </Label>

              <button
                type="button"
                class="text-xs text-muted-foreground transition hover:text-foreground"
              >
                Забыли пароль?
              </button>
            </div>

            <div class="relative">
              <Input
                id="password"
                v-model="password"
                :type="showPassword ? 'text' : 'password'"
                autocomplete="current-password"
                placeholder="••••••••"
                class="pr-10"
                :disabled="isLoading"
              />

              <button
                type="button"
                class="absolute right-0 top-0 flex h-full w-10 items-center justify-center text-muted-foreground hover:text-foreground"
                @click="showPassword = !showPassword"
              >
                <EyeOff
                  v-if="showPassword"
                  class="size-4"
                />

                <Eye
                  v-else
                  class="size-4"
                />

                <span class="sr-only">
                  {{
                    showPassword
                      ? "Скрыть пароль"
                      : "Показать пароль"
                  }}
                </span>
              </button>
            </div>
          </div>

          <!-- Error -->
          <div
            v-if="false"
            class="rounded-lg border border-destructive/30 bg-destructive/5 px-3 py-2 text-sm text-destructive"
          >
            Неверный логин или пароль
          </div>

          <!-- Submit -->
          <Button
            type="submit"
            class="w-full"
            :disabled="!username || !password || isLoading"
          >
            <span v-if="isLoading">
              Вход...
            </span>

            <span v-else>
              Войти
            </span>
          </Button>
        </form>
      </div>

      <p class="mt-6 text-center text-xs text-muted-foreground">
        Municipal AI Assistant
      </p>
    </div>
  </main>
</template>