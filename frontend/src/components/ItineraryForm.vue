<script setup>
import { computed, ref } from 'vue'
import { storeToRefs } from 'pinia'
import { useItineraryStore } from '../stores/itinerary'

const store = useItineraryStore()
const { request, ui, raw } = storeToRefs(store)

const destinationDraft = ref('')

const addDestination = () => {
  const value = destinationDraft.value.trim()
  if (!value) return
  if (!request.value.destination.includes(value)) request.value.destination.push(value)
  destinationDraft.value = ''
}

const removeDestination = (idx) => {
  request.value.destination.splice(idx, 1)
}

const isValid = computed(() => {
  if (!request.value.departure.trim()) return false
  if (!Array.isArray(request.value.destination) || request.value.destination.length === 0) return false
  if (!Number.isFinite(Number(request.value.pax)) || Number(request.value.pax) <= 0) return false
  const min = Number(request.value.budget.min)
  const max = Number(request.value.budget.max)
  if (!Number.isFinite(min) || !Number.isFinite(max) || min < 0 || max < 0 || min > max) return false
  const s = request.value.time.start_date
  const e = request.value.time.end_date
  if (!s || !e) return false
  if (s > e) return false
  return true
})

const submitError = ref('')

const recommendedViews = computed(() => (Array.isArray(raw.value?.views) ? raw.value.views : []))

const onGenerate = async () => {
  submitError.value = ''
  try {
    await store.generateItinerary({
      departure: request.value.departure.trim(),
      destination: request.value.destination.map((d) => d.trim()).filter(Boolean),
      pax: Number(request.value.pax),
      budget: {
        min: Number(request.value.budget.min),
        max: Number(request.value.budget.max),
        currency: request.value.budget.currency || 'CNY',
      },
      time: {
        start_date: request.value.time.start_date,
        end_date: request.value.time.end_date,
      },
    })
  } catch (e) {
    submitError.value = String(e?.message || ui.value.error || 'Request failed.')
  }
}
</script>

<template>
  <div class="flex h-full flex-col gap-4">
    <div class="border border-[var(--line)] bg-[rgba(10,10,10,0.68)] p-4">
      <div class="mb-3 text-[11px] uppercase tracking-[0.24em] text-[var(--dim)]">Input Console</div>

      <div class="grid grid-cols-1 gap-3">
        <label class="block">
          <div class="mb-1 text-[11px] uppercase tracking-[0.2em] text-[var(--dim)]">Departure</div>
          <input
            v-model="request.departure"
            class="w-full border border-[var(--line)] bg-transparent px-3 py-2 text-[13px] text-[var(--chalk)] outline-none focus:border-[var(--line-strong)]"
            placeholder="Kuala Lumpur"
          />
        </label>

        <div>
          <div class="mb-1 text-[11px] uppercase tracking-[0.2em] text-[var(--dim)]">Destination</div>
          <div class="flex gap-2">
            <input
              v-model="destinationDraft"
              class="flex-1 border border-[var(--line)] bg-transparent px-3 py-2 text-[13px] outline-none focus:border-[var(--line-strong)]"
              placeholder="Bangkok"
              @keydown.enter.prevent="addDestination"
            />
            <button
              type="button"
              class="border border-[var(--line)] px-3 py-2 text-[11px] uppercase tracking-[0.22em] text-[var(--muted)] hover:border-[var(--line-strong)] hover:text-[var(--chalk)]"
              @click="addDestination"
            >
              Add
            </button>
          </div>
          <div class="mt-2 flex flex-wrap gap-2">
            <button
              v-for="(d, idx) in request.destination"
              :key="d + idx"
              type="button"
              class="group flex items-center gap-2 border border-[var(--line)] bg-[rgba(10,10,10,0.6)] px-2 py-1 text-[12px] text-[var(--muted)] hover:border-[var(--line-strong)]"
              @click="removeDestination(idx)"
            >
              <span>{{ d }}</span>
              <span class="text-[10px] text-[rgba(244,244,245,0.42)] group-hover:text-[rgba(244,244,245,0.7)]"
                >×</span
              >
            </button>
          </div>
        </div>

        <div class="grid grid-cols-2 gap-3">
          <label class="block">
            <div class="mb-1 text-[11px] uppercase tracking-[0.2em] text-[var(--dim)]">Pax</div>
            <input
              v-model.number="request.pax"
              type="number"
              min="1"
              class="w-full border border-[var(--line)] bg-transparent px-3 py-2 text-[13px] outline-none focus:border-[var(--line-strong)]"
            />
          </label>
          <label class="block">
            <div class="mb-1 text-[11px] uppercase tracking-[0.2em] text-[var(--dim)]">Currency</div>
            <select
              v-model="request.budget.currency"
              class="w-full border border-[var(--line)] bg-transparent px-3 py-2 text-[13px] outline-none focus:border-[var(--line-strong)]"
            >
              <option value="CNY">CNY</option>
              <option value="USD">USD</option>
              <option value="EUR">EUR</option>
            </select>
          </label>
        </div>

        <div class="grid grid-cols-2 gap-3">
          <label class="block">
            <div class="mb-1 text-[11px] uppercase tracking-[0.2em] text-[var(--dim)]">Budget Min</div>
            <input
              v-model.number="request.budget.min"
              type="number"
              min="0"
              class="w-full border border-[var(--line)] bg-transparent px-3 py-2 text-[13px] outline-none focus:border-[var(--line-strong)]"
            />
          </label>
          <label class="block">
            <div class="mb-1 text-[11px] uppercase tracking-[0.2em] text-[var(--dim)]">Budget Max</div>
            <input
              v-model.number="request.budget.max"
              type="number"
              min="0"
              class="w-full border border-[var(--line)] bg-transparent px-3 py-2 text-[13px] outline-none focus:border-[var(--line-strong)]"
            />
          </label>
        </div>

        <div class="grid grid-cols-2 gap-3">
          <label class="block">
            <div class="mb-1 text-[11px] uppercase tracking-[0.2em] text-[var(--dim)]">Start</div>
            <input
              v-model="request.time.start_date"
              type="date"
              class="w-full border border-[var(--line)] bg-transparent px-3 py-2 text-[13px] outline-none focus:border-[var(--line-strong)]"
            />
          </label>
          <label class="block">
            <div class="mb-1 text-[11px] uppercase tracking-[0.2em] text-[var(--dim)]">End</div>
            <input
              v-model="request.time.end_date"
              type="date"
              class="w-full border border-[var(--line)] bg-transparent px-3 py-2 text-[13px] outline-none focus:border-[var(--line-strong)]"
            />
          </label>
        </div>

        <div class="pt-1">
          <button
            type="button"
            :disabled="!isValid || ui.loading"
            class="w-full border border-[var(--line)] px-3 py-3 text-[11px] uppercase tracking-[0.28em] text-[var(--muted)] hover:border-[var(--line-strong)] hover:text-[var(--chalk)] disabled:cursor-not-allowed disabled:opacity-40"
            @click="onGenerate"
          >
            <span v-if="ui.loading">Generating…</span>
            <span v-else>Generate Itinerary</span>
          </button>
        </div>
        <div v-if="submitError" class="border border-[var(--line)] bg-[rgba(10,10,10,0.6)] px-3 py-2 text-[12px] text-[rgba(244,244,245,0.82)]">
          {{ submitError }}
        </div>

        <div class="border border-[var(--line)] bg-[rgba(10,10,10,0.52)] p-3">
          <div class="mb-2 text-[11px] uppercase tracking-[0.22em] text-[var(--dim)]">Recommended Attractions</div>
          <div v-if="recommendedViews.length === 0" class="text-[12px] text-[rgba(244,244,245,0.42)]">
            Generate an itinerary to see recommendations.
          </div>
          <div v-else class="flex flex-wrap gap-2">
            <div
              v-for="(v, idx) in recommendedViews"
              :key="(v?.name || 'view') + '_' + idx"
              class="border border-[var(--line)] bg-[rgba(10,10,10,0.62)] px-2 py-1 text-[12px] text-[rgba(244,244,245,0.78)]"
              :title="v?.location || ''"
            >
              <span class="mr-2">{{ v?.name || 'View' }}</span>
              <span v-if="v?.location" class="text-[rgba(244,244,245,0.5)]">{{ v.location }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

