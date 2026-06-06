<template>
	<router-view />
</template>

<script setup>
import { onMounted, onUnmounted } from "vue";
import {
	useNotificationsStore,
	ensureNotificationsConnected,
} from "@store/notifications.js";

const notificationsStore = useNotificationsStore();
let pollTimer = null;

function onVisibilityChange() {
	if (document.visibilityState === "visible" && localStorage.getItem("tokenAuth")) {
		ensureNotificationsConnected();
		notificationsStore.pollTaskProgress();
	}
}

onMounted(() => {
	if (localStorage.getItem("tokenAuth")) {
		ensureNotificationsConnected();
	}

    pollTimer = setInterval(() => {
		if (!localStorage.getItem("tokenAuth")) return;
		const store = notificationsStore;
		// Только пока есть активная обработка или WS отвалился.
		if (!store.connected || store.isProcessing) {
			store.pollTaskProgress();
		}
	}, 5000);

	document.addEventListener("visibilitychange", onVisibilityChange);
});

onUnmounted(() => {
	if (pollTimer) clearInterval(pollTimer);
	document.removeEventListener("visibilitychange", onVisibilityChange);
	notificationsStore.disconnect();
});
</script>
