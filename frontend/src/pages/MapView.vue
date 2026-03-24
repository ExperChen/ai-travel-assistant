<script setup>
import { computed } from 'vue'
import { storeToRefs } from 'pinia'
import { useItineraryStore } from '../stores/itinerary'

const store = useItineraryStore()
const { raw } = storeToRefs(store)

const hotels = computed(() => {
  const list = Array.isArray(raw.value?.hotels) ? raw.value.hotels : []
  return list.filter((h) => h && typeof h === 'object')
})
const views = computed(() => {
  const list = Array.isArray(raw.value?.views) ? raw.value.views : []
  return list.filter((v) => v && typeof v === 'object')
})

function normalizeEmbedUrl(mapSource) {
  const src = typeof mapSource === 'string' ? mapSource.trim() : ''
  if (!src) return ''
  if (/output=embed/i.test(src)) return src

  try {
    const url = new URL(src)
    const host = url.hostname.toLowerCase()
    if (!host.includes('google.')) return src

    if (url.pathname.startsWith('/maps/embed')) return src

    const q = url.searchParams.get('query') || url.searchParams.get('q') || ''
    if (q) return `https://www.google.com/maps?q=${encodeURIComponent(q)}&output=embed`

    return `https://www.google.com/maps?q=${encodeURIComponent(src)}&output=embed`
  } catch {
    return `https://www.google.com/maps?q=${encodeURIComponent(src)}&output=embed`
  }
}
</script>

<template>
  <div class="grid grid-cols-12 gap-6">
    <section class="col-span-12 lg:col-span-6">
      <div class="border border-[var(--line)] bg-[rgba(10,10,10,0.6)]">
        <div class="border-b border-[var(--line)] px-4 py-3 text-[11px] uppercase tracking-[0.24em] text-[var(--dim)]">
          Hotels
        </div>
        <div v-if="hotels.length === 0" class="px-4 py-5 text-[13px] text-[rgba(244,244,245,0.62)]">
          No hotel data yet. Generate an itinerary first.
        </div>
        <div v-else class="divide-y divide-[rgba(244,244,245,0.12)]">
          <div v-for="(h, idx) in hotels" :key="h.name + '_' + idx" class="px-4 py-4">
            <div class="text-[13px] text-[rgba(244,244,245,0.9)]">{{ h.name }}</div>
            <div class="mt-1 text-[12px] text-[rgba(244,244,245,0.6)]">{{ h.location }}</div>
            <div class="mt-2 flex flex-wrap gap-2 text-[11px] text-[rgba(244,244,245,0.48)]">
              <span v-if="h.rating">Rating: {{ h.rating }}</span>
              <span v-if="h.price">• {{ h.price }}</span>
            </div>
            <a
              v-if="h.map_source"
              :href="h.map_source"
              target="_blank"
              rel="noreferrer"
              class="mt-3 inline-block border border-[var(--line)] px-3 py-2 text-[11px] uppercase tracking-[0.22em] text-[var(--muted)] hover:border-[var(--line-strong)] hover:text-[var(--chalk)]"
            >
              Open Map
            </a>
            <div v-if="h.map_source" class="mt-3 aspect-[16/10] w-full overflow-hidden border border-[var(--line)]">
              <iframe
                :src="normalizeEmbedUrl(h.map_source)"
                class="h-full w-full"
                loading="lazy"
                referrerpolicy="no-referrer"
              ></iframe>
            </div>
            <div v-if="h.map_source" class="mt-2 text-[12px] text-[rgba(244,244,245,0.48)]">
              If the preview is blank, this map provider blocks embedding. Use Open Map instead.
            </div>
            <div v-else class="mt-3 text-[12px] text-[rgba(244,244,245,0.48)]">No map source.</div>
          </div>
        </div>
      </div>
    </section>

    <section class="col-span-12 lg:col-span-6">
      <div class="border border-[var(--line)] bg-[rgba(10,10,10,0.6)]">
        <div class="border-b border-[var(--line)] px-4 py-3 text-[11px] uppercase tracking-[0.24em] text-[var(--dim)]">
          Views
        </div>
        <div v-if="views.length === 0" class="px-4 py-5 text-[13px] text-[rgba(244,244,245,0.62)]">
          No view data yet. Generate an itinerary first.
        </div>
        <div v-else class="grid grid-cols-1 gap-4 p-4 sm:grid-cols-2">
          <div v-for="(v, idx) in views" :key="v.name + '_' + idx" class="border border-[var(--line)] bg-[rgba(10,10,10,0.65)]">
            <div class="aspect-[16/10] w-full overflow-hidden border-b border-[rgba(244,244,245,0.14)]">
              <img
                v-if="v.image"
                :src="v.image"
                alt=""
                loading="lazy"
                referrerpolicy="no-referrer"
                class="h-full w-full object-cover grayscale contrast-125 saturate-50"
              />
              <div v-else class="grid h-full w-full place-items-center text-[12px] text-[rgba(244,244,245,0.55)]">IMAGE</div>
            </div>
            <div class="p-3">
              <div class="text-[13px] text-[rgba(244,244,245,0.9)]">{{ v.name }}</div>
              <div class="mt-1 text-[12px] text-[rgba(244,244,245,0.6)]">{{ v.location }}</div>
              <div class="mt-2 text-[11px] text-[rgba(244,244,245,0.48)]">
                <span>{{ v.arrival_time }}</span>
                <span v-if="v.departure_time"> → {{ v.departure_time }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

